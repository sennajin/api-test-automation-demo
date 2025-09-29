# API Testing Automation Framework

A comprehensive pytest-based API testing framework for RESTful APIs, with a focus on the ReqRes.in API. This framework provides extensive test coverage for API endpoints, including functional, performance, and security testing.

## Features

- **Comprehensive Test Coverage**: CRUD operations, authentication, security, and performance tests
- **Robust API Client**: Custom client with retry logic, error handling, and rate limiting protection
- **Schema Validation**: JSON schema validation for response structure verification
- **Performance Testing**: Load and stress testing with Locust and pytest-based performance assertions
- **Advanced Reporting**: Allure reporting with GitHub Pages deployment and historical tracking
- **Test Data Management**: Comprehensive test data fixtures for various scenarios
- **Parallel Execution**: Support for parallel test execution with pytest-xdist
- **CI/CD Integration**: Automated testing with GitHub Actions and comprehensive reporting
- **Security Testing**: Dedicated security test suite with authentication and authorization tests
- **Smoke Testing**: Quick validation tests for basic API functionality

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
│   └── locust_to_allure.py # Locust to Allure results converter
├── tests/                  # Test files
│   ├── conftest.py         # Pytest configuration and fixtures
│   ├── schemas/            # JSON schemas for validation
│   │   └── json_schemas.py # Schema definitions
│   ├── test_auth_login.py  # Authentication tests
│   ├── test_users_crud.py  # CRUD operation tests (includes smoke tests)
│   ├── test_users_security.py # Security tests
│   ├── test_performance.py # Performance tests
│   ├── test_constants.py   # Test constants and configuration
│   └── security_config.py  # Security test configuration
├── pytest.ini             # Pytest configuration
├── pyproject.toml         # Project configuration
└── requirements.txt       # Project dependencies
```

## Installation

1. Clone the repository
2. Create and activate a virtual environment (Python 3.12+ recommended)
3. Install dependencies:

```bash
pip install -r requirements.txt
```

Or install with development dependencies:

```bash
pip install -e ".[dev]"
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
pytest -m performance  # Run performance tests
pytest -m "not slow"  # Exclude slow tests
pytest -m "crud and not slow"  # Run CRUD tests excluding slow ones
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
locust -f perf/locustfile.py BasicLoadUser --host=https://reqres.in --users=50 --spawn-rate=5 --run-time=120s --headless

# Web UI for interactive testing
locust -f perf/locustfile.py --host=https://reqres.in
```

### Advanced Performance Testing

The framework includes sophisticated performance testing capabilities:

```bash
# Run pytest performance tests
pytest -m performance

# Run Locust with CSV output for Allure integration
locust -f perf/locustfile.py --host=https://reqres.in --users=10 --spawn-rate=2 --run-time=60s --headless --csv=locust_results --html=locust-report.html

# Convert Locust results to Allure format
python scripts/locust_to_allure.py --csv-file locust_results_stats.csv --output-dir allure-results
```

## Reporting

### Local Reporting

Generate and view Allure reports locally:

```bash
# Run tests with Allure reporting
pytest --alluredir=reports/allure-results

# Generate and open Allure report (requires Allure CLI)
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report
```

### CI/CD Reporting

The project includes a comprehensive GitHub Actions workflow that:
- Runs tests on Python 3.12
- Executes both pytest and Locust performance tests
- Generates combined Allure reports from both test types
- Publishes reports to GitHub Pages with historical data
- Includes automated scheduling (daily at 2 AM UTC)
- Supports manual workflow dispatch

**Workflow Features:**
- **Parallel Test Execution**: Uses pytest-xdist for parallel test runs
- **Performance Testing**: Automated Locust load testing with Allure integration
- **Report Merging**: Combines pytest and Locust results into unified Allure reports
- **Historical Tracking**: Maintains test history across runs
- **Artifact Management**: Stores test artifacts and reports

The Allure reports are available at: `https://<username>.github.io/<repository>/`

To enable GitHub Pages for your repository:
1. Go to your repository settings
2. Navigate to the "Pages" section
3. Select "GitHub Actions" as the source
4. The workflow will automatically deploy the Allure reports to GitHub Pages

## Test Categories

The framework includes the following test categories:

- **Smoke Tests**: Basic API availability and functionality tests (integrated in `test_users_crud.py`)
- **Regression Tests**: Comprehensive functional tests
- **CRUD Tests**: Create, Read, Update, Delete operations (`test_users_crud.py`)
- **Security Tests**: Authentication, authorization, and security edge cases (`test_users_security.py`, `test_auth_login.py`)
- **Performance Tests**: Response time, throughput, and load testing (`test_performance.py`)
- **Data Validation Tests**: Schema validation and data integrity tests
- **Authentication Tests**: Login and authentication flow testing (`test_auth_login.py`)

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
The performance testing approach uses multiple complementary methods:
- **Locust-based load testing**: For realistic user simulation and concurrency testing
- **Pytest-based performance assertions**: For consistent performance validation during regular test runs
- **Automated CI/CD performance testing**: Integrated performance testing in the GitHub Actions workflow
- **Allure performance reporting**: Combined reporting of both pytest and Locust performance results

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

### Test Data Strategy
The framework includes comprehensive test data management:
- **Valid Data**: Standard test cases for positive scenarios
- **Invalid Data**: Edge cases and boundary testing
- **Performance Data**: Specialized data for load testing
- **Edge Case Data**: Unicode, special characters, and extreme values
- **Update Data**: Specific data for update operations

This strategy ensures that the API is tested from multiple perspectives, providing confidence in both its functional correctness and non-functional characteristics like performance, security, and reliability.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
