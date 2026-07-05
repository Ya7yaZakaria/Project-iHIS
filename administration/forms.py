"""CSRF-protected administration forms."""

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


DEPARTMENT_TYPES = (
    "Clinical", "Laboratory", "Radiology", "Pharmacy", "Reception", "Nursing",
    "Administration", "Rehabilitation", "Dentistry", "Women’s Health",
)


class DepartmentForm(FlaskForm):
    code = StringField("Code", validators=[DataRequired(), Length(max=30)])
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    department_type = SelectField("Department type", choices=[(x, x) for x in DEPARTMENT_TYPES], validators=[DataRequired()])
    location = StringField("Location", validators=[Optional(), Length(max=120)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Save department")


class StaffAssignmentForm(FlaskForm):
    user_id = SelectField("Staff member", validators=[DataRequired()])
    department_id = SelectField("Department", validators=[DataRequired()])
    specialty_id = SelectField("Doctor specialty", validators=[Optional()])
    submit = SubmitField("Assign staff")


class EmptyForm(FlaskForm):
    submit = SubmitField("Confirm")
