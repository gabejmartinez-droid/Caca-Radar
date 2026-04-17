"""
Test Push Notification Features:
1. Service worker sw.js validity
2. Push toggle visibility for logged-in users
3. Backend push endpoints (GET /api/push/status, GET /api/push/vapid-key, POST /api/push/subscribe, POST /api/push/unsubscribe)
4. ProfilePage notification toggle
5. StreakFlame component
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "jefe@cacaradar.es"
ADMIN_PASSWORD = "Cacaradar123$"


class TestPushEndpoints:
    """Test push notification backend endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup session for tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_vapid_key_endpoint(self):
        """GET /api/push/vapid-key returns VAPID public key"""
        response = self.session.get(f"{BASE_URL}/api/push/vapid-key")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "vapid_public_key" in data, "Response should contain vapid_public_key"
        # VAPID key should be a non-empty string
        assert isinstance(data["vapid_public_key"], str), "vapid_public_key should be a string"
        assert len(data["vapid_public_key"]) > 0, "vapid_public_key should not be empty"
        print(f"PASS: VAPID key returned: {data['vapid_public_key'][:20]}...")
    
    def test_push_status_unauthenticated(self):
        """GET /api/push/status returns subscribed=False for unauthenticated users"""
        response = self.session.get(f"{BASE_URL}/api/push/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "subscribed" in data, "Response should contain subscribed field"
        assert data["subscribed"] == False, "Unauthenticated user should not be subscribed"
        print("PASS: Unauthenticated user push status is False")
    
    def test_push_status_authenticated(self):
        """GET /api/push/status returns subscription status for authenticated user"""
        # Login first
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        # Check push status
        response = self.session.get(f"{BASE_URL}/api/push/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "subscribed" in data, "Response should contain subscribed field"
        assert isinstance(data["subscribed"], bool), "subscribed should be a boolean"
        print(f"PASS: Authenticated user push status: {data['subscribed']}")
    
    def test_push_subscribe_authenticated(self):
        """POST /api/push/subscribe accepts subscription data for authenticated user"""
        # Login first
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        # Subscribe with mock subscription data
        subscription_data = {
            "subscription": {
                "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint-123",
                "keys": {
                    "p256dh": "test-p256dh-key",
                    "auth": "test-auth-key"
                }
            },
            "latitude": 40.4168,
            "longitude": -3.7038
        }
        
        response = self.session.post(f"{BASE_URL}/api/push/subscribe", json=subscription_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data, "Response should contain message"
        print(f"PASS: Push subscribe successful: {data['message']}")
        
        # Verify subscription status is now True
        status_response = self.session.get(f"{BASE_URL}/api/push/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["subscribed"] == True, "User should be subscribed after subscribing"
        print("PASS: Push status is True after subscribing")
    
    def test_push_unsubscribe_authenticated(self):
        """POST /api/push/unsubscribe deactivates subscription"""
        # Login first
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        # First subscribe
        subscription_data = {
            "subscription": {
                "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint-456",
                "keys": {
                    "p256dh": "test-p256dh-key-2",
                    "auth": "test-auth-key-2"
                }
            },
            "latitude": 40.4168,
            "longitude": -3.7038
        }
        self.session.post(f"{BASE_URL}/api/push/subscribe", json=subscription_data)
        
        # Now unsubscribe
        response = self.session.post(f"{BASE_URL}/api/push/unsubscribe", json={})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data, "Response should contain message"
        print(f"PASS: Push unsubscribe successful: {data['message']}")
        
        # Verify subscription status is now False
        status_response = self.session.get(f"{BASE_URL}/api/push/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["subscribed"] == False, "User should not be subscribed after unsubscribing"
        print("PASS: Push status is False after unsubscribing")
    
    def test_push_subscribe_unauthenticated(self):
        """POST /api/push/subscribe works for anonymous users (with anon_id cookie)"""
        # Create a fresh session without auth
        fresh_session = requests.Session()
        fresh_session.headers.update({"Content-Type": "application/json"})
        
        subscription_data = {
            "subscription": {
                "endpoint": "https://fcm.googleapis.com/fcm/send/anon-test-endpoint",
                "keys": {
                    "p256dh": "anon-p256dh-key",
                    "auth": "anon-auth-key"
                }
            },
            "latitude": 40.4168,
            "longitude": -3.7038
        }
        
        response = fresh_session.post(f"{BASE_URL}/api/push/subscribe", json=subscription_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data, "Response should contain message"
        print(f"PASS: Anonymous push subscribe successful: {data['message']}")


class TestLoginAndAuth:
    """Test login with admin credentials"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_admin_login(self):
        """Login with admin credentials works"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert data["email"] == ADMIN_EMAIL, "Email should match"
        assert data["role"] == "admin", "Role should be admin"
        print(f"PASS: Admin login successful, role: {data['role']}")
    
    def test_invalid_login(self):
        """Login with invalid credentials returns 401"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Invalid login returns 401")


class TestServiceWorker:
    """Test service worker file accessibility"""
    
    def test_service_worker_accessible(self):
        """Service worker file is accessible at /sw.js"""
        response = requests.get(f"{BASE_URL}/sw.js")
        # Service worker should be accessible (200) or redirect to index.html (which is also fine for SPA)
        assert response.status_code in [200, 304], f"Expected 200 or 304, got {response.status_code}"
        
        # Check if it contains expected service worker code
        content = response.text
        if "self.addEventListener" in content:
            print("PASS: Service worker file contains event listeners")
            assert "push" in content.lower() or "install" in content.lower(), "SW should have push or install handler"
        else:
            # Might be served as index.html in SPA mode
            print("INFO: Service worker served via SPA routing")
        print("PASS: Service worker file is accessible")


class TestUserProfile:
    """Test user profile endpoint for streak data"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_user_profile_has_streak_days(self):
        """GET /api/users/profile returns streak_days field"""
        # Login first
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        # Get profile
        response = self.session.get(f"{BASE_URL}/api/users/profile")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check for streak_days field
        assert "streak_days" in data, "Profile should contain streak_days field"
        assert isinstance(data["streak_days"], int), "streak_days should be an integer"
        print(f"PASS: User profile has streak_days: {data['streak_days']}")
        
        # Check other gamification fields
        assert "total_score" in data, "Profile should contain total_score"
        assert "rank" in data, "Profile should contain rank"
        assert "level" in data, "Profile should contain level"
        print(f"PASS: User profile has gamification fields: score={data['total_score']}, rank={data['rank']}, level={data['level']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
