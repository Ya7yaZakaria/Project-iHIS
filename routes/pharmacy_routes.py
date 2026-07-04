"""Pharmacy catalog, queue, dispensing, inventory, and medication-history routes."""

from datetime import datetime, timezone

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload, selectinload

from auth.decorators import permission_required, role_required
from extensions import db
from models import (DispensingRecord, Medication, Patient, PatientMedicationHistory,
                    PharmacyInventory, Prescription, PrescriptionItem,
                    StockMovement)
from pharmacy.forms import (AddStockForm, CancelPrescriptionForm,
                            CompleteDispensingForm, DispenseForm,
                            MedicationForm, ReviewPrescriptionForm)
from services.pharmacy_service import (PharmacyError, add_stock,
                                       cancel_prescription,
                                       complete_dispensing, create_medication,
                                       deactivate_medication,
                                       dispense_prescription_item,
                                       get_expired_items, get_low_stock_items,
                                       review_prescription,
                                       update_medication)


pharmacy_bp = Blueprint("pharmacy", __name__, url_prefix="/pharmacy")
patient_medication_bp = Blueprint("patient_medication", __name__, url_prefix="/patients")


def _prescription(value):
    return db.get_or_404(Prescription, value)


def _medication(value):
    return db.get_or_404(Medication, value)


def _inventory_choices(form, item=None, medication_id=None):
    medication_id = medication_id or (item.substitute_medication_id or item.medication_id if item else None)
    batches = db.session.scalars(db.select(PharmacyInventory).where(
        PharmacyInventory.medication_id == medication_id,
        PharmacyInventory.quantity_on_hand > 0,
        PharmacyInventory.deleted_at.is_(None),
    ).order_by(PharmacyInventory.expiry_date)).all() if medication_id else []
    form.inventory_batch_id.choices = [("", "Automatic FEFO")] + [
        (batch.id, f"{batch.batch_number} · {batch.quantity_on_hand} · exp {batch.expiry_date or 'none'}")
        for batch in batches
    ]


@pharmacy_bp.get("")
@pharmacy_bp.get("/")
@role_required("Pharmacist", "Admin")
def dashboard():
    today = datetime.now(timezone.utc).date()
    pending = db.session.scalars(db.select(Prescription).where(
        Prescription.status == "sent_to_pharmacy", Prescription.deleted_at.is_(None)
    ).order_by(Prescription.sent_at)).all()
    under_review = db.session.scalars(db.select(Prescription).where(
        Prescription.status.in_(["under_review", "partially_dispensed"]),
        Prescription.completed_at.is_(None), Prescription.deleted_at.is_(None)
    )).all()
    dispensed = db.session.scalars(db.select(DispensingRecord).where(
        db.func.date(DispensingRecord.dispensed_at) == today
    )).all()
    movements = db.session.scalars(db.select(StockMovement).order_by(StockMovement.moved_at.desc()).limit(10)).all()
    return render_template("pharmacy/dashboard.html", pending=pending, under_review=under_review,
                           dispensed_today=len(dispensed), low_stock=get_low_stock_items(),
                           expired=get_expired_items(), movements=movements)


@pharmacy_bp.get("/medications")
@role_required("Pharmacist", "Admin")
def medications():
    search = request.args.get("search", "").strip()
    statement = db.select(Medication).where(Medication.deleted_at.is_(None))
    if search:
        term = f"%{search}%"
        statement = statement.where(db.or_(Medication.generic_name.ilike(term), Medication.brand_name.ilike(term), Medication.code.ilike(term)))
    items = db.session.scalars(statement.order_by(Medication.generic_name, Medication.brand_name)).all()
    return render_template("pharmacy/medications.html", medications=items, search=search)


@pharmacy_bp.route("/medications/create", methods=["GET", "POST"])
@role_required("Admin")
def medication_create():
    form = MedicationForm()
    if form.validate_on_submit():
        try:
            create_medication(actor=current_user, **{name: getattr(form, name).data for name in
                ("generic_name", "brand_name", "strength", "dosage_form", "route", "category", "manufacturer", "barcode", "code", "is_active")})
            flash("Medication created.", "success")
            return redirect(url_for("pharmacy.medications"))
        except PharmacyError as exc:
            flash(str(exc), "danger")
    return render_template("pharmacy/medication_form.html", form=form, medication=None)


