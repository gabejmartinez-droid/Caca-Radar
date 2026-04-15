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
    
    def test_share_endpoint(self):
        """Test share data endpoint for reports"""
        # Get a report to share (if any exist)
        reports_success, reports_response = self.run_test(
            "Get Reports for Share Test", "GET", "reports", 200
        )
        
        if not reports_success or not reports_response or len(reports_response) == 0:
            self.log("   ⚠️  No reports available for share test")
            return True, {"message": "No reports to test sharing"}
        
        report_id = reports_response[0]['id']
        
        # Test share endpoint
        success, response = self.run_test(
            "Share Report Data", "GET", f"reports/{report_id}/share", 200
        )
        
        if success:
            # Check if response contains expected share fields
            expected_fields = ['url', 'title', 'text', 'report_id', 'municipality', 'contributor']
            missing_fields = [field for field in expected_fields if field not in response]
            if missing_fields:
                self.log(f"   ⚠️  Missing share fields: {missing_fields}")
            else:
                self.log(f"   ✅ Share data contains all required fields")
                self.log(f"   📄 Title: {response.get('title', '')[:50]}...")
                self.log(f"   🔗 URL: {response.get('url', '')}")
        
        return success, response
    
    def test_vapid_key_endpoint(self):
        """Test VAPID public key endpoint for push notifications"""
        success, response = self.run_test(
            "VAPID Public Key", "GET", "push/vapid-key", 200
        )
        
        if success:
            if 'vapid_public_key' in response:
                key = response['vapid_public_key']
                self.log(f"   ✅ VAPID key received: {key[:20]}...{key[-10:] if len(key) > 30 else key}")
            else:
                self.log(f"   ⚠️  No vapid_public_key in response: {response}")
        
        return success, response
    
    def test_push_subscribe_endpoint(self):
        """Test push notification subscription endpoint"""
        if not self.user_token:
            self.log("⚠️  Skipping push subscribe - no user token")
            return False, {}
        
        # Mock push subscription object
        mock_subscription = {
            "endpoint": "https://fcm.googleapis.com/fcm/send/mock-endpoint",
            "keys": {
                "p256dh": "mock-p256dh-key",
                "auth": "mock-auth-key"
            }
        }
        
        success, response = self.run_test(
            "Push Subscribe", "POST", "push/subscribe", 200,
            {
                "subscription": mock_subscription,
                "latitude": 40.4168,
                "longitude": -3.7038
            },
            cookies={'access_token': self.user_token}
        )
        
        if success:
            self.log(f"   ✅ Push subscription successful: {response.get('message', '')}")
        
        return success, response
    
    def test_push_unsubscribe_endpoint(self):
        """Test push notification unsubscribe endpoint"""
        if not self.user_token:
            self.log("⚠️  Skipping push unsubscribe - no user token")
            return False, {}
        
        success, response = self.run_test(
            "Push Unsubscribe", "POST", "push/unsubscribe", 200,
            {},
            cookies={'access_token': self.user_token}
        )
        
        if success:
            self.log(f"   ✅ Push unsubscribe successful: {response.get('message', '')}")
        
        return success, response
    
    def test_municipality_analytics_endpoint(self):
        """Test municipality analytics endpoint with comprehensive data"""
        if not self.municipality_token:
            self.log("⚠️  Skipping municipality analytics - no municipality token")
            return False, {}
        
        success, response = self.run_test(
            "Municipality Analytics", "GET", "municipality/analytics", 200,
            cookies={'access_token': self.municipality_token}
        )
        
        if success:
            # Check if response contains expected analytics fields
            expected_fields = ['municipality', 'summary', 'daily_reports', 'hourly_distribution', 'status_distribution', 'top_zones']
            missing_fields = [field for field in expected_fields if field not in response]
            if missing_fields:
                self.log(f"   ⚠️  Missing analytics fields: {missing_fields}")
            else:
                self.log(f"   ✅ Analytics contains all required fields")
                
                # Check data structure details
                daily_reports = response.get('daily_reports', [])
                hourly_distribution = response.get('hourly_distribution', [])
                status_distribution = response.get('status_distribution', [])
                top_zones = response.get('top_zones', [])
                
                self.log(f"   📊 Daily reports: {len(daily_reports)} data points")
                self.log(f"   🕐 Hourly distribution: {len(hourly_distribution)} hours")
                self.log(f"   📈 Status distribution: {len(status_distribution)} statuses")
                self.log(f"   🗺️  Top zones: {len(top_zones)} zones")
                
                # Validate expected data point counts
                if len(daily_reports) == 30:
                    self.log(f"   ✅ Daily reports has correct 30 data points")
                else:
                    self.log(f"   ⚠️  Daily reports expected 30 points, got {len(daily_reports)}")
                    
                if len(hourly_distribution) == 24:
                    self.log(f"   ✅ Hourly distribution has correct 24 hours")
                else:
                    self.log(f"   ⚠️  Hourly distribution expected 24 hours, got {len(hourly_distribution)}")
        
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
    
    def test_reports_freshness_filter(self):
        """Test reports endpoint with freshness filter"""
        success, response = self.run_test(
            "Reports with Freshness Filter", "GET", "reports?freshness=Fresca", 200
        )
        
        if success and isinstance(response, list):
            # Check if reports have freshness labels
            for report in response[:3]:  # Check first 3 reports
                if 'freshness' in report:
                    self.log(f"   ✅ Report has freshness: {report['freshness']}")
                    break
            else:
                self.log("   ⚠️  No reports with freshness field found")
        
        return success, response
    
    def test_reports_confirmed_filter(self):
        """Test reports endpoint with confirmed_only filter"""
        success, response = self.run_test(
            "Reports with Confirmed Filter", "GET", "reports?confirmed_only=true", 200
        )
        
        if success and isinstance(response, list):
            # Check if all returned reports are verified
            verified_count = sum(1 for r in response if r.get('status') == 'verified')
            self.log(f"   ✅ Returned {len(response)} reports, {verified_count} verified")
        
        return success, response
    
    def test_user_subscription_trial(self):
        """Test free trial subscription activation"""
        # Create a new user for trial test
        test_email = f"trial.user.{uuid.uuid4().hex[:8]}@test.es"
        
        success, response = self.run_test(
            "Trial User Registration", "POST", "auth/register", 200,
            {
                "email": test_email,
                "password": "testpass123",
                "name": "Trial User"
            }
        )
        
        if not success:
            return False, {}
            
        trial_token = self.session.cookies.get('access_token')
        
        # Test free trial activation
        success, response = self.run_test(
            "Free Trial Activation", "POST", "users/subscribe", 200,
            {"plan": "monthly"},
            cookies={'access_token': trial_token}
        )
        
        if success:
            if response.get('trial'):
                self.log(f"   ✅ Free trial activated: {response.get('message')}")
            else:
                self.log(f"   ⚠️  Expected trial activation, got: {response}")
        
        return success, response
    
    def test_photo_upload_premium_restriction(self):
        """Test photo upload is restricted to premium users"""
        # Create a free user
        test_email = f"free.photo.{uuid.uuid4().hex[:8]}@test.es"
        
        success, response = self.run_test(
            "Free User for Photo Test", "POST", "auth/register", 200,
            {
                "email": test_email,
                "password": "testpass123",
                "name": "Free Photo User"
            }
        )
        
        if not success:
            return False, {}
            
        free_token = self.session.cookies.get('access_token')
        
        # Create a report first
        success, report_response = self.run_test(
            "Create Report for Photo Test", "POST", "reports", 200,
            {
                "latitude": 40.4168,
                "longitude": -3.7038,
                "description": "Test report for photo upload"
            },
            cookies={'access_token': free_token}
        )
        
        if not success:
            return False, {}
        
        report_id = report_response.get('id')
        
        # Try to upload photo as free user (should fail with 403)
        success, response = self.run_test(
            "Photo Upload (Free User)", "POST", f"reports/{report_id}/photo", 403,
            {},  # Would normally be FormData but testing restriction
            cookies={'access_token': free_token}
        )
        
        if success:
            self.log(f"   ✅ Photo upload correctly restricted for free users")
        
        return success, response
    
    def test_badges_endpoint(self):
        """Test user badges endpoint"""
        if not self.user_token:
            self.log("⚠️  Skipping badges test - no user token")
            return False, {}
        
        success, response = self.run_test(
            "User Badges", "GET", "users/badges", 200,
            cookies={'access_token': self.user_token}
        )
        
        if success:
            if isinstance(response, list):
                earned_badges = [b for b in response if b.get('earned')]
                self.log(f"   ✅ Badges endpoint returned {len(response)} badges, {len(earned_badges)} earned")
            else:
                self.log(f"   ⚠️  Expected list of badges, got: {type(response)}")
        
        return success, response
    
    def test_weekly_leaderboard(self):
        """Test weekly leaderboard endpoint"""
        # First, activate subscription for a user to access leaderboard
        if not self.user_token:
            self.log("⚠️  Skipping weekly leaderboard - no user token")
            return False, {}
        
        # Try to activate subscription first
        self.run_test(
            "Activate Subscription for Leaderboard", "POST", "users/subscribe", 200,
            {"plan": "monthly"},
            cookies={'access_token': self.user_token}
        )
        
        # Test weekly leaderboard
        success, response = self.run_test(
            "Weekly Leaderboard", "GET", "leaderboard/weekly", 200,
            cookies={'access_token': self.user_token}
        )
        
        if success:
            if isinstance(response, list):
                self.log(f"   ✅ Weekly leaderboard returned {len(response)} users")
            else:
                self.log(f"   ⚠️  Expected list of users, got: {type(response)}")
        
        return success, response
    
    def test_saved_locations_crud(self):
        """Test saved locations CRUD operations"""
        if not self.user_token:
            self.log("⚠️  Skipping saved locations - no user token")
            return False, {}
        
        # Create saved location
        success, response = self.run_test(
            "Create Saved Location", "POST", "users/saved-locations", 200,
            {
                "name": "home",
                "latitude": 40.4168,
                "longitude": -3.7038,
                "label": "Mi Casa"
            },
            cookies={'access_token': self.user_token}
        )
        
        if not success:
            return False, {}
        
        location_id = response.get('id')
        
        # Get saved locations
        success, response = self.run_test(
            "Get Saved Locations", "GET", "users/saved-locations", 200,
            cookies={'access_token': self.user_token}
        )
        
        if success and isinstance(response, list):
            self.log(f"   ✅ Retrieved {len(response)} saved locations")
        
        # Delete saved location
        if location_id:
            success, response = self.run_test(
                "Delete Saved Location", "DELETE", f"users/saved-locations/{location_id}", 200,
                cookies={'access_token': self.user_token}
            )
        
        return success, response
    
    def test_neighborhood_cleanliness_score(self):
        """Test neighborhood cleanliness score endpoint"""
        success, response = self.run_test(
            "Neighborhood Cleanliness Score", "GET", "neighborhood/score?lat=40.42&lon=-3.70", 200
        )
        
        if success:
            if 'score' in response:
                score = response['score']
                self.log(f"   ✅ Cleanliness score: {score}/100")
            else:
                self.log(f"   ⚠️  No score in response: {response}")
        
        return success, response
    
    def test_admin_metrics_endpoint(self):
        """Test admin metrics endpoint"""
        if not self.admin_token:
            self.log("⚠️  Skipping admin metrics - no admin token")
            return False, {}
        
        success, response = self.run_test(
            "Admin Metrics", "GET", "admin/metrics", 200,
            cookies={'access_token': self.admin_token}
        )
        
        if success:
            expected_fields = ['total_users', 'total_reports', 'active_subscriptions']
            missing_fields = [field for field in expected_fields if field not in response]
            if missing_fields:
                self.log(f"   ⚠️  Missing admin metrics fields: {missing_fields}")
            else:
                self.log(f"   ✅ Admin metrics contains all required fields")
                self.log(f"   📊 Users: {response.get('total_users')}, Reports: {response.get('total_reports')}, Subscriptions: {response.get('active_subscriptions')}")
        
        return success, response
    
    def test_reports_confidence_scores(self):
        """Test reports include confidence scores"""
        success, response = self.run_test(
            "Reports with Confidence Scores", "GET", "reports", 200
        )
        
        if success and isinstance(response, list) and len(response) > 0:
            # Check if reports have confidence scores
            reports_with_confidence = [r for r in response[:5] if 'confidence' in r]
            self.log(f"   ✅ {len(reports_with_confidence)}/5 reports have confidence scores")
            
            if reports_with_confidence:
                avg_confidence = sum(r['confidence'] for r in reports_with_confidence) / len(reports_with_confidence)
                self.log(f"   📊 Average confidence: {avg_confidence:.1f}%")
        
        return success, response

    def run_all_tests(self):
        """Run all backend tests"""
        self.log("🚀 Starting Caca Radar Backend Tests - Iteration 8: Monetization & Gamification")
        
        # Basic connectivity
        self.test_health_check()
        
        # Authentication
        self.test_admin_login()
        self.test_municipality_login()
        self.test_user_registration()
        
        # ITERATION 8 NEW FEATURES TESTING
        self.log("\n🆕 Testing New Features - Reports with Freshness & Confidence")
        self.test_reports_freshness_filter()
        self.test_reports_confirmed_filter()
        self.test_reports_confidence_scores()
        
        self.log("\n🆕 Testing New Features - Subscription & Trial System")
        self.test_user_subscription_trial()
        self.test_photo_upload_premium_restriction()
        
        self.log("\n🆕 Testing New Features - Badges & Gamification")
        self.test_badges_endpoint()
        self.test_weekly_leaderboard()
        
        self.log("\n🆕 Testing New Features - Saved Locations")
        self.test_saved_locations_crud()
        
        self.log("\n🆕 Testing New Features - Neighborhood & Admin")
        self.test_neighborhood_cleanliness_score()
        self.test_admin_metrics_endpoint()
        
        # PREVIOUS FEATURES TESTING
        self.log("\n📋 Testing Previous Features")
        self.test_user_profile_endpoint()
        self.test_reports_with_category_filter()
        self.test_report_creation_with_category()
        self.test_photo_review_endpoint()
        self.test_municipality_subscription_pricing()
        self.test_contributor_anonymity()
        self.test_flag_threshold()
        
        # Social sharing & push notifications
        self.test_share_endpoint()
        self.test_vapid_key_endpoint()
        self.test_push_subscribe_endpoint()
        self.test_push_unsubscribe_endpoint()
        
        # Municipality analytics
        self.test_municipality_analytics_endpoint()
        
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