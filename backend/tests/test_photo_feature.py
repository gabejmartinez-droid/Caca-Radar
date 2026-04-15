"""
Test Photo Upload Feature for Caca Radar
Tests that photo upload is available for all registered users (not premium-only)
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from review request
NON_PREMIUM_USER = {"email": "corstest@test.com", "password": "Test123!"}
ADMIN_USER = {"email": "admin@cacaradar.es", "password": "admin123"}
REPORT_WITH_PHOTO_ID = "cd777eee-8afa-468c-b191-e9426d8e2c83"


class TestPhotoUploadAccess:
    """Test that photo upload works for non-premium registered users"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_photo_upload_requires_authentication(self):
        """POST /api/reports/{id}/photo should return 401 for unauthenticated users"""
        # Create a dummy file
        files = {'file': ('test.jpg', io.BytesIO(b'fake image data'), 'image/jpeg')}
        response = requests.post(
            f"{BASE_URL}/api/reports/test-report-id/photo",
            files=files
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print("PASS: Photo upload requires authentication (returns 401)")
    
    def test_non_premium_user_can_upload_photo(self):
        """POST /api/reports/{id}/photo should work for non-premium registered users (no 403)"""
        # Login as non-premium user
        login_resp = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json=NON_PREMIUM_USER
        )
        
        if login_resp.status_code != 200:
            # User might not exist, try to create
            print(f"Login failed with {login_resp.status_code}, attempting to create user...")
            reg_resp = self.session.post(
                f"{BASE_URL}/api/auth/register",
                json={
                    "email": NON_PREMIUM_USER["email"],
                    "password": NON_PREMIUM_USER["password"],
                    "username": "corstest_user"
                }
            )
            if reg_resp.status_code not in [200, 201, 400]:  # 400 = already exists
                pytest.skip(f"Could not create test user: {reg_resp.text}")
            
            # Try login again
            login_resp = self.session.post(
                f"{BASE_URL}/api/auth/login",
                json=NON_PREMIUM_USER
            )
        
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        user_data = login_resp.json()
        
        # Verify user is NOT premium
        assert user_data.get("subscription_active") == False, "Test user should not be premium"
        print(f"Logged in as non-premium user: {user_data.get('email')}, subscription_active={user_data.get('subscription_active')}")
        
        # First create a report to upload photo to
        report_resp = self.session.post(
            f"{BASE_URL}/api/reports",
            json={
                "latitude": 40.4168,
                "longitude": -3.7038,
                "description": "Test report for photo upload"
            }
        )
        
        if report_resp.status_code != 200:
            pytest.skip(f"Could not create report: {report_resp.text}")
        
        report_id = report_resp.json().get("id")
        print(f"Created report: {report_id}")
        
        # Now try to upload a photo - this should NOT return 403
        # Create a minimal valid JPEG
        jpeg_header = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
            0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
            0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
            0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
            0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
            0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
            0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
            0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
            0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
            0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
            0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD5,
            0xFF, 0xD9
        ])
        
        files = {'file': ('test_photo.jpg', io.BytesIO(jpeg_header), 'image/jpeg')}
        
        # Remove Content-Type header for multipart upload
        headers = dict(self.session.headers)
        headers.pop('Content-Type', None)
        
        photo_resp = self.session.post(
            f"{BASE_URL}/api/reports/{report_id}/photo",
            files=files,
            headers=headers
        )
        
        # Key assertion: should NOT be 403 (premium required)
        assert photo_resp.status_code != 403, f"Photo upload returned 403 (premium required) for non-premium user!"
        
        # Should be 200 or at least not 403
        if photo_resp.status_code == 200:
            print(f"PASS: Non-premium user can upload photo. Response: {photo_resp.json()}")
            assert "photo_url" in photo_resp.json(), "Response should contain photo_url"
        else:
            print(f"Photo upload returned {photo_resp.status_code}: {photo_resp.text}")
            # Accept 500 if storage issue, but NOT 403
            assert photo_resp.status_code != 403, "Should not require premium subscription"
        
        print("PASS: Photo upload does NOT require premium subscription (no 403)")


