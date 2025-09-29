# API Testing Automation Framework

A comprehensive pytest-based API testing framework for RESTful APIs, with a focus on the ReqRes.in API. This framework provides extensive test coverage for API endpoints, including functional, performance, and security testing.

## Features

- **Comprehensive Test Coverage**: CRUD operations, authentication, security, and performance tests
- **Robust API Client**: Custom client with retry logic, error handling, and rate limiting protection
- **Schema Validation**: JSON schema validation for response structure verification
- **Performance Testing**: Load and stress testing with Locust
- **Reporting**: Allure reporting for detailed test results visualization
- **Test Data Management**: Fixtures for various test data scenarios
- **Parallel Execution**: Support for parallel test execution with pytest-xdist

## Project Structure

```
├── perf/                   # Performance testing files
│   └── locustfile.py       # Locust load testing configuration
├── reports/                # Test reports directory
│   ├── allure-results/     # Allure test results
│   └── allure-report/      # Generated Allure reports
├── resources/              # Test resources
│   └── data/               # Test data files
│       └── test_users.json # User data for testing
├── scripts/                # Utility scripts
│   ├── generate_allure_report.bat  # Windows script for Allure reports
│   └── generate_allure_report.py   # Python script for Allure reports
├── tests/                  # Test files
│   ├── conftest.py         # Pytest configuration and fixtures
│   ├── schemas/            # JSON schemas for validation
│   │   └── json_schemas.py # Schema definitions
│   ├── test_auth_login.py  # Authentication tests
│   ├── test_users_crud.py  # CRUD operation tests
│   ├── test_users_security.py # Security tests
│   └── test_performance.py # Performance tests
├── pytest.ini             # Pytest configuration
├── pyproject.toml         # Project configuration
└── requirements.txt       # Project dependencies
```

## Installation

1. Clone the repository
2. Create and activate a virtual environment (Python 3.10+ required)
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running Tests

### Basic Test Execution

Run all tests:

```bash
pytest
```

Run specific test categories:

```bash
pytest -m smoke  # Run smoke tests
pytest -m regression  # Run regression tests
pytest -m crud  # Run CRUD tests
pytest -m security  # Run security tests
```

### Parallel Test Execution

Run tests in parallel:

```bash
pytest -n auto  # Use all available CPU cores
pytest -n 4     # Use 4 CPU cores
```

### Performance Testing

Run performance tests with Locust:

```bash
# Basic load test (10 users, 2 users/second spawn rate, 60 second test)
locust -f perf/locustfile.py --host=https://reqres.in --users=10 --spawn-rate=2 --run-time=60s --headless

# High concurrency test (50 users, 5 users/second spawn rate, 120 second test)
locust -f perf/locustfile.py BasicLoadUser HighConcurrencyUser --host=https://reqres.in --users=50 --spawn-rate=5 --run-time=120s --headless

# Web UI for interactive testing
locust -f perf/locustfile.py --host=https://reqres.in
```

## Reporting

### Local Reporting

Generate and view Allure reports locally:

```bash
# Run tests with Allure reporting
pytest --alluredir=reports/allure-results

# Generate and open Allure report
python scripts/generate_allure_report.py --open

# Or use the batch script on Windows
scripts\generate_allure_report.bat
```

### CI/CD Reporting

The project includes a GitHub Actions workflow that:
- Runs tests on Python 3.10
- Excludes slow tests
- Generates Allure reports
- Publishes the reports to GitHub Pages

The Allure reports are available at: `https://<username>.github.io/<repository>/`

To enable GitHub Pages for your repository:
1. Go to your repository settings
2. Navigate to the "Pages" section
3. Select "GitHub Actions" as the source
4. The workflow will automatically deploy the Allure reports to GitHub Pages

## Test Categories

The framework includes the following test categories:

- **Smoke Tests**: Basic API availability and functionality tests
- **Regression Tests**: Comprehensive functional tests
- **CRUD Tests**: Create, Read, Update, Delete operations
- **Security Tests**: Authentication, authorization, and security edge cases
- **Performance Tests**: Response time, throughput, and load testing
- **Data Validation Tests**: Schema validation and data integrity tests

## Test Strategy and Reasoning

The testing strategy for this framework follows a multi-layered approach designed to ensure comprehensive API quality assurance:

### Pyramid Testing Approach
- **Foundation Layer**: Unit and component tests that validate individual API endpoints and their basic functionality
- **Middle Layer**: Integration tests that verify interactions between multiple endpoints and features
- **Top Layer**: End-to-end scenarios that simulate real user workflows

### Strategic Test Selection
The test selection strategy prioritizes:

1. **Critical Path Testing**: Ensuring key user management actions like creating, retrieving, updating, and deleting users—work correctly.
2. **Risk-Based Testing**: Focusing more tests on high-risk areas (authentication, data manipulation)
3. **Boundary Analysis**: Testing edge cases and limits of the API's capabilities

Here’s a revised section that integrates the explanation about your **pytest marks**:

---

### Test Organization Reasoning
Tests are organized by **functional area** rather than test type to:

* Improve maintainability by keeping related tests together
* Enable selective execution of specific functional areas
* Provide better visibility into test coverage for each feature

In addition, **pytest markers** are used to tag tests for quick filtering and targeted runs.
This allows you to execute only the tests you need (for example, just CRUD or just performance) without running the entire suite:

```
@pytest.mark.smoke           # Basic availability checks
@pytest.mark.regression      # Regression tests
@pytest.mark.crud            # CRUD operation tests
@pytest.mark.post            # POST call tests
@pytest.mark.get             # GET operation tests
@pytest.mark.put             # PUT operation tests
@pytest.mark.delete          # DELETE operation tests
@pytest.mark.negative        # Negative test cases
@pytest.mark.data_validation # Data validation tests
@pytest.mark.performance     # Performance and load tests
@pytest.mark.security        # Security and penetration tests
@pytest.mark.slow            # Slow-running tests
```

Using both **functional grouping** and **markers** provides maximum flexibility:
you can keep related tests together for clarity while still running focused subsets
(for example, `pytest -m "crud and not slow"`) as part of CI/CD pipelines or local development.


### Performance Testing Philosophy
The performance testing approach uses two complementary methods:
- **Locust-based load testing**: For realistic user simulation and concurrency testing
- **Pytest-based performance assertions**: For consistent performance validation during regular test runs

### Schema Validation Strategy
JSON schema validation is used extensively because:
- It provides a contract-first approach to API testing
- It catches structural changes that might break client applications
- It reduces the need for numerous explicit assertions

### Retry and Resilience Mechanisms
The custom API client includes retry logic to:
- Handle transient failures gracefully
- Prevent false test failures due to network issues or rate limiting
- Simulate real-world client behavior with exponential backoff

This strategy ensures that the API is tested from multiple perspectives, providing confidence in both its functional correctness and non-functional characteristics like performance, security, and reliability.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
