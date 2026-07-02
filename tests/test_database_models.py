from services.seed import seed_database
from extensions import db
from models import Role, User


REQUIRED_TABLES = {
    "users", "roles", "permissions", "patients", "doctors", "specialties",
    "appointments", "medical_records", "diagnoses", "prescriptions", "medications",
    "lab_orders", "lab_results", "radiology_orders", "radiology_reports", "vital_signs",
    "nursing_notes", "pharmacy_inventory", "departments", "notifications", "messages",
    "audit_logs", "ai_recommendations", "system_settings", "dentists", "dental_specialties",
    "dental_records", "dental_charts", "dental_procedures", "dental_images", "orthodontic_cases",
    "physical_therapists", "therapy_assessments", "therapy_sessions", "therapy_plans",
    "therapy_exercises", "exercise_library", "rehabilitation_progress", "functional_outcomes",
    "referrals", "care_teams", "multidisciplinary_cases", "womens_health_profiles", "pregnancies",
    "pregnancy_visits", "antenatal_visits", "obstetric_history", "delivery_records",
    "postpartum_visits", "gynecology_journeys", "gynecology_visits", "infertility_journeys",
    "infertility_cycles", "partner_records", "semen_analyses", "folliculometry_records",
    "follicle_measurements", "ovulation_induction_cycles", "iui_cycles",
    "fertility_medication_protocols", "womens_ultrasound_reports", "fetal_biometry",
    "fetal_doppler_records", "gynecology_ultrasound_records", "pregnancy_risk_flags",
    "womens_health_calculations", "womens_health_timeline_events",
}


def test_complete_table_inventory(app):
    with app.app_context():
        assert REQUIRED_TABLES.issubset(db.metadata.tables)


def test_seed_is_idempotent(session):
    first = seed_database("one-time-test-password")
    second = seed_database("ignored-on-existing-user")
    assert first["admin"].id == second["admin"].id
    assert session.query(User).filter_by(username="superadmin").count() == 1
    assert session.query(Role).count() == 12
    assert len(first["admin"].roles[0].permissions) > 0
