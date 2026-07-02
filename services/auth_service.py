"""Authentication and authorization application services."""

import hashlib
from datetime import timedelta

from flask import current_app, has_request_context, request
from sqlalchemy import or_

from extensions import db
from models import AuditLog, Role, User
from models.base import utcnow


ROLE_REDIRECTS = {
    "Super Admin": "/dashboard/super-admin", "Admin": "/dashboard/admin",
    "Doctor": "/dashboard/doctor", "Women’s Health Doctor": "/dashboard/womens-health",
    "Receptionist": "/dashboard/reception", "Nurse": "/dashboard/nursing",
    "Laboratory": "/dashboard/laboratory", "Radiology": "/dashboard/radiology",
    "Pharmacist": "/dashboard/pharmacy", "Dentist": "/dashboard/dentistry",
    "Rehabilitation Specialist": "/dashboard/rehabilitation", "Patient": "/dashboard/patient",
}


def _identifier_fingerprint(identifier):
    return hashlib.sha256(identifier.strip().lower().encode("utf-8")).hexdigest()[:16]


def log_auth_event(action, outcome="success", actor=None, target_user=None, details=None, commit=False):
    context = dict(details or {})
    ip_address = None
    if has_request_context():
        ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
        context["user_agent"] = request.user_agent.string[:255]
    event = AuditLog(
        actor_user_id=actor.id if actor else None, action=action, resource_type="user",
        resource_id=target_user.id if target_user else None, outcome=outcome,
        ip_address=(ip_address or "")[:45] or None, details=context or None,
        tenant_id=(target_user.tenant_id if target_user else None),
    )
    db.session.add(event)
    if commit:
        db.session.commit()
    return event


def authenticate_user(identifier, password):
    normalized = identifier.strip().lower()
    user = db.session.execute(db.select(User).where(or_(db.func.lower(User.username) == normalized, db.func.lower(User.email) == normalized))).scalar_one_or_none()
    fingerprint = _identifier_fingerprint(normalized)
    if not user:
        log_auth_event("auth.login_failed", "failure", details={"reason": "invalid_credentials", "identifier_fingerprint": fingerprint}, commit=True)
        return None, "Invalid username/email or password."
    if not user.is_active or user.is_deleted:
        log_auth_event("auth.login_failed", "failure", target_user=user, details={"reason": "inactive"}, commit=True)
        return None, "This account is unavailable. Contact an administrator."
    if user.is_locked:
        log_auth_event("auth.login_failed", "failure", target_user=user, details={"reason": "locked"}, commit=True)
        return None, "This account is temporarily locked. Try again later."
    if user.locked_until:
        user.reset_failed_logins()
    if not user.check_password(password):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        reason = "invalid_credentials"
        if user.failed_login_attempts >= current_app.config["MAX_FAILED_LOGIN_ATTEMPTS"]:
            user.locked_until = utcnow() + timedelta(minutes=current_app.config["ACCOUNT_LOCKOUT_MINUTES"])
            reason = "account_locked"
        log_auth_event("auth.login_failed", "failure", target_user=user, details={"reason": reason, "attempts": user.failed_login_attempts})
        db.session.commit()
        return None, "Invalid username/email or password."
    user.reset_failed_logins()
    user.last_login_at = utcnow()
    log_auth_event("auth.login_succeeded", actor=user, target_user=user)
    db.session.commit()
    return user, None


def register_user(username, email, first_name, last_name, password, role, actor):
    username, email = username.strip().lower(), email.strip().lower()
    duplicate = db.session.execute(db.select(User).where(or_(db.func.lower(User.username) == username, db.func.lower(User.email) == email))).scalar_one_or_none()
    if duplicate:
        raise ValueError("A user with that username or email already exists.")
    if not actor.has_role("Super Admin") and role.name in {"Super Admin", "Admin"}:
        raise PermissionError("Only a Super Admin may assign administrative roles.")
    if len(password) < current_app.config["MIN_PASSWORD_LENGTH"]:
        raise ValueError(f"Password must contain at least {current_app.config['MIN_PASSWORD_LENGTH']} characters.")
    user = User(username=username, email=email, first_name=first_name.strip(), last_name=last_name.strip(), roles=[role], must_change_password=True)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    log_auth_event("auth.user_registered", actor=actor, target_user=user, details={"role": role.name})
    db.session.commit()
    return user


def change_password(user, current_password, new_password):
    if not user.check_password(current_password):
        return False, "Current password is incorrect."
    if current_password == new_password:
        return False, "The new password must be different."
    if len(new_password) < current_app.config["MIN_PASSWORD_LENGTH"]:
        return False, f"Password must contain at least {current_app.config['MIN_PASSWORD_LENGTH']} characters."
    user.set_password(new_password)
    user.password_changed_at = utcnow()
    user.must_change_password = False
    log_auth_event("auth.password_changed", actor=user, target_user=user)
    db.session.commit()
    return True, None


def check_user_permission(user, permission_code):
    return bool(user and (user.has_role("Super Admin") or user.has_permission(permission_code)))


def get_redirect_for_role(user):
    role = user.primary_role
    return ROLE_REDIRECTS.get(role.name if role else None, "/auth/profile")
