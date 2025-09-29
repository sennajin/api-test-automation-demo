"""Centralized test constants and configuration values."""

from __future__ import annotations
from enum import IntEnum
from typing import Dict, List, Final, TypedDict


# Version tracking for configuration changes
CONFIG_VERSION: Final[str] = "1.0.0"


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


class PatternConfig(TypedDict, total=False):
    LONG_STRING: str
    EMPTY_STRING: str
    SPECIAL_CHARS: str
    UNICODE_CHARS: str
    NUMERIC_STRING: str


class PaginationConfig(TypedDict):
    DEFAULT_PAGE: int
    TEST_PAGES: List[int]
    INVALID_PAGE: str


class TimeoutConfig(TypedDict):
    DEFAULT: float
    FAST: float
    SLOW: float


class RetryConfig(TypedDict):
    MAX_RETRIES: int
    BACKOFF_FACTOR: float
    RETRY_STATUS_CODES: List[int]
    MAX_BACKOFF: float


class SanitizationPatternsConfig(TypedDict):
    HTML_TAGS: str
    SQL_INJECTION: str
    SCRIPT_INJECTION: str
    PATH_TRAVERSAL: str
    COMMAND_INJECTION: str


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

# Common test data patterns
TEST_PATTERNS: Final[PatternConfig] = {
    # 1000 chars to test handling of long string inputs (chosen to exceed typical
    # VARCHAR limits in databases while staying under request size limits)
    "LONG_STRING": "x" * 1000,
    "EMPTY_STRING": "",  # Test handling of empty inputs
    "SPECIAL_CHARS": "José María O'Connor-Smith",  # Test handling of accents and special chars
    "UNICODE_CHARS": "张三李四",  # Test handling of non-Latin characters
    "NUMERIC_STRING": "12345",  # Test handling of numeric strings vs integers
}

# Pagination defaults
PAGINATION_DEFAULTS: Final[PaginationConfig] = {
    "DEFAULT_PAGE": 1,
    "TEST_PAGES": [1, 2, 3],  # Common pages to test pagination functionality
    "INVALID_PAGE": "invalid",  # String value to test type validation for page parameter
}

# Environment-specific timeout configurations
ENV_SPECIFIC_TIMEOUTS: Dict[str, TimeoutConfig] = {
    "local": {"DEFAULT": 10.0, "FAST": 5.0, "SLOW": 30.0},
    "ci": {"DEFAULT": 30.0, "FAST": 10.0, "SLOW": 60.0},
    "staging": {"DEFAULT": 45.0, "FAST": 15.0, "SLOW": 90.0},
}

# Default test timeouts (in seconds)
TIMEOUTS: Final[TimeoutConfig] = ENV_SPECIFIC_TIMEOUTS["ci"]  # Default to CI environment


# Retry configuration for rate limiting
class RetrySettings:
    # Number of retry attempts before giving up (increased for CI)
    MAX_RETRIES: Final[int] = 5
    # Exponential backoff factor between retries (in seconds)
    BACKOFF_FACTOR: Final[float] = 2.0
    # Status codes that should trigger a retry:
    # 429: Too Many Requests (rate limiting)
    # 502: Bad Gateway, 503: Service Unavailable, 504: Gateway Timeout (server errors)
    RETRY_STATUS_CODES: Final[List[int]] = [429, 502, 503, 504]
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

# Patterns for testing input sanitization
SANITIZATION_PATTERNS: Final[SanitizationPatternsConfig] = {
    "HTML_TAGS": "<script>alert('XSS')</script>",
    "SQL_INJECTION": "' OR '1'='1",
    "SCRIPT_INJECTION": "javascript:alert(document.cookie)",
    "PATH_TRAVERSAL": "../../../etc/passwd",
    "COMMAND_INJECTION": "$(cat /etc/passwd)"
}

# Expected security headers in responses
EXPECTED_SECURITY_HEADERS: Final[List[str]] = [
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-XSS-Protection"
]