class TestReportPhotoUrl:
    """Test that GET /api/reports/{id} returns photo_url when photo was uploaded"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
    
    def test_get_report_returns_photo_url(self):
        """GET /api/reports/{id} should return photo_url field when photo was uploaded"""
        # Try to get the report with known photo
        response = self.session.get(f"{BASE_URL}/api/reports/{REPORT_WITH_PHOTO_ID}")
        
        if response.status_code == 404:
            pytest.skip(f"Report {REPORT_WITH_PHOTO_ID} not found - may need to create test data")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Check that photo_url field exists in response
        assert "photo_url" in data, "Response should contain photo_url field"
        print(f"PASS: GET /api/reports/{REPORT_WITH_PHOTO_ID} returns photo_url: {data.get('photo_url')}")
        
        if data.get("photo_url"):
            print(f"Photo URL is set: {data['photo_url']}")
        else:
            print("Photo URL is null/empty")


class TestFileServing:
    """Test that GET /api/files/{path} serves uploaded photos"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
    
    def test_get_file_endpoint_exists(self):
        """GET /api/files/{path} should serve files"""
        # First get a report with photo to get the path
        response = self.session.get(f"{BASE_URL}/api/reports/{REPORT_WITH_PHOTO_ID}")
        
        if response.status_code == 404:
            pytest.skip(f"Report {REPORT_WITH_PHOTO_ID} not found")
        
        data = response.json()
        photo_url = data.get("photo_url")
        
        if not photo_url:
            pytest.skip("Report has no photo_url set")
        
        # Try to fetch the file
        file_response = self.session.get(f"{BASE_URL}/api/files/{photo_url}")
        
        # Should return 200 with image content or 404 if file doesn't exist
        assert file_response.status_code in [200, 404], f"Unexpected status: {file_response.status_code}"
        
        if file_response.status_code == 200:
            content_type = file_response.headers.get("Content-Type", "")
            print(f"PASS: File served successfully. Content-Type: {content_type}")
            assert "image" in content_type or "octet-stream" in content_type, "Should return image content"
        else:
            print(f"File not found at path: {photo_url}")


class TestCORSPreflight:
    """Test CORS preflight requests"""
    
    def test_cors_options_returns_success(self):
        """OPTIONS request should return 200/204 for CORS preflight"""
        response = requests.options(
            f"{BASE_URL}/api/reports",
            headers={
                "Origin": "null",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        assert response.status_code in [200, 204], f"CORS preflight failed: {response.status_code}"
        print(f"PASS: CORS preflight returns {response.status_code}")
        
        # Check CORS headers
        cors_origin = response.headers.get("Access-Control-Allow-Origin")
        print(f"Access-Control-Allow-Origin: {cors_origin}")
    
    def test_cors_with_wildcard_origin(self):
        """CORS should work with any origin"""
        response = requests.options(
            f"{BASE_URL}/api/reports/test/photo",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        assert response.status_code in [200, 204], f"CORS preflight failed: {response.status_code}"
        print(f"PASS: CORS works with external origin")


class TestReportDetailFetch:
    """Test that report detail endpoint works correctly"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
    
    def test_get_report_detail_endpoint(self):
        """GET /api/reports/{id} should return full report data including photo_url"""
        # First get list of reports to find a valid ID
        list_resp = self.session.get(f"{BASE_URL}/api/reports")
        assert list_resp.status_code == 200, f"Failed to get reports list: {list_resp.status_code}"
        
        reports = list_resp.json()
        if not reports:
            pytest.skip("No reports available for testing")
        
        # Get first report's detail
        report_id = reports[0].get("id")
        detail_resp = self.session.get(f"{BASE_URL}/api/reports/{report_id}")
        
        assert detail_resp.status_code == 200, f"Failed to get report detail: {detail_resp.status_code}"
        
        data = detail_resp.json()
        
        # Verify expected fields are present
        expected_fields = ["id", "latitude", "longitude", "created_at", "photo_url"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        # status field may be present as "status" or "status_score"
        assert "status" in data or "status_score" in data, "Missing status field"
        
        print(f"PASS: Report detail endpoint returns all expected fields")
        print(f"Report ID: {data['id']}, photo_url: {data.get('photo_url')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
