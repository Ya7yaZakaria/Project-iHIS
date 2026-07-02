"""Laboratory route placeholders."""
from flask import Blueprint
from auth.decorators import role_required
laboratory_bp = Blueprint("laboratory", __name__, url_prefix="/laboratory")

@laboratory_bp.get("/")
@role_required("Laboratory")
def index(): return "Laboratory module placeholder"
