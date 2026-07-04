"""Validated forms for the Rehabilitation module."""

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DateTimeLocalField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class RehabilitationRecordForm(FlaskForm):
    patient_id = SelectField("Patient", validators=[DataRequired()])
    visit_id = SelectField("Medical record / visit", validators=[Optional()])
    doctor_id = SelectField("Doctor", validators=[Optional()])

    referral_source = StringField(
        "Referral source",
        validators=[Optional(), Length(max=160)],
    )
    chief_complaint = TextAreaField(
        "Chief complaint",
        validators=[Optional(), Length(max=3000)],
    )
    functional_limitation = TextAreaField(
        "Functional limitation",
        validators=[Optional(), Length(max=3000)],
    )
    pain_score = IntegerField(
        "Pain score",
        validators=[Optional(), NumberRange(min=0, max=10)],
    )
    mobility_status = StringField(
        "Mobility status",
        validators=[Optional(), Length(max=120)],
    )
    rehabilitation_diagnosis = TextAreaField(
        "Rehabilitation diagnosis",
        validators=[Optional(), Length(max=3000)],
    )
    therapy_goals = TextAreaField(
        "Therapy goals",
        validators=[Optional(), Length(max=3000)],
    )
    status = SelectField(
        "Status",
        choices=[
            ("active", "Active"),
            ("completed", "Completed"),
            ("archived", "Archived"),
        ],
        default="active",
        validators=[DataRequired()],
    )

    submit = SubmitField("Save rehabilitation record")


class RehabilitationAssessmentForm(FlaskForm):
    assessment_date = DateField(
        "Assessment date",
        validators=[DataRequired()],
    )
    physical_exam = TextAreaField(
        "Physical examination",
        validators=[Optional(), Length(max=3000)],
    )
    range_of_motion = TextAreaField(
        "Range of motion",
        validators=[Optional(), Length(max=3000)],
    )
    muscle_power = TextAreaField(
        "Muscle power",
        validators=[Optional(), Length(max=3000)],
    )
    balance_assessment = TextAreaField(
        "Balance assessment",
        validators=[Optional(), Length(max=3000)],
    )
    gait_assessment = TextAreaField(
        "Gait assessment",
        validators=[Optional(), Length(max=3000)],
    )
    neurological_findings = TextAreaField(
        "Neurological findings",
        validators=[Optional(), Length(max=3000)],
    )
    red_flags = TextAreaField(
        "Red flags",
        validators=[Optional(), Length(max=3000)],
    )
    functional_score = IntegerField(
        "Functional score",
        validators=[Optional(), NumberRange(min=0, max=100)],
    )
    assessment_summary = TextAreaField(
        "Assessment summary",
        validators=[Optional(), Length(max=3000)],
    )

    submit = SubmitField("Save assessment")


