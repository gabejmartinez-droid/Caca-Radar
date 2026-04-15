"""
Admin 2FA Login and Dashboard Tests
Tests for:
- POST /api/admin/login (step 1: credentials, sends verification code)
- POST /api/admin/verify (step 2: verify code, get session)
- GET /api/admin/dashboard (platform stats)
- GET /api/admin/users (paginated user list)
- GET /api/admin/photo-violations (pending photo violations)
- POST /api/admin/moderate/{report_id} (hide/dismiss reports)
"""
import pytest
import requests
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

# Admin credentials from test_credentials.md
ADMIN_EMAIL = "jefe@cacaradar.es"
ADMIN_PASSWORD = "Cacaradar123$"

# Free user (should get 403 on admin endpoints)
FREE_USER_EMAIL = "corstest@test.com"
FREE_USER_PASSWORD = "Test123!"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def mongo_client():
    """MongoDB client for reading 2FA codes"""
    client = AsyncIOMotorClient(MONGO_URL)
    yield client
    client.close()


def get_admin_code_from_db():
    """Synchronously get the admin 2FA code from MongoDB"""
    import asyncio
    
    async def _get_code():
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        record = await db.admin_codes.find_one({"email": ADMIN_EMAIL})
        client.close()
        return record.get("code") if record else None
    
    return asyncio.get_event_loop().run_until_complete(_get_code())


