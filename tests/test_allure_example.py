"""
Example test demonstrating Allure reporting integration.

This test shows how to use Allure features like:
- Step-by-step execution tracking
- Request/response attachments
- Test categorization and labeling
- Performance metrics
"""

import allure
import pytest
import requests
from tests.conftest import allure_attach_response, allure_attach_request


@allure.epic("API Testing")
@allure.feature("User Management")
@allure.story("User Retrieval")
class TestAllureExample:
    """Example test class demonstrating Allure reporting features."""

    @allure.title("Get user by ID - Success Case")
    @allure.description("Test retrieving a specific user by ID with valid data")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("api", "get", "users")
    def test_get_user_by_id_success(self, api_client, users_endpoint, allure_attach_request, allure_attach_response):
        """Test successful user retrieval with Allure reporting."""
        
        user_id = 2
        url = f"{users_endpoint}/{user_id}"
        
        with allure.step(f"Making GET request to {url}"):
            # Attach request details
            allure_attach_request("GET", url)
            
            # Make the request
            response = api_client.get(url)
            
            # Attach response details
            allure_attach_response(response, "User retrieval response")
        
        with allure.step("Validating response"):
            assert response.status_code == 200
            
            data = response.json()
            assert "data" in data
            assert data["data"]["id"] == user_id
            
            # Attach validation results
            allure.attach(
                name="Validation Results",
                body=f"Status: {response.status_code}\nUser ID: {data['data']['id']}\nEmail: {data['data'].get('email', 'N/A')}",
                attachment_type=allure.attachment_type.TEXT
            )

    @allure.title("Get user by ID - Not Found Case")
    @allure.description("Test retrieving a non-existent user by ID")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("api", "get", "users", "negative")
    def test_get_user_by_id_not_found(self, api_client, users_endpoint, allure_attach_request, allure_attach_response):
        """Test user retrieval with non-existent ID."""
        
        user_id = 999  # Non-existent user
        url = f"{users_endpoint}/{user_id}"
        
        with allure.step(f"Making GET request to non-existent user {user_id}"):
            allure_attach_request("GET", url)
            response = api_client.get(url)
            allure_attach_response(response, "Not found response")
        
        with allure.step("Validating 404 response"):
            assert response.status_code == 404

    @allure.title("Create new user - Success Case")
    @allure.description("Test creating a new user with valid data")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("api", "post", "users")
    def test_create_user_success(self, api_client, users_endpoint, valid_user_data, allure_attach_request, allure_attach_response):
        """Test successful user creation with Allure reporting."""
        
        with allure.step("Preparing user data"):
            allure.attach(
                name="User Data",
                body=str(valid_user_data),
                attachment_type=allure.attachment_type.JSON
            )
        
        with allure.step(f"Making POST request to {users_endpoint}"):
            allure_attach_request("POST", users_endpoint, json=valid_user_data)
            response = api_client.post(users_endpoint, json=valid_user_data)
            allure_attach_response(response, "User creation response")
        
        with allure.step("Validating creation response"):
            assert response.status_code == 201
            
            data = response.json()
            assert "id" in data
            assert data["name"] == valid_user_data["name"]
            assert data["job"] == valid_user_data["job"]
            
            # Attach created user details
            allure.attach(
                name="Created User",
                body=f"ID: {data['id']}\nName: {data['name']}\nJob: {data['job']}\nCreated: {data.get('createdAt', 'N/A')}",
                attachment_type=allure.attachment_type.TEXT
            )

    @allure.title("Performance Test - Response Time")
    @allure.description("Test API response time meets performance requirements")
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("api", "performance", "users")
    def test_user_list_performance(self, api_client, users_endpoint, performance_timer, allure_attach_response):
        """Test user list endpoint performance with timing metrics."""
        
        with allure.step("Measuring response time"):
            timer = performance_timer.start()
            response = api_client.get(users_endpoint)
            timer.stop()
            
            allure_attach_response(response, "Performance test response")
        
        with allure.step("Validating performance metrics"):
            # Attach performance data
            allure.attach(
                name="Performance Metrics",
                body=f"Response Time: {timer.elapsed:.3f}s\nStatus Code: {response.status_code}",
                attachment_type=allure.attachment_type.TEXT
            )
            
            # Assert performance requirements
            timer.assert_within("RESPONSE_TIME_FAST")
            assert response.status_code == 200

    @allure.title("Bulk User Operations")
    @allure.description("Test multiple user operations in sequence")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("api", "bulk", "users")
    def test_bulk_user_operations(self, api_client, users_endpoint, all_valid_users, allure_attach_response):
        """Test multiple user operations with comprehensive reporting."""
        
        created_users = []
        
        with allure.step("Creating multiple users"):
            for i, user_data in enumerate(all_valid_users[:3]):  # Limit to 3 for demo
                with allure.step(f"Creating user {i+1}: {user_data['name']}"):
                    response = api_client.post(users_endpoint, json=user_data)
                    allure_attach_response(response, f"User {i+1} creation")
                    
                    assert response.status_code == 201
                    created_users.append(response.json())
        
        with allure.step("Retrieving all users"):
            response = api_client.get(users_endpoint)
            allure_attach_response(response, "User list response")
            
            assert response.status_code == 200
            data = response.json()
            
            # Attach summary
            allure.attach(
                name="Bulk Operations Summary",
                body=f"Created: {len(created_users)} users\nTotal in system: {data.get('total', 'Unknown')}",
                attachment_type=allure.attachment_type.TEXT
            )
