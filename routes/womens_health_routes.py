"""Women's Health dashboard and clinical workflows."""
from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from auth.decorators import role_required
from extensions import db
from models import (AntenatalVisit, DeliveryRecord, FolliculometryRecord,
                    GynecologyJourney, GynecologyVisit, InfertilityCycle, LabOrder,
                    InfertilityJourney, IUICycle, PartnerRecord, Patient,
                    PostpartumVisit, Pregnancy, PregnancyVisit, RadiologyOrder, SemenAnalysis,
                    WomensHealthProfile, WomensUltrasoundAttachment,
                    WomensUltrasoundReport)
from services.womens_health import *
from services.womens_health.common import approval_for, can_manage
from services.womens_health.ultrasound_service import attach_ultrasound_file, ultrasound_attachment_path
from womens_health.forms import *


womens_health_bp = Blueprint("womens_health", __name__, url_prefix="/womens-health")
womens_health_clinical_bp = Blueprint("womens_health_clinical", __name__)


def _lines(value): return [line.strip() for line in (value or "").splitlines() if line.strip()]
def _profile(patient_id):
    patient = db.get_or_404(Patient, patient_id)
    return patient, patient.womens_health_profile
def _can_view(patient):
    if current_user.has_role("Patient"): return patient.user_id == current_user.id
    return can_manage(current_user) or current_user.has_permission("womens_health.view") or (current_user.has_role("Nurse") and current_user.has_permission("womens_health.record_anc_basic"))
def _require_patient_view(patient):
    if not _can_view(patient): abort(403)
def _signed(source):
    approval=approval_for(source); return bool(approval and approval.status=="signed")
def _signed_sources(profile):
    from models import WomensHealthApproval
    return {(item.source_type,item.source_id) for item in db.session.scalars(db.select(WomensHealthApproval).where(WomensHealthApproval.profile_id==profile.id,WomensHealthApproval.status=="signed")).all()}


@womens_health_bp.get("")
@womens_health_bp.get("/")
@role_required("Women’s Health Doctor", "Admin")
def dashboard():
    today=date.today(); week_end=today+timedelta(days=7)
    pregnancies=db.session.scalars(db.select(Pregnancy).where(Pregnancy.status=="ongoing",Pregnancy.deleted_at.is_(None))).all()
    anc_due=db.session.scalars(db.select(PregnancyVisit).where(PregnancyVisit.next_follow_up<=today)).all()
    active_cycles=db.session.scalars(db.select(InfertilityCycle).where(InfertilityCycle.status.in_(["planned","active"]))).all()
    follic_due=[cycle for cycle in active_cycles if cycle.cycle_start_date<=today and calculate_cycle_day(cycle.cycle_start_date,today) in {8,9,10,11,12,13,14}]
    iui_week=db.session.scalars(db.select(IUICycle).where(db.func.date(IUICycle.performed_at)>=today,db.func.date(IUICycle.performed_at)<=week_end)).all()
    postpartum_due=db.session.scalars(db.select(PostpartumVisit).where(PostpartumVisit.follow_up_date<=today)).all()
    patient_ids=db.session.scalars(db.select(Patient.id).join(Patient.womens_health_profile)).all()
    pending_labs=db.session.scalar(db.select(db.func.count(LabOrder.id)).where(LabOrder.patient_id.in_(patient_ids),LabOrder.status.in_(["requested","sample_collected","processing"]))) if patient_ids else 0
    pending_radiology=db.session.scalar(db.select(db.func.count(RadiologyOrder.id)).where(RadiologyOrder.patient_id.in_(patient_ids),RadiologyOrder.status.in_(["requested","scheduled","patient_arrived","imaging_performed","report_drafted"]))) if patient_ids else 0
    return render_template("womens_health/dashboard.html",pregnancies=pregnancies,
        high_risk=[p for p in pregnancies if p.risk_category=="high" or p.high_risk_flags],anc_due=anc_due,
        pending_investigations=(pending_labs or 0)+(pending_radiology or 0),active_cycles=active_cycles,follic_due=follic_due,
        iui_week=iui_week,postpartum_due=postpartum_due)


