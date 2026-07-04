"""Transactional pharmacy catalog, prescription, and inventory workflows."""

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

from extensions import db
from models import (DispensingRecord, Medication, PatientMedicationHistory,
                    PharmacyInventory, Prescription, PrescriptionItem,
                    StockMovement)
from services.auth_service import log_auth_event


class PharmacyError(ValueError):
    pass


def _now():
    return datetime.now(timezone.utc)


def _quantity(value, label="Quantity", allow_zero=False):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise PharmacyError(f"{label} must be a number.")
    if result < 0 or (result == 0 and not allow_zero):
        raise PharmacyError(f"{label} must be {'zero or greater' if allow_zero else 'greater than zero'}.")
    return result.quantize(Decimal("0.01"))


def _audit(action, actor, resource, **details):
    log_auth_event(
        action,
        actor=actor,
        details={"resource_type": resource.__class__.__name__, "resource_id": resource.id, **details},
    )


def _require_catalog(actor):
    if not actor.has_role("Super Admin", "Admin"):
        raise PermissionError("Medication catalog administration is required.")


def _require_dispense(actor):
    if not (actor.has_role("Super Admin", "Pharmacist") or actor.has_permission("pharmacy.dispense")):
        raise PermissionError("Pharmacy dispensing access is required.")


def _require_inventory(actor):
    if not (actor.has_role("Super Admin") or actor.has_permission("pharmacy.manage_inventory")):
        raise PermissionError("Pharmacy inventory permission is required.")


def create_medication(*, actor, generic_name, brand_name=None, strength=None, dosage_form=None,
                      route=None, category=None, manufacturer=None, barcode=None, code=None,
                      is_active=True):
    _require_catalog(actor)
    generic_name = generic_name.strip()
    brand_name = (brand_name or "").strip() or None
    strength = (strength or "").strip() or None
    duplicate = db.session.scalar(db.select(Medication).where(
        db.func.lower(Medication.generic_name) == generic_name.lower(),
        db.func.coalesce(db.func.lower(Medication.brand_name), "") == (brand_name or "").lower(),
        db.func.coalesce(db.func.lower(Medication.strength), "") == (strength or "").lower(),
        Medication.deleted_at.is_(None),
    ))
    if duplicate:
        raise PharmacyError("This medication already exists.")
    if barcode and db.session.scalar(db.select(Medication.id).where(Medication.barcode == barcode.strip())):
        raise PharmacyError("Barcode already exists.")
    medication = Medication(
        generic_name=generic_name, brand_name=brand_name, strength=strength,
        form=(dosage_form or "").strip() or None, route=(route or "").strip() or None,
        category=(category or "").strip() or None,
        manufacturer=(manufacturer or "").strip() or None,
        barcode=(barcode or "").strip() or None, code=(code or "").strip() or None,
        is_active=bool(is_active),
    )
    db.session.add(medication)
    db.session.flush()
    _audit("pharmacy.medication_created", actor, medication)
    db.session.commit()
    return medication


def update_medication(medication, *, actor, **fields):
    _require_catalog(actor)
    mapping = {"dosage_form": "form"}
    for key, value in fields.items():
        key = mapping.get(key, key)
        if key in {"generic_name", "brand_name", "strength", "form", "route", "category", "manufacturer", "barcode", "code"}:
            setattr(medication, key, value.strip() if isinstance(value, str) and value.strip() else None)
        elif key == "is_active":
            medication.is_active = bool(value)
    if not medication.generic_name:
        raise PharmacyError("Generic name is required.")
    duplicate = db.session.scalar(db.select(Medication.id).where(
        db.func.lower(Medication.generic_name) == medication.generic_name.lower(),
        db.func.coalesce(db.func.lower(Medication.brand_name), "") == (medication.brand_name or "").lower(),
        db.func.coalesce(db.func.lower(Medication.strength), "") == (medication.strength or "").lower(),
        Medication.id != medication.id, Medication.deleted_at.is_(None),
    ))
    if duplicate:
        raise PharmacyError("This medication already exists.")
    _audit("pharmacy.medication_updated", actor, medication)
    db.session.commit()
    return medication


