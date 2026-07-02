"""Add authentication security state to users.

Revision ID: 20260702_0002
Revises: 20260702_0001
"""

from alembic import op
import sqlalchemy as sa


revision = "20260702_0002"
down_revision = "20260702_0001"
branch_labels = None
depends_on = None


def _columns():
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}


def upgrade():
    existing = _columns()
    with op.batch_alter_table("users") as batch:
        if "failed_login_attempts" not in existing:
            batch.add_column(sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"))
        if "locked_until" not in existing:
            batch.add_column(sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))
        if "password_changed_at" not in existing:
            batch.add_column(sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True))
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("users")}
    if "ix_users_locked_until" not in indexes:
        op.create_index("ix_users_locked_until", "users", ["locked_until"], unique=False)


def downgrade():
    existing = _columns()
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("users")}
    if "ix_users_locked_until" in indexes:
        op.drop_index("ix_users_locked_until", table_name="users")
    with op.batch_alter_table("users") as batch:
        for column in ("password_changed_at", "locked_until", "failed_login_attempts"):
            if column in existing:
                batch.drop_column(column)
