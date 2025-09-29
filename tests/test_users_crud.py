<<<<<<< HEAD
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

=======
"""Comprehensive CRUD tests for user management API."""
>>>>>>> fa2d84e (moved schema validation helper to conftest.py)
from __future__ import annotations
import pytest
<<<<<<< HEAD

from tests.conftest import assert_valid_schema, verify_user_creation_response
=======
from typing import Any, Dict
from tests.conftest import assert_valid_schema
>>>>>>> fa2d84e (moved schema validation helper to conftest.py)
from tests.schemas.json_schemas import (
    CREATE_USER_SCHEMA,
    UPDATE_USER_SCHEMA,
    SINGLE_USER_SCHEMA,
    LIST_USERS_SCHEMA,
    ERROR_SCHEMA,
)
from tests.test_constants import TEST_USER_IDS, HTTP_STATUS


<<<<<<< HEAD
class TestUserCreation:
    """
    Test suite for user creation operations (POST /users).
    
    This class provides comprehensive testing for user creation functionality,
    covering both positive and negative test scenarios. It validates the API's
    behavior when creating users with various data inputs and edge cases.
    
    Test Coverage:
    - Valid user creation with proper data
    - Invalid field values and data types
    - Missing required fields
    - Empty and malformed payloads
    - Extra fields in requests
    - Edge cases with boundary values
    - Unicode and special character handling
    
    Key Test Methods:
    - test_create_user_with_valid_data: Tests successful user creation
    - test_create_user_with_invalid_fields: Tests validation with invalid data
    - test_create_user_with_missing_fields: Tests required field validation
    - test_create_user_with_empty_payload: Tests empty request handling
    - test_create_user_with_extra_fields: Tests additional field handling
    - test_create_user_edge_cases: Tests boundary values and edge cases
    
    All tests include proper error handling and schema validation to ensure
    the API responds correctly under various conditions.
    """
=======
class BaseUserTest:
    """Base class for all user tests with common methods."""

    def verify_user_data(self, payload: Dict[str, Any], expected_data: Dict[str, Any]) -> None:
        """Verify user data matches expected values."""
        for key, value in expected_data.items():
            assert payload[key] == value


class TestUserCreation(BaseUserTest):
    """Tests for POST /users endpoint."""
>>>>>>> fa2d84e (moved schema validation helper to conftest.py)

    @pytest.mark.crud
    def test_create_user_with_valid_data(self, api_client, users_endpoint, valid_user_data):
<<<<<<< HEAD
        """
        Test successful user creation with valid data.
        
        Purpose:
            Validates that the API successfully creates a user when provided with
            valid user data, including proper response structure and status code.
        
        Parameters:
            api_client: Configured API client for making requests
            users_endpoint: Base URL for users endpoint
            valid_user_data: Valid user data fixture containing name and job
        
        Assertions:
            - Response status code is 201 (Created)
            - Response body matches CREATE_USER_SCHEMA
            - Response contains the submitted user data
            - Response includes generated ID and timestamp
        
        Notes:
            This is a positive test case that verifies the happy path
            for user creation. The test uses the verify_user_creation_response
            helper function to validate both status code and response structure.
        """
        # Make API request to create user with valid data
        response = api_client.post(users_endpoint, json=valid_user_data)
        
        # Verify response using the helper from conftest.py
        # This validates status code, schema, and data consistency
        verify_user_creation_response(
            response=response,
            expected_status_code=201,
            expected_data=valid_user_data,
            schema=CREATE_USER_SCHEMA
        )
=======
        """Test successful user creation with valid data."""
        response = api_client.post(users_endpoint, json=valid_user_data, bulk_mode=True)
        assert response.status_code == HTTP_STATUS["CREATED"]

        payload = response.json()
        assert_valid_schema(payload, CREATE_USER_SCHEMA)
        self.verify_user_data(payload, valid_user_data)
        assert "id" in payload
        assert "createdAt" in payload
>>>>>>> fa2d84e (moved schema validation helper to conftest.py)

    @pytest.mark.negative
    @pytest.mark.parametrize("test_case", [
        {"desc": "empty name", "field": "name", "value": ""},
        {"desc": "null name", "field": "name", "value": None},
        {"desc": "empty job", "field": "job", "value": ""},
        {"desc": "null job", "field": "job", "value": None},
        {"desc": "missing job field", "field": "job", "value": "__REMOVE__"},
        {"desc": "empty payload", "payload": {}}
    ])
