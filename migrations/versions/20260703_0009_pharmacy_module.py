"""Phase 9 pharmacy workflow and inventory audit models.

Revision ID: 20260703_0009
Revises: 70f62bb698c5
"""

from alembic import op
import sqlalchemy as sa


revision = "20260703_0009"
down_revision = "70f62bb698c5"
branch_labels = None
depends_on = None


def _base_columns():
    return [
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("tenant_id", sa.String(36)),
    ]


def _indexes(table, columns):
    for column in columns:
        op.create_index(f"ix_{table}_{column}", table, [column])


def upgrade():
    with op.batch_alter_table("medications") as batch:
        batch.add_column(sa.Column("category", sa.String(100)))
        batch.add_column(sa.Column("manufacturer", sa.String(160)))
        batch.add_column(sa.Column("barcode", sa.String(120)))
        batch.create_index("ix_medications_category", ["category"])
        batch.create_index("ix_medications_barcode", ["barcode"], unique=True)

    with op.batch_alter_table("prescriptions") as batch:
        batch.add_column(sa.Column("pharmacy_notes", sa.Text()))
        batch.add_column(sa.Column("sent_at", sa.DateTime(timezone=True)))
        batch.add_column(sa.Column("reviewed_at", sa.DateTime(timezone=True)))
        batch.add_column(sa.Column("reviewed_by_id", sa.String(36)))
        batch.add_column(sa.Column("completed_at", sa.DateTime(timezone=True)))
        batch.add_column(sa.Column("completed_by_id", sa.String(36)))
        batch.add_column(sa.Column("cancelled_at", sa.DateTime(timezone=True)))
        batch.add_column(sa.Column("cancelled_by_id", sa.String(36)))
        batch.add_column(sa.Column("cancellation_reason", sa.Text()))
        for column in ("sent_at", "reviewed_at", "reviewed_by_id", "completed_at", "completed_by_id", "cancelled_at", "cancelled_by_id"):
            batch.create_index(f"ix_prescriptions_{column}", [column])
        batch.create_foreign_key("fk_prescriptions_reviewed_by_id_users", "users", ["reviewed_by_id"], ["id"])
        batch.create_foreign_key("fk_prescriptions_completed_by_id_users", "users", ["completed_by_id"], ["id"])
        batch.create_foreign_key("fk_prescriptions_cancelled_by_id_users", "users", ["cancelled_by_id"], ["id"])

    op.execute("UPDATE prescriptions SET status='created' WHERE status IN ('active', 'ordered')")

    with op.batch_alter_table("prescription_items") as batch:
        batch.add_column(sa.Column("requested_quantity", sa.Numeric(12, 2), nullable=False, server_default="1"))
        batch.add_column(sa.Column("dispensed_quantity", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch.add_column(sa.Column("substitute_medication_id", sa.String(36)))
        batch.add_column(sa.Column("substitution_note", sa.Text()))
        batch.create_index("ix_prescription_items_substitute_medication_id", ["substitute_medication_id"])
        batch.create_foreign_key("fk_prescription_items_substitute_medication_id_medications", "medications", ["substitute_medication_id"], ["id"])
    op.execute("UPDATE prescription_items SET requested_quantity=CAST(quantity AS NUMERIC) WHERE CAST(quantity AS NUMERIC) > 0")
    with op.batch_alter_table("prescription_items") as batch:
        batch.alter_column("requested_quantity", server_default=None)
        batch.alter_column("dispensed_quantity", server_default=None)

    with op.batch_alter_table("pharmacy_inventory") as batch:
        batch.add_column(sa.Column("supplier", sa.String(160)))

    op.create_table(
        "dispensing_records", *_base_columns(),
        sa.Column("prescription_item_id", sa.String(36), sa.ForeignKey("prescription_items.id"), nullable=False),
        sa.Column("inventory_batch_id", sa.String(36), sa.ForeignKey("pharmacy_inventory.id"), nullable=False),
        sa.Column("medication_id", sa.String(36), sa.ForeignKey("medications.id"), nullable=False),
        sa.Column("pharmacist_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("dispensed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text()),
    )
    _indexes("dispensing_records", ("is_active", "created_at", "deleted_at", "tenant_id", "prescription_item_id", "inventory_batch_id", "medication_id", "pharmacist_id", "dispensed_at"))

    op.create_table(
        "stock_movements", *_base_columns(),
        sa.Column("inventory_batch_id", sa.String(36), sa.ForeignKey("pharmacy_inventory.id"), nullable=False),
        sa.Column("medication_id", sa.String(36), sa.ForeignKey("medications.id"), nullable=False),
        sa.Column("prescription_item_id", sa.String(36), sa.ForeignKey("prescription_items.id")),
        sa.Column("actor_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("movement_type", sa.String(30), nullable=False),
        sa.Column("quantity_change", sa.Numeric(12, 2), nullable=False),
        sa.Column("balance_after", sa.Numeric(12, 2), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("moved_at", sa.DateTime(timezone=True), nullable=False),
    )
    _indexes("stock_movements", ("is_active", "created_at", "deleted_at", "tenant_id", "inventory_batch_id", "medication_id", "prescription_item_id", "actor_user_id", "movement_type", "moved_at"))

    op.create_table(
        "patient_medication_history", *_base_columns(),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("prescription_id", sa.String(36), sa.ForeignKey("prescriptions.id"), nullable=False),
        sa.Column("prescription_item_id", sa.String(36), sa.ForeignKey("prescription_items.id"), nullable=False),
        sa.Column("medication_id", sa.String(36), sa.ForeignKey("medications.id"), nullable=False),
        sa.Column("quantity_dispensed", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("first_dispensed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_dispensed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="partial"),
        sa.Column("pharmacy_notes", sa.Text()),
        sa.UniqueConstraint("prescription_item_id", name="uq_medication_history_prescription_item"),
    )
    _indexes("patient_medication_history", ("is_active", "created_at", "deleted_at", "tenant_id", "patient_id", "prescription_id", "prescription_item_id", "medication_id", "last_dispensed_at", "status"))


def downgrade():
    op.drop_table("patient_medication_history")
    op.drop_table("stock_movements")
    op.drop_table("dispensing_records")
    with op.batch_alter_table("pharmacy_inventory") as batch:
        batch.drop_column("supplier")
    with op.batch_alter_table("prescription_items") as batch:
        batch.drop_constraint("fk_prescription_items_substitute_medication_id_medications", type_="foreignkey")
        batch.drop_index("ix_prescription_items_substitute_medication_id")
        for column in ("substitution_note", "substitute_medication_id", "dispensed_quantity", "requested_quantity"):
            batch.drop_column(column)
    with op.batch_alter_table("prescriptions") as batch:
        for name in ("fk_prescriptions_reviewed_by_id_users", "fk_prescriptions_completed_by_id_users", "fk_prescriptions_cancelled_by_id_users"):
            batch.drop_constraint(name, type_="foreignkey")
        for column in ("sent_at", "reviewed_at", "reviewed_by_id", "completed_at", "completed_by_id", "cancelled_at", "cancelled_by_id"):
            batch.drop_index(f"ix_prescriptions_{column}")
        for column in ("cancellation_reason", "cancelled_by_id", "cancelled_at", "completed_by_id", "completed_at", "reviewed_by_id", "reviewed_at", "sent_at", "pharmacy_notes"):
            batch.drop_column(column)
    with op.batch_alter_table("medications") as batch:
        batch.drop_index("ix_medications_barcode")
        batch.drop_index("ix_medications_category")
        batch.drop_column("barcode")
        batch.drop_column("manufacturer")
        batch.drop_column("category")
