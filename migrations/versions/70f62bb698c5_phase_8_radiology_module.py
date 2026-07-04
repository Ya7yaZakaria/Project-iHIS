"""Phase 8 radiology module

Revision ID: 70f62bb698c5
Revises: 20260703_0006
Create Date: 2026-07-03 01:01:26.892024
"""

from alembic import op
import sqlalchemy as sa


revision = "70f62bb698c5"
down_revision = "20260703_0006"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "imaging_studies",
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("modality", sa.String(length=40), nullable=False),
        sa.Column("body_region", sa.String(length=120), nullable=False),
        sa.Column("preparation_instructions", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_imaging_studies")),
    )

    with op.batch_alter_table("imaging_studies", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_imaging_studies_body_region"), ["body_region"], unique=False)
        batch_op.create_index(batch_op.f("ix_imaging_studies_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_imaging_studies_deleted_at"), ["deleted_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_imaging_studies_is_active"), ["is_active"], unique=False)
        batch_op.create_index(batch_op.f("ix_imaging_studies_modality"), ["modality"], unique=False)
        batch_op.create_index(batch_op.f("ix_imaging_studies_name"), ["name"], unique=True)
        batch_op.create_index(batch_op.f("ix_imaging_studies_tenant_id"), ["tenant_id"], unique=False)

    op.create_table(
        "radiology_attachments",
        sa.Column("radiology_order_id", sa.String(length=36), nullable=False),
        sa.Column("uploaded_by_id", sa.String(length=36), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("stored_name", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=False),
        sa.Column("extension", sa.String(length=12), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=60), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(
            ["radiology_order_id"],
            ["radiology_orders.id"],
            name=op.f("fk_radiology_attachments_radiology_order_id_radiology_orders"),
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by_id"],
            ["users.id"],
            name=op.f("fk_radiology_attachments_uploaded_by_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_radiology_attachments")),
        sa.UniqueConstraint("stored_name", name=op.f("uq_radiology_attachments_stored_name")),
    )

    with op.batch_alter_table("radiology_attachments", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_radiology_attachments_category"), ["category"], unique=False)
        batch_op.create_index(batch_op.f("ix_radiology_attachments_checksum_sha256"), ["checksum_sha256"], unique=False)
        batch_op.create_index(batch_op.f("ix_radiology_attachments_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_radiology_attachments_deleted_at"), ["deleted_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_radiology_attachments_is_active"), ["is_active"], unique=False)
        batch_op.create_index(batch_op.f("ix_radiology_attachments_radiology_order_id"), ["radiology_order_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_radiology_attachments_tenant_id"), ["tenant_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_radiology_attachments_uploaded_by_id"), ["uploaded_by_id"], unique=False)

    with op.batch_alter_table("radiology_orders", schema=None) as batch_op:
        batch_op.add_column(sa.Column("imaging_study_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("assigned_radiology_user_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("patient_arrived_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("imaging_performed_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("cancellation_reason", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "urgent_finding_flag",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )

        batch_op.create_index(batch_op.f("ix_radiology_orders_assigned_radiology_user_id"), ["assigned_radiology_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_radiology_orders_cancelled_at"), ["cancelled_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_radiology_orders_imaging_performed_at"), ["imaging_performed_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_radiology_orders_imaging_study_id"), ["imaging_study_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_radiology_orders_patient_arrived_at"), ["patient_arrived_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_radiology_orders_priority"), ["priority"], unique=False)
        batch_op.create_index(batch_op.f("ix_radiology_orders_scheduled_at"), ["scheduled_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_radiology_orders_urgent_finding_flag"), ["urgent_finding_flag"], unique=False)
        batch_op.create_foreign_key(
            batch_op.f("fk_radiology_orders_assigned_radiology_user_id_users"),
            "users",
            ["assigned_radiology_user_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_radiology_orders_imaging_study_id_imaging_studies"),
            "imaging_studies",
            ["imaging_study_id"],
            ["id"],
        )

    with op.batch_alter_table("radiology_orders", schema=None) as batch_op:
        batch_op.alter_column("urgent_finding_flag", server_default=None)

    with op.batch_alter_table("radiology_reports", schema=None) as batch_op:
        batch_op.add_column(sa.Column("verified_by_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("reviewed_by_doctor_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("clinical_indication", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("technique", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("recommendations", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "is_abnormal",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))

        batch_op.create_index(batch_op.f("ix_radiology_reports_is_abnormal"), ["is_abnormal"], unique=False)
        batch_op.create_index(batch_op.f("ix_radiology_reports_reviewed_at"), ["reviewed_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_radiology_reports_reviewed_by_doctor_id"), ["reviewed_by_doctor_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_radiology_reports_verified_at"), ["verified_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_radiology_reports_verified_by_id"), ["verified_by_id"], unique=False)
        batch_op.create_foreign_key(
            batch_op.f("fk_radiology_reports_reviewed_by_doctor_id_doctors"),
            "doctors",
            ["reviewed_by_doctor_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_radiology_reports_verified_by_id_users"),
            "users",
            ["verified_by_id"],
            ["id"],
        )

    with op.batch_alter_table("radiology_reports", schema=None) as batch_op:
        batch_op.alter_column("is_abnormal", server_default=None)


def downgrade():
    with op.batch_alter_table("radiology_reports", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_radiology_reports_verified_by_id_users"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_radiology_reports_reviewed_by_doctor_id_doctors"), type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_radiology_reports_verified_by_id"))
        batch_op.drop_index(batch_op.f("ix_radiology_reports_verified_at"))
        batch_op.drop_index(batch_op.f("ix_radiology_reports_reviewed_by_doctor_id"))
        batch_op.drop_index(batch_op.f("ix_radiology_reports_reviewed_at"))
        batch_op.drop_index(batch_op.f("ix_radiology_reports_is_abnormal"))
        batch_op.drop_column("reviewed_at")
        batch_op.drop_column("verified_at")
        batch_op.drop_column("is_abnormal")
        batch_op.drop_column("recommendations")
        batch_op.drop_column("technique")
        batch_op.drop_column("clinical_indication")
        batch_op.drop_column("reviewed_by_doctor_id")
        batch_op.drop_column("verified_by_id")

    with op.batch_alter_table("radiology_orders", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_radiology_orders_imaging_study_id_imaging_studies"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_radiology_orders_assigned_radiology_user_id_users"), type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_radiology_orders_urgent_finding_flag"))
        batch_op.drop_index(batch_op.f("ix_radiology_orders_scheduled_at"))
        batch_op.drop_index(batch_op.f("ix_radiology_orders_priority"))
        batch_op.drop_index(batch_op.f("ix_radiology_orders_patient_arrived_at"))
        batch_op.drop_index(batch_op.f("ix_radiology_orders_imaging_study_id"))
        batch_op.drop_index(batch_op.f("ix_radiology_orders_imaging_performed_at"))
        batch_op.drop_index(batch_op.f("ix_radiology_orders_cancelled_at"))
        batch_op.drop_index(batch_op.f("ix_radiology_orders_assigned_radiology_user_id"))
        batch_op.drop_column("urgent_finding_flag")
        batch_op.drop_column("cancellation_reason")
        batch_op.drop_column("cancelled_at")
        batch_op.drop_column("imaging_performed_at")
        batch_op.drop_column("patient_arrived_at")
        batch_op.drop_column("scheduled_at")
        batch_op.drop_column("assigned_radiology_user_id")
        batch_op.drop_column("imaging_study_id")

    with op.batch_alter_table("radiology_attachments", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_radiology_attachments_uploaded_by_id"))
        batch_op.drop_index(batch_op.f("ix_radiology_attachments_tenant_id"))
        batch_op.drop_index(batch_op.f("ix_radiology_attachments_radiology_order_id"))
        batch_op.drop_index(batch_op.f("ix_radiology_attachments_is_active"))
        batch_op.drop_index(batch_op.f("ix_radiology_attachments_deleted_at"))
        batch_op.drop_index(batch_op.f("ix_radiology_attachments_created_at"))
        batch_op.drop_index(batch_op.f("ix_radiology_attachments_checksum_sha256"))
        batch_op.drop_index(batch_op.f("ix_radiology_attachments_category"))

    op.drop_table("radiology_attachments")

    with op.batch_alter_table("imaging_studies", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_imaging_studies_tenant_id"))
        batch_op.drop_index(batch_op.f("ix_imaging_studies_name"))
        batch_op.drop_index(batch_op.f("ix_imaging_studies_modality"))
        batch_op.drop_index(batch_op.f("ix_imaging_studies_is_active"))
        batch_op.drop_index(batch_op.f("ix_imaging_studies_deleted_at"))
        batch_op.drop_index(batch_op.f("ix_imaging_studies_created_at"))
        batch_op.drop_index(batch_op.f("ix_imaging_studies_body_region"))

    op.drop_table("imaging_studies")