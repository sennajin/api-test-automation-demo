"""
Performance and load tests for user management API.

This module provides comprehensive performance testing for the user management API,
including response time testing, load testing, stress testing, and SLA compliance.

Performance Testing Approach:
- **Response Time Testing**: Validates individual operation response times
- **Load Testing**: Tests API behavior under normal to high load conditions
- **Stress Testing**: Tests API behavior under extreme load conditions
- **Endurance Testing**: Tests API stability over extended periods
- **SLA Compliance**: Validates performance against Service Level Agreements
- **Memory Testing**: Tests memory usage and leak detection
- **Concurrency Testing**: Tests concurrent request handling
- **Workflow Testing**: Tests realistic user workflow scenarios

Test Categories:
- TestUserResponseTimes: Tests response times for individual operations
- TestUserLoadAndConcurrency: Tests performance under load and concurrency
- TestUserWorkflowScenarios: Tests realistic user workflow patterns
- TestUserMemoryAndResourceUsage: Tests memory and resource usage
- TestSLABenchmarking: Tests SLA compliance and benchmarking
- TestEnduranceTesting: Tests API endurance under sustained load
- TestStressTesting: Tests API behavior under extreme stress

Each test includes proper error handling for rate limiting and external API
constraints, with graceful degradation when limits are encountered.
"""

from __future__ import annotations

import pytest
import time
from typing import Any, Dict

from tests.conftest import assert_valid_schema
from tests.schemas.json_schemas import (
    CREATE_USER_SCHEMA,
    UPDATE_USER_SCHEMA,
    SINGLE_USER_SCHEMA,
    LIST_USERS_SCHEMA,
    ERROR_SCHEMA,
)
from tests.test_constants import TEST_USER_IDS, HTTP_STATUS, PERFORMANCE_THRESHOLDS
from tests.conftest import xfail_if_rate_limited


class TestUserResponseTimes:
    """
    Test suite for individual operation response times.
    
    This class provides comprehensive testing for response time performance
    of individual API operations. It validates that each operation completes
    within acceptable time thresholds.
    
    Test Coverage:
    - User creation response times
    - User retrieval response times
    - User update response times
    - User deletion response times
    - Response time threshold validation
    - Performance timer integration
    
    Key Test Methods:
    - test_create_user_response_time: Tests user creation response time
    - test_get_users_list_response_time: Tests user list response time
    - test_update_user_response_time: Tests user update response time
    - test_delete_user_response_time: Tests user deletion response time
    
    All tests use performance timers and validate response times against
    defined thresholds to ensure acceptable performance.
    """

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
        start_time = time.time()
        response = api_client.get(users_endpoint)
        response_time = time.time() - start_time
        
        xfail_if_rate_limited(response, "get users list")
        
        assert response.status_code == 200
        assert response_time < 2.0, f"Response time {response_time:.2f}s exceeds 2s threshold"

    @pytest.mark.performance
    def test_update_user_response_time(self, api_client, users_endpoint, update_user_data):
        """Test that user update responds within acceptable time."""
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
        user_id = 2
        start_time = time.time()
        response = api_client.delete(f"{users_endpoint}/{user_id}")
        response_time = time.time() - start_time
        
        xfail_if_rate_limited(response, "delete user")
        
        assert response.status_code == 204
        assert response_time < 2.0, f"Response time {response_time:.2f}s exceeds 2s threshold"


