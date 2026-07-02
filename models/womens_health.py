"""Women's Health longitudinal journey, fertility, and imaging models."""

from extensions import db
from .base import BaseModel


class WomensHealthProfile(BaseModel):
    __tablename__ = "womens_health_profiles"
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, unique=True, index=True)
    blood_group = db.Column(db.String(5))
    rhesus_status = db.Column(db.String(12))
    menarche_age = db.Column(db.Integer)
    cycle_pattern = db.Column(db.String(80))
    contraception = db.Column(db.String(120))
    gynecologic_history = db.Column(db.JSON)
    family_history = db.Column(db.JSON)
    patient = db.relationship("Patient", back_populates="womens_health_profile")
    pregnancies = db.relationship("Pregnancy", back_populates="profile")
    gynecology_journeys = db.relationship("GynecologyJourney", back_populates="profile")
    infertility_journeys = db.relationship("InfertilityJourney", back_populates="profile")


class Pregnancy(BaseModel):
    __tablename__ = "pregnancies"
    profile_id = db.Column(db.String(36), db.ForeignKey("womens_health_profiles.id"), nullable=False, index=True)
    pregnancy_number = db.Column(db.Integer, nullable=False)
    gravida = db.Column(db.Integer)
    para = db.Column(db.Integer)
    gtpal = db.Column(db.String(20))
    lmp = db.Column(db.Date, index=True)
    estimated_due_date = db.Column(db.Date, index=True)
    risk_category = db.Column(db.String(30), nullable=False, default="low", index=True)
    status = db.Column(db.String(30), nullable=False, default="ongoing", index=True)
    maternal_conditions = db.Column(db.JSON)
    fetal_conditions = db.Column(db.JSON)
    delivery_plan = db.Column(db.Text)
    outcome = db.Column(db.String(120))
    profile = db.relationship("WomensHealthProfile", back_populates="pregnancies")
    visits = db.relationship("PregnancyVisit", back_populates="pregnancy")
    antenatal_visits = db.relationship("AntenatalVisit", back_populates="pregnancy")
    ultrasound_reports = db.relationship("WomensUltrasoundReport", back_populates="pregnancy")


class PregnancyVisit(BaseModel):
    __tablename__ = "pregnancy_visits"
    pregnancy_id = db.Column(db.String(36), db.ForeignKey("pregnancies.id"), nullable=False, index=True)
    medical_record_id = db.Column(db.String(36), db.ForeignKey("medical_records.id"), index=True)
    doctor_id = db.Column(db.String(36), db.ForeignKey("doctors.id"), index=True)
    visit_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    visit_type = db.Column(db.String(60), nullable=False, default="obstetric")
    gestational_age_weeks = db.Column(db.Integer)
    gestational_age_days = db.Column(db.Integer)
    assessment = db.Column(db.Text)
    plan = db.Column(db.Text)
    next_follow_up = db.Column(db.Date)
    pregnancy = db.relationship("Pregnancy", back_populates="visits")


class AntenatalVisit(BaseModel):
    __tablename__ = "antenatal_visits"
    pregnancy_id = db.Column(db.String(36), db.ForeignKey("pregnancies.id"), nullable=False, index=True)
    pregnancy_visit_id = db.Column(db.String(36), db.ForeignKey("pregnancy_visits.id"), unique=True, index=True)
    visit_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    weight_kg = db.Column(db.Numeric(7, 2))
    systolic_bp = db.Column(db.Integer)
    diastolic_bp = db.Column(db.Integer)
    fundal_height_cm = db.Column(db.Numeric(5, 2))
    fetal_heart_rate = db.Column(db.Integer)
    fetal_movement = db.Column(db.String(80))
    presentation = db.Column(db.String(60))
    urine_findings = db.Column(db.JSON)
    pregnancy = db.relationship("Pregnancy", back_populates="antenatal_visits")


class ObstetricHistory(BaseModel):
    __tablename__ = "obstetric_history"
    profile_id = db.Column(db.String(36), db.ForeignKey("womens_health_profiles.id"), nullable=False, index=True)
    pregnancy_order = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer)
    gestational_age_weeks = db.Column(db.Integer)
    outcome = db.Column(db.String(80), nullable=False, index=True)
    delivery_mode = db.Column(db.String(80))
    neonatal_outcome = db.Column(db.String(160))
    complications = db.Column(db.JSON)


class DeliveryRecord(BaseModel):
    __tablename__ = "delivery_records"
    pregnancy_id = db.Column(db.String(36), db.ForeignKey("pregnancies.id"), nullable=False, unique=True, index=True)
    delivered_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    gestational_age_weeks = db.Column(db.Integer)
    delivery_mode = db.Column(db.String(80), nullable=False, index=True)
    indication = db.Column(db.Text)
    place_of_delivery = db.Column(db.String(160))
    attendants = db.Column(db.JSON)
    maternal_complications = db.Column(db.JSON)
    newborns = db.Column(db.JSON)
    outcome = db.Column(db.String(80), nullable=False)


