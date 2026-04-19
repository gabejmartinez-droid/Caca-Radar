"""Scoring Service — Points calculation, streak bonuses, subscriber multiplier."""
from datetime import datetime, timezone, timedelta
import math

# Scoring constants
REPORT_BASE_POINTS = 10
REPORT_PHOTO_BONUS = 5
REPORT_DESCRIPTION_BONUS = 3
MAX_SCORING_REPORTS_PER_DAY = 5

VALIDATION_CORRECT = 4
VALIDATION_INCORRECT = -3
VALIDATION_EARLY_BONUS = 5  # First 5 validators
EARLY_VALIDATOR_THRESHOLD = 5

UPVOTE_POINTS = 2
DOWNVOTE_POINTS = -2

REPORT_VERIFIED_BONUS = 5

SUBSCRIBER_MULTIPLIER = 1.5
SUBSCRIBER_MAX_BONUS_CAP = 50  # Max bonus points from multiplier per action

STREAK_BONUSES = {7: 15, 14: 30, 30: 50}

HOT_ZONE_BONUS = 5
HOT_ZONE_THRESHOLD = 10  # Reports in area within 7 days


def calc_report_points(has_photo: bool, has_description: bool, daily_count: int, is_subscriber: bool) -> dict:
    """Calculate points for submitting a report."""
    if daily_count >= MAX_SCORING_REPORTS_PER_DAY:
        return {"points": 0, "breakdown": {"reason": "daily_limit_reached"}}

    base = REPORT_BASE_POINTS
    photo = REPORT_PHOTO_BONUS if has_photo else 0
    desc = REPORT_DESCRIPTION_BONUS if has_description else 0
    raw = base + photo + desc

    bonus = 0
    if is_subscriber:
        bonus = min(int(raw * (SUBSCRIBER_MULTIPLIER - 1)), SUBSCRIBER_MAX_BONUS_CAP)

    total = raw + bonus
    return {
        "points": total,
        "breakdown": {"base": base, "photo": photo, "description": desc, "subscriber_bonus": bonus}
    }


def calc_validation_points(is_correct: bool, validator_index: int, is_subscriber: bool) -> dict:
    """Calculate points for validating a report."""
    raw = VALIDATION_CORRECT if is_correct else VALIDATION_INCORRECT
    early = VALIDATION_EARLY_BONUS if is_correct and validator_index < EARLY_VALIDATOR_THRESHOLD else 0
    subtotal = raw + early

    bonus = 0
    if is_subscriber and subtotal > 0:
        bonus = min(int(subtotal * (SUBSCRIBER_MULTIPLIER - 1)), SUBSCRIBER_MAX_BONUS_CAP)

    total = subtotal + bonus
    return {
        "points": total,
        "breakdown": {"base": raw, "early_bonus": early, "subscriber_bonus": bonus}
    }


def calc_vote_points(vote_type: str) -> int:
    return UPVOTE_POINTS if vote_type == "upvote" else DOWNVOTE_POINTS


def calc_streak_bonus(streak_days: int) -> int:
    """Return bonus for reaching a streak milestone (only on exact day)."""
    return STREAK_BONUSES.get(streak_days, 0)


def calc_verified_bonus(is_subscriber: bool) -> int:
    raw = REPORT_VERIFIED_BONUS
    bonus = min(int(raw * (SUBSCRIBER_MULTIPLIER - 1)), SUBSCRIBER_MAX_BONUS_CAP) if is_subscriber else 0
    return raw + bonus


async def update_streak(db, user_id: str):
    """Update user's daily streak. Returns new streak count."""
    from bson import ObjectId
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return 0

    today = datetime.now(timezone.utc).date()
    last_active = user.get("last_active_date")

    if last_active:
        if isinstance(last_active, str):
            last_active = datetime.fromisoformat(last_active).date()
        elif isinstance(last_active, datetime):
            last_active = last_active.date()

    if last_active == today:
        return user.get("streak_days", 0)

    if last_active and (today - last_active).days == 1:
        new_streak = user.get("streak_days", 0) + 1
    else:
        new_streak = 1

    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"streak_days": new_streak, "last_active_date": today.isoformat()}}
    )

    # Award streak bonus
    bonus = calc_streak_bonus(new_streak)
    if bonus > 0:
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"total_score": bonus}}
        )

    return new_streak


async def reset_daily_counts(db):
    """Reset daily report counts for all users. Call at midnight or on startup."""
    today = datetime.now(timezone.utc).date().isoformat()
    await db.users.update_many(
        {"daily_reset_date": {"$ne": today}},
        {"$set": {"daily_report_count": 0, "daily_reset_date": today}}
    )
