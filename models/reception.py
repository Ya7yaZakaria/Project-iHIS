"""Reception module models.

Phase 14 keeps reception practical:
- Reuse Appointment for queue/check-in/follow-up.
- Add only a billing initiation placeholder.
"""

from extensions import db
from .base import BaseModel


class BillingInitiation(BaseModel):
    __tablename__ = "billing_initiations"

    patient_id = db.Column(
        db.String(36),
        db.ForeignKey("patients.id"),
        nullable=False,
        index=True,
    )
    appointment_id = db.Column(
        db.String(36),
        db.ForeignKey("appointments.id"),
        nullable=True,
        index=True,
    )
    status = db.Column(
        db.String(30),
        nullable=False,
        default="pending",
        index=True,
    )
    started_by_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    notes = db.Column(db.Text)

    patient = db.relationship("Patient")
    appointment = db.relationship("Appointment")
    started_by = db.relationship("User", foreign_keys=[started_by_id])