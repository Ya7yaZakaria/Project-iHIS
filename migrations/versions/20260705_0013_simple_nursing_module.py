"""Phase 13 simple nursing module.

Revision ID: 20260705_0013
Revises: 20260704_0012
"""

from alembic import op
import sqlalchemy as sa


revision = "20260705_0013"
down_revision = "20260704_0012"
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(table):
    return _inspector().has_table(table)


def _indexes(table):
    return {item["name"] for item in _inspector().get_indexes(table)}


def _base_columns():
    return [
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("tenant_id", sa.String(36)),
    ]


def _create_index_if_missing(table, column, unique=False):
    name = f"ix_{table}_{column}"
    if name not in _indexes(table):
        op.create_index(name, table, [column], unique=unique)


def upgrade():
    if not _has_table("medication_administrations"):
        op.create_table(
            "medication_administrations",
            *_base_columns(),
            sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=False),
            sa.Column("medical_record_id", sa.String(36), sa.ForeignKey("medical_records.id")),
            sa.Column("prescription_item_id", sa.String(36), sa.ForeignKey("prescription_items.id")),
            sa.Column("medication_name", sa.String(160), nullable=False),
            sa.Column("dose", sa.String(120)),
            sa.Column("scheduled_time", sa.DateTime(timezone=True)),
            sa.Column("given_at", sa.DateTime(timezone=True)),
            sa.Column("status", sa.String(30), nullable=False, server_default="given"),
            sa.Column("given_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("missed_reason", sa.Text()),
            sa.Column("patient_reaction", sa.Text()),
            sa.Column("notes", sa.Text()),
        )

    for column in (
        "is_active",
        "created_at",
        "deleted_at",
        "tenant_id",
        "patient_id",
        "medical_record_id",
        "prescription_item_id",
        "medication_name",
        "scheduled_time",
        "given_at",
        "status",
        "given_by_id",
    ):
        _create_index_if_missing("medication_administrations", column)

    if not _has_table("nursing_care_plans"):
        op.create_table(
            "nursing_care_plans",
            *_base_columns(),
            sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=False),
            sa.Column("medical_record_id", sa.String(36), sa.ForeignKey("medical_records.id")),
            sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("nursing_diagnosis", sa.Text(), nullable=False),
            sa.Column("goals", sa.Text(), nullable=False),
            sa.Column("interventions", sa.Text(), nullable=False),
            sa.Column("evaluation", sa.Text()),
            sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        )

    for column in (
        "is_active",
        "created_at",
        "deleted_at",
        "tenant_id",
        "patient_id",
        "medical_record_id",
        "created_by_id",
        "status",
    ):
        _create_index_if_missing("nursing_care_plans", column)


def downgrade():
    if _has_table("nursing_care_plans"):
        op.drop_table("nursing_care_plans")

    if _has_table("medication_administrations"):
        op.drop_table("medication_administrations")