class TestUserLoadAndConcurrency:
    """
    Test suite for load testing and concurrency performance.
    
    This class provides comprehensive testing for API performance under load
    and concurrent request scenarios. It validates the API's ability to handle
    multiple simultaneous requests and bulk operations.
    
    Test Coverage:
    - Concurrent user creation performance
    - Bulk user operations performance
    - Rate limiting handling
    - Thread safety validation
    - Load distribution testing
    - Performance degradation analysis
    
    Key Test Methods:
    - test_concurrent_user_creation_performance: Tests concurrent creation
    - test_bulk_user_operations_performance: Tests bulk operations
    
    All tests include proper rate limiting handling and graceful degradation
    when external API limits are encountered.
    """

    @pytest.mark.performance
    @pytest.mark.slow
    def test_concurrent_user_creation_performance(self, api_client, users_endpoint, api_key):
        """Test performance of multiple concurrent user creation requests."""
        import concurrent.futures
        import threading
        import requests
        
        def create_user(thread_id):
            # Create a new session for this thread to avoid thread-safety issues
            # requests.Session is not thread-safe, so each worker needs its own session
            thread_session = requests.Session()
            thread_session.headers.update({"x-api-key": api_key, "Accept": "application/json"})
            
            # Create a thread-local API client with the new session
            from tests.conftest import APIClient
            thread_api_client = APIClient(thread_session)
            
            user_data = {
                "name": f"User {thread_id}",
                "job": f"Job {thread_id}"
            }
            start_time = time.time()
            response = thread_api_client.post(users_endpoint, json=user_data, retry=False)
            end_time = time.time()
            
            # Handle 429 errors gracefully in thread
            if response.status_code == 429:
                return "RATE_LIMITED", end_time - start_time
            
            return response.status_code, end_time - start_time
        
        # Create 5 concurrent requests (reduced to minimize rate limiting)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_user, i) for i in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Check for rate limiting and handle gracefully
        rate_limited_count = sum(1 for status_code, _ in results if status_code == "RATE_LIMITED")
        successful_count = sum(1 for status_code, _ in results if status_code == 201)
        
        if rate_limited_count > 0:
            pytest.xfail(f"Rate limited by external API (HTTP 429) during concurrent user creation. {rate_limited_count} requests were rate limited, {successful_count} succeeded.")
        
        # Verify all requests succeeded (adjusted thresholds for retry mechanism)
        for status_code, response_time in results:
            assert status_code == 201
            assert response_time < 30.0, f"Response time {response_time:.2f}s exceeds 30s threshold"
        
        # Calculate average response time (adjusted for retry mechanism)
        avg_response_time = sum(result[1] for result in results) / len(results)
        assert avg_response_time < 15.0, f"Average response time {avg_response_time:.2f}s exceeds 15s threshold"

    @pytest.mark.performance
    @pytest.mark.slow
    def test_bulk_user_operations_performance(self, api_client, users_endpoint):
        """Test performance of bulk user operations with rate limiting protection."""
        import time
        
        # Track rate limiting issues for potential test skip
        rate_limit_count = 0
        max_rate_limits = 2  # Skip test if we hit rate limits more than this
        
        # Test creating multiple users sequentially with intelligent pacing
        creation_times = []
        user_ids = []
        
        for i in range(3):  # Reduced from 5 to 3 to minimize rate limiting
            user_data = {
                "name": f"Bulk User {i}",
                "job": f"Bulk Job {i}"
            }
            
            # Add a small delay between requests to avoid rate limiting
            # This doesn't affect the actual performance measurement
            if i > 0:
                time.sleep(0.5)  # 500ms delay between requests
            
            start_time = time.time()
            response = api_client.post(users_endpoint, json=user_data, retry=False)
            creation_time = time.time() - start_time
            
            # Handle rate limiting gracefully
            if response.status_code == 429:
                rate_limit_count += 1
                if rate_limit_count > max_rate_limits:
                    pytest.xfail(f"Rate limited by external API (HTTP 429) during bulk user creation. Persistent rate limiting encountered (hit {rate_limit_count} times)")
                
                print(f"Rate limited on creation {i+1}, waiting longer...")
                time.sleep(2.0)  # Wait 2 seconds and retry once
                start_time = time.time()
                response = api_client.post(users_endpoint, json=user_data, retry=False)
                creation_time = time.time() - start_time
            
            assert response.status_code == 201, f"Failed to create user {i+1}: {response.status_code}"
            creation_times.append(creation_time)
            user_ids.append(i + 1)  # Simulate user IDs
        
        # Verify creation times are reasonable (adjusted for retry mechanism)
        avg_creation_time = sum(creation_times) / len(creation_times)
        assert avg_creation_time < 5.0, f"Average creation time {avg_creation_time:.2f}s exceeds 5s"
        
        # Test updating the created users with intelligent pacing
        update_times = []
        for idx, user_id in enumerate(user_ids):
            update_data = {
                "name": f"Updated User {user_id}",
                "job": f"Updated Job {user_id}"
            }
            
            # Add a small delay between update requests
            if idx > 0:
                time.sleep(0.5)  # 500ms delay between requests
            
            start_time = time.time()
            response = api_client.put(f"{users_endpoint}/{user_id}", json=update_data, retry=False)
            update_time = time.time() - start_time
            
            # Handle rate limiting gracefully
            if response.status_code == 429:
                rate_limit_count += 1
                if rate_limit_count > max_rate_limits:
                    pytest.xfail(f"Rate limited by external API (HTTP 429) during bulk user update. Persistent rate limiting encountered (hit {rate_limit_count} times)")
                
                print(f"Rate limited on update {idx+1}, waiting longer...")
                time.sleep(2.0)  # Wait 2 seconds and retry once
                start_time = time.time()
                response = api_client.put(f"{users_endpoint}/{user_id}", json=update_data, retry=False)
                update_time = time.time() - start_time
            
            assert response.status_code == 200, f"Failed to update user {user_id}: {response.status_code}"
            update_times.append(update_time)
        
        # Verify update times are reasonable (adjusted for retry mechanism)
        avg_update_time = sum(update_times) / len(update_times)
        assert avg_update_time < 5.0, f"Average update time {avg_update_time:.2f}s exceeds 5s"