<<<<<<< HEAD
    def test_create_user_with_invalid_fields(self, api_client, users_endpoint, field, value):
        """
        Test user creation with invalid field values.
        
        Purpose:
            Validates that the API properly handles invalid field values
            such as empty strings and null values for required fields.
        
        Parameters:
            api_client: Configured API client for making requests
            users_endpoint: Base URL for users endpoint
            field: Field name to test (name or job)
            value: Invalid value to test (empty string or None)
        
        Assertions:
            - Response status code is either 201 (accepted) or 400 (validation error)
            - API handles invalid data gracefully without crashing
        
        Notes:
            This test uses parametrization to test multiple invalid field combinations.
            The ReqRes API is permissive and accepts these values, but in a real API
            you would expect 400 status codes for validation errors.
        """
        # Create base user data with valid values
        user_data = {"name": "Test User", "job": "Tester"}
        # Override the specified field with invalid value
        user_data[field] = value
        
        # Make API request with invalid field data
        response = api_client.post(users_endpoint, json=user_data, bulk_mode=True)
        
        # ReqRes API actually accepts these, but we test the behavior
        # In a real API, you'd expect 400 status codes for validation errors
        assert response.status_code in [201, 400], (
            f"Expected status code 201 or 400 for invalid field '{field}' with value {value}, "
            f"but got {response.status_code}. Response: {response.text}"
        )

    @pytest.mark.data_validation
    @pytest.mark.post
    @pytest.mark.parametrize("edge_case_data", [
        # Boundary values
        {"name": "A", "job": "B"},  # Single character
        {"name": "x" * 1000, "job": "y" * 1000},  # Very long strings
        {"name": "🚀", "job": "💻"},  # Emoji only
        {"name": "测试", "job": "工程师"},  # Non-ASCII
        {"name": "José María", "job": "Ingénieur"},  # Accented characters
        {"name": "User & Co.", "job": "R&D Engineer"},  # Special characters
        {"name": "123", "job": "456"},  # Numeric strings
        {"name": "User\nName", "job": "Test\nJob"},  # Newlines
        {"name": "User\tName", "job": "Test\tJob"},  # Tabs
        {"name": "  User  ", "job": "  Job  "},  # Leading/trailing spaces
    ])
    def test_create_user_edge_cases(self, api_client, users_endpoint, edge_case_data):
        """
        Test user creation with various edge cases.
        
        Purpose:
            Validates that the API properly handles edge case data including
            boundary values, Unicode characters, special characters, and whitespace.
        
        Parameters:
            api_client: Configured API client for making requests
            users_endpoint: Base URL for users endpoint
            edge_case_data: Dictionary containing edge case name and job values
        
        Assertions:
            - Response status code is 201 (Created)
            - Response contains the submitted edge case data
            - Data is preserved exactly as submitted (no truncation or modification)
        
        Notes:
            This test uses parametrization to test multiple edge case scenarios
            including Unicode, special characters, and boundary values.
        """
        # Make API request with edge case data
        response = api_client.post(users_endpoint, json=edge_case_data, bulk_mode=True)
        
        # Verify successful creation with edge case data
        assert response.status_code == 201, (
            f"Expected status code 201 for edge case data {edge_case_data}, "
            f"but got {response.status_code}. Response: {response.text}"
        )
        
        # Parse response and verify data integrity
        payload = response.json()
        # Ensure the API preserves the exact edge case data without modification
        assert payload["name"] == edge_case_data["name"]
        assert payload["job"] == edge_case_data["job"]

    @pytest.mark.negative
    @pytest.mark.data_validation
    @pytest.mark.post
    def test_create_user_with_missing_fields(self, api_client, users_endpoint):
        """Test user creation with missing required fields."""
        incomplete_data = {"name": "Test User"}  # Missing job
        
        response = api_client.post(users_endpoint, json=incomplete_data, bulk_mode=True)
        
        # ReqRes API is permissive, but test the behavior
        assert response.status_code in [201, 400], (
            f"Expected status code 201 or 400 for incomplete data, "
            f"but got {response.status_code}. Response: {response.text}"
        )

    @pytest.mark.negative
    @pytest.mark.post
    def test_create_user_with_empty_payload(self, api_client, users_endpoint):
        """Test user creation with empty JSON payload."""
        response = api_client.post(users_endpoint, json={}, bulk_mode=True)
        
        assert response.status_code in [201, 400], (
            f"Expected status code 201 or 400 for empty payload, "
            f"but got {response.status_code}. Response: {response.text}"
        )