class PostpartumVisit(BaseModel):
    __tablename__ = "postpartum_visits"
    pregnancy_id = db.Column(db.String(36), db.ForeignKey("pregnancies.id"), nullable=False, index=True)
    medical_record_id = db.Column(db.String(36), db.ForeignKey("medical_records.id"), index=True)
    visit_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    maternal_assessment = db.Column(db.Text)
    wound_assessment = db.Column(db.Text)
    lactation_status = db.Column(db.String(80))
    contraception_plan = db.Column(db.String(160))
    mood_screen = db.Column(db.JSON)
    follow_up_plan = db.Column(db.Text)


class GynecologyJourney(BaseModel):
    __tablename__ = "gynecology_journeys"
    journey_number = db.Column(db.String(50), nullable=False, unique=True, index=True)
    profile_id = db.Column(db.String(36), db.ForeignKey("womens_health_profiles.id"), nullable=False, index=True)
    primary_condition = db.Column(db.String(160), nullable=False, index=True)
    started_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    ended_at = db.Column(db.DateTime(timezone=True))
    status = db.Column(db.String(30), nullable=False, default="active", index=True)
    summary = db.Column(db.Text)
    profile = db.relationship("WomensHealthProfile", back_populates="gynecology_journeys")
    visits = db.relationship("GynecologyVisit", back_populates="journey")


class GynecologyVisit(BaseModel):
    __tablename__ = "gynecology_visits"
    journey_id = db.Column(db.String(36), db.ForeignKey("gynecology_journeys.id"), nullable=False, index=True)
    medical_record_id = db.Column(db.String(36), db.ForeignKey("medical_records.id"), index=True)
    doctor_id = db.Column(db.String(36), db.ForeignKey("doctors.id"), index=True)
    visit_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    visit_type = db.Column(db.String(60), nullable=False, default="gynecology")
    symptoms = db.Column(db.JSON)
    examination = db.Column(db.Text)
    assessment = db.Column(db.Text)
    plan = db.Column(db.Text)
    journey = db.relationship("GynecologyJourney", back_populates="visits")


class InfertilityJourney(BaseModel):
    __tablename__ = "infertility_journeys"
    journey_number = db.Column(db.String(50), nullable=False, unique=True, index=True)
    profile_id = db.Column(db.String(36), db.ForeignKey("womens_health_profiles.id"), nullable=False, index=True)
    infertility_type = db.Column(db.String(30), nullable=False, index=True)
    duration_months = db.Column(db.Integer)
    female_factor = db.Column(db.JSON)
    male_factor = db.Column(db.JSON)
    combined_factor = db.Column(db.Boolean, nullable=False, default=False)
    unexplained = db.Column(db.Boolean, nullable=False, default=False)
    started_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default="active", index=True)
    outcome = db.Column(db.String(120))
    profile = db.relationship("WomensHealthProfile", back_populates="infertility_journeys")
    cycles = db.relationship("InfertilityCycle", back_populates="journey")
    partner_records = db.relationship("PartnerRecord", back_populates="journey")


class InfertilityCycle(BaseModel):
    __tablename__ = "infertility_cycles"
    __table_args__ = (db.UniqueConstraint("journey_id", "cycle_number", name="uq_infertility_journey_cycle"),)
    journey_id = db.Column(db.String(36), db.ForeignKey("infertility_journeys.id"), nullable=False, index=True)
    cycle_number = db.Column(db.Integer, nullable=False)
    cycle_type = db.Column(db.String(60), nullable=False, index=True)
    cycle_start_date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default="planned", index=True)
    protocol = db.Column(db.JSON)
    trigger_at = db.Column(db.DateTime(timezone=True))
    outcome = db.Column(db.String(80))
    cancellation_reason = db.Column(db.Text)
    journey = db.relationship("InfertilityJourney", back_populates="cycles")


class PartnerRecord(BaseModel):
    __tablename__ = "partner_records"
    journey_id = db.Column(db.String(36), db.ForeignKey("infertility_journeys.id"), nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date)
    occupation = db.Column(db.String(120))
    smoking_status = db.Column(db.String(40))
    fertility_history = db.Column(db.Text)
    previous_procedures = db.Column(db.JSON)
    previous_surgeries = db.Column(db.JSON)
    current_medications = db.Column(db.JSON)
    journey = db.relationship("InfertilityJourney", back_populates="partner_records")
    semen_analyses = db.relationship("SemenAnalysis", back_populates="partner")


