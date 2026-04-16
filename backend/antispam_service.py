"""Anti-Spam Service — Trust score, cooldowns, proximity checks, rate limits."""
from datetime import datetime, timezone, timedelta
import math

# Trust score constants
TRUST_DEFAULT = 50
TRUST_MIN = 0
TRUST_MAX = 100

TRUST_CORRECT_VALIDATION = 2
TRUST_VERIFIED_REPORT = 3
TRUST_UPVOTED_REPORT_MIN = 1
TRUST_UPVOTED_REPORT_MAX = 5
TRUST_DOWNVOTED_REPORT = -5
TRUST_FALSE_REPORT = -10
TRUST_SPAM_BEHAVIOR = -15

# Rate limits
COOLDOWN_SECONDS = 30
MAX_REPORTS_PER_DAY = 5
PROXIMITY_METERS = 1
GPS_ACCURACY_METERS = 30

# Trust tiers
TIER_TRUSTED = 80       # Auto-visible, higher weight
TIER_NORMAL_MIN = 50
TIER_LOW_MIN = 20
TIER_RESTRICTED = 0     # Rate-limited or hidden


def get_trust_tier(trust_score: int) -> str:
    if trust_score >= TIER_TRUSTED:
        return "trusted"
    elif trust_score >= TIER_NORMAL_MIN:
        return "normal"
    elif trust_score >= TIER_LOW_MIN:
        return "low"
    else:
        return "restricted"


def get_validation_weight(trust_score: int) -> float:
    """Higher trust = stronger vote weight."""
    if trust_score >= 80:
        return 1.5
    elif trust_score >= 50:
        return 1.0
    elif trust_score >= 20:
        return 0.7
    else:
        return 0.3


def clamp_trust(score: int) -> int:
    return max(TRUST_MIN, min(TRUST_MAX, score))


def haversine_meters(lat1, lon1, lat2, lon2) -> float:
    """Calculate distance between two GPS coordinates in meters."""
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def check_cooldown(db, user_id: str) -> bool:
    """Return True if user is within cooldown period."""
    last_report = await db.reports.find_one(
        {"user_id": user_id},
        sort=[("created_at", -1)]
    )
    if not last_report:
        return False

    created = last_report.get("created_at", "")
    if isinstance(created, str):
        created = datetime.fromisoformat(created)
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)

    diff = (datetime.now(timezone.utc) - created).total_seconds()
    return diff < COOLDOWN_SECONDS


async def check_proximity_duplicate(db, lat: float, lon: float, exclude_id: str = None):
    """Check if there's an active report within PROXIMITY_METERS.
    Returns the nearby report dict if found, None otherwise."""
    recent_cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    query = {
        "archived": {"$ne": True},
        "flagged": {"$ne": True},
        "created_at": {"$gte": recent_cutoff}
    }
    if exclude_id:
        query["id"] = {"$ne": exclude_id}

    nearby_reports = await db.reports.find(query, {"_id": 0, "id": 1, "latitude": 1, "longitude": 1}).to_list(500)

    for r in nearby_reports:
        dist = haversine_meters(lat, lon, r["latitude"], r["longitude"])
        if dist < PROXIMITY_METERS:
            return r
    return None


async def check_gps_plausible(lat: float, lon: float) -> bool:
    """Basic check that GPS is within Spain bounding box."""
    # Spain approx bounding box (including Canary Islands)
    return 27.0 <= lat <= 44.0 and -19.0 <= lon <= 5.0


async def update_trust_score(db, user_id: str, delta: int, reason: str):
    """Adjust user's trust score and log the change."""
    from bson import ObjectId
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return

    current = user.get("trust_score", TRUST_DEFAULT)
    new_score = clamp_trust(current + delta)

    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"trust_score": new_score}}
    )

    # Log trust change
    await db.trust_log.insert_one({
        "user_id": user_id,
        "delta": delta,
        "old_score": current,
        "new_score": new_score,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


async def detect_spam_patterns(db, user_id: str) -> list:
    """Detect spam patterns and return list of violations."""
    violations = []
    one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

    # Check rapid posting (more than 10 reports in 1 hour)
    recent_count = await db.reports.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": one_hour_ago}
    })
    if recent_count > 10:
        violations.append("rapid_posting")

    # Check same-location spam
    recent_reports = await db.reports.find(
        {"user_id": user_id, "created_at": {"$gte": one_hour_ago}},
        {"_id": 0, "latitude": 1, "longitude": 1}
    ).to_list(20)

    if len(recent_reports) >= 3:
        # Check if multiple reports cluster at same spot
        for i in range(len(recent_reports)):
            cluster = 1
            for j in range(i + 1, len(recent_reports)):
                dist = haversine_meters(
                    recent_reports[i]["latitude"], recent_reports[i]["longitude"],
                    recent_reports[j]["latitude"], recent_reports[j]["longitude"]
                )
                if dist < 20:  # 20 meters
                    cluster += 1
            if cluster >= 3:
                violations.append("location_cluster_spam")
                break

    return violations


async def is_hot_zone(db, lat: float, lon: float) -> bool:
    """Check if location is a hot zone (high-activity area)."""
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    nearby = await db.reports.find(
        {"created_at": {"$gte": week_ago}, "archived": {"$ne": True}},
        {"_id": 0, "latitude": 1, "longitude": 1}
    ).to_list(500)

    count = 0
    for r in nearby:
        if haversine_meters(lat, lon, r["latitude"], r["longitude"]) < 200:  # 200m radius
            count += 1
    return count >= 10  # 10+ reports = hot zone
