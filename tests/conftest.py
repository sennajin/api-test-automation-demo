"""Test configuration and fixtures for the API automation test suite.

This module provides comprehensive test configuration, fixtures, and utility functions
for the pytest API automation framework. It includes setup for Allure reporting,
API client configuration, data fixtures, and validation utilities.

Key Components:
- **Pytest Configuration**: Command-line options and Allure reporting setup
- **API Client Fixtures**: Configured API client with retry logic and error handling
- **Data Fixtures**: Test data for various scenarios (valid, invalid, edge cases)
- **Validation Utilities**: Schema validation and response verification helpers
- **Performance Utilities**: Timing and performance measurement tools
- **Allure Integration**: Test reporting and attachment management

Fixtures:
- base_url: Base URL for the API under test
- api_key: API key for authentication
- api_client: Configured API client with retry logic
- users_endpoint: Users API endpoint URL
- login_endpoint: Login API endpoint URL
- support_endpoint: Support/Resources API endpoint URL
- valid_user_data: Valid user data for testing
- update_user_data: User data for update operations
- invalid_credentials: Invalid credentials for negative testing
- valid_credentials: Valid credentials for authentication testing
- response_validator: Response validation helper
- performance_timer: Performance measurement utility

Utilities:
- assert_valid_schema: Validates response against JSON schema
- verify_user_creation_response: Comprehensive user creation response validation
- xfail_if_rate_limited: Handles rate limiting gracefully in tests
- APIClient: Custom API client with retry logic and error handling
- PerformanceTimer: Performance measurement and threshold validation
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import Any, cast

import allure
import pytest
import requests
from jsonschema import ValidationError, validate

from tests.test_constants import BULK_RETRY_CONFIG, RETRY_CONFIG, TIMEOUTS


class SchemaValidationError(AssertionError):
    """Wrap jsonschema's ValidationError so pytest shows assertion context."""


def assert_valid_schema(payload: Any, schema: Mapping[str, Any]) -> None:
    """Assert that ``payload`` satisfies the provided JSON schema."""
    try:
        validate(instance=payload, schema=schema)
    except ValidationError as exc:
        raise SchemaValidationError(str(exc)) from exc


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command-line options for pytest.

    The function defines additional command-line options that can be added to pytest
    to configure settings for API testing. These options allow customization for the
    API key and base URL, which are used during test execution.

    Parameters:
        parser (pytest.Parser): The parser used by pytest to add and manage
                                custom command-line options.
    """
    parser.addoption("--api-key", action="store", default=None, help="ReqRes API key")
    parser.addoption(
        "--base-url",
        action="store",
        default=os.getenv("BASE_URL", "https://reqres.in"),
        help="Base URL for the API under test",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Configure Allure reporting with environment information."""
    # Set Allure environment properties
    allure.dynamic.label("framework", "pytest")
    allure.dynamic.label("language", "python")
    allure.dynamic.label("test_type", "api_automation")

    # Add environment information
    base_url = config.getoption("--base-url")
    api_key = config.getoption("--api-key") or os.getenv("REQRES_API_KEY") or "reqres-free-v1"

    allure.dynamic.label("environment", "test")
    allure.dynamic.label("base_url", base_url)
    allure.dynamic.label("api_key", api_key[:10] + "..." if len(api_key) > 10 else api_key)


@pytest.fixture(scope="session")
def base_url(pytestconfig: pytest.Config) -> str:
    """Base URL fixture for the API under test.

    Returns the base URL configured via command line option or environment variable.
    Defaults to 'https://reqres.in' if not specified.

    Usage:
        Used by other fixtures to construct endpoint URLs.
        Can be overridden via --base-url command line option.
    """
    return pytestconfig.getoption("--base-url")


@pytest.fixture(scope="session")
def api_key(pytestconfig: pytest.Config) -> str:
    """API key fixture for authentication.

    Returns the API key in order of preference:
    1. Command line option --api-key
    2. Environment variable REQRES_API_KEY
    3. Default value "reqres-free-v1"

    Usage:
        Used by the API client for authentication headers.
        Can be overridden via --api-key command line option.
    """
    # prefer CLI, else env, else default free key
    return pytestconfig.getoption("--api-key") or os.getenv("REQRES_API_KEY") or "reqres-free-v1"


