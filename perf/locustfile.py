"""Basic Locust load tests for user management API.

This file focuses on essential concurrent load testing scenarios.
For functional performance testing, use pytest tests in tests/test_performance.py
"""

from __future__ import annotations

import random

from locust import HttpUser, between, task


class BasicLoadUser(HttpUser):
    """Basic load testing user for concurrent API testing."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Called when a user starts. Set up headers and base configuration."""
        self.client.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "x-api-key": "reqres-free-v1",
            }
        )

    @task(5)
    def get_users_list(self):
        """Test GET /api/users - most common operation."""
        page = random.randint(1, 3)
        self.client.get("/api/users", params={"page": page}, name="GET /api/users")

    @task(3)
    def get_single_user(self):
        """Test GET /api/users/{id} for existing users."""
        user_id = random.randint(1, 12)  # ReqRes has users 1-12
        self.client.get(f"/api/users/{user_id}", name="GET /api/users/{id}")

    @task(2)
    def create_user(self):
        """Test POST /api/users for user creation."""
        user_data = {
            "name": f"Load Test User {random.randint(1, 1000)}",
            "job": f"Load Test Job {random.randint(1, 100)}",
        }
        self.client.post("/api/users", json=user_data, name="POST /api/users")
