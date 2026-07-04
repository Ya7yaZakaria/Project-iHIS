"""Validated forms for laboratory workflows."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, DecimalField, IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class LabOrderEditForm(FlaskForm):
    priority = SelectField("Priority", choices=[("routine", "Routine"), ("urgent", "Urgent"), ("stat", "STAT")])
    department_id = SelectField("Laboratory department", choices=[], validators=[Optional()])
    assigned_to_id = SelectField("Assigned laboratory user", choices=[], validators=[Optional()])
    clinical_notes = TextAreaField("Clinical notes", validators=[Optional()])
    submit = SubmitField("Update order")


class CancelLabOrderForm(FlaskForm):
    reason = TextAreaField("Cancellation reason", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Cancel order")


class ResultForm(FlaskForm):
    component_name = StringField("Component", validators=[DataRequired(), Length(max=160)])
    result_type = SelectField("Result type", choices=[("numeric", "Numeric"), ("text", "Text"), ("qualitative", "Positive / negative")])
    value_numeric = DecimalField("Numeric result", validators=[Optional()])
    value_text = StringField("Text or qualitative result", validators=[Optional(), Length(max=255)])
    unit = StringField("Unit", validators=[Optional(), Length(max=40)])
    reference_range = StringField("Reference range", validators=[Optional(), Length(max=120)])
    abnormal_flag = SelectField("Flag", choices=[("normal", "Normal"), ("low", "Low"), ("high", "High"), ("critical", "Critical")])
    comments = TextAreaField("Laboratory comments", validators=[Optional()])
    attachment = FileField("Result attachment", validators=[Optional(), FileAllowed(["pdf", "png", "jpg", "jpeg"], "PDF or image files only.")])
    submit = SubmitField("Save result")


class LabTestForm(FlaskForm):
    code = StringField("Code", validators=[DataRequired(), Length(max=60)])
    name = StringField("Test name", validators=[DataRequired(), Length(max=160)])
    category = StringField("Category", validators=[DataRequired(), Length(max=100)])
    unit = StringField("Default unit", validators=[Optional(), Length(max=40)])
    reference_range = StringField("Reference range", validators=[Optional(), Length(max=120)])
    sample_type = StringField("Sample type", validators=[Optional(), Length(max=80)])
    turnaround_minutes = IntegerField("Turnaround time (minutes)", validators=[Optional(), NumberRange(min=1)])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save test")
