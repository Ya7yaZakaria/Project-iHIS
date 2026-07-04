"""Phase 14 reception module.

Revision ID: 20260705_0014
Revises: 20260705_0013
"""

from alembic import op
import sqlalchemy as sa


revision = "20260705_0014"
down_revision = "20260705_0013"
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
    if not _has_table("billing_initiations"):
        op.create_table(
            "billing_initiations",
            *_base_columns(),
            sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=False),
            sa.Column("appointment_id", sa.String(36), sa.ForeignKey("appointments.id")),
            sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
            sa.Column("started_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("notes", sa.Text()),
        )

    for column in (
        "is_active",
        "created_at",
        "deleted_at",
        "tenant_id",
        "patient_id",
        "appointment_id",
        "status",
        "started_by_id",
    ):
        _create_index_if_missing("billing_initiations", column)


def downgrade():
    if _has_table("billing_initiations"):
        op.drop_table("billing_initiations")