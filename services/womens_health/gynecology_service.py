from uuid import uuid4
from extensions import db
from models import GynecologyJourney, GynecologyVisit
from .common import audit, create_draft, now, require_manage, timeline_event


def create_gynecology_journey(profile, *, actor, primary_condition, summary=None):
    require_manage(actor)
    journey = GynecologyJourney(journey_number=f"GYN-{uuid4().hex[:10].upper()}", profile=profile,
        primary_condition=primary_condition.strip(), summary=summary, started_at=now(), status="active")
    db.session.add(journey); db.session.flush(); create_draft(profile, journey)
    profile.active_journey_type, profile.active_journey_id = "gynecology", journey.id
    timeline_event(profile, "gynecology_journey", "Gynecology journey created", journey,
                   gynecology_journey=journey, summary=primary_condition)
    audit("womens_health.gynecology_journey_created", actor, journey)
    db.session.commit(); return journey


def create_gynecology_visit(journey, *, actor, visit_at=None, **fields):
    require_manage(actor); visit_at = visit_at or now()
    visit = GynecologyVisit(journey=journey, doctor_id=actor.doctor_profile.id if actor.doctor_profile else None,
                            visit_at=visit_at, **fields)
    db.session.add(visit); db.session.flush(); create_draft(journey.profile, visit)
    timeline_event(journey.profile, "gynecology_visit", "Gynecology visit", visit,
                   event_at=visit_at, gynecology_journey=journey, summary=visit.diagnosis or visit.assessment)
    audit("womens_health.gynecology_visit_created", actor, visit, journey_id=journey.id)
    db.session.commit(); return visit
