from extensions import db
from models import AntenatalVisit, DeliveryRecord, PostpartumVisit, Pregnancy, PregnancyVisit
from .common import audit, create_draft, now, require_manage, timeline_event
from .womens_health_calculators import calculate_edd, calculate_ga


def create_pregnancy(profile, *, actor, lmp=None, estimated_due_date=None, **fields):
    require_manage(actor)
    if not lmp and not estimated_due_date: raise ValueError("LMP or EDD is required.")
    number = (db.session.scalar(db.select(db.func.max(Pregnancy.pregnancy_number)).where(Pregnancy.profile_id == profile.id)) or 0) + 1
    pregnancy = Pregnancy(profile=profile, pregnancy_number=number, lmp=lmp,
        estimated_due_date=estimated_due_date or calculate_edd(lmp), **fields)
    db.session.add(pregnancy); db.session.flush(); create_draft(profile, pregnancy)
    profile.active_journey_type, profile.active_journey_id = "pregnancy", pregnancy.id
    timeline_event(profile, "pregnancy_created", f"Pregnancy {number} created", pregnancy,
                   pregnancy=pregnancy, summary=f"EDD {pregnancy.estimated_due_date}")
    audit("womens_health.pregnancy_created", actor, pregnancy, profile_id=profile.id)
    db.session.commit(); return pregnancy


def create_antenatal_visit(pregnancy, *, actor, visit_at=None, complaint=None, assessment=None,
                           plan=None, follow_up_date=None, weight_kg=None, systolic_bp=None,
                           diastolic_bp=None, urine_findings=None, fetal_heart_rate=None,
                           fundal_height_cm=None, fetal_movement=None, presentation=None,
                           medical_record_id=None):
    nurse_only = actor.has_role("Nurse") and actor.has_permission("womens_health.record_anc_basic")
    if not nurse_only: require_manage(actor)
    if nurse_only and any((complaint, assessment, plan)):
        raise PermissionError("Nurses may record ANC measurements only.")
    visit_at = visit_at or now(); ga = calculate_ga(lmp=pregnancy.lmp, edd=pregnancy.estimated_due_date, on_date=visit_at.date())
    clinical = PregnancyVisit(pregnancy=pregnancy, medical_record_id=medical_record_id,
        doctor_id=actor.doctor_profile.id if actor.doctor_profile else None, visit_at=visit_at,
        gestational_age_weeks=ga["weeks"], gestational_age_days=ga["days"], complaint=complaint,
        assessment=assessment, plan=plan, next_follow_up=follow_up_date)
    db.session.add(clinical); db.session.flush()
    anc = AntenatalVisit(pregnancy=pregnancy, pregnancy_visit=clinical, visit_at=visit_at,
        weight_kg=weight_kg, systolic_bp=systolic_bp, diastolic_bp=diastolic_bp,
        urine_findings=urine_findings, fetal_heart_rate=fetal_heart_rate,
        fundal_height_cm=fundal_height_cm, fetal_movement=fetal_movement,
        presentation=presentation, recorded_by_id=actor.id)
    db.session.add(anc); db.session.flush(); create_draft(pregnancy.profile, anc)
    timeline_event(pregnancy.profile, "anc_visit", "Antenatal visit", anc, event_at=visit_at,
                   pregnancy=pregnancy, summary=f"GA {ga['weeks']}w {ga['days']}d")
    audit("womens_health.anc_created", actor, anc, pregnancy_id=pregnancy.id)
    db.session.commit(); return anc


def create_delivery_record(pregnancy, *, actor, delivered_at, delivery_mode, outcome, **fields):
    require_manage(actor)
    if pregnancy.delivery_record: raise ValueError("Delivery record already exists.")
    record = DeliveryRecord(pregnancy=pregnancy, delivered_at=delivered_at,
                            delivery_mode=delivery_mode, outcome=outcome, **fields)
    pregnancy.status, pregnancy.outcome = "delivered", outcome
    db.session.add(record); db.session.flush(); create_draft(pregnancy.profile, record)
    timeline_event(pregnancy.profile, "delivery", "Delivery", record, event_at=delivered_at,
                   pregnancy=pregnancy, summary=f"{delivery_mode}: {outcome}")
    audit("womens_health.delivery_created", actor, record, pregnancy_id=pregnancy.id)
    db.session.commit(); return record


def create_postpartum_visit(pregnancy, *, actor, visit_at=None, **fields):
    require_manage(actor); visit_at = visit_at or now()
    record = PostpartumVisit(pregnancy=pregnancy, visit_at=visit_at, **fields)
    db.session.add(record); db.session.flush(); create_draft(pregnancy.profile, record)
    timeline_event(pregnancy.profile, "postpartum_visit", "Postpartum visit", record,
                   event_at=visit_at, pregnancy=pregnancy)
    audit("womens_health.postpartum_created", actor, record, pregnancy_id=pregnancy.id)
    db.session.commit(); return record
