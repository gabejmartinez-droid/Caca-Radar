"""Ranking Service — Percentile-based rank assignment, weekly recalculation."""
import math
from rank_metadata import DEFAULT_RANK_NAME, get_rank_for_percentile, get_rank_key


async def recalculate_all_ranks(db):
    """Recalculate ranks for all users based on total_score percentiles.
    Returns (count, rank_changes) where rank_changes is a list of {user_id, old_rank, new_rank}."""
    users = await db.users.find(
        {"role": "user", "total_score": {"$exists": True}},
        {"_id": 1, "total_score": 1, "rank": 1}
    ).sort("total_score", -1).to_list(100000)

    total = len(users)
    if total == 0:
        return 0, []

    from bson import ObjectId
    updates = []
    rank_changes = []
    for i, user in enumerate(users):
        percentile = ((total - i) / total) * 100  # 100 = top, 0 = bottom
        rank = get_rank_for_percentile(percentile)
        level = max(1, math.ceil(percentile / 10))  # 1–10

        old_rank = user.get("rank", DEFAULT_RANK_NAME)
        if old_rank != rank:
            rank_changes.append({
                "user_id": str(user["_id"]),
                "old_rank": old_rank,
                "new_rank": rank,
                "old_rank_key": get_rank_key(old_rank),
                "new_rank_key": get_rank_key(rank),
            })

        updates.append({
            "filter": {"_id": user["_id"]},
            "update": {"$set": {"rank": rank, "rank_key": get_rank_key(rank), "level": level, "rank_percentile": round(percentile, 1)}}
        })

    # Batch update
    from motor.motor_asyncio import AsyncIOMotorClient
    for u in updates:
        await db.users.update_one(u["filter"], u["update"])

    return total, rank_changes


async def get_user_rank_info(db, user_id: str) -> dict:
    """Get rank info for a specific user."""
    from bson import ObjectId
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return {}

    return {
        "total_score": user.get("total_score", 0),
        "rank": user.get("rank", DEFAULT_RANK_NAME),
        "rank_key": user.get("rank_key", get_rank_key(user.get("rank", DEFAULT_RANK_NAME))),
        "level": user.get("level", 1),
        "trust_score": user.get("trust_score", 50),
        "streak_days": user.get("streak_days", 0),
        "report_count": user.get("report_count", 0),
        "vote_count": user.get("vote_count", 0),
        "rank_percentile": user.get("rank_percentile", 0)
    }