@pharmacy_bp.route("/medications/<medication_id>/edit", methods=["GET", "POST"])
@role_required("Admin")
def medication_edit(medication_id):
    medication = _medication(medication_id)
    form = MedicationForm(obj=medication)
    if request.method == "GET":
        form.dosage_form.data = medication.form
    if form.validate_on_submit():
        try:
            update_medication(medication, actor=current_user, **{name: getattr(form, name).data for name in
                ("generic_name", "brand_name", "strength", "dosage_form", "route", "category", "manufacturer", "barcode", "code", "is_active")})
            flash("Medication updated.", "success")
            return redirect(url_for("pharmacy.medications"))
        except PharmacyError as exc:
            flash(str(exc), "danger")
    return render_template("pharmacy/medication_form.html", form=form, medication=medication)


@pharmacy_bp.post("/medications/<medication_id>/deactivate")
@role_required("Admin")
def medication_deactivate(medication_id):
    deactivate_medication(_medication(medication_id), actor=current_user)
    flash("Medication deactivated.", "success")
    return redirect(url_for("pharmacy.medications"))


@pharmacy_bp.get("/prescriptions")
@role_required("Pharmacist", "Admin")
def prescriptions():
    status = request.args.get("status", "")
    statement = db.select(Prescription).options(joinedload(Prescription.patient), selectinload(Prescription.items)).where(
        Prescription.status != "created", Prescription.deleted_at.is_(None))
    if status:
        statement = statement.where(Prescription.status == status)
    items = db.session.scalars(statement.order_by(Prescription.sent_at.desc())).unique().all()
    return render_template("pharmacy/prescriptions.html", prescriptions=items, status=status)


@pharmacy_bp.get("/prescriptions/<prescription_id>")
@role_required("Pharmacist", "Admin", "Doctor", "Womenâ€™s Health Doctor")
def prescription_detail(prescription_id):
    prescription = _prescription(prescription_id)
    if current_user.has_role("Doctor", "Womenâ€™s Health Doctor") and (not current_user.doctor_profile or prescription.doctor_id != current_user.doctor_profile.id):
        abort(403)
    return render_template("pharmacy/prescription_detail.html", prescription=prescription,
                           review_form=ReviewPrescriptionForm(), complete_form=CompleteDispensingForm(),
                           cancel_form=CancelPrescriptionForm())


@pharmacy_bp.route("/prescriptions/<prescription_id>/review", methods=["GET", "POST"])
@role_required("Pharmacist")
def prescription_review(prescription_id):
    prescription = _prescription(prescription_id)
    form = ReviewPrescriptionForm()
    if form.validate_on_submit():
        try:
            review_prescription(prescription, actor=current_user, notes=form.notes.data)
            flash("Prescription is under review.", "success")
            return redirect(url_for("pharmacy.prescription_detail", prescription_id=prescription.id))
        except PharmacyError as exc:
            flash(str(exc), "danger")
    return render_template("pharmacy/prescription_detail.html", prescription=prescription,
                           review_form=form, complete_form=CompleteDispensingForm(), cancel_form=CancelPrescriptionForm())


@pharmacy_bp.route("/prescriptions/<prescription_id>/dispense", methods=["GET", "POST"])
@role_required("Pharmacist")
def prescription_dispense(prescription_id):
    prescription = _prescription(prescription_id)
    form = DispenseForm()
    open_items = [item for item in prescription.items if item.dispensed_quantity < item.requested_quantity]
    form.item_id.choices = [(item.id, f"{item.medication.generic_name} · remaining {item.requested_quantity - item.dispensed_quantity}") for item in open_items]
    medications = db.session.scalars(db.select(Medication).where(Medication.is_active.is_(True), Medication.deleted_at.is_(None)).order_by(Medication.generic_name)).all()
    form.substitute_medication_id.choices = [("", "No substitution")] + [(m.id, f"{m.generic_name} {m.strength or ''}") for m in medications]
    selected = db.session.get(PrescriptionItem, form.item_id.data) if form.item_id.data else (open_items[0] if open_items else None)
    _inventory_choices(form, selected, form.substitute_medication_id.data or None)
    if form.validate_on_submit():
        item = db.get_or_404(PrescriptionItem, form.item_id.data)
        if item.prescription_id != prescription.id:
            abort(400)
        try:
            dispense_prescription_item(item, form.quantity.data, actor=current_user,
                inventory_batch=db.session.get(PharmacyInventory, form.inventory_batch_id.data) if form.inventory_batch_id.data else None,
                substitute_medication=db.session.get(Medication, form.substitute_medication_id.data) if form.substitute_medication_id.data else None,
                substitution_note=form.substitution_note.data, notes=form.notes.data)
            flash("Medication dispensed and inventory updated.", "success")
            return redirect(url_for("pharmacy.prescription_detail", prescription_id=prescription.id))
        except PharmacyError as exc:
            db.session.rollback()
            flash(str(exc), "danger")
    return render_template("pharmacy/dispense.html", prescription=prescription, form=form)


