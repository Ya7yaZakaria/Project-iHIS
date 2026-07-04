from extensions import db
from models import WomensHealthProfile
from .common import audit, create_draft, require_manage, timeline_event


def create_womens_health_profile(patient, *, actor, **fields):
    require_manage(actor)
    if patient.womens_health_profile:
        raise ValueError("Women's Health profile already exists.")
    profile = WomensHealthProfile(patient=patient, **fields)
    db.session.add(profile); db.session.flush()
    create_draft(profile, profile)
    timeline_event(profile, "profile_created", "Women's Health profile created", profile)
    audit("womens_health.profile_created", actor, profile, patient_id=patient.id)
    db.session.commit(); return profile


def update_womens_health_profile(profile, *, actor, **fields):
    require_manage(actor)
    allowed = {"blood_group", "rhesus_status", "menarche_age", "cycle_pattern", "contraception",
               "gynecologic_history", "family_history", "ob_gyn_summary", "menstrual_history",
               "contraception_history", "infertility_history", "surgical_history", "risk_flags",
               "active_journey_type", "active_journey_id"}
    for key, value in fields.items():
        if key in allowed: setattr(profile, key, value)
    approval=create_draft(profile,profile); approval.status="draft"; approval.signed_by_id=None; approval.signed_at=None
    audit("womens_health.profile_updated", actor, profile)
    db.session.commit(); return profile
