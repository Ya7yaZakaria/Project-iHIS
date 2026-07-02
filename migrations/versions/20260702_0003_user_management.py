"""Add canonical user department and incomplete doctor profile support.

Revision ID: 20260702_0003
Revises: 20260702_0002
"""

from alembic import op
import sqlalchemy as sa


revision = "20260702_0003"
down_revision = "20260702_0002"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("department_id", sa.String(36), nullable=True))
        batch.create_foreign_key("fk_users_department_id_departments", "departments", ["department_id"], ["id"])
        batch.create_index("ix_users_department_id", ["department_id"], unique=False)
    op.execute(sa.text("""
        UPDATE users SET department_id = COALESCE(
            (SELECT department_id FROM doctors WHERE doctors.user_id = users.id),
            (SELECT department_id FROM dentists WHERE dentists.user_id = users.id),
            (SELECT department_id FROM physical_therapists WHERE physical_therapists.user_id = users.id)
        ) WHERE department_id IS NULL
    """))
    with op.batch_alter_table("doctors") as batch:
        batch.alter_column("specialty_id", existing_type=sa.String(36), nullable=True)
        batch.alter_column("license_number", existing_type=sa.String(80), nullable=True)


def downgrade():
    null_profiles = op.get_bind().execute(sa.text("SELECT COUNT(*) FROM doctors WHERE specialty_id IS NULL OR license_number IS NULL")).scalar_one()
    if null_profiles:
        raise RuntimeError("Complete all Doctor specialty and license fields before downgrading Phase 4.")
    with op.batch_alter_table("doctors") as batch:
        batch.alter_column("license_number", existing_type=sa.String(80), nullable=False)
        batch.alter_column("specialty_id", existing_type=sa.String(36), nullable=False)
    with op.batch_alter_table("users") as batch:
        batch.drop_index("ix_users_department_id")
        batch.drop_constraint("fk_users_department_id_departments", type_="foreignkey")
        batch.drop_column("department_id")
