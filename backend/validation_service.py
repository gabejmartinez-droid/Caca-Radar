"""Validation Service — Consensus logic, report verification/rejection, weighted votes."""
import uuid
from datetime import datetime, timezone
from bson import ObjectId
from antispam_service import get_validation_weight, update_trust_score, TRUST_CORRECT_VALIDATION, TRUST_VERIFIED_REPORT, TRUST_FALSE_REPORT
from scoring_service import calc_validation_points, calc_verified_bonus

CONFIRMATIONS_NEEDED = 3
NET_VOTE_THRESHOLD = 0  # Positive net score needed


async def process_validation(db, report_id: str, user_id: str, vote: str, is_subscriber: bool):
    """Process a validation vote and check if report reaches consensus."""

    report = await db.reports.find_one({"id": report_id})
    if not report:
        return {"error": "Report not found"}

    # Get validator's trust score for weighting
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        user = None
    trust = user.get("trust_score", 50) if user else 50
    weight = get_validation_weight(trust)

    # Subscriber gets a small boost (not pay-to-win)
    if is_subscriber:
        weight = min(weight * 1.1, 2.0)

    # Count existing validations
    validation_count = await db.validations.count_documents({"report_id": report_id})

    # Store validation
    validation_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "report_id": report_id,
        "vote": vote,
        "weight": weight,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.validations.insert_one(validation_doc)

    # Update report counts
    if vote == "confirm":
        await db.reports.update_one({"id": report_id}, {"$inc": {"validation_count": 1, "upvotes": 1}})
    else:
        await db.reports.update_one({"id": report_id}, {"$inc": {"downvotes": 1}})

    # Increment user's vote_count
    if user:
        await db.users.update_one({"_id": ObjectId(user_id)}, {"$inc": {"vote_count": 1}})

    # Check consensus
    updated = await db.reports.find_one({"id": report_id})
    result = await check_consensus(db, updated, validation_count)

    return {"validation_recorded": True, "validator_index": validation_count, "consensus": result}


async def check_consensus(db, report: dict, validator_count: int) -> dict:
    """Check if a report has reached consensus for verification or rejection."""

    report_id = report["id"]
    upvotes = report.get("upvotes", 0)
    downvotes = report.get("downvotes", 0)
    net_score = upvotes - downvotes
    current_status = report.get("status", "pending")

    if current_status != "pending":
        return {"status": current_status, "changed": False}

    # Get weighted votes
    validations = await db.validations.find({"report_id": report_id}).to_list(100)
    weighted_confirm = sum(v.get("weight", 1.0) for v in validations if v["vote"] == "confirm")
    weighted_reject = sum(v.get("weight", 1.0) for v in validations if v["vote"] == "reject")

    # Verification: 3+ confirmations AND positive net score
    if weighted_confirm >= CONFIRMATIONS_NEEDED and net_score > NET_VOTE_THRESHOLD:
        await db.reports.update_one({"id": report_id}, {"$set": {"status": "verified"}})

        # Reward reporter
        reporter_id = report.get("user_id", "")
        try:
            reporter = await db.users.find_one({"_id": ObjectId(reporter_id)})
        except Exception:
            reporter = None

        if reporter:
            is_sub = reporter.get("subscription_active", False)
            bonus = calc_verified_bonus(is_sub)
            await db.users.update_one(
                {"_id": ObjectId(reporter_id)},
                {"$inc": {"total_score": bonus}}
            )
            await update_trust_score(db, reporter_id, TRUST_VERIFIED_REPORT, "report_verified")

        # Reward correct validators
        await reward_validators(db, report_id, "confirm")

        return {"status": "verified", "changed": True}

    # Rejection: more weighted rejections than confirmations AND enough total votes
    total_validations = len(validations)
    if total_validations >= CONFIRMATIONS_NEEDED and weighted_reject > weighted_confirm:
        await db.reports.update_one({"id": report_id}, {"$set": {"status": "rejected"}})

        # Penalize reporter
        reporter_id = report.get("user_id", "")
        try:
            reporter = await db.users.find_one({"_id": ObjectId(reporter_id)})
        except Exception:
            reporter = None
        if reporter:
            await update_trust_score(db, reporter_id, TRUST_FALSE_REPORT, "report_rejected")

        # Reward correct validators
        await reward_validators(db, report_id, "reject")

        return {"status": "rejected", "changed": True}

    return {"status": "pending", "changed": False}


async def reward_validators(db, report_id: str, winning_vote: str):
    """Reward validators who voted with consensus, penalize those against."""

    validations = await db.validations.find({"report_id": report_id}).to_list(100)

    for i, v in enumerate(validations):
        uid = v["user_id"]
        try:
            user = await db.users.find_one({"_id": ObjectId(uid)})
        except Exception:
            user = None

        is_correct = v["vote"] == winning_vote
        is_sub = user.get("subscription_active", False) if user else False
        result = calc_validation_points(is_correct, i, is_sub)

        if user:
            await db.users.update_one(
                {"_id": ObjectId(uid)},
                {"$inc": {"total_score": result["points"]}}
            )
            if is_correct:
                await update_trust_score(db, uid, TRUST_CORRECT_VALIDATION, "correct_validation")
