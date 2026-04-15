"""Weekly Digest Service — Generate and send weekly email summaries to municipalities."""
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


async def generate_municipality_digest(db, muni_name: str) -> dict:
    """Generate weekly stats for a municipality."""
    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()
    prev_week_start = (now - timedelta(days=14)).isoformat()

    new_reports = await db.reports.count_documents({"municipality": muni_name, "created_at": {"$gte": week_ago}})
    prev_reports = await db.reports.count_documents({"municipality": muni_name, "created_at": {"$gte": prev_week_start, "$lt": week_ago}})
    resolved = await db.reports.count_documents({"municipality": muni_name, "archived": True, "created_at": {"$gte": week_ago}})
    flagged = await db.reports.count_documents({"municipality": muni_name, "flagged": True, "created_at": {"$gte": week_ago}})
    active = await db.reports.count_documents({"municipality": muni_name, "archived": False, "flagged": False})

    # Top zones this week
    reports = await db.reports.find(
        {"municipality": muni_name, "created_at": {"$gte": week_ago}},
        {"_id": 0, "latitude": 1, "longitude": 1}
    ).to_list(500)
    zone_map = {}
    for r in reports:
        key = f"{round(r['latitude'], 3)},{round(r['longitude'], 3)}"
        zone_map[key] = zone_map.get(key, 0) + 1
    top_zones = sorted(zone_map.items(), key=lambda x: -x[1])[:5]

    trend = "up" if new_reports > prev_reports else "down" if new_reports < prev_reports else "stable"
    trend_pct = round(((new_reports - prev_reports) / max(prev_reports, 1)) * 100)

    return {
        "municipality": muni_name,
        "period": f"{(now - timedelta(days=7)).strftime('%d/%m')} - {now.strftime('%d/%m/%Y')}",
        "new_reports": new_reports,
        "prev_week_reports": prev_reports,
        "trend": trend,
        "trend_pct": trend_pct,
        "resolved": resolved,
        "flagged": flagged,
        "active_total": active,
        "top_zones": [{"zone": z[0], "count": z[1]} for z in top_zones]
    }


def build_digest_html(digest: dict) -> str:
    """Build HTML email for the weekly digest."""
    trend_icon = "&#9650;" if digest["trend"] == "up" else "&#9660;" if digest["trend"] == "down" else "&#9654;"
    trend_color = "#FF5252" if digest["trend"] == "up" else "#66BB6A" if digest["trend"] == "down" else "#8D99AE"

    zones_html = ""
    for z in digest["top_zones"]:
        zones_html += f'<tr><td style="padding:4px 8px;font-size:13px;color:#2B2D42;">{z["zone"]}</td><td style="padding:4px 8px;font-size:13px;color:#FF6B6B;font-weight:700;text-align:right;">{z["count"]}</td></tr>'

    flagged_count = digest['flagged']
    flagged_html = ""
    if flagged_count > 0:
        flagged_html = f"<div style='background:#FFF3E0;border-radius:12px;padding:12px;margin-bottom:16px;'><p style='font-size:12px;color:#E65100;margin:0;'>&#9888; {flagged_count} reportes marcados pendientes de revisión</p></div>"

    zones_section = ""
    if zones_html:
        zones_section = "<div style='background:#fff;border-radius:12px;padding:16px;margin-bottom:16px;border:1px solid #eee;'><h3 style='color:#2B2D42;font-size:14px;margin:0 0 8px;'>Zonas con más actividad</h3><table width='100%'>" + zones_html + "</table></div>"

    return f"""
    <div style="font-family:'Helvetica Neue',Arial,sans-serif;max-width:520px;margin:0 auto;padding:24px;">
      <div style="text-align:center;margin-bottom:20px;">
        <h1 style="color:#2B2D42;font-size:22px;margin:0;">Caca Radar</h1>
        <p style="color:#8D99AE;font-size:13px;margin:4px 0;">Resumen Semanal — {digest['municipality']}</p>
        <p style="color:#8D99AE;font-size:12px;margin:0;">{digest['period']}</p>
      </div>

      <div style="background:#F8F9FA;border-radius:12px;padding:20px;margin-bottom:16px;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="text-align:center;padding:8px;">
              <p style="font-size:28px;font-weight:900;color:#2B2D42;margin:0;">{digest['new_reports']}</p>
              <p style="font-size:11px;color:#8D99AE;margin:2px 0;">Nuevos reportes</p>
              <p style="font-size:12px;color:{trend_color};margin:0;">{trend_icon} {abs(digest['trend_pct'])}%</p>
            </td>
            <td style="text-align:center;padding:8px;">
              <p style="font-size:28px;font-weight:900;color:#66BB6A;margin:0;">{digest['resolved']}</p>
              <p style="font-size:11px;color:#8D99AE;margin:2px 0;">Resueltos</p>
            </td>
            <td style="text-align:center;padding:8px;">
              <p style="font-size:28px;font-weight:900;color:#FFA726;margin:0;">{digest['active_total']}</p>
              <p style="font-size:11px;color:#8D99AE;margin:2px 0;">Activos total</p>
            </td>
          </tr>
        </table>
      </div>

      {zones_section}
      {flagged_html}

      <div style="text-align:center;margin-top:20px;">
        <a href="#" style="display:inline-block;background:#2B2D42;color:white;padding:10px 24px;border-radius:8px;text-decoration:none;font-size:13px;font-weight:700;">Abrir Panel de Control</a>
      </div>

      <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
      <p style="color:#8D99AE;font-size:11px;text-align:center;">Caca Radar — Manteniendo las calles limpias</p>
    </div>
    """


async def send_weekly_digests(db):
    """Send weekly digest to all active municipality accounts."""
    from email_service import send_email, is_configured

    munis = await db.users.find(
        {"role": "municipality", "municipality_subscription_active": True},
        {"_id": 0, "email": 1, "municipality_name": 1}
    ).to_list(500)

    sent = 0
    for muni in munis:
        try:
            digest = await generate_municipality_digest(db, muni["municipality_name"])
            html = build_digest_html(digest)
            subject = f"Resumen Semanal — {muni['municipality_name']} — Caca Radar"
            await send_email(muni["email"], subject, html)
            sent += 1
        except Exception as e:
            logger.error(f"Failed digest for {muni.get('municipality_name')}: {e}")

    logger.info(f"Weekly digests sent to {sent}/{len(munis)} municipalities")
    return {"sent": sent, "total": len(munis)}
