"""Physical therapy, rehabilitation, referral, and care-team models."""

from extensions import db
from .base import BaseModel


care_team_members = db.Table(
    "care_team_members",
    db.Column("care_team_id", db.String(36), db.ForeignKey("care_teams.id", ondelete="CASCADE"), primary_key=True),
    db.Column("user_id", db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("member_role", db.String(80), nullable=False, default="member"),
)


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


class TherapyPlan(BaseModel):
    __tablename__ = "therapy_plans"
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    therapist_id = db.Column(db.String(36), db.ForeignKey("physical_therapists.id"), nullable=False, index=True)
    assessment_id = db.Column(db.String(36), db.ForeignKey("therapy_assessments.id"), index=True)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date)
    goals = db.Column(db.JSON, nullable=False)
    interventions = db.Column(db.JSON)
    frequency = db.Column(db.String(120))
    status = db.Column(db.String(30), nullable=False, default="active", index=True)
    exercises = db.relationship("TherapyExercise", back_populates="plan")
    sessions = db.relationship("TherapySession", back_populates="plan")


class TherapySession(BaseModel):
    __tablename__ = "therapy_sessions"
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    therapist_id = db.Column(db.String(36), db.ForeignKey("physical_therapists.id"), nullable=False, index=True)
    therapy_plan_id = db.Column(db.String(36), db.ForeignKey("therapy_plans.id"), index=True)
    scheduled_start = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    duration_minutes = db.Column(db.Integer)
    session_type = db.Column(db.String(60), nullable=False, default="individual")
    interventions = db.Column(db.JSON)
    response = db.Column(db.Text)
    status = db.Column(db.String(30), nullable=False, default="scheduled", index=True)
    plan = db.relationship("TherapyPlan", back_populates="sessions")


class ExerciseLibrary(BaseModel):
    __tablename__ = "exercise_library"
    code = db.Column(db.String(50), unique=True, index=True)
    name = db.Column(db.String(160), nullable=False, index=True)
    category = db.Column(db.String(80), nullable=False, index=True)
    instructions = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255))
    video_path = db.Column(db.String(255))
    contraindications = db.Column(db.JSON)


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
