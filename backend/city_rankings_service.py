"""City & Barrio Rankings Service — Population data from Wikipedia, report density calculations."""
import logging
import requests
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Optional

from bson.decimal128 import Decimal128
from location_share_service import get_report_age_bucket, select_preview_scope, slugify_location_segment

logger = logging.getLogger(__name__)

# Top Spanish cities with populations (2023 INE data, cached as fallback)
# Source: https://en.wikipedia.org/wiki/List_of_municipalities_in_Spain
SPAIN_CITY_POPULATIONS = {
    "Madrid": 3332035,
    "Barcelona": 1636193,
    "Valencia": 800215,
    "Sevilla": 681998,
    "Zaragoza": 674997,
    "Málaga": 578460,
    "Murcia": 462979,
    "Palma": 416065,
    "Las Palmas de Gran Canaria": 379925,
    "Bilbao": 346843,
    "Alicante": 337482,
    "Córdoba": 325708,
    "Valladolid": 298866,
    "Vigo": 293642,
    "Gijón": 271843,
    "L'Hospitalet de Llobregat": 264923,
    "Vitoria-Gasteiz": 253672,
    "A Coruña": 245711,
    "Granada": 231775,
    "Elche": 234765,
    "Oviedo": 220020,
    "Badalona": 223506,
    "Cartagena": 218244,
    "Terrassa": 223627,
    "Jerez de la Frontera": 213105,
    "Sabadell": 216520,
    "Móstoles": 210198,
    "Santa Cruz de Tenerife": 209194,
    "Alcalá de Henares": 204823,
    "Pamplona": 203418,
    "Fuenlabrada": 197836,
    "Almería": 200753,
    "Leganés": 190781,
    "San Sebastián": 188240,
    "Getafe": 183567,
    "Burgos": 178966,
    "Santander": 172956,
    "Albacete": 174336,
    "Castellón de la Plana": 172624,
    "Alcorcón": 170514,
    "San Cristóbal de La Laguna": 160130,
    "Logroño": 152398,
    "Badajoz": 150610,
    "Salamanca": 144228,
    "Huelva": 143663,
    "Marbella": 147633,
    "Lleida": 140403,
    "Tarragona": 137580,
    "León": 124028,
    "Cádiz": 116979,
    "Jaén": 112999,
    "Ourense": 105636,
    "Torrejón de Ardoz": 133484,
    "Parla": 132615,
    "Algeciras": 122982,
    "Alcobendas": 118228,
    "Reus": 107211,
    "Telde": 102164,
    "Barakaldo": 100502,
    "Lugo": 98560,
    "Girona": 103369,
    "Santiago de Compostela": 98179,
    "Cáceres": 96068,
    "Lorca": 95637,
    "Torrevieja": 93000,
    "Pontevedra": 83260,
    "Toledo": 85449,
    "Roquetas de Mar": 97000,
    "Benidorm": 71034,
    "Mérida": 59352,
    "Segovia": 51674,
    "Ávila": 57744,
    "Soria": 39398,
    "Teruel": 35890,
    "Cuenca": 54690,
    "Huesca": 54080,
    "Zamora": 61827,
    "Palencia": 78892,
    "Ciudad Real": 75504,
    "Guadalajara": 87484,
}


def get_population(city_name: str) -> int:
    """Get population for a Spanish city. Returns 0 if unknown."""
    # Exact match
    if city_name in SPAIN_CITY_POPULATIONS:
        return SPAIN_CITY_POPULATIONS[city_name]
    # Case-insensitive match
    lower = city_name.lower()
    for name, pop in SPAIN_CITY_POPULATIONS.items():
        if name.lower() == lower:
            return pop
    return 0


def _coerce_coordinate(value) -> Optional[float]:
    if value is None:
        return None
    try:
        if isinstance(value, Decimal128):
            return float(value.to_decimal())
        return float(value)
    except (TypeError, ValueError):
        return None


