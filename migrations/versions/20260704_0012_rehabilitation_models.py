"""Phase 12 rehabilitation schema extensions.

Revision ID: 20260704_0012
Revises: 20260704_0011
"""

from alembic import op
import sqlalchemy as sa


revision = "20260704_0012"
down_revision = "20260704_0011"
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(table):
    return _inspector().has_table(table)


def _columns(table):
    return {item["name"] for item in _inspector().get_columns(table)}


def _indexes(table):
    return {item["name"] for item in _inspector().get_indexes(table)}


def _foreign_keys(table):
    return {
        column
        for item in _inspector().get_foreign_keys(table)
        for column in item.get("constrained_columns", ())
    }


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
    if not _has_table("rehabilitation_records"):
        op.create_table(
            "rehabilitation_records",
            *_base_columns(),
            sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=False),
            sa.Column("visit_id", sa.String(36), sa.ForeignKey("medical_records.id")),
            sa.Column("doctor_id", sa.String(36), sa.ForeignKey("users.id")),
            sa.Column("referral_source", sa.String(160)),
            sa.Column("chief_complaint", sa.Text()),
            sa.Column("functional_limitation", sa.Text()),
            sa.Column("pain_score", sa.Integer()),
            sa.Column("mobility_status", sa.String(120)),
            sa.Column("rehabilitation_diagnosis", sa.Text()),
            sa.Column("therapy_goals", sa.Text()),
            sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        )
    for column in ("is_active", "created_at", "deleted_at", "tenant_id", "patient_id", "visit_id", "doctor_id", "status"):
        _create_index_if_missing("rehabilitation_records", column)

    if not _has_table("rehabilitation_assessments"):
        op.create_table(
            "rehabilitation_assessments",
            *_base_columns(),
            sa.Column("rehabilitation_record_id", sa.String(36), sa.ForeignKey("rehabilitation_records.id"), nullable=False),
            sa.Column("assessment_date", sa.Date(), nullable=False),
            sa.Column("physical_exam", sa.Text()),
            sa.Column("range_of_motion", sa.Text()),
            sa.Column("muscle_power", sa.Text()),
            sa.Column("balance_assessment", sa.Text()),
            sa.Column("gait_assessment", sa.Text()),
            sa.Column("neurological_findings", sa.Text()),
            sa.Column("red_flags", sa.Text()),
            sa.Column("functional_score", sa.Numeric(8, 2)),
            sa.Column("assessment_summary", sa.Text()),
        )
    for column in ("is_active", "created_at", "deleted_at", "tenant_id", "rehabilitation_record_id", "assessment_date"):
        _create_index_if_missing("rehabilitation_assessments", column)

    plan_columns = _columns("therapy_plans")
    plan_additions = [
        sa.Column("rehabilitation_record_id", sa.String(36)),
        sa.Column("plan_name", sa.String(160)),
        sa.Column("duration", sa.String(120)),
        sa.Column("modalities", sa.Text()),
        sa.Column("exercise_program", sa.Text()),
        sa.Column("home_program", sa.Text()),
        sa.Column("review_date", sa.Date()),
        sa.Column("discharge_criteria", sa.Text()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    ]
    missing = [column for column in plan_additions if column.name not in plan_columns]
    if missing or "rehabilitation_record_id" not in _foreign_keys("therapy_plans"):
        with op.batch_alter_table("therapy_plans") as batch:
            for column in missing:
                batch.add_column(column)
            if "rehabilitation_record_id" not in _foreign_keys("therapy_plans"):
                batch.create_foreign_key(
                    "fk_therapy_plans_rehabilitation_record_id_rehabilitation_records",
                    "rehabilitation_records", ["rehabilitation_record_id"], ["id"],
                )
    for column in ("rehabilitation_record_id", "plan_name", "review_date", "active"):
        _create_index_if_missing("therapy_plans", column)

    session_columns = _columns("therapy_sessions")
    session_additions = [
        sa.Column("therapist_user_id", sa.String(36)),
        sa.Column("session_date", sa.DateTime(timezone=True)),
        sa.Column("pain_before", sa.Integer()),
        sa.Column("pain_after", sa.Integer()),
        sa.Column("modalities_used", sa.Text()),
        sa.Column("exercises_performed", sa.Text()),
        sa.Column("progress_notes", sa.Text()),
        sa.Column("patient_tolerance", sa.Text()),
        sa.Column("next_session_plan", sa.Text()),
    ]
    missing = [column for column in session_additions if column.name not in session_columns]
    if missing or "therapist_user_id" not in _foreign_keys("therapy_sessions"):
        with op.batch_alter_table("therapy_sessions") as batch:
            for column in missing:
                batch.add_column(column)
            if "therapist_user_id" not in _foreign_keys("therapy_sessions"):
                batch.create_foreign_key(
                    "fk_therapy_sessions_therapist_user_id_users",
                    "users", ["therapist_user_id"], ["id"],
                )
    op.execute("UPDATE therapy_sessions SET session_date = scheduled_start WHERE session_date IS NULL")
    for column in ("therapist_user_id", "session_date"):
        _create_index_if_missing("therapy_sessions", column)

    exercise_columns = _columns("exercise_library")
    exercise_additions = [
        sa.Column("target_region", sa.String(120)),
        sa.Column("indication", sa.Text()),
        sa.Column("repetitions", sa.Integer()),
        sa.Column("sets", sa.Integer()),
        sa.Column("frequency", sa.String(120)),
        sa.Column("media_placeholder", sa.String(255)),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    ]
    missing = [column for column in exercise_additions if column.name not in exercise_columns]
    if missing:
        with op.batch_alter_table("exercise_library") as batch:
            for column in missing:
                batch.add_column(column)
    op.execute("UPDATE exercise_library SET target_region = category WHERE target_region IS NULL")
    for column in ("target_region", "active"):
        _create_index_if_missing("exercise_library", column)


def downgrade():
    for table, columns in (
        ("exercise_library", ("active", "target_region")),
        ("therapy_sessions", ("session_date", "therapist_user_id")),
        ("therapy_plans", ("active", "review_date", "plan_name", "rehabilitation_record_id")),
    ):
        if _has_table(table):
            existing_indexes = _indexes(table)
            for column in columns:
                name = f"ix_{table}_{column}"
                if name in existing_indexes:
                    op.drop_index(name, table_name=table)

    if _has_table("exercise_library"):
        columns = _columns("exercise_library")
        with op.batch_alter_table("exercise_library") as batch:
            for column in ("target_region", "indication", "repetitions", "sets", "frequency", "media_placeholder", "active"):
                if column in columns:
                    batch.drop_column(column)

    if _has_table("therapy_sessions"):
        columns = _columns("therapy_sessions")
        with op.batch_alter_table("therapy_sessions") as batch:
            if "therapist_user_id" in _foreign_keys("therapy_sessions"):
                batch.drop_constraint("fk_therapy_sessions_therapist_user_id_users", type_="foreignkey")
            for column in ("therapist_user_id", "session_date", "pain_before", "pain_after", "modalities_used", "exercises_performed", "progress_notes", "patient_tolerance", "next_session_plan"):
                if column in columns:
                    batch.drop_column(column)

    if _has_table("therapy_plans"):
        columns = _columns("therapy_plans")
        with op.batch_alter_table("therapy_plans") as batch:
            if "rehabilitation_record_id" in _foreign_keys("therapy_plans"):
                batch.drop_constraint("fk_therapy_plans_rehabilitation_record_id_rehabilitation_records", type_="foreignkey")
            for column in ("rehabilitation_record_id", "plan_name", "duration", "modalities", "exercise_program", "home_program", "review_date", "discharge_criteria", "active"):
                if column in columns:
                    batch.drop_column(column)

    if _has_table("rehabilitation_assessments"):
        op.drop_table("rehabilitation_assessments")
    if _has_table("rehabilitation_records"):
        op.drop_table("rehabilitation_records")
