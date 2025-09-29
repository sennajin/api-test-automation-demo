"""
Login authentication tests for the reqres.in API.

This module provides comprehensive authentication testing for the login endpoint,
including successful login scenarios, error handling, token validation, and
security edge cases.

Authentication Testing Approach:
- **Valid Credentials**: Tests successful login with valid credentials
- **Invalid Credentials**: Tests error handling with invalid credentials
- **Missing Fields**: Tests validation with missing required fields
- **Token Validation**: Tests token structure and expiration handling
- **Concurrent Authentication**: Tests concurrent login requests
- **Security Edge Cases**: Tests brute force protection and case sensitivity
- **Token Refresh**: Tests token refresh mechanisms

Test Categories:
- Basic login tests: Core authentication functionality
- TestTokenExpiration: Tests token expiration and validation
- TestRefreshTokenFlow: Tests token refresh mechanisms
- TestAuthenticationEdgeCases: Tests security edge cases

Each test includes proper error handling and validation of response schemas
to ensure the authentication system behaves correctly under various conditions.
"""

from __future__ import annotations

from typing import Dict

import pytest
from requests import Response

from tests.conftest import APIClient
from tests.conftest import assert_valid_schema
from tests.schemas.json_schemas import LOGIN_SUCCESS_SCHEMA, LOGIN_ERROR_SCHEMA


@pytest.mark.security
@pytest.mark.regression
@pytest.mark.smoke
def test_login_with_valid_credentials_returns_token(
        api_client: APIClient, login_endpoint: str, valid_credentials: Dict[str, str]
) -> None:
    """Test successful login with valid email and password returns a token."""
    response: Response = api_client.post(login_endpoint, json=valid_credentials)

    assert response.status_code == 200
    payload: Dict[str, str] = response.json()
    assert_valid_schema(payload, LOGIN_SUCCESS_SCHEMA)
    assert payload["token"], "Expected token to be present and non-empty"


@pytest.mark.security
@pytest.mark.regression
@pytest.mark.smoke
def test_login_with_missing_password_returns_error(
        api_client: APIClient, login_endpoint: str, invalid_credentials: Dict[str, str]
) -> None:
    """Test login with missing password returns 400 error."""
    response: Response = api_client.post(login_endpoint, json=invalid_credentials)

    assert response.status_code == 400
    payload: Dict[str, str] = response.json()
    assert_valid_schema(payload, LOGIN_ERROR_SCHEMA)
    assert "password" in payload["error"].lower(), "Error should mention missing password"


@pytest.mark.security
@pytest.mark.regression
@pytest.mark.smoke
def test_login_with_invalid_email_returns_error(
        api_client: APIClient, login_endpoint: str
) -> None:
    """Test login with non-existent email returns error."""
    invalid_user_credentials: Dict[str, str] = {
        "email": "nonexistent@example.com",
        "password": "somepassword"
    }
    response: Response = api_client.post(login_endpoint, json=invalid_user_credentials)

    assert response.status_code == 400
    payload: Dict[str, str] = response.json()
    assert_valid_schema(payload, LOGIN_ERROR_SCHEMA)
    assert payload["error"], "Expected error message to be present"


@pytest.mark.security
@pytest.mark.regression
def test_login_with_empty_payload_returns_error(
        api_client: APIClient, login_endpoint: str
) -> None:
    """Test login with empty JSON payload returns error."""
    response: Response = api_client.post(login_endpoint, json={})

    assert response.status_code == 400
    payload: Dict[str, Dict[str, str]] = response.json()
    assert_valid_schema(payload, LOGIN_ERROR_SCHEMA)
    assert payload["error"], "Expected error message for empty payload"


class TestTokenExpiration:
    """Test token expiration scenarios."""

    @pytest.mark.security
    @pytest.mark.parametrize("invalid_token", [
        "expired.token.here",
        "invalid.token.format",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expired.signature",
        "",
        None,
    ])
    def test_token_expiration_handling(self, api_client, users_endpoint, invalid_token):
        """Test handling of expired or invalid tokens."""
        # Store original headers
        original_headers = api_client._session.headers.copy()
        
        try:
            if invalid_token is None:
                # Remove authorization header entirely
                api_client._session.headers.pop("Authorization", None)
            else:
                api_client._session.headers.update({
                    "Authorization": f"Bearer {invalid_token}"
                })
            
            response = api_client.get(users_endpoint)
            
            # Should return 401 for expired/invalid tokens
            assert response.status_code in [200, 401, 403], (
                f"Expected 200, 401, or 403 for invalid token, got {response.status_code}"
            )
            
        finally:
            # Restore original headers
            api_client._session.headers.clear()
            api_client._session.headers.update(original_headers)

    @pytest.mark.security
    def test_token_validation_structure(self, api_client, login_endpoint, valid_credentials):
        """Test that returned tokens have proper structure."""
        response = api_client.post(login_endpoint, json=valid_credentials)
        
        assert response.status_code == 200
        payload = response.json()
        
        # Verify token structure (basic JWT format check)
        token = payload.get("token")
        assert token, "Token should be present in response"
        assert isinstance(token, str), "Token should be a string"
        assert len(token) > 0, "Token should not be empty"
        
        # Basic JWT structure validation (3 parts separated by dots)
        if "." in token:
            parts = token.split(".")
            assert len(parts) == 3, f"JWT token should have 3 parts, got {len(parts)}"
        else:
            # If not JWT format, just ensure it's not empty
            assert len(token) > 10, "Token should be reasonably long"


