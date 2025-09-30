"""
API endpoint tests for the ReqRes.in API.

This module provides test coverage for all API endpoints including
CRUD operations, authentication, and performance testing.

Testing Approach:
- **Positive Testing**: Validates successful operations with valid data
- **Negative Testing**: Tests error handling with invalid inputs and edge cases
- **Boundary Testing**: Validates behavior at data limits and boundaries
- **Domain Testing**: Tests various data domains (Unicode, special characters, etc.)
- **IRepeatability Testing**: Ensures operations can be safely repeated
- **Schema Validation**: Verifies response structure matches expected schemas

Test Categories:
- TestUserCreation: Tests user creation with various data scenarios
- TestUserRetrieval: Tests user retrieval and pagination functionality
- TestUserUpdate: Tests user update operations (PUT/PATCH)
- TestUserDeletion: Tests user deletion and repeatability
- TestAuthentication: Tests login, register, and logout functionality
- TestPerformance: Tests response time and SLA compliance

Each test class is designed to be independent and can be run in isolation.
Tests use pytest fixtures for setup and teardown, with proper error handling
and assertion messages for debugging.
"""

from __future__ import annotations
import pytest
from typing import Any, Dict

from tests.conftest import assert_valid_schema, verify_user_creation_response, xfail_if_rate_limited
from tests.schemas.json_schemas import (
    CREATE_USER_SCHEMA,
    UPDATE_USER_SCHEMA,
    SINGLE_USER_SCHEMA,
    LIST_USERS_SCHEMA,
    ERROR_SCHEMA,
    RESOURCE_LIST_SCHEMA,
    LOGIN_SUCCESS_SCHEMA,
    LOGIN_ERROR_SCHEMA,
    REGISTER_SUCCESS_SCHEMA,
)
from tests.test_constants import TEST_USER_IDS, HTTP_STATUS, TEST_PATTERNS


class BaseUserTest:
    """Base class for all user tests with common methods."""

    def verify_user_data(self, payload: Dict[str, Any], expected_data: Dict[str, Any]) -> None:
        """Verify user data matches expected values."""
        for key, value in expected_data.items():
            assert payload[key] == value


class TestUserCreation(BaseUserTest):
    """Tests for POST /users endpoint."""

    @pytest.mark.crud
    def test_create_user_with_valid_data(self, api_client, users_endpoint, valid_user_data):
        """Test successful user creation with valid data."""
        response = api_client.post(users_endpoint, json=valid_user_data, bulk_mode=True)
        assert response.status_code == HTTP_STATUS["CREATED"]

        payload = response.json()
        assert_valid_schema(payload, CREATE_USER_SCHEMA)
        self.verify_user_data(payload, valid_user_data)
        assert "id" in payload
        assert "createdAt" in payload

    @pytest.mark.negative
    @pytest.mark.parametrize("test_case", [
        {"desc": "empty name", "field": "name", "value": ""},
        {"desc": "null name", "field": "name", "value": None},
        {"desc": "empty job", "field": "job", "value": ""},
        {"desc": "null job", "field": "job", "value": None},
        {"desc": "missing job field", "field": "job", "value": "__REMOVE__"},
        {"desc": "empty payload", "payload": {}}
    ])
    def test_create_user_invalid_data(self, api_client, users_endpoint, test_case, valid_user_data):
        """Test user creation with various invalid data scenarios."""
        if "payload" in test_case:
            user_data = test_case["payload"]
        else:
            user_data = valid_user_data.copy()
            if test_case["value"] == "__REMOVE__":
                user_data.pop(test_case["field"], None)
            else:
                user_data[test_case["field"]] = test_case["value"]

        response = api_client.post(users_endpoint, json=user_data, bulk_mode=True)
        # Handle rate limiting gracefully
        xfail_if_rate_limited(response, "user creation with invalid data")
        # ReqRes API is permissive, but we document the actual behavior
        assert response.status_code in [HTTP_STATUS["CREATED"], HTTP_STATUS["BAD_REQUEST"]]

    @pytest.mark.negative
    @pytest.mark.data_validation
    def test_create_user_with_extra_fields(self, api_client, users_endpoint):
        """Test user creation with additional fields."""
        user_data = {
            "name": "Test User",
            "job": "Tester",
            "email": "test@example.com",  # Extra field
            "age": 30  # Extra field
        }
        response = api_client.post(users_endpoint, json=user_data, bulk_mode=True)
        assert response.status_code == HTTP_STATUS["CREATED"]

        payload = response.json()
        expected_data = {"name": user_data["name"], "job": user_data["job"]}
        self.verify_user_data(payload, expected_data)

    @pytest.mark.data_validation
    @pytest.mark.parametrize("pattern_key,test_value", [
        ("SPECIAL_CHARS", TEST_PATTERNS["SPECIAL_CHARS"]),
        ("UNICODE_CHARS", TEST_PATTERNS["UNICODE_CHARS"]),
    ])
    def test_create_user_with_unicode_and_special_chars(self, api_client, users_endpoint, pattern_key, test_value):
        """Test user creation with Unicode and special characters."""
        user_data = {
            "name": test_value,
            "job": f"Test Job {pattern_key}"
        }
        response = api_client.post(users_endpoint, json=user_data, bulk_mode=True)
        assert response.status_code == HTTP_STATUS["CREATED"]

        payload = response.json()
        assert_valid_schema(payload, CREATE_USER_SCHEMA)
        self.verify_user_data(payload, user_data)

    @pytest.mark.negative
    def test_create_user_with_empty_string(self, api_client, users_endpoint):
        """Test user creation with empty string (should fail validation)."""
        user_data = {
            "name": "",  # Empty string should fail
            "job": "Test Job"
        }
        response = api_client.post(users_endpoint, json=user_data, bulk_mode=True)
        # Empty string should either be rejected or handled gracefully
        assert response.status_code in [HTTP_STATUS["CREATED"], HTTP_STATUS["BAD_REQUEST"]]
        
        if response.status_code == HTTP_STATUS["CREATED"]:
            # If API accepts empty string, verify it's handled correctly
            payload = response.json()
            # Don't validate schema for this edge case as it may not meet requirements
            print(f"API accepted empty string: {payload}")


