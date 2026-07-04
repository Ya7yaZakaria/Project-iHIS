"""Phase 6 appointment workflow fields

Revision ID: cc0cb484ec7c
Revises: 20260702_0004
Create Date: 2026-07-02
"""

from alembic import op
import sqlalchemy as sa


revision = "cc0cb484ec7c"
down_revision = "20260702_0004"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "appointments",
        sa.Column("arrival_time", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "appointments",
        sa.Column("consultation_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "appointments",
        sa.Column("consultation_completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "appointments",
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "appointments",
        sa.Column("cancelled_by_id", sa.String(length=36), nullable=True),
    )
    op.add_column(
        "appointments",
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "appointments",
        sa.Column("queue_number", sa.Integer(), nullable=True),
    )
    op.add_column(
        "appointments",
        sa.Column("reception_notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "appointments",
        sa.Column("follow_up_of_id", sa.String(length=36), nullable=True),
    )

    with op.batch_alter_table("appointments") as batch:
        batch.create_foreign_key(
            "fk_appointments_cancelled_by_id_users",
            "users",
            ["cancelled_by_id"],
            ["id"],
        )

        batch.create_foreign_key(
            "fk_appointments_follow_up_of_id_appointments",
            "appointments",
            ["follow_up_of_id"],
            ["id"],
        )

    op.execute("UPDATE appointments SET status = 'booked' WHERE status = 'scheduled'")

    op.create_index(
        "ix_appointments_arrival_time",
        "appointments",
        ["arrival_time"],
    )
    op.create_index(
        "ix_appointments_consultation_started_at",
        "appointments",
        ["consultation_started_at"],
    )
    op.create_index(
        "ix_appointments_consultation_completed_at",
        "appointments",
        ["consultation_completed_at"],
    )
    op.create_index(
        "ix_appointments_cancelled_at",
        "appointments",
        ["cancelled_at"],
    )
    op.create_index(
        "ix_appointments_cancelled_by_id",
        "appointments",
        ["cancelled_by_id"],
    )
    op.create_index(
        "ix_appointments_queue_number",
        "appointments",
        ["queue_number"],
    )
    op.create_index(
        "ix_appointments_follow_up_of_id",
        "appointments",
        ["follow_up_of_id"],
    )


def downgrade():
    op.drop_index("ix_appointments_follow_up_of_id", table_name="appointments")
    op.drop_index("ix_appointments_queue_number", table_name="appointments")
    op.drop_index("ix_appointments_cancelled_by_id", table_name="appointments")
    op.drop_index("ix_appointments_cancelled_at", table_name="appointments")
    op.drop_index("ix_appointments_consultation_completed_at", table_name="appointments")
    op.drop_index("ix_appointments_consultation_started_at", table_name="appointments")
    op.drop_index("ix_appointments_arrival_time", table_name="appointments")

    with op.batch_alter_table("appointments") as batch:
        batch.drop_constraint(
            "fk_appointments_follow_up_of_id_appointments",
            type_="foreignkey",
        )
        batch.drop_constraint(
            "fk_appointments_cancelled_by_id_users",
            type_="foreignkey",
        )

    op.drop_column("appointments", "follow_up_of_id")
    op.drop_column("appointments", "reception_notes")
    op.drop_column("appointments", "queue_number")
    op.drop_column("appointments", "cancellation_reason")
    op.drop_column("appointments", "cancelled_by_id")
    op.drop_column("appointments", "cancelled_at")
    op.drop_column("appointments", "consultation_completed_at")
    op.drop_column("appointments", "consultation_started_at")
    op.drop_column("appointments", "arrival_time")
