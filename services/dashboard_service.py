"""Unified role dashboard data services."""

from datetime import datetime, timedelta, timezone

from extensions import db
from models import (
    Appointment, AuditLog, DentalRecord, LabOrder, LabResult, MedicationAdministration,
    NursingNote, Patient, PharmacyInventory, Prescription, RadiologyOrder,
    RadiologyReport, RehabilitationRecord, TherapyPlan, User,
)


def _base(**extra):
    data = {"metrics": [], "worklists": [], "alerts": [], "recent_activity": [],
            "quick_actions": [], "placeholders": []}
    data.update(extra)
    return data


def _metric(label, value, icon="activity", tone="primary"):
    return {"label": label, "value": value, "icon": icon, "tone": tone}


def _today_bounds():
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=1)


def _all(model, *criteria, limit=None, order_by=None):
    statement = db.select(model).where(model.deleted_at.is_(None), *criteria)
    if order_by is not None: statement = statement.order_by(order_by)
    if limit: statement = statement.limit(limit)
    return list(db.session.scalars(statement).all())


def _patient_for(user):
    return db.session.scalar(db.select(Patient).where(Patient.user_id == user.id, Patient.deleted_at.is_(None)))


def get_doctor_dashboard(user):
    start, end = _today_bounds(); doctor = user.doctor_profile
    if doctor is None:
        return _base(metrics=[_metric("Today’s appointments", 0, "calendar-check"),
            _metric("Pending reports", 0, "file-medical", "warning"), _metric("Follow-up reminders", 0, "arrow-repeat"),
            _metric("Critical patients", 0, "exclamation-triangle", "danger")], placeholders=["AI clinical assistant"])
    appointments = _all(Appointment, Appointment.doctor_id == (doctor.id if doctor else None),
                        Appointment.scheduled_start >= start, Appointment.scheduled_start < end,
                        order_by=Appointment.scheduled_start)
    followups = _all(Appointment, Appointment.doctor_id == (doctor.id if doctor else None),
                     Appointment.appointment_type == "follow_up", Appointment.scheduled_start >= start,
                     limit=8, order_by=Appointment.scheduled_start)
    pending_labs = _all(LabOrder, LabOrder.doctor_id == (doctor.id if doctor else None),
                        LabOrder.status.notin_(("completed", "cancelled")), limit=8, order_by=LabOrder.ordered_at.desc())
    pending_rad = _all(RadiologyOrder, RadiologyOrder.doctor_id == (doctor.id if doctor else None),
                       RadiologyOrder.status.notin_(("completed", "cancelled")), limit=8, order_by=RadiologyOrder.ordered_at.desc())
    return _base(metrics=[_metric("Today’s appointments", len(appointments), "calendar-check"),
        _metric("Pending reports", len(pending_labs) + len(pending_rad), "file-medical", "warning"),
        _metric("Follow-up reminders", len(followups), "arrow-repeat"),
        _metric("Critical patients", 0, "exclamation-triangle", "danger")],
        worklists=appointments, recent_activity=(pending_labs + pending_rad)[:8], follow_ups=followups,
        alerts=[], quick_actions=[("Open appointments", "/appointments"), ("Patient records", "/patients")],
        placeholders=["AI clinical assistant", "Critical patient rules"])


def get_womens_health_dashboard(user):
    from models import InfertilityCycle, IUICycle, Pregnancy, PregnancyVisit
    start, end = _today_bounds()
    pregnancies = _all(Pregnancy, Pregnancy.status == "ongoing")
    visits = _all(PregnancyVisit, PregnancyVisit.visit_at >= start, PregnancyVisit.visit_at < end)
    infertility = _all(InfertilityCycle, InfertilityCycle.status.in_(("planned", "active")))
    iui = _all(IUICycle)
    high_risk = [x for x in pregnancies if x.risk_category in {"high", "critical"}]
    return _base(metrics=[_metric("Pregnant patients today", len(visits), "heart-pulse"),
        _metric("High-risk pregnancies", len(high_risk), "exclamation-triangle", "danger"),
        _metric("ANC visits due", len(visits), "calendar2-week"),
        _metric("Active infertility cycles", len(infertility), "activity")], worklists=visits,
        recent_activity=pregnancies[:8], alerts=high_risk, quick_actions=[("Women’s Health workspace", "/womens-health")],
        placeholders=["Folliculometry due", "Postpartum follow-ups"], iui_cycles=iui)


