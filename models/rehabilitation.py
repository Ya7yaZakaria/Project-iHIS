"""Rehabilitation records, assessments, plans, sessions, and exercises."""

from extensions import db
from sqlalchemy.orm import synonym

from .base import BaseModel


care_team_members = db.Table(
    "care_team_members",
    db.Column(
        "care_team_id",
        db.String(36),
        db.ForeignKey("care_teams.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "user_id",
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column("member_role", db.String(80), nullable=False, default="member"),
)


class RehabilitationRecord(BaseModel):
    __tablename__ = "rehabilitation_records"

    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    visit_id = db.Column(db.String(36), db.ForeignKey("medical_records.id"), index=True)
    doctor_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)
    referral_source = db.Column(db.String(160))
    chief_complaint = db.Column(db.Text)
    functional_limitation = db.Column(db.Text)
    pain_score = db.Column(db.Integer)
    mobility_status = db.Column(db.String(120))
    rehabilitation_diagnosis = db.Column(db.Text)
    therapy_goals = db.Column(db.Text)
    status = db.Column(db.String(30), nullable=False, default="active", index=True)

    patient = db.relationship("Patient")
    visit = db.relationship("MedicalRecord")
    doctor = db.relationship("User", foreign_keys=[doctor_id])
    assessments = db.relationship(
        "RehabilitationAssessment",
        back_populates="rehabilitation_record",
        cascade="all, delete-orphan",
    )
    therapy_plans = db.relationship(
        "TherapyPlan",
        back_populates="rehabilitation_record",
        cascade="all, delete-orphan",
    )


class RehabilitationAssessment(BaseModel):
    __tablename__ = "rehabilitation_assessments"

    rehabilitation_record_id = db.Column(
        db.String(36),
        db.ForeignKey("rehabilitation_records.id"),
        nullable=False,
        index=True,
    )
    assessment_date = db.Column(db.Date, nullable=False, index=True)
    physical_exam = db.Column(db.Text)
    range_of_motion = db.Column(db.Text)
    muscle_power = db.Column(db.Text)
    balance_assessment = db.Column(db.Text)
    gait_assessment = db.Column(db.Text)
    neurological_findings = db.Column(db.Text)
    red_flags = db.Column(db.Text)
    functional_score = db.Column(db.Numeric(8, 2))
    assessment_summary = db.Column(db.Text)

    rehabilitation_record = db.relationship(
        "RehabilitationRecord",
        back_populates="assessments",
    )


class TherapyPlan(BaseModel):
    __tablename__ = "therapy_plans"

    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    therapist_id = db.Column(db.String(36), db.ForeignKey("physical_therapists.id"), nullable=False, index=True)
    assessment_id = db.Column(db.String(36), db.ForeignKey("therapy_assessments.id"), index=True)
    rehabilitation_record_id = db.Column(
        db.String(36),
        db.ForeignKey("rehabilitation_records.id"),
        index=True,
    )
    plan_name = db.Column(db.String(160), index=True)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date)
    goals = db.Column(db.JSON, nullable=False)
    interventions = db.Column(db.JSON)
    frequency = db.Column(db.String(120))
    duration = db.Column(db.String(120))
    modalities = db.Column(db.Text)
    exercise_program = db.Column(db.Text)
    home_program = db.Column(db.Text)
    review_date = db.Column(db.Date, index=True)
    discharge_criteria = db.Column(db.Text)
    active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    status = db.Column(db.String(30), nullable=False, default="active", index=True)

    patient = db.relationship("Patient")
    therapist = db.relationship("PhysicalTherapist")
    assessment = db.relationship("TherapyAssessment")
    rehabilitation_record = db.relationship(
        "RehabilitationRecord",
        back_populates="therapy_plans",
    )
    sessions = db.relationship(
        "TherapySession",
        back_populates="therapy_plan",
        cascade="all, delete-orphan",
    )
    exercises = db.relationship("TherapyExercise", back_populates="plan")


class TherapySession(BaseModel):
    __tablename__ = "therapy_sessions"

    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    therapy_plan_id = db.Column(
        db.String(36),
        db.ForeignKey("therapy_plans.id"),
        index=True,
    )
    therapist_id = db.Column(db.String(36), db.ForeignKey("physical_therapists.id"), nullable=False, index=True)
    therapist_user_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)
    scheduled_start = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    session_date = db.Column(db.DateTime(timezone=True), index=True)
    duration_minutes = db.Column(db.Integer)
    session_type = db.Column(db.String(60), nullable=False, default="individual")
    interventions = db.Column(db.JSON)
    response = db.Column(db.Text)
    status = db.Column(db.String(30), nullable=False, default="scheduled", index=True)
    pain_before = db.Column(db.Integer)
    pain_after = db.Column(db.Integer)
    modalities_used = db.Column(db.Text)
    exercises_performed = db.Column(db.Text)
    progress_notes = db.Column(db.Text)
    patient_tolerance = db.Column(db.Text)
    next_session_plan = db.Column(db.Text)

    therapy_plan = db.relationship("TherapyPlan", back_populates="sessions")
    patient = db.relationship("Patient")
    therapist = db.relationship("PhysicalTherapist", foreign_keys=[therapist_id])
    therapist_user = db.relationship("User", foreign_keys=[therapist_user_id])


