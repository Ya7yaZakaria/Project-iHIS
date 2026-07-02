"""CSRF-protected forms for user and role administration."""

from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, SelectMultipleField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Optional, Regexp


USERNAME_RULE = Regexp(r"^[A-Za-z0-9_.-]+$", message="Use letters, numbers, dots, underscores, or hyphens only.")
EMAIL_RULE = Regexp(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", message="Enter a valid email address.")


class UserFieldsMixin:
    first_name = StringField("First name", validators=[DataRequired(), Length(max=100)])
    last_name = StringField("Last name", validators=[DataRequired(), Length(max=100)])
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80), USERNAME_RULE])
    email = StringField("Email", validators=[DataRequired(), Length(max=255), EMAIL_RULE])
    phone = StringField("Phone", validators=[Optional(), Length(max=40)])
    role_id = SelectField("Role", validators=[DataRequired()])
    department_id = SelectField("Department", validators=[Optional()])
    specialty_id = SelectField("Doctor specialty", validators=[Optional()])
    license_number = StringField("Medical license number", validators=[Optional(), Length(max=80)])


class CreateUserForm(FlaskForm, UserFieldsMixin):
    password = PasswordField("Temporary password", validators=[DataRequired(), Length(min=8, max=255)])
    confirm_password = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Create user")


class EditUserForm(FlaskForm, UserFieldsMixin):
    submit = SubmitField("Save changes")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("New temporary password", validators=[DataRequired(), Length(min=8, max=255)])
    confirm_password = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Reset password")


class EmptyForm(FlaskForm):
    submit = SubmitField("Confirm")


class RolePermissionsForm(FlaskForm):
    permission_ids = SelectMultipleField("Permissions", validators=[Optional()])
    submit = SubmitField("Save permissions")
