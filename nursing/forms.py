"""Simple forms for the Nursing module."""

from flask_wtf import FlaskForm
from wtforms import (
    DateTimeLocalField,
    DecimalField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class SimpleVitalSignForm(FlaskForm):
    medical_record_id = SelectField("Visit / medical record", choices=[], validators=[Optional()])

    systolic_bp = IntegerField("Systolic BP", validators=[Optional(), NumberRange(min=0, max=300)])
    diastolic_bp = IntegerField("Diastolic BP", validators=[Optional(), NumberRange(min=0, max=200)])
    pulse_bpm = IntegerField("Pulse", validators=[Optional(), NumberRange(min=0, max=300)])
    temperature_c = DecimalField("Temperature °C", places=1, validators=[Optional()])
    respiratory_rate = IntegerField("Respiratory rate", validators=[Optional(), NumberRange(min=0, max=100)])
    oxygen_saturation = DecimalField("SpO2 %", places=1, validators=[Optional(), NumberRange(min=0, max=100)])
    weight_kg = DecimalField("Weight kg", places=2, validators=[Optional(), NumberRange(min=0, max=500)])
    height_cm = DecimalField("Height cm", places=2, validators=[Optional(), NumberRange(min=0, max=300)])
    pain_score = IntegerField("Pain score", validators=[Optional(), NumberRange(min=0, max=10)])

    submit = SubmitField("Record vitals")


class SimpleNursingNoteForm(FlaskForm):
    medical_record_id = SelectField("Visit / medical record", choices=[], validators=[Optional()])
    note_type = SelectField(
        "Note type",
        choices=[
            ("progress", "Progress"),
            ("handover", "Handover"),
            ("care_plan", "Care plan"),
            ("observation", "Observation"),
        ],
        default="progress",
        validators=[DataRequired()],
    )

    subjective_note = TextAreaField("Subjective", validators=[Optional(), Length(max=3000)])
    objective_note = TextAreaField("Objective", validators=[Optional(), Length(max=3000)])
    nursing_assessment = TextAreaField("Nursing assessment", validators=[Optional(), Length(max=3000)])
    nursing_intervention = TextAreaField("Nursing intervention", validators=[Optional(), Length(max=3000)])
    response_to_care = TextAreaField("Response to care", validators=[Optional(), Length(max=3000)])
    follow_up_recommendation = TextAreaField("Follow-up recommendation", validators=[Optional(), Length(max=3000)])

    submit = SubmitField("Add nursing note")


class MedicationAdministrationForm(FlaskForm):
    patient_id = SelectField("Patient", choices=[], validators=[DataRequired()])
    medical_record_id = SelectField("Visit / medical record", choices=[], validators=[Optional()])
    prescription_item_id = SelectField("Prescription item", choices=[], validators=[Optional()])

    medication_name = StringField("Medication", validators=[DataRequired(), Length(max=160)])
    dose = StringField("Dose", validators=[Optional(), Length(max=120)])
    scheduled_time = DateTimeLocalField(
        "Scheduled time",
        format="%Y-%m-%dT%H:%M",
        validators=[Optional()],
    )
    given_at = DateTimeLocalField(
        "Given at",
        format="%Y-%m-%dT%H:%M",
        validators=[Optional()],
    )

    status = SelectField(
        "Status",
        choices=[
            ("given", "Given"),
            ("missed", "Missed"),
            ("held", "Held"),
            ("refused", "Refused"),
        ],
        default="given",
        validators=[DataRequired()],
    )

    missed_reason = TextAreaField("Missed / held / refused reason", validators=[Optional(), Length(max=2000)])
    patient_reaction = TextAreaField("Patient reaction", validators=[Optional(), Length(max=2000)])
    notes = TextAreaField("Administration notes", validators=[Optional(), Length(max=3000)])

    submit = SubmitField("Save administration")


class NursingCarePlanForm(FlaskForm):
    patient_id = SelectField("Patient", choices=[], validators=[DataRequired()])
    medical_record_id = SelectField("Visit / medical record", choices=[], validators=[Optional()])

    nursing_diagnosis = TextAreaField("Nursing diagnosis", validators=[DataRequired(), Length(max=3000)])
    goals = TextAreaField("Goals", validators=[DataRequired(), Length(max=3000)])
    interventions = TextAreaField("Interventions", validators=[DataRequired(), Length(max=3000)])
    evaluation = TextAreaField("Evaluation", validators=[Optional(), Length(max=3000)])

    status = SelectField(
        "Status",
        choices=[
            ("active", "Active"),
            ("improved", "Improved"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        default="active",
        validators=[DataRequired()],
    )

    submit = SubmitField("Save care plan")