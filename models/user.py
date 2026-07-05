"""Identity, authorization, communication, and administration models."""

from datetime import timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from .base import BaseModel, TimestampMixin, new_uuid, utcnow


ROLE_PRIORITY = (
    "Super Admin", "Admin", "Women’s Health Doctor", "Doctor", "Receptionist",
    "Nurse", "Laboratory", "Radiology", "Pharmacist", "Dentist",
    "Rehabilitation Specialist", "Patient",
)


user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("role_id", db.String(36), db.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.String(36), db.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    db.Column("permission_id", db.String(36), db.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Role(BaseModel):
    __tablename__ = "roles"
    name = db.Column(db.String(80), nullable=False, unique=True, index=True)
    description = db.Column(db.String(255))
    is_system = db.Column(db.Boolean, nullable=False, default=False)
    users = db.relationship("User", secondary=user_roles, back_populates="roles")
    permissions = db.relationship("Permission", secondary=role_permissions, back_populates="roles")


class Permission(BaseModel):
    __tablename__ = "permissions"
    code = db.Column(db.String(120), nullable=False, unique=True, index=True)
    module = db.Column(db.String(60), nullable=False, index=True)
    action = db.Column(db.String(40), nullable=False)
    description = db.Column(db.String(255))
    roles = db.relationship("Role", secondary=role_permissions, back_populates="permissions")


class User(BaseModel, UserMixin):
    __tablename__ = "users"
    username = db.Column(db.String(80), nullable=False, unique=True, index=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(40), index=True)
    department_id = db.Column(db.String(36), db.ForeignKey("departments.id"), index=True)
    last_login_at = db.Column(db.DateTime(timezone=True))
    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime(timezone=True), index=True)
    password_changed_at = db.Column(db.DateTime(timezone=True))
    must_change_password = db.Column(db.Boolean, nullable=False, default=True)
    roles = db.relationship("Role", secondary=user_roles, back_populates="users")
    department = db.relationship("Department", foreign_keys=[department_id])
    doctor_profile = db.relationship("Doctor", back_populates="user", uselist=False)

    def set_password(self, password):
        if not password:
            raise ValueError("Password cannot be empty")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_permission(self, code):
        return any(permission.code == code for role in self.roles for permission in role.permissions)

    def has_role(self, *names):
        return any(role.name in names for role in self.roles)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def primary_role(self):
        by_name = {role.name: role for role in self.roles}
        return next((by_name[name] for name in ROLE_PRIORITY if name in by_name), self.roles[0] if self.roles else None)

    @property
    def role_id(self):
        role = self.primary_role
        return role.id if role else None

    @property
    def is_locked(self):
        if not self.locked_until:
            return False
        locked_until = self.locked_until
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        return locked_until > utcnow()

    def reset_failed_logins(self):
        self.failed_login_attempts = 0
        self.locked_until = None

    @property
    def is_authenticated(self):
        return bool(self.is_active and not self.is_deleted)


class Department(BaseModel):
    __tablename__ = "departments"
    code = db.Column(db.String(30), nullable=False, unique=True, index=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    description = db.Column(db.String(255))
    location = db.Column(db.String(120))
    department_type = db.Column(db.String(40), nullable=False, default="Clinical", index=True)


class Notification(BaseModel):
    __tablename__ = "notifications"
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(160), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(40), nullable=False, default="general", index=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    read_at = db.Column(db.DateTime(timezone=True))
    data = db.Column(db.JSON)
    user = db.relationship("User", foreign_keys=[user_id])


class Message(BaseModel):
    __tablename__ = "messages"
    sender_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    recipient_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    subject = db.Column(db.String(160))
    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime(timezone=True))
    read_at = db.Column(db.DateTime(timezone=True))
    sender = db.relationship("User", foreign_keys=[sender_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])


class AuditLog(db.Model, TimestampMixin):
    __tablename__ = "audit_logs"
    id = db.Column(db.String(36), primary_key=True, default=new_uuid)
    tenant_id = db.Column(db.String(36), index=True)
    actor_user_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)
    action = db.Column(db.String(120), nullable=False, index=True)
    resource_type = db.Column(db.String(100), nullable=False, index=True)
    resource_id = db.Column(db.String(36), index=True)
    outcome = db.Column(db.String(30), nullable=False, default="success", index=True)
    ip_address = db.Column(db.String(45))
    details = db.Column(db.JSON)
    actor = db.relationship("User", foreign_keys=[actor_user_id])


class AIRecommendation(BaseModel):
    __tablename__ = "ai_recommendations"
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    medical_record_id = db.Column(db.String(36), db.ForeignKey("medical_records.id"), index=True)
    recommendation_type = db.Column(db.String(80), nullable=False, index=True)
    model_name = db.Column(db.String(120))
    model_version = db.Column(db.String(60))
    content = db.Column(db.JSON, nullable=False)
    confidence = db.Column(db.Numeric(5, 4))
    status = db.Column(db.String(30), nullable=False, default="pending_review", index=True)
    reviewed_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)
    reviewed_at = db.Column(db.DateTime(timezone=True))


class SystemSetting(BaseModel):
    __tablename__ = "system_settings"
    key = db.Column(db.String(120), nullable=False, unique=True, index=True)
    value = db.Column(db.JSON)
    category = db.Column(db.String(60), nullable=False, default="general", index=True)
    is_secret = db.Column(db.Boolean, nullable=False, default=False)
    description = db.Column(db.String(255))