class APIClient:
    """Lightweight wrapper over requests.Session with convenience helpers.

    Features:
    - Automatic retry with exponential backoff for rate limiting (429) and server errors (5xx)
    - Configurable retry behavior (can be disabled per request)
    - Jitter to prevent thundering herd problems
    - Comprehensive logging of retry attempts

    Rate Limiting Solution:
    Instead of accepting 429 responses as valid test outcomes, this client automatically
    retries rate-limited requests with exponential backoff. This ensures tests focus on
    actual business logic rather than infrastructure limitations.

    Usage:
    - Default behavior: All requests retry automatically on 429/5xx errors
    - Disable retries: Pass retry=False to any HTTP method
    - Rate limiting tests: Use api_client_no_retry fixture or retry=False parameter
    """

    def __init__(self, session: requests.Session) -> None:
        """Represents a class that is initialized with a requests session.

        Manages a given session and can be used to perform HTTP operations or other
        session-related functionalities. This class encapsulates the session instance
        to facilitate interactions with external services or APIs securely and efficiently.

        Args:
            session: An instance of `requests.Session` to be used for making HTTP requests.
        """
        self._session = session

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        headers: MutableMapping[str, str] | None = None,
        timeout: float | None = None,
        retry: bool = True,
        bulk_mode: bool = False,
    ) -> requests.Response:
        """Send an HTTP request with optional retries and exponential backoff.

        This is a thin wrapper around requests.Session.request that adds:
        - Default timeout if none is provided
        - Configurable retry logic (enabled by default)
        - Exponential backoff with jitter for 429 and selected 5xx responses
        - A more aggressive backoff profile for bulk operations

        Args:
            method: HTTP method to use (e.g., "GET", "POST").
            url: Fully-qualified request URL.
            params: Optional query parameters to append to the URL.
            json: Optional JSON-serializable body to send as application/json.
            data: Optional request body for form-encoded or raw data.
            headers: Optional mapping of HTTP headers to include with the request.
            timeout: Request timeout in seconds. If None, uses TIMEOUTS["DEFAULT"].
            retry: Whether to apply retry/backoff behavior on retryable failures.
            bulk_mode: If True, use BULK_RETRY_CONFIG; otherwise use RETRY_CONFIG.

        Returns:
            requests.Response: The final response from the server. If a retryable
            status code is encountered and max retries are exhausted, the last
            response is returned. When retries are exhausted without success, the
            response will include header 'X-Retry-Exhausted: 1' to allow callers to
            distinguish this case.

        Raises:
            requests.exceptions.RequestException: If a network/connection error occurs
                and retries are exhausted.
            RuntimeError: If the retry loop exits unexpectedly (should not occur).

        Notes:
            Retryable status codes are defined in RETRY_CONFIG["RETRY_STATUS_CODES"].
            Backoff is exponential with a cap (MAX_BACKOFF) and small jitter to reduce
            synchronization (thundering herd) issues.
        """
        # Use default timeout if none provided
        if timeout is None:
            timeout = TIMEOUTS["DEFAULT"]

        # Implement retry logic for rate limiting and server errors
        import random
        import time

        # Use bulk retry config for bulk operations, regular config otherwise
        config = BULK_RETRY_CONFIG if bulk_mode else RETRY_CONFIG

        max_retries = config["MAX_RETRIES"] if retry else 0
        backoff_factor = config["BACKOFF_FACTOR"]
        retry_status_codes = config["RETRY_STATUS_CODES"]
        max_backoff = config["MAX_BACKOFF"]

        for attempt in range(max_retries + 1):
            try:
                response = self._session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    data=data,
                    headers=headers,
                    timeout=timeout,
                )

                # If successful or non-retryable error, return response
                if response.status_code not in retry_status_codes:
                    return response

                # If this is the last attempt, return the response (don't retry)
                if attempt == max_retries:
                    # Ensure callers can detect exhaustion distinctly via a flag
                    response.headers.setdefault("X-Retry-Exhausted", "1")
                    return response

                # Calculate backoff time with jitter
                backoff_time = min(backoff_factor * (2**attempt), max_backoff)
                jitter = random.uniform(0, 0.1 * backoff_time)  # Add up to 10% jitter
                wait_time = backoff_time + jitter

                print(
                    f"Rate limited (attempt {attempt + 1}/{max_retries + 1}), waiting {wait_time:.2f}s before retry..."
                )
                time.sleep(wait_time)

            except requests.exceptions.RequestException as e:
                # If this is the last attempt, re-raise the exception
                if attempt == max_retries:
                    # Attach retry exhaustion info before raising
                    e.args = (*e.args, "X-Retry-Exhausted=1")
                    raise

                # For connection errors, also apply backoff
                backoff_time = min(backoff_factor * (2**attempt), max_backoff)
                jitter = random.uniform(0, 0.1 * backoff_time)
                wait_time = backoff_time + jitter

                print(
                    f"Request failed (attempt {attempt + 1}/{max_retries + 1}): {e}, waiting {wait_time:.2f}s before retry..."
                )
                time.sleep(wait_time)

        # This should never be reached, but just in case
        raise RuntimeError("Unexpected end of retry loop")

    def get(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: MutableMapping[str, str] | None = None,
        timeout: float | None = None,
        retry: bool = True,
    ) -> requests.Response:
        """Send a GET request.

        Args:
            url: Target URL.
            params: Optional query string parameters.
            headers: Optional HTTP headers.
            timeout: Request timeout in seconds.
            retry: Whether to use retry/backoff logic.

        Returns:
            requests.Response: Server response.
        """
        return self.request(
            "GET", url, params=params, headers=headers, timeout=timeout, retry=retry
        )

    def post(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        headers: MutableMapping[str, str] | None = None,
        timeout: float | None = None,
        retry: bool = True,
        bulk_mode: bool = False,
    ) -> requests.Response:
        """Send a POST request.

        Args:
            url: Target URL.
            params: Optional query string parameters.
            json: Optional JSON body.
            data: Optional raw/form body.
            headers: Optional HTTP headers.
            timeout: Request timeout in seconds.
            retry: Whether to use retry/backoff logic.
            bulk_mode: Use bulk retry configuration.

        Returns:
            requests.Response: Server response.
        """
        return self.request(
            "POST",
            url,
            params=params,
            json=json,
            data=data,
            headers=headers,
            timeout=timeout,
            retry=retry,
            bulk_mode=bulk_mode,
        )

    def put(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        headers: MutableMapping[str, str] | None = None,
        timeout: float | None = None,
        retry: bool = True,
        bulk_mode: bool = False,
    ) -> requests.Response:
        """Send a PUT request.

        Args:
            url: Target URL.
            params: Optional query string parameters.
            json: Optional JSON body.
            data: Optional raw/form body.
            headers: Optional HTTP headers.
            timeout: Request timeout in seconds.
            retry: Whether to use retry/backoff logic.
            bulk_mode: Use bulk retry configuration.

        Returns:
            requests.Response: Server response.
        """
        return self.request(
            "PUT",
            url,
            params=params,
            json=json,
            data=data,
            headers=headers,
            timeout=timeout,
            retry=retry,
            bulk_mode=bulk_mode,
        )

    def patch(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        headers: MutableMapping[str, str] | None = None,
        timeout: float | None = None,
        retry: bool = True,
    ) -> requests.Response:
        """Send a PATCH request.

        Args:
            url: Target URL.
            params: Optional query string parameters.
            json: Optional JSON body.
            data: Optional raw/form body.
            headers: Optional HTTP headers.
            timeout: Request timeout in seconds.
            retry: Whether to use retry/backoff logic.

        Returns:
            requests.Response: Server response.
        """
        return self.request(
            "PATCH",
            url,
            params=params,
            json=json,
            data=data,
            headers=headers,
            timeout=timeout,
            retry=retry,
        )

    def delete(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: MutableMapping[str, str] | None = None,
        timeout: float | None = None,
        retry: bool = True,
    ) -> requests.Response:
        """Send a DELETE request.

        Args:
            url: Target URL.
            params: Optional query string parameters.
            headers: Optional HTTP headers.
            timeout: Request timeout in seconds.
            retry: Whether to use retry/backoff logic.

        Returns:
            requests.Response: Server response.
        """
        return self.request(
            "DELETE", url, params=params, headers=headers, timeout=timeout, retry=retry
        )


