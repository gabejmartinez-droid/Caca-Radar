"""Email Service — Send transactional emails via Resend."""
import os
import asyncio
import logging
from html import escape
import resend

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "no-reply@cacaradar.es")
ADMIN_NOTIFICATION_EMAIL = os.environ.get("ADMIN_NOTIFICATION_EMAIL") or os.environ.get("ADMIN_EMAIL", "jefe@cacaradar.es")


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
    dashboard_url = os.environ.get("FRONTEND_URL", "https://cacaradar.es") + "/dashboard/login"
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

      <div style="background: #2B2D42; border-radius: 16px; padding: 20px; text-align: center; margin-bottom: 24px;">
        <p style="color: white; font-size: 14px; margin: 0 0 12px;">Una vez verificado, accede a tu panel en:</p>
        <a href="{dashboard_url}" style="color: #FF6B6B; font-size: 16px; font-weight: 700; text-decoration: none;">{dashboard_url}</a>
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


async def send_municipality_admin_notification(details: dict, event_type: str = "created") -> dict:
    """Notify the admin when a municipality account/subscription needs setup."""
    event_labels = {
        "registered": "Nueva solicitud municipal",
        "created": "Nueva suscripción municipal",
        "activated": "Suscripción municipal activada",
    }
    label = event_labels.get(event_type, "Actividad municipal")
    municipality_name = escape(str(details.get("municipality_name") or "Sin municipio"))
    province = escape(str(details.get("province") or details.get("municipality_province") or ""))
    contact_name = escape(str(details.get("name") or details.get("contact_name") or ""))
    email = escape(str(details.get("email") or ""))
    tier = escape(str(details.get("tier") or details.get("plan") or "Pendiente"))
    product_id = escape(str(details.get("product_id") or "Pendiente"))
    price = escape(str(details.get("price") or "Pendiente"))
    expires = escape(str(details.get("expires") or ""))
    created_at = escape(str(details.get("created_at") or ""))
    admin_url = os.environ.get("FRONTEND_URL", "https://cacaradar.es").rstrip("/") + "/admin"

    subject = f"Caca Radar — {label}: {municipality_name}"
    html = f"""
    <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 32px;">
      <div style="margin-bottom: 24px;">
        <h1 style="color: #2B2D42; font-size: 24px; margin: 0 0 6px;">{label}</h1>
        <p style="color: #8D99AE; font-size: 14px; margin: 0;">Caca Radar municipal dashboard setup needed</p>
      </div>

      <div style="background: #F8F9FA; border-radius: 16px; padding: 20px; margin-bottom: 20px;">
        <p style="color: #2B2D42; font-size: 14px; margin: 6px 0;"><strong>Municipio:</strong> {municipality_name}</p>
        <p style="color: #2B2D42; font-size: 14px; margin: 6px 0;"><strong>Provincia:</strong> {province}</p>
        <p style="color: #2B2D42; font-size: 14px; margin: 6px 0;"><strong>Contacto:</strong> {contact_name}</p>
        <p style="color: #2B2D42; font-size: 14px; margin: 6px 0;"><strong>Email:</strong> {email}</p>
        <p style="color: #2B2D42; font-size: 14px; margin: 6px 0;"><strong>Plan:</strong> {tier}</p>
        <p style="color: #2B2D42; font-size: 14px; margin: 6px 0;"><strong>Product ID:</strong> {product_id}</p>
        <p style="color: #2B2D42; font-size: 14px; margin: 6px 0;"><strong>Precio:</strong> {price}</p>
        {"<p style='color: #2B2D42; font-size: 14px; margin: 6px 0;'><strong>Caduca:</strong> " + expires + "</p>" if expires else ""}
        {"<p style='color: #8D99AE; font-size: 12px; margin: 12px 0 0;'><strong>Creado:</strong> " + created_at + "</p>" if created_at else ""}
      </div>

      <div style="background: #2B2D42; border-radius: 16px; padding: 18px; text-align: center;">
        <p style="color: white; font-size: 14px; margin: 0 0 10px;">Next step: configure or verify the custom municipal dashboard.</p>
        <a href="{admin_url}" style="color: #FF6B6B; font-size: 15px; font-weight: 700; text-decoration: none;">Open admin dashboard</a>
      </div>
    </div>
    """
    return await send_email(ADMIN_NOTIFICATION_EMAIL, subject, html)


async def send_admin_verification_code(to: str, code: str) -> dict:
    """Send an admin 2FA verification code email."""
    subject = "Caca Radar — Código de acceso Admin"
    html = f"""
    <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px;">
      <div style="text-align: center; margin-bottom: 24px;">
        <h1 style="color: #2B2D42; font-size: 24px; margin: 12px 0 4px;">Caca Radar</h1>
        <p style="color: #FF6B6B; font-size: 14px; font-weight: 700; margin: 0;">Panel de Administración</p>
      </div>

      <div style="background: #2B2D42; border-radius: 16px; padding: 24px; text-align: center; margin-bottom: 24px;">
        <p style="color: white; font-size: 14px; margin: 0 0 12px;">Tu código de verificación:</p>
        <div style="background: white; border-radius: 12px; padding: 16px; display: inline-block; border: 2px solid #FF6B6B;">
          <span style="font-size: 32px; font-weight: 900; letter-spacing: 8px; color: #2B2D42;">{code}</span>
        </div>
      </div>

      <p style="color: #8D99AE; font-size: 13px; text-align: center; line-height: 1.5;">
        Este código expira en 10 minutos.<br>
        Si no has solicitado este código, alguien puede estar intentando acceder a tu cuenta.
      </p>
    </div>
    """
    return await send_email(to, subject, html)
