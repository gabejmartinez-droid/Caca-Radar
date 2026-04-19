"""
Test Capacitor Bearer Token Authentication
==========================================
Tests the dual-auth architecture for mobile Capacitor apps:
- Web: Uses cookies (httponly, secure, samesite=none)
- Capacitor Native: Uses Bearer token in Authorization header

The Emergent proxy ALWAYS returns access-control-allow-origin: *
which breaks cookie-based auth for cross-origin requests.
Solution: Bearer token auth with withCredentials=false for Capacitor.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "jefe@cacaradar.es"
ADMIN_PASSWORD = "Cacaradar123$"

# Simulate Capacitor native by sending Origin header
CAPACITOR_HEADERS = {
    "Content-Type": "application/json",
    "Origin": "capacitor://localhost"
}


class TestLoginReturnsTokens:
    """Test that login returns access_token and refresh_token in JSON body"""
    
    def test_login_returns_access_token_in_body(self):
        """POST /api/auth/login should return access_token in JSON response"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers=CAPACITOR_HEADERS
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Response missing access_token"
        assert isinstance(data["access_token"], str), "access_token should be string"
        assert len(data["access_token"]) > 50, "access_token seems too short"
        print(f"✓ Login returns access_token in body (length: {len(data['access_token'])})")
    
    def test_login_returns_refresh_token_in_body(self):
        """POST /api/auth/login should return refresh_token in JSON response"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers=CAPACITOR_HEADERS
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "refresh_token" in data, "Response missing refresh_token"
        assert isinstance(data["refresh_token"], str), "refresh_token should be string"
        assert len(data["refresh_token"]) > 50, "refresh_token seems too short"
        print(f"✓ Login returns refresh_token in body (length: {len(data['refresh_token'])})")
    
    def test_login_returns_user_data(self):
        """POST /api/auth/login should return user data along with tokens"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers=CAPACITOR_HEADERS
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data, "Response missing user id"
        assert "email" in data, "Response missing email"
        assert data["email"] == ADMIN_EMAIL, f"Email mismatch: {data['email']}"
        print(f"✓ Login returns user data: id={data['id']}, email={data['email']}")


