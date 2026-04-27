from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import md5
from typing import Optional

from bson.decimal128 import Decimal128


ACTIVE_REPORT_FILTER = {
    "archived": {"$ne": True},
    "flagged": {"$ne": True},
}

LOCATION_SHARE_COPY = {
    "headline": "¿Cuánta caca de perro hay en nuestras aceras?",
    "subtitle": "Mapa colaborativo",
    "primary_label": "reportes recientes",
    "time_window": "últimas 24 h",
    "fresh_label": "frescos",
    "old_label": "antiguos",
    "fossil_label": "fósiles",
    "cta_primary": "Ver el mapa en Caca Radar",
    "cta_secondary": "Ayuda a mejorar tu zona",
    "footer": "Reporta. Mejora. Respeta.",
}


@dataclass(frozen=True)
class ResolvedLocation:
    city: str
    city_slug: str
    barrio: str = ""
    barrio_slug: str = ""

    @property
    def display_label(self) -> str:
        return f"{self.city} — {self.barrio}" if self.barrio else self.city


def slugify_location_segment(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    ascii_only = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_only).strip("-").lower()
    return slug or "espana"


def _coerce_coordinate(value) -> Optional[float]:
    if value is None:
        return None
    try:
        if isinstance(value, Decimal128):
            return float(value.to_decimal())
        return float(value)
    except (TypeError, ValueError):
        return None


def build_share_path(city_slug: str, barrio_slug: str | None = None) -> str:
    if barrio_slug:
        return f"/api/share/location/{city_slug}/{barrio_slug}"
    return f"/api/share/location/{city_slug}"


def build_share_image_path(city_slug: str, barrio_slug: str | None = None) -> str:
    if barrio_slug:
        return f"/api/share-image/location/{city_slug}/{barrio_slug}"
    return f"/api/share-image/location/{city_slug}"


def build_download_path(city_slug: str, barrio_slug: str | None = None) -> str:
    query = [f"kind=city-report", "source=share", f"city={city_slug}"]
    if barrio_slug:
        query.append(f"barrio={barrio_slug}")
    return f"/download?{'&'.join(query)}"


def get_report_age_bucket(created_at: str, refreshed_at: str | None = None) -> str:
    timestamp = refreshed_at or created_at
    try:
        dt = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except Exception:
        return "fossil"
    age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
    if age_hours <= 24:
        return "fresh"
    if age_hours <= 24 * 7:
        return "old"
    return "fossil"


def get_freshness_label(bucket: str) -> str:
    if bucket == "fresh":
        return "Fresca"
    if bucket == "old":
        return "En proceso"
    return "Fósil"