def deactivate_medication(medication, *, actor):
    _require_catalog(actor)
    medication.is_active = False
    _audit("pharmacy.medication_deactivated", actor, medication)
    db.session.commit()
    return medication


def send_prescription_to_pharmacy(prescription, *, actor):
    if not actor.has_role("Super Admin", "Admin", "Doctor", "Womenâ€™s Health Doctor"):
        raise PermissionError("Only a Doctor may send prescriptions.")
    if actor.has_role("Doctor", "Womenâ€™s Health Doctor") and (
        not actor.doctor_profile or prescription.doctor_id != actor.doctor_profile.id
    ):
        raise PermissionError("Only the prescribing Doctor may send this prescription.")
    if prescription.status != "created" or prescription.completed_at:
        raise PharmacyError("Only created prescriptions can be sent.")
    if not prescription.items:
        raise PharmacyError("A prescription must contain at least one item.")
    prescription.status = "sent_to_pharmacy"
    prescription.sent_at = _now()
    _audit("pharmacy.prescription_sent", actor, prescription)
    db.session.commit()
    return prescription


def review_prescription(prescription, *, actor, notes=None):
    _require_dispense(actor)
    if prescription.status != "sent_to_pharmacy" or prescription.completed_at:
        raise PharmacyError("Only prescriptions sent to pharmacy can be reviewed.")
    prescription.status = "under_review"
    prescription.reviewed_by_id = actor.id
    prescription.reviewed_at = _now()
    if notes:
        prescription.pharmacy_notes = notes.strip()
    _audit("pharmacy.prescription_reviewed", actor, prescription)
    db.session.commit()
    return prescription


def cancel_prescription(prescription, *, actor, reason=None):
    allowed = actor.has_role("Super Admin", "Admin", "Pharmacist")
    if actor.has_role("Doctor", "Womenâ€™s Health Doctor") and actor.doctor_profile:
        allowed = allowed or prescription.doctor_id == actor.doctor_profile.id
    if not allowed:
        raise PermissionError("You cannot cancel this prescription.")
    if prescription.completed_at or prescription.status == "cancelled":
        raise PharmacyError("This prescription is already closed.")
    if any(Decimal(item.dispensed_quantity or 0) > 0 for item in prescription.items):
        raise PharmacyError("A prescription cannot be cancelled after dispensing has started.")
    prescription.status = "cancelled"
    prescription.cancelled_at = _now()
    prescription.cancelled_by_id = actor.id
    prescription.cancellation_reason = (reason or "").strip() or None
    _audit("pharmacy.prescription_cancelled", actor, prescription, reason=prescription.cancellation_reason)
    db.session.commit()
    return prescription


def create_stock_movement(batch, *, actor, movement_type, quantity_change,
                          prescription_item=None, notes=None):
    if movement_type == "dispense":
        _require_dispense(actor)
    else:
        _require_inventory(actor)
    change = _quantity(abs(quantity_change), allow_zero=False)
    if Decimal(str(quantity_change)) < 0:
        change = -change
    movement = StockMovement(
        inventory_batch=batch, medication_id=batch.medication_id,
        prescription_item=prescription_item, actor_user_id=actor.id,
        movement_type=movement_type, quantity_change=change,
        balance_after=batch.quantity_on_hand, notes=(notes or "").strip() or None,
        moved_at=_now(),
    )
    db.session.add(movement)
    return movement


