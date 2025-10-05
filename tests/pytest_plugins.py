"""
Pytest plugins for rate limiting protection.

This module provides pytest hooks to add delays between test classes
to prevent overwhelming external APIs with too many concurrent requests.
"""

import time


class RateLimitProtection:
    """Plugin to add delays between test classes to prevent rate limiting."""

    def __init__(self):
        self.last_test_class = None
        self.class_delay = 2.0  # 2 seconds between test classes
        self.test_delay = 0.5  # 0.5 seconds between tests in the same class

    def pytest_runtest_setup(self, item):
        """Add delay before each test if it's in a different class."""
        test_class = item.cls.__name__ if item.cls else "NoClass"

        if self.last_test_class and self.last_test_class != test_class:
            print(
                f"\nRate limiting protection: Waiting {self.class_delay}s between test classes..."
            )
            time.sleep(self.class_delay)

        self.last_test_class = test_class

        # Small delay between tests in the same class
        if self.last_test_class == test_class:
            time.sleep(self.test_delay)


# Register the plugin
def pytest_configure(config):
    """Register the rate limiting protection plugin."""
    config.pluginmanager.register(RateLimitProtection(), "rate_limit_protection")
