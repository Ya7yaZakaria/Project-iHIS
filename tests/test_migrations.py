"""End-to-end Alembic smoke tests against an isolated SQLite database."""

import sqlite3

from app import create_app
from config import CONFIGS, TestingConfig


def test_migrations_upgrade_to_latest_and_downgrade(tmp_path, monkeypatch):
    database_path = tmp_path / "migration_smoke.db"

    class MigrationTestConfig(TestingConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{database_path.as_posix()}"

    monkeypatch.setitem(CONFIGS, "migration_test", MigrationTestConfig)
    application = create_app("migration_test")
    runner = application.test_cli_runner()

    upgrade = runner.invoke(args=["db", "upgrade"])
    assert upgrade.exit_code == 0, upgrade.output

    connection = sqlite3.connect(database_path)
    revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    user_columns = {row[1] for row in connection.execute("PRAGMA table_info(users)")}
    doctor_columns = {row[1]: row[3] for row in connection.execute("PRAGMA table_info(doctors)")}
    appointment_columns = {row[1] for row in connection.execute("PRAGMA table_info(appointments)")}
    appointment_foreign_keys = {(row[3], row[2], row[4]) for row in connection.execute("PRAGMA foreign_key_list(appointments)")}
    radiology_order_columns = {row[1] for row in connection.execute("PRAGMA table_info(radiology_orders)")}
    radiology_report_columns = {row[1] for row in connection.execute("PRAGMA table_info(radiology_reports)")}
    dental_record_columns = {row[1] for row in connection.execute("PRAGMA table_info(dental_records)")}
    dental_chart_columns = {row[1] for row in connection.execute("PRAGMA table_info(dental_charts)")}
    dental_procedure_columns = {row[1] for row in connection.execute("PRAGMA table_info(dental_procedures)")}
    orthodontic_columns = {row[1] for row in connection.execute("PRAGMA table_info(orthodontic_cases)")}
    ultrasound_columns = {row[1] for row in connection.execute("PRAGMA table_info(womens_ultrasound_reports)")}
    lab_test_indexes = {row[1]: row[2] for row in connection.execute("PRAGMA index_list(lab_tests)")}
    table_names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    connection.close()

    assert revision == "20260705_0013"

    assert "department_id" in user_columns
    assert doctor_columns["specialty_id"] == 0
    assert doctor_columns["license_number"] == 0

    assert "prescription_items" in table_names
    assert "medical_attachments" in table_names
    assert "lab_tests" in table_names
    assert "imaging_studies" in table_names
    assert "radiology_attachments" in table_names
    assert "dispensing_records" in table_names
    assert "stock_movements" in table_names
    assert "patient_medication_history" in table_names
    assert "womens_health_approvals" in table_names
    assert "womens_ultrasound_attachments" in table_names
    assert "medication_administrations" in table_names
    assert "nursing_care_plans" in table_names

    assert "arrival_time" in appointment_columns
    assert "consultation_started_at" in appointment_columns
    assert "consultation_completed_at" in appointment_columns
    assert "cancelled_at" in appointment_columns
    assert "cancelled_by_id" in appointment_columns
    assert "cancellation_reason" in appointment_columns
    assert "queue_number" in appointment_columns
    assert "reception_notes" in appointment_columns
    assert "follow_up_of_id" in appointment_columns
    assert ("cancelled_by_id", "users", "id") in appointment_foreign_keys
    assert ("follow_up_of_id", "appointments", "id") in appointment_foreign_keys

    assert "imaging_study_id" in radiology_order_columns
    assert "assigned_radiology_user_id" in radiology_order_columns
    assert "scheduled_at" in radiology_order_columns
    assert "patient_arrived_at" in radiology_order_columns
    assert "imaging_performed_at" in radiology_order_columns
    assert "urgent_finding_flag" in radiology_order_columns

    assert "technique" in radiology_report_columns
    assert "verified_at" in radiology_report_columns
    assert "reviewed_at" in radiology_report_columns
    assert "is_abnormal" in radiology_report_columns

    assert {"oral_hygiene_history", "allergies", "medical_alerts", "dental_complaints", "dental_diagnosis"}.issubset(dental_record_columns)
    assert {"caries", "missing_teeth", "filled_teeth", "crown_bridge", "implant", "root_canal", "mobility", "periodontal_notes"}.issubset(dental_chart_columns)
    assert {"diagnosis", "treatment_details", "materials_used", "dentist_notes", "follow_up_date", "cost_placeholder"}.issubset(dental_procedure_columns)
    assert {"malocclusion_class", "progress_notes", "follow_up_visits"}.issubset(orthodontic_columns)
    assert "attachments" not in ultrasound_columns
    assert lab_test_indexes["ix_lab_tests_code"] == 1

    downgrade = runner.invoke(args=["db", "downgrade", "base"])
    assert downgrade.exit_code == 0, downgrade.output
