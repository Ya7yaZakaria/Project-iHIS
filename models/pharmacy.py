"""Pharmacy batch inventory, dispensing, movement, and medication history models."""

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
    supplier = db.Column(db.String(160))
    medication = db.relationship("Medication", backref="inventory_batches")
    dispensing_records = db.relationship("DispensingRecord", back_populates="inventory_batch")
    movements = db.relationship("StockMovement", back_populates="inventory_batch")


class DispensingRecord(BaseModel):
    __tablename__ = "dispensing_records"
    prescription_item_id = db.Column(db.String(36), db.ForeignKey("prescription_items.id"), nullable=False, index=True)
    inventory_batch_id = db.Column(db.String(36), db.ForeignKey("pharmacy_inventory.id"), nullable=False, index=True)
    medication_id = db.Column(db.String(36), db.ForeignKey("medications.id"), nullable=False, index=True)
    pharmacist_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    quantity = db.Column(db.Numeric(12, 2), nullable=False)
    dispensed_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    notes = db.Column(db.Text)
    prescription_item = db.relationship("PrescriptionItem", back_populates="dispensing_records")
    inventory_batch = db.relationship("PharmacyInventory", back_populates="dispensing_records")
    medication = db.relationship("Medication")
    pharmacist = db.relationship("User")


class StockMovement(BaseModel):
    __tablename__ = "stock_movements"
    inventory_batch_id = db.Column(db.String(36), db.ForeignKey("pharmacy_inventory.id"), nullable=False, index=True)
    medication_id = db.Column(db.String(36), db.ForeignKey("medications.id"), nullable=False, index=True)
    prescription_item_id = db.Column(db.String(36), db.ForeignKey("prescription_items.id"), index=True)
    actor_user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    movement_type = db.Column(db.String(30), nullable=False, index=True)
    quantity_change = db.Column(db.Numeric(12, 2), nullable=False)
    balance_after = db.Column(db.Numeric(12, 2), nullable=False)
    notes = db.Column(db.Text)
    moved_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    inventory_batch = db.relationship("PharmacyInventory", back_populates="movements")
    medication = db.relationship("Medication")
    prescription_item = db.relationship("PrescriptionItem")
    actor = db.relationship("User")


class PatientMedicationHistory(BaseModel):
    __tablename__ = "patient_medication_history"
    __table_args__ = (db.UniqueConstraint("prescription_item_id", name="uq_medication_history_prescription_item"),)
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False, index=True)
    prescription_id = db.Column(db.String(36), db.ForeignKey("prescriptions.id"), nullable=False, index=True)
    prescription_item_id = db.Column(db.String(36), db.ForeignKey("prescription_items.id"), nullable=False, index=True)
    medication_id = db.Column(db.String(36), db.ForeignKey("medications.id"), nullable=False, index=True)
    quantity_dispensed = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    first_dispensed_at = db.Column(db.DateTime(timezone=True), nullable=False)
    last_dispensed_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default="partial", index=True)
    pharmacy_notes = db.Column(db.Text)
    patient = db.relationship("Patient", backref="medication_history")
    prescription = db.relationship("Prescription")
    prescription_item = db.relationship("PrescriptionItem")
    medication = db.relationship("Medication")