@womens_health_clinical_bp.route("/patients/<patient_id>/womens-health",methods=["GET","POST"])
@login_required
def profile(patient_id):
    patient,profile=_profile(patient_id); _require_patient_view(patient)
    if current_user.has_role("Patient") and profile and not _signed(profile): abort(403)
    form=ProfileForm(obj=profile)
    if request.method=="GET" and profile:
        for name in ("menstrual_history","contraception_history","infertility_history","surgical_history","risk_flags"):
            getattr(form,name).data="\n".join(getattr(profile,name) or [])
    if form.validate_on_submit():
        if not can_manage(current_user): abort(403)
        values={name:getattr(form,name).data for name in ("ob_gyn_summary","menarche_age","cycle_pattern","blood_group","rhesus_status")}
        values.update({name:_lines(getattr(form,name).data) for name in ("menstrual_history","contraception_history","infertility_history","surgical_history","risk_flags")})
        profile=create_womens_health_profile(patient,actor=current_user,**values) if not profile else update_womens_health_profile(profile,actor=current_user,**values)
        flash("Women's Health profile saved.","success"); return redirect(url_for("womens_health_clinical.profile",patient_id=patient.id))
    timeline=build_womens_health_timeline(profile,signed_only=current_user.has_role("Patient")) if profile else []
    return render_template("womens_health/profile.html",patient=patient,profile=profile,form=form,timeline=timeline,sign_form=SignForm())


@womens_health_clinical_bp.route("/patients/<patient_id>/pregnancies/create",methods=["GET","POST"])
@role_required("Women’s Health Doctor","Admin")
def pregnancy_create(patient_id):
    patient,profile=_profile(patient_id)
    if not profile: flash("Create the Women's Health profile first.","warning"); return redirect(url_for("womens_health_clinical.profile",patient_id=patient.id))
    form=PregnancyForm()
    if form.validate_on_submit():
        try:
            pregnancy=create_pregnancy(profile,actor=current_user,**{n:getattr(form,n).data for n in ("lmp","estimated_due_date","gravida","para","abortions","living_children","previous_cs_count","previous_vaginal_births","risk_category")},high_risk_flags=_lines(form.high_risk_flags.data))
            flash("Pregnancy created.","success"); return redirect(url_for("womens_health_clinical.pregnancy_detail",pregnancy_id=pregnancy.id))
        except ValueError as exc: flash(str(exc),"danger")
    return render_template("pregnancy/create.html",form=form,patient=patient)


@womens_health_clinical_bp.get("/pregnancies/<pregnancy_id>")
@login_required
def pregnancy_detail(pregnancy_id):
    pregnancy=db.get_or_404(Pregnancy,pregnancy_id); _require_patient_view(pregnancy.profile.patient)
    if current_user.has_role("Patient") and not _signed(pregnancy): abort(403)
    visits=pregnancy.antenatal_visits
    if current_user.has_role("Patient"): visits=[item for item in visits if _signed(item)]
    return render_template("pregnancy/detail.html",pregnancy=pregnancy,antenatal_visits=visits,sign_form=SignForm())


@womens_health_clinical_bp.route("/pregnancies/<pregnancy_id>/antenatal-visits/create",methods=["GET","POST"])
@login_required
def antenatal_create(pregnancy_id):
    pregnancy=db.get_or_404(Pregnancy,pregnancy_id)
    if not (can_manage(current_user) or current_user.has_permission("womens_health.record_anc_basic")): abort(403)
    form=AntenatalVisitForm()
    if form.validate_on_submit():
        try:
            anc=create_antenatal_visit(pregnancy,actor=current_user,**{n:getattr(form,n).data for n in ("visit_at","weight_kg","systolic_bp","diastolic_bp","fetal_heart_rate","fundal_height_cm","fetal_movement","presentation","complaint","assessment","plan","follow_up_date")},urine_findings={"summary":form.urine_findings.data} if form.urine_findings.data else None)
            flash("ANC visit saved.","success"); return redirect(url_for("womens_health_clinical.pregnancy_detail",pregnancy_id=pregnancy.id))
        except (ValueError,PermissionError) as exc: flash(str(exc),"danger")
    return render_template("pregnancy/antenatal_visit_form.html",form=form,pregnancy=pregnancy)


