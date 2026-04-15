"""
Test suite for server.py refactor and new features:
1. Backend starts successfully after refactor (deps.py extraction)
2. GET /api/health returns ok
3. POST /api/auth/register works (username required)
4. POST /api/auth/login works with cookie auth
5. GET /api/reports returns reports with freshness labels
6. GET /api/rankings/cities works for premium users (403 for free)
7. GET /api/rankings/barrios?city=Madrid works for premium users
8. GET /api/rankings/cities/share is public
9. GET /api/notifications returns unread notifications
10. POST /api/municipality/subscribe returns €50/mes price
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://caca-radar.preview.emergentagent.com').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "admin@cacaradar.es"
ADMIN_PASSWORD = "admin123"
FREE_USER_EMAIL = "corstest@test.com"
FREE_USER_PASSWORD = "Test123!"
MUNICIPALITY_EMAIL = "madrid@cacaradar.es"
MUNICIPALITY_PASSWORD = "madrid123"


class TestHealthAndRefactor:
    """Test that backend starts successfully after deps.py refactor"""
    
    def test_health_endpoint(self):
        """GET /api/health returns ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print("PASS: GET /api/health returns ok")


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_register_requires_username(self):
        """POST /api/auth/register requires username field"""
        unique_email = f"test_{uuid.uuid4().hex[:8]}@test.com"
        
        # Try without username - should fail
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "Test123!"
        })
        # Should fail with 422 (validation error) because username is required
        assert response.status_code == 422
        print("PASS: Register without username returns 422")
    
    def test_register_with_username(self):
        """POST /api/auth/register works with username"""
        unique_username = f"test_{uuid.uuid4().hex[:8]}"
        unique_email = f"{unique_username}@test.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "Test123!",
            "username": unique_username
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("username") == unique_username
        assert data.get("email") == unique_email
        assert "id" in data
        print(f"PASS: Register with username works - created user {unique_username}")
    
    def test_login_with_cookie_auth(self):
        """POST /api/auth/login sets httpOnly cookies"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("email") == ADMIN_EMAIL
        
        # Check cookies are set
        cookies = session.cookies.get_dict()
        assert "access_token" in cookies or response.cookies.get("access_token") is not None
        print("PASS: Login sets cookies and returns user data")
    
    def test_login_invalid_credentials(self):
        """POST /api/auth/login returns 401 for invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("PASS: Login with invalid credentials returns 401")


class TestReportsEndpoint:
    """Test reports endpoint with freshness labels"""
    
    def test_reports_returns_freshness_labels(self):
        """GET /api/reports returns reports with freshness field"""
        response = requests.get(f"{BASE_URL}/api/reports")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Check that reports have freshness field
        if len(data) > 0:
            report = data[0]
            assert "freshness" in report
            assert report["freshness"] in ["Fresca", "En proceso", "Fósil"]
            print(f"PASS: Reports have freshness labels - found '{report['freshness']}'")
        else:
            print("PASS: Reports endpoint works (no reports to check freshness)")


class TestRankingsEndpoints:
    """Test city and barrio rankings endpoints"""
    
    @pytest.fixture
    def premium_session(self):
        """Get authenticated session for premium user (admin)"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Could not login as admin: {response.text}")
        return session
    
    @pytest.fixture
    def free_session(self):
        """Get authenticated session for free user"""
        session = requests.Session()
        # Create a new free user
        unique_username = f"free_{uuid.uuid4().hex[:8]}"
        unique_email = f"{unique_username}@test.com"
        
        response = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "Test123!",
            "username": unique_username
        })
        if response.status_code != 200:
            pytest.skip(f"Could not create free user: {response.text}")
        return session
    
    def test_city_rankings_requires_premium(self, free_session):
        """GET /api/rankings/cities returns 403 for free users"""
        response = free_session.get(f"{BASE_URL}/api/rankings/cities")
        assert response.status_code == 403
        print("PASS: City rankings returns 403 for free users")
    
    def test_city_rankings_works_for_premium(self, premium_session):
        """GET /api/rankings/cities works for premium users"""
        response = premium_session.get(f"{BASE_URL}/api/rankings/cities")
        assert response.status_code == 200
        data = response.json()
        assert "dirtiest" in data or "cleanest" in data or isinstance(data, list)
        print("PASS: City rankings works for premium users")
    
    def test_barrio_rankings_requires_premium(self, free_session):
        """GET /api/rankings/barrios?city=Madrid returns 403 for free users"""
        response = free_session.get(f"{BASE_URL}/api/rankings/barrios?city=Madrid")
        assert response.status_code == 403
        print("PASS: Barrio rankings returns 403 for free users")
    
    def test_barrio_rankings_works_for_premium(self, premium_session):
        """GET /api/rankings/barrios?city=Madrid works for premium users"""
        response = premium_session.get(f"{BASE_URL}/api/rankings/barrios?city=Madrid")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
        print("PASS: Barrio rankings works for premium users")
    
    def test_city_rankings_share_is_public(self):
        """GET /api/rankings/cities/share is public (no auth required)"""
        response = requests.get(f"{BASE_URL}/api/rankings/cities/share")
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "cities" in data
        assert "download_links" in data
        assert "share_text" in data
        print("PASS: City rankings share endpoint is public")


class TestNotificationsEndpoint:
    """Test notifications endpoint"""
    
    def test_notifications_requires_auth(self):
        """GET /api/notifications returns 401 for unauthenticated users"""
        response = requests.get(f"{BASE_URL}/api/notifications")
        assert response.status_code == 401
        print("PASS: Notifications requires authentication")
    
    def test_notifications_returns_list(self):
        """GET /api/notifications returns list for authenticated user"""
        session = requests.Session()
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200
        
        response = session.get(f"{BASE_URL}/api/notifications")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print("PASS: Notifications returns list for authenticated user")


class TestMunicipalitySubscription:
    """Test municipality subscription endpoint"""
    
    def test_municipality_subscribe_returns_50_euros(self):
        """POST /api/municipality/subscribe returns €50/mes price"""
        session = requests.Session()
        
        # Login as municipality user
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MUNICIPALITY_EMAIL,
            "password": MUNICIPALITY_PASSWORD
        })
        assert login_response.status_code == 200
        
        # Subscribe
        response = session.post(f"{BASE_URL}/api/municipality/subscribe", json={})
        assert response.status_code == 200
        data = response.json()
        
        # Check price is €50/mes
        assert data.get("price") == "€50/mes" or "50" in str(data.get("price", ""))
        assert data.get("plan") == "monthly"
        print(f"PASS: Municipality subscription returns €50/mes - got: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
