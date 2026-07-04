"""Appointment and reception forms."""

from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    DateTimeLocalField,
    HiddenField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, Optional


class AppointmentSearchForm(FlaskForm):
    search = StringField("Search", validators=[Optional(), Length(max=120)])
    status = SelectField("Status", validators=[Optional()], choices=[])
    doctor_id = SelectField("Doctor", validators=[Optional()], choices=[])
    department_id = SelectField("Department", validators=[Optional()], choices=[])
    date = DateField("Date", validators=[Optional()])
    submit = SubmitField("Filter")


class AppointmentForm(FlaskForm):
    patient_id = SelectField("Patient", validators=[DataRequired()], choices=[])
    doctor_id = SelectField("Doctor", validators=[Optional()], choices=[])
    department_id = SelectField("Department", validators=[Optional()], choices=[])
    scheduled_start = DateTimeLocalField(
        "Start time",
        validators=[DataRequired()],
        format="%Y-%m-%dT%H:%M",
    )
    scheduled_end = DateTimeLocalField(
        "End time",
        validators=[Optional()],
        format="%Y-%m-%dT%H:%M",
    )
    appointment_type = SelectField(
        "Appointment type",
        validators=[DataRequired()],
        choices=[
            ("consultation", "Consultation"),
            ("follow_up", "Follow-up"),
            ("urgent", "Urgent"),
            ("procedure", "Procedure"),
            ("review", "Review"),
        ],
    )
    status = SelectField(
        "Status",
        validators=[DataRequired()],
        choices=[
            ("booked", "Booked"),
            ("confirmed", "Confirmed"),
            ("arrived", "Arrived"),
            ("waiting", "Waiting"),
            ("in_consultation", "In Consultation"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
            ("no_show", "No-show"),
            ("follow_up_scheduled", "Follow-up Scheduled"),
        ],
    )
    reason = TextAreaField("Reason", validators=[Optional(), Length(max=1000)])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=1000)])
    reception_notes = TextAreaField(
        "Reception notes",
        validators=[Optional(), Length(max=1000)],
    )
    submit = SubmitField("Save appointment")


class RescheduleForm(FlaskForm):
    scheduled_start = DateTimeLocalField(
        "New start time",
        validators=[DataRequired()],
        format="%Y-%m-%dT%H:%M",
    )
    scheduled_end = DateTimeLocalField(
        "New end time",
        validators=[Optional()],
        format="%Y-%m-%dT%H:%M",
    )
    submit = SubmitField("Reschedule")


class CancelAppointmentForm(FlaskForm):
    reason = TextAreaField(
        "Cancellation reason",
        validators=[Optional(), Length(max=1000)],
    )
    submit = SubmitField("Cancel appointment")


class CheckInForm(FlaskForm):
    appointment_id = HiddenField("Appointment ID", validators=[DataRequired()])
    reception_notes = TextAreaField(
        "Reception notes",
        validators=[Optional(), Length(max=1000)],
    )
    submit = SubmitField("Mark arrived")


class NoShowForm(FlaskForm):
    appointment_id = HiddenField("Appointment ID", validators=[DataRequired()])
    submit = SubmitField("Mark no-show")


class StartConsultationForm(FlaskForm):
    appointment_id = HiddenField("Appointment ID", validators=[DataRequired()])
    submit = SubmitField("Start consultation")


class CompleteAppointmentForm(FlaskForm):
    appointment_id = HiddenField("Appointment ID", validators=[DataRequired()])
    submit = SubmitField("Complete appointment")


class FollowUpForm(FlaskForm):
    scheduled_start = DateTimeLocalField(
        "Follow-up date and time",
        validators=[DataRequired()],
        format="%Y-%m-%dT%H:%M",
    )
    scheduled_end = DateTimeLocalField(
        "End time",
        validators=[Optional()],
        format="%Y-%m-%dT%H:%M",
    )
    submit = SubmitField("Schedule follow-up")
