"""Push Notification Service — Web Push for nearby report alerts."""
import os
import json
import logging
from pywebpush import webpush, WebPushException
from antispam_service import haversine_meters

logger = logging.getLogger(__name__)

VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_CLAIMS_EMAIL = os.environ.get("VAPID_CLAIMS_EMAIL", "mailto:no-reply@cacaradar.es")

NEARBY_RADIUS_METERS = 500  # Notify users within 500m


def is_configured() -> bool:
    return bool(VAPID_PRIVATE_KEY and VAPID_PUBLIC_KEY)


async def send_push(subscription_info: dict, title: str, body: str, url: str = "/") -> bool:
    """Send a push notification to a single subscription."""
    if not is_configured():
        logger.warning(f"[PUSH MOCK] {title}: {body}")
        return False

    payload = json.dumps({"title": title, "body": body, "url": url, "icon": "/icon-192.png", "badge": "/icon-192.png"})

    try:
        webpush(
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_CLAIMS_EMAIL}
        )
        return True
    except WebPushException as e:
        logger.error(f"Push failed: {e}")
        if e.response and e.response.status_code in (404, 410):
            return False  # Subscription expired — caller should remove it
        return False
    except Exception as e:
        logger.error(f"Push error: {e}")
        return False


async def notify_nearby_users(db, report_lat: float, report_lon: float, report_id: str, municipality: str):
    """Send push notifications to users subscribed to alerts near a new report."""
    # Find active push subscriptions
    subs = await db.push_subscriptions.find(
        {"active": True, "latitude": {"$exists": True}},
        {"_id": 0}
    ).to_list(1000)

    sent_count = 0
    expired = []

    for sub in subs:
        sub_lat = sub.get("latitude", 0)
        sub_lon = sub.get("longitude", 0)
        dist = haversine_meters(report_lat, report_lon, sub_lat, sub_lon)

        if dist <= NEARBY_RADIUS_METERS:
            dist_text = f"{int(dist)}m" if dist < 1000 else f"{dist/1000:.1f}km"
            success = await send_push(
                subscription_info=sub.get("subscription"),
                title=f"Nuevo reporte a {dist_text}",
                body=f"Nuevo reporte de caca en {municipality}",
                url=f"/?report={report_id}"
            )
            if success:
                sent_count += 1
            elif not success and is_configured():
                expired.append(sub.get("id"))

    # Remove expired subscriptions
    if expired:
        await db.push_subscriptions.update_many(
            {"id": {"$in": expired}},
            {"$set": {"active": False}}
        )

    logger.info(f"Push notifications sent to {sent_count} nearby users for report {report_id}")
    return sent_count
