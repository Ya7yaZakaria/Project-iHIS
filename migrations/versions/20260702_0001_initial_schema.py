"""Frozen explicit Phase 2 iHIS schema.

Revision ID: 20260702_0001
Revises: None
"""

from alembic import op
import sqlalchemy as sa

revision = "20260702_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('dental_specialties',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('code', sa.String(40), nullable=False),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('description', sa.String(255)),
    )
    op.create_table('departments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('code', sa.String(30), nullable=False),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('description', sa.String(255)),
        sa.Column('location', sa.String(120)),
    )
    op.create_table('exercise_library',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('code', sa.String(50)),
        sa.Column('name', sa.String(160), nullable=False),
        sa.Column('category', sa.String(80), nullable=False),
        sa.Column('instructions', sa.Text, nullable=False),
        sa.Column('image_path', sa.String(255)),
        sa.Column('video_path', sa.String(255)),
        sa.Column('contraindications', sa.JSON),
    )
    op.create_table('medications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('generic_name', sa.String(160), nullable=False),
        sa.Column('brand_name', sa.String(160)),
        sa.Column('form', sa.String(60)),
        sa.Column('strength', sa.String(80)),
        sa.Column('route', sa.String(60)),
        sa.Column('code', sa.String(80)),
    )
    op.create_table('permissions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('code', sa.String(120), nullable=False),
        sa.Column('module', sa.String(60), nullable=False),
        sa.Column('action', sa.String(40), nullable=False),
        sa.Column('description', sa.String(255)),
    )
    op.create_table('roles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('name', sa.String(80), nullable=False),
        sa.Column('description', sa.String(255)),
        sa.Column('is_system', sa.Boolean, nullable=False),
    )
    op.create_table('specialties',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('code', sa.String(40), nullable=False),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('category', sa.String(60), nullable=False),
        sa.Column('description', sa.String(255)),
    )
    op.create_table('system_settings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('key', sa.String(120), nullable=False),
        sa.Column('value', sa.JSON),
        sa.Column('category', sa.String(60), nullable=False),
        sa.Column('is_secret', sa.Boolean, nullable=False),
        sa.Column('description', sa.String(255)),
    )
    op.create_table('users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('username', sa.String(80), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(40)),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
        sa.Column('must_change_password', sa.Boolean, nullable=False),
    )
    op.create_table('audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36)),
        sa.Column('actor_user_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('action', sa.String(120), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', sa.String(36)),
        sa.Column('outcome', sa.String(30), nullable=False),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('details', sa.JSON),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table('dentists',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('dental_specialty_id', sa.String(36), sa.ForeignKey('dental_specialties.id'), nullable=False),
        sa.Column('department_id', sa.String(36), sa.ForeignKey('departments.id')),
        sa.Column('license_number', sa.String(80), nullable=False),
        sa.Column('qualifications', sa.JSON),
    )
    op.create_table('doctors',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('specialty_id', sa.String(36), sa.ForeignKey('specialties.id'), nullable=False),
        sa.Column('department_id', sa.String(36), sa.ForeignKey('departments.id')),
        sa.Column('license_number', sa.String(80), nullable=False),
        sa.Column('title', sa.String(80)),
        sa.Column('qualifications', sa.JSON),
        sa.Column('digital_signature_path', sa.String(255)),
    )
    op.create_table('messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('sender_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('recipient_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('subject', sa.String(160)),
        sa.Column('body', sa.Text, nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True)),
        sa.Column('read_at', sa.DateTime(timezone=True)),
    )
    op.create_table('notifications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(160), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('category', sa.String(40), nullable=False),
        sa.Column('is_read', sa.Boolean, nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True)),
        sa.Column('data', sa.JSON),
    )
    op.create_table('patients',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('medical_record_number', sa.String(50), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('date_of_birth', sa.Date, nullable=False),
        sa.Column('sex_at_birth', sa.String(30), nullable=False),
        sa.Column('blood_type', sa.String(5)),
        sa.Column('phone', sa.String(40)),
        sa.Column('email', sa.String(255)),
        sa.Column('address', sa.Text),
        sa.Column('emergency_contact', sa.JSON),
        sa.Column('allergies', sa.JSON),
        sa.Column('chronic_conditions', sa.JSON),
    )
    op.create_table('pharmacy_inventory',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('medication_id', sa.String(36), sa.ForeignKey('medications.id'), nullable=False),
        sa.Column('batch_number', sa.String(80), nullable=False),
        sa.Column('quantity_on_hand', sa.Numeric(12, 2), nullable=False),
        sa.Column('reorder_level', sa.Numeric(12, 2), nullable=False),
        sa.Column('unit_cost', sa.Numeric(12, 2)),
        sa.Column('expiry_date', sa.Date),
        sa.Column('location', sa.String(120)),
        sa.UniqueConstraint('medication_id', 'batch_number', name='uq_inventory_medication_batch'),
    )
    op.create_table('physical_therapists',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('department_id', sa.String(36), sa.ForeignKey('departments.id')),
        sa.Column('license_number', sa.String(80), nullable=False),
        sa.Column('specialty', sa.String(120), nullable=False),
        sa.Column('qualifications', sa.JSON),
    )
    op.create_table('role_permissions',
        sa.Column('role_id', sa.String(36), sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('permission_id', sa.String(36), sa.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    )
    op.create_table('user_roles',
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('role_id', sa.String(36), sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    )
    op.create_table('appointments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('appointment_number', sa.String(50), nullable=False),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('doctor_id', sa.String(36), sa.ForeignKey('doctors.id')),
        sa.Column('department_id', sa.String(36), sa.ForeignKey('departments.id')),
        sa.Column('scheduled_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('scheduled_end', sa.DateTime(timezone=True)),
        sa.Column('appointment_type', sa.String(60), nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('reason', sa.Text),
        sa.Column('notes', sa.Text),
        sa.CheckConstraint('scheduled_end IS NULL OR scheduled_end > scheduled_start', name='ck_appointment_time_order'),
    )
    op.create_table('care_teams',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('name', sa.String(160), nullable=False),
        sa.Column('purpose', sa.String(255)),
        sa.Column('lead_user_id', sa.String(36), sa.ForeignKey('users.id')),
    )
    op.create_table('referrals',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('referring_user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('receiving_department_id', sa.String(36), sa.ForeignKey('departments.id')),
        sa.Column('receiving_provider_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('referral_type', sa.String(60), nullable=False),
        sa.Column('reason', sa.Text, nullable=False),
        sa.Column('priority', sa.String(20), nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('referred_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table('womens_health_profiles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('blood_group', sa.String(5)),
        sa.Column('rhesus_status', sa.String(12)),
        sa.Column('menarche_age', sa.Integer),
        sa.Column('cycle_pattern', sa.String(80)),
        sa.Column('contraception', sa.String(120)),
        sa.Column('gynecologic_history', sa.JSON),
        sa.Column('family_history', sa.JSON),
    )
    op.create_table('care_team_members',
        sa.Column('care_team_id', sa.String(36), sa.ForeignKey('care_teams.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('member_role', sa.String(80), nullable=False),
    )
    op.create_table('gynecology_journeys',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('journey_number', sa.String(50), nullable=False),
        sa.Column('profile_id', sa.String(36), sa.ForeignKey('womens_health_profiles.id'), nullable=False),
        sa.Column('primary_condition', sa.String(160), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True)),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('summary', sa.Text),
    )
    op.create_table('infertility_journeys',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('journey_number', sa.String(50), nullable=False),
        sa.Column('profile_id', sa.String(36), sa.ForeignKey('womens_health_profiles.id'), nullable=False),
        sa.Column('infertility_type', sa.String(30), nullable=False),
        sa.Column('duration_months', sa.Integer),
        sa.Column('female_factor', sa.JSON),
        sa.Column('male_factor', sa.JSON),
        sa.Column('combined_factor', sa.Boolean, nullable=False),
        sa.Column('unexplained', sa.Boolean, nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('outcome', sa.String(120)),
    )
    op.create_table('medical_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('record_number', sa.String(50), nullable=False),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('doctor_id', sa.String(36), sa.ForeignKey('doctors.id')),
        sa.Column('appointment_id', sa.String(36), sa.ForeignKey('appointments.id')),
        sa.Column('encounter_type', sa.String(60), nullable=False),
        sa.Column('encounter_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('chief_complaint', sa.Text),
        sa.Column('history', sa.Text),
        sa.Column('examination', sa.Text),
        sa.Column('assessment', sa.Text),
        sa.Column('plan', sa.Text),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('signed_at', sa.DateTime(timezone=True)),
    )
    op.create_table('obstetric_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('profile_id', sa.String(36), sa.ForeignKey('womens_health_profiles.id'), nullable=False),
        sa.Column('pregnancy_order', sa.Integer, nullable=False),
        sa.Column('year', sa.Integer),
        sa.Column('gestational_age_weeks', sa.Integer),
        sa.Column('outcome', sa.String(80), nullable=False),
        sa.Column('delivery_mode', sa.String(80)),
        sa.Column('neonatal_outcome', sa.String(160)),
        sa.Column('complications', sa.JSON),
    )
    op.create_table('pregnancies',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('profile_id', sa.String(36), sa.ForeignKey('womens_health_profiles.id'), nullable=False),
        sa.Column('pregnancy_number', sa.Integer, nullable=False),
        sa.Column('gravida', sa.Integer),
        sa.Column('para', sa.Integer),
        sa.Column('gtpal', sa.String(20)),
        sa.Column('lmp', sa.Date),
        sa.Column('estimated_due_date', sa.Date),
        sa.Column('risk_category', sa.String(30), nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('maternal_conditions', sa.JSON),
        sa.Column('fetal_conditions', sa.JSON),
        sa.Column('delivery_plan', sa.Text),
        sa.Column('outcome', sa.String(120)),
    )
    op.create_table('ai_recommendations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('medical_record_id', sa.String(36), sa.ForeignKey('medical_records.id')),
        sa.Column('recommendation_type', sa.String(80), nullable=False),
        sa.Column('model_name', sa.String(120)),
        sa.Column('model_version', sa.String(60)),
        sa.Column('content', sa.JSON, nullable=False),
        sa.Column('confidence', sa.Numeric(5, 4)),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('reviewed_by_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('reviewed_at', sa.DateTime(timezone=True)),
    )
    op.create_table('delivery_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('pregnancy_id', sa.String(36), sa.ForeignKey('pregnancies.id'), nullable=False),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('gestational_age_weeks', sa.Integer),
        sa.Column('delivery_mode', sa.String(80), nullable=False),
        sa.Column('indication', sa.Text),
        sa.Column('place_of_delivery', sa.String(160)),
        sa.Column('attendants', sa.JSON),
        sa.Column('maternal_complications', sa.JSON),
        sa.Column('newborns', sa.JSON),
        sa.Column('outcome', sa.String(80), nullable=False),
    )
    op.create_table('dental_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('dentist_id', sa.String(36), sa.ForeignKey('dentists.id')),
        sa.Column('medical_record_id', sa.String(36), sa.ForeignKey('medical_records.id')),
        sa.Column('visit_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('chief_complaint', sa.Text),
        sa.Column('dental_history', sa.Text),
        sa.Column('examination', sa.Text),
        sa.Column('treatment_plan', sa.Text),
        sa.Column('progress_notes', sa.Text),
        sa.Column('status', sa.String(30), nullable=False),
    )
    op.create_table('diagnoses',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('medical_record_id', sa.String(36), sa.ForeignKey('medical_records.id'), nullable=False),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('doctor_id', sa.String(36), sa.ForeignKey('doctors.id')),
        sa.Column('icd10_code', sa.String(20)),
        sa.Column('description', sa.String(255), nullable=False),
        sa.Column('diagnosis_type', sa.String(30), nullable=False),
        sa.Column('diagnosed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
    )
    op.create_table('gynecology_visits',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('journey_id', sa.String(36), sa.ForeignKey('gynecology_journeys.id'), nullable=False),
        sa.Column('medical_record_id', sa.String(36), sa.ForeignKey('medical_records.id')),
        sa.Column('doctor_id', sa.String(36), sa.ForeignKey('doctors.id')),
        sa.Column('visit_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('visit_type', sa.String(60), nullable=False),
        sa.Column('symptoms', sa.JSON),
        sa.Column('examination', sa.Text),
        sa.Column('assessment', sa.Text),
        sa.Column('plan', sa.Text),
    )
    op.create_table('infertility_cycles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('journey_id', sa.String(36), sa.ForeignKey('infertility_journeys.id'), nullable=False),
        sa.Column('cycle_number', sa.Integer, nullable=False),
        sa.Column('cycle_type', sa.String(60), nullable=False),
        sa.Column('cycle_start_date', sa.Date, nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('protocol', sa.JSON),
        sa.Column('trigger_at', sa.DateTime(timezone=True)),
        sa.Column('outcome', sa.String(80)),
        sa.Column('cancellation_reason', sa.Text),
        sa.UniqueConstraint('journey_id', 'cycle_number', name='uq_infertility_journey_cycle'),
    )
    op.create_table('lab_orders',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('order_number', sa.String(50), nullable=False),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('doctor_id', sa.String(36), sa.ForeignKey('doctors.id'), nullable=False),
        sa.Column('medical_record_id', sa.String(36), sa.ForeignKey('medical_records.id')),
        sa.Column('test_code', sa.String(60)),
        sa.Column('test_name', sa.String(160), nullable=False),
        sa.Column('priority', sa.String(20), nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('ordered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('specimen_type', sa.String(80)),
        sa.Column('clinical_notes', sa.Text),
    )
    op.create_table('multidisciplinary_cases',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('case_number', sa.String(50), nullable=False),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('care_team_id', sa.String(36), sa.ForeignKey('care_teams.id')),
        sa.Column('medical_record_id', sa.String(36), sa.ForeignKey('medical_records.id')),
        sa.Column('title', sa.String(160), nullable=False),
        sa.Column('summary', sa.Text),
        sa.Column('recommendations', sa.Text),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('meeting_at', sa.DateTime(timezone=True)),
    )
    op.create_table('nursing_notes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('medical_record_id', sa.String(36), sa.ForeignKey('medical_records.id')),
        sa.Column('nurse_user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('note_type', sa.String(60), nullable=False),
        sa.Column('note', sa.Text, nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table('partner_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('journey_id', sa.String(36), sa.ForeignKey('infertility_journeys.id'), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('date_of_birth', sa.Date),
        sa.Column('occupation', sa.String(120)),
        sa.Column('smoking_status', sa.String(40)),
        sa.Column('fertility_history', sa.Text),
        sa.Column('previous_procedures', sa.JSON),
        sa.Column('previous_surgeries', sa.JSON),
        sa.Column('current_medications', sa.JSON),
    )
    op.create_table('postpartum_visits',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('pregnancy_id', sa.String(36), sa.ForeignKey('pregnancies.id'), nullable=False),
        sa.Column('medical_record_id', sa.String(36), sa.ForeignKey('medical_records.id')),
        sa.Column('visit_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('maternal_assessment', sa.Text),
        sa.Column('wound_assessment', sa.Text),
        sa.Column('lactation_status', sa.String(80)),
        sa.Column('contraception_plan', sa.String(160)),
        sa.Column('mood_screen', sa.JSON),
        sa.Column('follow_up_plan', sa.Text),
    )
    op.create_table('pregnancy_risk_flags',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('pregnancy_id', sa.String(36), sa.ForeignKey('pregnancies.id'), nullable=False),
        sa.Column('code', sa.String(60), nullable=False),
        sa.Column('label', sa.String(160), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('identified_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('source', sa.String(80)),
        sa.Column('notes', sa.Text),
    )
    op.create_table('pregnancy_visits',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('pregnancy_id', sa.String(36), sa.ForeignKey('pregnancies.id'), nullable=False),
        sa.Column('medical_record_id', sa.String(36), sa.ForeignKey('medical_records.id')),
        sa.Column('doctor_id', sa.String(36), sa.ForeignKey('doctors.id')),
        sa.Column('visit_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('visit_type', sa.String(60), nullable=False),
        sa.Column('gestational_age_weeks', sa.Integer),
        sa.Column('gestational_age_days', sa.Integer),
        sa.Column('assessment', sa.Text),
        sa.Column('plan', sa.Text),
        sa.Column('next_follow_up', sa.Date),
    )
    op.create_table('prescriptions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('prescription_number', sa.String(50), nullable=False),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('doctor_id', sa.String(36), sa.ForeignKey('doctors.id'), nullable=False),
        sa.Column('medical_record_id', sa.String(36), sa.ForeignKey('medical_records.id')),
        sa.Column('medication_id', sa.String(36), sa.ForeignKey('medications.id'), nullable=False),
        sa.Column('dosage', sa.String(120), nullable=False),
        sa.Column('frequency', sa.String(120), nullable=False),
        sa.Column('duration', sa.String(120)),
        sa.Column('instructions', sa.Text),
        sa.Column('prescribed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
    )
    op.create_table('radiology_orders',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('order_number', sa.String(50), nullable=False),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('doctor_id', sa.String(36), sa.ForeignKey('doctors.id'), nullable=False),
        sa.Column('medical_record_id', sa.String(36), sa.ForeignKey('medical_records.id')),
        sa.Column('modality', sa.String(40), nullable=False),
        sa.Column('body_part', sa.String(100), nullable=False),
        sa.Column('priority', sa.String(20), nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('ordered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('clinical_indication', sa.Text),
        sa.Column('dicom_study_uid', sa.String(128)),
    )
    op.create_table('therapy_assessments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('therapist_id', sa.String(36), sa.ForeignKey('physical_therapists.id'), nullable=False),
        sa.Column('medical_record_id', sa.String(36), sa.ForeignKey('medical_records.id')),
        sa.Column('assessment_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('assessment_type', sa.String(60), nullable=False),
        sa.Column('pain_score', sa.Integer),
        sa.Column('mobility', sa.JSON),
        sa.Column('strength', sa.JSON),
        sa.Column('range_of_motion', sa.JSON),
        sa.Column('balance', sa.JSON),
        sa.Column('gait', sa.JSON),
        sa.Column('functional_summary', sa.Text),
    )
    op.create_table('vital_signs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('medical_record_id', sa.String(36), sa.ForeignKey('medical_records.id')),
        sa.Column('recorded_by_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('temperature_c', sa.Numeric(4, 1)),
        sa.Column('pulse_bpm', sa.Integer),
        sa.Column('respiratory_rate', sa.Integer),
        sa.Column('systolic_bp', sa.Integer),
        sa.Column('diastolic_bp', sa.Integer),
        sa.Column('oxygen_saturation', sa.Numeric(5, 2)),
        sa.Column('weight_kg', sa.Numeric(7, 2)),
        sa.Column('height_cm', sa.Numeric(6, 2)),
        sa.Column('pain_score', sa.Integer),
    )
    op.create_table('womens_health_timeline_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('profile_id', sa.String(36), sa.ForeignKey('womens_health_profiles.id'), nullable=False),
        sa.Column('pregnancy_id', sa.String(36), sa.ForeignKey('pregnancies.id')),
        sa.Column('gynecology_journey_id', sa.String(36), sa.ForeignKey('gynecology_journeys.id')),
        sa.Column('infertility_journey_id', sa.String(36), sa.ForeignKey('infertility_journeys.id')),
        sa.Column('event_type', sa.String(80), nullable=False),
        sa.Column('event_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('title', sa.String(160), nullable=False),
        sa.Column('summary', sa.Text),
        sa.Column('source_type', sa.String(80)),
        sa.Column('source_id', sa.String(36)),
        sa.Column('data', sa.JSON),
    )
    op.create_table('antenatal_visits',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('pregnancy_id', sa.String(36), sa.ForeignKey('pregnancies.id'), nullable=False),
        sa.Column('pregnancy_visit_id', sa.String(36), sa.ForeignKey('pregnancy_visits.id')),
        sa.Column('visit_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('weight_kg', sa.Numeric(7, 2)),
        sa.Column('systolic_bp', sa.Integer),
        sa.Column('diastolic_bp', sa.Integer),
        sa.Column('fundal_height_cm', sa.Numeric(5, 2)),
        sa.Column('fetal_heart_rate', sa.Integer),
        sa.Column('fetal_movement', sa.String(80)),
        sa.Column('presentation', sa.String(60)),
        sa.Column('urine_findings', sa.JSON),
    )
    op.create_table('dental_charts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('dental_record_id', sa.String(36), sa.ForeignKey('dental_records.id'), nullable=False),
        sa.Column('tooth_number', sa.String(12), nullable=False),
        sa.Column('numbering_system', sa.String(20), nullable=False),
        sa.Column('condition', sa.String(80), nullable=False),
        sa.Column('surfaces', sa.JSON),
        sa.Column('periodontal_data', sa.JSON),
        sa.Column('notes', sa.Text),
        sa.UniqueConstraint('dental_record_id', 'tooth_number', 'numbering_system', name='uq_dental_chart_tooth'),
    )
    op.create_table('dental_images',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('dental_record_id', sa.String(36), sa.ForeignKey('dental_records.id'), nullable=False),
        sa.Column('image_type', sa.String(60), nullable=False),
        sa.Column('file_path', sa.String(255), nullable=False),
        sa.Column('tooth_number', sa.String(12)),
        sa.Column('captured_at', sa.DateTime(timezone=True)),
        sa.Column('description', sa.Text),
    )
    op.create_table('dental_procedures',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('dental_record_id', sa.String(36), sa.ForeignKey('dental_records.id'), nullable=False),
        sa.Column('dentist_id', sa.String(36), sa.ForeignKey('dentists.id'), nullable=False),
        sa.Column('tooth_number', sa.String(12)),
        sa.Column('procedure_code', sa.String(40)),
        sa.Column('procedure_name', sa.String(160), nullable=False),
        sa.Column('performed_at', sa.DateTime(timezone=True)),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('notes', sa.Text),
    )
    op.create_table('fertility_medication_protocols',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('infertility_cycle_id', sa.String(36), sa.ForeignKey('infertility_cycles.id'), nullable=False),
        sa.Column('medication_id', sa.String(36), sa.ForeignKey('medications.id')),
        sa.Column('medication_name', sa.String(160), nullable=False),
        sa.Column('dose', sa.String(80), nullable=False),
        sa.Column('route', sa.String(60)),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date),
        sa.Column('instructions', sa.Text),
    )
    op.create_table('folliculometry_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('infertility_cycle_id', sa.String(36), sa.ForeignKey('infertility_cycles.id'), nullable=False),
        sa.Column('scan_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cycle_day', sa.Integer, nullable=False),
        sa.Column('endometrium_mm', sa.Numeric(6, 2)),
        sa.Column('endometrium_pattern', sa.String(80)),
        sa.Column('notes', sa.Text),
    )
    op.create_table('lab_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('lab_order_id', sa.String(36), sa.ForeignKey('lab_orders.id'), nullable=False),
        sa.Column('component_name', sa.String(160), nullable=False),
        sa.Column('value_text', sa.String(255)),
        sa.Column('value_numeric', sa.Numeric(18, 6)),
        sa.Column('unit', sa.String(40)),
        sa.Column('reference_range', sa.String(120)),
        sa.Column('abnormal_flag', sa.String(20)),
        sa.Column('is_critical', sa.Boolean, nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('resulted_at', sa.DateTime(timezone=True)),
        sa.Column('validated_by_id', sa.String(36), sa.ForeignKey('users.id')),
    )
    op.create_table('orthodontic_cases',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('dentist_id', sa.String(36), sa.ForeignKey('dentists.id'), nullable=False),
        sa.Column('dental_record_id', sa.String(36), sa.ForeignKey('dental_records.id')),
        sa.Column('diagnosis', sa.Text),
        sa.Column('appliance_type', sa.String(100)),
        sa.Column('treatment_plan', sa.Text),
        sa.Column('start_date', sa.Date),
        sa.Column('expected_end_date', sa.Date),
        sa.Column('actual_end_date', sa.Date),
        sa.Column('status', sa.String(30), nullable=False),
    )
    op.create_table('ovulation_induction_cycles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('infertility_cycle_id', sa.String(36), sa.ForeignKey('infertility_cycles.id'), nullable=False),
        sa.Column('medication_protocol', sa.JSON),
        sa.Column('stimulation_start_date', sa.Date),
        sa.Column('trigger_medication', sa.String(120)),
        sa.Column('trigger_at', sa.DateTime(timezone=True)),
        sa.Column('luteal_support', sa.JSON),
        sa.Column('response', sa.String(120)),
    )
    op.create_table('radiology_reports',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('radiology_order_id', sa.String(36), sa.ForeignKey('radiology_orders.id'), nullable=False),
        sa.Column('radiologist_id', sa.String(36), sa.ForeignKey('doctors.id')),
        sa.Column('findings', sa.Text),
        sa.Column('impression', sa.Text),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('is_critical', sa.Boolean, nullable=False),
        sa.Column('reported_at', sa.DateTime(timezone=True)),
        sa.Column('image_links', sa.JSON),
    )
    op.create_table('semen_analyses',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('partner_id', sa.String(36), sa.ForeignKey('partner_records.id'), nullable=False),
        sa.Column('collected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('volume_ml', sa.Numeric(7, 2)),
        sa.Column('concentration_million_ml', sa.Numeric(10, 2)),
        sa.Column('total_motility_percent', sa.Numeric(5, 2)),
        sa.Column('progressive_motility_percent', sa.Numeric(5, 2)),
        sa.Column('normal_morphology_percent', sa.Numeric(5, 2)),
        sa.Column('interpretation', sa.Text),
        sa.Column('raw_results', sa.JSON),
    )
    op.create_table('therapy_plans',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('therapist_id', sa.String(36), sa.ForeignKey('physical_therapists.id'), nullable=False),
        sa.Column('assessment_id', sa.String(36), sa.ForeignKey('therapy_assessments.id')),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date),
        sa.Column('goals', sa.JSON, nullable=False),
        sa.Column('interventions', sa.JSON),
        sa.Column('frequency', sa.String(120)),
        sa.Column('status', sa.String(30), nullable=False),
    )
    op.create_table('womens_health_calculations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('profile_id', sa.String(36), sa.ForeignKey('womens_health_profiles.id'), nullable=False),
        sa.Column('pregnancy_id', sa.String(36), sa.ForeignKey('pregnancies.id')),
        sa.Column('infertility_cycle_id', sa.String(36), sa.ForeignKey('infertility_cycles.id')),
        sa.Column('calculation_type', sa.String(80), nullable=False),
        sa.Column('inputs', sa.JSON, nullable=False),
        sa.Column('result', sa.JSON, nullable=False),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('calculated_by_id', sa.String(36), sa.ForeignKey('users.id')),
    )
    op.create_table('womens_ultrasound_reports',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('report_number', sa.String(50), nullable=False),
        sa.Column('profile_id', sa.String(36), sa.ForeignKey('womens_health_profiles.id'), nullable=False),
        sa.Column('pregnancy_id', sa.String(36), sa.ForeignKey('pregnancies.id')),
        sa.Column('gynecology_journey_id', sa.String(36), sa.ForeignKey('gynecology_journeys.id')),
        sa.Column('infertility_journey_id', sa.String(36), sa.ForeignKey('infertility_journeys.id')),
        sa.Column('medical_record_id', sa.String(36), sa.ForeignKey('medical_records.id')),
        sa.Column('radiology_order_id', sa.String(36), sa.ForeignKey('radiology_orders.id')),
        sa.Column('performed_by_id', sa.String(36), sa.ForeignKey('doctors.id')),
        sa.Column('scan_type', sa.String(80), nullable=False),
        sa.Column('performed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('findings', sa.Text),
        sa.Column('impression', sa.Text),
        sa.Column('measurements', sa.JSON),
        sa.Column('attachments', sa.JSON),
        sa.Column('status', sa.String(30), nullable=False),
    )
    op.create_table('fetal_biometry',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('ultrasound_report_id', sa.String(36), sa.ForeignKey('womens_ultrasound_reports.id'), nullable=False),
        sa.Column('fetus_label', sa.String(20), nullable=False),
        sa.Column('biparietal_diameter_mm', sa.Numeric(7, 2)),
        sa.Column('head_circumference_mm', sa.Numeric(7, 2)),
        sa.Column('abdominal_circumference_mm', sa.Numeric(7, 2)),
        sa.Column('femur_length_mm', sa.Numeric(7, 2)),
        sa.Column('estimated_fetal_weight_g', sa.Numeric(9, 2)),
        sa.Column('estimated_gestational_age_days', sa.Integer),
        sa.Column('percentile', sa.Numeric(5, 2)),
    )
    op.create_table('fetal_doppler_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('ultrasound_report_id', sa.String(36), sa.ForeignKey('womens_ultrasound_reports.id'), nullable=False),
        sa.Column('vessel', sa.String(80), nullable=False),
        sa.Column('fetus_label', sa.String(20), nullable=False),
        sa.Column('pulsatility_index', sa.Numeric(8, 3)),
        sa.Column('resistance_index', sa.Numeric(8, 3)),
        sa.Column('systolic_diastolic_ratio', sa.Numeric(8, 3)),
        sa.Column('peak_systolic_velocity', sa.Numeric(9, 3)),
        sa.Column('cerebroplacental_ratio', sa.Numeric(8, 3)),
        sa.Column('interpretation', sa.String(160)),
    )
    op.create_table('follicle_measurements',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('folliculometry_record_id', sa.String(36), sa.ForeignKey('folliculometry_records.id'), nullable=False),
        sa.Column('ovary', sa.String(10), nullable=False),
        sa.Column('follicle_number', sa.Integer, nullable=False),
        sa.Column('diameter_mm', sa.Numeric(6, 2), nullable=False),
        sa.Column('dimensions', sa.JSON),
    )
    op.create_table('functional_outcomes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('therapy_plan_id', sa.String(36), sa.ForeignKey('therapy_plans.id')),
        sa.Column('instrument', sa.String(120), nullable=False),
        sa.Column('score', sa.Numeric(10, 2), nullable=False),
        sa.Column('maximum_score', sa.Numeric(10, 2)),
        sa.Column('measured_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('interpretation', sa.Text),
    )
    op.create_table('gynecology_ultrasound_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('ultrasound_report_id', sa.String(36), sa.ForeignKey('womens_ultrasound_reports.id'), nullable=False),
        sa.Column('uterine_position', sa.String(80)),
        sa.Column('uterine_dimensions', sa.JSON),
        sa.Column('endometrium_mm', sa.Numeric(6, 2)),
        sa.Column('endometrium_description', sa.String(160)),
        sa.Column('right_ovary', sa.JSON),
        sa.Column('left_ovary', sa.JSON),
        sa.Column('adnexal_findings', sa.JSON),
        sa.Column('free_fluid', sa.String(120)),
    )
    op.create_table('iui_cycles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('infertility_cycle_id', sa.String(36), sa.ForeignKey('infertility_cycles.id'), nullable=False),
        sa.Column('partner_id', sa.String(36), sa.ForeignKey('partner_records.id')),
        sa.Column('performed_at', sa.DateTime(timezone=True)),
        sa.Column('semen_analysis_id', sa.String(36), sa.ForeignKey('semen_analyses.id')),
        sa.Column('post_wash_count', sa.Numeric(10, 2)),
        sa.Column('luteal_support', sa.JSON),
        sa.Column('pregnancy_test_date', sa.Date),
        sa.Column('outcome', sa.String(80)),
    )
    op.create_table('rehabilitation_progress',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('therapy_plan_id', sa.String(36), sa.ForeignKey('therapy_plans.id'), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('pain_score', sa.Integer),
        sa.Column('mobility_score', sa.Numeric(8, 2)),
        sa.Column('strength_score', sa.Numeric(8, 2)),
        sa.Column('balance_score', sa.Numeric(8, 2)),
        sa.Column('compliance_percent', sa.Numeric(5, 2)),
        sa.Column('notes', sa.Text),
    )
    op.create_table('therapy_exercises',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('therapy_plan_id', sa.String(36), sa.ForeignKey('therapy_plans.id'), nullable=False),
        sa.Column('exercise_id', sa.String(36), sa.ForeignKey('exercise_library.id'), nullable=False),
        sa.Column('sets', sa.Integer),
        sa.Column('repetitions', sa.Integer),
        sa.Column('duration_seconds', sa.Integer),
        sa.Column('frequency', sa.String(80)),
        sa.Column('progression', sa.Text),
    )
    op.create_table('therapy_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('therapist_id', sa.String(36), sa.ForeignKey('physical_therapists.id'), nullable=False),
        sa.Column('therapy_plan_id', sa.String(36), sa.ForeignKey('therapy_plans.id')),
        sa.Column('scheduled_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer),
        sa.Column('session_type', sa.String(60), nullable=False),
        sa.Column('interventions', sa.JSON),
        sa.Column('response', sa.Text),
        sa.Column('status', sa.String(30), nullable=False),
    )
    op.create_index('ix_dental_specialties_code', 'dental_specialties', ['code'], unique=True)
    op.create_index('ix_dental_specialties_name', 'dental_specialties', ['name'], unique=True)
    op.create_index('ix_dental_specialties_is_active', 'dental_specialties', ['is_active'], unique=False)
    op.create_index('ix_dental_specialties_created_at', 'dental_specialties', ['created_at'], unique=False)
    op.create_index('ix_dental_specialties_deleted_at', 'dental_specialties', ['deleted_at'], unique=False)
    op.create_index('ix_dental_specialties_tenant_id', 'dental_specialties', ['tenant_id'], unique=False)
    op.create_index('ix_departments_code', 'departments', ['code'], unique=True)
    op.create_index('ix_departments_name', 'departments', ['name'], unique=True)
    op.create_index('ix_departments_is_active', 'departments', ['is_active'], unique=False)
    op.create_index('ix_departments_created_at', 'departments', ['created_at'], unique=False)
    op.create_index('ix_departments_deleted_at', 'departments', ['deleted_at'], unique=False)
    op.create_index('ix_departments_tenant_id', 'departments', ['tenant_id'], unique=False)
    op.create_index('ix_exercise_library_code', 'exercise_library', ['code'], unique=True)
    op.create_index('ix_exercise_library_name', 'exercise_library', ['name'], unique=False)
    op.create_index('ix_exercise_library_category', 'exercise_library', ['category'], unique=False)
    op.create_index('ix_exercise_library_is_active', 'exercise_library', ['is_active'], unique=False)
    op.create_index('ix_exercise_library_created_at', 'exercise_library', ['created_at'], unique=False)
    op.create_index('ix_exercise_library_deleted_at', 'exercise_library', ['deleted_at'], unique=False)
    op.create_index('ix_exercise_library_tenant_id', 'exercise_library', ['tenant_id'], unique=False)
    op.create_index('ix_medications_generic_name', 'medications', ['generic_name'], unique=False)
    op.create_index('ix_medications_brand_name', 'medications', ['brand_name'], unique=False)
    op.create_index('ix_medications_code', 'medications', ['code'], unique=True)
    op.create_index('ix_medications_is_active', 'medications', ['is_active'], unique=False)
    op.create_index('ix_medications_created_at', 'medications', ['created_at'], unique=False)
    op.create_index('ix_medications_deleted_at', 'medications', ['deleted_at'], unique=False)
    op.create_index('ix_medications_tenant_id', 'medications', ['tenant_id'], unique=False)
    op.create_index('ix_permissions_code', 'permissions', ['code'], unique=True)
    op.create_index('ix_permissions_module', 'permissions', ['module'], unique=False)
    op.create_index('ix_permissions_is_active', 'permissions', ['is_active'], unique=False)
    op.create_index('ix_permissions_created_at', 'permissions', ['created_at'], unique=False)
    op.create_index('ix_permissions_deleted_at', 'permissions', ['deleted_at'], unique=False)
    op.create_index('ix_permissions_tenant_id', 'permissions', ['tenant_id'], unique=False)
    op.create_index('ix_roles_name', 'roles', ['name'], unique=True)
    op.create_index('ix_roles_is_active', 'roles', ['is_active'], unique=False)
    op.create_index('ix_roles_created_at', 'roles', ['created_at'], unique=False)
    op.create_index('ix_roles_deleted_at', 'roles', ['deleted_at'], unique=False)
    op.create_index('ix_roles_tenant_id', 'roles', ['tenant_id'], unique=False)
    op.create_index('ix_specialties_code', 'specialties', ['code'], unique=True)
    op.create_index('ix_specialties_name', 'specialties', ['name'], unique=True)
    op.create_index('ix_specialties_category', 'specialties', ['category'], unique=False)
    op.create_index('ix_specialties_is_active', 'specialties', ['is_active'], unique=False)
    op.create_index('ix_specialties_created_at', 'specialties', ['created_at'], unique=False)
    op.create_index('ix_specialties_deleted_at', 'specialties', ['deleted_at'], unique=False)
    op.create_index('ix_specialties_tenant_id', 'specialties', ['tenant_id'], unique=False)
    op.create_index('ix_system_settings_key', 'system_settings', ['key'], unique=True)
    op.create_index('ix_system_settings_category', 'system_settings', ['category'], unique=False)
    op.create_index('ix_system_settings_is_active', 'system_settings', ['is_active'], unique=False)
    op.create_index('ix_system_settings_created_at', 'system_settings', ['created_at'], unique=False)
    op.create_index('ix_system_settings_deleted_at', 'system_settings', ['deleted_at'], unique=False)
    op.create_index('ix_system_settings_tenant_id', 'system_settings', ['tenant_id'], unique=False)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_phone', 'users', ['phone'], unique=False)
    op.create_index('ix_users_is_active', 'users', ['is_active'], unique=False)
    op.create_index('ix_users_created_at', 'users', ['created_at'], unique=False)
    op.create_index('ix_users_deleted_at', 'users', ['deleted_at'], unique=False)
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'], unique=False)
    op.create_index('ix_audit_logs_tenant_id', 'audit_logs', ['tenant_id'], unique=False)
    op.create_index('ix_audit_logs_actor_user_id', 'audit_logs', ['actor_user_id'], unique=False)
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'], unique=False)
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'], unique=False)
    op.create_index('ix_audit_logs_resource_id', 'audit_logs', ['resource_id'], unique=False)
    op.create_index('ix_audit_logs_outcome', 'audit_logs', ['outcome'], unique=False)
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'], unique=False)
    op.create_index('ix_dentists_user_id', 'dentists', ['user_id'], unique=True)
    op.create_index('ix_dentists_dental_specialty_id', 'dentists', ['dental_specialty_id'], unique=False)
    op.create_index('ix_dentists_department_id', 'dentists', ['department_id'], unique=False)
    op.create_index('ix_dentists_license_number', 'dentists', ['license_number'], unique=True)
    op.create_index('ix_dentists_is_active', 'dentists', ['is_active'], unique=False)
    op.create_index('ix_dentists_created_at', 'dentists', ['created_at'], unique=False)
    op.create_index('ix_dentists_deleted_at', 'dentists', ['deleted_at'], unique=False)
    op.create_index('ix_dentists_tenant_id', 'dentists', ['tenant_id'], unique=False)
    op.create_index('ix_doctors_user_id', 'doctors', ['user_id'], unique=True)
    op.create_index('ix_doctors_specialty_id', 'doctors', ['specialty_id'], unique=False)
    op.create_index('ix_doctors_department_id', 'doctors', ['department_id'], unique=False)
    op.create_index('ix_doctors_license_number', 'doctors', ['license_number'], unique=True)
    op.create_index('ix_doctors_is_active', 'doctors', ['is_active'], unique=False)
    op.create_index('ix_doctors_created_at', 'doctors', ['created_at'], unique=False)
    op.create_index('ix_doctors_deleted_at', 'doctors', ['deleted_at'], unique=False)
    op.create_index('ix_doctors_tenant_id', 'doctors', ['tenant_id'], unique=False)
    op.create_index('ix_messages_sender_id', 'messages', ['sender_id'], unique=False)
    op.create_index('ix_messages_recipient_id', 'messages', ['recipient_id'], unique=False)
    op.create_index('ix_messages_is_active', 'messages', ['is_active'], unique=False)
    op.create_index('ix_messages_created_at', 'messages', ['created_at'], unique=False)
    op.create_index('ix_messages_deleted_at', 'messages', ['deleted_at'], unique=False)
    op.create_index('ix_messages_tenant_id', 'messages', ['tenant_id'], unique=False)
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'], unique=False)
    op.create_index('ix_notifications_category', 'notifications', ['category'], unique=False)
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'], unique=False)
    op.create_index('ix_notifications_is_active', 'notifications', ['is_active'], unique=False)
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'], unique=False)
    op.create_index('ix_notifications_deleted_at', 'notifications', ['deleted_at'], unique=False)
    op.create_index('ix_notifications_tenant_id', 'notifications', ['tenant_id'], unique=False)
    op.create_index('ix_patients_medical_record_number', 'patients', ['medical_record_number'], unique=True)
    op.create_index('ix_patients_user_id', 'patients', ['user_id'], unique=True)
    op.create_index('ix_patients_first_name', 'patients', ['first_name'], unique=False)
    op.create_index('ix_patients_last_name', 'patients', ['last_name'], unique=False)
    op.create_index('ix_patients_date_of_birth', 'patients', ['date_of_birth'], unique=False)
    op.create_index('ix_patients_phone', 'patients', ['phone'], unique=False)
    op.create_index('ix_patients_email', 'patients', ['email'], unique=False)
    op.create_index('ix_patients_is_active', 'patients', ['is_active'], unique=False)
    op.create_index('ix_patients_created_at', 'patients', ['created_at'], unique=False)
    op.create_index('ix_patients_deleted_at', 'patients', ['deleted_at'], unique=False)
    op.create_index('ix_patients_tenant_id', 'patients', ['tenant_id'], unique=False)
    op.create_index('ix_pharmacy_inventory_medication_id', 'pharmacy_inventory', ['medication_id'], unique=False)
    op.create_index('ix_pharmacy_inventory_batch_number', 'pharmacy_inventory', ['batch_number'], unique=False)
    op.create_index('ix_pharmacy_inventory_expiry_date', 'pharmacy_inventory', ['expiry_date'], unique=False)
    op.create_index('ix_pharmacy_inventory_is_active', 'pharmacy_inventory', ['is_active'], unique=False)
    op.create_index('ix_pharmacy_inventory_created_at', 'pharmacy_inventory', ['created_at'], unique=False)
    op.create_index('ix_pharmacy_inventory_deleted_at', 'pharmacy_inventory', ['deleted_at'], unique=False)
    op.create_index('ix_pharmacy_inventory_tenant_id', 'pharmacy_inventory', ['tenant_id'], unique=False)
    op.create_index('ix_physical_therapists_user_id', 'physical_therapists', ['user_id'], unique=True)
    op.create_index('ix_physical_therapists_department_id', 'physical_therapists', ['department_id'], unique=False)
    op.create_index('ix_physical_therapists_license_number', 'physical_therapists', ['license_number'], unique=True)
    op.create_index('ix_physical_therapists_specialty', 'physical_therapists', ['specialty'], unique=False)
    op.create_index('ix_physical_therapists_is_active', 'physical_therapists', ['is_active'], unique=False)
    op.create_index('ix_physical_therapists_created_at', 'physical_therapists', ['created_at'], unique=False)
    op.create_index('ix_physical_therapists_deleted_at', 'physical_therapists', ['deleted_at'], unique=False)
    op.create_index('ix_physical_therapists_tenant_id', 'physical_therapists', ['tenant_id'], unique=False)
    op.create_index('ix_appointments_doctor_start', 'appointments', ['doctor_id', 'scheduled_start'], unique=False)
    op.create_index('ix_appointments_appointment_number', 'appointments', ['appointment_number'], unique=True)
    op.create_index('ix_appointments_patient_id', 'appointments', ['patient_id'], unique=False)
    op.create_index('ix_appointments_doctor_id', 'appointments', ['doctor_id'], unique=False)
    op.create_index('ix_appointments_department_id', 'appointments', ['department_id'], unique=False)
    op.create_index('ix_appointments_scheduled_start', 'appointments', ['scheduled_start'], unique=False)
    op.create_index('ix_appointments_status', 'appointments', ['status'], unique=False)
    op.create_index('ix_appointments_is_active', 'appointments', ['is_active'], unique=False)
    op.create_index('ix_appointments_created_at', 'appointments', ['created_at'], unique=False)
    op.create_index('ix_appointments_deleted_at', 'appointments', ['deleted_at'], unique=False)
    op.create_index('ix_appointments_tenant_id', 'appointments', ['tenant_id'], unique=False)
    op.create_index('ix_care_teams_patient_id', 'care_teams', ['patient_id'], unique=False)
    op.create_index('ix_care_teams_lead_user_id', 'care_teams', ['lead_user_id'], unique=False)
    op.create_index('ix_care_teams_is_active', 'care_teams', ['is_active'], unique=False)
    op.create_index('ix_care_teams_created_at', 'care_teams', ['created_at'], unique=False)
    op.create_index('ix_care_teams_deleted_at', 'care_teams', ['deleted_at'], unique=False)
    op.create_index('ix_care_teams_tenant_id', 'care_teams', ['tenant_id'], unique=False)
    op.create_index('ix_referrals_patient_id', 'referrals', ['patient_id'], unique=False)
    op.create_index('ix_referrals_referring_user_id', 'referrals', ['referring_user_id'], unique=False)
    op.create_index('ix_referrals_receiving_department_id', 'referrals', ['receiving_department_id'], unique=False)
    op.create_index('ix_referrals_receiving_provider_id', 'referrals', ['receiving_provider_id'], unique=False)
    op.create_index('ix_referrals_referral_type', 'referrals', ['referral_type'], unique=False)
    op.create_index('ix_referrals_status', 'referrals', ['status'], unique=False)
    op.create_index('ix_referrals_referred_at', 'referrals', ['referred_at'], unique=False)
    op.create_index('ix_referrals_is_active', 'referrals', ['is_active'], unique=False)
    op.create_index('ix_referrals_created_at', 'referrals', ['created_at'], unique=False)
    op.create_index('ix_referrals_deleted_at', 'referrals', ['deleted_at'], unique=False)
    op.create_index('ix_referrals_tenant_id', 'referrals', ['tenant_id'], unique=False)
    op.create_index('ix_womens_health_profiles_patient_id', 'womens_health_profiles', ['patient_id'], unique=True)
    op.create_index('ix_womens_health_profiles_is_active', 'womens_health_profiles', ['is_active'], unique=False)
    op.create_index('ix_womens_health_profiles_created_at', 'womens_health_profiles', ['created_at'], unique=False)
    op.create_index('ix_womens_health_profiles_deleted_at', 'womens_health_profiles', ['deleted_at'], unique=False)
    op.create_index('ix_womens_health_profiles_tenant_id', 'womens_health_profiles', ['tenant_id'], unique=False)
    op.create_index('ix_gynecology_journeys_journey_number', 'gynecology_journeys', ['journey_number'], unique=True)
    op.create_index('ix_gynecology_journeys_profile_id', 'gynecology_journeys', ['profile_id'], unique=False)
    op.create_index('ix_gynecology_journeys_primary_condition', 'gynecology_journeys', ['primary_condition'], unique=False)
    op.create_index('ix_gynecology_journeys_started_at', 'gynecology_journeys', ['started_at'], unique=False)
    op.create_index('ix_gynecology_journeys_status', 'gynecology_journeys', ['status'], unique=False)
    op.create_index('ix_gynecology_journeys_is_active', 'gynecology_journeys', ['is_active'], unique=False)
    op.create_index('ix_gynecology_journeys_created_at', 'gynecology_journeys', ['created_at'], unique=False)
    op.create_index('ix_gynecology_journeys_deleted_at', 'gynecology_journeys', ['deleted_at'], unique=False)
    op.create_index('ix_gynecology_journeys_tenant_id', 'gynecology_journeys', ['tenant_id'], unique=False)
    op.create_index('ix_infertility_journeys_journey_number', 'infertility_journeys', ['journey_number'], unique=True)
    op.create_index('ix_infertility_journeys_profile_id', 'infertility_journeys', ['profile_id'], unique=False)
    op.create_index('ix_infertility_journeys_infertility_type', 'infertility_journeys', ['infertility_type'], unique=False)
    op.create_index('ix_infertility_journeys_started_at', 'infertility_journeys', ['started_at'], unique=False)
    op.create_index('ix_infertility_journeys_status', 'infertility_journeys', ['status'], unique=False)
    op.create_index('ix_infertility_journeys_is_active', 'infertility_journeys', ['is_active'], unique=False)
    op.create_index('ix_infertility_journeys_created_at', 'infertility_journeys', ['created_at'], unique=False)
    op.create_index('ix_infertility_journeys_deleted_at', 'infertility_journeys', ['deleted_at'], unique=False)
    op.create_index('ix_infertility_journeys_tenant_id', 'infertility_journeys', ['tenant_id'], unique=False)
    op.create_index('ix_medical_records_record_number', 'medical_records', ['record_number'], unique=True)
    op.create_index('ix_medical_records_patient_id', 'medical_records', ['patient_id'], unique=False)
    op.create_index('ix_medical_records_doctor_id', 'medical_records', ['doctor_id'], unique=False)
    op.create_index('ix_medical_records_appointment_id', 'medical_records', ['appointment_id'], unique=False)
    op.create_index('ix_medical_records_encounter_type', 'medical_records', ['encounter_type'], unique=False)
    op.create_index('ix_medical_records_encounter_at', 'medical_records', ['encounter_at'], unique=False)
    op.create_index('ix_medical_records_status', 'medical_records', ['status'], unique=False)
    op.create_index('ix_medical_records_is_active', 'medical_records', ['is_active'], unique=False)
    op.create_index('ix_medical_records_created_at', 'medical_records', ['created_at'], unique=False)
    op.create_index('ix_medical_records_deleted_at', 'medical_records', ['deleted_at'], unique=False)
    op.create_index('ix_medical_records_tenant_id', 'medical_records', ['tenant_id'], unique=False)
    op.create_index('ix_obstetric_history_profile_id', 'obstetric_history', ['profile_id'], unique=False)
    op.create_index('ix_obstetric_history_outcome', 'obstetric_history', ['outcome'], unique=False)
    op.create_index('ix_obstetric_history_is_active', 'obstetric_history', ['is_active'], unique=False)
    op.create_index('ix_obstetric_history_created_at', 'obstetric_history', ['created_at'], unique=False)
    op.create_index('ix_obstetric_history_deleted_at', 'obstetric_history', ['deleted_at'], unique=False)
    op.create_index('ix_obstetric_history_tenant_id', 'obstetric_history', ['tenant_id'], unique=False)
    op.create_index('ix_pregnancies_profile_id', 'pregnancies', ['profile_id'], unique=False)
    op.create_index('ix_pregnancies_lmp', 'pregnancies', ['lmp'], unique=False)
    op.create_index('ix_pregnancies_estimated_due_date', 'pregnancies', ['estimated_due_date'], unique=False)
    op.create_index('ix_pregnancies_risk_category', 'pregnancies', ['risk_category'], unique=False)
    op.create_index('ix_pregnancies_status', 'pregnancies', ['status'], unique=False)
    op.create_index('ix_pregnancies_is_active', 'pregnancies', ['is_active'], unique=False)
    op.create_index('ix_pregnancies_created_at', 'pregnancies', ['created_at'], unique=False)
    op.create_index('ix_pregnancies_deleted_at', 'pregnancies', ['deleted_at'], unique=False)
    op.create_index('ix_pregnancies_tenant_id', 'pregnancies', ['tenant_id'], unique=False)
    op.create_index('ix_ai_recommendations_patient_id', 'ai_recommendations', ['patient_id'], unique=False)
    op.create_index('ix_ai_recommendations_medical_record_id', 'ai_recommendations', ['medical_record_id'], unique=False)
    op.create_index('ix_ai_recommendations_recommendation_type', 'ai_recommendations', ['recommendation_type'], unique=False)
    op.create_index('ix_ai_recommendations_status', 'ai_recommendations', ['status'], unique=False)
    op.create_index('ix_ai_recommendations_reviewed_by_id', 'ai_recommendations', ['reviewed_by_id'], unique=False)
    op.create_index('ix_ai_recommendations_is_active', 'ai_recommendations', ['is_active'], unique=False)
    op.create_index('ix_ai_recommendations_created_at', 'ai_recommendations', ['created_at'], unique=False)
    op.create_index('ix_ai_recommendations_deleted_at', 'ai_recommendations', ['deleted_at'], unique=False)
    op.create_index('ix_ai_recommendations_tenant_id', 'ai_recommendations', ['tenant_id'], unique=False)
    op.create_index('ix_delivery_records_pregnancy_id', 'delivery_records', ['pregnancy_id'], unique=True)
    op.create_index('ix_delivery_records_delivered_at', 'delivery_records', ['delivered_at'], unique=False)
    op.create_index('ix_delivery_records_delivery_mode', 'delivery_records', ['delivery_mode'], unique=False)
    op.create_index('ix_delivery_records_is_active', 'delivery_records', ['is_active'], unique=False)
    op.create_index('ix_delivery_records_created_at', 'delivery_records', ['created_at'], unique=False)
    op.create_index('ix_delivery_records_deleted_at', 'delivery_records', ['deleted_at'], unique=False)
    op.create_index('ix_delivery_records_tenant_id', 'delivery_records', ['tenant_id'], unique=False)
    op.create_index('ix_dental_records_patient_id', 'dental_records', ['patient_id'], unique=False)
    op.create_index('ix_dental_records_dentist_id', 'dental_records', ['dentist_id'], unique=False)
    op.create_index('ix_dental_records_medical_record_id', 'dental_records', ['medical_record_id'], unique=False)
    op.create_index('ix_dental_records_visit_at', 'dental_records', ['visit_at'], unique=False)
    op.create_index('ix_dental_records_status', 'dental_records', ['status'], unique=False)
    op.create_index('ix_dental_records_is_active', 'dental_records', ['is_active'], unique=False)
    op.create_index('ix_dental_records_created_at', 'dental_records', ['created_at'], unique=False)
    op.create_index('ix_dental_records_deleted_at', 'dental_records', ['deleted_at'], unique=False)
    op.create_index('ix_dental_records_tenant_id', 'dental_records', ['tenant_id'], unique=False)
    op.create_index('ix_diagnoses_medical_record_id', 'diagnoses', ['medical_record_id'], unique=False)
    op.create_index('ix_diagnoses_patient_id', 'diagnoses', ['patient_id'], unique=False)
    op.create_index('ix_diagnoses_doctor_id', 'diagnoses', ['doctor_id'], unique=False)
    op.create_index('ix_diagnoses_icd10_code', 'diagnoses', ['icd10_code'], unique=False)
    op.create_index('ix_diagnoses_is_active', 'diagnoses', ['is_active'], unique=False)
    op.create_index('ix_diagnoses_created_at', 'diagnoses', ['created_at'], unique=False)
    op.create_index('ix_diagnoses_deleted_at', 'diagnoses', ['deleted_at'], unique=False)
    op.create_index('ix_diagnoses_tenant_id', 'diagnoses', ['tenant_id'], unique=False)
    op.create_index('ix_gynecology_visits_journey_id', 'gynecology_visits', ['journey_id'], unique=False)
    op.create_index('ix_gynecology_visits_medical_record_id', 'gynecology_visits', ['medical_record_id'], unique=False)
    op.create_index('ix_gynecology_visits_doctor_id', 'gynecology_visits', ['doctor_id'], unique=False)
    op.create_index('ix_gynecology_visits_visit_at', 'gynecology_visits', ['visit_at'], unique=False)
    op.create_index('ix_gynecology_visits_is_active', 'gynecology_visits', ['is_active'], unique=False)
    op.create_index('ix_gynecology_visits_created_at', 'gynecology_visits', ['created_at'], unique=False)
    op.create_index('ix_gynecology_visits_deleted_at', 'gynecology_visits', ['deleted_at'], unique=False)
    op.create_index('ix_gynecology_visits_tenant_id', 'gynecology_visits', ['tenant_id'], unique=False)
    op.create_index('ix_infertility_cycles_journey_id', 'infertility_cycles', ['journey_id'], unique=False)
    op.create_index('ix_infertility_cycles_cycle_type', 'infertility_cycles', ['cycle_type'], unique=False)
    op.create_index('ix_infertility_cycles_cycle_start_date', 'infertility_cycles', ['cycle_start_date'], unique=False)
    op.create_index('ix_infertility_cycles_status', 'infertility_cycles', ['status'], unique=False)
    op.create_index('ix_infertility_cycles_is_active', 'infertility_cycles', ['is_active'], unique=False)
    op.create_index('ix_infertility_cycles_created_at', 'infertility_cycles', ['created_at'], unique=False)
    op.create_index('ix_infertility_cycles_deleted_at', 'infertility_cycles', ['deleted_at'], unique=False)
    op.create_index('ix_infertility_cycles_tenant_id', 'infertility_cycles', ['tenant_id'], unique=False)
    op.create_index('ix_lab_orders_order_number', 'lab_orders', ['order_number'], unique=True)
    op.create_index('ix_lab_orders_patient_id', 'lab_orders', ['patient_id'], unique=False)
    op.create_index('ix_lab_orders_doctor_id', 'lab_orders', ['doctor_id'], unique=False)
    op.create_index('ix_lab_orders_medical_record_id', 'lab_orders', ['medical_record_id'], unique=False)
    op.create_index('ix_lab_orders_test_code', 'lab_orders', ['test_code'], unique=False)
    op.create_index('ix_lab_orders_test_name', 'lab_orders', ['test_name'], unique=False)
    op.create_index('ix_lab_orders_status', 'lab_orders', ['status'], unique=False)
    op.create_index('ix_lab_orders_ordered_at', 'lab_orders', ['ordered_at'], unique=False)
    op.create_index('ix_lab_orders_is_active', 'lab_orders', ['is_active'], unique=False)
    op.create_index('ix_lab_orders_created_at', 'lab_orders', ['created_at'], unique=False)
    op.create_index('ix_lab_orders_deleted_at', 'lab_orders', ['deleted_at'], unique=False)
    op.create_index('ix_lab_orders_tenant_id', 'lab_orders', ['tenant_id'], unique=False)
    op.create_index('ix_multidisciplinary_cases_case_number', 'multidisciplinary_cases', ['case_number'], unique=True)
    op.create_index('ix_multidisciplinary_cases_patient_id', 'multidisciplinary_cases', ['patient_id'], unique=False)
    op.create_index('ix_multidisciplinary_cases_care_team_id', 'multidisciplinary_cases', ['care_team_id'], unique=False)
    op.create_index('ix_multidisciplinary_cases_medical_record_id', 'multidisciplinary_cases', ['medical_record_id'], unique=False)
    op.create_index('ix_multidisciplinary_cases_status', 'multidisciplinary_cases', ['status'], unique=False)
    op.create_index('ix_multidisciplinary_cases_meeting_at', 'multidisciplinary_cases', ['meeting_at'], unique=False)
    op.create_index('ix_multidisciplinary_cases_is_active', 'multidisciplinary_cases', ['is_active'], unique=False)
    op.create_index('ix_multidisciplinary_cases_created_at', 'multidisciplinary_cases', ['created_at'], unique=False)
    op.create_index('ix_multidisciplinary_cases_deleted_at', 'multidisciplinary_cases', ['deleted_at'], unique=False)
    op.create_index('ix_multidisciplinary_cases_tenant_id', 'multidisciplinary_cases', ['tenant_id'], unique=False)
    op.create_index('ix_nursing_notes_patient_id', 'nursing_notes', ['patient_id'], unique=False)
    op.create_index('ix_nursing_notes_medical_record_id', 'nursing_notes', ['medical_record_id'], unique=False)
    op.create_index('ix_nursing_notes_nurse_user_id', 'nursing_notes', ['nurse_user_id'], unique=False)
    op.create_index('ix_nursing_notes_recorded_at', 'nursing_notes', ['recorded_at'], unique=False)
    op.create_index('ix_nursing_notes_is_active', 'nursing_notes', ['is_active'], unique=False)
    op.create_index('ix_nursing_notes_created_at', 'nursing_notes', ['created_at'], unique=False)
    op.create_index('ix_nursing_notes_deleted_at', 'nursing_notes', ['deleted_at'], unique=False)
    op.create_index('ix_nursing_notes_tenant_id', 'nursing_notes', ['tenant_id'], unique=False)
    op.create_index('ix_partner_records_journey_id', 'partner_records', ['journey_id'], unique=False)
    op.create_index('ix_partner_records_is_active', 'partner_records', ['is_active'], unique=False)
    op.create_index('ix_partner_records_created_at', 'partner_records', ['created_at'], unique=False)
    op.create_index('ix_partner_records_deleted_at', 'partner_records', ['deleted_at'], unique=False)
    op.create_index('ix_partner_records_tenant_id', 'partner_records', ['tenant_id'], unique=False)
    op.create_index('ix_postpartum_visits_pregnancy_id', 'postpartum_visits', ['pregnancy_id'], unique=False)
    op.create_index('ix_postpartum_visits_medical_record_id', 'postpartum_visits', ['medical_record_id'], unique=False)
    op.create_index('ix_postpartum_visits_visit_at', 'postpartum_visits', ['visit_at'], unique=False)
    op.create_index('ix_postpartum_visits_is_active', 'postpartum_visits', ['is_active'], unique=False)
    op.create_index('ix_postpartum_visits_created_at', 'postpartum_visits', ['created_at'], unique=False)
    op.create_index('ix_postpartum_visits_deleted_at', 'postpartum_visits', ['deleted_at'], unique=False)
    op.create_index('ix_postpartum_visits_tenant_id', 'postpartum_visits', ['tenant_id'], unique=False)
    op.create_index('ix_pregnancy_risk_flags_pregnancy_id', 'pregnancy_risk_flags', ['pregnancy_id'], unique=False)
    op.create_index('ix_pregnancy_risk_flags_code', 'pregnancy_risk_flags', ['code'], unique=False)
    op.create_index('ix_pregnancy_risk_flags_severity', 'pregnancy_risk_flags', ['severity'], unique=False)
    op.create_index('ix_pregnancy_risk_flags_identified_at', 'pregnancy_risk_flags', ['identified_at'], unique=False)
    op.create_index('ix_pregnancy_risk_flags_is_active', 'pregnancy_risk_flags', ['is_active'], unique=False)
    op.create_index('ix_pregnancy_risk_flags_created_at', 'pregnancy_risk_flags', ['created_at'], unique=False)
    op.create_index('ix_pregnancy_risk_flags_deleted_at', 'pregnancy_risk_flags', ['deleted_at'], unique=False)
    op.create_index('ix_pregnancy_risk_flags_tenant_id', 'pregnancy_risk_flags', ['tenant_id'], unique=False)
    op.create_index('ix_pregnancy_visits_pregnancy_id', 'pregnancy_visits', ['pregnancy_id'], unique=False)
    op.create_index('ix_pregnancy_visits_medical_record_id', 'pregnancy_visits', ['medical_record_id'], unique=False)
    op.create_index('ix_pregnancy_visits_doctor_id', 'pregnancy_visits', ['doctor_id'], unique=False)
    op.create_index('ix_pregnancy_visits_visit_at', 'pregnancy_visits', ['visit_at'], unique=False)
    op.create_index('ix_pregnancy_visits_is_active', 'pregnancy_visits', ['is_active'], unique=False)
    op.create_index('ix_pregnancy_visits_created_at', 'pregnancy_visits', ['created_at'], unique=False)
    op.create_index('ix_pregnancy_visits_deleted_at', 'pregnancy_visits', ['deleted_at'], unique=False)
    op.create_index('ix_pregnancy_visits_tenant_id', 'pregnancy_visits', ['tenant_id'], unique=False)
    op.create_index('ix_prescriptions_prescription_number', 'prescriptions', ['prescription_number'], unique=True)
    op.create_index('ix_prescriptions_patient_id', 'prescriptions', ['patient_id'], unique=False)
    op.create_index('ix_prescriptions_doctor_id', 'prescriptions', ['doctor_id'], unique=False)
    op.create_index('ix_prescriptions_medical_record_id', 'prescriptions', ['medical_record_id'], unique=False)
    op.create_index('ix_prescriptions_medication_id', 'prescriptions', ['medication_id'], unique=False)
    op.create_index('ix_prescriptions_prescribed_at', 'prescriptions', ['prescribed_at'], unique=False)
    op.create_index('ix_prescriptions_status', 'prescriptions', ['status'], unique=False)
    op.create_index('ix_prescriptions_is_active', 'prescriptions', ['is_active'], unique=False)
    op.create_index('ix_prescriptions_created_at', 'prescriptions', ['created_at'], unique=False)
    op.create_index('ix_prescriptions_deleted_at', 'prescriptions', ['deleted_at'], unique=False)
    op.create_index('ix_prescriptions_tenant_id', 'prescriptions', ['tenant_id'], unique=False)
    op.create_index('ix_radiology_orders_order_number', 'radiology_orders', ['order_number'], unique=True)
    op.create_index('ix_radiology_orders_patient_id', 'radiology_orders', ['patient_id'], unique=False)
    op.create_index('ix_radiology_orders_doctor_id', 'radiology_orders', ['doctor_id'], unique=False)
    op.create_index('ix_radiology_orders_medical_record_id', 'radiology_orders', ['medical_record_id'], unique=False)
    op.create_index('ix_radiology_orders_modality', 'radiology_orders', ['modality'], unique=False)
    op.create_index('ix_radiology_orders_status', 'radiology_orders', ['status'], unique=False)
    op.create_index('ix_radiology_orders_ordered_at', 'radiology_orders', ['ordered_at'], unique=False)
    op.create_index('ix_radiology_orders_dicom_study_uid', 'radiology_orders', ['dicom_study_uid'], unique=True)
    op.create_index('ix_radiology_orders_is_active', 'radiology_orders', ['is_active'], unique=False)
    op.create_index('ix_radiology_orders_created_at', 'radiology_orders', ['created_at'], unique=False)
    op.create_index('ix_radiology_orders_deleted_at', 'radiology_orders', ['deleted_at'], unique=False)
    op.create_index('ix_radiology_orders_tenant_id', 'radiology_orders', ['tenant_id'], unique=False)
    op.create_index('ix_therapy_assessments_patient_id', 'therapy_assessments', ['patient_id'], unique=False)
    op.create_index('ix_therapy_assessments_therapist_id', 'therapy_assessments', ['therapist_id'], unique=False)
    op.create_index('ix_therapy_assessments_medical_record_id', 'therapy_assessments', ['medical_record_id'], unique=False)
    op.create_index('ix_therapy_assessments_assessment_at', 'therapy_assessments', ['assessment_at'], unique=False)
    op.create_index('ix_therapy_assessments_is_active', 'therapy_assessments', ['is_active'], unique=False)
    op.create_index('ix_therapy_assessments_created_at', 'therapy_assessments', ['created_at'], unique=False)
    op.create_index('ix_therapy_assessments_deleted_at', 'therapy_assessments', ['deleted_at'], unique=False)
    op.create_index('ix_therapy_assessments_tenant_id', 'therapy_assessments', ['tenant_id'], unique=False)
    op.create_index('ix_vital_signs_patient_id', 'vital_signs', ['patient_id'], unique=False)
    op.create_index('ix_vital_signs_medical_record_id', 'vital_signs', ['medical_record_id'], unique=False)
    op.create_index('ix_vital_signs_recorded_by_id', 'vital_signs', ['recorded_by_id'], unique=False)
    op.create_index('ix_vital_signs_recorded_at', 'vital_signs', ['recorded_at'], unique=False)
    op.create_index('ix_vital_signs_is_active', 'vital_signs', ['is_active'], unique=False)
    op.create_index('ix_vital_signs_created_at', 'vital_signs', ['created_at'], unique=False)
    op.create_index('ix_vital_signs_deleted_at', 'vital_signs', ['deleted_at'], unique=False)
    op.create_index('ix_vital_signs_tenant_id', 'vital_signs', ['tenant_id'], unique=False)
    op.create_index('ix_womens_health_timeline_events_profile_id', 'womens_health_timeline_events', ['profile_id'], unique=False)
    op.create_index('ix_womens_health_timeline_events_pregnancy_id', 'womens_health_timeline_events', ['pregnancy_id'], unique=False)
    op.create_index('ix_womens_health_timeline_events_gynecology_journey_id', 'womens_health_timeline_events', ['gynecology_journey_id'], unique=False)
    op.create_index('ix_womens_health_timeline_events_infertility_journey_id', 'womens_health_timeline_events', ['infertility_journey_id'], unique=False)
    op.create_index('ix_womens_health_timeline_events_event_type', 'womens_health_timeline_events', ['event_type'], unique=False)
    op.create_index('ix_womens_health_timeline_events_event_at', 'womens_health_timeline_events', ['event_at'], unique=False)
    op.create_index('ix_womens_health_timeline_events_source_id', 'womens_health_timeline_events', ['source_id'], unique=False)
    op.create_index('ix_womens_health_timeline_events_is_active', 'womens_health_timeline_events', ['is_active'], unique=False)
    op.create_index('ix_womens_health_timeline_events_created_at', 'womens_health_timeline_events', ['created_at'], unique=False)
    op.create_index('ix_womens_health_timeline_events_deleted_at', 'womens_health_timeline_events', ['deleted_at'], unique=False)
    op.create_index('ix_womens_health_timeline_events_tenant_id', 'womens_health_timeline_events', ['tenant_id'], unique=False)
    op.create_index('ix_antenatal_visits_pregnancy_id', 'antenatal_visits', ['pregnancy_id'], unique=False)
    op.create_index('ix_antenatal_visits_pregnancy_visit_id', 'antenatal_visits', ['pregnancy_visit_id'], unique=True)
    op.create_index('ix_antenatal_visits_visit_at', 'antenatal_visits', ['visit_at'], unique=False)
    op.create_index('ix_antenatal_visits_is_active', 'antenatal_visits', ['is_active'], unique=False)
    op.create_index('ix_antenatal_visits_created_at', 'antenatal_visits', ['created_at'], unique=False)
    op.create_index('ix_antenatal_visits_deleted_at', 'antenatal_visits', ['deleted_at'], unique=False)
    op.create_index('ix_antenatal_visits_tenant_id', 'antenatal_visits', ['tenant_id'], unique=False)
    op.create_index('ix_dental_charts_dental_record_id', 'dental_charts', ['dental_record_id'], unique=False)
    op.create_index('ix_dental_charts_tooth_number', 'dental_charts', ['tooth_number'], unique=False)
    op.create_index('ix_dental_charts_condition', 'dental_charts', ['condition'], unique=False)
    op.create_index('ix_dental_charts_is_active', 'dental_charts', ['is_active'], unique=False)
    op.create_index('ix_dental_charts_created_at', 'dental_charts', ['created_at'], unique=False)
    op.create_index('ix_dental_charts_deleted_at', 'dental_charts', ['deleted_at'], unique=False)
    op.create_index('ix_dental_charts_tenant_id', 'dental_charts', ['tenant_id'], unique=False)
    op.create_index('ix_dental_images_dental_record_id', 'dental_images', ['dental_record_id'], unique=False)
    op.create_index('ix_dental_images_image_type', 'dental_images', ['image_type'], unique=False)
    op.create_index('ix_dental_images_tooth_number', 'dental_images', ['tooth_number'], unique=False)
    op.create_index('ix_dental_images_captured_at', 'dental_images', ['captured_at'], unique=False)
    op.create_index('ix_dental_images_is_active', 'dental_images', ['is_active'], unique=False)
    op.create_index('ix_dental_images_created_at', 'dental_images', ['created_at'], unique=False)
    op.create_index('ix_dental_images_deleted_at', 'dental_images', ['deleted_at'], unique=False)
    op.create_index('ix_dental_images_tenant_id', 'dental_images', ['tenant_id'], unique=False)
    op.create_index('ix_dental_procedures_dental_record_id', 'dental_procedures', ['dental_record_id'], unique=False)
    op.create_index('ix_dental_procedures_dentist_id', 'dental_procedures', ['dentist_id'], unique=False)
    op.create_index('ix_dental_procedures_tooth_number', 'dental_procedures', ['tooth_number'], unique=False)
    op.create_index('ix_dental_procedures_procedure_code', 'dental_procedures', ['procedure_code'], unique=False)
    op.create_index('ix_dental_procedures_performed_at', 'dental_procedures', ['performed_at'], unique=False)
    op.create_index('ix_dental_procedures_status', 'dental_procedures', ['status'], unique=False)
    op.create_index('ix_dental_procedures_is_active', 'dental_procedures', ['is_active'], unique=False)
    op.create_index('ix_dental_procedures_created_at', 'dental_procedures', ['created_at'], unique=False)
    op.create_index('ix_dental_procedures_deleted_at', 'dental_procedures', ['deleted_at'], unique=False)
    op.create_index('ix_dental_procedures_tenant_id', 'dental_procedures', ['tenant_id'], unique=False)
    op.create_index('ix_fertility_medication_protocols_infertility_cycle_id', 'fertility_medication_protocols', ['infertility_cycle_id'], unique=False)
    op.create_index('ix_fertility_medication_protocols_medication_id', 'fertility_medication_protocols', ['medication_id'], unique=False)
    op.create_index('ix_fertility_medication_protocols_is_active', 'fertility_medication_protocols', ['is_active'], unique=False)
    op.create_index('ix_fertility_medication_protocols_created_at', 'fertility_medication_protocols', ['created_at'], unique=False)
    op.create_index('ix_fertility_medication_protocols_deleted_at', 'fertility_medication_protocols', ['deleted_at'], unique=False)
    op.create_index('ix_fertility_medication_protocols_tenant_id', 'fertility_medication_protocols', ['tenant_id'], unique=False)
    op.create_index('ix_folliculometry_records_infertility_cycle_id', 'folliculometry_records', ['infertility_cycle_id'], unique=False)
    op.create_index('ix_folliculometry_records_scan_at', 'folliculometry_records', ['scan_at'], unique=False)
    op.create_index('ix_folliculometry_records_is_active', 'folliculometry_records', ['is_active'], unique=False)
    op.create_index('ix_folliculometry_records_created_at', 'folliculometry_records', ['created_at'], unique=False)
    op.create_index('ix_folliculometry_records_deleted_at', 'folliculometry_records', ['deleted_at'], unique=False)
    op.create_index('ix_folliculometry_records_tenant_id', 'folliculometry_records', ['tenant_id'], unique=False)
    op.create_index('ix_lab_results_lab_order_id', 'lab_results', ['lab_order_id'], unique=False)
    op.create_index('ix_lab_results_component_name', 'lab_results', ['component_name'], unique=False)
    op.create_index('ix_lab_results_abnormal_flag', 'lab_results', ['abnormal_flag'], unique=False)
    op.create_index('ix_lab_results_is_critical', 'lab_results', ['is_critical'], unique=False)
    op.create_index('ix_lab_results_status', 'lab_results', ['status'], unique=False)
    op.create_index('ix_lab_results_resulted_at', 'lab_results', ['resulted_at'], unique=False)
    op.create_index('ix_lab_results_validated_by_id', 'lab_results', ['validated_by_id'], unique=False)
    op.create_index('ix_lab_results_is_active', 'lab_results', ['is_active'], unique=False)
    op.create_index('ix_lab_results_created_at', 'lab_results', ['created_at'], unique=False)
    op.create_index('ix_lab_results_deleted_at', 'lab_results', ['deleted_at'], unique=False)
    op.create_index('ix_lab_results_tenant_id', 'lab_results', ['tenant_id'], unique=False)
    op.create_index('ix_orthodontic_cases_patient_id', 'orthodontic_cases', ['patient_id'], unique=False)
    op.create_index('ix_orthodontic_cases_dentist_id', 'orthodontic_cases', ['dentist_id'], unique=False)
    op.create_index('ix_orthodontic_cases_dental_record_id', 'orthodontic_cases', ['dental_record_id'], unique=False)
    op.create_index('ix_orthodontic_cases_status', 'orthodontic_cases', ['status'], unique=False)
    op.create_index('ix_orthodontic_cases_is_active', 'orthodontic_cases', ['is_active'], unique=False)
    op.create_index('ix_orthodontic_cases_created_at', 'orthodontic_cases', ['created_at'], unique=False)
    op.create_index('ix_orthodontic_cases_deleted_at', 'orthodontic_cases', ['deleted_at'], unique=False)
    op.create_index('ix_orthodontic_cases_tenant_id', 'orthodontic_cases', ['tenant_id'], unique=False)
    op.create_index('ix_ovulation_induction_cycles_infertility_cycle_id', 'ovulation_induction_cycles', ['infertility_cycle_id'], unique=True)
    op.create_index('ix_ovulation_induction_cycles_is_active', 'ovulation_induction_cycles', ['is_active'], unique=False)
    op.create_index('ix_ovulation_induction_cycles_created_at', 'ovulation_induction_cycles', ['created_at'], unique=False)
    op.create_index('ix_ovulation_induction_cycles_deleted_at', 'ovulation_induction_cycles', ['deleted_at'], unique=False)
    op.create_index('ix_ovulation_induction_cycles_tenant_id', 'ovulation_induction_cycles', ['tenant_id'], unique=False)
    op.create_index('ix_radiology_reports_radiology_order_id', 'radiology_reports', ['radiology_order_id'], unique=False)
    op.create_index('ix_radiology_reports_radiologist_id', 'radiology_reports', ['radiologist_id'], unique=False)
    op.create_index('ix_radiology_reports_status', 'radiology_reports', ['status'], unique=False)
    op.create_index('ix_radiology_reports_is_critical', 'radiology_reports', ['is_critical'], unique=False)
    op.create_index('ix_radiology_reports_reported_at', 'radiology_reports', ['reported_at'], unique=False)
    op.create_index('ix_radiology_reports_is_active', 'radiology_reports', ['is_active'], unique=False)
    op.create_index('ix_radiology_reports_created_at', 'radiology_reports', ['created_at'], unique=False)
    op.create_index('ix_radiology_reports_deleted_at', 'radiology_reports', ['deleted_at'], unique=False)
    op.create_index('ix_radiology_reports_tenant_id', 'radiology_reports', ['tenant_id'], unique=False)
    op.create_index('ix_semen_analyses_partner_id', 'semen_analyses', ['partner_id'], unique=False)
    op.create_index('ix_semen_analyses_collected_at', 'semen_analyses', ['collected_at'], unique=False)
    op.create_index('ix_semen_analyses_is_active', 'semen_analyses', ['is_active'], unique=False)
    op.create_index('ix_semen_analyses_created_at', 'semen_analyses', ['created_at'], unique=False)
    op.create_index('ix_semen_analyses_deleted_at', 'semen_analyses', ['deleted_at'], unique=False)
    op.create_index('ix_semen_analyses_tenant_id', 'semen_analyses', ['tenant_id'], unique=False)
    op.create_index('ix_therapy_plans_patient_id', 'therapy_plans', ['patient_id'], unique=False)
    op.create_index('ix_therapy_plans_therapist_id', 'therapy_plans', ['therapist_id'], unique=False)
    op.create_index('ix_therapy_plans_assessment_id', 'therapy_plans', ['assessment_id'], unique=False)
    op.create_index('ix_therapy_plans_start_date', 'therapy_plans', ['start_date'], unique=False)
    op.create_index('ix_therapy_plans_status', 'therapy_plans', ['status'], unique=False)
    op.create_index('ix_therapy_plans_is_active', 'therapy_plans', ['is_active'], unique=False)
    op.create_index('ix_therapy_plans_created_at', 'therapy_plans', ['created_at'], unique=False)
    op.create_index('ix_therapy_plans_deleted_at', 'therapy_plans', ['deleted_at'], unique=False)
    op.create_index('ix_therapy_plans_tenant_id', 'therapy_plans', ['tenant_id'], unique=False)
    op.create_index('ix_womens_health_calculations_profile_id', 'womens_health_calculations', ['profile_id'], unique=False)
    op.create_index('ix_womens_health_calculations_pregnancy_id', 'womens_health_calculations', ['pregnancy_id'], unique=False)
    op.create_index('ix_womens_health_calculations_infertility_cycle_id', 'womens_health_calculations', ['infertility_cycle_id'], unique=False)
    op.create_index('ix_womens_health_calculations_calculation_type', 'womens_health_calculations', ['calculation_type'], unique=False)
    op.create_index('ix_womens_health_calculations_calculated_at', 'womens_health_calculations', ['calculated_at'], unique=False)
    op.create_index('ix_womens_health_calculations_calculated_by_id', 'womens_health_calculations', ['calculated_by_id'], unique=False)
    op.create_index('ix_womens_health_calculations_is_active', 'womens_health_calculations', ['is_active'], unique=False)
    op.create_index('ix_womens_health_calculations_created_at', 'womens_health_calculations', ['created_at'], unique=False)
    op.create_index('ix_womens_health_calculations_deleted_at', 'womens_health_calculations', ['deleted_at'], unique=False)
    op.create_index('ix_womens_health_calculations_tenant_id', 'womens_health_calculations', ['tenant_id'], unique=False)
    op.create_index('ix_womens_ultrasound_reports_report_number', 'womens_ultrasound_reports', ['report_number'], unique=True)
    op.create_index('ix_womens_ultrasound_reports_profile_id', 'womens_ultrasound_reports', ['profile_id'], unique=False)
    op.create_index('ix_womens_ultrasound_reports_pregnancy_id', 'womens_ultrasound_reports', ['pregnancy_id'], unique=False)
    op.create_index('ix_womens_ultrasound_reports_gynecology_journey_id', 'womens_ultrasound_reports', ['gynecology_journey_id'], unique=False)
    op.create_index('ix_womens_ultrasound_reports_infertility_journey_id', 'womens_ultrasound_reports', ['infertility_journey_id'], unique=False)
    op.create_index('ix_womens_ultrasound_reports_medical_record_id', 'womens_ultrasound_reports', ['medical_record_id'], unique=False)
    op.create_index('ix_womens_ultrasound_reports_radiology_order_id', 'womens_ultrasound_reports', ['radiology_order_id'], unique=False)
    op.create_index('ix_womens_ultrasound_reports_performed_by_id', 'womens_ultrasound_reports', ['performed_by_id'], unique=False)
    op.create_index('ix_womens_ultrasound_reports_scan_type', 'womens_ultrasound_reports', ['scan_type'], unique=False)
    op.create_index('ix_womens_ultrasound_reports_performed_at', 'womens_ultrasound_reports', ['performed_at'], unique=False)
    op.create_index('ix_womens_ultrasound_reports_status', 'womens_ultrasound_reports', ['status'], unique=False)
    op.create_index('ix_womens_ultrasound_reports_is_active', 'womens_ultrasound_reports', ['is_active'], unique=False)
    op.create_index('ix_womens_ultrasound_reports_created_at', 'womens_ultrasound_reports', ['created_at'], unique=False)
    op.create_index('ix_womens_ultrasound_reports_deleted_at', 'womens_ultrasound_reports', ['deleted_at'], unique=False)
    op.create_index('ix_womens_ultrasound_reports_tenant_id', 'womens_ultrasound_reports', ['tenant_id'], unique=False)
    op.create_index('ix_fetal_biometry_ultrasound_report_id', 'fetal_biometry', ['ultrasound_report_id'], unique=False)
    op.create_index('ix_fetal_biometry_is_active', 'fetal_biometry', ['is_active'], unique=False)
    op.create_index('ix_fetal_biometry_created_at', 'fetal_biometry', ['created_at'], unique=False)
    op.create_index('ix_fetal_biometry_deleted_at', 'fetal_biometry', ['deleted_at'], unique=False)
    op.create_index('ix_fetal_biometry_tenant_id', 'fetal_biometry', ['tenant_id'], unique=False)
    op.create_index('ix_fetal_doppler_records_ultrasound_report_id', 'fetal_doppler_records', ['ultrasound_report_id'], unique=False)
    op.create_index('ix_fetal_doppler_records_vessel', 'fetal_doppler_records', ['vessel'], unique=False)
    op.create_index('ix_fetal_doppler_records_is_active', 'fetal_doppler_records', ['is_active'], unique=False)
    op.create_index('ix_fetal_doppler_records_created_at', 'fetal_doppler_records', ['created_at'], unique=False)
    op.create_index('ix_fetal_doppler_records_deleted_at', 'fetal_doppler_records', ['deleted_at'], unique=False)
    op.create_index('ix_fetal_doppler_records_tenant_id', 'fetal_doppler_records', ['tenant_id'], unique=False)
    op.create_index('ix_follicle_measurements_folliculometry_record_id', 'follicle_measurements', ['folliculometry_record_id'], unique=False)
    op.create_index('ix_follicle_measurements_is_active', 'follicle_measurements', ['is_active'], unique=False)
    op.create_index('ix_follicle_measurements_created_at', 'follicle_measurements', ['created_at'], unique=False)
    op.create_index('ix_follicle_measurements_deleted_at', 'follicle_measurements', ['deleted_at'], unique=False)
    op.create_index('ix_follicle_measurements_tenant_id', 'follicle_measurements', ['tenant_id'], unique=False)
    op.create_index('ix_functional_outcomes_patient_id', 'functional_outcomes', ['patient_id'], unique=False)
    op.create_index('ix_functional_outcomes_therapy_plan_id', 'functional_outcomes', ['therapy_plan_id'], unique=False)
    op.create_index('ix_functional_outcomes_instrument', 'functional_outcomes', ['instrument'], unique=False)
    op.create_index('ix_functional_outcomes_measured_at', 'functional_outcomes', ['measured_at'], unique=False)
    op.create_index('ix_functional_outcomes_is_active', 'functional_outcomes', ['is_active'], unique=False)
    op.create_index('ix_functional_outcomes_created_at', 'functional_outcomes', ['created_at'], unique=False)
    op.create_index('ix_functional_outcomes_deleted_at', 'functional_outcomes', ['deleted_at'], unique=False)
    op.create_index('ix_functional_outcomes_tenant_id', 'functional_outcomes', ['tenant_id'], unique=False)
    op.create_index('ix_gynecology_ultrasound_records_ultrasound_report_id', 'gynecology_ultrasound_records', ['ultrasound_report_id'], unique=True)
    op.create_index('ix_gynecology_ultrasound_records_is_active', 'gynecology_ultrasound_records', ['is_active'], unique=False)
    op.create_index('ix_gynecology_ultrasound_records_created_at', 'gynecology_ultrasound_records', ['created_at'], unique=False)
    op.create_index('ix_gynecology_ultrasound_records_deleted_at', 'gynecology_ultrasound_records', ['deleted_at'], unique=False)
    op.create_index('ix_gynecology_ultrasound_records_tenant_id', 'gynecology_ultrasound_records', ['tenant_id'], unique=False)
    op.create_index('ix_iui_cycles_infertility_cycle_id', 'iui_cycles', ['infertility_cycle_id'], unique=True)
    op.create_index('ix_iui_cycles_partner_id', 'iui_cycles', ['partner_id'], unique=False)
    op.create_index('ix_iui_cycles_performed_at', 'iui_cycles', ['performed_at'], unique=False)
    op.create_index('ix_iui_cycles_semen_analysis_id', 'iui_cycles', ['semen_analysis_id'], unique=False)
    op.create_index('ix_iui_cycles_is_active', 'iui_cycles', ['is_active'], unique=False)
    op.create_index('ix_iui_cycles_created_at', 'iui_cycles', ['created_at'], unique=False)
    op.create_index('ix_iui_cycles_deleted_at', 'iui_cycles', ['deleted_at'], unique=False)
    op.create_index('ix_iui_cycles_tenant_id', 'iui_cycles', ['tenant_id'], unique=False)
    op.create_index('ix_rehabilitation_progress_patient_id', 'rehabilitation_progress', ['patient_id'], unique=False)
    op.create_index('ix_rehabilitation_progress_therapy_plan_id', 'rehabilitation_progress', ['therapy_plan_id'], unique=False)
    op.create_index('ix_rehabilitation_progress_recorded_at', 'rehabilitation_progress', ['recorded_at'], unique=False)
    op.create_index('ix_rehabilitation_progress_is_active', 'rehabilitation_progress', ['is_active'], unique=False)
    op.create_index('ix_rehabilitation_progress_created_at', 'rehabilitation_progress', ['created_at'], unique=False)
    op.create_index('ix_rehabilitation_progress_deleted_at', 'rehabilitation_progress', ['deleted_at'], unique=False)
    op.create_index('ix_rehabilitation_progress_tenant_id', 'rehabilitation_progress', ['tenant_id'], unique=False)
    op.create_index('ix_therapy_exercises_therapy_plan_id', 'therapy_exercises', ['therapy_plan_id'], unique=False)
    op.create_index('ix_therapy_exercises_exercise_id', 'therapy_exercises', ['exercise_id'], unique=False)
    op.create_index('ix_therapy_exercises_is_active', 'therapy_exercises', ['is_active'], unique=False)
    op.create_index('ix_therapy_exercises_created_at', 'therapy_exercises', ['created_at'], unique=False)
    op.create_index('ix_therapy_exercises_deleted_at', 'therapy_exercises', ['deleted_at'], unique=False)
    op.create_index('ix_therapy_exercises_tenant_id', 'therapy_exercises', ['tenant_id'], unique=False)
    op.create_index('ix_therapy_sessions_patient_id', 'therapy_sessions', ['patient_id'], unique=False)
    op.create_index('ix_therapy_sessions_therapist_id', 'therapy_sessions', ['therapist_id'], unique=False)
    op.create_index('ix_therapy_sessions_therapy_plan_id', 'therapy_sessions', ['therapy_plan_id'], unique=False)
    op.create_index('ix_therapy_sessions_scheduled_start', 'therapy_sessions', ['scheduled_start'], unique=False)
    op.create_index('ix_therapy_sessions_status', 'therapy_sessions', ['status'], unique=False)
    op.create_index('ix_therapy_sessions_is_active', 'therapy_sessions', ['is_active'], unique=False)
    op.create_index('ix_therapy_sessions_created_at', 'therapy_sessions', ['created_at'], unique=False)
    op.create_index('ix_therapy_sessions_deleted_at', 'therapy_sessions', ['deleted_at'], unique=False)
    op.create_index('ix_therapy_sessions_tenant_id', 'therapy_sessions', ['tenant_id'], unique=False)


def downgrade():
    op.drop_table('therapy_sessions')
    op.drop_table('therapy_exercises')
    op.drop_table('rehabilitation_progress')
    op.drop_table('iui_cycles')
    op.drop_table('gynecology_ultrasound_records')
    op.drop_table('functional_outcomes')
    op.drop_table('follicle_measurements')
    op.drop_table('fetal_doppler_records')
    op.drop_table('fetal_biometry')
    op.drop_table('womens_ultrasound_reports')
    op.drop_table('womens_health_calculations')
    op.drop_table('therapy_plans')
    op.drop_table('semen_analyses')
    op.drop_table('radiology_reports')
    op.drop_table('ovulation_induction_cycles')
    op.drop_table('orthodontic_cases')
    op.drop_table('lab_results')
    op.drop_table('folliculometry_records')
    op.drop_table('fertility_medication_protocols')
    op.drop_table('dental_procedures')
    op.drop_table('dental_images')
    op.drop_table('dental_charts')
    op.drop_table('antenatal_visits')
    op.drop_table('womens_health_timeline_events')
    op.drop_table('vital_signs')
    op.drop_table('therapy_assessments')
    op.drop_table('radiology_orders')
    op.drop_table('prescriptions')
    op.drop_table('pregnancy_visits')
    op.drop_table('pregnancy_risk_flags')
    op.drop_table('postpartum_visits')
    op.drop_table('partner_records')
    op.drop_table('nursing_notes')
    op.drop_table('multidisciplinary_cases')
    op.drop_table('lab_orders')
    op.drop_table('infertility_cycles')
    op.drop_table('gynecology_visits')
    op.drop_table('diagnoses')
    op.drop_table('dental_records')
    op.drop_table('delivery_records')
    op.drop_table('ai_recommendations')
    op.drop_table('pregnancies')
    op.drop_table('obstetric_history')
    op.drop_table('medical_records')
    op.drop_table('infertility_journeys')
    op.drop_table('gynecology_journeys')
    op.drop_table('care_team_members')
    op.drop_table('womens_health_profiles')
    op.drop_table('referrals')
    op.drop_table('care_teams')
    op.drop_table('appointments')
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_table('physical_therapists')
    op.drop_table('pharmacy_inventory')
    op.drop_table('patients')
    op.drop_table('notifications')
    op.drop_table('messages')
    op.drop_table('doctors')
    op.drop_table('dentists')
    op.drop_table('audit_logs')
    op.drop_table('users')
    op.drop_table('system_settings')
    op.drop_table('specialties')
    op.drop_table('roles')
    op.drop_table('permissions')
    op.drop_table('medications')
    op.drop_table('exercise_library')
    op.drop_table('departments')
    op.drop_table('dental_specialties')

