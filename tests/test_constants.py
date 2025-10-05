"""Test constants and configuration (Google-style).

This module centralizes constants, typed configurations, and enums used by the
API test-suite. Keeping these values in one place ensures consistency across
tests and makes it easy to tune performance thresholds, retries, and timeouts.

Overview:
  - Strongly-typed configuration using TypedDict for clarity and IDE help.
  - HttpStatus enum for readable assertions in tests.
  - Groups of constants for performance, retries, timeouts, and test data.

Usage:
  Import the constants directly in tests, for example::

      from tests.test_constants import HTTP_STATUS, TEST_USER_IDS, TIMEOUTS
      assert HTTP_STATUS.OK == 200
      existing_id = TEST_USER_IDS["EXISTING_USER"]

Notes:
  All values are chosen to be reasonable defaults for CI environments. Adjust
  them if your target API has different performance characteristics.
"""

from __future__ import annotations

from enum import IntEnum

# Type definitions for better IDE support
from typing import Final, Literal, TypedDict

UserIdKey = Literal["EXISTING_USER", "ANOTHER_USER", "NON_EXISTENT_USER", "INVALID_USER"]

class UserIdConfig(TypedDict):
    """User identifier configuration.

    Attributes:
        EXISTING_USER (int): ID known to exist in the target system.
        ANOTHER_USER (int): A second valid user ID for comparative tests.
        NON_EXISTENT_USER (int): An ID that should not exist; used for 404 flows.
        INVALID_USER (str): Non-numeric value to validate type handling.
    """

    EXISTING_USER: int
    ANOTHER_USER: int
    NON_EXISTENT_USER: int
    INVALID_USER: str


class PerformanceConfig(TypedDict):
    """Performance thresholds used by tests.

    Attributes:
        RESPONSE_TIME_FAST (float): Expected upper bound for simple operations (s).
        RESPONSE_TIME_SLOW (float): Acceptable bound for complex operations (s).
        AVERAGE_RESPONSE_TIME (float): Target average across operations (s).
        CONCURRENT_REQUESTS (int): Number of concurrent requests for load tests.
        BULK_OPERATIONS (int): Number of operations for bulk/perf scenarios.
    """

    RESPONSE_TIME_FAST: float
    RESPONSE_TIME_SLOW: float
    AVERAGE_RESPONSE_TIME: float
    CONCURRENT_REQUESTS: int
    BULK_OPERATIONS: int


class TimeoutConfig(TypedDict):
    """Timeout configuration in seconds.

    Attributes:
        DEFAULT (float): Default timeout used by most tests.
        FAST (float): Stricter timeout for quick operations.
        SLOW (float): Relaxed timeout for heavy operations.
    """

    DEFAULT: float
    FAST: float
    SLOW: float


class RetryConfig(TypedDict):
    """Retry settings for handling transient failures.

    Attributes:
        MAX_RETRIES (int): Maximum number of retry attempts.
        BACKOFF_FACTOR (float): Exponential backoff factor between retries (s).
        RETRY_STATUS_CODES (list[int]): HTTP status codes that trigger a retry.
        MAX_BACKOFF (float): Maximum backoff time in seconds.
    """

    MAX_RETRIES: int
    BACKOFF_FACTOR: float
    RETRY_STATUS_CODES: list[int]
    MAX_BACKOFF: float


# Use enum for HTTP status codes for better type safety and code completion
class HttpStatus(IntEnum):
    """HTTP status codes used in assertions.

    Members:
        OK: 200, request succeeded.
        CREATED: 201, resource successfully created.
        NO_CONTENT: 204, successful with no response body.
        BAD_REQUEST: 400, client-side validation error.
        NOT_FOUND: 404, resource was not found.
    """

    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    NOT_FOUND = 404


# Alias for backward compatibility
HTTP_STATUS = HttpStatus
"""Alias for backward compatibility; prefer using HttpStatus directly."""


# Test user IDs for consistent testing
TEST_USER_IDS: Final[UserIdConfig] = {
    "EXISTING_USER": 2,
    "ANOTHER_USER": 3,
    "NON_EXISTENT_USER": 999,  # A user ID that should not exist in the system
    "INVALID_USER": "abc",  # Non-numeric value to test type validation
}
"""Preset user IDs used across tests.

Keys follow UserIdKey and map to either a valid integer user ID or a string for
invalid input scenarios.
"""


