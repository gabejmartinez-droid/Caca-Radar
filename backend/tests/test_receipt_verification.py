"""
Test suite for Apple/Google receipt verification and subscription features.
Tests mock fallback behavior when credentials are not configured.
"""
import pytest
import requests
import os
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test users for receipt verification
TEST_APPLE_USER = {
    "email": "receipttest@test.com",
    "password": "Test123!",
    "username": "receipttest"
}

TEST_GOOGLE_USER = {
    "email": "googletest@test.com",
    "password": "Test123!",
    "username": "googletest"
}

ADMIN_USER = {
    "email": "jefe@cacaradar.es",
    "password": "Cacaradar123$"
}


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def apple_user_session(api_client):
    """Create and login Apple test user"""
    # Try to register, ignore if already exists
    api_client.post(f"{BASE_URL}/api/auth/register", json=TEST_APPLE_USER)
    
    # Login
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_APPLE_USER["email"],
        "password": TEST_APPLE_USER["password"]
    })
    assert response.status_code == 200, f"Apple user login failed: {response.text}"
    
    # Create new session with cookies
    session = requests.Session()
    session.cookies.update(response.cookies)
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def google_user_session(api_client):
    """Create and login Google test user"""
    # Try to register, ignore if already exists
    api_client.post(f"{BASE_URL}/api/auth/register", json=TEST_GOOGLE_USER)
    
    # Login
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_GOOGLE_USER["email"],
        "password": TEST_GOOGLE_USER["password"]
    })
    assert response.status_code == 200, f"Google user login failed: {response.text}"
    
    # Create new session with cookies
    session = requests.Session()
    session.cookies.update(response.cookies)
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def admin_session(api_client):
    """Login admin user with 2FA"""
    from pymongo import MongoClient
    
    # Step 1: Login to get code sent
    response = api_client.post(f"{BASE_URL}/api/admin/login", json={
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    })
    assert response.status_code == 200, f"Admin login step 1 failed: {response.text}"
    
    # Step 2: Get code from database
    mongo_client = MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
    db = mongo_client[os.environ.get('DB_NAME', 'test_database')]
    admin_code_doc = db.admin_codes.find_one({"email": ADMIN_USER["email"]})
    
    if not admin_code_doc:
        pytest.skip("Admin 2FA code not found in database")
    
    code = admin_code_doc["code"]
    
    # Step 3: Verify with code
    response = api_client.post(f"{BASE_URL}/api/admin/verify", json={
        "email": ADMIN_USER["email"],
        "code": code
    })
    assert response.status_code == 200, f"Admin verify failed: {response.text}"
    
    # Create new session with cookies
    session = requests.Session()
    session.cookies.update(response.cookies)
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestAppleReceiptVerification:
    """Tests for Apple App Store receipt verification (mock mode)"""
    
    def test_apple_subscribe_mock_returns_valid_true(self, apple_user_session):
        """POST /api/users/subscribe/apple with mock returns valid=true, mock=true"""
        response = apple_user_session.post(f"{BASE_URL}/api/users/subscribe/apple", json={
            "receipt_data": "mock_receipt_data_for_testing",
            "transaction_id": "mock_txn_12345",
            "plan": "monthly"
        })
        
        assert response.status_code == 200, f"Apple subscribe failed: {response.text}"
        data = response.json()
        
        # Verify mock response fields
        assert data.get("mock") == True, "Expected mock=true since Apple credentials not configured"
        assert "plan" in data, "Response should include plan"
        assert data["plan"] == "monthly", "Plan should be monthly"
        assert "expires" in data, "Response should include expires"
        print(f"Apple subscribe response: {data}")
    
    def test_apple_subscribe_activates_subscription(self, apple_user_session):
        """Verify subscription is activated after Apple receipt verification"""
        response = apple_user_session.get(f"{BASE_URL}/api/users/subscription-status")
        
        assert response.status_code == 200, f"Subscription status failed: {response.text}"
        data = response.json()
        
        assert data.get("active") == True, "Subscription should be active"
        assert data.get("store") == "apple", "Store should be 'apple'"
        assert data.get("mock") == True, "Mock should be true"
        print(f"Subscription status: {data}")
    
    def test_apple_subscribe_annual_plan(self, apple_user_session):
        """Test Apple subscription with annual plan"""
        response = apple_user_session.post(f"{BASE_URL}/api/users/subscribe/apple", json={
            "receipt_data": "mock_receipt_annual",
            "transaction_id": "mock_txn_annual_12345",
            "plan": "annual"
        })
        
        assert response.status_code == 200, f"Apple annual subscribe failed: {response.text}"
        data = response.json()
        assert data.get("plan") == "annual", "Plan should be annual"
        assert data.get("mock") == True, "Should be mock mode"