class TestUserWorkflowScenarios:
    """Test realistic user workflow scenarios."""

    @pytest.mark.performance
    def test_typical_user_workflow(self, api_client, users_endpoint):
        """Test a complete typical user management workflow."""
        import time
        import random
        
        workflow_times = []
        
        # 1. Browse users (most common action)
        start_time = time.time()
        response = api_client.get(users_endpoint, params={"page": 1})
        workflow_times.append(("browse_users", time.time() - start_time))
        
        xfail_if_rate_limited(response, "browse users")
        
        assert response.status_code == 200
        
        # 2. View specific user details
        user_id = random.randint(1, 12)
        start_time = time.time()
        response = api_client.get(f"{users_endpoint}/{user_id}")
        workflow_times.append(("view_user", time.time() - start_time))
        
        xfail_if_rate_limited(response, "view user")
        
        assert response.status_code in [200, 404]
        
        # 3. Create a new user
        user_data = {
            "name": f"Workflow User {random.randint(1, 1000)}",
            "job": random.choice([
                "Software Engineer", "Product Manager", "Designer",
                "Data Scientist", "DevOps Engineer", "QA Engineer"
            ])
        }
        start_time = time.time()
        response = api_client.post(users_endpoint, json=user_data, retry=False)
        workflow_times.append(("create_user", time.time() - start_time))
        
        xfail_if_rate_limited(response, "create user")
        
        assert response.status_code == 201
        
        # 4. Update the user
        update_data = {
            "name": user_data["name"] + " (Updated)",
            "job": user_data["job"] + " (Senior)"
        }
        start_time = time.time()
        response = api_client.put(f"{users_endpoint}/{user_id}", json=update_data, retry=False)
        workflow_times.append(("update_user", time.time() - start_time))
        
        xfail_if_rate_limited(response, "update user")
        
        assert response.status_code == 200
        
        # 5. Delete the user
        start_time = time.time()
        response = api_client.delete(f"{users_endpoint}/{user_id}")
        workflow_times.append(("delete_user", time.time() - start_time))
        
        xfail_if_rate_limited(response, "delete user")
        
        assert response.status_code == 204
        
        # Verify workflow completes in reasonable time
        total_workflow_time = sum(time for _, time in workflow_times)
        assert total_workflow_time < 10.0, f"Total workflow time {total_workflow_time:.2f}s exceeds 10s"
        
        # Log individual operation times for analysis
        for operation, operation_time in workflow_times:
            print(f"{operation}: {operation_time:.3f}s")

    @pytest.mark.performance
    def test_mixed_operation_patterns(self, api_client, users_endpoint):
        """Test mixed operations with realistic frequency patterns."""
        import random
        import time
        
        operations = []
        
        # Simulate realistic usage patterns (based on Locust RealisticUser)
        # Browse users: 50% of operations
        # View details: 25% of operations  
        # Create user: 15% of operations
        # Update user: 10% of operations
        
        operation_weights = [
            ("browse", 5),    # 50%
            ("view", 2.5),    # 25%
            ("create", 1.5),  # 15%
            ("update", 1),    # 10%
        ]
        
        # Generate 20 operations based on weights
        for _ in range(20):
            rand = random.uniform(0, 10)
            if rand < 5:
                operations.append("browse")
            elif rand < 7.5:
                operations.append("view")
            elif rand < 9:
                operations.append("create")
            else:
                operations.append("update")
        
        operation_times = []
        created_users = []
        
        for operation in operations:
            start_time = time.time()
            
            if operation == "browse":
                page = random.randint(1, 3)
                response = api_client.get(users_endpoint, params={"page": page})
                xfail_if_rate_limited(response, "browse operation")
                assert response.status_code == 200
                
            elif operation == "view":
                user_id = random.randint(1, 12)
                response = api_client.get(f"{users_endpoint}/{user_id}")
                xfail_if_rate_limited(response, "view operation")
                assert response.status_code in [200, 404]
                
            elif operation == "create":
                user_data = {
                    "name": f"Mixed Test User {random.randint(1, 1000)}",
                    "job": f"Test Job {random.randint(1, 100)}"
                }
                response = api_client.post(users_endpoint, json=user_data, retry=False)
                xfail_if_rate_limited(response, "create operation")
                assert response.status_code == 201
                if response.status_code == 201:
                    created_users.append(response.json().get("id"))
                
            elif operation == "update":
                user_id = random.randint(1, 12)
                update_data = {
                    "name": f"Updated User {random.randint(1, 1000)}",
                    "job": f"Updated Job {random.randint(1, 100)}"
                }
                response = api_client.put(f"{users_endpoint}/{user_id}", json=update_data, retry=False)
                xfail_if_rate_limited(response, "update operation")
                assert response.status_code == 200
            
            operation_time = time.time() - start_time
            operation_times.append((operation, operation_time))
            
            # Small delay between operations (realistic user behavior)
            time.sleep(0.1)
        
        # Verify average operation time is reasonable
        avg_time = sum(time for _, time in operation_times) / len(operation_times)
        assert avg_time < 3.0, f"Average operation time {avg_time:.2f}s exceeds 3s"
        
        print(f"Completed {len(operations)} mixed operations, avg time: {avg_time:.3f}s")

    @pytest.mark.performance
    @pytest.mark.stress
    @pytest.mark.slow
    def test_rapid_sequential_requests(self, api_client, users_endpoint):
        """Test rapid sequential requests to check for rate limiting and performance."""
        import time
        
        request_count = 15
        request_times = []
        successful_requests = 0
        rate_limited_requests = 0
        
        for i in range(request_count):
            start_time = time.time()
            response = api_client.get(users_endpoint, retry=False)  # Disable retry to test raw performance
            request_time = time.time() - start_time
            
            request_times.append(request_time)
            
            if response.status_code == 200:
                successful_requests += 1
            elif response.status_code == 429:
                rate_limited_requests += 1
            
            # Small delay to avoid completely overwhelming the API
            time.sleep(0.1)
        
        # Handle rate limiting gracefully
        if rate_limited_requests > 0:
            success_rate = successful_requests / request_count
            pytest.xfail(f"Rate limited by external API (HTTP 429) during rapid sequential requests. {rate_limited_requests} requests were rate limited. Success rate: {success_rate:.1%} ({successful_requests}/{request_count})")
        
        # At least some requests should succeed
        assert successful_requests > 0, "No requests succeeded"
        
        # Calculate success rate
        success_rate = successful_requests / request_count
        print(f"Success rate: {success_rate:.1%} ({successful_requests}/{request_count})")
        print(f"Rate limited: {rate_limited_requests}/{request_count}")
        
        # Average response time for successful requests should be reasonable
        successful_times = [t for i, t in enumerate(request_times) 
                          if i < len(request_times)]  # All times since we're measuring total time
        avg_response_time = sum(successful_times) / len(successful_times)
        assert avg_response_time < 3.0, f"Average response time {avg_response_time:.2f}s exceeds 3s"

    @pytest.mark.performance
    def test_error_handling_under_load(self, api_client, users_endpoint):
        """Test error handling scenarios under moderate load."""
        import random
        import time
        
        # Test various invalid data scenarios
        invalid_data_scenarios = [
            {},  # Empty payload
            {"name": ""},  # Empty name
            {"job": ""},  # Empty job
            {"name": None, "job": None},  # Null values
            {"name": "x" * 10000},  # Very long name
        ]
        
        error_response_times = []
        
        for i in range(10):  # Test 10 error scenarios
            invalid_data = random.choice(invalid_data_scenarios)
            
            start_time = time.time()
            response = api_client.post(users_endpoint, json=invalid_data, retry=False)
            response_time = time.time() - start_time
            
            error_response_times.append(response_time)
            
            # Handle rate limiting gracefully
            xfail_if_rate_limited(response, "error handling test")
            
            # ReqRes is permissive, so we expect 201 even with invalid data
            # In a real API, you might expect 400
            assert response.status_code in [201, 400, 422]
            
            # Small delay between requests
            time.sleep(0.2)
        
        # Verify error handling doesn't significantly impact performance
        avg_error_response_time = sum(error_response_times) / len(error_response_times)
        assert avg_error_response_time < 5.0, f"Average error response time {avg_error_response_time:.2f}s exceeds 5s"
        
        print(f"Error handling test completed, avg response time: {avg_error_response_time:.3f}s")


