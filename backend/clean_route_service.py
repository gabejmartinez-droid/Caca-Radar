"""Clean Route Service — Analyze paths to avoid high-density poop areas."""
import math
from datetime import datetime, timezone, timedelta
from antispam_service import haversine_meters

CORRIDOR_WIDTH_METERS = 200  # How wide to scan along the route
DANGER_ZONE_RADIUS = 100     # Cluster radius in meters
DANGER_THRESHOLD = 3         # Min reports to be a danger zone


def interpolate_points(lat1, lon1, lat2, lon2, num_points=20):
    """Generate intermediate points along a straight line."""
    points = []
    for i in range(num_points + 1):
        t = i / num_points
        points.append((lat1 + t * (lat2 - lat1), lon1 + t * (lon2 - lon1)))
    return points


def cluster_reports(reports, radius_meters=DANGER_ZONE_RADIUS):
    """Cluster nearby reports into danger zones."""
    clusters = []
    used = set()

    for i, r in enumerate(reports):
        if i in used:
            continue
        cluster = [r]
        used.add(i)
        for j, r2 in enumerate(reports):
            if j in used:
                continue
            dist = haversine_meters(r["latitude"], r["longitude"], r2["latitude"], r2["longitude"])
            if dist < radius_meters:
                cluster.append(r2)
                used.add(j)

        if len(cluster) >= DANGER_THRESHOLD:
            avg_lat = sum(c["latitude"] for c in cluster) / len(cluster)
            avg_lon = sum(c["longitude"] for c in cluster) / len(cluster)
            clusters.append({
                "latitude": round(avg_lat, 6),
                "longitude": round(avg_lon, 6),
                "report_count": len(cluster),
                "radius": radius_meters,
                "risk_level": "alto" if len(cluster) >= 8 else "medio" if len(cluster) >= 5 else "bajo"
            })

    return clusters


async def analyze_clean_route(db, start_lat, start_lon, end_lat, end_lon):
    """Analyze a route between two points and identify danger zones to avoid."""
    # Get all active reports from last 7 days
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    # Calculate bounding box for the corridor
    min_lat = min(start_lat, end_lat) - 0.005
    max_lat = max(start_lat, end_lat) + 0.005
    min_lon = min(start_lon, end_lon) - 0.005
    max_lon = max(start_lon, end_lon) + 0.005

    reports = await db.reports.find({
        "latitude": {"$gte": min_lat, "$lte": max_lat},
        "longitude": {"$gte": min_lon, "$lte": max_lon},
        "archived": {"$ne": True},
        "flagged": {"$ne": True},
        "created_at": {"$gte": week_ago}
    }, {"_id": 0, "latitude": 1, "longitude": 1, "created_at": 1}).to_list(1000)

    # Filter reports within corridor
    path_points = interpolate_points(start_lat, start_lon, end_lat, end_lon)
    corridor_reports = []
    for r in reports:
        for pp in path_points:
            if haversine_meters(r["latitude"], r["longitude"], pp[0], pp[1]) < CORRIDOR_WIDTH_METERS:
                corridor_reports.append(r)
                break

    # Cluster into danger zones
    danger_zones = cluster_reports(corridor_reports)

    # Calculate safe waypoints (deviate around danger zones)
    waypoints = [{"latitude": start_lat, "longitude": start_lon, "type": "start"}]

    for zone in sorted(danger_zones, key=lambda z: haversine_meters(start_lat, start_lon, z["latitude"], z["longitude"])):
        # Suggest a deviation perpendicular to the path
        dx = end_lon - start_lon
        dy = end_lat - start_lat
        length = math.sqrt(dx * dx + dy * dy) or 1
        # Perpendicular offset (0.002 degrees ≈ 200m)
        offset = 0.002
        perp_lat = zone["latitude"] + (-dx / length) * offset
        perp_lon = zone["longitude"] + (dy / length) * offset
        waypoints.append({
            "latitude": round(perp_lat, 6),
            "longitude": round(perp_lon, 6),
            "type": "detour",
            "avoiding": zone["report_count"]
        })

    waypoints.append({"latitude": end_lat, "longitude": end_lon, "type": "end"})

    total_distance = haversine_meters(start_lat, start_lon, end_lat, end_lon)
    risk_score = min(100, len(corridor_reports) * 5)

    return {
        "start": {"latitude": start_lat, "longitude": start_lon},
        "end": {"latitude": end_lat, "longitude": end_lon},
        "danger_zones": danger_zones,
        "waypoints": waypoints,
        "corridor_reports": len(corridor_reports),
        "total_reports_area": len(reports),
        "distance_meters": round(total_distance),
        "risk_score": risk_score,
        "recommendation": "Ruta limpia" if risk_score < 20 else "Precaución en algunas zonas" if risk_score < 50 else "Zona de alto riesgo"
    }
