"""Radiology route placeholders."""
from flask import Blueprint
from auth.decorators import role_required
radiology_bp = Blueprint("radiology", __name__, url_prefix="/radiology")

@radiology_bp.get("/")
@role_required("Radiology")
def index(): return "Radiology module placeholder"
