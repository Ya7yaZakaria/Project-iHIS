"""Patient demographics, EMR dashboard, and attachment routes."""

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from auth.decorators import role_required
from emr.forms import AttachmentForm, PatientForm, lines, unlines
from extensions import db
from models import MedicalAttachment, MedicalRecord, Patient
from services.auth_service import log_auth_event
from services.emr_service import (attachment_path, build_patient_timeline,
                                  can_view_demographics, can_view_emr,
                                  create_patient, require_emr_access,
                                  search_patients, update_patient,
                                  upload_attachment)

patient_bp = Blueprint("patients", __name__, url_prefix="/patients")


def _patient(patient_id): return db.get_or_404(Patient, patient_id)
def _history_data(form):
    return {name: lines(getattr(form,name).data) for name in ("allergies","chronic_conditions","surgical_history","family_history","vaccination_history")}


@patient_bp.get("")
@patient_bp.get("/")
@login_required
def index():
    if current_user.has_role("Patient"):
        patient=db.session.execute(db.select(Patient).filter_by(user_id=current_user.id)).scalar_one_or_none()
        return redirect(url_for("patients.detail",patient_id=patient.id)) if patient else abort(404)
    if not current_user.has_role("Super Admin","Admin","Receptionist"): abort(403)
    search=request.args.get("search",""); pagination=search_patients(search,page=request.args.get("page",1,type=int))
    return render_template("patients/index.html",patients=pagination.items,pagination=pagination,search=search)


@patient_bp.route("/create",methods=["GET","POST"])
@role_required("Super Admin","Admin","Receptionist")
def create():
    form=PatientForm()
    if form.validate_on_submit():
        try:
            patient=create_patient(actor=current_user,first_name=form.first_name.data,last_name=form.last_name.data,date_of_birth=form.date_of_birth.data,sex_at_birth=form.sex_at_birth.data,medical_record_number=form.medical_record_number.data,blood_type=form.blood_type.data or None,phone=form.phone.data or None,email=form.email.data or None,address=form.address.data or None,**_history_data(form))
            flash("Patient registered.","success"); return redirect(url_for("patients.detail",patient_id=patient.id))
        except (ValueError,PermissionError) as exc: flash(str(exc),"danger")
    return render_template("patients/create.html",form=form)


@patient_bp.get("/<patient_id>")
@login_required
def detail(patient_id):
    patient=_patient(patient_id)
    if not can_view_demographics(current_user,patient): abort(403)
    return render_template("patients/detail.html",patient=patient,can_open_emr=can_view_emr(current_user,patient,audit_denied=False))


@patient_bp.route("/<patient_id>/edit",methods=["GET","POST"])
@role_required("Super Admin","Admin","Receptionist")
def edit(patient_id):
    patient=_patient(patient_id); form=PatientForm(obj=patient)
    if request.method=="GET":
        for name in ("allergies","chronic_conditions","surgical_history","family_history","vaccination_history"): getattr(form,name).data=unlines(getattr(patient,name))
    if form.validate_on_submit():
        try:
            update_patient(patient,actor=current_user,medical_record_number=form.medical_record_number.data,first_name=form.first_name.data,last_name=form.last_name.data,date_of_birth=form.date_of_birth.data,sex_at_birth=form.sex_at_birth.data,blood_type=form.blood_type.data or None,phone=form.phone.data or None,email=form.email.data or None,address=form.address.data or None,**_history_data(form))
            flash("Patient updated.","success"); return redirect(url_for("patients.detail",patient_id=patient.id))
        except (ValueError,PermissionError) as exc: flash(str(exc),"danger")
    return render_template("patients/create.html",form=form,patient=patient)


@patient_bp.get("/<patient_id>/emr")
@login_required
def emr_dashboard(patient_id):
    patient=_patient(patient_id)
    try: require_emr_access(current_user,patient)
    except PermissionError: abort(403)
    log_auth_event("emr.viewed",actor=current_user,details={"patient_id":patient.id}); db.session.commit()
    timeline=build_patient_timeline(patient)
    return render_template("emr/dashboard.html",patient=patient,timeline=timeline)


@patient_bp.get("/<patient_id>/emr/timeline")
@login_required
def timeline(patient_id):
    patient=_patient(patient_id)
    try: require_emr_access(current_user,patient)
    except PermissionError: abort(403)
    log_auth_event("emr.timeline_viewed",actor=current_user,details={"patient_id":patient.id}); db.session.commit()
    return render_template("emr/dashboard.html",patient=patient,timeline=build_patient_timeline(patient))


@patient_bp.route("/<patient_id>/attachments",methods=["GET","POST"])
@login_required
def attachments(patient_id):
    patient=_patient(patient_id); form=AttachmentForm()
    try: require_emr_access(current_user,patient,write=request.method=="POST")
    except PermissionError: abort(403)
    if request.method=="GET": log_auth_event("emr.attachments_viewed",actor=current_user,details={"patient_id":patient.id}); db.session.commit()
    visits=db.session.execute(db.select(MedicalRecord).filter_by(patient_id=patient.id).order_by(MedicalRecord.encounter_at.desc())).scalars().all()
    form.medical_record_id.choices=[("","Patient-level document")]+[(v.id,f"{v.encounter_at:%Y-%m-%d} — {v.encounter_type}") for v in visits]
    if form.validate_on_submit():
        visit=db.session.get(MedicalRecord,form.medical_record_id.data) if form.medical_record_id.data else None
        if visit and visit.patient_id!=patient.id: abort(400)
        try:
            upload_attachment(patient,form.file.data,actor=current_user,medical_record=visit,category=form.category.data,description=form.description.data)
            flash("Document uploaded securely.","success"); return redirect(url_for("patients.attachments",patient_id=patient.id))
        except (ValueError,PermissionError) as exc: flash(str(exc),"danger")
    return render_template("attachments/upload.html",patient=patient,form=form)


@patient_bp.get("/attachments/<attachment_id>/download")
@login_required
def download_attachment(attachment_id):
    attachment=db.get_or_404(MedicalAttachment,attachment_id)
    try: require_emr_access(current_user,attachment.patient)
    except PermissionError: abort(403)
    try: path=attachment_path(attachment)
    except FileNotFoundError: abort(404)
    log_auth_event("emr.attachment_downloaded",actor=current_user,details={"patient_id":attachment.patient_id,"attachment_id":attachment.id}); db.session.commit()
    return send_file(path,as_attachment=True,download_name=attachment.original_name,mimetype=attachment.mime_type)
