"""Ranking Service — Percentile-based rank assignment, weekly recalculation."""
from datetime import datetime, timezone
import math

# Rank definitions (percentile thresholds, cumulative from top)
RANKS = [
    (1,   "Director General de la Cagada Nacional"),
    (3,   "Comisario Principal del Apocalipsis Canino"),
    (6,   "Comisario de Heces Urbanas"),
    (11,  "Inspector Jefe del Marrón"),
    (18,  "Inspector de Truños"),
    (28,  "Subinspector del Mojón"),
    (40,  "Oficial de Deposiciones"),
    (55,  "Policía de la Caca"),
    (75,  "Agente de Excrementos"),
    (100, "Aspirante Cagón"),
]


def get_rank_for_percentile(percentile: float) -> str:
    """Given a percentile (0–100, 100 = top), return the rank title."""
    inverse = 100 - percentile  # Convert to "top X%"
    for threshold, title in RANKS:
        if inverse <= threshold:
            return title
    return RANKS[-1][1]


async def recalculate_all_ranks(db):
    """Recalculate ranks for all users based on total_score percentiles."""
    users = await db.users.find(
        {"role": "user", "total_score": {"$exists": True}},
        {"_id": 1, "total_score": 1}
    ).sort("total_score", -1).to_list(100000)

    total = len(users)
    if total == 0:
        return 0

    from bson import ObjectId
    updates = []
    for i, user in enumerate(users):
        percentile = ((total - i) / total) * 100  # 100 = top, 0 = bottom
        rank = get_rank_for_percentile(percentile)
        level = max(1, math.ceil(percentile / 10))  # 1–10

        updates.append({
            "filter": {"_id": user["_id"]},
            "update": {"$set": {"rank": rank, "level": level, "rank_percentile": round(percentile, 1)}}
        })

    # Batch update
    from motor.motor_asyncio import AsyncIOMotorClient
    for u in updates:
        await db.users.update_one(u["filter"], u["update"])

    return total


async def get_user_rank_info(db, user_id: str) -> dict:
    """Get rank info for a specific user."""
    from bson import ObjectId
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return {}

    return {
        "total_score": user.get("total_score", 0),
        "rank": user.get("rank", "Aspirante Cagón"),
        "level": user.get("level", 1),
        "trust_score": user.get("trust_score", 50),
        "streak_days": user.get("streak_days", 0),
        "report_count": user.get("report_count", 0),
        "vote_count": user.get("vote_count", 0),
        "rank_percentile": user.get("rank_percentile", 0)
    }