=======
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
        # ReqRes API is permissive, but we document the actual behavior
        assert response.status_code in [HTTP_STATUS["CREATED"], HTTP_STATUS["BAD_REQUEST"]]
>>>>>>> fa2d84e (moved schema validation helper to conftest.py)

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
<<<<<<< HEAD
        
        assert response.status_code == 201, (
            f"Expected status code 201 for user creation with extra fields, "
            f"but got {response.status_code}. Response: {response.text}"
        )
        payload = response.json()
        assert payload["name"] == user_data["name"], (
            f"Expected name '{user_data['name']}' in response, but got '{payload['name']}'"
        )
        assert payload["job"] == user_data["job"], (
            f"Expected job '{user_data['job']}' in response, but got '{payload['job']}'"
        )


class TestUserRetrieval:
    """
    Test suite for user retrieval operations (GET /users).
    
    This class provides comprehensive testing for user retrieval functionality,
    including individual user retrieval, user listing, and pagination features.
    It covers both positive scenarios (successful retrievals) and negative scenarios
    (error handling for invalid requests).
    
    Test Coverage:
    - Retrieving existing users by ID
    - Handling non-existent user IDs
    - Invalid ID format handling
    - User list pagination functionality
    - Response schema validation
    - Error response validation
    
    Key Test Methods:
    - test_get_existing_user: Tests successful user retrieval
    - test_get_nonexistent_user: Tests 404 handling for missing users
    - test_get_user_with_invalid_id: Tests invalid ID format handling
    - test_get_users_list_pagination: Tests pagination functionality
    
    All tests validate response schemas and include proper error handling
    to ensure the API behaves correctly under various retrieval scenarios.
    """
=======
        assert response.status_code == HTTP_STATUS["CREATED"]

        payload = response.json()
        expected_data = {"name": user_data["name"], "job": user_data["job"]}
        self.verify_user_data(payload, expected_data)


class TestUserRetrieval(BaseUserTest):
    """Tests for GET /users endpoints."""
>>>>>>> fa2d84e (moved schema validation helper to conftest.py)

    @pytest.mark.crud
    def test_get_existing_user(self, api_client, users_endpoint, response_validator):
        """
        Test retrieving an existing user by ID.
        
        Purpose:
            Validates that the API successfully retrieves a user when provided
            with a valid, existing user ID, including proper response structure.
        
        Parameters:
            api_client: Configured API client for making requests
            users_endpoint: Base URL for users endpoint
            response_validator: Helper function for response validation
        
        Assertions:
            - Response status code is 200 (OK)
            - Response body matches SINGLE_USER_SCHEMA
            - Response contains the requested user data
            - User ID in response matches the requested ID
        
        Notes:
            This is a positive test case that verifies the happy path
            for user retrieval. Uses a known existing user ID from test constants.
        """
        # Use a known existing user ID from test constants
        user_id = TEST_USER_IDS["EXISTING_USER"]
        
        # Make API request to retrieve user by ID
        response = api_client.get(f"{users_endpoint}/{user_id}")
<<<<<<< HEAD
        
        # Validate response structure and status code
=======
>>>>>>> fa2d84e (moved schema validation helper to conftest.py)
        payload = response_validator(response, HTTP_STATUS["OK"], SINGLE_USER_SCHEMA)
        
        # Verify the returned user ID matches the requested ID
        assert payload["data"]["id"] == user_id, (
            f"Expected user ID {user_id} in response data, but got {payload['data']['id']}"
        )

    @pytest.mark.negative
    @pytest.mark.parametrize("user_id_key, expected_status", [
        ("NON_EXISTENT_USER", "NOT_FOUND"),
        ("INVALID_FORMAT", "NOT_FOUND")
    ])
    def test_get_user_negative_cases(self, api_client, users_endpoint, user_id_key, expected_status):
        """Test retrieving users with invalid or non-existent IDs."""
        user_id = TEST_USER_IDS[user_id_key]
        response = api_client.get(f"{users_endpoint}/{user_id}")
<<<<<<< HEAD
        
        assert response.status_code == HTTP_STATUS["NOT_FOUND"], (
            f"Expected status code 404 for non-existent user {user_id}, "
            f"but got {response.status_code}. Response: {response.text}"
        )
        payload = response.json()
        assert payload == {}, (
            f"Expected empty object for 404 response, but got: {payload}"
        )  # ReqRes returns empty object for 404

    @pytest.mark.negative
    @pytest.mark.get
    def test_get_user_with_invalid_id(self, api_client, users_endpoint):
        """Test retrieving user with invalid ID format."""
        invalid_id = "abc"
        response = api_client.get(f"{users_endpoint}/{invalid_id}")
        
        assert response.status_code == 404, (
            f"Expected status code 404 for invalid ID '{invalid_id}', "
            f"but got {response.status_code}. Response: {response.text}"
        )