class TestAdminLoginStep1:
    """Test POST /api/admin/login - Step 1: Credentials validation"""
    
    def test_admin_login_wrong_credentials_returns_401(self, api_client):
        """Wrong credentials should return 401"""
        response = api_client.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data
        print(f"✓ Wrong credentials returns 401: {data['detail']}")
    
    def test_admin_login_non_admin_user_returns_401(self, api_client):
        """Non-admin user should return 401"""
        response = api_client.post(f"{BASE_URL}/api/admin/login", json={
            "email": FREE_USER_EMAIL,
            "password": FREE_USER_PASSWORD
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print("✓ Non-admin user returns 401")
    
    def test_admin_login_correct_credentials_sends_code(self, api_client):
        """Correct credentials should send verification code and return success"""
        response = api_client.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        assert data.get("email_sent") == True
        print(f"✓ Correct credentials sends code: {data['message']}")
        
        # Verify code was stored in DB
        code = get_admin_code_from_db()
        assert code is not None, "2FA code should be stored in admin_codes collection"
        assert len(code) == 6, f"Code should be 6 digits, got: {code}"
        print(f"✓ 2FA code stored in DB: {code}")


class TestAdminLoginStep2:
    """Test POST /api/admin/verify - Step 2: Code verification"""
    
    def test_admin_verify_wrong_code_returns_400(self, api_client):
        """Wrong code should return 400"""
        # First, trigger step 1 to ensure there's a code
        api_client.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        response = api_client.post(f"{BASE_URL}/api/admin/verify", json={
            "email": ADMIN_EMAIL,
            "code": "000000"  # Wrong code
        })
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data
        print(f"✓ Wrong code returns 400: {data['detail']}")
    
    def test_admin_verify_no_pending_code_returns_400(self, api_client):
        """No pending code should return 400"""
        # Use a different email that has no pending code
        response = api_client.post(f"{BASE_URL}/api/admin/verify", json={
            "email": "nonexistent@cacaradar.es",
            "code": "123456"
        })
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ No pending code returns 400")
    
    def test_admin_verify_correct_code_sets_cookies(self, api_client):
        """Correct code should set session cookies and return role=admin"""
        # Step 1: Get a fresh code
        step1_response = api_client.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert step1_response.status_code == 200
        
        # Get the code from DB
        code = get_admin_code_from_db()
        assert code is not None, "Code should exist after step 1"
        
        # Step 2: Verify with correct code
        response = api_client.post(f"{BASE_URL}/api/admin/verify", json={
            "email": ADMIN_EMAIL,
            "code": code
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("role") == "admin", f"Expected role=admin, got: {data}"
        
        # Check cookies were set
        cookies = response.cookies
        assert "access_token" in cookies or "access_token" in api_client.cookies, "access_token cookie should be set"
        print(f"✓ Correct code sets cookies and returns role=admin")


class TestAdminDashboard:
    """Test GET /api/admin/dashboard - Platform stats"""
    
    @pytest.fixture(autouse=True)
    def setup_admin_session(self, api_client):
        """Authenticate as admin before each test"""
        # Step 1
        api_client.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        # Step 2
        code = get_admin_code_from_db()
        if code:
            api_client.post(f"{BASE_URL}/api/admin/verify", json={
                "email": ADMIN_EMAIL,
                "code": code
            })
    
    def test_admin_dashboard_returns_stats(self, api_client):
        """Admin dashboard should return full platform stats"""
        response = api_client.get(f"{BASE_URL}/api/admin/dashboard")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Check users section
        assert "users" in data
        assert "total" in data["users"]
        assert "premium" in data["users"]
        assert "free" in data["users"]
        assert "conversion_rate" in data["users"]
        assert "new_7d" in data["users"]
        assert "new_30d" in data["users"]
        
        # Check subscriptions section
        assert "subscriptions" in data
        assert "monthly" in data["subscriptions"]
        assert "annual" in data["subscriptions"]
        assert "municipality_active" in data["subscriptions"]
        assert "municipality_total" in data["subscriptions"]
        assert "est_monthly_revenue" in data["subscriptions"]
        
        # Check reports section
        assert "reports" in data
        assert "total" in data["reports"]
        assert "active" in data["reports"]
        assert "flagged" in data["reports"]
        assert "last_7d" in data["reports"]
        assert "last_30d" in data["reports"]
        
        print(f"✓ Dashboard returns full stats: {data['users']['total']} users, {data['reports']['total']} reports")
    
    def test_admin_dashboard_returns_403_for_non_admin(self, api_client):
        """Non-admin user should get 403"""
        # Login as free user
        api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": FREE_USER_EMAIL,
            "password": FREE_USER_PASSWORD
        })
        
        response = api_client.get(f"{BASE_URL}/api/admin/dashboard")
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✓ Non-admin user gets 403 on dashboard")


class TestAdminUsers:
    """Test GET /api/admin/users - Paginated user list"""
    
    @pytest.fixture(autouse=True)
    def setup_admin_session(self, api_client):
        """Authenticate as admin before each test"""
        api_client.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        code = get_admin_code_from_db()
        if code:
            api_client.post(f"{BASE_URL}/api/admin/verify", json={
                "email": ADMIN_EMAIL,
                "code": code
            })
    
    def test_admin_users_returns_paginated_list(self, api_client):
        """Admin users endpoint should return paginated user list"""
        response = api_client.get(f"{BASE_URL}/api/admin/users?skip=0&limit=20")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert isinstance(data["users"], list)
        print(f"✓ Users endpoint returns {len(data['users'])} users, total: {data['total']}")
    
    def test_admin_users_search_works(self, api_client):
        """Search parameter should filter users"""
        response = api_client.get(f"{BASE_URL}/api/admin/users?search=test")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "users" in data
        print(f"✓ Search returns {len(data['users'])} users matching 'test'")


class TestAdminPhotoViolations:
    """Test GET /api/admin/photo-violations - Pending photo violations"""
    
    @pytest.fixture(autouse=True)
    def setup_admin_session(self, api_client):
        """Authenticate as admin before each test"""
        api_client.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        code = get_admin_code_from_db()
        if code:
            api_client.post(f"{BASE_URL}/api/admin/verify", json={
                "email": ADMIN_EMAIL,
                "code": code
            })
    
    def test_admin_photo_violations_returns_list(self, api_client):
        """Photo violations endpoint should return list"""
        response = api_client.get(f"{BASE_URL}/api/admin/photo-violations")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "violations" in data
        assert "total" in data
        assert isinstance(data["violations"], list)
        print(f"✓ Photo violations returns {data['total']} pending violations")


class TestAdminModerate:
    """Test POST /api/admin/moderate/{report_id} - Moderation actions"""
    
    @pytest.fixture(autouse=True)
    def setup_admin_session(self, api_client):
        """Authenticate as admin before each test"""
        api_client.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        code = get_admin_code_from_db()
        if code:
            api_client.post(f"{BASE_URL}/api/admin/verify", json={
                "email": ADMIN_EMAIL,
                "code": code
            })
    
    def test_admin_moderate_nonexistent_report_returns_404(self, api_client):
        """Moderating nonexistent report should return 404"""
        response = api_client.post(
            f"{BASE_URL}/api/admin/moderate/nonexistent-report-id",
            json={"action": "hide"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print("✓ Nonexistent report returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
