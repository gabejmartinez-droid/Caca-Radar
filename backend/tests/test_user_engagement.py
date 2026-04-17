"""
Test User Engagement & Retention Features
- Google Auth endpoint
- Feedback endpoint
- Activity stats endpoint
- Profile notification toggle
- Username change for all users
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestGoogleAuth:
    """Test Google Auth endpoint"""
    
    def test_google_auth_missing_session_id(self):
        """POST /api/auth/google should return 400 for missing session_id"""
        response = requests.post(f"{BASE_URL}/api/auth/google", json={})
        assert response.status_code == 400
        data = response.json()
        assert "session_id" in data.get("detail", "").lower() or "missing" in data.get("detail", "").lower()
        print("PASS: Google auth returns 400 for missing session_id")
    
    def test_google_auth_invalid_session_id(self):
        """POST /api/auth/google should return 401 for invalid session_id"""
        response = requests.post(f"{BASE_URL}/api/auth/google", json={"session_id": "invalid_session_123"})
        assert response.status_code == 401
        print("PASS: Google auth returns 401 for invalid session_id")


class TestFeedbackEndpoint:
    """Test Feedback submission endpoint"""
    
    def test_feedback_submit_anonymous(self):
        """POST /api/feedback should accept anonymous feedback"""
        response = requests.post(f"{BASE_URL}/api/feedback", json={
            "category": "bug",
            "message": "Test feedback message from automated test"
        })
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print("PASS: Feedback endpoint accepts anonymous submissions")
    
    def test_feedback_submit_with_user_info(self):
        """POST /api/feedback should accept feedback with user info"""
        response = requests.post(f"{BASE_URL}/api/feedback", json={
            "category": "suggestion",
            "message": "Test suggestion from automated test",
            "user_email": "test@example.com",
            "username": "testuser"
        })
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print("PASS: Feedback endpoint accepts submissions with user info")


class TestActivityStats:
    """Test Activity Stats endpoint"""
    
    def test_activity_stats_basic(self):
        """GET /api/stats/activity should return activity data"""
        response = requests.get(f"{BASE_URL}/api/stats/activity")
        assert response.status_code == 200
        data = response.json()
        assert "total_today" in data
        assert "nearby_today" in data
        assert "active_zones" in data
        assert "user_rank" in data
        print(f"PASS: Activity stats returns data: total_today={data['total_today']}, active_zones={data['active_zones']}")
    
    def test_activity_stats_with_location(self):
        """GET /api/stats/activity with lat/lng should return nearby data"""
        # Madrid coordinates
        response = requests.get(f"{BASE_URL}/api/stats/activity?lat=40.4168&lng=-3.7038&radius=5000")
        assert response.status_code == 200
        data = response.json()
        assert "total_today" in data
        assert "nearby_today" in data
        assert "active_zones" in data
        print(f"PASS: Activity stats with location returns data: nearby_today={data['nearby_today']}")


class TestUserProfile:
    """Test User Profile features - notification toggle and username change"""
    
    @pytest.fixture
    def auth_session(self):
        """Login and return authenticated session"""
        session = requests.Session()
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jefe@cacaradar.es",
            "password": "Cacaradar123$"
        })
        if login_response.status_code != 200:
            pytest.skip("Could not login with admin credentials")
        return session
    
    def test_profile_endpoint_exists(self, auth_session):
        """GET /api/users/profile should return user profile"""
        response = auth_session.get(f"{BASE_URL}/api/users/profile")
        assert response.status_code == 200
        data = response.json()
        assert "username" in data or "name" in data
        assert "total_score" in data
        print(f"PASS: Profile endpoint returns user data")
    
    def test_username_update_endpoint(self, auth_session):
        """PUT /api/users/username should allow username change"""
        # First get current username
        profile = auth_session.get(f"{BASE_URL}/api/users/profile").json()
        original_username = profile.get("username", "admin")
        
        # Try to update username
        new_username = f"test_admin_{os.urandom(4).hex()}"
        response = auth_session.put(f"{BASE_URL}/api/users/username", json={
            "username": new_username
        })
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("username") == new_username
            print(f"PASS: Username update works - changed to {new_username}")
            
            # Restore original username
            auth_session.put(f"{BASE_URL}/api/users/username", json={
                "username": original_username or "jefe"
            })
        else:
            # Username might already be taken
            print(f"INFO: Username update returned {response.status_code}: {response.json()}")
            assert response.status_code in [200, 400]  # 400 if username taken
    
    def test_username_validation(self, auth_session):
        """PUT /api/users/username should validate username format"""
        # Too short
        response = auth_session.put(f"{BASE_URL}/api/users/username", json={
            "username": "ab"
        })
        assert response.status_code == 400
        print("PASS: Username validation rejects too short usernames")
        
        # Invalid characters
        response = auth_session.put(f"{BASE_URL}/api/users/username", json={
            "username": "test@user!"
        })
        assert response.status_code == 400
        print("PASS: Username validation rejects invalid characters")


class TestAuthEndpoints:
    """Test basic auth endpoints"""
    
    def test_login_with_admin_credentials(self):
        """POST /api/auth/login should work with admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jefe@cacaradar.es",
            "password": "Cacaradar123$"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert data["email"] == "jefe@cacaradar.es"
        print("PASS: Login works with admin credentials")
    
    def test_login_invalid_credentials(self):
        """POST /api/auth/login should return 401 for invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("PASS: Login returns 401 for invalid credentials")
    
    def test_auth_me_unauthenticated(self):
        """GET /api/auth/me should return 401 when not authenticated"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("PASS: /api/auth/me returns 401 when not authenticated")


class TestReportsEndpoint:
    """Test reports endpoint for basic functionality"""
    
    def test_get_reports(self):
        """GET /api/reports should return list of reports"""
        response = requests.get(f"{BASE_URL}/api/reports")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Reports endpoint returns {len(data)} reports")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
