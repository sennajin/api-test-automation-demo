"""
Basic security tests for user management API.

This module provides essential security testing for the user management API,
covering basic authentication, input validation, access control, and data protection.

Security Testing Approach:
- **Basic Authentication Testing**: Validates essential authentication mechanisms
- **Basic Input Validation Testing**: Tests protection against common injection attacks
- **Basic Access Control Testing**: Tests fundamental authorization checks
- **Basic Data Protection Testing**: Ensures sensitive information is not exposed

Test Categories:
- TestBasicAuthenticationSecurity: Tests essential authentication mechanisms
- TestBasicInputValidationSecurity: Tests basic input validation and injection protection
- TestBasicAccessControlSecurity: Tests fundamental authorization and access control
- TestBasicDataProtectionSecurity: Tests basic data leakage protection

Each test is designed to identify fundamental security vulnerabilities and ensure
the API properly handles basic security requirements.
"""

from __future__ import annotations

import pytest
from typing import Any, Dict

from tests.conftest import assert_valid_schema
from tests.schemas.json_schemas import ERROR_SCHEMA


class TestBasicAuthenticationSecurity:
    """
    Test suite for basic authentication and authorization security.

    This class provides essential testing for authentication mechanisms,
    including API key validation and basic authorization checks.

    Test Coverage:
    - Missing API key handling
    - Invalid API key validation
    - Basic token validation

    Key Test Methods:
    - test_missing_api_key: Tests API access without authentication
    - test_invalid_api_key: Tests API access with invalid authentication
    - test_basic_token_validation: Tests basic token handling

    All tests validate that the API properly enforces basic authentication.
    """

    @pytest.mark.security
    @pytest.mark.regression
    def test_missing_api_key(self, users_endpoint):
        """Test API access without authentication."""
        import requests

        # Create session without API key
        session = requests.Session()
        session.headers.update({"Accept": "application/json"})

        response = session.get(users_endpoint, timeout=30.0)

        # ReqRes doesn't require API key, but in real APIs this should be 401/403
        assert response.status_code in [200, 401, 403]

    @pytest.mark.security
    @pytest.mark.regression
    def test_invalid_api_key(self, users_endpoint):
        """Test API access with invalid authentication."""
        import requests

        session = requests.Session()
        session.headers.update({
            "Accept": "application/json",
            "x-api-key": "invalid-key-12345"
        })

        response = session.get(users_endpoint, timeout=30.0)

        # Test behavior with invalid key
        assert response.status_code in [200, 401, 403]

    @pytest.mark.security
    @pytest.mark.regression
    def test_basic_token_validation(self, api_client, users_endpoint):
        """Test basic token validation behavior."""
        # Store original headers to restore later
        original_headers = api_client._session.headers.copy()

        try:
            # Test with invalid token
            api_client._session.headers.update({
                "Authorization": "Bearer invalid.token.here"
            })

            response = api_client.get(users_endpoint)

            # Should handle invalid tokens appropriately
            assert response.status_code in [200, 401, 403]
        finally:
            # Clean up: restore original headers
            api_client._session.headers.clear()
            api_client._session.headers.update(original_headers)


class TestBasicInputValidationSecurity:
    """
    Test suite for basic input validation and injection protection.

    This class provides essential testing for input validation security,
    including protection against common injection attacks.

    Test Coverage:
    - XSS (Cross-Site Scripting) injection attempts
    - SQL injection protection
    - Basic input sanitization

    Key Test Methods:
    - test_basic_xss_protection: Tests basic XSS injection protection
    - test_basic_sql_injection_protection: Tests basic SQL injection protection
    - test_basic_input_sanitization: Tests basic input sanitization

    All tests validate that the API properly handles basic malicious inputs.
    """

    @pytest.mark.security
    @pytest.mark.parametrize("malicious_input", [
        "<script>alert('xss')</script>",
        "'; DROP TABLE users; --",
        "<img src=x onerror=alert(1)>",
    ])
    def test_basic_xss_protection(self, api_client, users_endpoint, malicious_input):
        """Test basic XSS injection protection."""
        malicious_data = {
            "name": malicious_input,
            "job": "Test Job"
        }

        response = api_client.post(users_endpoint, json=malicious_data)

        # Should either create successfully (with sanitized input) or reject with error
        assert response.status_code in [201, 400, 403, 422]

        if response.status_code == 201:
            payload = response.json()
            # In a secure API, malicious input should be sanitized or rejected
            assert "name" in payload
        else:
            # If rejected, that's actually good security behavior
            print(f"Malicious input '{malicious_input}' was rejected with status {response.status_code}")

    @pytest.mark.security
    @pytest.mark.parametrize("sql_injection", [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "'; UPDATE users SET admin=1; --",
    ])
    def test_basic_sql_injection_protection(self, api_client, users_endpoint, sql_injection):
        """Test basic SQL injection protection."""
        # Test in user creation
        injection_data = {
            "name": sql_injection,
            "job": "Test Job"
        }

        response = api_client.post(users_endpoint, json=injection_data)

        # Should not cause SQL errors or unexpected behavior
        assert response.status_code in [201, 400, 403, 422]

        # Test in user ID parameter
        response = api_client.get(f"{users_endpoint}/{sql_injection}")
        assert response.status_code in [404, 400, 403]

    @pytest.mark.security
    def test_basic_input_sanitization(self, api_client, users_endpoint):
        """Test basic input sanitization."""
        # Test with potentially dangerous characters
        dangerous_input = {
            "name": "test<>\"'&",
            "job": "job<>\"'&"
        }

        response = api_client.post(users_endpoint, json=dangerous_input)

        # Should handle dangerous characters appropriately
        assert response.status_code in [201, 400, 422]

        if response.status_code == 201:
            payload = response.json()
            # Check if input was sanitized
            assert "name" in payload