def add_stock(*, actor, medication, batch_number, quantity, expiry_date=None,
              supplier=None, reorder_level=0, unit_cost=None, location=None):
    _require_inventory(actor)
    amount = _quantity(quantity)
    batch_number = batch_number.strip()
    batch = db.session.scalar(db.select(PharmacyInventory).where(
        PharmacyInventory.medication_id == medication.id,
        PharmacyInventory.batch_number == batch_number,
        PharmacyInventory.deleted_at.is_(None),
    ))
    if batch:
        if expiry_date and batch.expiry_date and expiry_date != batch.expiry_date:
            raise PharmacyError("This batch number already has a different expiry date.")
        batch.quantity_on_hand = Decimal(batch.quantity_on_hand or 0) + amount
        batch.expiry_date = batch.expiry_date or expiry_date
        batch.supplier = (supplier or "").strip() or batch.supplier
        batch.reorder_level = _quantity(reorder_level, "Reorder level", allow_zero=True)
        batch.location = (location or "").strip() or batch.location
        if unit_cost is not None:
            batch.unit_cost = _quantity(unit_cost, "Unit cost", allow_zero=True)
    else:
        batch = PharmacyInventory(
            medication=medication, batch_number=batch_number, quantity_on_hand=amount,
            expiry_date=expiry_date, supplier=(supplier or "").strip() or None,
            reorder_level=_quantity(reorder_level, "Reorder level", allow_zero=True),
            unit_cost=_quantity(unit_cost, "Unit cost", allow_zero=True) if unit_cost is not None else None,
            location=(location or "").strip() or None,
        )
        db.session.add(batch)
        db.session.flush()
    create_stock_movement(batch, actor=actor, movement_type="addition", quantity_change=amount)
    _audit("pharmacy.stock_added", actor, batch, quantity=str(amount))
    db.session.commit()
    return batch


def reduce_stock(batch, quantity, *, actor, prescription_item=None, movement_type="dispense", notes=None):
    if movement_type == "dispense":
        _require_dispense(actor)
    else:
        _require_inventory(actor)
    amount = _quantity(quantity)
    if batch.expiry_date and batch.expiry_date < date.today():
        raise PharmacyError("Expired stock cannot be dispensed.")
    if Decimal(batch.quantity_on_hand or 0) < amount:
        raise PharmacyError("Insufficient stock in the selected batch.")
    batch.quantity_on_hand = Decimal(batch.quantity_on_hand or 0) - amount
    movement = create_stock_movement(
        batch, actor=actor, movement_type=movement_type,
        quantity_change=-amount, prescription_item=prescription_item, notes=notes,
    )
    audit_action = "pharmacy.stock_adjusted" if movement_type == "adjustment" else "pharmacy.stock_reduced"
    _audit(audit_action, actor, batch, quantity=str(amount), movement_type=movement_type)
    return movement


def check_stock_availability(medication, quantity=None):
    total = db.session.scalar(db.select(db.func.coalesce(db.func.sum(PharmacyInventory.quantity_on_hand), 0)).where(
        PharmacyInventory.medication_id == medication.id,
        PharmacyInventory.quantity_on_hand > 0,
        PharmacyInventory.is_active.is_(True),
        PharmacyInventory.deleted_at.is_(None),
        db.or_(PharmacyInventory.expiry_date.is_(None), PharmacyInventory.expiry_date >= date.today()),
    )) or Decimal("0")
    total = Decimal(total)
    return (total >= _quantity(quantity)) if quantity is not None else total


def _usable_batches(medication_id):
    return db.session.scalars(db.select(PharmacyInventory).where(
        PharmacyInventory.medication_id == medication_id,
        PharmacyInventory.quantity_on_hand > 0,
        PharmacyInventory.is_active.is_(True), PharmacyInventory.deleted_at.is_(None),
        db.or_(PharmacyInventory.expiry_date.is_(None), PharmacyInventory.expiry_date >= date.today()),
    ).order_by(PharmacyInventory.expiry_date.is_(None), PharmacyInventory.expiry_date,
               PharmacyInventory.created_at)).all()


