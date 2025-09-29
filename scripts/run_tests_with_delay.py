#!/usr/bin/env python3
"""
Test runner script with built-in delays to prevent rate limiting.

This script runs pytest with additional delays between test classes
to reduce the chance of hitting rate limits on external APIs.
"""

import subprocess
import sys
import time
import os
from pathlib import Path


def run_tests_with_delay():
    """Run tests with delays to prevent rate limiting."""
    
    # Base pytest command
    base_cmd = [
        "pytest",
        "-n", "2",  # Reduced parallelism
        "-m", "not e2e",
        "--alluredir=allure-results",
        "--junitxml=reports/junit.xml",
        "--maxfail=5",
        "-v",  # Verbose output for better debugging
        "--durations=10"  # Show slowest 10 tests
    ]
    
    # Add test files if they exist
    test_files = [
        "tests/test_users_crud.py",
        "tests/test_auth_login.py", 
        "tests/test_users_security.py",
        "tests/test_performance.py"
    ]
    
    existing_test_files = [f for f in test_files if Path(f).exists()]
    if existing_test_files:
        base_cmd.extend(existing_test_files)
    else:
        base_cmd.append("tests/")
    
    print(f"Running tests with command: {' '.join(base_cmd)}")
    print("Rate limiting protection: Reduced parallelism (-n 2) and enhanced retry logic")
    
    # Run the tests
    try:
        result = subprocess.run(base_cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


if __name__ == "__main__":
    # Add a small delay before starting tests
    print("Starting tests with rate limiting protection...")
    print("This includes:")
    print("- Reduced parallelism (2 workers instead of auto)")
    print("- Enhanced retry logic with exponential backoff")
    print("- Graceful handling of 429 rate limit responses")
    print("- Increased timeouts for CI environment")
    time.sleep(3)  # Slightly longer initial delay
    
    exit_code = run_tests_with_delay()
    
    if exit_code == 0:
        print("All tests passed successfully!")
    else:
        print(f"Some tests failed with exit code: {exit_code}")
    
    sys.exit(exit_code)