@womens_health_clinical_bp.route("/pregnancies/<pregnancy_id>/delivery",methods=["GET","POST"])
@role_required("Women’s Health Doctor","Admin")
def delivery_create(pregnancy_id):
    pregnancy=db.get_or_404(Pregnancy,pregnancy_id); form=DeliveryForm()
    if form.validate_on_submit():
        record=create_delivery_record(pregnancy,actor=current_user,**{n:getattr(form,n).data for n in ("delivered_at","delivery_mode","outcome","indication","place_of_delivery")})
        return redirect(url_for("womens_health_clinical.pregnancy_detail",pregnancy_id=pregnancy.id))
    return render_template("pregnancy/delivery_form.html",form=form,pregnancy=pregnancy)


@womens_health_clinical_bp.route("/pregnancies/<pregnancy_id>/postpartum",methods=["GET","POST"])
@role_required("Women’s Health Doctor","Admin")
def postpartum_create(pregnancy_id):
    pregnancy=db.get_or_404(Pregnancy,pregnancy_id); form=PostpartumForm()
    if form.validate_on_submit():
        create_postpartum_visit(pregnancy,actor=current_user,**{n:getattr(form,n).data for n in ("maternal_assessment","wound_assessment","lactation_status","contraception_plan","follow_up_plan","follow_up_date")})
        return redirect(url_for("womens_health_clinical.pregnancy_detail",pregnancy_id=pregnancy.id))
    return render_template("pregnancy/postpartum_form.html",form=form,pregnancy=pregnancy)


@womens_health_clinical_bp.get("/patients/<patient_id>/gynecology")
@login_required
def gynecology(patient_id):
    patient,profile=_profile(patient_id); _require_patient_view(patient)
    journeys=profile.gynecology_journeys if profile else []
    if current_user.has_role("Patient"): journeys=[item for item in journeys if _signed(item)]
    return render_template("gynecology/journey.html",patient=patient,profile=profile,journeys=journeys,signed_sources=_signed_sources(profile) if profile and current_user.has_role("Patient") else None)


@womens_health_clinical_bp.route("/patients/<patient_id>/gynecology/create",methods=["GET","POST"])
@role_required("Women’s Health Doctor","Admin")
def gynecology_create(patient_id):
    patient,profile=_profile(patient_id); form=GynecologyJourneyForm()
    if not profile: return redirect(url_for("womens_health_clinical.profile",patient_id=patient.id))
    if form.validate_on_submit():
        journey=create_gynecology_journey(profile,actor=current_user,primary_condition=form.primary_condition.data,summary=form.summary.data)
        return redirect(url_for("womens_health_clinical.gynecology",patient_id=patient.id))
    return render_template("gynecology/visit_form.html",form=form,title="Create gynecology journey")


@womens_health_clinical_bp.route("/gynecology/<journey_id>/visits/create",methods=["GET","POST"])
@role_required("Women’s Health Doctor","Admin")
def gynecology_visit_create(journey_id):
    journey=db.get_or_404(GynecologyJourney,journey_id); form=GynecologyVisitForm()
    if form.validate_on_submit():
        create_gynecology_visit(journey,actor=current_user,symptoms=_lines(form.symptoms.data),procedures=_lines(form.procedures.data),**{n:getattr(form,n).data for n in ("examination","diagnosis","assessment","plan","follow_up_date")})
        return redirect(url_for("womens_health_clinical.gynecology",patient_id=journey.profile.patient_id))
    return render_template("gynecology/visit_form.html",form=form,title="Add gynecology visit")


@womens_health_clinical_bp.get("/patients/<patient_id>/infertility")
@login_required
def infertility(patient_id):
    patient,profile=_profile(patient_id); _require_patient_view(patient)
    journeys=profile.infertility_journeys if profile else []
    if current_user.has_role("Patient"): journeys=[item for item in journeys if _signed(item)]
    return render_template("infertility/journey.html",patient=patient,profile=profile,journeys=journeys,signed_sources=_signed_sources(profile) if profile and current_user.has_role("Patient") else None)


