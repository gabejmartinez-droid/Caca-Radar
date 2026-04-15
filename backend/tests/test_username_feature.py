"""
Test suite for Username Feature in Caca Radar
Tests registration with username, login needs_username flag, and PUT /users/username endpoint
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://caca-radar.preview.emergentagent.com').rstrip('/')

class TestRegistrationWithUsername:
    """Test registration flow with username requirement"""
    
    def test_register_with_valid_username(self):
        """Registration with valid username should succeed"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"test_user_{unique_id}@test.com"
        username = f"user_{unique_id}"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": "Test1234!",
            "username": username
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response contains username and needs_username=false
        assert "username" in data, "Response should contain username"
        assert data["username"] == username.lower(), f"Username should be {username.lower()}"
        assert data.get("needs_username") == False, "needs_username should be False for new registration"
        print(f"✓ Registration with username succeeded: {data['username']}")
    
    def test_register_without_username_fails(self):
        """Registration without username should return validation error"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"test_no_user_{unique_id}@test.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": "Test1234!"
            # Missing username
        })
        
        # Should return 422 (validation error) since username is required
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        print("✓ Registration without username correctly rejected with 422")
    
    def test_register_with_short_username_fails(self):
        """Registration with username < 3 chars should fail"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"test_short_{unique_id}@test.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": "Test1234!",
            "username": "ab"  # Too short
        })
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "3" in response.text or "20" in response.text, "Error should mention length requirement"
        print("✓ Short username correctly rejected")
    
    def test_register_with_long_username_fails(self):
        """Registration with username > 20 chars should fail"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"test_long_{unique_id}@test.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": "Test1234!",
            "username": "a" * 21  # Too long
        })
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ Long username correctly rejected")
    
    def test_register_with_invalid_chars_fails(self):
        """Registration with invalid characters in username should fail"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"test_invalid_{unique_id}@test.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": "Test1234!",
            "username": "user@name!"  # Invalid chars
        })
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ Invalid characters in username correctly rejected")
    
    def test_register_with_duplicate_username_fails(self):
        """Registration with duplicate username should fail"""
        unique_id = str(uuid.uuid4())[:8]
        username = f"dup_user_{unique_id}"
        
        # First registration
        email1 = f"test_dup1_{unique_id}@test.com"
        response1 = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email1,
            "password": "Test1234!",
            "username": username
        })
        assert response1.status_code == 200, f"First registration failed: {response1.text}"
        
        # Second registration with same username
        email2 = f"test_dup2_{unique_id}@test.com"
        response2 = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email2,
            "password": "Test1234!",
            "username": username
        })
        
        assert response2.status_code == 400, f"Expected 400, got {response2.status_code}: {response2.text}"
        assert "uso" in response2.text.lower() or "duplicate" in response2.text.lower() or "ya" in response2.text.lower(), \
            "Error should mention username already in use"
        print("✓ Duplicate username correctly rejected")


class TestLoginNeedsUsername:
    """Test login flow with needs_username flag"""
    
    def test_login_user_with_username_returns_needs_username_false(self):
        """Login for user WITH username should return needs_username=false"""
        # Use test credentials from test_credentials.md
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@cacaradar.es",
            "password": "admin123"
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Admin should have username set
        assert "needs_username" in data, "Response should contain needs_username"
        print(f"✓ Login response contains needs_username: {data.get('needs_username')}")
        print(f"  Username: {data.get('username')}")
    
    def test_login_returns_username_in_response(self):
        """Login should return username in response"""
        # Create a new user with username first
        unique_id = str(uuid.uuid4())[:8]
        email = f"test_login_{unique_id}@test.com"
        username = f"login_user_{unique_id}"
        
        # Register
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": "Test1234!",
            "username": username
        })
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        
        # Login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": "Test1234!"
        })
        
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        data = login_response.json()
        
        assert data.get("username") == username.lower(), f"Expected username {username.lower()}, got {data.get('username')}"
        assert data.get("needs_username") == False, "needs_username should be False"
        print(f"✓ Login returns correct username: {data['username']}")


