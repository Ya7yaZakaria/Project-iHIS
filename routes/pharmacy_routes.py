"""Pharmacy route placeholders."""
from flask import Blueprint
from auth.decorators import role_required
pharmacy_bp = Blueprint("pharmacy", __name__, url_prefix="/pharmacy")

@pharmacy_bp.get("/")
@role_required("Pharmacist")
def index(): return "Pharmacy module placeholder"