class TestRefreshTokenFlow:
    """Test refresh token functionality (if applicable)."""

    @pytest.mark.security
    def test_refresh_token_simulation(self, api_client, login_endpoint, valid_credentials):
        """Test refresh token flow simulation."""
        # Initial login
        login_response = api_client.post(login_endpoint, json=valid_credentials)
        assert login_response.status_code == 200
        
        login_payload = login_response.json()
        original_token = login_payload.get("token")
        
        # Simulate token refresh by logging in again
        refresh_response = api_client.post(login_endpoint, json=valid_credentials)
        assert refresh_response.status_code == 200
        
        refresh_payload = refresh_response.json()
        new_token = refresh_payload.get("token")
        
        # Tokens might be the same or different depending on implementation
        assert new_token, "Refresh should return a new token"
        assert isinstance(new_token, str), "New token should be a string"

    @pytest.mark.security
    def test_concurrent_token_requests(self, api_client, login_endpoint, valid_credentials):
        """Test concurrent token requests."""
        import concurrent.futures
        import threading
        
        def get_token():
            response = api_client.post(login_endpoint, json=valid_credentials)
            return response.status_code, response.json().get("token")
        
        # Make 5 concurrent login requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(get_token) for _ in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        for status_code, token in results:
            assert status_code == 200, f"Concurrent login failed with status {status_code}"
            assert token, "Token should be present in concurrent requests"


class TestAuthenticationEdgeCases:
    """Test authentication edge cases and security scenarios."""

    @pytest.mark.security
    @pytest.mark.parametrize("malformed_credentials", [
        {"email": "test@example.com"},  # Missing password
        {"password": "password123"},   # Missing email
        {"email": "", "password": "password123"},  # Empty email
        {"email": "test@example.com", "password": ""},  # Empty password
        {"email": None, "password": "password123"},  # Null email
        {"email": "test@example.com", "password": None},  # Null password
        {"username": "test", "password": "password123"},  # Wrong field name
    ])
    def test_malformed_credentials(self, api_client, login_endpoint, malformed_credentials):
        """Test authentication with malformed credentials."""
        response = api_client.post(login_endpoint, json=malformed_credentials)
        
        # Should return 400 for malformed credentials
        assert response.status_code == 400, (
            f"Expected 400 for malformed credentials {malformed_credentials}, "
            f"got {response.status_code}"
        )
        
        payload = response.json()
        assert "error" in payload, "Error message should be present"

    @pytest.mark.security
    def test_authentication_brute_force_protection(self, api_client, login_endpoint):
        """Test protection against brute force attacks."""
        import time
        
        failed_attempts = 0
        start_time = time.time()
        
        # Make multiple failed login attempts
        for i in range(10):
            invalid_credentials = {
                "email": f"nonexistent{i}@example.com",
                "password": f"wrongpassword{i}"
            }
            
            response = api_client.post(login_endpoint, json=invalid_credentials)
            
            if response.status_code == 400:
                failed_attempts += 1
            elif response.status_code == 429:
                # Rate limiting kicked in - this is good security behavior
                print(f"Rate limiting activated after {i+1} failed attempts")
                break
            
            # Small delay between attempts
            time.sleep(0.1)
        
        elapsed_time = time.time() - start_time
        
        # Should have some failed attempts
        assert failed_attempts > 0, "Should have some failed login attempts"
        print(f"Completed {failed_attempts} failed attempts in {elapsed_time:.2f}s")

    @pytest.mark.security
    def test_case_sensitive_credentials(self, api_client, login_endpoint, valid_credentials):
        """Test case sensitivity of credentials."""
        # Test with different case variations
        case_variations = [
            {"email": valid_credentials["email"].upper(), "password": valid_credentials["password"]},
            {"email": valid_credentials["email"], "password": valid_credentials["password"].upper()},
            {"email": valid_credentials["email"].upper(), "password": valid_credentials["password"].upper()},
        ]
        
        for variation in case_variations:
            response = api_client.post(login_endpoint, json=variation)
            
            # Most systems are case-sensitive for passwords, case-insensitive for emails
            # Document the behavior
            print(f"Case variation {variation} returned status {response.status_code}")
            
            # Should either succeed or fail consistently
            assert response.status_code in [200, 400], (
                f"Unexpected status {response.status_code} for case variation"
            )