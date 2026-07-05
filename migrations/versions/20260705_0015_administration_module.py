"""Phase 15 administration module.

Revision ID: 20260705_0015
Revises: 20260705_0014
"""
from alembic import op
import sqlalchemy as sa

revision = "20260705_0015"
down_revision = "20260705_0014"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {item["name"] for item in inspector.get_columns("departments")}
    if "department_type" not in columns:
        with op.batch_alter_table("departments") as batch:
            batch.add_column(sa.Column("department_type", sa.String(40), nullable=False, server_default="Clinical"))
            batch.create_index("ix_departments_department_type", ["department_type"])


def downgrade():
    columns = {item["name"] for item in sa.inspect(op.get_bind()).get_columns("departments")}
    if "department_type" in columns:
        with op.batch_alter_table("departments") as batch:
            batch.drop_index("ix_departments_department_type")
            batch.drop_column("department_type")
