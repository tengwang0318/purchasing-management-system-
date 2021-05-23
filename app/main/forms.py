from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, Email, Regexp
from wtforms import ValidationError
from flask_pagedown.fields import PageDownField
from ..models import Role, User, Purchase, Storage, Inventory, Medicine


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')


class EditProfileForm(FlaskForm):
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')


class EditProfileAdminForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    username = StringField('Username', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Usernames must have only letters, numbers, dots or '
               'underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class PostForm(FlaskForm):
    body = PageDownField("What's on your mind?", validators=[DataRequired()])
    submit = SubmitField('Submit')


class CommentForm(FlaskForm):
    body = StringField('Enter your comment', validators=[DataRequired()])
    submit = SubmitField('Submit')


class PurchaseForm(FlaskForm):
    medicine_id = StringField("Enter the medicine id", validators=[DataRequired()])
    count = StringField("Enter the count", validators=[DataRequired()])
    submit = SubmitField("Submit")

    def validate_count(self, field):
        try:
            field.data = int(field.data)
        except TypeError:
            raise ValidationError("Please enter the correct count")

    def validate_medicine_id(self, field):
        medicine = Medicine.query.filter_by(medicine_id=field.data).first()
        if not medicine:
            raise ValidationError("Please enter the correct medicine id from Medicine Table ")


class RefundForm(FlaskForm):
    purchase_id = StringField("Enter the previous purchase id", validators=[DataRequired()])
    submit = SubmitField("Submit")

    def validate_purchase_id(self, field):
        truncation = Purchase.query.filter_by(id=field.data).first()
        if not truncation:
            raise ValidationError("We don't have this truncation")
        return_goods = truncation.return_goods
        if return_goods:
            raise ValidationError("Goods have been returned!")


class StorageForm(FlaskForm):
    storage_items_id = StringField("Enter the truncation ID can storage into warehouse", validators=[DataRequired()])

    submit = SubmitField("Submit")

    def validate_storage_items_id(self, field):
        truncation = Purchase.query.filter_by(id=field.data).first()
        if not truncation:
            raise ValidationError("We don't have this truncation")
        if truncation.return_goods:
            raise ValidationError("Goods have been returned!")
        if truncation.have_storage:
            raise ValidationError("Goods have been stored!")


class AllocateForm(FlaskForm):
    receiver = StringField("Enter the receiver ID", validators=[DataRequired()])
    medicine_id = StringField("Enter the medicine_id", validators=[DataRequired()])
    count = StringField("Enter the count", validators=[DataRequired()])
    submit = SubmitField("Submit")

    def validate_medicine_id(self, field):
        truncation = Inventory.query.filter_by(medicine_id=field.data).first()
        if not truncation:
            raise ValidationError("We don't have this medicine in warehouse!")

    def validate_count(self, field):
        truncation = Inventory.query.filter_by(medicine_id=self.medicine_id.data).first()
        if not truncation:
            raise ValidationError("We don't have this medicine in warehouse!")
        if truncation.count < int(field.data):
            raise ValidationError("We don't have enough medicine. ")


class AccountForm(FlaskForm):
    start_year = IntegerField("Start Year:", validators=[DataRequired()])
    start_month = IntegerField("Start Month:", validators=[DataRequired()])
    start_day = IntegerField("Start Day:", validators=[DataRequired()])
    end_year = IntegerField("End Year:", validators=[DataRequired()])
    end_month = IntegerField("End Month:", validators=[DataRequired()])
    end_day = IntegerField("End Day:", validators=[DataRequired()])
    submit = SubmitField("Submit")


class InventoryWarningForm(FlaskForm):
    medicine_id = IntegerField("Enter medicine id:", validators=[DataRequired()])
    warning_count = IntegerField("Enter medicine inventory warning:", validators=[DataRequired()])
    submit = SubmitField("Submit")

    def validate_medicine_id(self, field):
        truncation = Inventory.query.filter_by(medicine_id=self.medicine_id.data).first()
        if not truncation:
            raise ValidationError("We don't have this medicine in warehouse!")