class TestUserRetrieval(BaseUserTest):
    """Tests for GET /users endpoints."""

    @pytest.mark.crud
    def test_get_existing_user(self, api_client, users_endpoint, response_validator):
        """Test retrieving an existing user by ID."""
        user_id = TEST_USER_IDS["EXISTING_USER"]
        response = api_client.get(f"{users_endpoint}/{user_id}")
        # Handle rate limiting gracefully
        xfail_if_rate_limited(response, "user retrieval")
        payload = response_validator(response, HTTP_STATUS["OK"], SINGLE_USER_SCHEMA)

        # Verify the returned user ID matches the requested ID
        assert payload["data"]["id"] == user_id

    @pytest.mark.negative
    @pytest.mark.parametrize("user_id_key, expected_status", [
        ("NON_EXISTENT_USER", "NOT_FOUND"),
        ("INVALID_USER", "NOT_FOUND")
    ])
    def test_get_user_negative_cases(self, api_client, users_endpoint, user_id_key, expected_status):
        """Test retrieving users with invalid or non-existent IDs."""
        user_id = TEST_USER_IDS[user_id_key]
        response = api_client.get(f"{users_endpoint}/{user_id}")
        assert response.status_code == HTTP_STATUS[expected_status]

        if expected_status == "NOT_FOUND":
            payload = response.json()
            assert payload == {}  # ReqRes returns empty object for 404

    @pytest.mark.crud
    def test_get_users_list(self, api_client, users_endpoint):
        """Test users list endpoint."""
        response = api_client.get(users_endpoint)
        # Handle rate limiting gracefully
        xfail_if_rate_limited(response, "users list")
        assert response.status_code == HTTP_STATUS["OK"]

        payload = response.json()
        assert_valid_schema(payload, LIST_USERS_SCHEMA)
        assert payload["data"], "Expected at least one user in the list"


class TestUserUpdate(BaseUserTest):
    """Tests for PUT /users/{id} endpoint."""

    @pytest.mark.crud
    def test_update_existing_user(self, api_client, users_endpoint, update_user_data):
        """Test successful user update."""
        user_id = TEST_USER_IDS["EXISTING_USER"]
        response = api_client.put(f"{users_endpoint}/{user_id}", json=update_user_data, bulk_mode=True)
        # Handle rate limiting gracefully
        xfail_if_rate_limited(response, "user update")
        assert response.status_code == HTTP_STATUS["OK"]

        payload = response.json()
        assert_valid_schema(payload, UPDATE_USER_SCHEMA)
        self.verify_user_data(payload, update_user_data)
        assert "updatedAt" in payload

    @pytest.mark.negative
    def test_update_non_existent_user(self, api_client, users_endpoint, update_user_data):
        """Test updating a user that doesn't exist."""
        user_id = TEST_USER_IDS["NON_EXISTENT_USER"]
        response = api_client.put(f"{users_endpoint}/{user_id}", json=update_user_data, bulk_mode=True)
        # Handle rate limiting gracefully
        xfail_if_rate_limited(response, "update non-existent user")
        # ReqRes API returns 200 even for non-existent users, but we document the behavior
        assert response.status_code == HTTP_STATUS["OK"]