@pharmacy_bp.post("/prescriptions/<prescription_id>/complete")
@role_required("Pharmacist")
def prescription_complete(prescription_id):
    form = CompleteDispensingForm()
    if not form.validate_on_submit():
        abort(400)
    try:
        complete_dispensing(_prescription(prescription_id), actor=current_user, notes=form.notes.data)
        flash("Dispensing completed.", "success")
    except PharmacyError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("pharmacy.prescription_detail", prescription_id=prescription_id))


@pharmacy_bp.post("/prescriptions/<prescription_id>/cancel")
@login_required
def prescription_cancel(prescription_id):
    form = CancelPrescriptionForm()
    if not form.validate_on_submit():
        abort(400)
    try:
        cancel_prescription(_prescription(prescription_id), actor=current_user, reason=form.reason.data)
        flash("Prescription cancelled.", "success")
    except PermissionError:
        abort(403)
    except PharmacyError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("pharmacy.prescription_detail", prescription_id=prescription_id))


@pharmacy_bp.get("/inventory")
@role_required("Pharmacist", "Admin")
def inventory():
    batches = db.session.scalars(db.select(PharmacyInventory).join(PharmacyInventory.medication).options(joinedload(PharmacyInventory.medication)).where(
        PharmacyInventory.deleted_at.is_(None)).order_by(Medication.generic_name, PharmacyInventory.expiry_date)).all()
    return render_template("pharmacy/inventory.html", batches=batches, low_stock=get_low_stock_items(), expired=get_expired_items())


@pharmacy_bp.route("/inventory/add-stock", methods=["GET", "POST"])
@permission_required("pharmacy.manage_inventory")
def inventory_add_stock():
    form = AddStockForm()
    medications = db.session.scalars(db.select(Medication).where(Medication.is_active.is_(True), Medication.deleted_at.is_(None)).order_by(Medication.generic_name)).all()
    form.medication_id.choices = [(m.id, f"{m.generic_name} {m.strength or ''}") for m in medications]
    if form.validate_on_submit():
        try:
            add_stock(actor=current_user, medication=_medication(form.medication_id.data), **{name: getattr(form, name).data for name in
                ("batch_number", "quantity", "expiry_date", "supplier", "reorder_level", "unit_cost", "location")})
            flash("Stock added.", "success")
            return redirect(url_for("pharmacy.inventory"))
        except PharmacyError as exc:
            flash(str(exc), "danger")
    return render_template("pharmacy/add_stock.html", form=form)


@pharmacy_bp.get("/inventory/movements")
@role_required("Pharmacist", "Admin")
def inventory_movements():
    movements = db.session.scalars(db.select(StockMovement).options(joinedload(StockMovement.medication), joinedload(StockMovement.inventory_batch)).order_by(StockMovement.moved_at.desc())).all()
    return render_template("pharmacy/stock_movements.html", movements=movements)


@patient_medication_bp.get("/<patient_id>/medication-history")
@login_required
def medication_history(patient_id):
    patient = db.get_or_404(Patient, patient_id)
    if current_user.has_role("Patient"):
        if patient.user_id != current_user.id:
            abort(403)
    elif not current_user.has_role("Super Admin", "Admin", "Doctor", "Womenâ€™s Health Doctor", "Nurse", "Pharmacist"):
        abort(403)
    history = db.session.scalars(db.select(PatientMedicationHistory).options(joinedload(PatientMedicationHistory.medication)).where(
        PatientMedicationHistory.patient_id == patient.id).order_by(PatientMedicationHistory.last_dispensed_at.desc())).all()
    return render_template("patients/medication_history.html", patient=patient, history=history)
