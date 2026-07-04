"""Freeze Phase 11 dentistry schema and reconcile metadata drift.

Revision ID: 20260704_0011
Revises: 20260703_0010
"""

from alembic import op
import sqlalchemy as sa


revision = "20260704_0011"
down_revision = "20260703_0010"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("dental_records") as batch:
        batch.add_column(sa.Column("oral_hygiene_history", sa.Text()))
        batch.add_column(sa.Column("allergies", sa.JSON()))
        batch.add_column(sa.Column("medical_alerts", sa.JSON()))
        batch.add_column(sa.Column("dental_complaints", sa.Text()))
        batch.add_column(sa.Column("dental_diagnosis", sa.Text()))

    with op.batch_alter_table("dental_charts") as batch:
        batch.add_column(sa.Column("caries", sa.String(40)))
        batch.add_column(sa.Column("missing_teeth", sa.Boolean()))
        batch.add_column(sa.Column("filled_teeth", sa.Boolean()))
        batch.add_column(sa.Column("crown_bridge", sa.Boolean()))
        batch.add_column(sa.Column("implant", sa.Boolean()))
        batch.add_column(sa.Column("root_canal", sa.Boolean()))
        batch.add_column(sa.Column("mobility", sa.String(20)))
        batch.add_column(sa.Column("periodontal_notes", sa.Text()))

    with op.batch_alter_table("dental_procedures") as batch:
        batch.add_column(sa.Column("diagnosis", sa.Text()))
        batch.add_column(sa.Column("treatment_details", sa.Text()))
        batch.add_column(sa.Column("materials_used", sa.JSON()))
        batch.add_column(sa.Column("dentist_notes", sa.Text()))
        batch.add_column(sa.Column("follow_up_date", sa.Date()))
        batch.add_column(sa.Column("cost_placeholder", sa.Numeric(10, 2)))

    with op.batch_alter_table("orthodontic_cases") as batch:
        batch.add_column(sa.Column("malocclusion_class", sa.String(40)))
        batch.add_column(sa.Column("progress_notes", sa.Text()))
        batch.add_column(sa.Column("follow_up_visits", sa.JSON()))

    with op.batch_alter_table("lab_tests") as batch:
        batch.drop_constraint("uq_lab_tests_code", type_="unique")
        batch.drop_index("ix_lab_tests_code")
        batch.create_index("ix_lab_tests_code", ["code"], unique=True)

    with op.batch_alter_table("womens_ultrasound_reports") as batch:
        batch.drop_column("attachments")


def downgrade():
    with op.batch_alter_table("womens_ultrasound_reports") as batch:
        batch.add_column(sa.Column("attachments", sa.JSON()))

    with op.batch_alter_table("lab_tests") as batch:
        batch.drop_index("ix_lab_tests_code")
        batch.create_index("ix_lab_tests_code", ["code"], unique=False)
        batch.create_unique_constraint("uq_lab_tests_code", ["code"])

    with op.batch_alter_table("orthodontic_cases") as batch:
        batch.drop_column("follow_up_visits")
        batch.drop_column("progress_notes")
        batch.drop_column("malocclusion_class")

    with op.batch_alter_table("dental_procedures") as batch:
        batch.drop_column("cost_placeholder")
        batch.drop_column("follow_up_date")
        batch.drop_column("dentist_notes")
        batch.drop_column("materials_used")
        batch.drop_column("treatment_details")
        batch.drop_column("diagnosis")

    with op.batch_alter_table("dental_charts") as batch:
        batch.drop_column("periodontal_notes")
        batch.drop_column("mobility")
        batch.drop_column("root_canal")
        batch.drop_column("implant")
        batch.drop_column("crown_bridge")
        batch.drop_column("filled_teeth")
        batch.drop_column("missing_teeth")
        batch.drop_column("caries")

    with op.batch_alter_table("dental_records") as batch:
        batch.drop_column("dental_diagnosis")
        batch.drop_column("dental_complaints")
        batch.drop_column("medical_alerts")
        batch.drop_column("allergies")
        batch.drop_column("oral_hygiene_history")