def dispense_prescription_item(item, quantity, *, actor, inventory_batch=None,
                               substitute_medication=None, substitution_note=None, notes=None):
    _require_dispense(actor)
    prescription = item.prescription
    if prescription.status not in {"under_review", "partially_dispensed"} or prescription.completed_at:
        raise PharmacyError("Prescription is not open for dispensing.")
    amount = _quantity(quantity)
    remaining = Decimal(item.requested_quantity or 0) - Decimal(item.dispensed_quantity or 0)
    if amount > remaining:
        raise PharmacyError("Dispensed quantity exceeds the remaining prescribed quantity.")
    medication = substitute_medication or item.medication
    if not medication.is_active or medication.is_deleted:
        raise PharmacyError("The medication is inactive.")
    batches = [inventory_batch] if inventory_batch else _usable_batches(medication.id)
    if inventory_batch and inventory_batch.medication_id != medication.id:
        raise PharmacyError("Selected batch does not match the dispensed medication.")
    if sum((Decimal(batch.quantity_on_hand or 0) for batch in batches), Decimal("0")) < amount:
        raise PharmacyError("Insufficient usable stock.")
    left = amount
    now = _now()
    for batch in batches:
        if left <= 0:
            break
        used = min(left, Decimal(batch.quantity_on_hand or 0))
        reduce_stock(batch, used, actor=actor, prescription_item=item, notes=notes)
        db.session.add(DispensingRecord(
            prescription_item=item, inventory_batch=batch, medication=medication,
            pharmacist_id=actor.id, quantity=used, dispensed_at=now,
            notes=(notes or "").strip() or None,
        ))
        left -= used
    item.dispensed_quantity = Decimal(item.dispensed_quantity or 0) + amount
    if substitute_medication:
        item.substitute_medication = substitute_medication
        item.substitution_note = (substitution_note or "").strip() or None
    if notes:
        prescription.pharmacy_notes = notes.strip()
    all_full = all(Decimal(i.dispensed_quantity or 0) >= Decimal(i.requested_quantity or 0) for i in prescription.items)
    prescription.status = "fully_dispensed" if all_full else "partially_dispensed"
    _audit("pharmacy.medication_dispensed", actor, prescription, item_id=item.id, quantity=str(amount))
    update_patient_medication_history(item, actor=actor, commit=False)
    db.session.commit()
    return item


def complete_dispensing(prescription, *, actor, notes=None):
    _require_dispense(actor)
    if prescription.status not in {"partially_dispensed", "fully_dispensed"} or prescription.completed_at:
        raise PharmacyError("Only a dispensed prescription can be completed.")
    prescription.completed_at = _now()
    prescription.completed_by_id = actor.id
    if notes:
        prescription.pharmacy_notes = notes.strip()
    _audit("pharmacy.dispensing_completed", actor, prescription, status=prescription.status)
    db.session.commit()
    return prescription


def update_patient_medication_history(item, *, actor, commit=True):
    total = Decimal(item.dispensed_quantity or 0)
    now = _now()
    history = db.session.scalar(db.select(PatientMedicationHistory).where(
        PatientMedicationHistory.prescription_item_id == item.id
    ))
    medication = item.substitute_medication or item.medication
    if history:
        history.quantity_dispensed = total
        history.last_dispensed_at = now
        history.medication_id = medication.id
        history.status = "full" if total >= Decimal(item.requested_quantity or 0) else "partial"
        history.pharmacy_notes = item.prescription.pharmacy_notes
    else:
        history = PatientMedicationHistory(
            patient_id=item.prescription.patient_id, prescription=item.prescription,
            prescription_item=item, medication=medication, quantity_dispensed=total,
            first_dispensed_at=now, last_dispensed_at=now,
            status="full" if total >= Decimal(item.requested_quantity or 0) else "partial",
            pharmacy_notes=item.prescription.pharmacy_notes,
        )
        db.session.add(history)
    db.session.flush()
    _audit("pharmacy.medication_history_updated", actor, history, item_id=item.id)
    if commit:
        db.session.commit()
    return history


def get_low_stock_items():
    rows = []
    medications = db.session.scalars(db.select(Medication).where(
        Medication.deleted_at.is_(None), Medication.is_active.is_(True)
    ).order_by(Medication.generic_name)).all()
    for medication in medications:
        batches = [b for b in medication.inventory_batches if b.is_active and not b.is_deleted]
        threshold = max((Decimal(b.reorder_level or 0) for b in batches), default=Decimal("0"))
        usable = Decimal(check_stock_availability(medication))
        if batches and usable <= threshold:
            rows.append({"medication": medication, "quantity": usable, "reorder_level": threshold})
    return rows


def get_expired_items():
    return db.session.scalars(db.select(PharmacyInventory).where(
        PharmacyInventory.expiry_date < date.today(),
        PharmacyInventory.quantity_on_hand > 0,
        PharmacyInventory.deleted_at.is_(None),
    ).order_by(PharmacyInventory.expiry_date)).all()
