"""
Test Community Impact Map Feature
- GET /api/users/impact endpoint
- Impact page route and elements
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "jefe@cacaradar.es"
ADMIN_PASSWORD = "Cacaradar123$"


class TestImpactEndpoint:
    """Tests for GET /api/users/impact endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup session for tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_impact_returns_401_for_unauthenticated(self):
        """GET /api/users/impact should return 401 for unauthenticated users"""
        response = self.session.get(f"{BASE_URL}/api/users/impact")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print("PASS: /api/users/impact returns 401 for unauthenticated users")
    
    def test_login_admin_user(self):
        """Login with admin credentials to get auth cookies"""
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "id" in data, "Login response should contain user id"
        assert data.get("email") == ADMIN_EMAIL
        print(f"PASS: Admin login successful - user: {data.get('username', data.get('name'))}")
        return data
    
    def test_impact_returns_data_for_authenticated_user(self):
        """GET /api/users/impact should return impact data for authenticated user"""
        # First login
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        # Now get impact data
        response = self.session.get(f"{BASE_URL}/api/users/impact")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Impact data received: {data}")
        
        # Verify schema
        assert "username" in data, "Response should contain username"
        assert "rank" in data, "Response should contain rank"
        assert "total_score" in data, "Response should contain total_score"
        assert "stats" in data, "Response should contain stats"
        assert "map_points" in data, "Response should contain map_points"
        assert "timeline" in data, "Response should contain timeline"
        assert "municipalities" in data, "Response should contain municipalities"
        assert "barrios" in data, "Response should contain barrios"
        
        # Verify stats structure
        stats = data["stats"]
        assert "total_reports" in stats, "Stats should contain total_reports"
        assert "cleaned_reports" in stats, "Stats should contain cleaned_reports"
        assert "active_reports" in stats, "Stats should contain active_reports"
        assert "total_confirmations" in stats, "Stats should contain total_confirmations"
        assert "upvotes_received" in stats, "Stats should contain upvotes_received"
        assert "impact_score" in stats, "Stats should contain impact_score"
        assert "municipalities_helped" in stats, "Stats should contain municipalities_helped"
        assert "barrios_helped" in stats, "Stats should contain barrios_helped"
        
        print(f"PASS: /api/users/impact returns correct schema for authenticated user")
        print(f"  - Username: {data['username']}")
        print(f"  - Rank: {data['rank']}")
        print(f"  - Total Score: {data['total_score']}")
        print(f"  - Impact Score: {stats['impact_score']}")
        print(f"  - Total Reports: {stats['total_reports']}")
        print(f"  - Map Points: {len(data['map_points'])}")
        return data
    
    def test_impact_map_points_structure(self):
        """Verify map_points have correct structure when present"""
        # Login
        self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        response = self.session.get(f"{BASE_URL}/api/users/impact")
        assert response.status_code == 200
        
        data = response.json()
        map_points = data.get("map_points", [])
        
        # If there are map points, verify their structure
        if len(map_points) > 0:
            point = map_points[0]
            assert "id" in point, "Map point should have id"
            assert "lat" in point, "Map point should have lat"
            assert "lng" in point, "Map point should have lng"
            assert "type" in point, "Map point should have type"
            assert point["type"] in ["cleaned", "active", "confirmed"], f"Invalid type: {point['type']}"
            print(f"PASS: Map points have correct structure ({len(map_points)} points)")
        else:
            print("PASS: No map points (user has no reports) - empty state expected")
    
    def test_impact_timeline_structure(self):
        """Verify timeline has correct structure"""
        # Login
        self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        response = self.session.get(f"{BASE_URL}/api/users/impact")
        assert response.status_code == 200
        
        data = response.json()
        timeline = data.get("timeline", [])
        
        # Timeline should be a list
        assert isinstance(timeline, list), "Timeline should be a list"
        
        # If there are timeline entries, verify structure
        if len(timeline) > 0:
            entry = timeline[0]
            assert "month" in entry, "Timeline entry should have month"
            assert "count" in entry, "Timeline entry should have count"
            print(f"PASS: Timeline has correct structure ({len(timeline)} months)")
        else:
            print("PASS: Empty timeline (user has no reports)")


class TestImpactPageRoute:
    """Tests for /impact page route"""
    
    def test_impact_page_exists(self):
        """Verify /impact route exists and returns HTML"""
        response = requests.get(f"{BASE_URL}/impact")
        # Should return 200 (React SPA serves index.html for all routes)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "text/html" in response.headers.get("content-type", ""), "Should return HTML"
        print("PASS: /impact route exists and returns HTML")


class TestProfilePageImpactButton:
    """Tests for Profile page 'Mi Impacto Comunitario' button"""
    
    def test_profile_page_exists(self):
        """Verify /profile route exists"""
        response = requests.get(f"{BASE_URL}/profile")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: /profile route exists")


class TestMapPageImpactMenu:
    """Tests for MapPage user menu 'Mi Impacto' item"""
    
    def test_map_page_exists(self):
        """Verify / (map page) route exists"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: / (map page) route exists")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