=======
        assert response.status_code == HTTP_STATUS[expected_status]
>>>>>>> fa2d84e (moved schema validation helper to conftest.py)

        if expected_status == "NOT_FOUND":
            payload = response.json()
            assert payload == {}  # ReqRes returns empty object for 404

    @pytest.mark.crud
<<<<<<< HEAD
    @pytest.mark.get
    def test_get_users_list_pagination(self, api_client, users_endpoint):
        """Test users list pagination functionality."""
        response = api_client.get(users_endpoint, params={"page": 1})
        
        assert response.status_code == 200, (
            f"Expected status code 200 for users list pagination, "
            f"but got {response.status_code}. Response: {response.text}"
        )
=======
    @pytest.mark.parametrize("page", [1, 2, 3])
    def test_get_users_list_pagination(self, api_client, users_endpoint, page):
        """Test users list with different page numbers."""
        response = api_client.get(users_endpoint, params={"page": page})
        assert response.status_code == HTTP_STATUS["OK"]

>>>>>>> fa2d84e (moved schema validation helper to conftest.py)
        payload = response.json()
        assert_valid_schema(payload, LIST_USERS_SCHEMA)
        assert payload["page"] == 1, (
            f"Expected page 1 in pagination response, but got {payload['page']}"
        )

<<<<<<< HEAD


class TestUserUpdate:
    """
    Test suite for user update operations (PUT/PATCH /users/{id}).
    
    This class provides comprehensive testing for user update functionality,
    covering both PUT (full update) and PATCH (partial update) operations.
    It validates the API's behavior when updating users with various data inputs
    and edge cases.
    
    Test Coverage:
    - Successful user updates with valid data
    - Updating non-existent users
    - Partial data updates (PATCH operations)
    - Empty payload handling
    - Idempotency testing (repeated operations)
    - Operation consistency validation
    - Response schema validation
    
    Key Test Methods:
    - test_update_existing_user: Tests successful user update
    - test_update_nonexistent_user: Tests updating missing users
    - test_update_user_partial_data: Tests partial updates
    - test_put_operation_idempotency: Tests PUT idempotency
    - test_patch_operation_idempotency: Tests PATCH idempotency
    - test_put_operation_consistency: Tests operation consistency
    
    All tests include proper error handling and schema validation to ensure
    the API responds correctly under various update scenarios.
    """
=======
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
>>>>>>> fa2d84e (moved schema validation helper to conftest.py)

    @pytest.mark.crud
    def test_update_existing_user(self, api_client, users_endpoint, update_user_data):
        """Test successful user update."""
        user_id = TEST_USER_IDS["EXISTING_USER"]
        response = api_client.put(f"{users_endpoint}/{user_id}", json=update_user_data)