class SemenAnalysis(BaseModel):
    __tablename__ = "semen_analyses"
    partner_id = db.Column(db.String(36), db.ForeignKey("partner_records.id"), nullable=False, index=True)
    collected_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    volume_ml = db.Column(db.Numeric(7, 2))
    concentration_million_ml = db.Column(db.Numeric(10, 2))
    total_motility_percent = db.Column(db.Numeric(5, 2))
    progressive_motility_percent = db.Column(db.Numeric(5, 2))
    normal_morphology_percent = db.Column(db.Numeric(5, 2))
    interpretation = db.Column(db.Text)
    raw_results = db.Column(db.JSON)
    partner = db.relationship("PartnerRecord", back_populates="semen_analyses")


class FolliculometryRecord(BaseModel):
    __tablename__ = "folliculometry_records"
    infertility_cycle_id = db.Column(db.String(36), db.ForeignKey("infertility_cycles.id"), nullable=False, index=True)
    scan_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    cycle_day = db.Column(db.Integer, nullable=False)
    endometrium_mm = db.Column(db.Numeric(6, 2))
    endometrium_pattern = db.Column(db.String(80))
    notes = db.Column(db.Text)
    measurements = db.relationship("FollicleMeasurement", back_populates="record")


class FollicleMeasurement(BaseModel):
    __tablename__ = "follicle_measurements"
    folliculometry_record_id = db.Column(db.String(36), db.ForeignKey("folliculometry_records.id"), nullable=False, index=True)
    ovary = db.Column(db.String(10), nullable=False)
    follicle_number = db.Column(db.Integer, nullable=False)
    diameter_mm = db.Column(db.Numeric(6, 2), nullable=False)
    dimensions = db.Column(db.JSON)
    record = db.relationship("FolliculometryRecord", back_populates="measurements")


class OvulationInductionCycle(BaseModel):
    __tablename__ = "ovulation_induction_cycles"
    infertility_cycle_id = db.Column(db.String(36), db.ForeignKey("infertility_cycles.id"), nullable=False, unique=True, index=True)
    medication_protocol = db.Column(db.JSON)
    stimulation_start_date = db.Column(db.Date)
    trigger_medication = db.Column(db.String(120))
    trigger_at = db.Column(db.DateTime(timezone=True))
    luteal_support = db.Column(db.JSON)
    response = db.Column(db.String(120))


class IUICycle(BaseModel):
    __tablename__ = "iui_cycles"
    infertility_cycle_id = db.Column(db.String(36), db.ForeignKey("infertility_cycles.id"), nullable=False, unique=True, index=True)
    partner_id = db.Column(db.String(36), db.ForeignKey("partner_records.id"), index=True)
    performed_at = db.Column(db.DateTime(timezone=True), index=True)
    semen_analysis_id = db.Column(db.String(36), db.ForeignKey("semen_analyses.id"), index=True)
    post_wash_count = db.Column(db.Numeric(10, 2))
    luteal_support = db.Column(db.JSON)
    pregnancy_test_date = db.Column(db.Date)
    outcome = db.Column(db.String(80))


class FertilityMedicationProtocol(BaseModel):
    __tablename__ = "fertility_medication_protocols"
    infertility_cycle_id = db.Column(db.String(36), db.ForeignKey("infertility_cycles.id"), nullable=False, index=True)
    medication_id = db.Column(db.String(36), db.ForeignKey("medications.id"), index=True)
    medication_name = db.Column(db.String(160), nullable=False)
    dose = db.Column(db.String(80), nullable=False)
    route = db.Column(db.String(60))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    instructions = db.Column(db.Text)


class WomensUltrasoundReport(BaseModel):
    __tablename__ = "womens_ultrasound_reports"
    report_number = db.Column(db.String(50), nullable=False, unique=True, index=True)
    profile_id = db.Column(db.String(36), db.ForeignKey("womens_health_profiles.id"), nullable=False, index=True)
    pregnancy_id = db.Column(db.String(36), db.ForeignKey("pregnancies.id"), index=True)
    gynecology_journey_id = db.Column(db.String(36), db.ForeignKey("gynecology_journeys.id"), index=True)
    infertility_journey_id = db.Column(db.String(36), db.ForeignKey("infertility_journeys.id"), index=True)
    medical_record_id = db.Column(db.String(36), db.ForeignKey("medical_records.id"), index=True)
    radiology_order_id = db.Column(db.String(36), db.ForeignKey("radiology_orders.id"), index=True)
    performed_by_id = db.Column(db.String(36), db.ForeignKey("doctors.id"), index=True)
    scan_type = db.Column(db.String(80), nullable=False, index=True)
    performed_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    findings = db.Column(db.Text)
    impression = db.Column(db.Text)
    measurements = db.Column(db.JSON)
    attachments = db.Column(db.JSON)
    status = db.Column(db.String(30), nullable=False, default="draft", index=True)
    pregnancy = db.relationship("Pregnancy", back_populates="ultrasound_reports")
    fetal_biometry = db.relationship("FetalBiometry", back_populates="report")
    doppler_records = db.relationship("FetalDopplerRecord", back_populates="report")