class TestUpdateUsername:
    """Test PUT /api/users/username endpoint"""
    
    def test_update_username_success(self):
        """Authenticated user can update their username"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"test_update_{unique_id}@test.com"
        old_username = f"old_user_{unique_id}"
        new_username = f"new_user_{unique_id}"
        
        # Register
        session = requests.Session()
        reg_response = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": "Test1234!",
            "username": old_username
        })
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        
        # Update username
        update_response = session.put(f"{BASE_URL}/api/users/username", json={
            "username": new_username
        })
        
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        data = update_response.json()
        assert data.get("username") == new_username.lower(), f"Expected {new_username.lower()}, got {data.get('username')}"
        print(f"✓ Username updated successfully: {old_username} -> {new_username}")
    
    def test_update_username_validates_length(self):
        """PUT /users/username validates length (3-20 chars)"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"test_len_{unique_id}@test.com"
        username = f"len_user_{unique_id}"
        
        # Register
        session = requests.Session()
        reg_response = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": "Test1234!",
            "username": username
        })
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        
        # Try to update with short username
        update_response = session.put(f"{BASE_URL}/api/users/username", json={
            "username": "ab"
        })
        
        assert update_response.status_code == 400, f"Expected 400, got {update_response.status_code}"
        print("✓ Username length validation works on update")
    
    def test_update_username_validates_characters(self):
        """PUT /users/username validates characters (alphanumeric + underscore)"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"test_char_{unique_id}@test.com"
        username = f"char_user_{unique_id}"
        
        # Register
        session = requests.Session()
        reg_response = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": "Test1234!",
            "username": username
        })
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        
        # Try to update with invalid characters
        update_response = session.put(f"{BASE_URL}/api/users/username", json={
            "username": "user@name!"
        })
        
        assert update_response.status_code == 400, f"Expected 400, got {update_response.status_code}"
        print("✓ Username character validation works on update")
    
    def test_update_username_rejects_duplicate(self):
        """PUT /users/username rejects duplicate usernames"""
        unique_id = str(uuid.uuid4())[:8]
        taken_username = f"taken_{unique_id}"
        
        # Create first user with the username
        email1 = f"test_taken1_{unique_id}@test.com"
        session1 = requests.Session()
        reg1 = session1.post(f"{BASE_URL}/api/auth/register", json={
            "email": email1,
            "password": "Test1234!",
            "username": taken_username
        })
        assert reg1.status_code == 200, f"First registration failed: {reg1.text}"
        
        # Create second user
        email2 = f"test_taken2_{unique_id}@test.com"
        session2 = requests.Session()
        reg2 = session2.post(f"{BASE_URL}/api/auth/register", json={
            "email": email2,
            "password": "Test1234!",
            "username": f"other_{unique_id}"
        })
        assert reg2.status_code == 200, f"Second registration failed: {reg2.text}"
        
        # Try to update second user's username to the taken one
        update_response = session2.put(f"{BASE_URL}/api/users/username", json={
            "username": taken_username
        })
        
        assert update_response.status_code == 400, f"Expected 400, got {update_response.status_code}"
        print("✓ Duplicate username rejected on update")
    
    def test_update_username_requires_auth(self):
        """PUT /users/username requires authentication"""
        response = requests.put(f"{BASE_URL}/api/users/username", json={
            "username": "test_user"
        })
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Username update requires authentication")


class TestGetMeEndpoint:
    """Test GET /api/auth/me endpoint returns needs_username"""
    
    def test_get_me_returns_needs_username(self):
        """GET /auth/me should return needs_username field"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"test_me_{unique_id}@test.com"
        username = f"me_user_{unique_id}"
        
        # Register
        session = requests.Session()
        reg_response = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": "Test1234!",
            "username": username
        })
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        
        # Get me
        me_response = session.get(f"{BASE_URL}/api/auth/me")
        
        assert me_response.status_code == 200, f"Get me failed: {me_response.text}"
        data = me_response.json()
        
        assert "needs_username" in data, "Response should contain needs_username"
        assert data.get("needs_username") == False, "needs_username should be False for user with username"
        assert data.get("username") == username.lower(), f"Expected username {username.lower()}"
        print(f"✓ GET /auth/me returns needs_username: {data['needs_username']}")


class TestUsernameEdgeCases:
    """Test edge cases for username feature"""
    
    def test_username_is_lowercased(self):
        """Username should be stored in lowercase"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"test_case_{unique_id}@test.com"
        username = f"MixedCase_{unique_id}"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": "Test1234!",
            "username": username
        })
        
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        
        assert data.get("username") == username.lower(), f"Username should be lowercased"
        print(f"✓ Username is lowercased: {username} -> {data['username']}")
    
    def test_username_with_underscore_allowed(self):
        """Username with underscores should be allowed"""
        unique_id = str(uuid.uuid4())[:6]
        email = f"test_under_{unique_id}@test.com"
        username = f"u_w_u_{unique_id}"  # Keep under 20 chars
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": "Test1234!",
            "username": username
        })
        
        assert response.status_code == 200, f"Registration failed: {response.text}"
        print(f"✓ Username with underscores allowed: {username}")
    
    def test_username_with_numbers_allowed(self):
        """Username with numbers should be allowed"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"test_num_{unique_id}@test.com"
        username = f"user123_{unique_id}"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": "Test1234!",
            "username": username
        })
        
        assert response.status_code == 200, f"Registration failed: {response.text}"
        print(f"✓ Username with numbers allowed: {username}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
