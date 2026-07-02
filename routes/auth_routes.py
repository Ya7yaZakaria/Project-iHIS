"""Authentication routes backed by the authentication service layer."""

from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from auth.decorators import role_required
from auth.forms import ChangePasswordForm, LoginForm, RegistrationForm
from extensions import db
from models import Role
from services.auth_service import (authenticate_user, change_password,
                                   get_redirect_for_role, log_auth_event,
                                   register_user)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _safe_next_url(candidate):
    if not candidate:
        return None
    parsed = urlsplit(candidate)
    return candidate if not parsed.scheme and not parsed.netloc and candidate.startswith("/") else None


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(get_redirect_for_role(current_user))
    form = LoginForm()
    if form.validate_on_submit():
        user, error = authenticate_user(form.identifier.data, form.password.data)
        if user:
            next_url = _safe_next_url(request.args.get("next"))
            session.clear()
            session.permanent = True
            login_user(user, remember=form.remember.data)
            return redirect(next_url or get_redirect_for_role(user))
        flash(error, "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.get("/logout")
@login_required
def logout():
    user = current_user._get_current_object()
    log_auth_event("auth.logout", actor=user, target_user=user, commit=True)
    logout_user()
    session.clear()
    flash("You have been signed out securely.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
@role_required("Super Admin", "Admin")
def register():
    form = RegistrationForm()
    roles = db.session.execute(db.select(Role).where(Role.is_active.is_(True), Role.deleted_at.is_(None)).order_by(Role.name)).scalars().all()
    if not current_user.has_role("Super Admin"):
        roles = [role for role in roles if role.name not in {"Super Admin", "Admin"}]
    form.role_id.choices = [(role.id, role.name) for role in roles]
    if form.validate_on_submit():
        role = db.session.get(Role, form.role_id.data)
        if role not in roles:
            flash("The selected role is not permitted.", "danger")
        else:
            try:
                user = register_user(form.username.data, form.email.data, form.first_name.data, form.last_name.data, form.password.data, role, current_user)
                flash(f"User {user.username} was registered.", "success")
                return redirect(url_for("auth.profile"))
            except (ValueError, PermissionError) as exc:
                flash(str(exc), "danger")
    return render_template("auth/register.html", form=form)


@auth_bp.get("/profile")
@login_required
def profile():
    return render_template("auth/profile.html")


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password_view():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        changed, error = change_password(current_user, form.current_password.data, form.new_password.data)
        if changed:
            flash("Your password has been changed.", "success")
            return redirect(url_for("auth.profile"))
        flash(error, "danger")
    return render_template("auth/change_password.html", form=form)


@auth_bp.get("/forgot-password")
def forgot_password():
    return render_template("auth/forgot_password.html")
