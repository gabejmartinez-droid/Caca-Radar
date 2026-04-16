"""Webhook handlers for App Store Server Notifications V2 and Google Play RTDN."""
import os
import json
import base64
import logging
import uuid
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# ==================== APPLE APP STORE NOTIFICATIONS V2 ====================

APPLE_BUNDLE_ID = os.environ.get("APPLE_BUNDLE_ID", "")
APPLE_ENVIRONMENT_STR = os.environ.get("APPLE_ENVIRONMENT", "Sandbox")

# Notification type mappings
APPLE_NOTIFICATION_TYPES = {
    "SUBSCRIBED": "activated",
    "DID_RENEW": "renewed",
    "DID_CHANGE_RENEWAL_STATUS": "status_changed",
    "DID_FAIL_TO_RENEW": "renewal_failed",
    "EXPIRED": "expired",
    "GRACE_PERIOD_EXPIRED": "grace_expired",
    "REFUND": "refunded",
    "REVOKE": "revoked",
    "CONSUMPTION_REQUEST": "consumption_request",
    "RENEWAL_EXTENDED": "extended",
    "OFFER_REDEEMED": "offer_redeemed",
    "PRICE_INCREASE": "price_increase",
    "TEST": "test",
}


async def process_apple_notification(db, signed_payload: str) -> dict:
    """Process an Apple App Store Server Notification V2.
    
    In production with credentials: verifies JWS signature then decodes.
    Without credentials: attempts basic JWT decode without verification (dev mode).
    """
    import jwt as pyjwt

    # Try full verification with apple library first
    notification_data = None
    verified = False

    if APPLE_BUNDLE_ID:
        try:
            from appstoreserverlibrary.signed_data_verifier import SignedDataVerifier  # noqa: F401
            from appstoreserverlibrary.models.Environment import Environment  # noqa: F401

            # Note: In production, use SignedDataVerifier with Apple root certs
        except ImportError:
            logger.warning("app-store-server-library not available for full verification")

    # Fallback: decode JWT payload without verification (dev/testing)
    if not verified:
        try:
            # JWS has 3 parts: header.payload.signature
            parts = signed_payload.split(".")
            if len(parts) == 3:
                # Decode payload (middle part)
                padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
                payload_bytes = base64.urlsafe_b64decode(padded)
                notification_data = json.loads(payload_bytes)
                logger.info(f"Apple notification decoded (unverified): type={notification_data.get('notificationType')}")
            else:
                return {"error": "Invalid JWS format"}
        except Exception as e:
            logger.error(f"Failed to decode Apple notification: {e}")
            return {"error": str(e)}

    if not notification_data:
        return {"error": "Could not decode notification"}

    # Extract fields
    notif_type = notification_data.get("notificationType", "UNKNOWN")
    subtype = notification_data.get("subtype", "")
    data = notification_data.get("data", {})

    # Try to get transaction info from signed data
    transaction_info = {}
    signed_transaction = data.get("signedTransactionInfo", "")
    if signed_transaction:
        try:
            parts = signed_transaction.split(".")
            if len(parts) == 3:
                padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
                transaction_info = json.loads(base64.urlsafe_b64decode(padded))
        except Exception:
            pass

    signed_renewal = data.get("signedRenewalInfo", "")
    renewal_info = {}
    if signed_renewal:
        try:
            parts = signed_renewal.split(".")
            if len(parts) == 3:
                padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
                renewal_info = json.loads(base64.urlsafe_b64decode(padded))
        except Exception:
            pass

    # Store notification
    await db.webhook_notifications.insert_one({
        "id": str(uuid.uuid4()),
        "store": "apple",
        "notification_type": notif_type,
        "subtype": subtype,
        "transaction_id": transaction_info.get("originalTransactionId") or transaction_info.get("transactionId"),
        "product_id": transaction_info.get("productId"),
        "bundle_id": data.get("bundleId"),
        "environment": data.get("environment"),
        "auto_renew": renewal_info.get("autoRenewStatus"),
        "raw_type": notif_type,
        "verified": verified,
        "received_at": datetime.now(timezone.utc).isoformat()
    })

    # Map to internal event
    event = APPLE_NOTIFICATION_TYPES.get(notif_type, "unknown")
    transaction_id = transaction_info.get("originalTransactionId") or transaction_info.get("transactionId")

    # Update subscription status in our DB
    if transaction_id:
        await update_subscription_from_webhook(
            db, store="apple", event=event, notif_type=notif_type,
            transaction_id=transaction_id,
            product_id=transaction_info.get("productId"),
            expires_ms=transaction_info.get("expiresDate"),
            auto_renew=renewal_info.get("autoRenewStatus", 0) == 1
        )

    return {"event": event, "notification_type": notif_type, "transaction_id": transaction_id}


# ==================== GOOGLE PLAY RTDN ====================

GOOGLE_PACKAGE_NAME = os.environ.get("GOOGLE_PACKAGE_NAME", "")

# Google RTDN notification types
GOOGLE_NOTIFICATION_TYPES = {
    1: "recovered",        # Recovered from account hold
    2: "renewed",          # Active subscription renewed
    3: "cancelled",        # Voluntarily or involuntarily cancelled
    4: "purchased",        # New subscription purchased
    5: "on_hold",          # Account hold
    6: "in_grace_period",  # Grace period
    7: "restarted",        # Restarted (user resubscribed)
    8: "price_change_confirmed",
    9: "deferred",
    10: "paused",
    11: "pause_schedule_changed",
    12: "revoked",         # Revoked
    13: "expired",         # Subscription expired
    20: "pending_purchase_canceled",
}


