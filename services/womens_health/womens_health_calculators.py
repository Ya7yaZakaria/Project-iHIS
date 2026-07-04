"""Deterministic Women's Health calculations; never clinical recommendations."""

from datetime import date, timedelta
from decimal import Decimal


def calculate_edd(lmp):
    if not lmp:
        raise ValueError("LMP is required.")
    return lmp + timedelta(days=280)


def calculate_ga(*, lmp=None, edd=None, on_date=None):
    on_date = on_date or date.today()
    if not lmp and not edd:
        raise ValueError("LMP or EDD is required.")
    effective_lmp = lmp or (edd - timedelta(days=280))
    days = (on_date - effective_lmp).days
    if days < 0:
        raise ValueError("Reference date cannot be before LMP.")
    return {"weeks": days // 7, "days": days % 7, "total_days": days}


def calculate_cycle_day(lmp, on_date=None):
    if not lmp:
        raise ValueError("Cycle LMP is required.")
    on_date = on_date or date.today()
    if on_date < lmp:
        raise ValueError("Scan date cannot be before cycle LMP.")
    return (on_date - lmp).days + 1


def calculate_bmi(weight_kg, height_cm):
    if weight_kg is None or height_cm is None:
        return None
    weight, height = Decimal(str(weight_kg)), Decimal(str(height_cm)) / Decimal("100")
    if weight <= 0 or height <= 0:
        raise ValueError("Weight and height must be positive.")
    return (weight / (height * height)).quantize(Decimal("0.01"))


def pregnancy_risk_summary(pregnancy):
    flags = pregnancy.high_risk_flags or []
    return {"category": pregnancy.risk_category, "flags": flags,
            "disclaimer": "Placeholder summary only; physician assessment is required."}