class TherapyPlanForm(FlaskForm):
    therapist_id = SelectField(
        "Physical therapist",
        validators=[DataRequired()],
    )
    assessment_id = SelectField(
        "Linked therapy assessment",
        validators=[Optional()],
    )
    plan_name = StringField(
        "Plan name",
        validators=[Optional(), Length(max=160)],
    )
    start_date = DateField(
        "Start date",
        validators=[DataRequired()],
    )
    end_date = DateField(
        "End date",
        validators=[Optional()],
    )
    goals = TextAreaField(
        "Goals",
        validators=[DataRequired(), Length(max=3000)],
    )
    interventions = TextAreaField(
        "Interventions",
        validators=[Optional(), Length(max=3000)],
    )
    frequency = StringField(
        "Frequency",
        validators=[Optional(), Length(max=120)],
    )
    duration = StringField(
        "Duration",
        validators=[Optional(), Length(max=120)],
    )
    modalities = TextAreaField(
        "Treatment modalities",
        validators=[Optional(), Length(max=3000)],
    )
    exercise_program = TextAreaField(
        "Exercise program",
        validators=[Optional(), Length(max=3000)],
    )
    home_program = TextAreaField(
        "Home program",
        validators=[Optional(), Length(max=3000)],
    )
    review_date = DateField(
        "Review date",
        validators=[Optional()],
    )
    discharge_criteria = TextAreaField(
        "Discharge criteria",
        validators=[Optional(), Length(max=3000)],
    )
    active = BooleanField("Active", default=True)
    status = SelectField(
        "Status",
        choices=[
            ("draft", "Draft"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        default="active",
        validators=[DataRequired()],
    )

    submit = SubmitField("Save therapy plan")


class TherapySessionForm(FlaskForm):
    therapist_id = SelectField(
        "Physical therapist",
        validators=[DataRequired()],
    )
    therapist_user_id = SelectField(
        "Therapist user",
        validators=[Optional()],
    )
    scheduled_start = DateTimeLocalField(
        "Scheduled start",
        validators=[DataRequired()],
        format="%Y-%m-%dT%H:%M",
    )
    session_date = DateTimeLocalField(
        "Session date",
        validators=[Optional()],
        format="%Y-%m-%dT%H:%M",
    )
    duration_minutes = IntegerField(
        "Duration minutes",
        validators=[Optional(), NumberRange(min=0, max=600)],
    )
    session_type = StringField(
        "Session type",
        default="individual",
        validators=[DataRequired(), Length(max=60)],
    )
    interventions = TextAreaField(
        "Interventions",
        validators=[Optional(), Length(max=3000)],
    )
    response = TextAreaField(
        "Response",
        validators=[Optional(), Length(max=3000)],
    )
    status = SelectField(
        "Status",
        choices=[
            ("scheduled", "Scheduled"),
            ("in_progress", "In progress"),
            ("completed", "Completed"),
            ("missed", "Missed"),
            ("cancelled", "Cancelled"),
        ],
        default="scheduled",
        validators=[DataRequired()],
    )
    pain_before = IntegerField(
        "Pain before",
        validators=[Optional(), NumberRange(min=0, max=10)],
    )
    pain_after = IntegerField(
        "Pain after",
        validators=[Optional(), NumberRange(min=0, max=10)],
    )
    modalities_used = TextAreaField(
        "Modalities used",
        validators=[Optional(), Length(max=3000)],
    )
    exercises_performed = TextAreaField(
        "Exercises performed",
        validators=[Optional(), Length(max=3000)],
    )
    progress_notes = TextAreaField(
        "Progress notes",
        validators=[Optional(), Length(max=3000)],
    )
    patient_tolerance = TextAreaField(
        "Patient tolerance",
        validators=[Optional(), Length(max=3000)],
    )
    next_session_plan = TextAreaField(
        "Next session plan",
        validators=[Optional(), Length(max=3000)],
    )

    submit = SubmitField("Save therapy session")


class ExerciseLibraryForm(FlaskForm):
    code = StringField(
        "Exercise code",
        validators=[Optional(), Length(max=50)],
    )
    exercise_name = StringField(
        "Exercise name",
        validators=[DataRequired(), Length(max=160)],
    )
    category = StringField(
        "Category",
        validators=[DataRequired(), Length(max=80)],
    )
    target_region = StringField(
        "Target region",
        validators=[Optional(), Length(max=120)],
    )
    indication = TextAreaField(
        "Indication",
        validators=[Optional(), Length(max=3000)],
    )
    contraindications = TextAreaField(
        "Contraindications",
        validators=[Optional(), Length(max=3000)],
    )
    instructions = TextAreaField(
        "Instructions",
        validators=[DataRequired(), Length(max=3000)],
    )
    image_path = StringField(
        "Image path",
        validators=[Optional(), Length(max=255)],
    )
    video_path = StringField(
        "Video path",
        validators=[Optional(), Length(max=255)],
    )
    repetitions = IntegerField(
        "Repetitions",
        validators=[Optional(), NumberRange(min=0, max=1000)],
    )
    sets = IntegerField(
        "Sets",
        validators=[Optional(), NumberRange(min=0, max=1000)],
    )
    frequency = StringField(
        "Frequency",
        validators=[Optional(), Length(max=120)],
    )
    media_placeholder = StringField(
        "Media placeholder",
        validators=[Optional(), Length(max=255)],
    )
    active = BooleanField("Active", default=True)

    submit = SubmitField("Save exercise")