<<<<<<< HEAD
        
        assert response.status_code == 200, (
            f"Expected status code 200 for user update, "
            f"but got {response.status_code}. Response: {response.text}"
        )
        payload = response.json()
        assert_valid_schema(payload, UPDATE_USER_SCHEMA)
        
        # Verify updated data
        assert payload["name"] == update_user_data["name"], (
            f"Expected updated name '{update_user_data['name']}' in response, but got '{payload['name']}'"
        )
        assert payload["job"] == update_user_data["job"], (
            f"Expected updated job '{update_user_data['job']}' in response, but got '{payload['job']}'"
        )
        assert "updatedAt" in payload, (
            f"Expected 'updatedAt' field in response, but it was missing. Response: {payload}"
        )

    @pytest.mark.negative
    @pytest.mark.put
    def test_update_nonexistent_user(self, api_client, users_endpoint, update_user_data):
        """Test updating a non-existent user."""
        user_id = 999  # Non-existent user
        response = api_client.put(f"{users_endpoint}/{user_id}", json=update_user_data)
        
        # ReqRes returns 200 even for non-existent users in PUT
        assert response.status_code == 200, (
            f"Expected status code 200 for updating non-existent user {user_id}, "
            f"but got {response.status_code}. Response: {response.text}"
        )
        payload = response.json()
        assert_valid_schema(payload, UPDATE_USER_SCHEMA)


    @pytest.mark.crud
    @pytest.mark.put
    def test_update_user_partial_data(self, api_client, users_endpoint):
        """Test updating user with partial data."""
        user_id = 2
        partial_data = {"name": "Updated Name Only"}
        
        response = api_client.put(f"{users_endpoint}/{user_id}", json=partial_data)
        
        assert response.status_code == 200, (
            f"Expected status code 200 for partial user update, "
            f"but got {response.status_code}. Response: {response.text}"
        )
        payload = response.json()
        assert payload["name"] == partial_data["name"], (
            f"Expected updated name '{partial_data['name']}' in response, but got '{payload['name']}'"
        )

    @pytest.mark.negative
    @pytest.mark.put
    def test_update_user_with_empty_payload(self, api_client, users_endpoint):
        """Test updating user with empty payload."""
        user_id = 2
        response = api_client.put(f"{users_endpoint}/{user_id}", json={})
        
        assert response.status_code == 200, (
            f"Expected status code 200 for user update with empty payload, "
            f"but got {response.status_code}. Response: {response.text}"
        )

    @pytest.mark.crud
    @pytest.mark.put
    def test_put_operation_idempotency(self, api_client, users_endpoint):
        """Test that PUT operations are idempotent."""
        user_id = 2
        update_data = {
            "name": "Idempotent Test User",
            "job": "Idempotent Test Job"
        }
        
        # First PUT request
        response1 = api_client.put(f"{users_endpoint}/{user_id}", json=update_data)
        assert response1.status_code == 200
        payload1 = response1.json()
        
        # Second PUT request with same data
        response2 = api_client.put(f"{users_endpoint}/{user_id}", json=update_data)
        assert response2.status_code == 200
        payload2 = response2.json()
        
        # Results should be identical (idempotent)
        assert payload1["name"] == payload2["name"]
        assert payload1["job"] == payload2["job"]
        assert payload1["updatedAt"] == payload2["updatedAt"]

    @pytest.mark.crud
    @pytest.mark.patch
    def test_patch_operation_idempotency(self, api_client, users_endpoint):
        """Test that PATCH operations are idempotent."""
        user_id = 2
        patch_data = {"name": "Patched User"}
        
        # First PATCH request
        response1 = api_client.patch(f"{users_endpoint}/{user_id}", json=patch_data)
        assert response1.status_code == 200
        payload1 = response1.json()
        
        # Second PATCH request with same data
        response2 = api_client.patch(f"{users_endpoint}/{user_id}", json=patch_data)
        assert response2.status_code == 200
        payload2 = response2.json()
        
        # Results should be identical (idempotent)
        assert payload1["name"] == payload2["name"]
        assert payload1["updatedAt"] == payload2["updatedAt"]

    @pytest.mark.crud
    @pytest.mark.put
    @pytest.mark.parametrize("update_data", [
        {"name": "Test User 1", "job": "Test Job 1"},
        {"name": "Test User 2", "job": "Test Job 2"},
        {"name": "Test User 3", "job": "Test Job 3"},
    ])
    def test_put_operation_consistency(self, api_client, users_endpoint, update_data):
        """Test PUT operation consistency with parameterized data."""
        user_id = 2
        response = api_client.put(f"{users_endpoint}/{user_id}", json=update_data)
        
        assert response.status_code == 200
        payload = response.json()
        assert payload["name"] == update_data["name"]
        assert payload["job"] == update_data["job"]
        assert "updatedAt" in payload