class TestBearerTokenAuth:
    """Test Bearer token authentication on protected endpoints"""
    
    @pytest.fixture
    def access_token(self):
        """Get access token via login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers=CAPACITOR_HEADERS
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_auth_me_with_bearer_token(self, access_token):
        """GET /api/auth/me should work with Bearer token (no cookies)"""
        headers = {
            **CAPACITOR_HEADERS,
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        assert response.status_code == 200, f"Auth/me failed: {response.text}"
        data = response.json()
        assert "email" in data, "Response missing email"
        assert data["email"] == ADMIN_EMAIL, f"Email mismatch: {data['email']}"
        print(f"✓ GET /api/auth/me works with Bearer token: {data['email']}")
    
    def test_auth_me_without_token_returns_401(self):
        """GET /api/auth/me without token should return 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=CAPACITOR_HEADERS)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /api/auth/me returns 401 without token")
    
    def test_users_profile_with_bearer_token(self, access_token):
        """GET /api/users/profile should work with Bearer token"""
        headers = {
            **CAPACITOR_HEADERS,
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(f"{BASE_URL}/api/users/profile", headers=headers)
        
        assert response.status_code == 200, f"Profile failed: {response.text}"
        data = response.json()
        assert "username" in data or "name" in data, "Response missing user info"
        print(f"✓ GET /api/users/profile works with Bearer token")
    
    def test_users_impact_with_bearer_token(self, access_token):
        """GET /api/users/impact should work with Bearer token"""
        headers = {
            **CAPACITOR_HEADERS,
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(f"{BASE_URL}/api/users/impact", headers=headers)
        
        assert response.status_code == 200, f"Impact failed: {response.text}"
        data = response.json()
        assert "stats" in data, "Response missing stats"
        assert "username" in data, "Response missing username"
        print(f"✓ GET /api/users/impact works with Bearer token: username={data['username']}")
    
    def test_reports_endpoint_works(self, access_token):
        """GET /api/reports should work (public endpoint)"""
        headers = {
            **CAPACITOR_HEADERS,
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(f"{BASE_URL}/api/reports", headers=headers)
        
        assert response.status_code == 200, f"Reports failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Reports should return a list"
        print(f"✓ GET /api/reports works: {len(data)} reports")


class TestTokenRefresh:
    """Test token refresh via POST body (not cookies)"""
    
    @pytest.fixture
    def tokens(self):
        """Get both tokens via login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers=CAPACITOR_HEADERS
        )
        assert response.status_code == 200
        data = response.json()
        return {
            "access_token": data["access_token"],
            "refresh_token": data["refresh_token"]
        }
    
    def test_refresh_with_body_token(self, tokens):
        """POST /api/auth/refresh with refresh_token in body should work"""
        response = requests.post(
            f"{BASE_URL}/api/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
            headers=CAPACITOR_HEADERS
        )
        
        assert response.status_code == 200, f"Refresh failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Response missing new access_token"
        assert len(data["access_token"]) > 50, "New access_token seems too short"
        print(f"✓ Token refresh via body works: new token length={len(data['access_token'])}")
    
    def test_refresh_without_token_returns_401(self):
        """POST /api/auth/refresh without token should return 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/refresh",
            json={},
            headers=CAPACITOR_HEADERS
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Token refresh without token returns 401")
    
    def test_new_access_token_works(self, tokens):
        """New access token from refresh should work on protected endpoints"""
        # Get new access token
        refresh_response = requests.post(
            f"{BASE_URL}/api/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
            headers=CAPACITOR_HEADERS
        )
        assert refresh_response.status_code == 200
        new_access_token = refresh_response.json()["access_token"]
        
        # Use new token on /api/auth/me
        headers = {
            **CAPACITOR_HEADERS,
            "Authorization": f"Bearer {new_access_token}"
        }
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        assert me_response.status_code == 200, f"Auth/me with new token failed: {me_response.text}"
        print("✓ New access token from refresh works on protected endpoints")


class TestRegisterReturnsTokens:
    """Test that register returns access_token and refresh_token in JSON body"""
    
    def test_register_returns_tokens(self):
        """POST /api/auth/register should return tokens in JSON response"""
        import uuid
        test_email = f"test_capacitor_{uuid.uuid4().hex[:8]}@test.com"
        test_username = f"test_{uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": test_email,
                "password": "TestPass123!",
                "username": test_username
            },
            headers=CAPACITOR_HEADERS
        )
        
        assert response.status_code == 200, f"Register failed: {response.text}"
        data = response.json()
        
        assert "access_token" in data, "Response missing access_token"
        assert "refresh_token" in data, "Response missing refresh_token"
        assert isinstance(data["access_token"], str), "access_token should be string"
        assert isinstance(data["refresh_token"], str), "refresh_token should be string"
        assert len(data["access_token"]) > 50, "access_token seems too short"
        assert len(data["refresh_token"]) > 50, "refresh_token seems too short"
        
        print(f"✓ Register returns tokens: access={len(data['access_token'])} chars, refresh={len(data['refresh_token'])} chars")
        
        # Verify the new token works
        headers = {
            **CAPACITOR_HEADERS,
            "Authorization": f"Bearer {data['access_token']}"
        }
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert me_response.status_code == 200, "New user token doesn't work"
        print(f"✓ New user's access token works on /api/auth/me")


class TestGoogleAuthReturnsTokens:
    """Test that Google Auth login endpoint exists"""
    
    def test_google_auth_endpoint_exists(self):
        """POST /api/auth/google/login endpoint should exist"""
        response = requests.post(
            f"{BASE_URL}/api/auth/google/login",
            json={"credential": "invalid_google_credential"},
            headers=CAPACITOR_HEADERS
        )
        # Should return 401 (invalid credential) not 404 (endpoint not found)
        assert response.status_code in [400, 401], f"Unexpected status: {response.status_code}"
        print(f"✓ POST /api/auth/google/login endpoint exists (returns {response.status_code} for invalid credential)")


class TestCORSWithCapacitorOrigin:
    """Test that CORS works with capacitor://localhost origin"""
    
    def test_cors_allows_capacitor_origin(self):
        """OPTIONS preflight should allow capacitor://localhost"""
        response = requests.options(
            f"{BASE_URL}/api/auth/login",
            headers={
                "Origin": "capacitor://localhost",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization"
            }
        )
        # The Emergent proxy returns access-control-allow-origin: * for all requests
        # This is fine because we use withCredentials=false for Capacitor
        assert response.status_code in [200, 204], f"CORS preflight failed: {response.status_code}"
        print(f"✓ CORS preflight works for capacitor://localhost")
    
    def test_login_works_with_capacitor_origin(self):
        """Login should work with capacitor://localhost origin"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers=CAPACITOR_HEADERS
        )
        assert response.status_code == 200, f"Login with Capacitor origin failed: {response.text}"
        print("✓ Login works with capacitor://localhost origin")


class TestAllProtectedEndpointsWithBearer:
    """Test all protected endpoints work with Bearer token"""
    
    @pytest.fixture
    def access_token(self):
        """Get access token via login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers=CAPACITOR_HEADERS
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_notifications_endpoint(self, access_token):
        """GET /api/notifications should work with Bearer token"""
        headers = {
            **CAPACITOR_HEADERS,
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(f"{BASE_URL}/api/notifications", headers=headers)
        assert response.status_code == 200, f"Notifications failed: {response.text}"
        print("✓ GET /api/notifications works with Bearer token")
    
    def test_subscription_status_endpoint(self, access_token):
        """GET /api/users/subscription-status should work with Bearer token"""
        headers = {
            **CAPACITOR_HEADERS,
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(f"{BASE_URL}/api/users/subscription-status", headers=headers)
        assert response.status_code == 200, f"Subscription status failed: {response.text}"
        data = response.json()
        assert "active" in data, "Response missing 'active' field"
        print(f"✓ GET /api/users/subscription-status works: active={data['active']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