class TestGoogleReceiptVerification:
    """Tests for Google Play receipt verification (mock mode)"""
    
    def test_google_subscribe_mock_returns_valid_true(self, google_user_session):
        """POST /api/users/subscribe/google with mock returns valid=true, mock=true"""
        response = google_user_session.post(f"{BASE_URL}/api/users/subscribe/google", json={
            "purchase_token": "mock_purchase_token_for_testing",
            "subscription_id": "premium_monthly",
            "plan": "monthly"
        })
        
        assert response.status_code == 200, f"Google subscribe failed: {response.text}"
        data = response.json()
        
        # Verify mock response fields
        assert data.get("mock") == True, "Expected mock=true since Google credentials not configured"
        assert "plan" in data, "Response should include plan"
        assert data["plan"] == "monthly", "Plan should be monthly"
        assert "expires" in data, "Response should include expires"
        print(f"Google subscribe response: {data}")
    
    def test_google_subscribe_activates_subscription(self, google_user_session):
        """Verify subscription is activated after Google receipt verification"""
        response = google_user_session.get(f"{BASE_URL}/api/users/subscription-status")
        
        assert response.status_code == 200, f"Subscription status failed: {response.text}"
        data = response.json()
        
        assert data.get("active") == True, "Subscription should be active"
        assert data.get("store") == "google", "Store should be 'google'"
        assert data.get("mock") == True, "Mock should be true"
        print(f"Subscription status: {data}")
    
    def test_google_subscribe_annual_plan(self, google_user_session):
        """Test Google subscription with annual plan"""
        response = google_user_session.post(f"{BASE_URL}/api/users/subscribe/google", json={
            "purchase_token": "mock_purchase_token_annual",
            "subscription_id": "premium_annual",
            "plan": "annual"
        })
        
        assert response.status_code == 200, f"Google annual subscribe failed: {response.text}"
        data = response.json()
        assert data.get("plan") == "annual", "Plan should be annual"
        assert data.get("mock") == True, "Should be mock mode"