@pytest.fixture(scope="session")
def client(api_key: str) -> requests.Session:
    """Create a configured requests.Session for API calls.

    Args:
        api_key: API key to include in default headers.

    Returns:
        Configured requests.Session with default headers.
    """
    session = requests.Session()
    session.headers.update({"x-api-key": api_key, "Accept": "application/json"})
    return session


@pytest.fixture(scope="session")
def api_client(client: requests.Session) -> APIClient:
    """Provide an APIClient with retry logic enabled by default.

    Args:
        client: Shared requests.Session fixture.

    Returns:
        APIClient instance using the provided session.
    """
    return APIClient(client)


@pytest.fixture(scope="session")
def api_client_no_retry(client: requests.Session) -> APIClient:
    """API client with retries disabled - useful for testing rate limiting behavior."""
    api_client = APIClient(client)
    # Override methods to default retry=False
    original_request = api_client.request

    def request_no_retry(*args, **kwargs):
        kwargs.setdefault("retry", False)
        return original_request(*args, **kwargs)

    api_client.request = request_no_retry
    return api_client


@pytest.fixture(scope="session")
def users_endpoint(base_url: str) -> str:
    """Users endpoint base URL.

    Args:
        base_url: Base host URL for the API.

    Returns:
        Fully-qualified /api/users endpoint.
    """
    return f"{base_url}/api/users"