async def get_city_rankings(db, limit: int = 50) -> dict:
    """Get cleanest and dirtiest cities ranked by active reports per 10,000 residents."""
    # Get active reports grouped by municipality
    pipeline = [
        {"$match": {"archived": {"$ne": True}, "flagged": {"$ne": True}}},
        {"$group": {
            "_id": "$municipality",
            "active_reports": {"$sum": 1},
            "province": {"$first": "$province"},
        }},
        {"$match": {"_id": {"$ne": None}, "_id": {"$ne": "Desconocido"}}},
    ]
    results = await db.reports.aggregate(pipeline).to_list(5000)

    cities = []
    for r in results:
        city_name = r["_id"]
        population = get_population(city_name)
        if population == 0:
            continue  # Skip cities without known population

        active = r["active_reports"]
        rate = round((active / population) * 10000, 2)
        cities.append({
            "city": city_name,
            "province": r.get("province", ""),
            "population": population,
            "active_reports": active,
            "reports_per_10k": rate,
        })

    # Sort: dirtiest first (most reports per 10k)
    cities.sort(key=lambda x: x["reports_per_10k"], reverse=True)

    # Build cleanest (reversed) and dirtiest lists
    dirtiest = cities[:limit]
    cleanest = list(reversed(cities))[:limit]

    # Add rank numbers
    for i, c in enumerate(dirtiest):
        c["rank"] = i + 1
    for i, c in enumerate(cleanest):
        c["rank"] = i + 1

    return {
        "dirtiest": dirtiest,
        "cleanest": cleanest,
        "total_cities": len(cities),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def get_barrio_rankings(db, city: str, limit: int = 50) -> dict:
    """Get barrio/neighborhood rankings within a city by report density."""
    normalized_city = (city or "").strip()
    reports = await db.reports.find(
        {"municipality": normalized_city, "archived": {"$ne": True}, "flagged": {"$ne": True}},
        {"_id": 0, "id": 1, "latitude": 1, "longitude": 1, "status": 1, "created_at": 1, "barrio": 1}
    ).to_list(10000)

    if not reports:
        return {"city": normalized_city, "barrios": [], "total_reports": 0}

    # Group reports into grid cells (~500m) to identify neighborhoods
    grid = defaultdict(list)
    for r in reports:
        lat = _coerce_coordinate(r.get("latitude"))
        lng = _coerce_coordinate(r.get("longitude"))
        if lat is None or lng is None:
            continue
        # Grid cell at ~500m resolution
        lat_cell = round(lat * 200) / 200  # ~0.005 degrees ≈ 500m
        lng_cell = round(lng * 200) / 200
        report = dict(r)
        report["latitude"] = lat
        report["longitude"] = lng
        grid[(lat_cell, lng_cell)].append(report)

    # Try to get barrio names via reverse geocode for each cluster center
    barrios = []
    for (lat, lng), cluster_reports in grid.items():
        count = len(cluster_reports)
        if count == 0:
            continue

        barrio_name = _cluster_barrio_name(cluster_reports)
        if not barrio_name:
            barrio_name = await _get_barrio_name(db, lat, lng, normalized_city)

        verified = sum(1 for r in cluster_reports if r.get("status") == "verified")
        barrios.append({
            "barrio": barrio_name,
            "active_reports": count,
            "verified_reports": verified,
            "latitude": lat,
            "longitude": lng,
        })

    # Merge barrios with same name
    merged = {}
    for b in barrios:
        name = b["barrio"]
        if name in merged:
            merged[name]["active_reports"] += b["active_reports"]
            merged[name]["verified_reports"] += b["verified_reports"]
        else:
            merged[name] = b.copy()

    barrio_list = list(merged.values())

    # Sort: dirtiest first
    barrio_list.sort(key=lambda x: x["active_reports"], reverse=True)
    barrio_list = barrio_list[:limit]

    for i, b in enumerate(barrio_list):
        b["rank"] = i + 1

    return {
        "city": normalized_city,
        "barrios": barrio_list,
        "total_reports": len(reports),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def get_active_report_cities(db, limit: int = 500) -> dict:
    """Return cities that currently have active reports."""
    pipeline = [
        {"$match": {"archived": {"$ne": True}, "flagged": {"$ne": True}}},
        {"$group": {
            "_id": "$municipality",
            "active_reports": {"$sum": 1},
            "province": {"$first": "$province"},
        }},
        {"$match": {"_id": {"$nin": [None, "", "Desconocido"]}}},
        {"$sort": {"active_reports": -1, "_id": 1}},
    ]
    results = await db.reports.aggregate(pipeline).to_list(limit)
    return {
        "cities": [
            {
                "city": r["_id"],
                "province": r.get("province", ""),
                "active_reports": r.get("active_reports", 0),
            }
            for r in results
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def get_active_report_barrios(db, city: str, limit: int = 500) -> dict:
    """Return barrios within a city that currently have active reports."""
    pipeline = [
        {"$match": {
            "municipality": city,
            "archived": {"$ne": True},
            "flagged": {"$ne": True},
            "barrio": {"$nin": [None, ""]},
        }},
        {"$group": {
            "_id": "$barrio",
            "active_reports": {"$sum": 1},
        }},
        {"$sort": {"active_reports": -1, "_id": 1}},
    ]
    results = await db.reports.aggregate(pipeline).to_list(limit)
    return {
        "city": city,
        "barrios": [
            {
                "barrio": r["_id"],
                "active_reports": r.get("active_reports", 0),
            }
            for r in results
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def get_city_report_summary(db, city: str, barrio: str | None = None, preview_limit: int = 250) -> dict:
    """Return active report counts, freshness buckets, and preview points for a city or barrio."""
    query = {"municipality": city, "archived": {"$ne": True}, "flagged": {"$ne": True}}
    if barrio:
        query["barrio"] = barrio

    reports = await db.reports.find(
        query,
        {
            "_id": 0,
            "id": 1,
            "latitude": 1,
            "longitude": 1,
            "created_at": 1,
            "refreshed_at": 1,
            "province": 1,
            "barrio": 1,
        },
    ).to_list(5000)

    if not reports:
        return {
            "city": city,
            "barrio": barrio or "",
            "province": "",
            "total_active_reports": 0,
            "fresh_reports": 0,
            "older_reports": 0,
            "fossil_reports": 0,
            "preview_points": [],
            "map_bounds": None,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    fresh_reports = 0
    older_reports = 0
    fossil_reports = 0
    all_points = []

    for report in reports:
        bucket = get_report_age_bucket(report.get("created_at", ""), report.get("refreshed_at"))
        if bucket == "fresh":
            fresh_reports += 1
        elif bucket == "old":
            older_reports += 1
        else:
            fossil_reports += 1

        lat = _coerce_coordinate(report.get("latitude"))
        lng = _coerce_coordinate(report.get("longitude"))
        if lat is None or lng is None:
            continue

        all_points.append({
            "id": report.get("id"),
            "lat": lat,
            "lng": lng,
            "bucket": "older" if bucket == "old" else bucket,
            "barrio": report.get("barrio", ""),
        })

    preview_points, map_bounds = select_preview_scope(
        slugify_location_segment(city),
        barrio,
        all_points,
        preview_limit=preview_limit,
    )

    return {
        "city": city,
        "barrio": barrio or "",
        "province": reports[0].get("province", ""),
        "total_active_reports": len(reports),
        "fresh_reports": fresh_reports,
        "older_reports": older_reports,
        "fossil_reports": fossil_reports,
        "preview_points": preview_points,
        "map_bounds": map_bounds,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def _get_barrio_name(db, lat: float, lng: float, city: str) -> str:
    """Get barrio name from cache or Nominatim reverse geocode."""
    # Check cache first
    cached = await db.barrio_cache.find_one(
        {"lat": lat, "lng": lng, "city": city},
        {"_id": 0, "barrio": 1}
    )
    if cached:
        return cached["barrio"]

    # Reverse geocode with high zoom for neighborhood detail
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lng, "format": "json", "addressdetails": 1, "zoom": 16},
            headers={"User-Agent": "CacaRadar/1.0"},
            timeout=5
        )
        resp.raise_for_status()
        data = resp.json()
        address = data.get("address", {})
        resolved_city = (
            address.get("city") or
            address.get("town") or
            address.get("village") or
            address.get("municipality") or
            ""
        ).strip()
        if not _matches_city(resolved_city, city):
            barrio = f"Zona {lat:.3f},{lng:.3f}"
        else:
            barrio = (
                address.get("neighbourhood") or
                address.get("suburb") or
                address.get("quarter") or
                address.get("city_district") or
                address.get("district") or
                f"{city} Centro"
            )
    except Exception:
        barrio = f"Zona {lat:.3f},{lng:.3f}"

    # Cache it
    await db.barrio_cache.update_one(
        {"lat": lat, "lng": lng, "city": city},
        {"$set": {"barrio": barrio, "city": city, "cached_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )

    return barrio


def _matches_city(resolved_city: str, requested_city: str) -> bool:
    return resolved_city.strip().lower() == requested_city.strip().lower()


def _cluster_barrio_name(cluster_reports: list[dict]) -> str:
    names = [
        (report.get("barrio") or "").strip()
        for report in cluster_reports
        if (report.get("barrio") or "").strip()
    ]
    if not names:
        return ""
    return Counter(names).most_common(1)[0][0]
