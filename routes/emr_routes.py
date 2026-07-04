"""Visit, diagnosis, prescription, order, vital, and nursing routes."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from auth.decorators import role_required
from emr.forms import (DiagnosisForm, NursingNoteForm, OrderForm,
                       PrescriptionForm, VisitForm, VitalSignForm)
from extensions import db
from models import LabTest, MedicalRecord, Patient, Prescription
from services.emr_service import (add_diagnosis, add_nursing_note,
                                  add_prescription_item, add_vital_sign,
                                  create_prescription,
                                  create_radiology_order, create_visit,
                                  require_emr_access, update_visit)
from services.laboratory_service import create_lab_order as create_catalog_lab_order
from services.auth_service import log_auth_event
from services.pharmacy_service import PharmacyError, send_prescription_to_pharmacy

emr_bp=Blueprint("emr",__name__)
def _visit(visit_id): return db.get_or_404(MedicalRecord,visit_id)

@emr_bp.route("/patients/<patient_id>/visits/create",methods=["GET","POST"])
@role_required("Doctor","Women’s Health Doctor")
def create_visit_route(patient_id):
    patient=db.get_or_404(Patient,patient_id); form=VisitForm()
    if form.validate_on_submit():
        try:
            visit=create_visit(patient,actor=current_user,**{name:getattr(form,name).data for name in ("encounter_type","encounter_at","note_format","chief_complaint","history_of_present_illness","history","subjective","objective","examination","assessment","plan","follow_up_date")})
            flash("Visit created.","success"); return redirect(url_for("emr.visit_detail",visit_id=visit.id))
        except PermissionError as exc: flash(str(exc),"danger")
    return render_template("visits/create.html",form=form,patient=patient)

@emr_bp.get("/visits/<visit_id>")
@login_required
def visit_detail(visit_id):
    visit=_visit(visit_id)
    try: require_emr_access(current_user,visit.patient)
    except PermissionError: abort(403)
    log_auth_event("emr.visit_viewed",actor=current_user,details={"patient_id":visit.patient_id,"visit_id":visit.id}); db.session.commit()
    return render_template("visits/detail.html",visit=visit,vital_form=VitalSignForm(),nursing_form=NursingNoteForm())

@emr_bp.route("/visits/<visit_id>/edit",methods=["GET","POST"])
@role_required("Doctor","Women’s Health Doctor")
def visit_edit(visit_id):
    visit=_visit(visit_id); form=VisitForm(obj=visit)
    if form.validate_on_submit():
        try:
            update_visit(visit,actor=current_user,**{name:getattr(form,name).data for name in ("encounter_type","encounter_at","note_format","chief_complaint","history_of_present_illness","history","subjective","objective","examination","assessment","plan","follow_up_date")})
            flash("Visit updated.","success"); return redirect(url_for("emr.visit_detail",visit_id=visit.id))
        except PermissionError as exc: flash(str(exc),"danger")
    return render_template("visits/edit.html",form=form,visit=visit)

@emr_bp.route("/visits/<visit_id>/diagnoses",methods=["GET","POST"])
@role_required("Doctor","Women’s Health Doctor")
def diagnoses(visit_id):
    visit=_visit(visit_id); form=DiagnosisForm()
    if form.validate_on_submit():
        try: add_diagnosis(visit,actor=current_user,description=form.description.data,diagnosis_type=form.diagnosis_type.data,icd10_code=form.icd10_code.data,notes=form.notes.data); flash("Diagnosis added.","success"); return redirect(url_for("emr.visit_detail",visit_id=visit.id))
        except PermissionError as exc: flash(str(exc),"danger")
    return render_template("visits/diagnoses.html",form=form,visit=visit)

@emr_bp.route("/visits/<visit_id>/prescriptions",methods=["GET","POST"])
@role_required("Doctor","Women’s Health Doctor")
def prescriptions(visit_id):
    visit=_visit(visit_id); form=PrescriptionForm()
    if form.validate_on_submit():
        try:
            prescription=create_prescription(visit,actor=current_user,notes=form.notes.data)
            add_prescription_item(prescription,actor=current_user,**{name:getattr(form,name).data for name in ("generic_name","brand_name","strength","dose","route","frequency","duration","quantity","instructions")})
            flash("Prescription created.","success"); return redirect(url_for("emr.visit_detail",visit_id=visit.id))
        except PermissionError as exc: db.session.rollback(); flash(str(exc),"danger")
    return render_template("prescriptions/create.html",form=form,visit=visit)

@emr_bp.post("/prescriptions/<prescription_id>/send-to-pharmacy")
@role_required("Doctor", "Womenâ€™s Health Doctor")
def send_prescription(prescription_id):
    prescription=db.get_or_404(Prescription,prescription_id)
    try:
        send_prescription_to_pharmacy(prescription,actor=current_user)
        flash("Prescription sent to pharmacy.","success")
    except PermissionError: abort(403)
    except PharmacyError as exc: flash(str(exc),"danger")
    return redirect(url_for("emr.visit_detail",visit_id=prescription.medical_record_id))

@emr_bp.route("/visits/<visit_id>/orders",methods=["GET","POST"])
@role_required("Doctor","Women’s Health Doctor")
def orders(visit_id):
    visit=_visit(visit_id); form=OrderForm()
    catalog=db.session.scalars(db.select(LabTest).where(LabTest.is_active.is_(True),LabTest.deleted_at.is_(None)).order_by(LabTest.category,LabTest.name)).all()
    form.lab_test_id.choices=[("","Use free-text test")]+[(item.id,f"{item.code} — {item.name}") for item in catalog]
    if form.validate_on_submit():
        try:
            if form.order_type.data=="lab":
                selected=db.session.get(LabTest,form.lab_test_id.data) if form.lab_test_id.data else None
                if not selected and not form.test_name.data: raise ValueError("Select a catalog test or enter a lab test name.")
                create_catalog_lab_order(visit,actor=current_user,lab_test=selected,test_name=form.test_name.data,test_code=form.test_code.data,priority=form.priority.data,specimen_type=form.specimen_type.data,clinical_notes=form.clinical_notes.data)
            else:
                if not form.modality.data or not form.body_part.data: raise ValueError("Modality and body part are required.")
                create_radiology_order(visit,actor=current_user,modality=form.modality.data,body_part=form.body_part.data,priority=form.priority.data,clinical_indication=form.clinical_notes.data)
            flash("Order requested.","success"); return redirect(url_for("emr.visit_detail",visit_id=visit.id))
        except (ValueError,PermissionError) as exc: flash(str(exc),"danger")
    return render_template("orders/create.html",form=form,visit=visit)

@emr_bp.post("/visits/<visit_id>/vitals")
@role_required("Nurse","Doctor","Women’s Health Doctor")
def vitals(visit_id):
    visit=_visit(visit_id); form=VitalSignForm()
    if not form.validate_on_submit(): abort(400)
    try: add_vital_sign(visit,actor=current_user,**{name:getattr(form,name).data for name in ("temperature_c","pulse_bpm","respiratory_rate","systolic_bp","diastolic_bp","oxygen_saturation","weight_kg","height_cm","pain_score")}); flash("Vital signs recorded.","success")
    except PermissionError: abort(403)
    return redirect(url_for("emr.visit_detail",visit_id=visit.id))

@emr_bp.post("/visits/<visit_id>/nursing-notes")
@role_required("Nurse")
def nursing_notes(visit_id):
    visit=_visit(visit_id); form=NursingNoteForm()
    if not form.validate_on_submit(): abort(400)
    try: add_nursing_note(visit,actor=current_user,note=form.note.data,note_type=form.note_type.data); flash("Nursing note added.","success")
    except PermissionError: abort(403)
    return redirect(url_for("emr.visit_detail",visit_id=visit.id))