class FetalBiometry(BaseModel):
    __tablename__ = "fetal_biometry"
    ultrasound_report_id = db.Column(db.String(36), db.ForeignKey("womens_ultrasound_reports.id"), nullable=False, index=True)
    fetus_label = db.Column(db.String(20), nullable=False, default="A")
    biparietal_diameter_mm = db.Column(db.Numeric(7, 2))
    head_circumference_mm = db.Column(db.Numeric(7, 2))
    abdominal_circumference_mm = db.Column(db.Numeric(7, 2))
    femur_length_mm = db.Column(db.Numeric(7, 2))
    estimated_fetal_weight_g = db.Column(db.Numeric(9, 2))
    estimated_gestational_age_days = db.Column(db.Integer)
    percentile = db.Column(db.Numeric(5, 2))
    report = db.relationship("WomensUltrasoundReport", back_populates="fetal_biometry")


class FetalDopplerRecord(BaseModel):
    __tablename__ = "fetal_doppler_records"
    ultrasound_report_id = db.Column(db.String(36), db.ForeignKey("womens_ultrasound_reports.id"), nullable=False, index=True)
    vessel = db.Column(db.String(80), nullable=False, index=True)
    fetus_label = db.Column(db.String(20), nullable=False, default="A")
    pulsatility_index = db.Column(db.Numeric(8, 3))
    resistance_index = db.Column(db.Numeric(8, 3))
    systolic_diastolic_ratio = db.Column(db.Numeric(8, 3))
    peak_systolic_velocity = db.Column(db.Numeric(9, 3))
    cerebroplacental_ratio = db.Column(db.Numeric(8, 3))
    interpretation = db.Column(db.String(160))
    report = db.relationship("WomensUltrasoundReport", back_populates="doppler_records")


class GynecologyUltrasoundRecord(BaseModel):
    __tablename__ = "gynecology_ultrasound_records"
    ultrasound_report_id = db.Column(db.String(36), db.ForeignKey("womens_ultrasound_reports.id"), nullable=False, unique=True, index=True)
    uterine_position = db.Column(db.String(80))
    uterine_dimensions = db.Column(db.JSON)
    endometrium_mm = db.Column(db.Numeric(6, 2))
    endometrium_description = db.Column(db.String(160))
    right_ovary = db.Column(db.JSON)
    left_ovary = db.Column(db.JSON)
    adnexal_findings = db.Column(db.JSON)
    free_fluid = db.Column(db.String(120))


class PregnancyRiskFlag(BaseModel):
    __tablename__ = "pregnancy_risk_flags"
    pregnancy_id = db.Column(db.String(36), db.ForeignKey("pregnancies.id"), nullable=False, index=True)
    code = db.Column(db.String(60), nullable=False, index=True)
    label = db.Column(db.String(160), nullable=False)
    severity = db.Column(db.String(20), nullable=False, index=True)
    identified_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    resolved_at = db.Column(db.DateTime(timezone=True))
    source = db.Column(db.String(80))
    notes = db.Column(db.Text)


class WomensHealthCalculation(BaseModel):
    __tablename__ = "womens_health_calculations"
    profile_id = db.Column(db.String(36), db.ForeignKey("womens_health_profiles.id"), nullable=False, index=True)
    pregnancy_id = db.Column(db.String(36), db.ForeignKey("pregnancies.id"), index=True)
    infertility_cycle_id = db.Column(db.String(36), db.ForeignKey("infertility_cycles.id"), index=True)
    calculation_type = db.Column(db.String(80), nullable=False, index=True)
    inputs = db.Column(db.JSON, nullable=False)
    result = db.Column(db.JSON, nullable=False)
    calculated_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    calculated_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)


class WomensHealthTimelineEvent(BaseModel):
    __tablename__ = "womens_health_timeline_events"
    profile_id = db.Column(db.String(36), db.ForeignKey("womens_health_profiles.id"), nullable=False, index=True)
    pregnancy_id = db.Column(db.String(36), db.ForeignKey("pregnancies.id"), index=True)
    gynecology_journey_id = db.Column(db.String(36), db.ForeignKey("gynecology_journeys.id"), index=True)
    infertility_journey_id = db.Column(db.String(36), db.ForeignKey("infertility_journeys.id"), index=True)
    event_type = db.Column(db.String(80), nullable=False, index=True)
    event_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    title = db.Column(db.String(160), nullable=False)
    summary = db.Column(db.Text)
    source_type = db.Column(db.String(80))
    source_id = db.Column(db.String(36), index=True)
    data = db.Column(db.JSON)
