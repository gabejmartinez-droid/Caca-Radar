"""Push Notification Service — Web Push + Native (FCM/APNs) for nearby report alerts."""
import os
import json
import time
import logging
from functools import lru_cache

import httpx
import jwt
from pywebpush import webpush, WebPushException
from antispam_service import haversine_meters

logger = logging.getLogger(__name__)

VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_CLAIMS_EMAIL = os.environ.get("VAPID_CLAIMS_EMAIL", "mailto:no-reply@cacaradar.es")

# FCM for native Capacitor push (optional)
FCM_SERVER_KEY = os.environ.get("FCM_SERVER_KEY", "")

# APNs for native iOS push (optional)
APPLE_TEAM_ID = os.environ.get("APPLE_TEAM_ID", "")
APPLE_KEY_ID = os.environ.get("APPLE_KEY_ID", "")
APPLE_BUNDLE_ID = os.environ.get("APPLE_BUNDLE_ID", "")
APPLE_KEY_PATH = os.environ.get("APPLE_KEY_PATH", "")
APPLE_PUSH_ENVIRONMENT = os.environ.get("APPLE_PUSH_ENVIRONMENT", "production").lower()

NEARBY_RADIUS_METERS = 500  # Notify users within 500m


def is_configured() -> bool:
    return bool(VAPID_PRIVATE_KEY and VAPID_PUBLIC_KEY)


def is_apns_configured() -> bool:
    return bool(APPLE_TEAM_ID and APPLE_KEY_ID and APPLE_BUNDLE_ID and APPLE_KEY_PATH)


def is_native_subscription(subscription: dict) -> bool:
    """Check if this is a native (FCM) push subscription vs Web Push."""
    return subscription.get("platform") == "native" or "token" in subscription


def get_native_platform(subscription: dict) -> str:
    platform = str(subscription.get("platform") or "").lower()
    if platform in {"ios", "android"}:
        return platform
    token = str(subscription.get("token") or "")
    # APNs device tokens are hex strings; FCM tokens are not.
    if token and all(ch in "0123456789abcdefABCDEF" for ch in token) and len(token) >= 64:
        return "ios"
    return "android"


@lru_cache(maxsize=1)
def _read_apns_key() -> str:
    if not APPLE_KEY_PATH:
        return ""
    with open(APPLE_KEY_PATH, "r", encoding="utf-8") as handle:
        return handle.read()


def _get_apns_host() -> str:
    if APPLE_PUSH_ENVIRONMENT in {"sandbox", "development", "dev"}:
        return "https://api.sandbox.push.apple.com"
    return "https://api.push.apple.com"


def _build_apns_jwt() -> str:
    issued_at = int(time.time())
    return jwt.encode(
        {"iss": APPLE_TEAM_ID, "iat": issued_at},
        _read_apns_key(),
        algorithm="ES256",
        headers={"alg": "ES256", "kid": APPLE_KEY_ID},
    )


async def send_web_push(subscription_info: dict, title: str, body: str, url: str = "/") -> bool:
    """Send a Web Push notification."""
    if not is_configured():
        logger.warning(f"[PUSH MOCK] Web: {title}: {body}")
        return False

    payload = json.dumps({
        "title": title, "body": body, "url": url,
        "icon": "/icon-192.png", "badge": "/icon-192.png",
        "tag": "caca-radar-nearby"
    })

    try:
        webpush(
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_CLAIMS_EMAIL}
        )
        return True
    except WebPushException as e:
        logger.error(f"Web push failed: {e}")
        if e.response and e.response.status_code in (404, 410):
            return False
        return False
    except Exception as e:
        logger.error(f"Web push error: {e}")
        return False


async def send_android_push(token: str, title: str, body: str, url: str = "/") -> bool:
    """Send an Android native push notification via FCM."""
    if not FCM_SERVER_KEY:
        logger.warning(f"[PUSH MOCK] Android native: {title}: {body}")
        return False
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://fcm.googleapis.com/fcm/send",
                headers={
                    "Authorization": f"key={FCM_SERVER_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "to": token,
                    "notification": {"title": title, "body": body},
                    "data": {"url": url, "title": title, "body": body},
                },
                timeout=10,
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("success", 0) > 0
            logger.error(f"FCM response {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Android native push error: {e}")
        return False


async def send_ios_push(token: str, title: str, body: str, url: str = "/") -> bool:
    """Send an iOS native push notification via APNs."""
    if not is_apns_configured():
        logger.warning(f"[PUSH MOCK] iOS native: {title}: {body}")
        return False

    payload = {
        "aps": {
            "alert": {"title": title, "body": body},
            "sound": "default",
        },
        "url": url,
        "title": title,
        "body": body,
    }
    endpoint = f"{_get_apns_host()}/3/device/{token}"
    headers = {
        "authorization": f"bearer {_build_apns_jwt()}",
        "apns-topic": APPLE_BUNDLE_ID,
        "apns-push-type": "alert",
        "apns-priority": "10",
    }
    try:
        async with httpx.AsyncClient(http2=True) as client:
            response = await client.post(endpoint, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            return True
        logger.error(f"APNs response {response.status_code}: {response.text}")
        return False
    except Exception as e:
        logger.error(f"iOS native push error: {e}")
        return False


async def send_push(subscription_info: dict, title: str, body: str, url: str = "/") -> bool:
    """Route to web or native push based on subscription type."""
    if is_native_subscription(subscription_info):
        token = subscription_info.get("token", "")
        platform = get_native_platform(subscription_info)
        if platform == "ios":
            return await send_ios_push(token, title, body, url)
        return await send_android_push(token, title, body, url)
    return await send_web_push(subscription_info, title, body, url)


async def notify_nearby_users(db, report_lat: float, report_lon: float, report_id: str, municipality: str):
    """Send push notifications to users subscribed to alerts near a new report."""
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
            elif not success and (is_configured() or FCM_SERVER_KEY or is_apns_configured()):
                expired.append(sub.get("user_id"))

    # Deactivate expired subscriptions
    if expired:
        await db.push_subscriptions.update_many(
            {"user_id": {"$in": expired}},
            {"$set": {"active": False}}
        )

    logger.info(f"Push notifications sent to {sent_count}/{len(subs)} nearby users for report {report_id}")
    return sent_count