class TestUserDeletion:
    """
    Test suite for user deletion operations (DELETE /users/{id}).
    
    This class provides comprehensive testing for user deletion functionality,
    covering both positive scenarios (successful deletions) and negative scenarios
    (error handling for invalid requests). It validates the API's behavior when
    deleting users and ensures proper idempotency.
    
    Test Coverage:
    - Successful user deletion
    - Deleting non-existent users
    - Invalid ID format handling
    - Idempotency testing (deleting same user multiple times)
    - Deletion consistency validation
    - Response validation (empty body for successful deletion)
    
    Key Test Methods:
    - test_delete_existing_user: Tests successful user deletion
    - test_delete_nonexistent_user: Tests deleting missing users
    - test_delete_user_with_invalid_id: Tests invalid ID handling
    - test_delete_user_twice: Tests deletion idempotency
    - test_delete_user_consistency: Tests deletion consistency
    
    All tests validate response codes and body content to ensure
    the API behaves correctly under various deletion scenarios.
    """

    @pytest.mark.crud
    @pytest.mark.delete
    def test_delete_existing_user(self, api_client, users_endpoint):
        """Test successful user deletion."""
        user_id = 2  # Known user in ReqRes
        response = api_client.delete(f"{users_endpoint}/{user_id}")
        
        assert response.status_code == 204, (
            f"Expected status code 204 for user deletion, "
            f"but got {response.status_code}. Response: {response.text}"
        )
        assert response.text == "", (
            f"Expected empty response body for successful deletion, but got: '{response.text}'"
        )  # No content expected

    @pytest.mark.negative
    @pytest.mark.delete
    def test_delete_nonexistent_user(self, api_client, users_endpoint):
        """Test deleting a non-existent user."""
        user_id = 999  # Non-existent user
        response = api_client.delete(f"{users_endpoint}/{user_id}")
        
        # ReqRes returns 204 even for non-existent users
        assert response.status_code == 204, (
            f"Expected status code 204 for deleting non-existent user {user_id}, "
            f"but got {response.status_code}. Response: {response.text}"
        )


    @pytest.mark.negative
    @pytest.mark.delete
    def test_delete_user_with_invalid_id(self, api_client, users_endpoint):
        """Test deleting user with invalid ID format."""
        invalid_id = "abc"
        response = api_client.delete(f"{users_endpoint}/{invalid_id}")
        
        # ReqRes returns 204 even for invalid IDs
        assert response.status_code == 204, (
            f"Expected status code 204 for deleting user with invalid ID '{invalid_id}', "
            f"but got {response.status_code}. Response: {response.text}"
        )

    @pytest.mark.negative
    @pytest.mark.delete
    def test_delete_user_twice(self, api_client, users_endpoint):
        """Test deleting the same user twice (idempotency test)."""
        user_id = 2  # Known user in ReqRes
        
        # First deletion
        response1 = api_client.delete(f"{users_endpoint}/{user_id}")
        assert response1.status_code == 204, (
            f"Expected status code 204 for first deletion of user {user_id}, "
            f"but got {response1.status_code}. Response: {response1.text}"
        )
        assert response1.text == "", (
            f"Expected empty response body for first deletion, but got: '{response1.text}'"
        )
        
        # Second deletion of the same user
        response2 = api_client.delete(f"{users_endpoint}/{user_id}")
        
        # ReqRes returns 204 even for already deleted users (idempotent behavior)
        # In real APIs, this might return 404 or 204 depending on implementation
        assert response2.status_code in [204, 404], (
            f"Expected status code 204 or 404 for second deletion of user {user_id}, "
            f"but got {response2.status_code}. Response: {response2.text}"
        )
        if response2.status_code == 204:
            assert response2.text == "", (
                f"Expected empty response body for second deletion, but got: '{response2.text}'"
            )

    @pytest.mark.crud
    @pytest.mark.delete
    def test_delete_user_consistency(self, api_client, users_endpoint):
        """Test user deletion behavior consistency."""
        user_id = 2  # Use a single known user ID
        response = api_client.delete(f"{users_endpoint}/{user_id}")
        
        assert response.status_code == 204, (
            f"Expected status code 204 for user deletion consistency test, "
            f"but got {response.status_code}. Response: {response.text}"
        )
        assert response.text == "", (
            f"Expected empty response body for deletion consistency test, but got: '{response.text}'"
        )


