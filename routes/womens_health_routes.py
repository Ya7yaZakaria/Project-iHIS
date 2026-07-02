"""Women's Health route placeholders."""
from flask import Blueprint
from auth.decorators import role_required
womens_health_bp = Blueprint("womens_health", __name__, url_prefix="/womens-health")

@womens_health_bp.get("/")
@role_required("Women’s Health Doctor")
def index(): return "Women’s Health module placeholder"
