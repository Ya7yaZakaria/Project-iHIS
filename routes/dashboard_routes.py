"""Unified role-protected dashboard routes."""

from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from auth.decorators import role_required
from services.auth_service import get_redirect_for_role
from services.dashboard_service import (
    _generic_role_dashboard, get_admin_dashboard, get_doctor_dashboard,
    get_laboratory_dashboard, get_nursing_dashboard, get_patient_dashboard,
    get_pharmacy_dashboard, get_radiology_dashboard, get_reception_dashboard,
    get_super_admin_dashboard, get_womens_health_dashboard,
)

dashboard_bp = Blueprint("dashboards", __name__, url_prefix="/dashboard")


def _render(template, title, data):
    return render_template(f"dashboard/{template}.html", dashboard=data, dashboard_title=title)


@dashboard_bp.get("")
@dashboard_bp.get("/")
@login_required
def index():
    return redirect(get_redirect_for_role(current_user))


@dashboard_bp.get("/super-admin")
@role_required("Super Admin")
def super_admin(): return _render("super_admin", "Super Admin", get_super_admin_dashboard(current_user))


@dashboard_bp.get("/admin")
@role_required("Admin")
def admin(): return _render("admin", "Administration", get_admin_dashboard(current_user))


@dashboard_bp.get("/doctor")
@role_required("Doctor")
def doctor(): return _render("doctor", "Doctor", get_doctor_dashboard(current_user))


@dashboard_bp.get("/womens-health")
@role_required("Women’s Health Doctor")
def womens_health(): return _render("womens_health", "Women’s Health", get_womens_health_dashboard(current_user))


@dashboard_bp.get("/reception")
@role_required("Receptionist")
def reception(): return _render("reception", "Reception", get_reception_dashboard(current_user))


@dashboard_bp.get("/nursing")
@role_required("Nurse")
def nursing(): return _render("nursing", "Nursing", get_nursing_dashboard(current_user))


@dashboard_bp.get("/laboratory")
@role_required("Laboratory")
def laboratory(): return _render("laboratory", "Laboratory", get_laboratory_dashboard(current_user))


@dashboard_bp.get("/radiology")
@role_required("Radiology")
def radiology(): return _render("radiology", "Radiology", get_radiology_dashboard(current_user))


@dashboard_bp.get("/pharmacy")
@role_required("Pharmacist")
def pharmacy(): return _render("pharmacy", "Pharmacy", get_pharmacy_dashboard(current_user))


@dashboard_bp.get("/dentistry")
@role_required("Dentist")
def dentistry(): return _render("dentistry", "Dentistry", _generic_role_dashboard("Dentist"))


@dashboard_bp.get("/rehabilitation")
@role_required("Rehabilitation Specialist")
def rehabilitation(): return _render("rehabilitation", "Rehabilitation", _generic_role_dashboard("Rehabilitation Specialist"))


@dashboard_bp.get("/patient")
@role_required("Patient")
def patient(): return _render("patient", "Patient Portal", get_patient_dashboard(current_user))
