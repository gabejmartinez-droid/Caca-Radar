"""Badges Service — Achievement system for gamification."""
from location_share_service import get_report_age_bucket

BADGES = {
    "first_report": {"name": "Primera Caca", "description": "Tu primer reporte", "icon": "flag", "threshold": 1, "field": "report_count"},
    "reporter_10": {"name": "Patrullero", "description": "10 reportes realizados", "icon": "map-pin", "threshold": 10, "field": "report_count"},
    "reporter_50": {"name": "Detective Marrón", "description": "50 reportes realizados", "icon": "search", "threshold": 50, "field": "report_count"},
    "reporter_100": {"name": "Comisario de Campo", "description": "100 reportes realizados", "icon": "award", "threshold": 100, "field": "report_count"},
    "confirmer_10": {"name": "Testigo Ocular", "description": "10 confirmaciones", "icon": "check-circle", "threshold": 10, "field": "vote_count"},
    "confirmer_50": {"name": "Validador Oficial", "description": "50 confirmaciones", "icon": "shield", "threshold": 50, "field": "vote_count"},
    "streak_3": {"name": "Constante", "description": "3 días de racha", "icon": "flame", "threshold": 3, "field": "streak_days"},
    "streak_7": {"name": "Dedicado", "description": "7 días de racha", "icon": "flame", "threshold": 7, "field": "streak_days"},
    "streak_14": {"name": "Comprometido", "description": "14 días de racha", "icon": "flame", "threshold": 14, "field": "streak_days"},
    "streak_30": {"name": "Imparable", "description": "30 días de racha", "icon": "flame", "threshold": 30, "field": "streak_days"},
    "trusted": {"name": "Fuente Fiable", "description": "Nivel de confianza 80+", "icon": "shield-check", "threshold": 80, "field": "trust_score"},
}


async def check_and_award_badges(db, user_id: str):
    """Check if user qualifies for any new badges and award them."""
    from bson import ObjectId
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return []

    existing = set(user.get("badges", []))
    newly_awarded = []

    for badge_id, badge in BADGES.items():
        if badge_id in existing:
            continue
        user_value = user.get(badge["field"], 0)
        if user_value >= badge["threshold"]:
            existing.add(badge_id)
            newly_awarded.append(badge_id)

    if newly_awarded:
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"badges": list(existing)}}
        )

    return newly_awarded


def get_user_badges(user: dict) -> list:
    """Get full badge info for a user."""
    earned = set(user.get("badges", []))
    result = []
    for badge_id, badge in BADGES.items():
        result.append({
            "id": badge_id,
            "name": badge["name"],
            "description": badge["description"],
            "icon": badge["icon"],
            "earned": badge_id in earned,
            "threshold": badge["threshold"],
            "field": badge["field"]
        })
    return result


def calc_confidence_score(report: dict) -> float:
    """Calculate a confidence score (0-100) for a report."""
    validations = report.get("validation_count", 0)
    upvotes = report.get("upvotes", 0)
    downvotes = report.get("downvotes", 0)
    net = upvotes - downvotes

    # Base from validations (max 40 pts)
    val_score = min(validations * 10, 40)
    # Net votes (max 30 pts)
    vote_score = min(max(net * 5, -15), 30)
    # Status bonus
    status_bonus = 30 if report.get("status") == "verified" else 0

    return max(0, min(100, val_score + vote_score + status_bonus))


def get_freshness_label(created_at: str, refreshed_at: str | None = None) -> str:
    """Map the shared age bucket helper to public freshness labels."""
    bucket = get_report_age_bucket(created_at, refreshed_at)
    if bucket == "fresh":
        return "Fresca"
    if bucket == "old":
        return "En proceso"
    return "Fósil"


def calc_neighborhood_cleanliness(reports: list) -> float:
    """Calculate cleanliness score 0-100 for a set of reports. Higher = cleaner."""
    if not reports:
        return 100
    active = sum(1 for r in reports if not r.get("archived") and not r.get("flagged"))
    total = len(reports)
    archived_ratio = (total - active) / max(total, 1)
    # Fewer active reports = cleaner
    score = max(0, 100 - (active * 10))
    # Bonus for resolved reports
    score += archived_ratio * 20
    return min(100, round(score, 1))