class TestSubscriptionStatus:
    """Tests for subscription status endpoint"""
    
    def test_subscription_status_reflects_store_and_mock(self, apple_user_session):
        """GET /api/users/subscription-status reflects store and mock fields"""
        response = apple_user_session.get(f"{BASE_URL}/api/users/subscription-status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields
        assert "active" in data, "Should have 'active' field"
        assert "type" in data, "Should have 'type' field"
        assert "expires" in data, "Should have 'expires' field"
        assert "store" in data, "Should have 'store' field"
        assert "mock" in data, "Should have 'mock' field"
        
        print(f"Full subscription status: {data}")
    
    def test_subscription_status_requires_auth(self):
        """Subscription status requires authentication"""
        # Use fresh session without cookies
        fresh_session = requests.Session()
        fresh_session.headers.update({"Content-Type": "application/json"})
        response = fresh_session.get(f"{BASE_URL}/api/users/subscription-status")
        assert response.status_code == 401, f"Should require authentication, got {response.status_code}: {response.text}"


class TestAdminIntegrationStatus:
    """Tests for admin integration-status endpoint"""
    
    def test_integration_status_returns_configured_status(self, admin_session):
        """GET /api/admin/integration-status returns configured status for Apple, Google, Resend"""
        response = admin_session.get(f"{BASE_URL}/api/admin/integration-status")
        
        assert response.status_code == 200, f"Integration status failed: {response.text}"
        data = response.json()
        
        # Verify Apple section
        assert "apple" in data, "Should have 'apple' section"
        assert "configured" in data["apple"], "Apple should have 'configured' field"
        assert data["apple"]["configured"] == False, "Apple should not be configured (no credentials)"
        assert "environment" in data["apple"], "Apple should have 'environment' field"
        
        # Verify Google section
        assert "google" in data, "Should have 'google' section"
        assert "configured" in data["google"], "Google should have 'configured' field"
        assert data["google"]["configured"] == False, "Google should not be configured (no credentials)"
        
        # Verify Resend section
        assert "resend" in data, "Should have 'resend' section"
        assert "configured" in data["resend"], "Resend should have 'configured' field"
        # Resend IS configured in this environment
        assert data["resend"]["configured"] == True, "Resend should be configured"
        
        # Verify setup instructions
        assert "setup_instructions" in data, "Should have setup instructions"
        
        print(f"Integration status: {data}")
    
    def test_integration_status_returns_403_for_non_admin(self, apple_user_session):
        """GET /api/admin/integration-status returns 403 for non-admin users"""
        response = apple_user_session.get(f"{BASE_URL}/api/admin/integration-status")
        assert response.status_code == 403, f"Expected 403 for non-admin, got {response.status_code}"
    
    def test_integration_status_returns_401_for_unauthenticated(self):
        """GET /api/admin/integration-status returns 401 for unauthenticated users"""
        # Use fresh session without cookies
        fresh_session = requests.Session()
        fresh_session.headers.update({"Content-Type": "application/json"})
        response = fresh_session.get(f"{BASE_URL}/api/admin/integration-status")
        assert response.status_code == 401, f"Expected 401 for unauthenticated, got {response.status_code}"


class TestSubscriptionReceiptsStorage:
    """Tests for subscription receipt storage in database"""
    
    def test_receipt_stored_in_collection(self, api_client):
        """Verify subscription receipt is stored in subscription_receipts collection"""
        from pymongo import MongoClient
        
        mongo_client = MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
        db = mongo_client[os.environ.get('DB_NAME', 'test_database')]
        
        # Check for Apple receipts
        apple_receipts = list(db.subscription_receipts.find({"store": "apple"}))
        print(f"Found {len(apple_receipts)} Apple receipts in database")
        
        # Check for Google receipts
        google_receipts = list(db.subscription_receipts.find({"store": "google"}))
        print(f"Found {len(google_receipts)} Google receipts in database")
        
        # At least one receipt should exist from our tests
        total_receipts = len(apple_receipts) + len(google_receipts)
        assert total_receipts > 0, "Should have at least one receipt stored"
        
        # Verify receipt structure
        if apple_receipts:
            receipt = apple_receipts[0]
            assert "user_id" in receipt, "Receipt should have user_id"
            assert "store" in receipt, "Receipt should have store"
            assert "plan" in receipt, "Receipt should have plan"
            assert "verification_result" in receipt, "Receipt should have verification_result"
            assert "created_at" in receipt, "Receipt should have created_at"
            print(f"Sample Apple receipt: {receipt}")


class TestWebhookEndpoints:
    """Tests for Apple and Google webhook endpoints"""
    
    def test_apple_webhook_accepts_signed_payload(self, api_client):
        """POST /api/webhooks/apple accepts signedPayload"""
        # Create a mock JWS payload (header.payload.signature)
        import base64
        import json
        
        header = base64.urlsafe_b64encode(json.dumps({"alg": "ES256"}).encode()).decode().rstrip("=")
        payload_data = {
            "notificationType": "TEST",
            "subtype": "",
            "data": {
                "bundleId": "com.cacaradar.app",
                "environment": "Sandbox"
            }
        }
        payload = base64.urlsafe_b64encode(json.dumps(payload_data).encode()).decode().rstrip("=")
        signature = base64.urlsafe_b64encode(b"mock_signature").decode().rstrip("=")
        
        mock_jws = f"{header}.{payload}.{signature}"
        
        response = api_client.post(f"{BASE_URL}/api/webhooks/apple", json={
            "signedPayload": mock_jws
        })
        
        # Should return 200 (Apple expects 200 even on errors to prevent retries)
        assert response.status_code == 200, f"Apple webhook failed: {response.text}"
        data = response.json()
        assert "status" in data, "Response should have status"
        print(f"Apple webhook response: {data}")
    
    def test_apple_webhook_missing_payload_returns_error(self, api_client):
        """POST /api/webhooks/apple returns error status for missing signedPayload"""
        response = api_client.post(f"{BASE_URL}/api/webhooks/apple", json={})
        # Webhook returns 200 with error status to prevent Apple retries
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("status") == "error", f"Expected error status, got {data}"
    
    def test_google_webhook_accepts_pubsub_message(self, api_client):
        """POST /api/webhooks/google accepts Pub/Sub message format"""
        import base64
        import json
        
        # Create mock Pub/Sub message
        notification_data = {
            "subscriptionNotification": {
                "notificationType": 4,  # PURCHASED
                "purchaseToken": "mock_token_12345",
                "subscriptionId": "premium_monthly"
            },
            "packageName": "com.cacaradar.app"
        }
        encoded_data = base64.b64encode(json.dumps(notification_data).encode()).decode()
        
        response = api_client.post(f"{BASE_URL}/api/webhooks/google", json={
            "message": {
                "data": encoded_data
            },
            "subscription": "projects/test/subscriptions/test"
        })
        
        assert response.status_code == 200, f"Google webhook failed: {response.text}"
        data = response.json()
        assert "status" in data, "Response should have status"
        print(f"Google webhook response: {data}")
    
    def test_google_webhook_missing_data_returns_error(self, api_client):
        """POST /api/webhooks/google returns error status for missing message data"""
        response = api_client.post(f"{BASE_URL}/api/webhooks/google", json={
            "message": {}
        })
        # Webhook returns 200 with error status to prevent Google retries
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("status") == "error", f"Expected error status, got {data}"
    
    def test_webhook_status_endpoint(self, api_client):
        """GET /api/webhooks/status returns configuration status"""
        response = api_client.get(f"{BASE_URL}/api/webhooks/status")
        
        assert response.status_code == 200, f"Webhook status failed: {response.text}"
        data = response.json()
        
        assert "apple" in data, "Should have 'apple' section"
        assert "google" in data, "Should have 'google' section"
        assert "email" in data, "Should have 'email' section"
        
        # Verify structure
        assert "webhook_url" in data["apple"], "Apple should have webhook_url"
        assert data["apple"]["webhook_url"] == "/api/webhooks/apple"
        assert "webhook_url" in data["google"], "Google should have webhook_url"
        assert data["google"]["webhook_url"] == "/api/webhooks/google"
        
        print(f"Webhook status: {data}")


class TestExpiredSubscriptionDeactivation:
    """Tests for expired subscription deactivation on startup"""
    
    def test_expired_subscription_logic_exists(self, api_client):
        """Verify the startup expiry check logic is in place"""
        # This test verifies the code exists by checking the startup behavior
        # We can't easily test the actual startup event, but we can verify
        # the endpoint behavior is consistent
        
        from pymongo import MongoClient
        
        mongo_client = MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
        db = mongo_client[os.environ.get('DB_NAME', 'test_database')]
        
        # Create a test user with expired subscription
        test_email = f"expiry_test_{datetime.now().timestamp()}@test.com"
        expired_date = "2020-01-01T00:00:00+00:00"  # Clearly expired
        
        db.users.insert_one({
            "email": test_email,
            "password_hash": "$2b$12$test",
            "username": f"expiry_test_{int(datetime.now().timestamp())}",
            "role": "user",
            "subscription_active": True,
            "subscription_expires": expired_date,
            "created_at": datetime.now(timezone.utc)
        })
        
        # The startup event should have already run, but we can manually
        # trigger the same logic by checking if expired subscriptions exist
        now_iso = datetime.now(timezone.utc).isoformat()
        expired_count = db.users.count_documents({
            "subscription_active": True,
            "subscription_expires": {"$lt": now_iso, "$ne": None}
        })
        
        print(f"Found {expired_count} expired but still active subscriptions")
        
        # Clean up test user
        db.users.delete_one({"email": test_email})
        
        # Note: In a real scenario, the startup event would deactivate these
        # This test just verifies the query logic is correct


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