def get_reception_dashboard(user):
    from services.reception_service import get_reception_dashboard as existing
    source = existing(user); counts = source["counts"]
    return _base(metrics=[_metric("Daily appointments", counts["daily_appointments"], "calendar3"),
        _metric("Waiting queue", counts["waiting"], "people", "warning"),
        _metric("Walk-ins", counts["walk_ins"], "person-plus"),
        _metric("No-shows", counts["no_shows"], "person-x", "danger")], worklists=source["appointments"],
        recent_activity=source["checked_in"], alerts=[], quick_actions=[("Register patient", "/reception/register-patient"),
        ("Open queue", "/reception/queue")], placeholders=[], reception=source)


def get_nursing_dashboard(user):
    from services.nursing_service import build_nursing_dashboard
    source = build_nursing_dashboard(user)
    return _base(metrics=[_metric("Assigned patients", len(source["assigned_patients"]), "people"),
        _metric("Patients needing vitals", len(source["today_tasks"]), "heart-pulse", "warning"),
        _metric("Medication tasks", len(source["recent_medications"]), "capsule"),
        _metric("Nursing alerts", len(source["alerts"]), "bell", "danger")],
        worklists=source["today_tasks"], recent_activity=source["recent_notes"], alerts=source["alerts"],
        quick_actions=[("Nursing workspace", "/nursing")], placeholders=[], nursing=source)


def get_laboratory_dashboard(user):
    pending = _all(LabOrder, LabOrder.status.notin_(("completed", "cancelled")), order_by=LabOrder.ordered_at)
    results = _all(LabResult); start, end = _today_bounds()
    collected = [x for x in pending if x.collected_at and start <= x.collected_at < end]
    awaiting = [x for x in results if x.status == "entered"]
    abnormal = [x for x in results if x.abnormal_flag or x.is_critical]
    return _base(metrics=[_metric("Pending lab orders", len(pending), "clipboard2-pulse"),
        _metric("Samples collected", len(collected), "droplet"), _metric("Awaiting verification", len(awaiting), "check2-square", "warning"),
        _metric("Abnormal results", len(abnormal), "exclamation-circle", "danger")], worklists=pending[:10],
        recent_activity=results[:10], alerts=abnormal[:10], quick_actions=[("Laboratory workspace", "/laboratory")],
        placeholders=["Critical results notifications"])


def get_radiology_dashboard(user):
    pending = _all(RadiologyOrder, RadiologyOrder.status.notin_(("completed", "cancelled")), order_by=RadiologyOrder.ordered_at)
    reports = _all(RadiologyReport); start, end = _today_bounds()
    scheduled = [x for x in pending if x.scheduled_at and start <= x.scheduled_at < end]
    awaiting = [x for x in reports if x.status in {"draft", "preliminary"}]
    urgent = [x for x in pending if x.urgent_finding_flag]
    return _base(metrics=[_metric("Pending radiology orders", len(pending), "radioactive"),
        _metric("Scheduled studies", len(scheduled), "calendar3"), _metric("Awaiting verification", len(awaiting), "file-check", "warning"),
        _metric("Urgent findings", len(urgent), "exclamation-triangle", "danger")], worklists=pending[:10],
        recent_activity=reports[:10], alerts=urgent[:10], quick_actions=[("Radiology workspace", "/radiology")],
        placeholders=["Urgent finding notifications"])


def get_pharmacy_dashboard(user):
    pending = _all(Prescription, Prescription.status == "sent_to_pharmacy", order_by=Prescription.prescribed_at)
    review = _all(Prescription, Prescription.status.in_(("under_review", "partially_dispensed")))
    inventory = _all(PharmacyInventory)
    low = [x for x in inventory if getattr(x, "quantity_on_hand", 0) <= getattr(x, "reorder_level", 0)]
    expired = [x for x in inventory if getattr(x, "expiry_date", None) and x.expiry_date < datetime.now(timezone.utc).date()]
    return _base(metrics=[_metric("Pending prescriptions", len(pending), "prescription2"),
        _metric("Under review", len(review), "search", "warning"), _metric("Dispensed today", 0, "bag-check"),
        _metric("Low stock items", len(low), "boxes", "danger")], worklists=(pending + review)[:10], recent_activity=[],
        alerts=(low + expired)[:10], quick_actions=[("Pharmacy workspace", "/pharmacy")], placeholders=[], expired=expired)


