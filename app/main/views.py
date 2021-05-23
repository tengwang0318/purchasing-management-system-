import datetime

from flask import render_template, redirect, url_for, abort, flash, request, \
    current_app, make_response
from flask_login import login_required, current_user
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm, PurchaseForm, RefundForm, StorageForm, \
    AllocateForm, AccountForm, InventoryWarningForm
from .. import db
from ..models import Permission, Role, User, Post, Comment, Inventory, Purchase, Refund, Storage, Allocate, Medicine, \
    Warning
from ..decorators import admin_required, permission_required


@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        post = Post(body=form.body.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts,
                           show_followed=show_followed, pagination=pagination)


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts,
                           pagination=pagination)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been published.')
        return redirect(url_for('.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // \
               current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('post.html', posts=[post], form=form,
                           comments=comments, pagination=pagination)


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permission.ADMIN):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        db.session.commit()
        flash('The post has been updated.')
        return redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are now following %s.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('You are not following this user.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following %s anymore.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of",
                           endpoint='.followers', pagination=pagination,
                           follows=follows)


@main.route('/followed_by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments,
                           pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))


# @main.route('/inventory')
# @login_required
# def inventory():
#     form = InventoryForm()
#     page = request.args.get('page', 1, type=int)
#     pagination = Inventory.query.order_by(Inventory.medicine_id).paginate(
#         page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
#         error_out=False)
#     inventory_items = pagination.items
#     return render_template('inventory.html', form=form, inventory_items=inventory_items, pagination=pagination,
#                            page=page)
#
#
# @main.route('/inventory_purchase')
# @login_required
# def inventory_purchase():
#     form = InventoryPurchaseForm()