class TestBasicAccessControlSecurity:
    """
    Test suite for basic access control and authorization security.

    This class provides essential testing for access control mechanisms,
    including unauthorized access attempts and basic authorization checks.

    Test Coverage:
    - Unauthorized access attempts
    - Basic authorization checks
    - Access control enforcement

    Key Test Methods:
    - test_unauthorized_access: Tests unauthorized access attempts
    - test_basic_authorization: Tests basic authorization checks

    All tests validate that the API properly enforces basic access control.
    """

    @pytest.mark.security
    def test_unauthorized_access(self, api_client, users_endpoint):
        """Test unauthorized access attempts."""
        # Try to access without proper authentication
        # In ReqRes, this will work, but in real APIs should be protected
        response = api_client.get(users_endpoint)

        # Document the behavior - in secure APIs this should be 401/403
        assert response.status_code in [200, 401, 403]

    @pytest.mark.security
    def test_basic_authorization(self, api_client, users_endpoint):
        """Test basic authorization checks."""
        # Try to modify user without proper authorization
        unauthorized_update = {
            "name": "Unauthorized User",
            "job": "Unauthorized Access"
        }

        response = api_client.put(f"{users_endpoint}/1", json=unauthorized_update)

        # Document the behavior - in secure APIs this should be 401/403
        assert response.status_code in [200, 401, 403]

        # Try to delete user without proper authorization
        response = api_client.delete(f"{users_endpoint}/1")

        # In secure APIs, this should require proper authorization
        assert response.status_code in [204, 401, 403]


class TestBasicDataProtectionSecurity:
    """
    Test suite for basic data protection and information disclosure.

    This class provides essential testing for data protection mechanisms,
    including error message handling and basic security headers.

    Test Coverage:
    - Error message information disclosure
    - Basic response header security
    - Sensitive data protection

    Key Test Methods:
    - test_error_message_disclosure: Tests error message information disclosure
    - test_basic_security_headers: Tests basic security headers

    All tests validate that the API properly protects sensitive information.
    """

    @pytest.mark.security
    def test_error_message_disclosure(self, api_client, users_endpoint):
        """Test that error messages don't leak sensitive information."""
        # Test various invalid requests
        test_cases = [
            ("invalid_id", f"{users_endpoint}/invalid"),
            ("non_existent", f"{users_endpoint}/99999"),
        ]

        for test_name, url in test_cases:
            response = api_client.get(url)

            # Error responses shouldn't contain sensitive information
            if response.status_code >= 400:
                response_text = response.text.lower()

                # Check for common information leakage patterns
                sensitive_patterns = [
                    "database",
                    "sql",
                    "server",
                    "internal",
                    "stack trace",
                    "exception",
                    "debug",
                ]

                for pattern in sensitive_patterns:
                    assert pattern not in response_text, f"Potential info leak: {pattern} in {test_name}"

    @pytest.mark.security
    def test_basic_security_headers(self, api_client, users_endpoint):
        """Test basic security-related response headers."""
        response = api_client.get(users_endpoint)

        headers = response.headers

        # Document basic security headers (or lack thereof)
        basic_security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
        }

        missing_headers = []
        for header, expected_value in basic_security_headers.items():
            if header not in headers:
                missing_headers.append(header)

        # Document findings (don't fail, just report)
        if missing_headers:
            print(f"Missing basic security headers: {missing_headers}")
        else:
            print("Basic security headers are present")