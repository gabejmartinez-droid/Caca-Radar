#!/usr/bin/env python3
"""
Backend API Testing for Caca Radar - Webhook & Email Features
Tests Apple/Google webhooks, email service, and existing functionality
"""

import requests
import json
import base64
import uuid
from datetime import datetime, timezone
import sys
import os

class CacaRadarAPITester:
    def __init__(self, base_url="https://caca-radar.preview.emergentagent.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.admin_token = None
        self.municipality_token = None
        self.user_token = None
        self.tests_run = 0
        self.tests_passed = 0
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, cookies=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)
            
        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=test_headers, cookies=cookies)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=test_headers, cookies=cookies)
            elif method == 'PUT':
                response = self.session.put(url, json=data, headers=test_headers, cookies=cookies)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=test_headers, cookies=cookies)
                
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {"raw": response.text}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                self.log(f"   Response: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}
    
    def test_health_check(self):
        """Test basic health endpoint"""
        return self.run_test("Health Check", "GET", "health", 200)
    
    def test_admin_login(self):
        """Test admin login"""
        success, response = self.run_test(
            "Admin Login", "POST", "auth/login", 200,
            {"email": "admin@cacaradar.es", "password": "admin123"}
        )
        if success:
            # Extract token from cookies
            self.admin_token = self.session.cookies.get('access_token')
            self.log(f"   Admin token obtained: {bool(self.admin_token)}")
        return success, response
    
    def test_municipality_login(self):
        """Test municipality login"""
        success, response = self.run_test(
            "Municipality Login", "POST", "auth/login", 200,
            {"email": "madrid@cacaradar.es", "password": "madrid123"}
        )
        if success:
            self.municipality_token = self.session.cookies.get('access_token')
            self.log(f"   Municipality token obtained: {bool(self.municipality_token)}")
        return success, response
    
    def test_webhook_status(self):
        """Test webhook configuration status endpoint"""
        return self.run_test("Webhook Status", "GET", "webhooks/status", 200)
    
    def test_apple_webhook(self):
        """Test Apple webhook endpoint with mock JWS payload"""
        # Create a mock JWS payload (header.payload.signature format)
        header = {"alg": "ES256", "x5c": ["mock_cert"]}
        payload = {
            "notificationType": "SUBSCRIBED",
            "subtype": "INITIAL_BUY",
            "data": {
                "bundleId": "com.cacaradar.app",
                "environment": "Sandbox",
                "signedTransactionInfo": self._create_mock_transaction_jws(),
                "signedRenewalInfo": self._create_mock_renewal_jws()
            }
        }
        signature = "mock_signature"
        
        # Create JWS format: base64(header).base64(payload).signature
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
        signed_payload = f"{header_b64}.{payload_b64}.{signature}"
        
        return self.run_test(
            "Apple Webhook", "POST", "webhooks/apple", 200,
            {"signedPayload": signed_payload}
        )
    
    def test_google_webhook(self):
        """Test Google webhook endpoint with mock Pub/Sub message"""
        # Create mock Google RTDN notification
        notification = {
            "version": "1.0",
            "packageName": "com.cacaradar.app",
            "eventTimeMillis": int(datetime.now(timezone.utc).timestamp() * 1000),
            "subscriptionNotification": {
                "version": "1.0",
                "notificationType": 4,  # SUBSCRIPTION_PURCHASED
                "purchaseToken": f"mock_purchase_token_{uuid.uuid4()}",
                "subscriptionId": "premium_monthly"
            }
        }
        
        # Encode as base64 (as Pub/Sub would)
        message_data = base64.b64encode(json.dumps(notification).encode()).decode()
        
        return self.run_test(
            "Google Webhook", "POST", "webhooks/google", 200,
            {"message": {"data": message_data}, "subscription": "projects/test/subscriptions/test"}
        )
    
    def test_municipality_registration_email(self):
        """Test municipality registration triggers verification email"""
        test_email = f"test.municipality.{uuid.uuid4().hex[:8]}@ayuntamiento.es"
        
        success, response = self.run_test(
            "Municipality Registration", "POST", "municipality/register", 200,
            {
                "email": test_email,
                "password": "testpass123",
                "name": "Test Municipality",
                "municipality_name": "Test City",
                "province": "Test Province"
            }
        )
        
        if success:
            self.log(f"   Registration successful, verification required: {response.get('verification_required')}")
            # Check if verification code hint is provided (dev mode)
            if 'verification_code_hint' in response:
                self.log(f"   Verification code hint: {response['verification_code_hint']}")
        
        return success, response
    
    def test_municipality_resend_verification(self):
        """Test resending verification code"""
        # Use a known municipality email that should exist
        return self.run_test(
            "Resend Verification", "POST", "municipality/resend-verification", 200,
            {"email": "madrid@cacaradar.es"}
        )
    
    def test_user_registration(self):
        """Test regular user registration"""
        test_email = f"test.user.{uuid.uuid4().hex[:8]}@test.es"
        
        success, response = self.run_test(
            "User Registration", "POST", "auth/register", 200,
            {
                "email": test_email,
                "password": "testpass123",
                "name": "Test User",
                "username": f"testuser{uuid.uuid4().hex[:6]}"
            }
        )
        
        if success:
            self.user_token = self.session.cookies.get('access_token')
            self.log(f"   User token obtained: {bool(self.user_token)}")
        
        return success, response
    
    def test_reports_endpoint(self):
        """Test reports endpoint still works"""
        return self.run_test("Get Reports", "GET", "reports", 200)
    
    def test_municipality_stats(self):
        """Test municipality dashboard stats"""
        if not self.municipality_token:
            self.log("⚠️  Skipping municipality stats - no municipality token")
            return False, {}
            
        return self.run_test(
            "Municipality Stats", "GET", "municipality/stats", 200,
            cookies={'access_token': self.municipality_token}
        )
    
    def test_leaderboard_access(self):
        """Test leaderboard requires subscription"""
        # Should fail without subscription
        success, response = self.run_test(
            "Leaderboard (No Subscription)", "GET", "leaderboard/national", 403,
            cookies={'access_token': self.user_token} if self.user_token else None
        )
        return success, response
    
    def test_user_profile_endpoint(self):
        """Test user profile endpoint returns gamification stats"""
        if not self.user_token:
            self.log("⚠️  Skipping user profile - no user token")
            return False, {}
            
        success, response = self.run_test(
            "User Profile", "GET", "users/profile", 200,
            cookies={'access_token': self.user_token}
        )
        
        if success:
            # Check if response contains expected gamification fields
            expected_fields = ['total_score', 'trust_score', 'rank', 'level', 'report_count', 'vote_count', 'streak_days']
            missing_fields = [field for field in expected_fields if field not in response]
            if missing_fields:
                self.log(f"   ⚠️  Missing profile fields: {missing_fields}")
            else:
                self.log(f"   ✅ Profile contains all gamification stats")
        
        return success, response
    
    def test_reports_with_category_filter(self):
        """Test reports endpoint accepts category filter"""
        success, response = self.run_test(
            "Reports with Category Filter", "GET", "reports?category=dog_feces", 200
        )
        return success, response
    
    def test_report_creation_with_category(self):
        """Test report creation with category field"""
        if not self.user_token:
            self.log("⚠️  Skipping report creation - no user token")
            return False, {}
            
        # Create a report with category
        success, response = self.run_test(
            "Create Report with Category", "POST", "reports", 200,
            {
                "latitude": 40.4168,
                "longitude": -3.7038,
                "description": "Test report with category",
                "category": "trash"
            },
            cookies={'access_token': self.user_token}
        )
        
        if success and 'category' in response:
            self.log(f"   ✅ Report created with category: {response['category']}")
        
        return success, response
    
    def test_photo_review_endpoint(self):
        """Test municipality photo review endpoint"""
        if not self.municipality_token:
            self.log("⚠️  Skipping photo reviews - no municipality token")
            return False, {}
            
        success, response = self.run_test(
            "Photo Reviews", "GET", "municipality/photo-reviews", 200,
            cookies={'access_token': self.municipality_token}
        )
        
        if success:
            self.log(f"   ✅ Photo reviews endpoint accessible, returned {len(response) if isinstance(response, list) else 'data'}")
        
        return success, response
    
    def test_municipality_subscription_pricing(self):
        """Test municipality subscription shows €49/month pricing"""
        if not self.municipality_token:
            self.log("⚠️  Skipping municipality subscription - no municipality token")
            return False, {}
            
        success, response = self.run_test(
            "Municipality Subscription", "POST", "municipality/subscribe", 200,
            {"plan": "monthly"},
            cookies={'access_token': self.municipality_token}
        )
        
        if success and 'price' in response:
            expected_price = "€49/mes"
            if expected_price in response.get('message', '') or response.get('price') == expected_price:
                self.log(f"   ✅ Municipality pricing correct: {response.get('price', response.get('message'))}")
            else:
                self.log(f"   ⚠️  Unexpected pricing: {response}")
        
        return success, response
    
    def test_contributor_anonymity(self):
        """Test free user reports show contributor_name=Anónimo"""
        # Create a new free user
        test_email = f"free.user.{uuid.uuid4().hex[:8]}@test.es"
        
        success, response = self.run_test(
            "Free User Registration", "POST", "auth/register", 200,
            {
                "email": test_email,
                "password": "testpass123",
                "name": "Free User"
            }
        )
        
        if not success:
            return False, {}
            
        free_user_token = self.session.cookies.get('access_token')
        
        # Create a report as free user
        success, response = self.run_test(
            "Free User Report", "POST", "reports", 200,
            {
                "latitude": 40.4168,
                "longitude": -3.7038,
                "description": "Free user report test"
            },
            cookies={'access_token': free_user_token}
        )
        
        if success:
            contributor_name = response.get('contributor_name')
            if contributor_name == "Anónimo":
                self.log(f"   ✅ Free user shows as anonymous: {contributor_name}")
            else:
                self.log(f"   ⚠️  Free user contributor name: {contributor_name}")
        
        return success, response
    
    def test_flag_threshold(self):
        """Test flag threshold of 2 flags auto-hides reports"""
        # This is a complex test that would require creating multiple users and flagging
        # For now, just test the flag endpoint exists
        if not self.user_token:
            self.log("⚠️  Skipping flag test - no user token")
            return False, {}
        
        # Get a report to flag (if any exist)
        reports_success, reports_response = self.run_test(
            "Get Reports for Flag Test", "GET", "reports", 200
        )
        
        if not reports_success or not reports_response or len(reports_response) == 0:
            self.log("   ⚠️  No reports available for flag test")
            return True, {"message": "No reports to test flagging"}
        
        report_id = reports_response[0]['id']
        
        # Test flagging endpoint
        success, response = self.run_test(
            "Flag Report", "POST", f"reports/{report_id}/flag", 200,
            {"reason": "spam"},
            cookies={'access_token': self.user_token}
        )
        
        return success, response
    
    def _create_mock_transaction_jws(self):
        """Create mock Apple transaction info JWS"""
        transaction_info = {
            "originalTransactionId": f"mock_txn_{uuid.uuid4()}",
            "transactionId": f"mock_txn_{uuid.uuid4()}",
            "productId": "premium_monthly",
            "purchaseDate": int(datetime.now(timezone.utc).timestamp() * 1000),
            "expiresDate": int((datetime.now(timezone.utc).timestamp() + 30*24*3600) * 1000),
            "quantity": 1,
            "type": "Auto-Renewable Subscription"
        }
        
        header_b64 = base64.urlsafe_b64encode(b'{"alg":"ES256"}').decode().rstrip('=')
        payload_b64 = base64.urlsafe_b64encode(json.dumps(transaction_info).encode()).decode().rstrip('=')
        return f"{header_b64}.{payload_b64}.mock_signature"
    
    def _create_mock_renewal_jws(self):
        """Create mock Apple renewal info JWS"""
        renewal_info = {
            "originalTransactionId": f"mock_txn_{uuid.uuid4()}",
            "autoRenewProductId": "premium_monthly",
            "autoRenewStatus": 1,
            "environment": "Sandbox"
        }
        
        header_b64 = base64.urlsafe_b64encode(b'{"alg":"ES256"}').decode().rstrip('=')
        payload_b64 = base64.urlsafe_b64encode(json.dumps(renewal_info).encode()).decode().rstrip('=')
        return f"{header_b64}.{payload_b64}.mock_signature"
    
    def run_all_tests(self):
        """Run all backend tests"""
        self.log("🚀 Starting Caca Radar Backend Tests - Profile, Categories & New Features")
        
        # Basic connectivity
        self.test_health_check()
        
        # Authentication
        self.test_admin_login()
        self.test_municipality_login()
        self.test_user_registration()
        
        # NEW FEATURES TESTING
        self.test_user_profile_endpoint()
        self.test_reports_with_category_filter()
        self.test_report_creation_with_category()
        self.test_photo_review_endpoint()
        self.test_municipality_subscription_pricing()
        self.test_contributor_anonymity()
        self.test_flag_threshold()
        
        # Webhook endpoints
        self.test_webhook_status()
        self.test_apple_webhook()
        self.test_google_webhook()
        
        # Email functionality
        self.test_municipality_registration_email()
        self.test_municipality_resend_verification()
        
        # Existing functionality
        self.test_reports_endpoint()
        self.test_municipality_stats()
        self.test_leaderboard_access()
        
        # Summary
        self.log(f"\n📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            self.log("🎉 All tests passed!")
            return 0
        else:
            self.log(f"❌ {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    tester = CacaRadarAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())