"""Rehabilitation route placeholders."""
from flask import Blueprint
from auth.decorators import role_required
rehabilitation_bp = Blueprint("rehabilitation", __name__, url_prefix="/rehabilitation")

@rehabilitation_bp.get("/")
@role_required("Rehabilitation Specialist")
def index(): return "Rehabilitation module placeholder"
