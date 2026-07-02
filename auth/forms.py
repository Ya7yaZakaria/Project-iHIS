"""CSRF-protected authentication forms."""

from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp


USERNAME_RULE = Regexp(r"^[A-Za-z0-9_.-]+$", message="Use letters, numbers, dots, underscores, or hyphens only.")
EMAIL_RULE = Regexp(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", message="Enter a valid email address.")


class LoginForm(FlaskForm):
    identifier = StringField("Email or username", validators=[DataRequired(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(max=255)])
    remember = BooleanField("Remember me")
    submit = SubmitField("Sign in")


class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80), USERNAME_RULE])
    email = StringField("Email", validators=[DataRequired(), Length(max=255), EMAIL_RULE])
    first_name = StringField("First name", validators=[DataRequired(), Length(max=100)])
    last_name = StringField("Last name", validators=[DataRequired(), Length(max=100)])
    role_id = SelectField("Role", validators=[DataRequired()])
    password = PasswordField("Temporary password", validators=[DataRequired(), Length(min=8, max=255)])
    confirm_password = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Register user")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current password", validators=[DataRequired(), Length(max=255)])
    new_password = PasswordField("New password", validators=[DataRequired(), Length(min=8, max=255)])
    confirm_password = PasswordField("Confirm new password", validators=[DataRequired(), EqualTo("new_password")])
    submit = SubmitField("Change password")
