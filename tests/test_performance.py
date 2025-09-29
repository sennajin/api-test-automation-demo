"""
Basic performance tests for user management API.

This module provides essential performance testing for the user management API,
including response time testing, basic load testing, and SLA compliance.

Performance Testing Approach:
- **Basic Response Time Testing**: Validates individual operation response times
- **Basic Load Testing**: Tests API behavior under normal load conditions
- **Basic SLA Compliance**: Validates performance against basic Service Level Agreements

Test Categories:
- TestBasicResponseTimes: Tests response times for individual operations
- TestBasicLoadTesting: Tests performance under basic load conditions
- TestBasicSLACompliance: Tests basic SLA compliance

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


class TestBasicResponseTimes:
    """
    Test suite for basic individual operation response times.
    
    This class provides essential testing for response time performance
    of individual API operations. It validates that each operation completes
    within acceptable time thresholds.
    
    Test Coverage:
    - User creation response times
    - User retrieval response times
    - User update response times
    - User deletion response times
    - Basic response time threshold validation
    
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


class TestBasicLoadTesting:
    """
    Test suite for basic load testing and concurrency performance.
    
    This class provides essential testing for API performance under load
    and concurrent request scenarios. It validates the API's ability to handle
    multiple simultaneous requests and basic bulk operations.
    
    Test Coverage:
    - Concurrent user creation performance
    - Basic bulk user operations performance
    - Rate limiting handling
    - Basic performance degradation analysis
    
    Key Test Methods:
    - test_basic_concurrent_requests: Tests concurrent request handling
    - test_basic_bulk_operations: Tests basic bulk operations
    
    All tests include proper rate limiting handling and graceful degradation
    when external API limits are encountered.
    """

    @pytest.mark.performance
    @pytest.mark.slow
    def test_basic_concurrent_requests(self, api_client, users_endpoint, api_key):
        """Test performance of basic concurrent requests."""
        import concurrent.futures
        import threading
        import requests
        
        def make_request(thread_id):
            # Create a new session for this thread to avoid thread-safety issues
            thread_session = requests.Session()
            thread_session.headers.update({"x-api-key": api_key, "Accept": "application/json"})
            
            # Create a thread-local API client with the new session
            from tests.conftest import APIClient
            thread_api_client = APIClient(thread_session)
            
            start_time = time.time()
            response = thread_api_client.get(users_endpoint, retry=False)
            end_time = time.time()
            
            # Handle 429 errors gracefully in thread
            if response.status_code == 429:
                return "RATE_LIMITED", end_time - start_time
            
            return response.status_code, end_time - start_time
        
        # Create 3 concurrent requests (reduced to minimize rate limiting)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, i) for i in range(3)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Check for rate limiting and handle gracefully
        rate_limited_count = sum(1 for status_code, _ in results if status_code == "RATE_LIMITED")
        successful_count = sum(1 for status_code, _ in results if status_code == 200)
        
        if rate_limited_count > 0:
            pytest.xfail(f"Rate limited by external API (HTTP 429) during concurrent requests. {rate_limited_count} requests were rate limited, {successful_count} succeeded.")
        
        # Verify all requests succeeded
        for status_code, response_time in results:
            assert status_code == 200
            assert response_time < 5.0, f"Response time {response_time:.2f}s exceeds 5s threshold"

    @pytest.mark.performance
    @pytest.mark.slow
    def test_basic_bulk_operations(self, api_client, users_endpoint):
        """Test performance of basic bulk user operations."""
        import time
        
        # Track rate limiting issues for potential test skip
        rate_limit_count = 0
        max_rate_limits = 2  # Skip test if we hit rate limits more than this
        
        # Test creating multiple users sequentially with intelligent pacing
        creation_times = []
        
        for i in range(3):  # Reduced to 3 to minimize rate limiting
            user_data = {
                "name": f"Bulk User {i}",
                "job": f"Bulk Job {i}"
            }
            
            # Add a small delay between requests to avoid rate limiting
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
        
        # Verify creation times are reasonable
        avg_creation_time = sum(creation_times) / len(creation_times)
        assert avg_creation_time < 5.0, f"Average creation time {avg_creation_time:.2f}s exceeds 5s"
        

class TestBasicSLACompliance:
    """
    Test suite for basic SLA compliance and performance benchmarking.
    
    This class provides essential testing for performance against basic
    Service Level Agreements (SLAs). It validates that the API meets
    fundamental performance requirements.
    
    Test Coverage:
    - Response time SLA compliance
    - Basic availability testing
    - Basic throughput testing
    
    Key Test Methods:
    - test_basic_response_time_sla: Tests basic response time SLA compliance
    - test_basic_availability: Tests basic API availability
    - test_basic_throughput: Tests basic throughput requirements
    
    All tests validate that the API meets basic SLA requirements.
    """

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

    @pytest.mark.performance
    @pytest.mark.sla
    def test_basic_availability(self, api_client, users_endpoint):
        """Test basic API availability."""
        import time
        
        # Basic availability test: 30 seconds with requests every 5 seconds
        test_duration = 30  # seconds
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
        sla_threshold = 95.0  # 95% availability SLA (basic requirement)
        
        print(f"Basic Availability Test Results:")
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
    def test_basic_throughput(self, api_client, users_endpoint):
        """Test basic API throughput requirements."""
        import time
        
        # Basic throughput test: 10 requests over 30 seconds
        target_requests = 10
        test_duration = 30  # seconds
        
        successful_requests = 0
        start_time = time.time()
        
        for i in range(target_requests):
            try:
                    response = api_client.get(users_endpoint, retry=False)
                if response.status_code == 200:
                    successful_requests += 1
                
                # Wait between requests to avoid rate limiting
                time.sleep(2.0)  # 2 second delay between requests
                
            except Exception as e:
                print(f"Request {i+1} failed: {e}")
        
        elapsed_time = time.time() - start_time
        actual_throughput = (successful_requests / elapsed_time) * 60  # requests per minute
        
        print(f"Basic Throughput Test Results:")
        print(f"  Target requests: {target_requests}")
        print(f"  Successful requests: {successful_requests}")
        print(f"  Test duration: {elapsed_time:.2f}s")
        print(f"  Actual throughput: {actual_throughput:.2f} req/min")
        
        # Basic throughput requirement: at least 10 requests per minute
        assert actual_throughput >= 10.0, (
            f"Throughput {actual_throughput:.2f} req/min below basic threshold of 10 req/min"
        )