class ExerciseLibrary(BaseModel):
    __tablename__ = "exercise_library"

    code = db.Column(db.String(50), unique=True, index=True)
    name = db.Column(db.String(160), nullable=False, index=True)
    exercise_name = synonym("name")
    category = db.Column(db.String(80), nullable=False, index=True)
    target_region = db.Column(db.String(120), index=True)
    indication = db.Column(db.Text)
    contraindications = db.Column(db.JSON)
    instructions = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255))
    video_path = db.Column(db.String(255))
    repetitions = db.Column(db.Integer)
    sets = db.Column(db.Integer)
    frequency = db.Column(db.String(120))
    media_placeholder = db.Column(db.String(255))
    active = db.Column(db.Boolean, nullable=False, default=True, index=True)


# Existing cross-module models remain registered because EMR and user-management
# depend on them. Sprint 12.1 does not otherwise change their schema.
class PhysicalTherapist(BaseModel):
    __tablename__ = "physical_therapists"
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, unique=True, index=True)
    department_id = db.Column(db.String(36), db.ForeignKey("departments.id"), index=True)
    license_number = db.Column(db.String(80), nullable=False, unique=True, index=True)
    specialty = db.Column(db.String(120), nullable=False, index=True)
    qualifications = db.Column(db.JSON)
    user = db.relationship("User")


class TherapyAssessment(BaseModel):
    __tablename__ = "therapy_assessments"
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    therapist_id = db.Column(db.String(36), db.ForeignKey("physical_therapists.id"), nullable=False, index=True)
    medical_record_id = db.Column(db.String(36), db.ForeignKey("medical_records.id"), index=True)
    assessment_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    assessment_type = db.Column(db.String(60), nullable=False, default="initial")
    pain_score = db.Column(db.Integer)
    mobility = db.Column(db.JSON)
    strength = db.Column(db.JSON)
    range_of_motion = db.Column(db.JSON)
    balance = db.Column(db.JSON)
    gait = db.Column(db.JSON)
    functional_summary = db.Column(db.Text)


class TherapyExercise(BaseModel):
    __tablename__ = "therapy_exercises"
    therapy_plan_id = db.Column(db.String(36), db.ForeignKey("therapy_plans.id"), nullable=False, index=True)
    exercise_id = db.Column(db.String(36), db.ForeignKey("exercise_library.id"), nullable=False, index=True)
    sets = db.Column(db.Integer)
    repetitions = db.Column(db.Integer)
    duration_seconds = db.Column(db.Integer)
    frequency = db.Column(db.String(80))
    progression = db.Column(db.Text)
    plan = db.relationship("TherapyPlan", back_populates="exercises")
    exercise = db.relationship("ExerciseLibrary")


class RehabilitationProgress(BaseModel):
    __tablename__ = "rehabilitation_progress"
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    therapy_plan_id = db.Column(db.String(36), db.ForeignKey("therapy_plans.id"), nullable=False, index=True)
    recorded_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    pain_score = db.Column(db.Integer)
    mobility_score = db.Column(db.Numeric(8, 2))
    strength_score = db.Column(db.Numeric(8, 2))
    balance_score = db.Column(db.Numeric(8, 2))
    compliance_percent = db.Column(db.Numeric(5, 2))
    notes = db.Column(db.Text)


class FunctionalOutcome(BaseModel):
    __tablename__ = "functional_outcomes"
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    therapy_plan_id = db.Column(db.String(36), db.ForeignKey("therapy_plans.id"), index=True)
    instrument = db.Column(db.String(120), nullable=False, index=True)
    score = db.Column(db.Numeric(10, 2), nullable=False)
    maximum_score = db.Column(db.Numeric(10, 2))
    measured_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    interpretation = db.Column(db.Text)


class Referral(BaseModel):
    __tablename__ = "referrals"
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    referring_user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    receiving_department_id = db.Column(db.String(36), db.ForeignKey("departments.id"), index=True)
    receiving_provider_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)
    referral_type = db.Column(db.String(60), nullable=False, index=True)
    reason = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), nullable=False, default="routine")
    status = db.Column(db.String(30), nullable=False, default="pending", index=True)
    referred_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)


class CareTeam(BaseModel):
    __tablename__ = "care_teams"
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    name = db.Column(db.String(160), nullable=False)
    purpose = db.Column(db.String(255))
    lead_user_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)
    members = db.relationship("User", secondary=care_team_members)


class MultidisciplinaryCase(BaseModel):
    __tablename__ = "multidisciplinary_cases"
    case_number = db.Column(db.String(50), nullable=False, unique=True, index=True)
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    care_team_id = db.Column(db.String(36), db.ForeignKey("care_teams.id"), index=True)
    medical_record_id = db.Column(db.String(36), db.ForeignKey("medical_records.id"), index=True)
    title = db.Column(db.String(160), nullable=False)
    summary = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    status = db.Column(db.String(30), nullable=False, default="open", index=True)
    meeting_at = db.Column(db.DateTime(timezone=True), index=True)
    care_team = db.relationship("CareTeam")
