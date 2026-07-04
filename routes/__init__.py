"""Blueprint registry for the iHIS web modules."""

from .auth_routes import auth_bp
from .appointment_routes import appointments_bp
from .dentistry_routes import dentistry_bp
from .doctor_routes import doctor_bp
from .dashboard_routes import dashboard_bp
from .emr_routes import emr_bp
from .laboratory_routes import laboratory_bp, patient_labs_bp
from .patient_routes import patient_bp
from .pharmacy_routes import patient_medication_bp, pharmacy_bp
from .radiology_routes import radiology_bp, patient_radiology_bp
from .reception_routes import reception_bp
from .rehabilitation_routes import rehabilitation_bp
from .womens_health_routes import womens_health_bp, womens_health_clinical_bp
from .user_routes import roles_bp, users_bp

BLUEPRINTS = (
    auth_bp,
    dashboard_bp,
    appointments_bp,
    patient_bp,
    doctor_bp,
    emr_bp,
    laboratory_bp,
    patient_labs_bp,

    radiology_bp,
    patient_radiology_bp,

    pharmacy_bp,
    patient_medication_bp,
    dentistry_bp,
    rehabilitation_bp,
    womens_health_bp,
    womens_health_clinical_bp,
    reception_bp,
    users_bp,
    roles_bp,
)