@womens_health_clinical_bp.route("/patients/<patient_id>/infertility/create",methods=["GET","POST"])
@role_required("Women’s Health Doctor","Admin")
def infertility_create(patient_id):
    patient,profile=_profile(patient_id); form=InfertilityJourneyForm()
    if not profile: return redirect(url_for("womens_health_clinical.profile",patient_id=patient.id))
    if form.validate_on_submit():
        create_infertility_journey(profile,actor=current_user,infertility_type=form.infertility_type.data,duration_months=form.duration_months.data,female_factor=_lines(form.female_factor.data),male_factor=_lines(form.male_factor.data),investigations=_lines(form.investigations.data),treatment_plan=form.treatment_plan.data)
        return redirect(url_for("womens_health_clinical.infertility",patient_id=patient.id))
    return render_template("infertility/cycle_form.html",form=form,title="Create infertility journey")


@womens_health_clinical_bp.route("/infertility/<journey_id>/cycles/create",methods=["GET","POST"])
@role_required("Women’s Health Doctor","Admin")
def cycle_create(journey_id):
    journey=db.get_or_404(InfertilityJourney,journey_id); form=InfertilityCycleForm()
    if form.validate_on_submit():
        cycle=create_infertility_cycle(journey,actor=current_user,cycle_type=form.cycle_type.data,cycle_start_date=form.cycle_start_date.data,protocol={"summary":form.protocol.data} if form.protocol.data else None,timed_intercourse_advice=form.timed_intercourse_advice.data)
        return redirect(url_for("womens_health_clinical.infertility",patient_id=journey.profile.patient_id))
    return render_template("infertility/cycle_form.html",form=form,title="Create treatment cycle")


@womens_health_clinical_bp.route("/cycles/<cycle_id>/folliculometry/create",methods=["GET","POST"])
@role_required("Women’s Health Doctor","Admin")
def folliculometry_create(cycle_id):
    cycle=db.get_or_404(InfertilityCycle,cycle_id); form=FolliculometryForm()
    if form.validate_on_submit():
        record=add_folliculometry_record(cycle,actor=current_user,scan_at=form.scan_at.data,endometrium_mm=form.endometrium_mm.data,endometrium_pattern=form.endometrium_pattern.data,notes=form.notes.data)
        if form.diameter_mm.data: add_follicle_measurement(record,actor=current_user,ovary=form.ovary.data,follicle_number=form.follicle_number.data or 1,diameter_mm=form.diameter_mm.data)
        return redirect(url_for("womens_health_clinical.infertility",patient_id=cycle.journey.profile.patient_id))
    return render_template("infertility/folliculometry_form.html",form=form,cycle=cycle)


@womens_health_clinical_bp.route("/cycles/<cycle_id>/iui/create",methods=["GET","POST"])
@role_required("Women’s Health Doctor","Admin")
def iui_create(cycle_id):
    cycle=db.get_or_404(InfertilityCycle,cycle_id); form=IUIForm()
    form.partner_id.choices=[("","Not linked")]+[(p.id,p.first_name+" "+p.last_name) for p in cycle.journey.partner_records]
    if form.validate_on_submit():
        create_iui_cycle(cycle,actor=current_user,partner_id=form.partner_id.data or None,performed_at=form.performed_at.data,trigger_at=form.trigger_at.data,stimulation_protocol={"summary":form.stimulation_protocol.data} if form.stimulation_protocol.data else None,semen_preparation_summary=form.semen_preparation_summary.data,post_wash_count=form.post_wash_count.data,luteal_support={"summary":form.luteal_support.data} if form.luteal_support.data else None,pregnancy_test_date=form.pregnancy_test_date.data,outcome=form.outcome.data)
        return redirect(url_for("womens_health_clinical.infertility",patient_id=cycle.journey.profile.patient_id))
    return render_template("infertility/iui_form.html",form=form,cycle=cycle)