class TestUserValidation:
    """
    Test suite for domain validation and edge case testing.
    
    This class provides comprehensive domain validation testing for user-related
    fields and parameters. It uses parameterized tests to validate various
    domain constraints, boundary cases, special characters, and data types.
    
    Test Coverage:
    - Name field domain validation (Unicode, special characters, length)
    - Job field domain validation (various job titles and formats)
    - User ID domain validation (valid/invalid ID ranges)
    - Pagination domain validation (page number handling)
    - Data type domain validation (string, number, boolean, null, array, object)
    - String length boundary testing
    - Unicode character support testing
    
    Key Test Methods:
    - test_name_domain_validation: Tests name field with various domains
    - test_job_domain_validation: Tests job field with various domains
    - test_user_id_domain_validation: Tests user ID validation
    - test_page_domain_validation: Tests pagination parameter validation
    - test_data_type_domain_validation: Tests different data types
    - test_string_length_domain_validation: Tests string length boundaries
    - test_unicode_domain_validation: Tests Unicode character support
    
    All tests use domain testing techniques to ensure robust input handling
    and proper validation on the API side.
    """

    @pytest.mark.data_validation
    @pytest.mark.post
    @pytest.mark.parametrize("name_domain,expected_status", [
        # Valid domain - normal strings
        ("John Doe", 201),
        ("Jane Smith", 201),
        ("José María", 201),
        ("张三李四", 201),
        
        # Boundary domain - single character
        ("A", 201),
        ("Z", 201),
        ("1", 201),
        
        # Boundary domain - empty string (edge case)
        ("", 201),  # ReqRes accepts empty strings
        
        # Boundary domain - very long strings
        ("x" * 100, 201),
        ("x" * 1000, 201),
        ("x" * 10000, 201),
        
        # Special character domain
        ("John O'Connor", 201),
        ("José-María", 201),
        ("User & Co.", 201),
        ("Test@Company", 201),
        
        # Numeric string domain
        ("12345", 201),
        ("User123", 201),
        ("123User", 201),
        
        # Unicode domain
        ("🚀 Developer", 201),
        ("测试用户", 201),
        ("Пользователь", 201),
        ("مستخدم", 201),
    ])
    def test_name_domain_validation(self, api_client, users_endpoint, name_domain, expected_status):
        """Test name field domain validation using domain testing techniques."""
        user_data = {
            "name": name_domain,
            "job": "Engineer"
        }
        
        response = api_client.post(users_endpoint, json=user_data, bulk_mode=True)
        assert response.status_code == expected_status
        
        if response.status_code == 201:
            payload = response.json()
            assert_valid_schema(payload, CREATE_USER_SCHEMA)
            assert payload["name"] == name_domain

    @pytest.mark.data_validation
    @pytest.mark.post
    @pytest.mark.parametrize("job_domain,expected_status", [
        # Valid domain - normal job titles
        ("Software Engineer", 201),
        ("Data Scientist", 201),
        ("Product Manager", 201),
        ("QA Engineer", 201),
        
        # Boundary domain - single word
        ("Engineer", 201),
        ("Manager", 201),
        ("Analyst", 201),
        
        # Boundary domain - empty string
        ("", 201),  # ReqRes accepts empty strings
        
        # Long job title domain
        ("Senior Software Engineer with 10+ years experience", 201),
        ("x" * 100, 201),
        ("x" * 1000, 201),
        
        # Special character domain
        ("R&D Engineer", 201),
        ("C++ Developer", 201),
        ("Front-end Developer", 201),
        ("Back-end Developer", 201),
        
        # Numeric domain
        ("Engineer Level 3", 201),
        ("Senior Engineer (Grade 5)", 201),
        ("123 Engineer", 201),
        
        # Unicode domain
        ("Développeur", 201),
        ("Ingénieur Logiciel", 201),
        ("مهندس برمجيات", 201),
        ("软件工程师", 201),
    ])
    def test_job_domain_validation(self, api_client, users_endpoint, job_domain, expected_status):
        """Test job field domain validation using domain testing techniques."""
        user_data = {
            "name": "Test User",
            "job": job_domain
        }
        
        response = api_client.post(users_endpoint, json=user_data, bulk_mode=True)
        assert response.status_code == expected_status
        
        if response.status_code == 201:
            payload = response.json()
            assert_valid_schema(payload, CREATE_USER_SCHEMA)
            assert payload["job"] == job_domain

    @pytest.mark.data_validation
    @pytest.mark.get
    @pytest.mark.parametrize("user_id_domain,expected_status", [
        # Valid domain - existing user IDs
        (1, 200),
        (2, 200),
        (3, 200),
        (4, 200),
        (5, 200),
        (6, 200),
        
        # Boundary domain - edge cases
        (0, 404),  # Zero ID
        (-1, 404),  # Negative ID
        
        # Invalid domain - non-existent IDs
        (999, 404),
        (1000, 404),
        (9999, 404),
        
        # Invalid domain - non-numeric
        ("abc", 404),
        ("", 404),
        (None, 404),
    ])
    def test_user_id_domain_validation(self, api_client, users_endpoint, user_id_domain, expected_status):
        """Test user ID domain validation for GET operations."""
        response = api_client.get(f"{users_endpoint}/{user_id_domain}")
        assert response.status_code == expected_status

    @pytest.mark.data_validation
    @pytest.mark.get
    @pytest.mark.parametrize("page_domain,expected_status", [
        # Valid domain - existing pages
        (1, 200),
        (2, 200),
        (3, 200),
        
        # Boundary domain - edge cases
        (0, 200),  # ReqRes defaults to page 1
        (-1, 200),  # ReqRes defaults to page 1
        
        # Large page numbers
        (100, 200),
        (1000, 200),
        (9999, 200),
        
        # Invalid domain - non-numeric
        ("abc", 200),  # ReqRes defaults to page 1
        ("", 200),  # ReqRes defaults to page 1
        (None, 200),  # ReqRes defaults to page 1
    ])
    def test_page_domain_validation(self, api_client, users_endpoint, page_domain, expected_status):
        """Test pagination domain validation."""
        response = api_client.get(users_endpoint, params={"page": page_domain})
        assert response.status_code == expected_status
        
        if response.status_code == 200:
            payload = response.json()
            # ReqRes normalizes invalid page numbers to 1 for non-numeric values and 0
            expected_page = 1 if page_domain in [0, "abc", "", None] else page_domain
            assert payload["page"] == expected_page

    @pytest.mark.data_validation
    @pytest.mark.post
    @pytest.mark.parametrize("data_type_domain,test_data,expected_status", [
        # String domain
        ("string", "Normal String", 201),
        ("string", "", 201),
        ("string", "x" * 1000, 201),
        
        # Numeric domain
        ("number", 123, 201),
        ("number", 0, 201),
        ("number", -1, 201),
        ("number", 999999, 201),
        
        # Boolean domain
        ("boolean", True, 201),
        ("boolean", False, 201),
        
        # Null domain
        ("null", None, 201),
        
        # Array domain
        ("array", ["item1", "item2"], 201),
        ("array", [], 201),
        ("array", [1, 2, 3], 201),
        
        # Object domain
        ("object", {"key": "value"}, 201),
        ("object", {}, 201),
        ("object", {"nested": {"key": "value"}}, 201),
    ])
    def test_data_type_domain_validation(self, api_client, users_endpoint, data_type_domain, test_data, expected_status):
        """Test different data type domains for user creation."""
        user_data = {
            "name": "Test User",
            "job": "Engineer",
            "extra_field": test_data  # Extra field with different data types
        }
        
        response = api_client.post(users_endpoint, json=user_data, bulk_mode=True)
        assert response.status_code == expected_status
        
        if response.status_code == 201:
            payload = response.json()
            assert_valid_schema(payload, CREATE_USER_SCHEMA)

    @pytest.mark.data_validation
    @pytest.mark.post
    @pytest.mark.parametrize("test_string,expected_status", [
        # Essential boundary values only
        ("", 201),                    # Empty string
        ("x", 201),                   # Single character
        ("x" * 255, 201),            # Common database field limit
        ("x" * 1024, 201),           # Common buffer size
    ])
    def test_string_length_domain_validation(self, api_client, users_endpoint, test_string, expected_status):
        """Test critical string length boundaries for name field."""
        user_data = {
            "name": test_string,
            "job": "Engineer"
        }
        
        response = api_client.post(users_endpoint, json=user_data, bulk_mode=True)
        assert response.status_code == expected_status
        
        if response.status_code == 201:
            payload = response.json()
            assert_valid_schema(payload, CREATE_USER_SCHEMA)
            assert payload["name"] == test_string

    @pytest.mark.data_validation
    @pytest.mark.post
    @pytest.mark.parametrize("name,job", [
        # Latin characters with accents
        ("José María", "Ingénieur"),
        ("François", "Développeur"),
        ("Müller", "Ingenieur"),
        
        # Asian characters
        ("张三", "软件工程师"),
        ("李四", "数据科学家"),
        ("山田太郎", "エンジニア"),
        ("김철수", "개발자"),
        
        # Arabic characters
        ("أحمد", "مهندس"),
        ("محمد", "مبرمج"),
        
        # Cyrillic characters
        ("Иван", "Инженер"),
        ("Петр", "Разработчик"),
        
        # Emoji and symbols
        ("🚀 Developer", "💻 Engineer"),
        ("Test User", "🎯 Analyst"),
    ])
    def test_unicode_domain_validation(self, api_client, users_endpoint, name, job):
        """Test Unicode domain validation for international character support."""
        user_data = {
            "name": name,
            "job": job
        }
        
        response = api_client.post(users_endpoint, json=user_data, bulk_mode=True)
        assert response.status_code == 201, (
            f"Expected status code 201 for Unicode user creation with name '{name}' and job '{job}', "
            f"but got {response.status_code}. Response: {response.text}"
        )
        
        payload = response.json()
        assert_valid_schema(payload, CREATE_USER_SCHEMA)
        assert payload["name"] == name, (
            f"Expected name '{name}' in response, but got '{payload['name']}'"
        )
        assert payload["job"] == job, (
            f"Expected job '{job}' in response, but got '{payload['job']}'"
        )
=======
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
>>>>>>> fa2d84e (moved schema validation helper to conftest.py)
