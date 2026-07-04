"""Radiology forms."""

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateTimeLocalField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, Optional


MODALITY_CHOICES = [
    ("X-ray", "X-ray"),
    ("Ultrasound", "Ultrasound"),
    ("CT", "CT"),
    ("MRI", "MRI"),
    ("Mammography", "Mammography"),
    ("Doppler", "Doppler"),
    ("Other", "Other"),
]

ORDER_STATUS_CHOICES = [
    ("requested", "Requested"),
    ("scheduled", "Scheduled"),
    ("patient_arrived", "Patient Arrived"),
    ("imaging_performed", "Imaging Performed"),
    ("report_drafted", "Report Drafted"),
    ("report_verified", "Report Verified"),
    ("reviewed_by_doctor", "Reviewed by Doctor"),
    ("cancelled", "Cancelled"),
]


class ImagingStudyForm(FlaskForm):
    name = StringField(
        "Study Name",
        validators=[DataRequired(), Length(max=160)],
    )

    modality = SelectField(
        "Modality",
        choices=MODALITY_CHOICES,
        validators=[DataRequired()],
    )

    body_region = StringField(
        "Body Region",
        validators=[DataRequired(), Length(max=120)],
    )

    preparation_instructions = TextAreaField(
        "Preparation Instructions",
        validators=[Optional()],
    )

    description = TextAreaField(
        "Description",
        validators=[Optional()],
    )

    is_active = BooleanField(
        "Active",
        default=True,
    )

    submit = SubmitField("Save")


class RadiologyOrderForm(FlaskForm):
    patient_id = SelectField(
        "Patient",
        coerce=str,
        validators=[DataRequired()],
    )

    doctor_id = SelectField(
        "Requesting Doctor",
        coerce=str,
        validators=[DataRequired()],
    )

    imaging_study_id = SelectField(
        "Imaging Study",
        coerce=str,
        validators=[Optional()],
    )

    modality = SelectField(
        "Modality",
        choices=MODALITY_CHOICES,
        validators=[DataRequired()],
    )

    body_part = StringField(
        "Body Part",
        validators=[DataRequired()],
    )

    priority = SelectField(
        "Priority",
        choices=[
            ("routine", "Routine"),
            ("urgent", "Urgent"),
            ("stat", "STAT"),
        ],
        validators=[DataRequired()],
    )

    clinical_indication = TextAreaField(
        "Clinical Indication",
        validators=[Optional()],
    )

    submit = SubmitField("Create Order")


class ScheduleStudyForm(FlaskForm):
    scheduled_at = DateTimeLocalField(
        "Scheduled Date & Time",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired()],
    )

    assigned_radiology_user_id = SelectField(
        "Assigned Radiology User",
        coerce=str,
        validators=[Optional()],
    )

    submit = SubmitField("Schedule")


class ReportForm(FlaskForm):
    clinical_indication = TextAreaField(
        "Clinical Indication",
        validators=[Optional()],
    )

    technique = TextAreaField(
        "Technique",
        validators=[Optional()],
    )

    findings = TextAreaField(
        "Findings",
        validators=[DataRequired()],
    )

    impression = TextAreaField(
        "Impression",
        validators=[DataRequired()],
    )

    recommendations = TextAreaField(
        "Recommendations",
        validators=[Optional()],
    )

    is_abnormal = BooleanField(
        "Abnormal Finding",
    )

    is_critical = BooleanField(
        "Critical Finding",
    )

    submit = SubmitField("Save Report")


class VerifyReportForm(FlaskForm):
    submit = SubmitField("Verify Report")


class RadiologySearchForm(FlaskForm):
    search = StringField(
        "Search",
        validators=[Optional()],
    )

    modality = SelectField(
        "Modality",
        choices=[("", "All")] + MODALITY_CHOICES,
        validators=[Optional()],
    )

    status = SelectField(
        "Status",
        choices=[("", "All")] + ORDER_STATUS_CHOICES,
        validators=[Optional()],
    )

    submit = SubmitField("Search")


class CancelRadiologyOrderForm(FlaskForm):
    reason = TextAreaField(
        "Cancellation Reason",
        validators=[Optional(), Length(max=1000)],
    )

    submit = SubmitField("Cancel Order")