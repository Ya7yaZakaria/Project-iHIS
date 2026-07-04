"""Phase 7 laboratory catalog and workflow metadata.

Revision ID: 20260703_0006
Revises: cc0cb484ec7c
"""

from alembic import op
import sqlalchemy as sa

revision = "20260703_0006"
down_revision = "cc0cb484ec7c"
branch_labels = None
depends_on = None


def _base():
    return [sa.Column("id", sa.String(36), primary_key=True), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)), sa.Column("tenant_id", sa.String(36))]


def upgrade():
    op.create_table("lab_tests", *_base(), sa.Column("code", sa.String(60), nullable=False), sa.Column("name", sa.String(160), nullable=False),
        sa.Column("category", sa.String(100), nullable=False), sa.Column("unit", sa.String(40)), sa.Column("reference_range", sa.String(120)),
        sa.Column("sample_type", sa.String(80)), sa.Column("turnaround_minutes", sa.Integer()), sa.UniqueConstraint("code", name="uq_lab_tests_code"))
    for column in ("code", "name", "category", "is_active", "created_at", "deleted_at", "tenant_id"):
        op.create_index(f"ix_lab_tests_{column}", "lab_tests", [column])
    with op.batch_alter_table("lab_orders") as batch:
        batch.add_column(sa.Column("lab_test_id", sa.String(36))); batch.add_column(sa.Column("department_id", sa.String(36)))
        batch.add_column(sa.Column("assigned_to_id", sa.String(36))); batch.add_column(sa.Column("collected_at", sa.DateTime(timezone=True)))
        batch.add_column(sa.Column("collected_by_id", sa.String(36))); batch.add_column(sa.Column("processing_started_at", sa.DateTime(timezone=True)))
        batch.add_column(sa.Column("cancelled_at", sa.DateTime(timezone=True))); batch.add_column(sa.Column("cancelled_by_id", sa.String(36)))
        batch.add_column(sa.Column("cancellation_reason", sa.Text()))
        batch.create_foreign_key("fk_lab_orders_test", "lab_tests", ["lab_test_id"], ["id"]); batch.create_foreign_key("fk_lab_orders_department", "departments", ["department_id"], ["id"])
        batch.create_foreign_key("fk_lab_orders_assigned", "users", ["assigned_to_id"], ["id"]); batch.create_foreign_key("fk_lab_orders_collected", "users", ["collected_by_id"], ["id"])
        batch.create_foreign_key("fk_lab_orders_cancelled", "users", ["cancelled_by_id"], ["id"])
    for column in ("lab_test_id", "department_id", "assigned_to_id", "collected_at", "collected_by_id", "processing_started_at", "cancelled_at", "cancelled_by_id"):
        op.create_index(f"ix_lab_orders_{column}", "lab_orders", [column])
    with op.batch_alter_table("lab_results") as batch:
        batch.add_column(sa.Column("result_type", sa.String(20), nullable=False, server_default="text")); batch.add_column(sa.Column("comments", sa.Text()))
        batch.add_column(sa.Column("entered_by_id", sa.String(36))); batch.add_column(sa.Column("verified_at", sa.DateTime(timezone=True)))
        batch.add_column(sa.Column("reviewed_by_id", sa.String(36))); batch.add_column(sa.Column("reviewed_at", sa.DateTime(timezone=True)))
        batch.add_column(sa.Column("attachment_name", sa.String(255))); batch.add_column(sa.Column("attachment_stored_name", sa.String(255)))
        batch.add_column(sa.Column("attachment_mime_type", sa.String(120))); batch.add_column(sa.Column("attachment_size", sa.Integer()))
        batch.create_foreign_key("fk_lab_results_entered", "users", ["entered_by_id"], ["id"]); batch.create_foreign_key("fk_lab_results_reviewed", "doctors", ["reviewed_by_id"], ["id"])
    for column in ("entered_by_id", "verified_at", "reviewed_by_id", "reviewed_at"):
        op.create_index(f"ix_lab_results_{column}", "lab_results", [column])


def downgrade():
    for column in ("reviewed_at", "reviewed_by_id", "verified_at", "entered_by_id"): op.drop_index(f"ix_lab_results_{column}", table_name="lab_results")
    with op.batch_alter_table("lab_results") as batch:
        batch.drop_constraint("fk_lab_results_reviewed", type_="foreignkey"); batch.drop_constraint("fk_lab_results_entered", type_="foreignkey")
        for column in ("attachment_size", "attachment_mime_type", "attachment_stored_name", "attachment_name", "reviewed_at", "reviewed_by_id", "verified_at", "entered_by_id", "comments", "result_type"): batch.drop_column(column)
    for column in ("cancelled_by_id", "cancelled_at", "processing_started_at", "collected_by_id", "collected_at", "assigned_to_id", "department_id", "lab_test_id"): op.drop_index(f"ix_lab_orders_{column}", table_name="lab_orders")
    with op.batch_alter_table("lab_orders") as batch:
        for name in ("fk_lab_orders_cancelled", "fk_lab_orders_collected", "fk_lab_orders_assigned", "fk_lab_orders_department", "fk_lab_orders_test"): batch.drop_constraint(name, type_="foreignkey")
        for column in ("cancellation_reason", "cancelled_by_id", "cancelled_at", "processing_started_at", "collected_by_id", "collected_at", "assigned_to_id", "department_id", "lab_test_id"): batch.drop_column(column)
    op.drop_table("lab_tests")
