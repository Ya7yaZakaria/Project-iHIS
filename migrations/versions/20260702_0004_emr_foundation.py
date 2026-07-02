"""Build the central EMR foundation and normalize prescriptions.

Revision ID: 20260702_0004
Revises: 20260702_0003
"""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "20260702_0004"
down_revision = "20260702_0003"
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


def upgrade():
    with op.batch_alter_table("patients") as batch:
        batch.add_column(sa.Column("surgical_history", sa.JSON()))
        batch.add_column(sa.Column("family_history", sa.JSON()))
        batch.add_column(sa.Column("vaccination_history", sa.JSON()))
    with op.batch_alter_table("medical_records") as batch:
        batch.add_column(sa.Column("history_of_present_illness", sa.Text()))
        batch.add_column(sa.Column("note_format", sa.String(20), nullable=False, server_default="standard"))
        batch.add_column(sa.Column("subjective", sa.Text()))
        batch.add_column(sa.Column("objective", sa.Text()))
        batch.add_column(sa.Column("follow_up_date", sa.Date()))
    with op.batch_alter_table("prescriptions") as batch:
        batch.add_column(sa.Column("notes", sa.Text()))

    op.create_table(
        "prescription_items", *_base_columns(),
        sa.Column("prescription_id", sa.String(36), sa.ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("medication_id", sa.String(36), sa.ForeignKey("medications.id"), nullable=False),
        sa.Column("dose", sa.String(120), nullable=False),
        sa.Column("route", sa.String(60)), sa.Column("frequency", sa.String(120), nullable=False),
        sa.Column("duration", sa.String(120)), sa.Column("quantity", sa.String(80)),
        sa.Column("instructions", sa.Text()),
    )
    for column in ("is_active", "created_at", "deleted_at", "tenant_id", "prescription_id", "medication_id"):
        op.create_index(f"ix_prescription_items_{column}", "prescription_items", [column])

    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, medication_id, dosage, frequency, duration, instructions, tenant_id, is_active, created_at, updated_at, deleted_at FROM prescriptions")).mappings()
    for row in rows:
        bind.execute(sa.text("""INSERT INTO prescription_items
            (id, prescription_id, medication_id, dose, frequency, duration, instructions, tenant_id, is_active, created_at, updated_at, deleted_at)
            VALUES (:id, :prescription_id, :medication_id, :dose, :frequency, :duration, :instructions, :tenant_id, :is_active, :created_at, :updated_at, :deleted_at)"""),
            {"id": str(uuid4()), "prescription_id": row["id"], "medication_id": row["medication_id"], "dose": row["dosage"], "frequency": row["frequency"], "duration": row["duration"], "instructions": row["instructions"], "tenant_id": row["tenant_id"], "is_active": row["is_active"], "created_at": row["created_at"], "updated_at": row["updated_at"], "deleted_at": row["deleted_at"]})
    with op.batch_alter_table("prescriptions") as batch:
        batch.drop_index("ix_prescriptions_medication_id")
        batch.drop_column("instructions")
        batch.drop_column("duration")
        batch.drop_column("frequency")
        batch.drop_column("dosage")
        batch.drop_column("medication_id")

    op.create_table(
        "medical_attachments", *_base_columns(),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("medical_record_id", sa.String(36), sa.ForeignKey("medical_records.id")),
        sa.Column("uploaded_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("stored_name", sa.String(255), nullable=False, unique=True),
        sa.Column("mime_type", sa.String(120), nullable=False), sa.Column("extension", sa.String(12), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False), sa.Column("checksum_sha256", sa.String(64), nullable=False),
        sa.Column("category", sa.String(60), nullable=False, server_default="clinical_document"), sa.Column("description", sa.Text()),
    )
    for column in ("is_active", "created_at", "deleted_at", "tenant_id", "patient_id", "medical_record_id", "uploaded_by_id", "checksum_sha256", "category"):
        op.create_index(f"ix_medical_attachments_{column}", "medical_attachments", [column])
    bind.execute(sa.text("UPDATE lab_orders SET status='requested' WHERE status='ordered'"))
    bind.execute(sa.text("UPDATE radiology_orders SET status='requested' WHERE status='ordered'"))


def downgrade():
    bind = op.get_bind()
    invalid = bind.execute(sa.text("SELECT COUNT(*) FROM prescriptions p WHERE (SELECT COUNT(*) FROM prescription_items i WHERE i.prescription_id=p.id) != 1")).scalar_one()
    if invalid:
        raise RuntimeError("Every prescription must have exactly one item before downgrading Phase 5.")
    with op.batch_alter_table("prescriptions") as batch:
        batch.add_column(sa.Column("medication_id", sa.String(36), sa.ForeignKey("medications.id"), nullable=True))
        batch.add_column(sa.Column("dosage", sa.String(120), nullable=True))
        batch.add_column(sa.Column("frequency", sa.String(120), nullable=True))
        batch.add_column(sa.Column("duration", sa.String(120)))
        batch.add_column(sa.Column("instructions", sa.Text()))
    bind.execute(sa.text("""UPDATE prescriptions SET
        medication_id=(SELECT medication_id FROM prescription_items WHERE prescription_id=prescriptions.id),
        dosage=(SELECT dose FROM prescription_items WHERE prescription_id=prescriptions.id),
        frequency=(SELECT frequency FROM prescription_items WHERE prescription_id=prescriptions.id),
        duration=(SELECT duration FROM prescription_items WHERE prescription_id=prescriptions.id),
        instructions=(SELECT instructions FROM prescription_items WHERE prescription_id=prescriptions.id)"""))
    with op.batch_alter_table("prescriptions") as batch:
        batch.alter_column("medication_id", existing_type=sa.String(36), nullable=False)
        batch.alter_column("dosage", existing_type=sa.String(120), nullable=False)
        batch.alter_column("frequency", existing_type=sa.String(120), nullable=False)
        batch.create_index("ix_prescriptions_medication_id", ["medication_id"])
        batch.drop_column("notes")
    op.drop_table("medical_attachments")
    op.drop_table("prescription_items")
    with op.batch_alter_table("medical_records") as batch:
        for column in ("follow_up_date", "objective", "subjective", "note_format", "history_of_present_illness"):
            batch.drop_column(column)
    with op.batch_alter_table("patients") as batch:
        for column in ("vaccination_history", "family_history", "surgical_history"):
            batch.drop_column(column)
    bind.execute(sa.text("UPDATE lab_orders SET status='ordered' WHERE status='requested'"))
    bind.execute(sa.text("UPDATE radiology_orders SET status='ordered' WHERE status='requested'"))