# Performance thresholds
class PerformanceThresholds:
    """Default performance thresholds for the test-suite.

    Attributes:
        RESPONSE_TIME_FAST (float): Upper bound for simple operations in seconds.
        RESPONSE_TIME_SLOW (float): Acceptable bound for complex operations in seconds.
        AVERAGE_RESPONSE_TIME (float): Target average response time in seconds.
        CONCURRENT_REQUESTS (int): Number of concurrent requests during load tests.
        BULK_OPERATIONS (int): Number of operations in bulk tests.
    """

    # Fast response expected for simple operations (e.g., single record retrieval)
    RESPONSE_TIME_FAST: Final[float] = 2.0  # seconds
    # Slower response acceptable for complex operations (e.g., filtered searches)
    RESPONSE_TIME_SLOW: Final[float] = 5.0  # seconds
    # Target average response time across all API operations
    AVERAGE_RESPONSE_TIME: Final[float] = 3.0  # seconds
    # Number of concurrent requests for load testing
    CONCURRENT_REQUESTS: Final[int] = 10
    # Number of operations to perform in bulk testing scenarios
    BULK_OPERATIONS: Final[int] = 5


# Use the class values to create the typed dictionary for compatibility
PERFORMANCE_THRESHOLDS: Final[PerformanceConfig] = {
    "RESPONSE_TIME_FAST": PerformanceThresholds.RESPONSE_TIME_FAST,
    "RESPONSE_TIME_SLOW": PerformanceThresholds.RESPONSE_TIME_SLOW,
    "AVERAGE_RESPONSE_TIME": PerformanceThresholds.AVERAGE_RESPONSE_TIME,
    "CONCURRENT_REQUESTS": PerformanceThresholds.CONCURRENT_REQUESTS,
    "BULK_OPERATIONS": PerformanceThresholds.BULK_OPERATIONS,
}
"""Concrete performance thresholds as a mapping compatible with TypedDict."""

# Test data patterns for Unicode and special character testing
TEST_PATTERNS: Final[dict[str, str]] = {
    "SPECIAL_CHARS": "José María O'Connor-Smith",  # Test handling of accents and special chars
    "UNICODE_CHARS": "张三李四",  # Test handling of non-Latin characters
    "EMPTY_STRING": "",  # Test handling of empty inputs
}
"""Common string patterns for unicode and edge-case testing."""

# Default test timeouts (in seconds)
TIMEOUTS: Final[TimeoutConfig] = {
    "DEFAULT": 30.0,
    "FAST": 10.0,
    "SLOW": 60.0,
}
"""Default timeouts in seconds for different test categories."""


# Retry configuration for rate limiting
class RetrySettings:
    """Default retry behavior for tests in CI environments.

    Attributes:
        MAX_RETRIES (int): Number of retry attempts before giving up.
        BACKOFF_FACTOR (float): Exponential backoff factor in seconds.
        RETRY_STATUS_CODES (list[int]): Status codes that should be retried.
        MAX_BACKOFF (float): Maximum backoff time regardless of retry count.
    """

    # Number of retry attempts before giving up (increased for CI)
    MAX_RETRIES: Final[int] = 5
    # Exponential backoff factor between retries (in seconds)
    BACKOFF_FACTOR: Final[float] = 2.0
    # Status codes that should trigger a retry:
    # 429: Too Many Requests (rate limiting)
    # 502: Bad Gateway, 503: Service Unavailable, 504: Gateway Timeout (server errors)
    RETRY_STATUS_CODES: Final[list[int]] = [429, 502, 503, 504]
    # Maximum backoff time regardless of retry count (increased for CI)
    MAX_BACKOFF: Final[float] = 30.0


# Create the typed dictionary for compatibility
RETRY_CONFIG: Final[RetryConfig] = {
    "MAX_RETRIES": RetrySettings.MAX_RETRIES,
    "BACKOFF_FACTOR": RetrySettings.BACKOFF_FACTOR,
    "RETRY_STATUS_CODES": RetrySettings.RETRY_STATUS_CODES,
    "MAX_BACKOFF": RetrySettings.MAX_BACKOFF,
}
"""Standard retry configuration suitable for most tests."""

# More aggressive retry configuration for bulk/performance tests
BULK_RETRY_CONFIG: Final[RetryConfig] = {
    "MAX_RETRIES": 8,  # More retries for bulk operations due to higher chance of rate limiting
    "BACKOFF_FACTOR": 3.0,  # Longer backoff to allow system recovery during heavy load
    "RETRY_STATUS_CODES": RetrySettings.RETRY_STATUS_CODES,
    "MAX_BACKOFF": 60.0,  # Longer maximum wait for bulk operations
}
"""More lenient retry configuration for bulk and performance scenarios."""
