"""
Test suite for Caca Radar - Rankings & Notifications Features
Tests: City rankings, Barrio rankings, Notifications, Archive cutoff, Freshness labels
"""
import pytest
import requests
import os
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
PREMIUM_USER = {"email": "admin@cacaradar.es", "password": "admin123"}
FREE_USER = {"email": "corstest@test.com", "password": "Test123!"}


class TestCityRankings:
    """City rankings endpoint tests - Premium only"""
    
    def test_city_rankings_requires_premium(self):
        """GET /api/rankings/cities returns 403 for free users"""
        session = requests.Session()
        # Login as free user
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json=FREE_USER)
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        
        # Try to access city rankings
        resp = session.get(f"{BASE_URL}/api/rankings/cities")
        assert resp.status_code == 403, f"Expected 403 for free user, got {resp.status_code}"
        assert "premium" in resp.json().get("detail", "").lower()
        print("PASS: City rankings returns 403 for free users")
    
    def test_city_rankings_works_for_premium(self):
        """GET /api/rankings/cities returns data for premium users"""
        session = requests.Session()
        # Login as premium user (admin)
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json=PREMIUM_USER)
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        
        # Access city rankings
        resp = session.get(f"{BASE_URL}/api/rankings/cities")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        assert "dirtiest" in data, "Missing 'dirtiest' list"
        assert "cleanest" in data, "Missing 'cleanest' list"
        assert "total_cities" in data, "Missing 'total_cities'"
        assert "generated_at" in data, "Missing 'generated_at'"
        
        # Check city data structure
        if data["dirtiest"]:
            city = data["dirtiest"][0]
            assert "city" in city, "Missing 'city' field"
            assert "reports_per_10k" in city, "Missing 'reports_per_10k' field"
            assert "population" in city, "Missing 'population' field"
            assert "rank" in city, "Missing 'rank' field"
            print(f"PASS: City rankings works for premium. Top city: {city['city']} with {city['reports_per_10k']} reports/10k")
        else:
            print("PASS: City rankings works for premium (no cities with data yet)")
    
    def test_city_rankings_unauthenticated(self):
        """GET /api/rankings/cities returns 401 for unauthenticated users"""
        resp = requests.get(f"{BASE_URL}/api/rankings/cities")
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"
        print("PASS: City rankings returns 401/403 for unauthenticated users")


class TestCityRankingsShare:
    """Public shareable city ranking endpoint tests"""
    
    def test_share_endpoint_is_public(self):
        """GET /api/rankings/cities/share is public (no auth required)"""
        resp = requests.get(f"{BASE_URL}/api/rankings/cities/share?list_type=dirtiest")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print("PASS: Share endpoint is public")
    
    def test_share_endpoint_returns_correct_structure(self):
        """GET /api/rankings/cities/share returns correct data structure"""
        resp = requests.get(f"{BASE_URL}/api/rankings/cities/share?list_type=dirtiest")
        assert resp.status_code == 200
        
        data = resp.json()
        assert "title" in data, "Missing 'title'"
        assert "cities" in data, "Missing 'cities'"
        assert "download_links" in data, "Missing 'download_links'"
        assert "share_text" in data, "Missing 'share_text'"
        assert "app_url" in data, "Missing 'app_url'"
        
        # Check download links
        assert "ios" in data["download_links"], "Missing iOS download link"
        assert "android" in data["download_links"], "Missing Android download link"
        
        print(f"PASS: Share endpoint returns correct structure. Title: {data['title']}")
    
    def test_share_endpoint_cleanest_list(self):
        """GET /api/rankings/cities/share?list_type=cleanest returns cleanest cities"""
        resp = requests.get(f"{BASE_URL}/api/rankings/cities/share?list_type=cleanest")
        assert resp.status_code == 200
        
        data = resp.json()
        assert "limpias" in data["title"].lower(), f"Expected 'limpias' in title, got: {data['title']}"
        print(f"PASS: Cleanest list returns correct title: {data['title']}")


class TestBarrioRankings:
    """Barrio rankings endpoint tests - Premium only"""
    
    def test_barrio_rankings_requires_premium(self):
        """GET /api/rankings/barrios returns 403 for free users"""
        session = requests.Session()
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json=FREE_USER)
        assert login_resp.status_code == 200
        
        resp = session.get(f"{BASE_URL}/api/rankings/barrios?city=Madrid")
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
        print("PASS: Barrio rankings returns 403 for free users")
    
    def test_barrio_rankings_works_for_premium(self):
        """GET /api/rankings/barrios returns data for premium users"""
        session = requests.Session()
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json=PREMIUM_USER)
        assert login_resp.status_code == 200
        
        resp = session.get(f"{BASE_URL}/api/rankings/barrios?city=Madrid")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        assert "city" in data, "Missing 'city'"
        assert "barrios" in data, "Missing 'barrios'"
        assert "total_reports" in data, "Missing 'total_reports'"
        
        if data["barrios"]:
            barrio = data["barrios"][0]
            assert "barrio" in barrio, "Missing 'barrio' field"
            assert "active_reports" in barrio, "Missing 'active_reports' field"
            assert "rank" in barrio, "Missing 'rank' field"
            print(f"PASS: Barrio rankings works. Top barrio in {data['city']}: {barrio['barrio']}")
        else:
            print(f"PASS: Barrio rankings works (no barrios with data in {data['city']})")


