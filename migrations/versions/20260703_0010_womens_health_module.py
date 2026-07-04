"""Phase 10 Women's Health clinical workflows.

Revision ID: 20260703_0010
Revises: 20260703_0009
"""
from alembic import op
import sqlalchemy as sa

revision="20260703_0010"; down_revision="20260703_0009"; branch_labels=None; depends_on=None

def base(): return [sa.Column("id",sa.String(36),primary_key=True),sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),sa.Column("deleted_at",sa.DateTime(timezone=True)),sa.Column("tenant_id",sa.String(36))]
def indexes(table,cols):
    for col in cols: op.create_index(f"ix_{table}_{col}",table,[col])

def upgrade():
    with op.batch_alter_table("womens_health_profiles") as b:
        for col in (sa.Column("ob_gyn_summary",sa.Text()),sa.Column("menstrual_history",sa.JSON()),sa.Column("contraception_history",sa.JSON()),sa.Column("infertility_history",sa.JSON()),sa.Column("surgical_history",sa.JSON()),sa.Column("risk_flags",sa.JSON()),sa.Column("active_journey_type",sa.String(40)),sa.Column("active_journey_id",sa.String(36))): b.add_column(col)
        b.create_index("ix_womens_health_profiles_active_journey_type",["active_journey_type"]); b.create_index("ix_womens_health_profiles_active_journey_id",["active_journey_id"])
    with op.batch_alter_table("pregnancies") as b:
        for name in ("abortions","living_children","previous_cs_count","previous_vaginal_births"): b.add_column(sa.Column(name,sa.Integer(),nullable=False,server_default="0"))
        b.add_column(sa.Column("high_risk_flags",sa.JSON()))
    with op.batch_alter_table("pregnancy_visits") as b: b.add_column(sa.Column("complaint",sa.Text()))
    with op.batch_alter_table("antenatal_visits") as b:
        b.add_column(sa.Column("recorded_by_id",sa.String(36))); b.create_index("ix_antenatal_visits_recorded_by_id",["recorded_by_id"]); b.create_foreign_key("fk_antenatal_visits_recorded_by_id_users","users",["recorded_by_id"],["id"])
    with op.batch_alter_table("postpartum_visits") as b: b.add_column(sa.Column("follow_up_date",sa.Date())); b.create_index("ix_postpartum_visits_follow_up_date",["follow_up_date"])
    with op.batch_alter_table("gynecology_visits") as b:
        b.add_column(sa.Column("diagnosis",sa.Text())); b.add_column(sa.Column("procedures",sa.JSON())); b.add_column(sa.Column("follow_up_date",sa.Date())); b.create_index("ix_gynecology_visits_follow_up_date",["follow_up_date"])
    with op.batch_alter_table("infertility_journeys") as b: b.add_column(sa.Column("investigations",sa.JSON())); b.add_column(sa.Column("treatment_plan",sa.Text()))
    with op.batch_alter_table("infertility_cycles") as b: b.add_column(sa.Column("timed_intercourse_advice",sa.Text()))
    with op.batch_alter_table("iui_cycles") as b:
        b.add_column(sa.Column("stimulation_protocol",sa.JSON())); b.add_column(sa.Column("semen_preparation_summary",sa.Text())); b.add_column(sa.Column("trigger_at",sa.DateTime(timezone=True)))
    with op.batch_alter_table("womens_ultrasound_reports") as b:
        for col in (sa.Column("pregnancy_visit_id",sa.String(36)),sa.Column("antenatal_visit_id",sa.String(36)),sa.Column("gynecology_visit_id",sa.String(36)),sa.Column("placenta",sa.String(160)),sa.Column("liquor",sa.String(160)),sa.Column("cervical_length_mm",sa.Numeric(6,2))): b.add_column(col)
        for name,target in (("pregnancy_visit_id","pregnancy_visits"),("antenatal_visit_id","antenatal_visits"),("gynecology_visit_id","gynecology_visits")):
            b.create_index(f"ix_womens_ultrasound_reports_{name}",[name]); b.create_foreign_key(f"fk_womens_ultrasound_reports_{name}_{target}",target,[name],["id"])
    op.create_table("womens_ultrasound_attachments",*base(),sa.Column("ultrasound_report_id",sa.String(36),sa.ForeignKey("womens_ultrasound_reports.id",ondelete="CASCADE"),nullable=False),sa.Column("uploaded_by_id",sa.String(36),sa.ForeignKey("users.id"),nullable=False),sa.Column("original_name",sa.String(255),nullable=False),sa.Column("stored_name",sa.String(255),nullable=False,unique=True),sa.Column("mime_type",sa.String(120),nullable=False),sa.Column("extension",sa.String(12),nullable=False),sa.Column("size_bytes",sa.Integer(),nullable=False),sa.Column("checksum_sha256",sa.String(64),nullable=False),sa.Column("description",sa.Text()))
    indexes("womens_ultrasound_attachments",("is_active","created_at","deleted_at","tenant_id","ultrasound_report_id","uploaded_by_id","checksum_sha256"))
    op.create_table("womens_health_approvals",*base(),sa.Column("profile_id",sa.String(36),sa.ForeignKey("womens_health_profiles.id"),nullable=False),sa.Column("source_type",sa.String(80),nullable=False),sa.Column("source_id",sa.String(36),nullable=False),sa.Column("status",sa.String(20),nullable=False,server_default="draft"),sa.Column("signed_by_id",sa.String(36),sa.ForeignKey("users.id")),sa.Column("signed_at",sa.DateTime(timezone=True)),sa.UniqueConstraint("source_type","source_id",name="uq_womens_health_approval_source"))
    indexes("womens_health_approvals",("is_active","created_at","deleted_at","tenant_id","profile_id","source_type","source_id","status","signed_by_id","signed_at"))

