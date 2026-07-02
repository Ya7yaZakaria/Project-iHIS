"""Transactional user, role, and permission administration services."""

from flask import current_app
from sqlalchemy import or_
from sqlalchemy.orm import joinedload, selectinload

from extensions import db
from models import (Department, Dentist, Doctor, Permission, PhysicalTherapist,
                    Role, Specialty, User)
from services.auth_service import log_auth_event


PROTECTED_ROLE_NAMES = {"Super Admin", "Admin"}
DOCTOR_ROLE_NAMES = {"Doctor", "Women’s Health Doctor"}


def _normalize(value):
    return value.strip().lower()


def _assert_admin(actor):
    if not actor or not actor.has_role("Super Admin", "Admin"):
        raise PermissionError("Administrator access is required.")


def _assert_manageable(actor, target=None, role=None, action="manage"):
    _assert_admin(actor)
    if target is not None and target.id == actor.id and action in {"edit", "deactivate", "reset_password", "activate"}:
        raise PermissionError("Use your personal profile settings for your own account.")
    if not actor.has_role("Super Admin"):
        target_protected = target and target.has_role(*PROTECTED_ROLE_NAMES)
        role_protected = role and role.name in PROTECTED_ROLE_NAMES
        if target_protected or role_protected:
            raise PermissionError("Only a Super Admin may manage administrative accounts.")


def _find_duplicate(username, email, exclude_user_id=None):
    statement = db.select(User).where(or_(db.func.lower(User.username) == username, db.func.lower(User.email) == email))
    if exclude_user_id:
        statement = statement.where(User.id != exclude_user_id)
    return db.session.execute(statement).scalar_one_or_none()


def _sync_provider_department(user):
    for model in (Doctor, Dentist, PhysicalTherapist):
        profile = db.session.execute(db.select(model).filter_by(user_id=user.id)).scalar_one_or_none()
        if profile:
            profile.department_id = user.department_id


def _sync_doctor_profile(user, role, specialty_id=None, license_number=None):
    profile = db.session.execute(db.select(Doctor).filter_by(user_id=user.id)).scalar_one_or_none()
    if role.name in DOCTOR_ROLE_NAMES:
        if profile is None:
            profile = Doctor(user=user)
            db.session.add(profile)
        profile.is_active = True
        profile.department_id = user.department_id
        profile.specialty_id = specialty_id or None
        profile.license_number = license_number.strip() if license_number else None
    elif profile:
        profile.is_active = False


def assign_role(user, role, actor, specialty_id=None, license_number=None):
    _assert_manageable(actor, target=user, role=role, action="assign_role")
    previous = [item.name for item in user.roles]
    user.roles = [role]
    _sync_doctor_profile(user, role, specialty_id, license_number)
    log_auth_event("users.role_assigned", actor=actor, target_user=user, details={"before": previous, "after": [role.name]})
    return user


def create_user(*, username, email, first_name, last_name, password, role, actor,
                phone=None, department_id=None, specialty_id=None, license_number=None):
    _assert_manageable(actor, role=role, action="create")
    username, email = _normalize(username), _normalize(email)
    if _find_duplicate(username, email):
        raise ValueError("A user with that username or email already exists.")
    if len(password) < current_app.config["MIN_PASSWORD_LENGTH"]:
        raise ValueError(f"Password must contain at least {current_app.config['MIN_PASSWORD_LENGTH']} characters.")
    user = User(
        username=username, email=email, first_name=first_name.strip(), last_name=last_name.strip(),
        phone=phone.strip() if phone else None, department_id=department_id or None,
        must_change_password=True, roles=[role],
    )
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.flush()
        _sync_doctor_profile(user, role, specialty_id, license_number)
        log_auth_event("users.created", actor=actor, target_user=user, details={"role": role.name, "department_id": user.department_id})
        db.session.commit()
        return user
    except Exception:
        db.session.rollback()
        raise


def update_user(user, *, username, email, first_name, last_name, role, actor,
                phone=None, department_id=None, specialty_id=None, license_number=None):
    _assert_manageable(actor, target=user, role=role, action="edit")
    username, email = _normalize(username), _normalize(email)
    if _find_duplicate(username, email, user.id):
        raise ValueError("A user with that username or email already exists.")
    before = {"username": user.username, "email": user.email, "department_id": user.department_id, "role": user.primary_role.name if user.primary_role else None}
    user.username, user.email = username, email
    user.first_name, user.last_name = first_name.strip(), last_name.strip()
    user.phone, user.department_id = (phone.strip() if phone else None), (department_id or None)
    try:
        assign_role(user, role, actor, specialty_id, license_number)
        _sync_provider_department(user)
        after = {"username": user.username, "email": user.email, "department_id": user.department_id, "role": role.name}
        log_auth_event("users.updated", actor=actor, target_user=user, details={"before": before, "after": after})
        db.session.commit()
        return user
    except Exception:
        db.session.rollback()
        raise


def deactivate_user(user, actor):
    _assert_manageable(actor, target=user, action="deactivate")
    if not user.is_active:
        return user
    user.is_active = False
    log_auth_event("users.deactivated", actor=actor, target_user=user)
    db.session.commit()
    return user


def activate_user(user, actor):
    _assert_manageable(actor, target=user, action="activate")
    user.is_active = True
    user.reset_failed_logins()
    log_auth_event("users.activated", actor=actor, target_user=user)
    db.session.commit()
    return user


def reset_user_password(user, password, actor):
    _assert_manageable(actor, target=user, action="reset_password")
    if len(password) < current_app.config["MIN_PASSWORD_LENGTH"]:
        raise ValueError(f"Password must contain at least {current_app.config['MIN_PASSWORD_LENGTH']} characters.")
    user.set_password(password)
    user.must_change_password = True
    user.password_changed_at = None
    user.reset_failed_logins()
    log_auth_event("users.password_reset", actor=actor, target_user=user)
    db.session.commit()
    return user


def assign_permissions(role, permission_ids, actor):
    if not actor.has_role("Super Admin"):
        raise PermissionError("Only a Super Admin may change role permissions.")
    if role.name == "Super Admin":
        raise PermissionError("Super Admin always has full access and cannot be restricted.")
    permissions = db.session.execute(db.select(Permission).where(Permission.id.in_(set(permission_ids)))).scalars().all() if permission_ids else []
    before = sorted(item.code for item in role.permissions)
    role.permissions = permissions
    log_auth_event("roles.permissions_assigned", actor=actor, details={"role_id": role.id, "role": role.name, "before": before, "after": sorted(item.code for item in permissions)})
    db.session.commit()
    return role


def search_users(search=None, role_id=None, status=None, department_id=None, page=1, per_page=20):
    statement = db.select(User).options(selectinload(User.roles), joinedload(User.department), joinedload(User.doctor_profile).joinedload(Doctor.specialty)).where(User.deleted_at.is_(None))
    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(or_(User.username.ilike(pattern), User.email.ilike(pattern), User.first_name.ilike(pattern), User.last_name.ilike(pattern), User.phone.ilike(pattern)))
    if role_id:
        statement = statement.where(User.roles.any(Role.id == role_id))
    if status == "active":
        statement = statement.where(User.is_active.is_(True))
    elif status == "inactive":
        statement = statement.where(User.is_active.is_(False))
    if department_id:
        statement = statement.where(User.department_id == department_id)
    return db.paginate(statement.order_by(User.last_name, User.first_name), page=max(page, 1), per_page=per_page, error_out=False)
