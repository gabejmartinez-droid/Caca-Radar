from datetime import datetime, timedelta, timezone

from location_share_service import (
    build_location_share_metadata,
    build_share_path,
    get_report_age_bucket,
    select_preview_scope,
    slugify_location_segment,
)
from share_image_service import build_location_share_card_image, get_share_image_media_type


def test_slugify_location_segment():
    assert slugify_location_segment("Cartagena") == "cartagena"
    assert slugify_location_segment("Casco Antiguo") == "casco-antiguo"
    assert slugify_location_segment("L'Hospitalet de Llobregat") == "l-hospitalet-de-llobregat"


def test_city_only_share_path_generation():
    assert build_share_path("cartagena") == "/api/share/location/cartagena"


def test_city_and_barrio_share_path_generation():
    assert build_share_path("cartagena", "casco-antiguo") == "/api/share/location/cartagena/casco-antiguo"


def test_metadata_generation_for_city_and_barrio():
    metadata = build_location_share_metadata(
        "https://cacaradar.es",
        {
            "city": "Cartagena",
            "city_slug": "cartagena",
            "barrio": "Casco Antiguo",
            "barrio_slug": "casco-antiguo",
            "display_label": "Cartagena — Casco Antiguo",
            "recent_report_count": 67,
        },
    )
    assert metadata["title"] == "Caca Radar — Cartagena, Casco Antiguo"
    assert metadata["share_url"] == "https://cacaradar.es/api/share/location/cartagena/casco-antiguo"
    assert metadata["image_url"] == "https://cacaradar.es/api/share-image/location/cartagena/casco-antiguo"


def test_report_age_bucket_thresholds():
    now = datetime.now(timezone.utc)
    fresh = (now - timedelta(hours=12)).isoformat()
    old = (now - timedelta(days=3)).isoformat()
    fossil = (now - timedelta(days=8)).isoformat()
    assert get_report_age_bucket(fresh) == "fresh"
    assert get_report_age_bucket(old) == "old"
    assert get_report_age_bucket(fossil) == "fossil"


def test_share_image_renderer_returns_bytes_and_supported_media_type():
    payload = {
        "city": "Cartagena",
        "city_slug": "cartagena",
        "barrio": "Casco Antiguo",
        "barrio_slug": "casco-antiguo",
        "display_label": "Cartagena — Casco Antiguo",
        "active_report_count": 436,
        "recent_report_count": 67,
        "fresh_count": 67,
        "old_count": 123,
        "fossil_count": 246,
        "time_window_label": "últimas 24 h",
        "preview_points": [],
        "map_bounds": None,
    }
    rendered = build_location_share_card_image(payload)
    assert isinstance(rendered, bytes)
    assert get_share_image_media_type() in {"image/png", "image/svg+xml"}


def test_select_preview_scope_prefers_casco_antiguo_for_city_view():
    points = [
        {"id": "1", "lat": 37.600, "lng": -0.986, "bucket": "fresh", "barrio": "Casco Antiguo"},
        {"id": "2", "lat": 37.601, "lng": -0.985, "bucket": "fresh", "barrio": "Casco Antiguo"},
        {"id": "3", "lat": 37.602, "lng": -0.984, "bucket": "old", "barrio": "Casco Antiguo"},
        {"id": "4", "lat": 37.603, "lng": -0.983, "bucket": "fossil", "barrio": "Casco Antiguo"},
        {"id": "5", "lat": 37.604, "lng": -0.982, "bucket": "fossil", "barrio": "Casco Antiguo"},
        {"id": "6", "lat": 37.670, "lng": -1.000, "bucket": "fresh", "barrio": "Periferia"},
    ]
    preview_points, map_bounds = select_preview_scope("cartagena", None, points, preview_limit=10)
    assert len(preview_points) == 5
    assert all(point["barrio"] == "Casco Antiguo" for point in preview_points)
    assert map_bounds is not None


def test_select_preview_scope_prefers_explicit_city_center_window():
    points = [
        {"id": "1", "lat": 40.418, "lng": -3.706, "bucket": "fresh", "barrio": "Centro"},
        {"id": "2", "lat": 40.419, "lng": -3.704, "bucket": "old", "barrio": "Sol"},
        {"id": "3", "lat": 40.450, "lng": -3.620, "bucket": "fossil", "barrio": "Lejano"},
    ]
    preview_points, map_bounds = select_preview_scope("madrid", None, points, preview_limit=10)
    assert len(preview_points) == 2
    assert {point["id"] for point in preview_points} == {"1", "2"}
    assert map_bounds is not None
    assert map_bounds["south"] == 40.412
    assert map_bounds["east"] == -3.696


def test_select_preview_scope_uses_requested_barrio_without_recentering():
    points = [
        {"id": "1", "lat": 37.600, "lng": -0.986, "bucket": "fresh", "barrio": "Centro"},
        {"id": "2", "lat": 37.670, "lng": -1.000, "bucket": "old", "barrio": "Centro"},
    ]
    preview_points, map_bounds = select_preview_scope("cartagena", "Centro", points, preview_limit=10)
    assert preview_points == points
    assert map_bounds is not None