class TestUserDeletion(BaseUserTest):
    """Tests for DELETE /users/{id} endpoint."""

    @pytest.mark.crud
    def test_delete_existing_user(self, api_client, users_endpoint):
        """Test successful user deletion."""
        user_id = TEST_USER_IDS["EXISTING_USER"]
        response = api_client.delete(f"{users_endpoint}/{user_id}")
        # Handle rate limiting gracefully
        xfail_if_rate_limited(response, "user deletion")
        assert response.status_code == HTTP_STATUS["NO_CONTENT"]
        assert not response.content  # Empty response body

    @pytest.mark.negative
    def test_delete_non_existent_user(self, api_client, users_endpoint):
        """Test deleting a user that doesn't exist."""
        user_id = TEST_USER_IDS["NON_EXISTENT_USER"]
        response = api_client.delete(f"{users_endpoint}/{user_id}")
        # ReqRes API returns 204 even for non-existent users, but we document the behavior
        assert response.status_code == HTTP_STATUS["NO_CONTENT"]

    @pytest.mark.negative
    def test_delete_user_twice(self, api_client, users_endpoint):
        """Test deleting a user twice (idempotency test)."""
        user_id = TEST_USER_IDS["EXISTING_USER"]

        # First deletion
        response = api_client.delete(f"{users_endpoint}/{user_id}")
        assert response.status_code == HTTP_STATUS["NO_CONTENT"]

        # Second deletion (should be idempotent)
        response = api_client.delete(f"{users_endpoint}/{user_id}")
        # ReqRes API returns 204 for the second deletion as well, showing idempotent behavior
        assert response.status_code == HTTP_STATUS["NO_CONTENT"]

    @pytest.mark.negative
    def test_delete_user_with_invalid_id(self, api_client, users_endpoint):
        """Test deleting a user with an invalid ID."""
        invalid_id = "invalid"
        response = api_client.delete(f"{users_endpoint}/{invalid_id}")
        # ReqRes API returns 204 even for invalid IDs, but we document the behavior
        assert response.status_code == HTTP_STATUS["NO_CONTENT"]