@womens_health_clinical_bp.route("/infertility/<journey_id>/partners/create",methods=["GET","POST"])
@role_required("Women’s Health Doctor","Admin")
def partner_create(journey_id):
    journey=db.get_or_404(InfertilityJourney,journey_id); form=PartnerForm()
    if form.validate_on_submit(): create_partner_record(journey,actor=current_user,first_name=form.first_name.data,last_name=form.last_name.data,date_of_birth=form.date_of_birth.data,fertility_history=form.fertility_history.data); return redirect(url_for("womens_health_clinical.infertility",patient_id=journey.profile.patient_id))
    return render_template("infertility/cycle_form.html",form=form,title="Add partner")


@womens_health_clinical_bp.route("/partners/<partner_id>/semen-analysis/create",methods=["GET","POST"])
@role_required("Women’s Health Doctor","Admin")
def semen_create(partner_id):
    partner=db.get_or_404(PartnerRecord,partner_id); form=SemenAnalysisForm()
    if form.validate_on_submit(): add_semen_analysis(partner,actor=current_user,**{n:getattr(form,n).data for n in ("volume_ml","concentration_million_ml","total_motility_percent","progressive_motility_percent","normal_morphology_percent","interpretation")}); return redirect(url_for("womens_health_clinical.infertility",patient_id=partner.journey.profile.patient_id))
    return render_template("infertility/cycle_form.html",form=form,title="Semen analysis")


@womens_health_clinical_bp.route("/womens-ultrasound/create",methods=["GET","POST"])
@role_required("Women’s Health Doctor","Admin")
def ultrasound_create():
    form=UltrasoundForm(); profiles=db.session.scalars(db.select(WomensHealthProfile).order_by(WomensHealthProfile.created_at.desc())).all()
    form.profile_id.choices=[(p.id,f"{p.patient.medical_record_number} · {p.patient.first_name} {p.patient.last_name}") for p in profiles]
    form.pregnancy_id.choices=[("","None")]+[(x.id,f"Pregnancy {x.pregnancy_number}") for p in profiles for x in p.pregnancies]
    form.pregnancy_visit_id.choices=[("","None")]+[(x.id,f"{x.visit_at:%Y-%m-%d} · pregnancy visit") for p in profiles for pregnancy in p.pregnancies for x in pregnancy.visits]
    form.antenatal_visit_id.choices=[("","None")]+[(x.id,f"{x.visit_at:%Y-%m-%d} · ANC") for p in profiles for pregnancy in p.pregnancies for x in pregnancy.antenatal_visits]
    form.gynecology_journey_id.choices=[("","None")]+[(x.id,x.primary_condition) for p in profiles for x in p.gynecology_journeys]
    form.gynecology_visit_id.choices=[("","None")]+[(x.id,f"{x.visit_at:%Y-%m-%d} · Gyn visit") for p in profiles for journey in p.gynecology_journeys for x in journey.visits]
    form.infertility_journey_id.choices=[("","None")]+[(x.id,x.journey_number) for p in profiles for x in p.infertility_journeys]
    if form.validate_on_submit():
        profile=db.get_or_404(WomensHealthProfile,form.profile_id.data)
        selected_pregnancy=db.session.get(Pregnancy,form.pregnancy_id.data) if form.pregnancy_id.data else None
        selected_gyn=db.session.get(GynecologyJourney,form.gynecology_journey_id.data) if form.gynecology_journey_id.data else None
        selected_infertility=db.session.get(InfertilityJourney,form.infertility_journey_id.data) if form.infertility_journey_id.data else None
        selected_pregnancy_visit=db.session.get(PregnancyVisit,form.pregnancy_visit_id.data) if form.pregnancy_visit_id.data else None
        selected_anc=db.session.get(AntenatalVisit,form.antenatal_visit_id.data) if form.antenatal_visit_id.data else None
        selected_gyn_visit=db.session.get(GynecologyVisit,form.gynecology_visit_id.data) if form.gynecology_visit_id.data else None
        linked_profiles=[selected_pregnancy.profile_id if selected_pregnancy else None,selected_gyn.profile_id if selected_gyn else None,selected_infertility.profile_id if selected_infertility else None,selected_pregnancy_visit.pregnancy.profile_id if selected_pregnancy_visit else None,selected_anc.pregnancy.profile_id if selected_anc else None,selected_gyn_visit.journey.profile_id if selected_gyn_visit else None]
        if any(value and value!=profile.id for value in linked_profiles): abort(400)
        biometry_values={n:getattr(form,n).data for n in ("biparietal_diameter_mm","head_circumference_mm","abdominal_circumference_mm","femur_length_mm","estimated_fetal_weight_g")}
        doppler_values={"vessel":form.doppler_vessel.data,"pulsatility_index":form.pulsatility_index.data,"resistance_index":form.resistance_index.data,"systolic_diastolic_ratio":form.systolic_diastolic_ratio.data,"peak_systolic_velocity":form.peak_systolic_velocity.data,"cerebroplacental_ratio":form.cerebroplacental_ratio.data,"interpretation":form.doppler_interpretation.data}
        report=create_womens_ultrasound(profile,actor=current_user,scan_type=form.scan_type.data,performed_at=form.performed_at.data,pregnancy=selected_pregnancy,pregnancy_visit_id=form.pregnancy_visit_id.data or None,antenatal_visit_id=form.antenatal_visit_id.data or None,gynecology_journey=selected_gyn,gynecology_visit_id=form.gynecology_visit_id.data or None,infertility_journey=selected_infertility,findings=form.findings.data,impression=form.impression.data,placenta=form.placenta.data,liquor=form.liquor.data,cervical_length_mm=form.cervical_length_mm.data,biometry=[biometry_values] if any(v is not None for v in biometry_values.values()) else None,dopplers=[doppler_values] if form.doppler_vessel.data else None)
        if form.file.data: attach_ultrasound_file(report,form.file.data,actor=current_user)
        return redirect(url_for("womens_health_clinical.profile",patient_id=profile.patient_id))
    return render_template("ultrasound/womens_ultrasound_form.html",form=form)


