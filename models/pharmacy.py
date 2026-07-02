"""Pharmacy inventory model."""

from extensions import db
from .base import BaseModel


class PharmacyInventory(BaseModel):
    __tablename__ = "pharmacy_inventory"
    __table_args__ = (db.UniqueConstraint("medication_id", "batch_number", name="uq_inventory_medication_batch"),)
    medication_id = db.Column(db.String(36), db.ForeignKey("medications.id"), nullable=False, index=True)
    batch_number = db.Column(db.String(80), nullable=False, index=True)
    quantity_on_hand = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    reorder_level = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    unit_cost = db.Column(db.Numeric(12, 2))
    expiry_date = db.Column(db.Date, index=True)
    location = db.Column(db.String(120))
    medication = db.relationship("Medication")
