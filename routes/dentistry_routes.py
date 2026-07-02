"""Dentistry route placeholders."""
from flask import Blueprint
from auth.decorators import role_required
dentistry_bp = Blueprint("dentistry", __name__, url_prefix="/dentistry")

@dentistry_bp.get("/")
@role_required("Dentist")
def index(): return "Dentistry module placeholder"