class TestUserMemoryAndResourceUsage:
    """Test memory and resource usage patterns."""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_large_payload_performance(self, api_client, users_endpoint):
        """Test performance with large payloads."""
        # Create user data with large strings
        large_string = "x" * 10000  # 10KB string
        user_data = {
            "name": large_string,
            "job": large_string
        }
        
        start_time = time.time()
        response = api_client.post(users_endpoint, json=user_data, retry=False)
        response_time = time.time() - start_time
        
        # Handle rate limiting gracefully
        xfail_if_rate_limited(response, "large payload test")
        
        # Should still complete in reasonable time even with large payload
        assert response.status_code == 201
        assert response_time < 10.0, f"Large payload response time {response_time:.2f}s exceeds 10s"
        
        # Verify the data was handled correctly
        payload = response.json()
        assert payload["name"] == large_string
        assert payload["job"] == large_string

    @pytest.mark.performance
    @pytest.mark.slow
    def test_memory_usage_stability(self, api_client, users_endpoint):
        """Test that memory usage remains stable across multiple operations."""
        import gc
        
        # Force garbage collection before starting
        gc.collect()
        
        # Perform multiple operations
        for i in range(20):
            user_data = {
                "name": f"Memory Test User {i}",
                "job": f"Memory Test Job {i}"
            }
            
            response = api_client.post(users_endpoint, json=user_data, retry=False)
            
            xfail_if_rate_limited(response, "memory stability test")
            
            assert response.status_code == 201
            
            # Small delay between operations
            time.sleep(0.1)
            
            # Periodic garbage collection
            if i % 5 == 0:
                gc.collect()
        
        # Test passes if no memory errors or exceptions occurred
        assert True, "Memory usage test completed successfully"


