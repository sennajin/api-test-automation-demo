"""Centralized test constants and configuration values."""

from __future__ import annotations

from enum import IntEnum
from typing import Final, TypedDict


# Type definitions for better IDE support
class UserIdConfig(TypedDict):
    EXISTING_USER: int
    ANOTHER_USER: int
    NON_EXISTENT_USER: int
    INVALID_USER: str


class PerformanceConfig(TypedDict):
    RESPONSE_TIME_FAST: float
    RESPONSE_TIME_SLOW: float
    AVERAGE_RESPONSE_TIME: float
    CONCURRENT_REQUESTS: int
    BULK_OPERATIONS: int


class TimeoutConfig(TypedDict):
    DEFAULT: float
    FAST: float
    SLOW: float


class RetryConfig(TypedDict):
    MAX_RETRIES: int
    BACKOFF_FACTOR: float
    RETRY_STATUS_CODES: list[int]
    MAX_BACKOFF: float


# Use enum for HTTP status codes for better type safety and code completion
class HttpStatus(IntEnum):
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    NOT_FOUND = 404


# Alias for backward compatibility
HTTP_STATUS = HttpStatus


# Test user IDs for consistent testing
TEST_USER_IDS: Final[UserIdConfig] = {
    "EXISTING_USER": 2,
    "ANOTHER_USER": 3,
    "NON_EXISTENT_USER": 999,  # A user ID that should not exist in the system
    "INVALID_USER": "abc",  # Non-numeric value to test type validation
}


# Performance thresholds
class PerformanceThresholds:
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

# Test data patterns for Unicode and special character testing
TEST_PATTERNS: Final[dict[str, str]] = {
    "SPECIAL_CHARS": "José María O'Connor-Smith",  # Test handling of accents and special chars
    "UNICODE_CHARS": "张三李四",  # Test handling of non-Latin characters
    "EMPTY_STRING": "",  # Test handling of empty inputs
}

# Default test timeouts (in seconds)
TIMEOUTS: Final[TimeoutConfig] = {
    "DEFAULT": 30.0,
    "FAST": 10.0,
    "SLOW": 60.0,
}


# Retry configuration for rate limiting
class RetrySettings:
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

# More aggressive retry configuration for bulk/performance tests
BULK_RETRY_CONFIG: Final[RetryConfig] = {
    "MAX_RETRIES": 8,  # More retries for bulk operations due to higher chance of rate limiting
    "BACKOFF_FACTOR": 3.0,  # Longer backoff to allow system recovery during heavy load
    "RETRY_STATUS_CODES": RetrySettings.RETRY_STATUS_CODES,
    "MAX_BACKOFF": 60.0,  # Longer maximum wait for bulk operations
}
