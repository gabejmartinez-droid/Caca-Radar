"""City & Barrio Rankings Service — Population data from Wikipedia, report density calculations."""
import logging
import requests
from datetime import datetime, timezone
from typing import Optional

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
    # Get reports for this city with their display_name (contains barrio info)
    reports = await db.reports.find(
        {"municipality": city, "archived": {"$ne": True}, "flagged": {"$ne": True}},
        {"_id": 0, "id": 1, "latitude": 1, "longitude": 1, "status": 1, "created_at": 1}
    ).to_list(10000)

    if not reports:
        return {"city": city, "barrios": [], "total_reports": 0}

    # Group reports into grid cells (~500m) to identify neighborhoods
    from collections import defaultdict
    grid = defaultdict(list)
    for r in reports:
        # Grid cell at ~500m resolution
        lat_cell = round(r["latitude"] * 200) / 200  # ~0.005 degrees ≈ 500m
        lng_cell = round(r["longitude"] * 200) / 200
        grid[(lat_cell, lng_cell)].append(r)

    # Try to get barrio names via reverse geocode for each cluster center
    barrios = []
    for (lat, lng), cluster_reports in grid.items():
        count = len(cluster_reports)
        if count == 0:
            continue

        # Use the cluster center for naming
        barrio_name = await _get_barrio_name(db, lat, lng, city)

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
        "city": city,
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


def _city_report_bucket(created_at: str, refreshed_at: Optional[str] = None) -> str:
    timestamp = refreshed_at or created_at
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except Exception:
        return "fossil"
    hours_diff = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
    if hours_diff < 48:
        return "fresh"
    if hours_diff < 144:
        return "older"
    return "fossil"


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
    preview_points = []
    latitudes = []
    longitudes = []

    for report in reports:
        bucket = _city_report_bucket(report.get("created_at", ""), report.get("refreshed_at"))
        if bucket == "fresh":
            fresh_reports += 1
        elif bucket == "older":
            older_reports += 1
        else:
            fossil_reports += 1

        lat = report.get("latitude")
        lng = report.get("longitude")
        if lat is None or lng is None:
            continue

        latitudes.append(lat)
        longitudes.append(lng)

        if len(preview_points) < preview_limit:
            preview_points.append({
                "id": report.get("id"),
                "lat": lat,
                "lng": lng,
                "bucket": bucket,
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
        {"lat": lat, "lng": lng},
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
        {"lat": lat, "lng": lng},
        {"$set": {"barrio": barrio, "city": city, "cached_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )

    return barrio