class TestNotifications:
    """Notification endpoint tests"""
    
    def test_notifications_requires_auth(self):
        """GET /api/notifications returns 401 for unauthenticated users"""
        resp = requests.get(f"{BASE_URL}/api/notifications")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("PASS: Notifications requires authentication")
    
    def test_notifications_returns_list(self):
        """GET /api/notifications returns list for authenticated user"""
        session = requests.Session()
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json=PREMIUM_USER)
        assert login_resp.status_code == 200
        
        resp = session.get(f"{BASE_URL}/api/notifications")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"PASS: Notifications returns list with {len(data)} items")
    
    def test_mark_notifications_read(self):
        """POST /api/notifications/read marks all as read"""
        session = requests.Session()
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json=PREMIUM_USER)
        assert login_resp.status_code == 200
        
        resp = session.post(f"{BASE_URL}/api/notifications/read", json={})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        data = resp.json()
        assert data.get("message") == "ok", f"Expected 'ok', got: {data}"
        print("PASS: Mark notifications read works")
    
    def test_mark_notifications_read_requires_auth(self):
        """POST /api/notifications/read returns 401 for unauthenticated"""
        resp = requests.post(f"{BASE_URL}/api/notifications/read", json={})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("PASS: Mark notifications read requires auth")


class TestFreshnessLabels:
    """Test freshness label logic"""
    
    def test_reports_have_freshness_field(self):
        """GET /api/reports returns freshness field"""
        resp = requests.get(f"{BASE_URL}/api/reports")
        assert resp.status_code == 200
        
        data = resp.json()
        if data:
            report = data[0]
            assert "freshness" in report, "Missing 'freshness' field in report"
            assert report["freshness"] in ["Fresca", "En proceso", "Fósil"], f"Invalid freshness: {report['freshness']}"
            print(f"PASS: Reports have freshness field. Sample: {report['freshness']}")
        else:
            print("PASS: Reports endpoint works (no reports to check freshness)")
    
    def test_freshness_filter_works(self):
        """GET /api/reports?freshness=Fresca filters correctly"""
        resp = requests.get(f"{BASE_URL}/api/reports?freshness=Fresca")
        assert resp.status_code == 200
        
        data = resp.json()
        for report in data:
            assert report.get("freshness") == "Fresca", f"Expected 'Fresca', got {report.get('freshness')}"
        print(f"PASS: Freshness filter works. Found {len(data)} 'Fresca' reports")


class TestArchiveCutoff:
    """Test archive cutoff is 30 days"""
    
    def test_archive_cutoff_in_startup(self):
        """Verify archive cutoff is 30 days by checking server code"""
        # This is a code verification test - we check the server.py file
        import subprocess
        result = subprocess.run(
            ["grep", "-n", "timedelta(days=30)", "/app/backend/server.py"],
            capture_output=True, text=True
        )
        assert "Archive old reports" in result.stdout or "days=30" in result.stdout, \
            "Archive cutoff should be 30 days"
        print("PASS: Archive cutoff is set to 30 days in server.py")


class TestSubscriptionPageFeatures:
    """Test subscription page lists all premium features"""
    
    def test_subscription_status_endpoint(self):
        """GET /api/users/subscription-status returns correct data"""
        session = requests.Session()
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json=PREMIUM_USER)
        assert login_resp.status_code == 200
        
        resp = session.get(f"{BASE_URL}/api/users/subscription-status")
        assert resp.status_code == 200
        
        data = resp.json()
        assert "active" in data, "Missing 'active' field"
        print(f"PASS: Subscription status works. Active: {data['active']}")


class TestRankRecalculation:
    """Test rank recalculation returns rank changes"""
    
    def test_admin_recalculate_ranks(self):
        """POST /api/admin/recalculate-ranks returns rank changes"""
        session = requests.Session()
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json=PREMIUM_USER)
        assert login_resp.status_code == 200
        
        resp = session.post(f"{BASE_URL}/api/admin/recalculate-ranks")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        assert "message" in data, "Missing 'message' field"
        assert "rank changes" in data["message"].lower() or "recalculated" in data["message"].lower()
        print(f"PASS: Rank recalculation works. Message: {data['message']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
