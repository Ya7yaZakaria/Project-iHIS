"""Shared authorization, approval, audit, and timeline helpers."""

from datetime import datetime, timezone

from extensions import db
from models import WomensHealthApproval, WomensHealthTimelineEvent
from services.auth_service import log_auth_event


def now():
    return datetime.now(timezone.utc)


def can_manage(actor):
    return actor.has_role("Super Admin", "Admin", "Women’s Health Doctor") or (
        actor.has_permission("womens_health.create") and actor.has_permission("womens_health.update")
    )


def require_manage(actor):
    if not can_manage(actor):
        raise PermissionError("Women's Health management access is required.")


def require_view(actor):
    if not (can_manage(actor) or actor.has_permission("womens_health.view")):
        raise PermissionError("Women's Health viewing access is required.")


def audit(action, actor, resource, **details):
    log_auth_event(action, actor=actor, details={
        "resource_type": resource.__class__.__name__, "resource_id": resource.id, **details,
    })


def approval_for(source):
    return db.session.scalar(db.select(WomensHealthApproval).where(
        WomensHealthApproval.source_type == source.__class__.__name__,
        WomensHealthApproval.source_id == source.id,
    ))


def create_draft(profile, source):
    approval = approval_for(source)
    if not approval:
        approval = WomensHealthApproval(profile_id=profile.id, source_type=source.__class__.__name__,
                                         source_id=source.id, status="draft")
        db.session.add(approval)
    return approval


def sign_record(source, profile, *, actor):
    require_manage(actor)
    approval = create_draft(profile, source)
    approval.status = "signed"
    approval.signed_by_id = actor.id
    approval.signed_at = now()
    audit("womens_health.record_signed", actor, source)
    db.session.commit()
    return approval


def timeline_event(profile, event_type, title, source, *, event_at=None, summary=None,
                   pregnancy=None, gynecology_journey=None, infertility_journey=None, data=None):
    event = db.session.scalar(db.select(WomensHealthTimelineEvent).where(
        WomensHealthTimelineEvent.source_type == source.__class__.__name__,
        WomensHealthTimelineEvent.source_id == source.id,
    ))
    if not event:
        event = WomensHealthTimelineEvent(profile_id=profile.id, source_type=source.__class__.__name__, source_id=source.id)
        db.session.add(event)
    event.event_type, event.title = event_type, title
    event.event_at, event.summary, event.data = event_at or now(), summary, data
    event.pregnancy_id = pregnancy.id if pregnancy else None
    event.gynecology_journey_id = gynecology_journey.id if gynecology_journey else None
    event.infertility_journey_id = infertility_journey.id if infertility_journey else None
    return event


def build_womens_health_timeline(profile, *, signed_only=False):
    statement = db.select(WomensHealthTimelineEvent).where(
        WomensHealthTimelineEvent.profile_id == profile.id,
        WomensHealthTimelineEvent.deleted_at.is_(None),
    )
    events = db.session.scalars(statement.order_by(WomensHealthTimelineEvent.event_at.desc())).all()
    if not signed_only:
        return events
    signed = {(item.source_type, item.source_id) for item in db.session.scalars(db.select(WomensHealthApproval).where(
        WomensHealthApproval.profile_id == profile.id, WomensHealthApproval.status == "signed"
    )).all()}
    return [event for event in events if (event.source_type, event.source_id) in signed]
