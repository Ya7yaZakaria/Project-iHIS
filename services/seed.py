"""Idempotent reference-data seeding for a new iHIS database."""

import os
import secrets

from extensions import db
from models import Department, DentalSpecialty, Permission, Role, Specialty, User


ROLE_NAMES = (
    "Super Admin", "Admin", "Doctor", "Women’s Health Doctor", "Receptionist",
    "Nurse", "Laboratory", "Radiology", "Pharmacist", "Dentist",
    "Rehabilitation Specialist", "Patient",
)

PERMISSION_MODULES = {
    "administration": ("view", "manage"),
    "patients": ("view", "create", "update"),
    "appointments": ("view", "create", "update", "cancel"),
    "emr": ("view", "create", "update", "sign"),
    "laboratory": ("view", "order", "result", "validate"),
    "radiology": ("view", "order", "report", "validate"),
    "pharmacy": ("view", "dispense", "manage_inventory"),
    "dentistry": ("view", "create", "update"),
    "rehabilitation": ("view", "create", "update"),
    "nursing": ("view", "record"),
    "reports": ("view", "generate"),
    "womens_health": ("view", "create", "update", "sign"),
    "users": ("view", "manage", "reset_password"),
    "roles": ("view", "manage_permissions"),
}

ROLE_PERMISSION_MAP = {
    "Admin": {"administration.view", "administration.manage", "reports.view", "reports.generate", "users.view", "users.manage", "users.reset_password", "roles.view"},
    "Doctor": {"patients.view", "appointments.view", "emr.view", "emr.create", "emr.update", "emr.sign", "laboratory.order", "radiology.order"},
    "Women’s Health Doctor": {"patients.view", "appointments.view", "emr.view", "emr.create", "emr.update", "emr.sign", "laboratory.order", "radiology.order", "womens_health.view", "womens_health.create", "womens_health.update", "womens_health.sign"},
    "Receptionist": {"patients.view", "patients.create", "patients.update", "appointments.view", "appointments.create", "appointments.update", "appointments.cancel"},
    "Nurse": {"patients.view", "emr.view", "nursing.view", "nursing.record"},
    "Laboratory": {"patients.view", "laboratory.view", "laboratory.result", "laboratory.validate"},
    "Radiology": {"patients.view", "radiology.view", "radiology.report", "radiology.validate"},
    "Pharmacist": {"patients.view", "pharmacy.view", "pharmacy.dispense", "pharmacy.manage_inventory"},
    "Dentist": {"patients.view", "dentistry.view", "dentistry.create", "dentistry.update"},
    "Rehabilitation Specialist": {"patients.view", "rehabilitation.view", "rehabilitation.create", "rehabilitation.update"},
    "Patient": {"patients.view", "appointments.view", "laboratory.view", "radiology.view"},
}

SPECIALTIES = (
    ("IM", "Internal Medicine", "medical"), ("CARD", "Cardiology", "medical"),
    ("NEUR", "Neurology", "medical"), ("PED", "Pediatrics", "medical"),
    ("ORTH", "Orthopedics", "surgical"), ("SURG", "Surgery", "surgical"),
    ("OBGYN", "Obstetrics and Gynecology", "womens_health"),
    ("MFM", "Maternal-Fetal Medicine", "womens_health"),
    ("REI", "Reproductive Endocrinology and Infertility", "womens_health"),
    ("RAD", "Radiology", "diagnostic"), ("PATH", "Pathology", "diagnostic"),
    ("PMR", "Physical Medicine and Rehabilitation", "rehabilitation"),
)

DENTAL_SPECIALTIES = (
    ("GEN-DENT", "General Dentistry"), ("ORTHO-DENT", "Orthodontics"),
    ("ENDO-DENT", "Endodontics"), ("PERIO-DENT", "Periodontics"),
    ("ORAL-SURG", "Oral Surgery"), ("PED-DENT", "Pediatric Dentistry"),
    ("IMPLANT", "Implantology"),
)

DEPARTMENTS = (
    ("OPD", "Outpatient Department"), ("ER", "Emergency Department"),
    ("OBGYN", "Women’s Health"), ("LAB", "Laboratory"),
    ("RAD", "Radiology"), ("PHARM", "Pharmacy"), ("DENT", "Dentistry"),
    ("REHAB", "Physical Therapy and Rehabilitation"), ("NURS", "Nursing"),
    ("ADMIN", "Administration"),
)


def _get_or_create(model, defaults=None, **lookup):
    instance = db.session.execute(db.select(model).filter_by(**lookup)).scalar_one_or_none()
    if instance is None:
        instance = model(**lookup, **(defaults or {}))
        db.session.add(instance)
    return instance


def seed_database(admin_password=None):
    """Create reference data and the initial super admin without overwriting data."""
    generated_password = None
    try:
        existing_role_names = set(db.session.execute(db.select(Role.name)).scalars())
        existing_permission_codes = set(db.session.execute(db.select(Permission.code)).scalars())
        roles = {name: _get_or_create(Role, name=name, defaults={"is_system": True}) for name in ROLE_NAMES}
        permissions = []
        for module, actions in PERMISSION_MODULES.items():
            for action in actions:
                code = f"{module}.{action}"
                permissions.append(_get_or_create(
                    Permission, code=code,
                    defaults={"module": module, "action": action, "description": f"{action.replace('_', ' ').title()} {module.replace('_', ' ')}"},
                ))
        for permission in permissions:
            if permission not in roles["Super Admin"].permissions and ("Super Admin" not in existing_role_names or permission.code not in existing_permission_codes):
                roles["Super Admin"].permissions.append(permission)
        permissions_by_code = {permission.code: permission for permission in permissions}
        for role_name, permission_codes in ROLE_PERMISSION_MAP.items():
            for code in permission_codes:
                permission = permissions_by_code[code]
                if permission not in roles[role_name].permissions and (role_name not in existing_role_names or code not in existing_permission_codes):
                    roles[role_name].permissions.append(permission)

        for code, name, category in SPECIALTIES:
            _get_or_create(Specialty, code=code, defaults={"name": name, "category": category})
        for code, name in DENTAL_SPECIALTIES:
            _get_or_create(DentalSpecialty, code=code, defaults={"name": name})
        for code, name in DEPARTMENTS:
            _get_or_create(Department, code=code, defaults={"name": name})

        username = os.getenv("SEED_ADMIN_USERNAME", "superadmin")
        email = os.getenv("SEED_ADMIN_EMAIL", "superadmin@ihis.local")
        admin = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()
        if admin is None:
            password = admin_password or os.getenv("SEED_ADMIN_PASSWORD")
            if not password:
                password = generated_password = secrets.token_urlsafe(18)
            admin = User(
                username=username, email=email,
                first_name=os.getenv("SEED_ADMIN_FIRST_NAME", "System"),
                last_name=os.getenv("SEED_ADMIN_LAST_NAME", "Administrator"),
                must_change_password=True,
            )
            admin.set_password(password)
            admin.roles.append(roles["Super Admin"])
            db.session.add(admin)
        elif roles["Super Admin"] not in admin.roles:
            admin.roles.append(roles["Super Admin"])
        db.session.commit()
        return {"admin": admin, "generated_password": generated_password}
    except Exception:
        db.session.rollback()
        raise