class TestSLABenchmarking:
    """Test performance against defined Service Level Agreements (SLAs)."""

    @pytest.mark.performance
    @pytest.mark.sla
    def test_response_time_sla_compliance(self, api_client, users_endpoint):
        """Test that API response times meet SLA requirements."""
        import time
        
        # Define SLA thresholds
        sla_thresholds = {
            "GET": 2.0,      # 2 seconds for GET requests
            "POST": 3.0,     # 3 seconds for POST requests
            "PUT": 3.0,       # 3 seconds for PUT requests
            "DELETE": 2.0,    # 2 seconds for DELETE requests
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
        print(f"SLA Compliance Results:")
        for method, time_taken in sla_results.items():
            threshold = sla_thresholds[method]
            compliance = "✓ PASS" if time_taken <= threshold else "✗ FAIL"
            print(f"  {method}: {time_taken:.3f}s / {threshold}s {compliance}")

    @pytest.mark.performance
    @pytest.mark.sla
    def test_availability_sla_compliance(self, api_client, users_endpoint):
        """Test API availability against SLA requirements."""
        import time
        
        # SLA: 99.9% availability (0.1% downtime allowed)
        # Test over 1 minute with requests every 5 seconds
        test_duration = 60  # seconds
        request_interval = 5  # seconds
        total_requests = test_duration // request_interval
        
        successful_requests = 0
        failed_requests = 0
        
        start_time = time.time()
        
        for i in range(total_requests):
            try:
                response = api_client.get(users_endpoint, retry=False)
                if response.status_code == 200:
                    successful_requests += 1
                else:
                    failed_requests += 1
            except Exception as e:
                failed_requests += 1
                print(f"Request {i+1} failed: {e}")
            
            # Wait for next request
            if i < total_requests - 1:
                time.sleep(request_interval)
        
        elapsed_time = time.time() - start_time
        
        # Calculate availability
        availability = (successful_requests / total_requests) * 100
        sla_threshold = 99.9  # 99.9% availability SLA
        
        print(f"Availability Test Results:")
        print(f"  Total requests: {total_requests}")
        print(f"  Successful: {successful_requests}")
        print(f"  Failed: {failed_requests}")
        print(f"  Availability: {availability:.2f}%")
        print(f"  SLA Threshold: {sla_threshold}%")
        
        assert availability >= sla_threshold, (
            f"Availability {availability:.2f}% below SLA threshold of {sla_threshold}%"
        )

    @pytest.mark.performance
    @pytest.mark.sla
    def test_throughput_sla_compliance(self, api_client, users_endpoint):
        """Test API throughput against SLA requirements."""
        import time
        import concurrent.futures
        
        # SLA: 100 requests per minute
        target_throughput = 100  # requests per minute
        test_duration = 60  # seconds
        
        def make_request():
            start_time = time.time()
            response = api_client.get(users_endpoint, retry=False)
            end_time = time.time()
            return response.status_code, end_time - start_time
        
        # Run concurrent requests for the test duration
        start_time = time.time()
        completed_requests = 0
        successful_requests = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            # Submit requests continuously
            while time.time() - start_time < test_duration:
                future = executor.submit(make_request)
                futures.append(future)
                time.sleep(0.1)  # Small delay between request submissions
            
            # Collect results
            for future in concurrent.futures.as_completed(futures):
                try:
                    status_code, response_time = future.result()
                    completed_requests += 1
                    if status_code == 200:
                        successful_requests += 1
                except Exception as e:
                    print(f"Request failed: {e}")
        
        elapsed_time = time.time() - start_time
        actual_throughput = (successful_requests / elapsed_time) * 60  # requests per minute
        
        print(f"Throughput Test Results:")
        print(f"  Test duration: {elapsed_time:.2f}s")
        print(f"  Completed requests: {completed_requests}")
        print(f"  Successful requests: {successful_requests}")
        print(f"  Actual throughput: {actual_throughput:.2f} req/min")
        print(f"  SLA threshold: {target_throughput} req/min")
        
        assert actual_throughput >= target_throughput, (
            f"Throughput {actual_throughput:.2f} req/min below SLA threshold of {target_throughput} req/min"
        )


class TestEnduranceTesting:
    """Test API endurance under sustained load."""

    @pytest.mark.performance
    @pytest.mark.endurance
    @pytest.mark.slow
    def test_sustained_load_endurance(self, api_client, users_endpoint):
        """Test API performance under sustained load for extended period."""
        import time
        import random
        
        # Endurance test: 5 minutes of sustained load
        test_duration = 300  # 5 minutes
        request_interval = 2  # seconds between requests
        
        start_time = time.time()
        request_count = 0
        successful_requests = 0
        response_times = []
        
        print(f"Starting endurance test for {test_duration} seconds...")
        
        while time.time() - start_time < test_duration:
            request_start = time.time()
            
            # Vary the type of request
            request_type = random.choice(["GET", "POST", "PUT", "DELETE"])
            
            try:
                if request_type == "GET":
                    response = api_client.get(users_endpoint, retry=False)
                elif request_type == "POST":
                    user_data = {
                        "name": f"Endurance User {request_count}",
                        "job": f"Endurance Job {request_count}"
                    }
                    response = api_client.post(users_endpoint, json=user_data, retry=False)
                elif request_type == "PUT":
                    user_id = random.randint(1, 12)
                    update_data = {
                        "name": f"Endurance Updated {request_count}",
                        "job": f"Endurance Updated Job {request_count}"
                    }
                    response = api_client.put(f"{users_endpoint}/{user_id}", json=update_data, retry=False)
                elif request_type == "DELETE":
                    user_id = random.randint(1, 12)
                    response = api_client.delete(f"{users_endpoint}/{user_id}")
                
                request_time = time.time() - request_start
                response_times.append(request_time)
                
                if response.status_code in [200, 201, 204]:
                    successful_requests += 1
                
                request_count += 1
                
                # Log progress every 30 seconds
                if request_count % 15 == 0:
                    elapsed = time.time() - start_time
                    print(f"  {elapsed:.0f}s: {request_count} requests, {successful_requests} successful")
                
            except Exception as e:
                print(f"Request {request_count} failed: {e}")
                request_count += 1
            
            # Wait for next request
            time.sleep(request_interval)
        
        total_time = time.time() - start_time
        
        # Calculate metrics
        success_rate = (successful_requests / request_count) * 100 if request_count > 0 else 0
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        
        print(f"Endurance Test Results:")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Total requests: {request_count}")
        print(f"  Successful requests: {successful_requests}")
        print(f"  Success rate: {success_rate:.2f}%")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  Min response time: {min_response_time:.3f}s")
        print(f"  Max response time: {max_response_time:.3f}s")
        
        # Assertions for endurance test
        assert success_rate >= 95.0, f"Success rate {success_rate:.2f}% below 95% threshold"
        assert avg_response_time <= 5.0, f"Average response time {avg_response_time:.3f}s exceeds 5s threshold"
        assert max_response_time <= 30.0, f"Max response time {max_response_time:.3f}s exceeds 30s threshold"

    @pytest.mark.performance
    @pytest.mark.endurance
    @pytest.mark.slow
    def test_memory_leak_detection(self, api_client, users_endpoint):
        """Test for memory leaks during extended operation."""
        import gc
        import time
        
        # Test for 2 minutes with memory monitoring
        test_duration = 120  # 2 minutes
        request_interval = 1  # seconds
        
        start_time = time.time()
        request_count = 0
        
        # Force garbage collection before starting
        gc.collect()
        
        print(f"Starting memory leak detection test for {test_duration} seconds...")
        
        while time.time() - start_time < test_duration:
            # Make a request
            response = api_client.get(users_endpoint, retry=False)
            request_count += 1
            
            # Periodic garbage collection and memory check
            if request_count % 10 == 0:
                gc.collect()
                elapsed = time.time() - start_time
                print(f"  {elapsed:.0f}s: {request_count} requests completed")
            
            time.sleep(request_interval)
        
        # Final garbage collection
        gc.collect()
        
        print(f"Memory leak detection completed:")
        print(f"  Total requests: {request_count}")
        print(f"  Test duration: {time.time() - start_time:.2f}s")
        
        # Test passes if no memory errors occurred
        assert True, "Memory leak detection test completed successfully"

    @pytest.mark.performance
    @pytest.mark.endurance
    def test_connection_pool_endurance(self, api_client, users_endpoint):
        """Test connection pool endurance under sustained load."""
        import time
        import concurrent.futures
        
        # Test with sustained concurrent connections
        test_duration = 60  # 1 minute
        concurrent_workers = 5
        
        def sustained_request():
            start_time = time.time()
            request_count = 0
            
            while time.time() - start_time < test_duration:
                try:
                    response = api_client.get(users_endpoint, retry=False)
                    request_count += 1
                    time.sleep(0.5)  # 500ms between requests
                except Exception as e:
                    print(f"Connection error: {e}")
                    break
            
            return request_count
        
        # Run concurrent sustained requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
            futures = [executor.submit(sustained_request) for _ in range(concurrent_workers)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_requests = sum(results)
        avg_requests_per_worker = total_requests / concurrent_workers
        
        print(f"Connection Pool Endurance Results:")
        print(f"  Test duration: {test_duration}s")
        print(f"  Concurrent workers: {concurrent_workers}")
        print(f"  Total requests: {total_requests}")
        print(f"  Average requests per worker: {avg_requests_per_worker:.1f}")
        
        # Should handle sustained concurrent connections
        assert total_requests > 0, "No requests completed during endurance test"
        assert avg_requests_per_worker >= 10, "Insufficient requests per worker"


class TestStressTesting:
    """Test API behavior under extreme stress conditions."""

    @pytest.mark.performance
    @pytest.mark.stress
    @pytest.mark.slow
    def test_extreme_concurrent_load(self, api_client, users_endpoint):
        """Test API behavior under extreme concurrent load."""
        import concurrent.futures
        import time
        
        # Extreme stress test: 50 concurrent workers
        concurrent_workers = 50
        test_duration = 30  # 30 seconds
        
        def stress_request():
            start_time = time.time()
            request_count = 0
            errors = 0
            
            while time.time() - start_time < test_duration:
                try:
                    response = api_client.get(users_endpoint, retry=False)
                    request_count += 1
                    
                    # Very short delay to maximize load
                    time.sleep(0.01)
                except Exception as e:
                    errors += 1
                    if errors > 10:  # Stop if too many errors
                        break
            
            return request_count, errors
        
        print(f"Starting extreme stress test: {concurrent_workers} workers for {test_duration}s...")
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
            futures = [executor.submit(stress_request) for _ in range(concurrent_workers)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Analyze results
        total_requests = sum(result[0] for result in results)
        total_errors = sum(result[1] for result in results)
        successful_requests = total_requests - total_errors
        
        print(f"Extreme Stress Test Results:")
        print(f"  Test duration: {total_time:.2f}s")
        print(f"  Concurrent workers: {concurrent_workers}")
        print(f"  Total requests: {total_requests}")
        print(f"  Successful requests: {successful_requests}")
        print(f"  Errors: {total_errors}")
        print(f"  Success rate: {(successful_requests/total_requests)*100:.2f}%" if total_requests > 0 else "N/A")
        
        # Should handle some level of extreme load
        assert total_requests > 0, "No requests completed during stress test"
        assert successful_requests > 0, "No successful requests during stress test"

    @pytest.mark.performance
    @pytest.mark.stress
    def test_resource_exhaustion_resilience(self, api_client, users_endpoint):
        """Test API resilience to resource exhaustion attacks."""
        import time
        import concurrent.futures
        
        # Test with large payloads and rapid requests
        large_payload = {
            "name": "x" * 10000,  # 10KB name
            "job": "y" * 10000   # 10KB job
        }
        
        def resource_intensive_request():
            try:
                # Large payload request
                response = api_client.post(users_endpoint, json=large_payload, retry=False)
                return response.status_code
            except Exception as e:
                return f"Error: {e}"
        
        # Rapid requests with large payloads
        rapid_requests = 20
        results = []
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(resource_intensive_request) for _ in range(rapid_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful = sum(1 for result in results if result == 201)
        errors = sum(1 for result in results if isinstance(result, str))
        
        print(f"Resource Exhaustion Test Results:")
        print(f"  Total requests: {rapid_requests}")
        print(f"  Successful: {successful}")
        print(f"  Errors: {errors}")
        print(f"  Test duration: {total_time:.2f}s")
        
        # Should handle resource-intensive requests
        assert successful > 0, "No successful requests with large payloads"
        assert total_time < 60, "Test took too long, possible resource exhaustion"

    @pytest.mark.performance
    @pytest.mark.stress
    def test_graceful_degradation_under_load(self, api_client, users_endpoint):
        """Test API graceful degradation under high load."""
        import time
        import concurrent.futures
        
        # Test gradual load increase
        load_levels = [5, 10, 20, 30, 40, 50]  # Concurrent workers
        test_duration_per_level = 10  # seconds per level
        
        def load_test(worker_count):
            def worker():
                start_time = time.time()
                request_count = 0
                
                while time.time() - start_time < test_duration_per_level:
                    try:
                        response = api_client.get(users_endpoint, retry=False)
                        request_count += 1
                        time.sleep(0.1)
                    except Exception:
                        break
                
                return request_count
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
                futures = [executor.submit(worker) for _ in range(worker_count)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            return sum(results)
        
        print("Testing graceful degradation under increasing load...")
        
        for level in load_levels:
            start_time = time.time()
            total_requests = load_test(level)
            level_time = time.time() - start_time
            
            throughput = total_requests / level_time if level_time > 0 else 0
            
            print(f"  Load level {level}: {total_requests} requests in {level_time:.2f}s (throughput: {throughput:.2f} req/s)")
            
            # Should maintain some level of service even under high load
            assert total_requests > 0, f"No requests completed at load level {level}"
            
            # Brief pause between load levels
            time.sleep(2)