@pytest.fixture(scope="session")
def support_endpoint(base_url: str) -> str:
    """Support/resources endpoint base URL.

    Args:
        base_url: Base host URL for the API.

    Returns:
        Fully-qualified /api/unknown endpoint.
    """
    return f"{base_url}/api/unknown"


@pytest.fixture(scope="session")
def login_endpoint(base_url: str) -> str:
    """Login endpoint base URL.

    Args:
        base_url: Base host URL for the API.

    Returns:
        Fully-qualified /api/login endpoint.
    """
    return f"{base_url}/api/login"


@pytest.fixture(scope="session")
def register_endpoint(base_url: str) -> str:
    """Register endpoint base URL.

    Args:
        base_url: Base host URL for the API.

    Returns:
        Fully-qualified /api/register endpoint.
    """
    return f"{base_url}/api/register"


@pytest.fixture(scope="session")
def logout_endpoint(base_url: str) -> str:
    """Logout endpoint base URL.

    Args:
        base_url: Base host URL for the API.

    Returns:
        Fully-qualified /api/logout endpoint.
    """
    return f"{base_url}/api/logout"


@pytest.fixture
def valid_credentials() -> dict[str, str]:
    """Valid login credentials for successful authentication."""
    return {"email": "eve.holt@reqres.in", "password": "cityslicka"}


@pytest.fixture
def invalid_credentials() -> dict[str, str]:
    """Invalid login credentials missing password."""
    return {
        "email": "peter@klaven"
        # Missing password intentionally for negative testing
    }


@pytest.fixture(scope="session")
def test_data() -> dict[str, Any]:
    """Load test data from JSON file."""
    test_data_path = Path(__file__).parent.parent / "resources" / "data" / "test_users.json"
    with open(test_data_path, encoding="utf-8") as f:
        return json.load(f)


def verify_user_creation_response(response, expected_status_code, expected_data, schema):
    """Verify user creation response.

    Args:
        response: API response to verify
        expected_status_code: Expected HTTP status code
        expected_data: Dictionary containing the user data that was submitted
        schema: Schema to validate the response against
    """
    # Verify status code
    assert response.status_code == expected_status_code

    # Verify response schema
    payload = response.json()
    assert_valid_schema(payload, schema)

    # Verify user data matches what was submitted
    assert payload["name"] == expected_data["name"]
    assert payload["job"] == expected_data["job"]

    # Verify system-generated fields exist
    assert "id" in payload
    assert "createdAt" in payload

    return payload


@pytest.fixture
def valid_user_data(test_data) -> dict[str, str]:
    """Get a deterministic valid user data for creation tests."""
    # Use first valid user for consistency across test runs
    return test_data["valid_users"][0].copy()


@pytest.fixture
def update_user_data(test_data) -> dict[str, str]:
    """Get a deterministic update user data for update tests."""
    # Use first update user for consistency across test runs
    return test_data["update_users"][0].copy()


@pytest.fixture
def invalid_user_data(test_data) -> dict[str, Any]:
    """Get a deterministic invalid user data for negative testing."""
    # Use first invalid user for consistency across test runs
    return test_data["invalid_users"][0].copy()