class TestAuthentication:
    """Tests for authentication endpoints."""

    @pytest.mark.security
    @pytest.mark.regression
    @pytest.mark.smoke
    def test_login_with_valid_credentials_returns_token(
            self, api_client, login_endpoint, valid_credentials
    ) -> None:
        """Test successful login with valid email and password returns a token."""
        response = api_client.post(login_endpoint, json=valid_credentials)

        assert response.status_code == 200
        payload = response.json()
        assert_valid_schema(payload, LOGIN_SUCCESS_SCHEMA)
        assert payload["token"], "Expected token to be present and non-empty"

    @pytest.mark.security
    @pytest.mark.regression
    @pytest.mark.smoke
    def test_login_with_missing_password_returns_error(
            self, api_client, login_endpoint, invalid_credentials
    ) -> None:
        """Test login with missing password returns 400 error."""
        response = api_client.post(login_endpoint, json=invalid_credentials)

        assert response.status_code == 400
        payload = response.json()
        assert_valid_schema(payload, LOGIN_ERROR_SCHEMA)
        assert "password" in payload["error"].lower(), "Error should mention missing password"

    @pytest.mark.security
    @pytest.mark.regression
    @pytest.mark.smoke
    def test_login_with_invalid_email_returns_error(
            self, api_client, login_endpoint
    ) -> None:
        """Test login with non-existent email returns error."""
        invalid_user_credentials = {
            "email": "nonexistent@example.com",
            "password": "somepassword"
        }
        response = api_client.post(login_endpoint, json=invalid_user_credentials)

        assert response.status_code == 400
        payload = response.json()
        assert_valid_schema(payload, LOGIN_ERROR_SCHEMA)
        assert payload["error"], "Expected error message to be present"

    @pytest.mark.security
    @pytest.mark.regression
    def test_login_with_empty_payload_returns_error(
            self, api_client, login_endpoint
    ) -> None:
        """Test login with empty JSON payload returns error."""
        response = api_client.post(login_endpoint, json={})

        assert response.status_code == 400
        payload = response.json()
        assert_valid_schema(payload, LOGIN_ERROR_SCHEMA)
        assert payload["error"], "Expected error message for empty payload"

    @pytest.mark.security
    @pytest.mark.regression
    @pytest.mark.smoke
    def test_register_with_valid_data_returns_token(
            self, api_client, register_endpoint, valid_credentials
    ) -> None:
        """Test successful user registration with valid email and password returns a token."""
        response = api_client.post(register_endpoint, json=valid_credentials)

        assert response.status_code == 200
        payload = response.json()
        assert_valid_schema(payload, REGISTER_SUCCESS_SCHEMA)
        assert payload["token"], "Expected token to be present and non-empty"
        assert payload["id"], "Expected user ID to be present"

    @pytest.mark.security
    @pytest.mark.regression
    @pytest.mark.smoke
    def test_register_with_missing_password_returns_error(
            self, api_client, register_endpoint, invalid_credentials
    ) -> None:
        """Test registration with missing password returns 400 error."""
        response = api_client.post(register_endpoint, json=invalid_credentials)

        assert response.status_code == 400
        payload = response.json()
        assert_valid_schema(payload, LOGIN_ERROR_SCHEMA)
        assert "password" in payload["error"].lower(), "Error should mention missing password"

    @pytest.mark.security
    @pytest.mark.regression
    @pytest.mark.smoke
    def test_register_with_invalid_email_returns_error(
            self, api_client, register_endpoint
    ) -> None:
        """Test registration with invalid email returns error."""
        invalid_user_credentials = {
            "email": "invalid-email",
            "password": "somepassword"
        }
        response = api_client.post(register_endpoint, json=invalid_user_credentials)

        assert response.status_code == 400
        payload = response.json()
        assert_valid_schema(payload, LOGIN_ERROR_SCHEMA)
        assert payload["error"], "Expected error message to be present"

    @pytest.mark.security
    @pytest.mark.regression
    def test_register_with_empty_payload_returns_error(
            self, api_client, register_endpoint
    ) -> None:
        """Test registration with empty JSON payload returns error."""
        response = api_client.post(register_endpoint, json={})

        assert response.status_code == 400
        payload = response.json()
        assert_valid_schema(payload, LOGIN_ERROR_SCHEMA)
        assert payload["error"], "Expected error message for empty payload"

    @pytest.mark.security
    @pytest.mark.regression
    @pytest.mark.smoke
    def test_logout_returns_success(
            self, api_client, logout_endpoint
    ) -> None:
        """Test logout endpoint returns success."""
        response = api_client.post(logout_endpoint)

        assert response.status_code == 200
        # Logout endpoint typically returns 200 OK with no content or minimal response