def get_admin_dashboard(user):
    from services.administration_service import get_administration_dashboard
    source = get_administration_dashboard()
    kpis = source["kpis"]
    return _base(metrics=[_metric("Patient volume", kpis["appointments"], "people"),
        _metric("Active patients", kpis["active_patients"], "person-check"),
        _metric("Staff activity", len(source["staff_activity"]), "person-workspace"),
        _metric("Operational KPIs", kpis["completed_visits"], "speedometer2")],
        worklists=source["department_performance"], recent_activity=source["staff_activity"][:10], alerts=[],
        quick_actions=[("Administration", "/administration"), ("Manage staff", "/administration/staff")],
        placeholders=["Revenue overview"], administration=source)


def get_super_admin_dashboard(user):
    users = _all(User)
    audit = list(db.session.scalars(db.select(AuditLog).order_by(AuditLog.created_at.desc()).limit(10)).all())
    active = [x for x in users if x.is_active]
    return _base(metrics=[_metric("Active users", len(active), "people"), _metric("System health", "Operational", "server", "success"),
        _metric("Security alerts", 0, "shield-exclamation", "warning"), _metric("Audit events", len(audit), "journal-text")],
        worklists=audit, recent_activity=active[:10], alerts=[], quick_actions=[("User management", "/users"),
        ("Roles & permissions", "/roles")], placeholders=["Error log viewer", "Backup and restore"])


def get_patient_dashboard(user):
    patient = _patient_for(user)
    if not patient:
        return _base(metrics=[_metric("Upcoming appointments", 0, "calendar3"), _metric("Recent lab results", 0, "clipboard2-pulse"),
            _metric("Active medications", 0, "capsule"), _metric("Health alerts", 0, "bell")],
            placeholders=["AI health insights"], patient=None)
    now = datetime.now(timezone.utc)
    appointments = _all(Appointment, Appointment.patient_id == patient.id, Appointment.scheduled_start >= now,
                        limit=10, order_by=Appointment.scheduled_start)
    labs = _all(LabOrder, LabOrder.patient_id == patient.id, limit=10, order_by=LabOrder.ordered_at.desc())
    medications = _all(Prescription, Prescription.patient_id == patient.id,
                       Prescription.status.notin_(("cancelled", "completed")), limit=10, order_by=Prescription.prescribed_at.desc())
    return _base(metrics=[_metric("Upcoming appointments", len(appointments), "calendar3"),
        _metric("Recent lab results", len(labs), "clipboard2-pulse"), _metric("Active medications", len(medications), "capsule"),
        _metric("Health alerts", 0, "bell")], worklists=appointments, recent_activity=labs, alerts=[],
        quick_actions=[("Appointments", "/appointments")], placeholders=["Medical documents", "AI health insights"], patient=patient,
        medications=medications)


def _generic_role_dashboard(role_name):
    model = DentalRecord if role_name == "Dentist" else RehabilitationRecord
    records = _all(model, limit=10, order_by=model.created_at.desc())
    active = [x for x in records if getattr(x, "is_active", True)]
    return _base(metrics=[_metric("Active patients", len(active), "people"), _metric("Recent records", len(records), "file-medical"),
        _metric("Follow-ups", 0, "arrow-repeat"), _metric("Alerts", 0, "bell")], worklists=records,
        quick_actions=[("Open workspace", "/dentistry" if role_name == "Dentist" else "/rehabilitation")], placeholders=["Advanced analytics"])


ROLE_SERVICES = {"Super Admin": get_super_admin_dashboard, "Admin": get_admin_dashboard,
    "Doctor": get_doctor_dashboard, "Women’s Health Doctor": get_womens_health_dashboard,
    "Receptionist": get_reception_dashboard, "Nurse": get_nursing_dashboard,
    "Laboratory": get_laboratory_dashboard, "Radiology": get_radiology_dashboard,
    "Pharmacist": get_pharmacy_dashboard, "Patient": get_patient_dashboard}


def get_dashboard_for_role(user):
    role = user.primary_role.name if user and user.primary_role else None
    if role in {"Dentist", "Rehabilitation Specialist"}: return _generic_role_dashboard(role)
    service = ROLE_SERVICES.get(role)
    return service(user) if service else _base(placeholders=["No dashboard is configured for this role."])
