```python
Role.insert_roles()
Medicine.insert_medicine()
admin_role = Role.query.filter_by(name="Administrator").first()
default_role = Role.query.filter_by(default=True).first()
for u in User.query.all():
	if u.role is None:
		if u.email == app.config['FLASKY_ADMIN']:
			u.role = admin_role
		else:
			u.role = default_role

```

```python
db.session.commit()
```
```python

```