class TestPerformance:
    """Tests for performance and response time validation."""

    @pytest.mark.performance
    def test_create_user_response_time(self, api_client, users_endpoint, valid_user_data, performance_timer):
        """Test that user creation responds within acceptable time."""
        performance_timer.start()
        response = api_client.post(users_endpoint, json=valid_user_data, retry=False)
        performance_timer.stop()
        
        xfail_if_rate_limited(response, "create user")
        
        assert response.status_code == HTTP_STATUS["CREATED"]
        performance_timer.assert_within("RESPONSE_TIME_FAST")

    @pytest.mark.performance
    def test_get_users_list_response_time(self, api_client, users_endpoint):
        """Test that users list responds within acceptable time."""
        import time
        start_time = time.time()
        response = api_client.get(users_endpoint)
        response_time = time.time() - start_time
        
        xfail_if_rate_limited(response, "get users list")
        
        assert response.status_code == 200
        assert response_time < 2.0, f"Response time {response_time:.2f}s exceeds 2s threshold"

    @pytest.mark.performance
    def test_update_user_response_time(self, api_client, users_endpoint, update_user_data):
        """Test that user update responds within acceptable time."""
        import time
        user_id = 2
        start_time = time.time()
        response = api_client.put(f"{users_endpoint}/{user_id}", json=update_user_data, retry=False)
        response_time = time.time() - start_time
        
        xfail_if_rate_limited(response, "update user")
        
        assert response.status_code == 200
        assert response_time < 2.0, f"Response time {response_time:.2f}s exceeds 2s threshold"

    @pytest.mark.performance
    def test_delete_user_response_time(self, api_client, users_endpoint):
        """Test that user deletion responds within acceptable time."""
        import time
        user_id = 2
        start_time = time.time()
        response = api_client.delete(f"{users_endpoint}/{user_id}")
        response_time = time.time() - start_time
        
        xfail_if_rate_limited(response, "delete user")
        
        assert response.status_code == 204
        assert response_time < 2.0, f"Response time {response_time:.2f}s exceeds 2s threshold"

    @pytest.mark.performance
    def test_login_response_time(self, api_client, login_endpoint, valid_credentials):
        """Test that login responds within acceptable time."""
        import time
        start_time = time.time()
        response = api_client.post(login_endpoint, json=valid_credentials, retry=False)
        response_time = time.time() - start_time
        
        xfail_if_rate_limited(response, "login")
        
        assert response.status_code == 200
        assert response_time < 2.0, f"Response time {response_time:.2f}s exceeds 2s threshold"

    @pytest.mark.performance
    def test_register_response_time(self, api_client, register_endpoint, valid_credentials):
        """Test that registration responds within acceptable time."""
        import time
        start_time = time.time()
        response = api_client.post(register_endpoint, json=valid_credentials, retry=False)
        response_time = time.time() - start_time
        
        xfail_if_rate_limited(response, "register")
        
        assert response.status_code == 200
        assert response_time < 2.0, f"Response time {response_time:.2f}s exceeds 2s threshold"

    @pytest.mark.performance
    def test_logout_response_time(self, api_client, logout_endpoint):
        """Test that logout responds within acceptable time."""
        import time
        start_time = time.time()
        response = api_client.post(logout_endpoint, retry=False)
        response_time = time.time() - start_time
        
        xfail_if_rate_limited(response, "logout")
        
        assert response.status_code == 200
        assert response_time < 2.0, f"Response time {response_time:.2f}s exceeds 2s threshold"

    @pytest.mark.performance
    @pytest.mark.sla
    def test_basic_response_time_sla(self, api_client, users_endpoint):
        """Test that API response times meet basic SLA requirements."""
        import time
        
        # Define basic SLA thresholds
        sla_thresholds = {
            "GET": 3.0,      # 3 seconds for GET requests
            "POST": 5.0,     # 5 seconds for POST requests
            "PUT": 5.0,       # 5 seconds for PUT requests
            "DELETE": 3.0,    # 3 seconds for DELETE requests
        }
        
        sla_results = {}
        
        # Test GET requests
        start_time = time.time()
        response = api_client.get(users_endpoint)
        get_time = time.time() - start_time
        sla_results["GET"] = get_time
        
        assert response.status_code == 200
        assert get_time <= sla_thresholds["GET"], (
            f"GET request took {get_time:.2f}s, exceeds SLA threshold of {sla_thresholds['GET']}s"
        )
        
        # Test POST requests
        user_data = {"name": "SLA Test User", "job": "SLA Test Job"}
        start_time = time.time()
        response = api_client.post(users_endpoint, json=user_data, retry=False)
        post_time = time.time() - start_time
        sla_results["POST"] = post_time
        
        assert response.status_code == 201
        assert post_time <= sla_thresholds["POST"], (
            f"POST request took {post_time:.2f}s, exceeds SLA threshold of {sla_thresholds['POST']}s"
        )
        
        # Test PUT requests
        user_id = 2
        update_data = {"name": "SLA Updated User", "job": "SLA Updated Job"}
        start_time = time.time()
        response = api_client.put(f"{users_endpoint}/{user_id}", json=update_data, retry=False)
        put_time = time.time() - start_time
        sla_results["PUT"] = put_time
        
        assert response.status_code == 200
        assert put_time <= sla_thresholds["PUT"], (
            f"PUT request took {put_time:.2f}s, exceeds SLA threshold of {sla_thresholds['PUT']}s"
        )
        
        # Test DELETE requests
        start_time = time.time()
        response = api_client.delete(f"{users_endpoint}/{user_id}")
        delete_time = time.time() - start_time
        sla_results["DELETE"] = delete_time
        
        assert response.status_code == 204
        assert delete_time <= sla_thresholds["DELETE"], (
            f"DELETE request took {delete_time:.2f}s, exceeds SLA threshold of {sla_thresholds['DELETE']}s"
        )
        
        # Report SLA compliance
        print(f"Basic SLA Compliance Results:")
        for method, time_taken in sla_results.items():
            threshold = sla_thresholds[method]
            compliance = "✓ PASS" if time_taken <= threshold else "✗ FAIL"
            print(f"  {method}: {time_taken:.3f}s / {threshold}s {compliance}")

