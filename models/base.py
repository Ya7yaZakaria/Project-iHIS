"""Portable model primitives shared across all iHIS domains."""

from datetime import datetime, timezone
from uuid import uuid4

from extensions import db


def utcnow():
    return datetime.now(timezone.utc)


def new_uuid():
    return str(uuid4())


class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)


class SoftDeleteMixin:
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True, index=True)

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def soft_delete(self):
        self.deleted_at = utcnow()

    def restore(self):
        self.deleted_at = None


class TenantMixin:
    tenant_id = db.Column(db.String(36), nullable=True, index=True)


class BaseModel(db.Model, TimestampMixin, SoftDeleteMixin, TenantMixin):
    __abstract__ = True
    id = db.Column(db.String(36), primary_key=True, default=new_uuid)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"
