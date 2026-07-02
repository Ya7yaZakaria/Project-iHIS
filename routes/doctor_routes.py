"""Doctor route placeholders."""
from flask import Blueprint
from auth.decorators import role_required
doctor_bp = Blueprint("doctors", __name__, url_prefix="/doctors")

@doctor_bp.get("/")
@role_required("Doctor", "Women’s Health Doctor")
def index(): return "Doctor module placeholder"