@pytest.fixture
def edge_case_user_data(test_data) -> dict[str, str]:
    """Get a deterministic edge case user data for validation testing."""
    # Use first edge case user for consistency across test runs
    return test_data["edge_case_users"][0].copy()


@pytest.fixture
def performance_user_data(test_data) -> dict[str, str]:
    """Get a deterministic performance user data for performance testing."""
    # Use first performance user for consistency across test runs
    return test_data["performance_users"][0].copy()


@pytest.fixture
def all_valid_users(test_data) -> list[dict[str, str]]:
    """Get all valid user data for bulk testing."""
    return test_data["valid_users"].copy()


@pytest.fixture
def all_invalid_users(test_data) -> list[dict[str, Any]]:
    """Get all invalid user data for comprehensive negative testing."""
    return test_data["invalid_users"].copy()


# Factory fixtures for better test data management
@pytest.fixture
def user_data_factory(test_data):
    """Factory fixture to create user data on demand."""

    def _create_user_data(data_type: str = "valid", index: int = 0):
        """Create user data by type and index.

        Args:
            data_type: Type of data ('valid', 'invalid', 'edge_case', 'performance', 'update')
            index: Index of the data item to return
        """
        data_key = f"{data_type}_users"
        if data_key in test_data:
            data_list = test_data[data_key]
            if index < len(data_list):
                return data_list[index].copy()
        return {"name": "Default User", "job": "Default Job"}

    return _create_user_data


@pytest.fixture
def isolated_user_data():
    """Create unique user data for each test to ensure test isolation."""
    import time
    import uuid

    # Create unique identifiers to prevent test interference
    timestamp = int(time.time() * 1000)  # milliseconds
    unique_id = str(uuid.uuid4())[:8]

    return {"name": f"Test User {unique_id}", "job": f"Test Job {timestamp}"}


@pytest.fixture
def isolated_update_data():
    """Create unique update data for each test to ensure test isolation."""
    import time
    import uuid

    # Create unique identifiers to prevent test interference
    timestamp = int(time.time() * 1000)  # milliseconds
    unique_id = str(uuid.uuid4())[:8]

    return {"name": f"Updated User {unique_id}", "job": f"Updated Job {timestamp}"}


@pytest.fixture
def response_validator():
    """Factory fixture for common response validations."""

    def _validate_response(response, expected_status=None, schema=None, max_time=None):
        """Validate common response patterns."""
        # Status code validation
        if expected_status:
            assert response.status_code == expected_status

        # Schema validation
        if schema:
            payload = response.json()
            assert_valid_schema(payload, schema)
            return payload

        return response

    return _validate_response


@pytest.fixture
def performance_timer():
    """Fixture for measuring and asserting response times."""
    import time

    from tests.test_constants import PERFORMANCE_THRESHOLDS

    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()
            return self

        def stop(self):
            self.end_time = time.time()
            return self

        from typing import Literal

        # Define the valid threshold key types
        threshold_key_type = Literal[
            "RESPONSE_TIME_FAST",
            "RESPONSE_TIME_SLOW",
            "AVERAGE_RESPONSE_TIME",
            "CONCURRENT_REQUESTS",
            "BULK_OPERATIONS",
        ]

        def assert_within(self, threshold_key: str = "RESPONSE_TIME_FAST") -> PerformanceTimer:
            """Assert that the response time is within the specified threshold.

            Args:
                threshold_key: Key to use for threshold lookup in PERFORMANCE_THRESHOLDS.
                              Must be one of: 'RESPONSE_TIME_FAST', 'RESPONSE_TIME_SLOW',
                              'AVERAGE_RESPONSE_TIME', 'CONCURRENT_REQUESTS', 'BULK_OPERATIONS'

            Returns:
                Self for method chaining

            Raises:
                AssertionError: If response time exceeds threshold or timer wasn't started/stopped
                KeyError: If threshold_key doesn't exist in PERFORMANCE_THRESHOLDS
            """
            # Ensure timer was properly started and stopped
            if not (self.start_time and self.end_time):
                raise AssertionError(
                    "Timer must be started and stopped before asserting response time"
                )

            # Verify threshold_key exists before trying to access it
            valid_keys = (
                "RESPONSE_TIME_FAST",
                "RESPONSE_TIME_SLOW",
                "AVERAGE_RESPONSE_TIME",
                "CONCURRENT_REQUESTS",
                "BULK_OPERATIONS",
            )

            if threshold_key not in valid_keys:
                valid_keys_str = ", ".join(f"'{k}'" for k in valid_keys)
                raise KeyError(f"Invalid threshold_key: '{threshold_key}'. Must be one of: {valid_keys_str}")

            # Use cast to tell the type checker this is a valid key
            validated_key = cast(self.threshold_key_type, threshold_key)
            threshold = PERFORMANCE_THRESHOLDS[validated_key]

            # Compare elapsed time against threshold
            response_time = self.elapsed
            assert response_time < threshold, (
                f"Response time {response_time:.2f}s exceeds {threshold_key} threshold of {threshold:.2f}s"
            )

            return self


        @property
        def elapsed(self) -> float:
            """Get elapsed time in seconds."""
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0.0

    return PerformanceTimer()


