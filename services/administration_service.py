"""Operational administration services for iHIS."""

from datetime import datetime, time, timedelta, timezone

from flask import has_request_context, request
from sqlalchemy import func
from sqlalchemy.orm import joinedload, selectinload

from extensions import db
from models import (Appointment, AuditLog, Department, Doctor, LabOrder, Patient,
                    Prescription, RadiologyOrder, Specialty, User)


class AdministrationServiceError(ValueError):
    pass


def _assert_admin(actor):
    if not actor or not actor.has_role("Super Admin", "Admin"):
        raise PermissionError("Administrator access is required.")


def _audit(action, actor, resource_type="administration", resource_id=None, details=None):
    ip = request.headers.get("X-Forwarded-For", request.remote_addr) if has_request_context() else None
    db.session.add(AuditLog(actor_user_id=actor.id if actor else None, action=action,
                            resource_type=resource_type, resource_id=resource_id,
                            ip_address=(ip or "")[:45] or None, details=details or None))


def _range(start_date=None, end_date=None, days=30):
    now = datetime.now(timezone.utc)
    start = datetime.combine(start_date, time.min, tzinfo=timezone.utc) if start_date else now - timedelta(days=days)
    end = datetime.combine(end_date, time.max, tzinfo=timezone.utc) if end_date else now
    return start, end


def _count(model, *criteria):
    return db.session.scalar(db.select(func.count(model.id)).where(model.deleted_at.is_(None), *criteria)) or 0


def get_patient_volume_stats(start_date=None, end_date=None, department_id=None):
    start, end = _range(start_date, end_date)
    criteria = [Appointment.scheduled_start.between(start, end)]
    if department_id:
        criteria.append(Appointment.department_id == department_id)
    return {
        "appointments": _count(Appointment, *criteria),
        "completed_visits": _count(Appointment, *criteria, Appointment.status == "completed"),
        "no_shows": _count(Appointment, *criteria, Appointment.status.in_(("no_show", "no-show"))),
        "active_patients": _count(Patient, Patient.is_active.is_(True)),
        "new_patients": _count(Patient, Patient.created_at.between(start, end)),
    }


def get_department_performance(start_date=None, end_date=None, department_id=None):
    start, end = _range(start_date, end_date)
    departments = db.session.scalars(db.select(Department).where(
        Department.deleted_at.is_(None), *( [Department.id == department_id] if department_id else [] )
    ).order_by(Department.name)).all()
    rows = []
    for department in departments:
        criteria = (Appointment.department_id == department.id, Appointment.scheduled_start.between(start, end))
        total = _count(Appointment, *criteria)
        completed = _count(Appointment, *criteria, Appointment.status == "completed")
        rows.append({"department": department, "appointments": total, "completed": completed,
                     "completion_rate": round(completed * 100 / total, 1) if total else 0,
                     "staff_count": _count(User, User.department_id == department.id, User.is_active.is_(True))})
    return rows


def get_staff_activity(department_id=None):
    statement = db.select(User).options(selectinload(User.roles), joinedload(User.department),
        joinedload(User.doctor_profile).joinedload(Doctor.specialty)).where(User.deleted_at.is_(None))
    if department_id:
        statement = statement.where(User.department_id == department_id)
    users = db.session.scalars(statement.order_by(User.last_name, User.first_name)).unique().all()
    return [{"user": user, "last_login_at": user.last_login_at,
             "status": "Active" if user.is_active else "Inactive"} for user in users]


def create_department(*, code, name, department_type, actor, description=None, location=None):
    _assert_admin(actor)
    code, name = code.strip().upper(), name.strip()
    duplicate = db.session.scalar(db.select(Department).where(
        (func.lower(Department.code) == code.lower()) | (func.lower(Department.name) == name.lower())))
    if duplicate:
        raise AdministrationServiceError("A department with that code or name already exists.")
    department = Department(code=code, name=name, department_type=department_type,
                            description=(description or "").strip() or None,
                            location=(location or "").strip() or None)
    db.session.add(department)
    db.session.flush()
    _audit("administration.department_created", actor, "department", department.id,
           {"code": code, "name": name, "department_type": department_type})
    db.session.commit()
    return department


