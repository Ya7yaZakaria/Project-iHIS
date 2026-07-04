from extensions import db
from models import PartnerRecord, SemenAnalysis
from .common import audit, create_draft, now, require_manage


def create_partner_record(journey, *, actor, first_name, last_name, **fields):
    require_manage(actor)
    record = PartnerRecord(journey=journey, first_name=first_name.strip(), last_name=last_name.strip(), **fields)
    db.session.add(record); db.session.flush(); create_draft(journey.profile, record)
    audit("womens_health.partner_created", actor, record, journey_id=journey.id)
    db.session.commit(); return record


def add_semen_analysis(partner, *, actor, collected_at=None, **fields):
    require_manage(actor)
    analysis = SemenAnalysis(partner=partner, collected_at=collected_at or now(), **fields)
    db.session.add(analysis); db.session.flush()
    journey = partner.journey; create_draft(journey.profile, analysis)
    audit("womens_health.semen_analysis_created", actor, analysis, partner_id=partner.id)
    db.session.commit(); return analysis
