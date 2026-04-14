"""Email Service — Send transactional emails via Resend."""
import os
import asyncio
import logging
import resend

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "no-reply@cacaradar.es")


def is_configured() -> bool:
    """Check if Resend is configured with a valid API key."""
    return bool(RESEND_API_KEY and RESEND_API_KEY.startswith("re_"))


def _init():
    if is_configured():
        resend.api_key = RESEND_API_KEY


async def send_email(to: str, subject: str, html: str) -> dict:
    """Send an email via Resend. Falls back to logging if not configured."""
    if not is_configured():
        logger.warning(f"[EMAIL MOCK] To: {to} | Subject: {subject}")
        logger.warning(f"[EMAIL MOCK] Body preview: {html[:200]}")
        return {"status": "mock", "to": to, "subject": subject}

    _init()
    params = {
        "from": SENDER_EMAIL,
        "to": [to],
        "subject": subject,
        "html": html,
    }

    try:
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Email sent to {to}: {result.get('id', 'unknown')}")
        return {"status": "sent", "email_id": result.get("id"), "to": to}
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return {"status": "error", "error": str(e), "to": to}


async def send_verification_code(to: str, code: str, municipality_name: str) -> dict:
    """Send a municipality verification code email."""
    subject = f"Caca Radar — Código de verificación para {municipality_name}"
    html = f"""
    <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px;">
      <div style="text-align: center; margin-bottom: 24px;">
        <div style="display: inline-block; background: #FF6B6B; color: white; width: 48px; height: 48px; border-radius: 50%; line-height: 48px; font-size: 24px;">&#128205;</div>
        <h1 style="color: #2B2D42; font-size: 24px; margin: 12px 0 4px;">Caca Radar</h1>
        <p style="color: #8D99AE; font-size: 14px; margin: 0;">Panel de Ayuntamiento</p>
      </div>

      <div style="background: #F8F9FA; border-radius: 16px; padding: 24px; text-align: center; margin-bottom: 24px;">
        <p style="color: #2B2D42; font-size: 16px; margin: 0 0 8px;">Tu código de verificación para</p>
        <p style="color: #2B2D42; font-size: 18px; font-weight: 700; margin: 0 0 16px;">{municipality_name}</p>
        <div style="background: white; border-radius: 12px; padding: 16px; display: inline-block; border: 2px solid #FF6B6B;">
          <span style="font-size: 32px; font-weight: 900; letter-spacing: 8px; color: #2B2D42;">{code}</span>
        </div>
      </div>

      <p style="color: #8D99AE; font-size: 13px; text-align: center; line-height: 1.5;">
        Este código expira en 1 hora.<br>
        Si no has solicitado este código, ignora este email.
      </p>

      <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
      <p style="color: #8D99AE; font-size: 11px; text-align: center;">
        Caca Radar — Manteniendo las calles de España limpias
      </p>
    </div>
    """
    return await send_email(to, subject, html)


async def send_subscription_update(to: str, event_type: str, details: dict) -> dict:
    """Send a subscription status update email."""
    event_labels = {
        "activated": "Suscripción Activada",
        "renewed": "Suscripción Renovada",
        "expired": "Suscripción Expirada",
        "cancelled": "Suscripción Cancelada",
        "refunded": "Reembolso Procesado",
    }
    label = event_labels.get(event_type, event_type)
    plan = details.get("plan", "Premium")
    expires = details.get("expires", "")

    subject = f"Caca Radar — {label}"
    html = f"""
    <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px;">
      <div style="text-align: center; margin-bottom: 24px;">
        <h1 style="color: #2B2D42; font-size: 24px;">Caca Radar</h1>
      </div>
      <div style="background: #F8F9FA; border-radius: 16px; padding: 24px; margin-bottom: 24px;">
        <h2 style="color: #2B2D42; font-size: 18px; margin: 0 0 12px;">{label}</h2>
        <p style="color: #8D99AE; font-size: 14px; margin: 4px 0;">Plan: <strong>{plan}</strong></p>
        {"<p style='color: #8D99AE; font-size: 14px; margin: 4px 0;'>Válido hasta: <strong>" + expires + "</strong></p>" if expires else ""}
      </div>
      <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
      <p style="color: #8D99AE; font-size: 11px; text-align: center;">Caca Radar</p>
    </div>
    """
    return await send_email(to, subject, html)
