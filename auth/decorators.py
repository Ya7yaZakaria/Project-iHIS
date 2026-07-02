"""Reusable RBAC decorators for HTML routes."""

from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def role_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.has_role("Super Admin") or current_user.has_role(*allowed_roles):
                return view(*args, **kwargs)
            abort(403)
        return wrapped
    return decorator


def permission_required(permission_code):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.has_role("Super Admin") or current_user.has_permission(permission_code):
                return view(*args, **kwargs)
            abort(403)
        return wrapped
    return decorator


__all__ = ["login_required", "role_required", "permission_required"]
