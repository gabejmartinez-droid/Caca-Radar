import requests
import sys
import json
from datetime import datetime

class CacaRadarAPITester:
    def __init__(self, base_url="https://caca-radar.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_credentials = {
            "email": "admin@cacaradar.es",
            "password": "admin123"
        }
        self.test_user_credentials = {
            "email": f"test_user_{datetime.now().strftime('%H%M%S')}@test.com",
            "password": "testpass123",
            "name": "Test User"
        }
        self.created_report_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = self.session.get(url)
            elif method == 'POST':
                if files:
                    response = self.session.post(url, data=data, files=files)
                else:
                    response = self.session.post(url, json=data)
            elif method == 'PUT':
                response = self.session.put(url, json=data)
            elif method == 'DELETE':
                response = self.session.delete(url)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        return self.run_test("Health Check", "GET", "health", 200)

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root Endpoint", "GET", "", 200)

    def test_admin_login(self):
        """Test admin login"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data=self.admin_credentials
        )
        return success

    def test_user_register(self):
        """Test user registration"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=self.test_user_credentials
        )
        return success

    def test_user_login(self):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": self.test_user_credentials["email"],
                "password": self.test_user_credentials["password"]
            }
        )
        return success

    def test_get_me(self):
        """Test get current user"""
        return self.run_test("Get Current User", "GET", "auth/me", 200)

    def test_get_reports(self):
        """Test get all reports"""
        return self.run_test("Get All Reports", "GET", "reports", 200)

    def test_create_report(self):
        """Test create report"""
        report_data = {
            "latitude": 40.4168,  # Madrid coordinates
            "longitude": -3.7038
        }
        success, response = self.run_test(
            "Create Report",
            "POST",
            "reports",
            200,
            data=report_data
        )
        if success and response.get("id"):
            self.created_report_id = response["id"]
            print(f"   Created report ID: {self.created_report_id}")
        return success

    def test_get_report_by_id(self):
        """Test get specific report"""
        if not self.created_report_id:
            print("❌ Skipping - No report ID available")
            return False
        
        return self.run_test(
            "Get Report by ID",
            "GET",
            f"reports/{self.created_report_id}",
            200
        )

    def test_vote_on_report(self):
        """Test voting on report"""
        if not self.created_report_id:
            print("❌ Skipping - No report ID available")
            return False
        
        vote_data = {"vote_type": "still_there"}
        return self.run_test(
            "Vote on Report",
            "POST",
            f"reports/{self.created_report_id}/vote",
            200,
            data=vote_data
        )

    def test_get_my_vote(self):
        """Test get my vote on report"""
        if not self.created_report_id:
            print("❌ Skipping - No report ID available")
            return False
        
        return self.run_test(
            "Get My Vote",
            "GET",
            f"reports/{self.created_report_id}/my-vote",
            200
        )

    def test_flag_report(self):
        """Test flagging report"""
        if not self.created_report_id:
            print("❌ Skipping - No report ID available")
            return False
        
        flag_data = {"reason": "Test flag"}
        return self.run_test(
            "Flag Report",
            "POST",
            f"reports/{self.created_report_id}/flag",
            200,
            data=flag_data
        )

    def test_logout(self):
        """Test logout"""
        return self.run_test("Logout", "POST", "auth/logout", 200)

    def test_duplicate_vote_error(self):
        """Test that duplicate voting returns error"""
        if not self.created_report_id:
            print("❌ Skipping - No report ID available")
            return False
        
        # First vote should succeed (already done in test_vote_on_report)
        # Second vote should fail
        vote_data = {"vote_type": "cleaned"}
        success, response = self.run_test(
            "Duplicate Vote (Should Fail)",
            "POST",
            f"reports/{self.created_report_id}/vote",
            400,  # Expecting error
            data=vote_data
        )
        return success

def main():
    print("🚀 Starting Caca Radar API Tests")
    print("=" * 50)
    
    tester = CacaRadarAPITester()
    
    # Test sequence
    tests = [
        ("Health Check", tester.test_health_check),
        ("Root Endpoint", tester.test_root_endpoint),
        ("Admin Login", tester.test_admin_login),
        ("User Registration", tester.test_user_register),
        ("User Login", tester.test_user_login),
        ("Get Current User", tester.test_get_me),
        ("Get All Reports", tester.test_get_reports),
        ("Create Report", tester.test_create_report),
        ("Get Report by ID", tester.test_get_report_by_id),
        ("Vote on Report", tester.test_vote_on_report),
        ("Get My Vote", tester.test_get_my_vote),
        ("Flag Report", tester.test_flag_report),
        ("Duplicate Vote Error", tester.test_duplicate_vote_error),
        ("Logout", tester.test_logout),
    ]
    
    print(f"\n📋 Running {len(tests)} tests...")
    
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_name} - Exception: {str(e)}")
    
    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())