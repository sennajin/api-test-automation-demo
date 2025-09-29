"""Simplified Locust load tests for user management API.

This file focuses on basic concurrent load testing scenarios.
For functional performance testing, use pytest tests in tests/test_performance.py
"""

from __future__ import annotations

import random
from locust import HttpUser, task, between


class BasicLoadUser(HttpUser):
    """Basic load testing user for concurrent API testing."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a user starts. Set up headers and base configuration."""
        self.client.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-api-key": "reqres-free-v1"
        })
    
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
            "job": f"Load Test Job {random.randint(1, 100)}"
        }
        self.client.post("/api/users", json=user_data, name="POST /api/users")
    
    @task(1)
    def update_user(self):
        """Test PUT /api/users/{id} for user updates."""
        user_id = random.randint(1, 12)
        update_data = {
            "name": f"Updated User {random.randint(1, 1000)}",
            "job": f"Updated Job {random.randint(1, 100)}"
        }
        self.client.put(f"/api/users/{user_id}", json=update_data, name="PUT /api/users/{id}")
    
    @task(1)
    def delete_user(self):
        """Test DELETE /api/users/{id} for user deletion."""
        user_id = random.randint(1, 12)
        self.client.delete(f"/api/users/{user_id}", name="DELETE /api/users/{id}")


class HighConcurrencyUser(HttpUser):
    """High concurrency user for stress testing with many simultaneous users."""
    
    wait_time = between(1.0, 3.0)  # Increased wait times to reduce rate limiting
    
    def on_start(self):
        """Set up headers for high concurrency testing."""
        self.client.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-api-key": "reqres-free-v1"
        })
    
    @task(8)
    def rapid_user_list_requests(self):
        """Rapidly request user lists to test concurrent load handling."""
        page = random.randint(1, 2)
        self.client.get("/api/users", params={"page": page}, name="GET /api/users (high load)")
    
    @task(2)
    def rapid_user_creation(self):
        """Create users under high concurrent load."""
        user_data = {
            "name": f"Concurrent User {random.randint(1, 10000)}",
            "job": f"Concurrent Job {random.randint(1, 100)}"
        }
        self.client.post("/api/users", json=user_data, name="POST /api/users (high load)")


class RealisticUsageUser(HttpUser):
    """User that simulates realistic usage patterns for load testing."""
    
    wait_time = between(2, 8)  # Realistic thinking time between actions
    
    def on_start(self):
        """Initialize realistic user session."""
        self.client.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-api-key": "reqres-free-v1"
        })
    
    @task(10)
    def browse_users(self):
        """Most common action - browsing users."""
        page = random.randint(1, 3)
        self.client.get("/api/users", params={"page": page}, name="Browse users")
    
    @task(5)
    def view_user_details(self):
        """View specific user details."""
        user_id = random.randint(1, 12)
        self.client.get(f"/api/users/{user_id}", name="View user details")
    
    @task(2)
    def create_new_user(self):
        """Occasionally create new users."""
        user_data = {
            "name": f"New User {random.randint(1, 1000)}",
            "job": random.choice([
                "Software Engineer", "Product Manager", "Designer",
                "Data Scientist", "DevOps Engineer", "QA Engineer"
            ])
        }
        self.client.post("/api/users", json=user_data, name="Create user")
    
    @task(1)
    def update_existing_user(self):
        """Rarely update users."""
        user_id = random.randint(1, 12)
        update_data = {
            "name": f"Updated User {random.randint(1, 1000)}",
            "job": f"Updated Job {random.randint(1, 100)}"
        }
        self.client.put(f"/api/users/{user_id}", json=update_data, name="Update user")


# Example usage commands:
#
# Basic load test (10 users, 2 users/second spawn rate, 60 second test):
# locust -f locustfile.py --host=https://reqres.in --users=10 --spawn-rate=2 --run-time=60s --headless
#
# High concurrency test (50 users, 5 users/second spawn rate, 120 second test):
# locust -f locustfile.py BasicLoadUser HighConcurrencyUser --host=https://reqres.in --users=50 --spawn-rate=5 --run-time=120s --headless
#
# Realistic usage simulation (20 users, 1 user/second spawn rate, 300 second test):
# locust -f locustfile.py RealisticUsageUser --host=https://reqres.in --users=20 --spawn-rate=1 --run-time=300s --headless
#
# Web UI for interactive testing:
# locust -f locustfile.py --host=https://reqres.in