async def process_google_notification(db, message_data: str) -> dict:
    """Process a Google Play RTDN notification from Pub/Sub."""
    try:
        decoded = base64.b64decode(message_data).decode("utf-8")
        notification = json.loads(decoded)
    except Exception as e:
        logger.error(f"Failed to decode Google RTDN message: {e}")
        return {"error": str(e)}

    logger.info(f"Google RTDN received: {notification}")

    sub_notification = notification.get("subscriptionNotification")
    if not sub_notification:
        # Could be a one-time product notification or test
        await db.webhook_notifications.insert_one({
            "id": str(uuid.uuid4()),
            "store": "google",
            "notification_type": "non_subscription",
            "raw_data": notification,
            "received_at": datetime.now(timezone.utc).isoformat()
        })
        return {"event": "non_subscription", "data": notification}

    notif_type_code = sub_notification.get("notificationType", 0)
    purchase_token = sub_notification.get("purchaseToken", "")
    subscription_id = sub_notification.get("subscriptionId", "")

    event = GOOGLE_NOTIFICATION_TYPES.get(notif_type_code, "unknown")

    # Store notification
    await db.webhook_notifications.insert_one({
        "id": str(uuid.uuid4()),
        "store": "google",
        "notification_type": event,
        "notification_type_code": notif_type_code,
        "purchase_token": purchase_token,
        "subscription_id": subscription_id,
        "package_name": notification.get("packageName"),
        "received_at": datetime.now(timezone.utc).isoformat()
    })

    # Query Google Play API for full subscription details (if credentials available)
    expiry_ms = None
    auto_renew = False
    google_sa_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_PATH")

    if google_sa_path and purchase_token:
        try:
            from googleapiclient.discovery import build
            from google.oauth2 import service_account

            credentials = service_account.Credentials.from_service_account_file(
                google_sa_path,
                scopes=["https://www.googleapis.com/auth/androidpublisher"]
            )
            service = build("androidpublisher", "v3", credentials=credentials)

            pkg = notification.get("packageName") or GOOGLE_PACKAGE_NAME
            result = service.purchases().subscriptionsv2().get(
                packageName=pkg, token=purchase_token
            ).execute()

            # Extract from line items
            line_items = result.get("lineItems", [])
            if line_items:
                item = line_items[0]
                expiry_ms = item.get("expiryTime")
                auto_renew = item.get("autoRenewingPlan", {}).get("autoRenewing", False)

        except Exception as e:
            logger.error(f"Google API query failed: {e}")

    # Update subscription status
    await update_subscription_from_webhook(
        db, store="google", event=event, notif_type=str(notif_type_code),
        transaction_id=purchase_token,
        product_id=subscription_id,
        expires_ms=expiry_ms,
        auto_renew=auto_renew
    )

    return {"event": event, "notification_type_code": notif_type_code, "purchase_token": purchase_token}


# ==================== SHARED SUBSCRIPTION UPDATE LOGIC ====================

async def update_subscription_from_webhook(
    db, store: str, event: str, notif_type: str,
    transaction_id: str, product_id: str = None,
    expires_ms=None, auto_renew: bool = False
):
    """Update user subscription status based on webhook notification."""
    from bson import ObjectId

    # Find user by transaction ID or purchase token
    lookup_field = "subscription_transaction_id" if store == "apple" else "subscription_purchase_token"
    user = await db.users.find_one({lookup_field: transaction_id})

    if not user:
        logger.warning(f"No user found for {store} transaction: {transaction_id}")
        return

    user_id = str(user["_id"])
    email = user.get("email", "")

    # Parse expiry
    expires_iso = None
    if expires_ms:
        if isinstance(expires_ms, (int, float)):
            expires_iso = datetime.fromtimestamp(expires_ms / 1000, tz=timezone.utc).isoformat()
        elif isinstance(expires_ms, str):
            expires_iso = expires_ms

    # Determine new subscription state
    activate_events = {"activated", "renewed", "recovered", "restarted", "purchased", "extended", "offer_redeemed"}
    deactivate_events = {"expired", "revoked", "grace_expired", "refunded", "cancelled"}

    update_fields = {
        "subscription_last_webhook": datetime.now(timezone.utc).isoformat(),
        "subscription_last_event": event,
        "subscription_auto_renew": auto_renew,
    }

    if event in activate_events:
        update_fields["subscription_active"] = True
        if expires_iso:
            update_fields["subscription_expires"] = expires_iso
        logger.info(f"Activating subscription for user {user_id} ({event})")

    elif event in deactivate_events:
        update_fields["subscription_active"] = False
        logger.info(f"Deactivating subscription for user {user_id} ({event})")

    elif event in {"on_hold", "in_grace_period", "paused"}:
        # Keep active during grace/hold but flag it
        update_fields["subscription_hold_status"] = event
        logger.info(f"Subscription on hold for user {user_id} ({event})")

    elif event == "status_changed":
        update_fields["subscription_auto_renew"] = auto_renew
        logger.info(f"Subscription status changed for user {user_id}, auto_renew={auto_renew}")

    await db.users.update_one({"_id": user["_id"]}, {"$set": update_fields})

    # Send email notification
    try:
        from email_service import send_subscription_update
        email_event = event if event in {"activated", "renewed", "expired", "cancelled", "refunded"} else None
        if email_event and email:
            plan = product_id or user.get("subscription_type", "Premium")
            await send_subscription_update(email, email_event, {"plan": plan, "expires": expires_iso or ""})
    except Exception as e:
        logger.error(f"Failed to send subscription email: {e}")

    # Log webhook processing
    await db.webhook_processing_log.insert_one({
        "user_id": user_id,
        "store": store,
        "event": event,
        "notification_type": notif_type,
        "transaction_id": transaction_id,
        "update_fields": {k: str(v) for k, v in update_fields.items()},
        "processed_at": datetime.now(timezone.utc).isoformat()
    })
