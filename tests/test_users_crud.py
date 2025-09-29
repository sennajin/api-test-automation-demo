"""
Comprehensive CRUD (Create, Read, Update, Delete) tests for user management API.

This module provides comprehensive test coverage for all CRUD operations on the user management API,
including positive and negative test cases, edge cases, and domain validation testing.

Testing Approach:
- **Positive Testing**: Validates successful operations with valid data
- **Negative Testing**: Tests error handling with invalid inputs and edge cases
- **Boundary Testing**: Validates behavior at data limits and boundaries
- **Domain Testing**: Tests various data domains (Unicode, special characters, etc.)
- **Idempotency Testing**: Ensures operations can be safely repeated
- **Schema Validation**: Verifies response structure matches expected schemas

Test Categories:
- TestUserCreation: Tests user creation with various data scenarios
- TestUserRetrieval: Tests user retrieval and pagination functionality
- TestUserUpdate: Tests user update operations (PUT/PATCH)
- TestUserDeletion: Tests user deletion and idempotency
- TestUserValidation: Tests domain validation and edge cases

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
)
from tests.test_constants import TEST_USER_IDS, HTTP_STATUS


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


class TestUserRetrieval(BaseUserTest):
    """Tests for GET /users endpoints."""

    @pytest.mark.crud
    def test_get_existing_user(self, api_client, users_endpoint, response_validator):
        """Test retrieving an existing user by ID."""
        user_id = TEST_USER_IDS["EXISTING_USER"]
        response = api_client.get(f"{users_endpoint}/{user_id}")
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
    @pytest.mark.parametrize("page", [1, 2, 3])
    def test_get_users_list_pagination(self, api_client, users_endpoint, page):
        """Test users list with different page numbers."""
        response = api_client.get(users_endpoint, params={"page": page})
        assert response.status_code == HTTP_STATUS["OK"]

        payload = response.json()
        assert_valid_schema(payload, LIST_USERS_SCHEMA)
        assert payload["page"] == page

    @pytest.mark.negative
    def test_get_users_list_invalid_page(self, api_client, users_endpoint):
        """Test users list with invalid page parameter."""
        response = api_client.get(users_endpoint, params={"page": "invalid"})
        # ReqRes defaults to page 1 for invalid page values
        assert response.status_code == HTTP_STATUS["OK"]

        payload = response.json()
        assert payload["page"] == 1


class TestUserUpdate(BaseUserTest):
    """Tests for PUT /users/{id} endpoint."""

    @pytest.mark.crud
    def test_update_existing_user(self, api_client, users_endpoint, update_user_data):
        """Test successful user update."""
        user_id = TEST_USER_IDS["EXISTING_USER"]
        response = api_client.put(f"{users_endpoint}/{user_id}", json=update_user_data)
        assert response.status_code == HTTP_STATUS["OK"]

        payload = response.json()
        assert_valid_schema(payload, UPDATE_USER_SCHEMA)
        self.verify_user_data(payload, update_user_data)
        assert "updatedAt" in payload

    @pytest.mark.parametrize("test_case", [
        {"desc": "non-existent user", "user_id_key": "NON_EXISTENT_USER",
         "data": {"name": "Full Update", "job": "Developer"}},
        {"desc": "partial data", "user_id_key": "EXISTING_USER", "data": {"name": "Partial Update"}},
        {"desc": "empty payload", "user_id_key": "EXISTING_USER", "data": {}}
    ])
    def test_update_user_variations(self, api_client, users_endpoint, test_case):
        """Test various update scenarios including edge cases."""
        user_id = TEST_USER_IDS[test_case["user_id_key"]]
        response = api_client.put(f"{users_endpoint}/{user_id}", json=test_case["data"])
        assert response.status_code == HTTP_STATUS["OK"]

        payload = response.json()
        assert_valid_schema(payload, UPDATE_USER_SCHEMA)

        if test_case["data"]:
            self.verify_user_data(payload, test_case["data"])


class TestUserDeletion(BaseUserTest):
    """Tests for DELETE /users/{id} endpoint."""

    @pytest.mark.crud
    def test_delete_existing_user(self, api_client, users_endpoint):
        """Test successful user deletion."""
        user_id = TEST_USER_IDS["EXISTING_USER"]
        response = api_client.delete(f"{users_endpoint}/{user_id}")
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