def xfail_if_rate_limited(response, where: str | None = None):
    """Helper function to handle 429 rate limiting gracefully."""
    if response.status_code == 429:
        where_txt = f" during {where}" if where else ""
        pytest.xfail(f"Rate limited by external API (HTTP 429){where_txt}.")


# Allure-specific fixtures and helpers
@pytest.fixture
def allure_environment():
    """Fixture to set up Allure environment information."""
    with allure.step("Setting up test environment"):
        allure.attach(
            name="Environment Info",
            body=f"Base URL: {os.getenv('BASE_URL', 'https://reqres.in')}\n"
            f"API Key: {os.getenv('REQRES_API_KEY', 'reqres-free-v1')[:10]}...",
            attachment_type=allure.attachment_type.TEXT,
        )


@pytest.fixture
def allure_attach_response():
    """Fixture to attach response details to Allure report."""

    def _attach_response(response: requests.Response, step_name: str = "API Response"):
        with allure.step(step_name):
            # Attach response status
            allure.attach(
                name="Response Status",
                body=str(response.status_code),
                attachment_type=allure.attachment_type.TEXT,
            )

            # Attach response headers
            allure.attach(
                name="Response Headers",
                body=str(dict(response.headers)),
                attachment_type=allure.attachment_type.JSON,
            )

            # Attach response body if available
            try:
                if response.content:
                    allure.attach(
                        name="Response Body",
                        body=response.text,
                        attachment_type=allure.attachment_type.JSON,
                    )
            except Exception:
                # If JSON parsing fails, attach as text
                allure.attach(
                    name="Response Body",
                    body=response.text,
                    attachment_type=allure.attachment_type.TEXT,
                )

    return _attach_response


@pytest.fixture
def allure_attach_request():
    """Fixture to attach request details to Allure report."""

    def _attach_request(method: str, url: str, **kwargs):
        with allure.step(f"Making {method} request to {url}"):
            # Attach request details
            request_info = {
                "method": method,
                "url": url,
                "params": kwargs.get("params"),
                "json": kwargs.get("json"),
                "data": kwargs.get("data"),
                "headers": kwargs.get("headers"),
                "timeout": kwargs.get("timeout"),
            }

            allure.attach(
                name="Request Details",
                body=str(request_info),
                attachment_type=allure.attachment_type.JSON,
            )

    return _attach_request


def allure_step(step_name: str):
    """Decorator to add Allure step to test methods."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            with allure.step(step_name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def allure_attach_file(file_path: str, name: str | None = None, attachment_type: str = "TEXT"):
    """Helper to attach files to Allure report."""
    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        allure.attach(
            name=name or os.path.basename(file_path),
            body=content,
            attachment_type=getattr(
                allure.attachment_type, attachment_type, allure.attachment_type.TEXT
            ),
        )


# Rate limiting protection hooks
_last_test_class = None


def pytest_runtest_setup(item):
    """Add delays between test classes to prevent rate limiting."""
    global _last_test_class
    import time

    test_class = item.cls.__name__ if item.cls else "NoClass"

    # Add delay between different test classes
    if _last_test_class and _last_test_class != test_class:
        print("\nRate limiting protection: Waiting 2s between test classes...")
        time.sleep(2.0)

    _last_test_class = test_class

    # Small delay between tests in the same class
    time.sleep(0.5)
