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
    table_names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    connection.close()

    assert revision == "20260703_0010"

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

    downgrade = runner.invoke(args=["db", "downgrade", "base"])
    assert downgrade.exit_code == 0, downgrade.output
