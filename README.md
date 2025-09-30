# API Testing Automation Framework

A pytest-based API testing framework for RESTful APIs, with a focus on the ReqRes.in API. This framework provides test coverage for core API functionality, including CRUD operations, authentication, and performance testing.

## Features

- **Test Coverage**: Test suite covering core CRUD operations, authentication, and performance
- **Robust API Client**: Custom client with retry logic, error handling, and rate limiting protection
- **Schema Validation**: JSON schema validation for response structure verification
- **Performance Testing**: Response time tracking and basic SLA compliance testing
- **Advanced Reporting**: Allure reporting with GitHub Pages deployment and historical tracking
- **Test Data Management**: Comprehensive test data fixtures for various scenarios
- **Parallel Execution**: Support for parallel test execution with pytest-xdist
- **CI/CD Integration**: Automated testing with GitHub Actions and comprehensive reporting

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
│   ├── test_api_endpoints.py # Streamlined test suite (CRUD, Auth, Performance)
│   └── test_constants.py   # Test constants and configuration
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
pytest -m security  # Run authentication tests
pytest -m performance  # Run performance tests
```

### Parallel Test Execution

Run tests in parallel:

```bash
pytest -n auto  # Use all available CPU cores
pytest -n 4     # Use 4 CPU cores
```
### CLI Test Runs:
---
![A test run with Failures and a test run that Succeeded](assets\img\test_api_endpoints_cli.png)

### Performance Testing

The framework includes performance testing capabilities:

```bash
# Run pytest performance tests
pytest -m performance

# Basic load test (10 users, 2 users/second spawn rate, 60 second test)
locust -f perf/locustfile.py --host=https://reqres.in --users=10 --spawn-rate=2 --run-time=60s --headless

# High concurrency test (50 users, 5 users/second spawn rate, 120 second test)
locust -f perf/locustfile.py BasicLoadUser --host=https://reqres.in --users=50 --spawn-rate=5 --run-time=120s --headless

# Run Locust with CSV output for Allure integration
locust -f perf/locustfile.py --host=https://reqres.in --users=10 --spawn-rate=2 --run-time=60s --headless --csv=locust_results --html=locust-report.html

# Convert Locust results to Allure format
python scripts/locust_to_allure.py --csv-file locust_results_stats.csv --output-dir allure-results
```

![Locusts tests run in CLI](assets\img\locust_tests.png)

### CI/CD Reporting

The project includes a GitHub Actions workflow that:
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

Generate and view Allure reports locally:

```bash
# Run tests with Allure reporting
pytest --alluredir=reports/allure-results

# Generate and open Allure report (requires Allure CLI)
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report
```

### Allure Test Reports:
![Allure test report dashboard](assets\img\allure_dashboard.png)

![Allure test report graphs](assets\img\allure_graphs.png)

![Allure test report suite details](assets\img\allure_suites.png)

## Test Strategy and Reasoning

The testing strategy focuses on core API functionality with a simplified, maintainable approach:

### Test Coverage
The test selection strategy prioritizes:

1. **Core Functionality**: Essential CRUD operations (Create, Read, Update, Delete)
2. **Authentication**: Basic login functionality with valid and invalid credentials
3. **Performance**: Response time tracking and SLA compliance
4. **Data Validation**: Schema validation and data integrity
5. **Error Handling**: Missing fields, extra fields, delete twice, update non-existent user

### Streamlined Organization
Tests are organized in a single file with clear class separation:

- **TestUserCreation**: User creation with valid data, invalid data, and extra fields
- **TestUserRetrieval**: User retrieval and list operations
- **TestUserUpdate**: User updates and non-existent user handling
- **TestUserDeletion**: User deletion including idempotency testing
- **TestAuthentication**: Login functionality and error handling
- **TestPerformance**: Response time tracking and SLA compliance

### Pytest Markers
The framework uses focused markers for test categorization:

```
@pytest.mark.crud            # CRUD operation tests
@pytest.mark.negative        # Negative test cases
@pytest.mark.data_validation # Data validation tests
@pytest.mark.performance     # Performance and response time tests
@pytest.mark.security        # Authentication tests
@pytest.mark.smoke           # Basic functionality tests
@pytest.mark.regression      # Regression tests
```

### Performance Testing
The performance testing approach focuses on:
- **Response Time Tracking**: Individual operation response time validation
- **SLA Compliance**: Basic performance threshold testing
- **Locust Integration**: Optional load testing for advanced scenarios
- **Allure Reporting**: Performance metrics in test reports

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