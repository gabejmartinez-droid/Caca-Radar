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

GENERIC_CITY_CENTER_ALIASES = [
    "casco-antiguo",
    "casco-historico",
    "centro",
    "centro-historico",
    "centro-historic",
    "old-town",
    "historic-centre",
    "city-center",
]

CITY_CENTER_FOCUS_AREAS = {
    "cartagena": ["casco-antiguo", "centro"],
    "madrid": ["centro", "sol", "palacio", "cortes", "embajadores", "justicia", "universidad"],
    "barcelona": ["ciutat-vella", "barri-gotic", "el-raval", "sant-pere-santa-caterina-i-la-ribera"],
    "sevilla": ["casco-antiguo", "centro", "santa-cruz", "arenal", "alfalfa"],
    "valencia": ["ciutat-vella", "el-carme", "la-seu", "el-mercat", "sant-francesc", "centro"],
    "oviedo": ["centro", "casco-antiguo"],
    "murcia": ["centro", "san-bartolome", "santa-eulalia", "san-juan", "san-lorenzo"],
    "cadiz": ["casco-antiguo", "centro"],
    "granada": ["centro", "albaicin", "realejo"],
    "toledo": ["casco-historico", "casco-antiguo", "centro"],
}

CITY_CENTER_PREVIEW_WINDOWS = {
    "cartagena": {"south": 37.595, "west": -0.994, "north": 37.605, "east": -0.979},
    "madrid": {"south": 40.412, "west": -3.715, "north": 40.424, "east": -3.696},
    "barcelona": {"south": 41.376, "west": 2.168, "north": 41.392, "east": 2.188},
    "sevilla": {"south": 37.382, "west": -5.999, "north": 37.394, "east": -5.983},
    "valencia": {"south": 39.468, "west": -0.384, "north": 39.478, "east": -0.367},
    "oviedo": {"south": 43.357, "west": -5.851, "north": 43.366, "east": -5.839},
    "murcia": {"south": 37.981, "west": -1.135, "north": 37.990, "east": -1.121},
    "cadiz": {"south": 36.526, "west": -6.300, "north": 36.536, "east": -6.286},
    "granada": {"south": 37.171, "west": -3.607, "north": 37.183, "east": -3.592},
    "toledo": {"south": 39.855, "west": -4.033, "north": 39.865, "east": -4.019},
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


def append_query_params(url: str, **params) -> str:
    valid_items = [(key, value) for key, value in params.items() if value not in (None, "")]
    if not valid_items:
        return url
    separator = "&" if "?" in url else "?"
    query = "&".join(f"{key}={value}" for key, value in valid_items)
    return f"{url}{separator}{query}"


def _fuzz_coordinate(value: float) -> float:
    return round(value, 3)


def _normalize_lookup(value: str) -> str:
    return slugify_location_segment(value)


def _city_center_aliases(city_slug: str) -> list[str]:
    specific = CITY_CENTER_FOCUS_AREAS.get(city_slug, [])
    aliases = specific + GENERIC_CITY_CENTER_ALIASES
    deduped = []
    seen = set()
    for alias in aliases:
        normalized = slugify_location_segment(alias)
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(normalized)
    return deduped


def _matches_center_alias(barrio_value: str, city_slug: str) -> bool:
    barrio_slug = slugify_location_segment(barrio_value or "")
    if not barrio_slug:
        return False
    return barrio_slug in _city_center_aliases(city_slug)


def _map_bounds_for_points(points: list[dict]) -> Optional[dict]:
    if not points:
        return None
    latitudes = [point["lat"] for point in points]
    longitudes = [point["lng"] for point in points]
    return {
        "south": min(latitudes),
        "west": min(longitudes),
        "north": max(latitudes),
        "east": max(longitudes),
        "center_lat": sum(latitudes) / len(latitudes),
        "center_lng": sum(longitudes) / len(longitudes),
    }


def _window_bounds(window: dict) -> dict:
    return {
        "south": window["south"],
        "west": window["west"],
        "north": window["north"],
        "east": window["east"],
        "center_lat": (window["south"] + window["north"]) / 2,
        "center_lng": (window["west"] + window["east"]) / 2,
    }


def _point_in_window(point: dict, window: dict) -> bool:
    return (
        window["south"] <= point["lat"] <= window["north"]
        and window["west"] <= point["lng"] <= window["east"]
    )


def select_preview_scope(city_slug: str, barrio: str | None, points: list[dict], preview_limit: int = 40) -> tuple[list[dict], Optional[dict]]:
    if not points:
        return [], None
    if barrio:
        selected = points[:preview_limit]
        return selected, _map_bounds_for_points(selected)

    window = CITY_CENTER_PREVIEW_WINDOWS.get(city_slug)
    if window:
        focused = [point for point in points if _point_in_window(point, window)]
        if focused:
            return focused[:preview_limit], _window_bounds(window)

    focused = [point for point in points if _matches_center_alias(point.get("barrio", ""), city_slug)]
    if len(focused) >= min(5, len(points)):
        selected = focused[:preview_limit]
        return selected, _map_bounds_for_points(selected)

    center_lat = sum(point["lat"] for point in points) / len(points)
    center_lng = sum(point["lng"] for point in points) / len(points)
    selected = sorted(
        points,
        key=lambda point: ((point["lat"] - center_lat) ** 2) + ((point["lng"] - center_lng) ** 2),
    )[:preview_limit]
    return selected, _map_bounds_for_points(selected)


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
            "barrio": 1,
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
    all_points = []

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
        all_points.append({
            "id": report.get("id"),
            "lat": lat,
            "lng": lng,
            "bucket": "older" if bucket == "old" else bucket,
            "barrio": report.get("barrio", ""),
        })

    preview_points, map_bounds = select_preview_scope(
        resolved.city_slug,
        resolved.barrio or None,
        all_points,
        preview_limit=preview_limit,
    )

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


def build_location_share_metadata(base_url: str, summary: dict, image_version: str | None = None) -> dict:
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
        "image_url": append_query_params(f"{base_url}{image_path}", v=image_version),
        "download_url": f"{base_url}{download_path}",
        "headline": LOCATION_SHARE_COPY["headline"],
        "time_window_label": LOCATION_SHARE_COPY["time_window"],
    }