def downgrade():
    op.drop_table("womens_health_approvals"); op.drop_table("womens_ultrasound_attachments")
    with op.batch_alter_table("womens_ultrasound_reports") as b:
        for name,target in (("pregnancy_visit_id","pregnancy_visits"),("antenatal_visit_id","antenatal_visits"),("gynecology_visit_id","gynecology_visits")): b.drop_constraint(f"fk_womens_ultrasound_reports_{name}_{target}",type_="foreignkey"); b.drop_index(f"ix_womens_ultrasound_reports_{name}")
        for name in ("cervical_length_mm","liquor","placenta","gynecology_visit_id","antenatal_visit_id","pregnancy_visit_id"): b.drop_column(name)
    with op.batch_alter_table("iui_cycles") as b:
        for name in ("trigger_at","semen_preparation_summary","stimulation_protocol"): b.drop_column(name)
    with op.batch_alter_table("infertility_cycles") as b: b.drop_column("timed_intercourse_advice")
    with op.batch_alter_table("infertility_journeys") as b: b.drop_column("treatment_plan"); b.drop_column("investigations")
    with op.batch_alter_table("gynecology_visits") as b: b.drop_index("ix_gynecology_visits_follow_up_date"); b.drop_column("follow_up_date"); b.drop_column("procedures"); b.drop_column("diagnosis")
    with op.batch_alter_table("postpartum_visits") as b: b.drop_index("ix_postpartum_visits_follow_up_date"); b.drop_column("follow_up_date")
    with op.batch_alter_table("antenatal_visits") as b: b.drop_constraint("fk_antenatal_visits_recorded_by_id_users",type_="foreignkey"); b.drop_index("ix_antenatal_visits_recorded_by_id"); b.drop_column("recorded_by_id")
    with op.batch_alter_table("pregnancy_visits") as b: b.drop_column("complaint")
    with op.batch_alter_table("pregnancies") as b:
        for name in ("high_risk_flags","previous_vaginal_births","previous_cs_count","living_children","abortions"): b.drop_column(name)
    with op.batch_alter_table("womens_health_profiles") as b:
        b.drop_index("ix_womens_health_profiles_active_journey_id"); b.drop_index("ix_womens_health_profiles_active_journey_type")
        for name in ("active_journey_id","active_journey_type","risk_flags","surgical_history","infertility_history","contraception_history","menstrual_history","ob_gyn_summary"): b.drop_column(name)
