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
        self.municipality_credentials = {
            "email": "madrid@cacaradar.es",
            "password": "madrid123"
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
        """Test flagging report with valid reason"""
        if not self.created_report_id:
            print("❌ Skipping - No report ID available")
            return False
        
        flag_data = {"reason": "inappropriate"}  # Valid flag reason
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

    def test_user_subscription(self):
        """Test user subscription endpoint (mocked)"""
        subscription_data = {"plan": "monthly"}
        return self.run_test(
            "User Subscription (Mocked)",
            "POST",
            "users/subscribe",
            200,
            data=subscription_data
        )

    def test_national_leaderboard(self):
        """Test national leaderboard (requires subscription)"""
        return self.run_test(
            "National Leaderboard",
            "GET",
            "leaderboard/national",
            200
        )

    def test_city_leaderboard(self):
        """Test city leaderboard"""
        return self.run_test(
            "City Leaderboard",
            "GET",
            "leaderboard/city/Madrid",
            200
        )

    def test_city_list(self):
        """Test city list for leaderboards"""
        return self.run_test(
            "City List",
            "GET",
            "leaderboard/cities",
            200
        )

    def test_municipality_login(self):
        """Test municipality login"""
        success, response = self.run_test(
            "Municipality Login",
            "POST",
            "auth/login",
            200,
            data=self.municipality_credentials
        )
        return success

    def test_municipality_stats(self):
        """Test municipality stats"""
        return self.run_test(
            "Municipality Stats",
            "GET",
            "municipality/stats",
            200
        )

    def test_municipality_reports(self):
        """Test municipality reports"""
        return self.run_test(
            "Municipality Reports",
            "GET",
            "municipality/reports",
            200
        )

    def test_municipality_flags(self):
        """Test municipality flags"""
        return self.run_test(
            "Municipality Flags",
            "GET",
            "municipality/flags",
            200
        )

    def test_municipality_moderate(self):
        """Test municipality moderation"""
        if not self.created_report_id:
            print("❌ Skipping - No report ID available")
            return False
        
        moderation_data = {"action": "dismiss"}
        return self.run_test(
            "Municipality Moderation",
            "POST",
            f"municipality/moderate/{self.created_report_id}",
            200,
            data=moderation_data
        )

    def test_apple_receipt_verification(self):
        """Test Apple receipt verification (mock mode)"""
        apple_data = {
            "receipt_data": "mock_receipt_data",
            "transaction_id": "mock_transaction_123",
            "plan": "monthly"
        }
        return self.run_test(
            "Apple Receipt Verification (Mock)",
            "POST",
            "users/subscribe/apple",
            200,
            data=apple_data
        )

    def test_google_receipt_verification(self):
        """Test Google receipt verification (mock mode)"""
        google_data = {
            "purchase_token": "mock_purchase_token_123",
            "subscription_id": "premium_monthly",
            "plan": "monthly"
        }
        return self.run_test(
            "Google Receipt Verification (Mock)",
            "POST",
            "users/subscribe/google",
            200,
            data=google_data
        )

    def test_subscription_status(self):
        """Test subscription status endpoint"""
        return self.run_test(
            "Subscription Status",
            "GET",
            "users/subscription-status",
            200
        )

    def test_municipality_register_valid_domain(self):
        """Test municipality registration with valid domain"""
        # Use a valid .es domain
        muni_data = {
            "email": f"contacto{datetime.now().strftime('%H%M%S')}@alcobendas.es",
            "password": "testpass123",
            "name": "Test Municipality Contact",
            "municipality_name": "Alcobendas",
            "province": "Madrid"
        }
        success, response = self.run_test(
            "Municipality Registration (Valid Domain)",
            "POST",
            "municipality/register",
            200,
            data=muni_data
        )
        if success and response.get("verification_code_hint"):
            self.test_verification_code = response["verification_code_hint"]
            self.test_municipality_email = muni_data["email"]
            print(f"   Verification code: {self.test_verification_code}")
        return success

    def test_municipality_register_invalid_domain(self):
        """Test municipality registration with invalid domain (should fail)"""
        muni_data = {
            "email": f"test{datetime.now().strftime('%H%M%S')}@gmail.com",
            "password": "testpass123",
            "name": "Test Contact",
            "municipality_name": "Test City",
            "province": "Test Province"
        }
        success, response = self.run_test(
            "Municipality Registration (Invalid Domain - Should Fail)",
            "POST",
            "municipality/register",
            400,  # Expecting error
            data=muni_data
        )
        return success

    def test_municipality_email_verification_correct(self):
        """Test municipality email verification with correct code"""
        if not hasattr(self, 'test_verification_code') or not hasattr(self, 'test_municipality_email'):
            print("❌ Skipping - No verification code available")
            return False
        
        verify_data = {
            "email": self.test_municipality_email,
            "code": self.test_verification_code
        }
        return self.run_test(
            "Municipality Email Verification (Correct Code)",
            "POST",
            "municipality/verify",
            200,
            data=verify_data
        )

    def test_municipality_email_verification_wrong(self):
        """Test municipality email verification with wrong code"""
        if not hasattr(self, 'test_municipality_email'):
            print("❌ Skipping - No municipality email available")
            return False
        
        verify_data = {
            "email": self.test_municipality_email,
            "code": "000000"  # Wrong code
        }
        success, response = self.run_test(
            "Municipality Email Verification (Wrong Code - Should Fail)",
            "POST",
            "municipality/verify",
            400,  # Expecting error
            data=verify_data
        )
        return success

    def test_municipality_resend_verification(self):
        """Test municipality resend verification code"""
        if not hasattr(self, 'test_municipality_email'):
            print("❌ Skipping - No municipality email available")
            return False
        
        resend_data = {
            "email": self.test_municipality_email
        }
        return self.run_test(
            "Municipality Resend Verification",
            "POST",
            "municipality/resend-verification",
            200,
            data=resend_data
        )

    def test_reverse_geocoding_in_report(self):
        """Test that report creation includes municipality from reverse geocoding"""
        report_data = {
            "latitude": 40.4168,  # Madrid coordinates
            "longitude": -3.7038
        }
        success, response = self.run_test(
            "Report with Reverse Geocoding",
            "POST",
            "reports",
            200,
            data=report_data
        )
        if success and response.get("municipality"):
            print(f"   Municipality auto-tagged: {response['municipality']}")
            return True
        return False

def main():
    print("🚀 Starting Caca Radar API Tests (Expanded Features)")
    print("=" * 60)
    
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
        ("Report with Reverse Geocoding", tester.test_reverse_geocoding_in_report),
        ("Get Report by ID", tester.test_get_report_by_id),
        ("Vote on Report", tester.test_vote_on_report),
        ("Get My Vote", tester.test_get_my_vote),
        ("Flag Report", tester.test_flag_report),
        ("Duplicate Vote Error", tester.test_duplicate_vote_error),
        ("User Subscription", tester.test_user_subscription),
        ("Apple Receipt Verification", tester.test_apple_receipt_verification),
        ("Google Receipt Verification", tester.test_google_receipt_verification),
        ("Subscription Status", tester.test_subscription_status),
        ("National Leaderboard", tester.test_national_leaderboard),
        ("City Leaderboard", tester.test_city_leaderboard),
        ("City List", tester.test_city_list),
        ("Municipality Registration (Valid Domain)", tester.test_municipality_register_valid_domain),
        ("Municipality Registration (Invalid Domain)", tester.test_municipality_register_invalid_domain),
        ("Municipality Email Verification (Correct)", tester.test_municipality_email_verification_correct),
        ("Municipality Email Verification (Wrong)", tester.test_municipality_email_verification_wrong),
        ("Municipality Resend Verification", tester.test_municipality_resend_verification),
        ("Municipality Login", tester.test_municipality_login),
        ("Municipality Stats", tester.test_municipality_stats),
        ("Municipality Reports", tester.test_municipality_reports),
        ("Municipality Flags", tester.test_municipality_flags),
        ("Municipality Moderation", tester.test_municipality_moderate),
        ("Logout", tester.test_logout),
    ]
    
    print(f"\n📋 Running {len(tests)} tests...")
    
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_name} - Exception: {str(e)}")
    
    # Print results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())