"""Role-protected dashboard placeholders for Phase 3."""

from flask import Blueprint, redirect, render_template, url_for

from auth.decorators import role_required

dashboard_bp = Blueprint("dashboards", __name__, url_prefix="/dashboard")


def _dashboard(title, description):
    return render_template("dashboard/role_dashboard.html", title=title, description=description)


@dashboard_bp.get("/super-admin")
@role_required("Super Admin")
def super_admin(): return _dashboard("Super Admin", "System governance, security, and configuration")

@dashboard_bp.get("/admin")
@role_required("Admin")
def admin(): return _dashboard("Administration", "Hospital operations and management")

@dashboard_bp.get("/doctor")
@role_required("Doctor", "Women’s Health Doctor")
def doctor(): return _dashboard("Doctor", "Clinical worklist and electronic medical records")

@dashboard_bp.get("/womens-health")
@role_required("Women’s Health Doctor")
def womens_health(): return redirect(url_for("womens_health.dashboard"))

@dashboard_bp.get("/reception")
@role_required("Receptionist")
def reception(): return redirect(url_for("reception.dashboard"))

@dashboard_bp.get("/nursing")
@role_required("Nurse")
def nursing(): return _dashboard("Nursing", "Patient monitoring, vital signs, and nursing notes")

@dashboard_bp.get("/laboratory")
@role_required("Laboratory")
def laboratory(): return redirect(url_for("laboratory.dashboard"))

@dashboard_bp.get("/radiology")
@role_required("Radiology")
def radiology(): return _dashboard("Radiology", "Imaging worklist and reporting")

@dashboard_bp.get("/pharmacy")
@role_required("Pharmacist")
def pharmacy(): return redirect(url_for("pharmacy.dashboard"))

@dashboard_bp.get("/dentistry")
@role_required("Dentist")
def dentistry(): return _dashboard("Dentistry", "Dental records, charting, and treatment plans")

@dashboard_bp.get("/rehabilitation")
@role_required("Rehabilitation Specialist")
def rehabilitation(): return _dashboard("Rehabilitation", "Therapy plans, sessions, and progress")

@dashboard_bp.get("/patient")
@role_required("Patient")
def patient(): return _dashboard("Patient Portal", "Appointments, records, prescriptions, and reports")
