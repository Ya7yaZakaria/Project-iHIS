from uuid import uuid4
from extensions import db
from models import (FollicleMeasurement, FolliculometryRecord, InfertilityCycle,
                    InfertilityJourney, IUICycle, OvulationInductionCycle)
from .common import audit, create_draft, now, require_manage, timeline_event
from .womens_health_calculators import calculate_cycle_day


def create_infertility_journey(profile, *, actor, infertility_type, duration_months=None, **fields):
    require_manage(actor)
    if infertility_type not in {"primary", "secondary"}: raise ValueError("Invalid infertility type.")
    journey = InfertilityJourney(journey_number=f"INF-{uuid4().hex[:10].upper()}", profile=profile,
        infertility_type=infertility_type, duration_months=duration_months, started_at=now(), **fields)
    db.session.add(journey); db.session.flush(); create_draft(profile, journey)
    profile.active_journey_type, profile.active_journey_id = "infertility", journey.id
    timeline_event(profile, "infertility_journey", "Infertility journey created", journey,
                   infertility_journey=journey, summary=infertility_type.title())
    audit("womens_health.infertility_journey_created", actor, journey)
    db.session.commit(); return journey


def create_infertility_cycle(journey, *, actor, cycle_type, cycle_start_date, protocol=None,
                             timed_intercourse_advice=None):
    require_manage(actor)
    number = (db.session.scalar(db.select(db.func.max(InfertilityCycle.cycle_number)).where(
        InfertilityCycle.journey_id == journey.id)) or 0) + 1
    cycle = InfertilityCycle(journey=journey, cycle_number=number, cycle_type=cycle_type,
        cycle_start_date=cycle_start_date, protocol=protocol, status="active",
        timed_intercourse_advice=timed_intercourse_advice)
    db.session.add(cycle); db.session.flush()
    if cycle_type in {"ovulation_induction", "oiti"}:
        db.session.add(OvulationInductionCycle(infertility_cycle_id=cycle.id, medication_protocol=protocol))
    create_draft(journey.profile, cycle)
    timeline_event(journey.profile, "infertility_cycle", f"Infertility cycle {number}", cycle,
                   infertility_journey=journey, summary=cycle_type)
    audit("womens_health.infertility_cycle_created", actor, cycle, journey_id=journey.id)
    db.session.commit(); return cycle


def add_folliculometry_record(cycle, *, actor, scan_at=None, cycle_day=None,
                              endometrium_mm=None, endometrium_pattern=None, notes=None):
    require_manage(actor); scan_at = scan_at or now()
    day = cycle_day or calculate_cycle_day(cycle.cycle_start_date, scan_at.date())
    record = FolliculometryRecord(cycle=cycle, scan_at=scan_at, cycle_day=day,
        endometrium_mm=endometrium_mm, endometrium_pattern=endometrium_pattern, notes=notes)
    db.session.add(record); db.session.flush(); create_draft(cycle.journey.profile, record)
    timeline_event(cycle.journey.profile, "folliculometry", f"Folliculometry day {day}", record,
                   event_at=scan_at, infertility_journey=cycle.journey)
    audit("womens_health.folliculometry_created", actor, record, cycle_id=cycle.id)
    db.session.commit(); return record


def add_follicle_measurement(record, *, actor, ovary, follicle_number, diameter_mm, dimensions=None):
    require_manage(actor)
    if ovary not in {"left", "right"}: raise ValueError("Ovary must be left or right.")
    item = FollicleMeasurement(record=record, ovary=ovary, follicle_number=follicle_number,
                               diameter_mm=diameter_mm, dimensions=dimensions)
    db.session.add(item); db.session.flush()
    audit("womens_health.follicle_measurement_added", actor, item, record_id=record.id)
    db.session.commit(); return item


def create_iui_cycle(cycle, *, actor, partner_id=None, performed_at=None,
                     stimulation_protocol=None, semen_preparation_summary=None,
                     trigger_at=None, luteal_support=None, pregnancy_test_date=None,
                     post_wash_count=None, semen_analysis_id=None, outcome=None):
    require_manage(actor)
    if cycle.iui_cycle: raise ValueError("IUI record already exists for this cycle.")
    iui = IUICycle(cycle=cycle, partner_id=partner_id, performed_at=performed_at,
        stimulation_protocol=stimulation_protocol, semen_preparation_summary=semen_preparation_summary,
        trigger_at=trigger_at, luteal_support=luteal_support, pregnancy_test_date=pregnancy_test_date,
        post_wash_count=post_wash_count, semen_analysis_id=semen_analysis_id, outcome=outcome)
    db.session.add(iui); db.session.flush(); create_draft(cycle.journey.profile, iui)
    timeline_event(cycle.journey.profile, "iui", "IUI cycle", iui,
                   event_at=performed_at or now(), infertility_journey=cycle.journey, summary=outcome)
    audit("womens_health.iui_created", actor, iui, cycle_id=cycle.id)
    db.session.commit(); return iui
