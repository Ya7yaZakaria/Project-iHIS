"""End-to-end Alembic smoke tests against an isolated SQLite database."""

import sqlite3

from app import create_app
from config import CONFIGS, TestingConfig


def test_migrations_upgrade_to_phase4_and_downgrade(tmp_path, monkeypatch):
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
    table_names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    connection.close()

    assert revision == "20260702_0004"
    assert "department_id" in user_columns
    assert doctor_columns["specialty_id"] == 0
    assert doctor_columns["license_number"] == 0
    assert "prescription_items" in table_names
    assert "medical_attachments" in table_names

    downgrade = runner.invoke(args=["db", "downgrade", "base"])
    assert downgrade.exit_code == 0, downgrade.output
