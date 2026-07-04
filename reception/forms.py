"""Forms for Phase 14 Reception module."""

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
from wtforms.validators import DataRequired, Email, Length, Optional


class ReceptionPatientSearchForm(FlaskForm):
    query = StringField(
        "Search",
        validators=[Optional(), Length(max=120)],
        render_kw={"placeholder": "Name, phone, file number, or email"},
    )
    phone = StringField("Phone", validators=[Optional(), Length(max=40)])
    date_of_birth = DateField("Date of birth", validators=[Optional()])
    submit = SubmitField("Search")


class ReceptionPatientRegistrationForm(FlaskForm):
    medical_record_number = StringField("File number", validators=[DataRequired(), Length(max=50)])
    first_name = StringField("First name", validators=[DataRequired(), Length(max=100)])
    last_name = StringField("Last name", validators=[DataRequired(), Length(max=100)])
    date_of_birth = DateField("Date of birth", validators=[DataRequired()])
    sex_at_birth = SelectField(
        "Sex at birth",
        choices=[
            ("female", "Female"),
            ("male", "Male"),
            ("other", "Other"),
            ("unknown", "Unknown"),
        ],
        validators=[DataRequired()],
    )
    phone = StringField("Phone", validators=[Optional(), Length(max=40)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=255)])
    address = TextAreaField("Address", validators=[Optional(), Length(max=1000)])

    national_id = StringField(
        "National ID placeholder",
        validators=[Optional(), Length(max=40)],
        description="Placeholder only. Not stored until national ID field is added to Patient model.",
    )

    submit = SubmitField("Register patient")


class ReceptionDemographicsForm(FlaskForm):
    patient_id = HiddenField(validators=[DataRequired()])
    first_name = StringField("First name", validators=[DataRequired(), Length(max=100)])
    last_name = StringField("Last name", validators=[DataRequired(), Length(max=100)])
    date_of_birth = DateField("Date of birth", validators=[DataRequired()])
    sex_at_birth = SelectField(
        "Sex at birth",
        choices=[
            ("female", "Female"),
            ("male", "Male"),
            ("other", "Other"),
            ("unknown", "Unknown"),
        ],
        validators=[DataRequired()],
    )
    phone = StringField("Phone", validators=[Optional(), Length(max=40)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=255)])
    address = TextAreaField("Address", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Update demographics")


class ReceptionCheckInForm(FlaskForm):
    appointment_id = SelectField("Appointment", choices=[], validators=[DataRequired()])
    reception_notes = TextAreaField("Reception notes", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Check in")


class QueueStatusForm(FlaskForm):
    appointment_id = HiddenField(validators=[DataRequired()])
    status = SelectField(
        "Queue status",
        choices=[
            ("waiting", "Waiting"),
            ("called", "Called placeholder"),
            ("in_consultation", "In consultation"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
            ("no_show", "No-show"),
        ],
        validators=[DataRequired()],
    )
    reception_notes = TextAreaField("Reception notes", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Update status")


class QueueReorderForm(FlaskForm):
    appointment_id = HiddenField(validators=[DataRequired()])
    queue_number = StringField("New queue number", validators=[DataRequired(), Length(max=10)])
    submit = SubmitField("Reorder")


class WalkInForm(FlaskForm):
    patient_id = SelectField("Existing patient", choices=[], validators=[Optional()])
    medical_record_number = StringField("New patient file number", validators=[Optional(), Length(max=50)])
    first_name = StringField("First name", validators=[Optional(), Length(max=100)])
    last_name = StringField("Last name", validators=[Optional(), Length(max=100)])
    date_of_birth = DateField("Date of birth", validators=[Optional()])
    sex_at_birth = SelectField(
        "Sex at birth",
        choices=[
            ("", "Select if registering new patient"),
            ("female", "Female"),
            ("male", "Male"),
            ("other", "Other"),
            ("unknown", "Unknown"),
        ],
        validators=[Optional()],
    )
    phone = StringField("Phone", validators=[Optional(), Length(max=40)])
    reason = TextAreaField("Reason", validators=[Optional(), Length(max=2000)])
    reception_notes = TextAreaField("Reception notes", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Create walk-in")


class FollowUpBookingForm(FlaskForm):
    patient_id = SelectField("Patient", choices=[], validators=[DataRequired()])
    follow_up_of_id = SelectField("Follow-up of appointment", choices=[], validators=[Optional()])
    scheduled_start = DateTimeLocalField(
        "Follow-up date/time",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired()],
    )
    doctor_id = SelectField("Doctor placeholder", choices=[], validators=[Optional()])
    reason = TextAreaField("Reason", validators=[Optional(), Length(max=2000)])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Book follow-up")


class BillingInitiationForm(FlaskForm):
    patient_id = SelectField("Patient", choices=[], validators=[DataRequired()])
    appointment_id = SelectField("Appointment", choices=[], validators=[Optional()])
    status = SelectField(
        "Payment status placeholder",
        choices=[
            ("not_started", "Not started"),
            ("pending", "Pending"),
            ("paid", "Paid"),
            ("cancelled", "Cancelled"),
        ],
        default="pending",
        validators=[DataRequired()],
    )
    notes = TextAreaField("Billing notes", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Start billing placeholder")