@main.route('/purchase', methods=['GET', 'POST'])
@login_required
def purchase():
    form = PurchaseForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        purchase_item = Purchase(medicine_id=form.medicine_id.data, count=form.count.data,
                                 author=current_user._get_current_object())
        db.session.add(purchase_item)
        db.session.commit()
        return redirect(url_for('.purchase'))
    # purchases = Purchase.query.order_by(Purchase.timestamp.desc()).all()
    page = request.args.get('page', 1, type=int)
    pagination = Purchase.query.order_by(Purchase.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    purchases = pagination.items

    return render_template('purchase.html', form=form, purchases=purchases, pagination=pagination)


@main.route('/return_goods', methods=['GET', "POST"])
@login_required
def return_goods():
    form = RefundForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        return_goods_item = Refund(purchase_id=form.purchase_id.data,
                                   author=current_user._get_current_object())
        db.session.add(return_goods_item)
        query = Purchase.query.filter_by(id=form.purchase_id.data).first()
        query.return_goods = True
        db.session.add(query)
        db.session.commit()
        return redirect(url_for('.return_goods'))
    page = request.args.get('page', 1, type=int)
    pagination = Refund.query.order_by(Refund.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    return_goods_items = pagination.items
    return render_template('return_goods.html', form=form, return_goods_items=return_goods_items, pagination=pagination,
                           Purchase=Purchase)


@main.route("/storage", methods=["GET", "POST"])
@login_required
def storage():
    form = StorageForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        storage_item = Storage(purchase_id=form.storage_items_id.data, author=current_user._get_current_object())
        db.session.add(storage_item)
        query = Purchase.query.filter_by(id=form.storage_items_id.data).first()
        query.have_storage = True

        temp_query = Inventory.query.filter_by(medicine_id=query.medicine_id).first()

        if temp_query:
            temp_query.count += int(query.count)
            # inventory_item = Inventory(medicine_id=query.medicine_id, count=query.count + temp_query.count)
        else:
            medicine_feature = Medicine.query.filter_by(medicine_id=query.medicine_id).first()
            temp_query = Inventory(medicine_id=query.medicine_id, medicine_name=medicine_feature.medicine_name,
                                   medicine_type=medicine_feature.medicine_type, count=query.count)
        db.session.add(temp_query)
        db.session.add(query)
        db.session.commit()

        # warning check
        warning_items = Warning.query.filter_by(medicine_id=query.medicine_id).first()
        if warning_items:
            warning_items.count = temp_query.count
            warning_items.warning = warning_items.count < warning_items.warning_count
            db.session.add(warning_items)
            db.session.commit()

        return redirect(url_for('.storage'))
    page = request.args.get('page', 1, type=int)
    pagination = Storage.query.order_by(Storage.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    storage_items = pagination.items
    return render_template('storage.html', form=form, storage_items=storage_items, pagination=pagination,
                           Purchase=Purchase)


@main.route("/inventory", methods=["GET", "POST"])
@login_required
def inventory():
    page = request.args.get('page', 1, type=int)
    pagination = Inventory.query.order_by(Inventory.medicine_id.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    inventory_items = pagination.items
    return render_template('inventory.html', inventory_items=inventory_items, pagination=pagination)


@main.route('/allocate', methods=['GET', "POST"])
@login_required
def allocate():
    form = AllocateForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        allocate_item = Allocate(medicine_id=form.medicine_id.data,
                                 receiver=form.receiver.data,
                                 count=form.count.data,
                                 author=current_user._get_current_object())
        db.session.add(allocate_item)

        query = Inventory.query.filter_by(medicine_id=form.medicine_id.data).first()
        query.count -= int(form.count.data)
        query = Inventory.query.filter_by(medicine_id=form.medicine_id.data).first()
        if query.count == 0:
            db.session.delete(query)
            db.session.commit()
        else:
            db.session.add(query)
            db.session.commit()

        warning_items = Warning.query.filter_by(medicine_id=form.medicine_id.data).first()
        if warning_items:
            warning_items.count = Inventory.query.filter_by(medicine_id=form.medicine_id.data).first().count
            warning_items.warning = warning_items.count < warning_items.warning_count
            db.session.add(warning_items)
            db.session.commit()

        return redirect(url_for('.allocate'))
    page = request.args.get('page', 1, type=int)
    pagination = Allocate.query.order_by(Allocate.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    allocate_items = pagination.items
    return render_template('allocate.html', form=form, allocate_items=allocate_items, pagination=pagination)


@main.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = AccountForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        start_year, start_month, start_day = form.start_year.data, form.start_month.data, form.start_day.data
        end_year, end_month, end_day = form.end_year.data, form.end_month.data, form.end_day.data
        start_time = datetime.date(year=start_year, month=start_month, day=start_day)
        end_time = datetime.date(year=end_year, month=end_month, day=end_day)
        # purchase_query = db.session.query(Purchase).filter(Purchase.timestamp <= end_time).all()
        purchase_query = Purchase.query.filter(Purchase.timestamp <= end_time).filter(
            Purchase.timestamp >= start_time).all()
        return_query = Refund.query.filter(Refund.timestamp <= end_time).filter(Refund.timestamp >= start_time).all()
        storage_query = Storage.query.filter(Storage.timestamp <= end_time).filter(
            Storage.timestamp >= start_time).all()
        allocate_query = Allocate.query.filter(Allocate.timestamp <= end_time).filter(
            Allocate.timestamp >= start_time).all()
        return render_template('account.html', form=form, purchase_query=purchase_query, return_query=return_query,
                               storage_query=storage_query, allocate_query=allocate_query, Purchase=Purchase)
    return render_template('account.html', form=form)


@main.route("/medicine", methods=['GET', "POST"])
@login_required
def medicine():
    page = request.args.get('page', 1, type=int)
    pagination = Medicine.query.order_by(Medicine.medicine_id.asc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    medicine_items = pagination.items
    return render_template('medicine.html', medicine_items=medicine_items, pagination=pagination)


@main.route("/warning", methods=['GET', "POST"])
@login_required
def warning():
    form = InventoryWarningForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        query = Warning.query.filter_by(medicine_id=form.medicine_id.data).first()
        if not query:
            warning_items = Warning(medicine_id=form.medicine_id.data,
                                    count=Inventory.query.filter_by(medicine_id=form.medicine_id.data).first().count,
                                    warning_count=form.warning_count.data,
                                    warning=Inventory.query.filter_by(
                                        medicine_id=form.medicine_id.data).first().count < form.warning_count.data)
            db.session.add(warning_items)
            db.session.commit()
        else:
            query.warning_count = form.warning_count.data
            query.warning = Inventory.query.filter_by(
                medicine_id=form.medicine_id.data).first().count < form.warning_count.data
            db.session.add(query)
            db.session.commit()
        return redirect(url_for('.warning'))
    page = request.args.get('page', 1, type=int)
    pagination = Warning.query.order_by(Warning.medicine_id.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    warning_items = pagination.items
    return render_template('warning.html', form=form, warning_items=warning_items, pagination=pagination)