def update_department(department, *, actor, **data):
    _assert_admin(actor)
    before = {key: getattr(department, key) for key in ("code", "name", "department_type", "location", "description", "is_active")}
    for key in before:
        if key in data:
            value = data[key].strip() if isinstance(data[key], str) else data[key]
            setattr(department, key, value if isinstance(value, bool) else (value or None))
    department.code = department.code.upper()
    _audit("administration.department_updated", actor, "department", department.id,
           {"before": before, "after": {key: getattr(department, key) for key in before}})
    db.session.commit()
    return department


def deactivate_department(department, actor):
    _assert_admin(actor)
    department.is_active = False
    _audit("administration.department_deactivated", actor, "department", department.id)
    db.session.commit()
    return department


def assign_staff_to_department(user, department, actor, specialty=None):
    _assert_admin(actor)
    previous = user.department_id
    user.department = department
    if user.doctor_profile:
        user.doctor_profile.department = department
        if specialty is not None:
            user.doctor_profile.specialty = specialty
    _audit("administration.staff_assigned", actor, "user", user.id,
           {"from_department_id": previous, "department_id": department.id,
            "specialty_id": specialty.id if specialty else None})
    db.session.commit()
    return user


def get_resource_allocation(department_id=None):
    departments = db.session.scalars(db.select(Department).where(
        Department.deleted_at.is_(None), *( [Department.id == department_id] if department_id else [] )
    ).order_by(Department.name)).all()
    now, horizon = datetime.now(timezone.utc), datetime.now(timezone.utc) + timedelta(days=7)
    return [{"department": item,
             "doctors": _count(Doctor, Doctor.department_id == item.id, Doctor.is_active.is_(True)),
             "nurses": db.session.scalar(db.select(func.count(User.id)).where(User.department_id == item.id,
                 User.is_active.is_(True), User.roles.any(name="Nurse"))) or 0,
             "staff": _count(User, User.department_id == item.id, User.is_active.is_(True)),
             "weekly_workload": _count(Appointment, Appointment.department_id == item.id,
                 Appointment.scheduled_start.between(now, horizon)),
             "rooms": "Placeholder", "clinic_schedules": "Placeholder"} for item in departments]


def get_operational_kpis(start_date=None, end_date=None, department_id=None, doctor_id=None):
    start, end = _range(start_date, end_date)
    appointment_filters = [Appointment.scheduled_start.between(start, end)]
    if department_id: appointment_filters.append(Appointment.department_id == department_id)
    if doctor_id: appointment_filters.append(Appointment.doctor_id == doctor_id)
    lab_filters = [LabOrder.ordered_at.between(start, end)]
    radiology_filters = [RadiologyOrder.ordered_at.between(start, end)]
    prescription_filters = [Prescription.prescribed_at.between(start, end)]
    if department_id: lab_filters.append(LabOrder.department_id == department_id)
    if doctor_id:
        lab_filters.append(LabOrder.doctor_id == doctor_id)
        radiology_filters.append(RadiologyOrder.doctor_id == doctor_id)
        prescription_filters.append(Prescription.doctor_id == doctor_id)
    volume = get_patient_volume_stats(start_date, end_date, department_id)
    return {**volume, "lab_orders": _count(LabOrder, *lab_filters),
            "radiology_orders": _count(RadiologyOrder, *radiology_filters),
            "prescriptions": _count(Prescription, *prescription_filters),
            "department_activity": get_department_performance(start_date, end_date, department_id),
            "start": start, "end": end}


def get_administration_dashboard(department_id=None):
    now = datetime.now(timezone.utc)
    periods = {}
    for label, days in (("daily", 1), ("weekly", 7), ("monthly", 30)):
        periods[label] = get_patient_volume_stats((now - timedelta(days=days)).date(), now.date(), department_id)
    return {"patient_volumes": periods, "department_performance": get_department_performance(department_id=department_id),
            "staff_activity": get_staff_activity(department_id), "resources": get_resource_allocation(department_id),
            "kpis": get_operational_kpis(department_id=department_id), "revenue": "Revenue overview placeholder"}


def log_administration_access(action, actor, details=None):
    _audit(action, actor, details=details)
    db.session.commit()
