"""
Smoke tests for user management API.

This module provides basic smoke tests to verify that the core functionality
of the user management API is working correctly. These tests are designed to
be fast, reliable, and provide quick feedback on API health.

Smoke Testing Approach:
- **Basic Functionality**: Tests core API endpoints are accessible
- **Schema Validation**: Verifies response structure matches expected schemas
- **Data Presence**: Ensures expected data is present in responses
- **Quick Health Check**: Provides fast feedback on API status

Test Categories:
- User listing tests: Tests user list endpoint functionality
- Single user tests: Tests individual user retrieval
- Resource listing tests: Tests resource endpoint functionality

These tests are marked with @pytest.mark.smoke and are typically run first
in any test suite to provide quick feedback on API health.
"""

from __future__ import annotations

import pytest

from tests.conftest import assert_valid_schema
from tests.schemas.json_schemas import LIST_USERS_SCHEMA, RESOURCE_LIST_SCHEMA, SINGLE_USER_SCHEMA


@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.parametrize("page", [1, 2])
def test_list_users_returns_expected_schema(api_client, users_endpoint, page: int) -> None:
    response = api_client.get(users_endpoint, params={"page": page})

    assert response.status_code == 200
    payload = response.json()
    assert_valid_schema(payload, LIST_USERS_SCHEMA)
    assert payload["data"], "Expected at least one user in the list"


@pytest.mark.smoke
@pytest.mark.regression
def test_single_user_response_matches_schema(api_client, users_endpoint) -> None:
    response = api_client.get(f"{users_endpoint}/2")

    assert response.status_code == 200
    payload = response.json()
    assert_valid_schema(payload, SINGLE_USER_SCHEMA)
    user = payload["data"]
    assert user["id"] == 2


@pytest.mark.smoke
@pytest.mark.regression
def test_list_resources_response_matches_schema(api_client, support_endpoint) -> None:
    response = api_client.get(support_endpoint)

    assert response.status_code == 200
    payload = response.json()
    assert_valid_schema(payload, RESOURCE_LIST_SCHEMA)
    assert payload["total"] >= len(payload["data"]) >= 1