SOURCE_MODELS={c.__name__:c for c in (WomensHealthProfile,Pregnancy,AntenatalVisit,DeliveryRecord,PostpartumVisit,GynecologyJourney,GynecologyVisit,InfertilityJourney,InfertilityCycle,FolliculometryRecord,IUICycle,PartnerRecord,SemenAnalysis,WomensUltrasoundReport)}
@womens_health_clinical_bp.post("/womens-health/records/<source_type>/<source_id>/sign")
@role_required("Women’s Health Doctor","Admin")
def sign(source_type,source_id):
    model=SOURCE_MODELS.get(source_type)
    if not model: abort(404)
    source=db.get_or_404(model,source_id)
    profile = source if isinstance(source,WomensHealthProfile) else getattr(source,"profile",None)
    if not profile:
        if getattr(source,"pregnancy",None): profile=source.pregnancy.profile
        elif getattr(source,"journey",None): profile=source.journey.profile
        elif getattr(source,"cycle",None): profile=source.cycle.journey.profile
        elif getattr(source,"partner",None): profile=source.partner.journey.profile
        elif getattr(source,"profile_id",None): profile=db.session.get(WomensHealthProfile,source.profile_id)
    if not profile: abort(400)
    sign_record(source,profile,actor=current_user); flash("Record signed and released.","success")
    return redirect(request.referrer or url_for("womens_health.dashboard"))


@womens_health_clinical_bp.get("/womens-ultrasound/<report_id>/attachments/<attachment_id>")
@login_required
def ultrasound_attachment(report_id,attachment_id):
    report=db.get_or_404(WomensUltrasoundReport,report_id); attachment=db.get_or_404(WomensUltrasoundAttachment,attachment_id)
    profile=db.get_or_404(WomensHealthProfile,report.profile_id); _require_patient_view(profile.patient)
    if attachment.ultrasound_report_id!=report.id: abort(404)
    if current_user.has_role("Patient") and (not approval_for(report) or approval_for(report).status!="signed"): abort(403)
    try: path=ultrasound_attachment_path(attachment)
    except FileNotFoundError: abort(404)
    return send_file(path,as_attachment=True,download_name=attachment.original_name,mimetype=attachment.mime_type)