def _build_etag(payload: dict) -> str:
    digest = md5(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return f'"{digest}"'


def build_cache_headers(payload: dict, max_age: int = 900) -> dict[str, str]:
    return {
        "Cache-Control": f"public, max-age={max_age}, stale-while-revalidate=3600",
        "ETag": _build_etag(payload),
    }


def _fuzz_coordinate(value: float) -> float:
    return round(value, 3)


def _normalize_lookup(value: str) -> str:
    return slugify_location_segment(value)


async def _resolve_city_name(db, city_value: str) -> Optional[str]:
    requested = _normalize_lookup(city_value)
    if not requested:
        return None
    cities = await db.reports.distinct(
        "municipality",
        {**ACTIVE_REPORT_FILTER, "municipality": {"$nin": [None, "", "Desconocido"]}},
    )
    for candidate in cities:
        if _normalize_lookup(candidate) == requested:
            return candidate
    return None


async def _resolve_barrio_name(db, city_name: str, barrio_value: str) -> Optional[str]:
    requested = _normalize_lookup(barrio_value)
    if not requested:
        return None
    barrios = await db.reports.distinct(
        "barrio",
        {
            **ACTIVE_REPORT_FILTER,
            "municipality": city_name,
            "barrio": {"$nin": [None, ""]},
        },
    )
    for candidate in barrios:
        if _normalize_lookup(candidate) == requested:
            return candidate
    return None


async def resolve_location(db, city_value: str, barrio_value: str | None = None) -> Optional[ResolvedLocation]:
    city_name = await _resolve_city_name(db, city_value)
    if not city_name:
        return None
    if barrio_value:
        barrio_name = await _resolve_barrio_name(db, city_name, barrio_value)
        if not barrio_name:
            return None
        return ResolvedLocation(
            city=city_name,
            city_slug=slugify_location_segment(city_name),
            barrio=barrio_name,
            barrio_slug=slugify_location_segment(barrio_name),
        )
    return ResolvedLocation(city=city_name, city_slug=slugify_location_segment(city_name))


async def get_location_share_summary(
    db,
    city_value: str,
    barrio_value: str | None = None,
    preview_limit: int = 40,
) -> dict:
    resolved = await resolve_location(db, city_value, barrio_value)
    if not resolved:
        return {
            "found": False,
            "has_data": False,
            "city": "",
            "city_slug": slugify_location_segment(city_value),
            "barrio": "",
            "barrio_slug": slugify_location_segment(barrio_value or "") if barrio_value else "",
            "display_label": city_value if not barrio_value else f"{city_value} — {barrio_value}",
            "active_report_count": 0,
            "recent_report_count": 0,
            "fresh_count": 0,
            "old_count": 0,
            "fossil_count": 0,
            "time_window_label": LOCATION_SHARE_COPY["time_window"],
            "preview_points": [],
            "map_bounds": None,
            "boundary_polygon": None,
        }

    query = {**ACTIVE_REPORT_FILTER, "municipality": resolved.city}
    if resolved.barrio:
        query["barrio"] = resolved.barrio

    reports = await db.reports.find(
        query,
        {
            "_id": 0,
            "id": 1,
            "latitude": 1,
            "longitude": 1,
            "created_at": 1,
            "refreshed_at": 1,
        },
    ).to_list(5000)

    if not reports:
        return {
            "found": True,
            "has_data": False,
            "city": resolved.city,
            "city_slug": resolved.city_slug,
            "barrio": resolved.barrio,
            "barrio_slug": resolved.barrio_slug,
            "display_label": resolved.display_label,
            "active_report_count": 0,
            "recent_report_count": 0,
            "fresh_count": 0,
            "old_count": 0,
            "fossil_count": 0,
            "time_window_label": LOCATION_SHARE_COPY["time_window"],
            "preview_points": [],
            "map_bounds": None,
            "boundary_polygon": None,
        }

    fresh_count = 0
    old_count = 0
    fossil_count = 0
    preview_points = []
    latitudes: list[float] = []
    longitudes: list[float] = []

    for report in reports:
        bucket = get_report_age_bucket(report.get("created_at", ""), report.get("refreshed_at"))
        if bucket == "fresh":
            fresh_count += 1
        elif bucket == "old":
            old_count += 1
        else:
            fossil_count += 1

        lat = _coerce_coordinate(report.get("latitude"))
        lng = _coerce_coordinate(report.get("longitude"))
        if lat is None or lng is None:
            continue
        lat = _fuzz_coordinate(lat)
        lng = _fuzz_coordinate(lng)
        latitudes.append(lat)
        longitudes.append(lng)
        if len(preview_points) < preview_limit:
            preview_points.append({
                "id": report.get("id"),
                "lat": lat,
                "lng": lng,
                "bucket": "older" if bucket == "old" else bucket,
            })

    map_bounds = None
    if latitudes and longitudes:
        map_bounds = {
            "south": min(latitudes),
            "west": min(longitudes),
            "north": max(latitudes),
            "east": max(longitudes),
            "center_lat": sum(latitudes) / len(latitudes),
            "center_lng": sum(longitudes) / len(longitudes),
        }

    return {
        "found": True,
        "has_data": True,
        "city": resolved.city,
        "city_slug": resolved.city_slug,
        "barrio": resolved.barrio,
        "barrio_slug": resolved.barrio_slug,
        "display_label": resolved.display_label,
        "active_report_count": len(reports),
        "recent_report_count": fresh_count,
        "fresh_count": fresh_count,
        "old_count": old_count,
        "fossil_count": fossil_count,
        "time_window_label": LOCATION_SHARE_COPY["time_window"],
        "preview_points": preview_points,
        "map_bounds": map_bounds,
        "boundary_polygon": None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def build_location_share_metadata(base_url: str, summary: dict) -> dict:
    city_slug = summary.get("city_slug") or slugify_location_segment(summary.get("city", ""))
    barrio_slug = summary.get("barrio_slug") or ""
    city = summary.get("city") or "España"
    barrio = summary.get("barrio") or ""
    location_label = summary.get("display_label") or (f"{city} — {barrio}" if barrio else city)

    share_path = build_share_path(city_slug, barrio_slug or None)
    image_path = build_share_image_path(city_slug, barrio_slug or None)
    download_path = build_download_path(city_slug, barrio_slug or None)

    if barrio:
        title = f"Caca Radar — {city}, {barrio}"
        description = (
            f"{summary.get('recent_report_count', 0)} reportes recientes en {barrio}, {city}. "
            "Mira el mapa y ayuda a mejorar tu zona."
        )
    else:
        title = f"Caca Radar — {city}"
        description = (
            f"{summary.get('recent_report_count', 0)} reportes recientes en {city}. "
            "Mira el mapa y ayuda a mejorar tu zona."
        )

    return {
        "title": title,
        "description": description,
        "location_label": location_label,
        "share_url": f"{base_url}{share_path}",
        "image_url": f"{base_url}{image_path}",
        "download_url": f"{base_url}{download_path}",
        "headline": LOCATION_SHARE_COPY["headline"],
        "time_window_label": LOCATION_SHARE_COPY["time_window"],
    }
