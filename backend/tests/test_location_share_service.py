from datetime import datetime, timedelta, timezone

from location_share_service import (
    build_location_share_metadata,
    build_share_path,
    get_report_age_bucket,
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
