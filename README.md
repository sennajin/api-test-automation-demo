# PyTest API Automation

A comprehensive PyTest-based API automation suite that demonstrates functional, negative, schema validation, security, and performance testing with CI/CD integration.

## Quick Start

### Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running All Tests
```bash
pytest
```

### Running with Reports

#### Standard HTML and JUnit Reports
```bash
# Generate HTML and JUnit reports
pytest --junitxml=reports/junit.xml --html=reports/report.html --self-contained-html

# Run with parallel execution for faster results
pytest -n auto --html=reports/report.html --self-contained-html --junitxml=reports/junit.xml

# Generate reports for specific test categories
pytest -m smoke --html=reports/smoke-report.html --self-contained-html --junitxml=reports/smoke-junit.xml
pytest -m crud --html=reports/crud-report.html --self-contained-html --junitxml=reports/crud-junit.xml
pytest -m performance --html=reports/performance-report.html --self-contained-html --junitxml=reports/performance-junit.xml
pytest -m security --html=reports/security-report.html --self-contained-html --junitxml=reports/security-junit.xml
```

#### Allure Reports (Advanced Reporting)
```bash
# Install Allure command line tool
# Windows: scoop install allure or choco install allure-commandline
# macOS: brew install allure
# Linux: npm install -g allure-commandline

# Run tests with Allure results collection
pytest --alluredir=reports/allure-results

# Generate and view Allure report
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report

# Or use the provided script (Windows)
scripts\generate_allure_report.bat --open --clean

# Or use the provided script (Cross-platform)
python scripts/generate_allure_report.py --open --clean
```

**Allure Report Features:**
- **Interactive Dashboard**: Visual test results with trends and history
- **Detailed Test Steps**: Step-by-step execution with attachments
- **Trends & Analytics**: Track test stability and performance over time
- **Smart Categorization**: Automatic grouping by features, severity, and status
- **Rich Attachments**: Request/response details, logs, and screenshots
- **Flaky Test Detection**: Identify unstable tests with trend analysis

### Running Specific Test Categories

#### Smoke Tests (Quick validation)
```bash
pytest -m smoke
```

#### CRUD Operations Tests
```bash
pytest -m crud
```

#### Negative Test Cases
```bash
pytest -m negative
```

#### Data Validation Tests
```bash
pytest -m validation
```

#### Performance Tests
```bash
pytest -m performance
```

#### HTTP Method Specific Tests
```bash
# POST operation tests
pytest -m post

# GET operation tests
pytest -m get

# PUT operation tests
pytest -m put

# DELETE operation tests
pytest -m delete

# Multiple HTTP methods
pytest -m "post or get"
pytest -m "put or delete"
```

#### Security Tests
```bash
pytest -m security
```

#### Slow-running Tests (Performance & Load)
```bash
pytest -m slow
```

## 🔧 Configuration

### Environment Variables
```bash
export BASE_URL="https://reqres.in"
export REQRES_API_KEY="your-api-key"
```

### Command Line Options
```bash
pytest --base-url="https://your-api.com" --api-key="your-key"
```

### Configuration Files
* `pytest.ini` for defaults
* `pyproject.toml` for dependencies and linting
* `BASE_URL` env or `--base-url` option to point at different hosts

## Test Strategy and Reasoning

This test suite implements a comprehensive risk-based testing approach aligned with best practices and the Technical Challenge requirements. The strategy prioritizes test cases based on business impact, failure probability, user experience, and security considerations.

### Response Time Goals

The test suite validates performance against explicit response time thresholds:

- **Individual Operations**: < 2 seconds
- **User Updates**: < 5 seconds  
- **End-to-End Workflow**: < 10 seconds
- **Bulk Operations**: < 30 seconds

These thresholds are validated through dedicated performance tests and load testing scenarios.

## Test Coverage

### GET Operations
- List users with pagination
- Get single user by ID
- Non-existent user handling (404)
- Invalid ID format handling
- Response time validation
- Schema validation

### POST Operations (User Creation)
- Valid user creation
- Response schema validation
- Missing field validation
- Empty field validation
- Null value handling
- Extra field handling
- Special character support
- Unicode character support
- Long string handling
- Response time validation

### PUT Operations (User Updates)
- Full user update
- Partial user update
- Non-existent user update
- Empty payload handling
- Invalid value validation
- Response time validation
- Schema validation

### DELETE Operations
- Successful user deletion
- Non-existent user deletion
- Invalid ID handling
- Multiple user deletion
- Response time validation

### Performance & Load Testing
- Concurrent request handling
- Bulk operations performance
- Response time thresholds
- Load testing with Locust

### Security Testing
- Authentication bypass attempts
- XSS injection protection
- SQL injection protection
- Input validation security
- Access control testing
- Rate limiting validation
- Information disclosure prevention
- Mass assignment protection

## Test Scenarios

### Positive Test Cases
- Valid data operations
- Successful CRUD operations
- Proper response schemas
- Expected status codes

### Negative Test Cases
- Invalid data handling
- Missing required fields
- Non-existent resource access
- Invalid ID formats
- Empty payloads

### Edge Cases
- Very long strings (1000+ characters)
- Special characters and symbols
- Unicode characters (Chinese, emojis)
- Numeric strings
- Null and empty values

### Performance Tests
- Response time under 2 seconds
- Concurrent request handling (10 simultaneous)
- Bulk operations (5+ sequential)
- Average response time validation

## Performance Testing - Hybrid Approach

This project implements a comprehensive hybrid approach for performance testing, separating functional performance validation from concurrent load testing.

### Pytest Performance Tests (Functional Performance)

Pytest performance tests focus on functional performance validation with detailed assertions and CI/CD integration. These tests include automatic retry mechanisms with exponential backoff to handle rate limiting gracefully.

#### Running Performance Tests

```bash
# Run all performance tests
pytest tests/test_performance.py -v

# Run specific performance categories
pytest -m performance                    # All performance tests (12 tests)
pytest -m "performance and not slow"    # Quick performance tests only (7 tests)
pytest -m stress                        # Stress tests only (2 tests)

# Run performance tests with detailed output and timing information
pytest tests/test_performance.py -v -s

# Run performance tests in parallel for faster execution
pytest tests/test_performance.py -n auto
```

#### Pytest Performance Test Categories

**TestUserResponseTimes** - Individual operation performance validation:
- `test_create_user_response_time` - Validates user creation performance
- `test_get_users_list_response_time` - Tests list retrieval performance  
- `test_update_user_response_time` - Measures user update performance
- `test_delete_user_response_time` - Validates deletion performance

**TestUserLoadAndConcurrency** - Multi-threaded concurrent request testing:
- `test_concurrent_user_creation_performance` - Tests 5 concurrent user creation requests
- `test_bulk_user_operations_performance` - Sequential bulk operations with rate limiting protection

**TestUserWorkflowScenarios** - Complete user workflow performance testing:
- `test_typical_user_workflow` - Complete CRUD workflow with timing analysis
- `test_mixed_operation_patterns` - Realistic usage patterns (browse 50%, view 25%, create 15%, update 10%)
- `test_rapid_sequential_requests` - Rate limiting behavior testing
- `test_error_handling_under_load` - Error scenario performance validation

**TestUserMemoryAndResourceUsage** - Resource usage and payload performance:
- `test_large_payload_performance` - Tests performance with large data payloads
- `test_memory_usage_stability` - Validates memory usage across multiple operations

### Locust Load Tests (Concurrent Load Testing)

Locust provides true concurrent multi-user load testing with realistic user behavior simulation. The tests are designed to work within ReqRes API rate limits while providing meaningful load testing scenarios.

#### Installation and Setup

```bash
# Install Locust
pip install locust

# Verify installation
locust --version
```

#### Running Load Tests

**Interactive Web Interface:**
```bash
cd perf
locust -f locustfile.py --host=https://reqres.in
# Open http://localhost:8089 in your browser for real-time monitoring
```

**Headless Load Tests:**

```bash
# Conservative load test (recommended for learning/development)
# 3 users, 0.5 users/second spawn rate, 60 seconds duration
locust -f locustfile.py BasicLoadUser --host=https://reqres.in --users=3 --spawn-rate=0.5 --run-time=60s --headless

# Moderate load test (realistic testing scenario)
# 5 users, 1 user/second spawn rate, 60 seconds duration  
locust -f locustfile.py BasicLoadUser --host=https://reqres.in --users=5 --spawn-rate=1 --run-time=60s --headless

# Stress test (expect some rate limiting - 429 errors)
# 10 users, 2 users/second spawn rate, 60 seconds duration
locust -f locustfile.py --host=https://reqres.in --users=10 --spawn-rate=2 --run-time=60s --headless

# Realistic usage simulation with mixed user behaviors
locust -f locustfile.py RealisticUsageUser --host=https://reqres.in --users=5 --spawn-rate=1 --run-time=120s --headless
```

#### Locust User Classes

**BasicLoadUser** - Standard concurrent load testing:
- Balanced mix of operations (GET 5x, POST 2x, PUT 1x, DELETE 1x)
- 1-3 second wait times between requests
- Suitable for general load testing scenarios

**HighConcurrencyUser** - High-load stress testing:
- Focused on rapid GET and POST operations
- 1-3 second wait times (increased from 0.5-2s to reduce rate limiting)
- Designed to test system limits and capacity

**RealisticUsageUser** - Real-world usage patterns:
- Weighted operations matching realistic usage (browse 10x, view 5x, create 2x, update 1x)
- 2-8 second wait times simulating real user thinking time
- Includes realistic job titles and user behavior patterns

## Test Data

Test data is managed through JSON fixtures in `resources/data/test_users.json`:

- **valid_users**: Standard valid user data
- **update_users**: Data for update operations
- **invalid_users**: Invalid data for negative testing
- **edge_case_users**: Special characters, unicode, long strings
- **performance_users**: Data optimized for performance testing

## Test Markers

Tests are organized with pytest markers for easy filtering:

- `@pytest.mark.smoke`: Basic availability checks
- `@pytest.mark.regression`: Regression tests
- `@pytest.mark.crud`: CRUD operation tests
- `@pytest.mark.post`: POST call tests
- `@pytest.mark.get`: GET operation tests
- `@pytest.mark.put`: PUT operation tests
- `@pytest.mark.delete`: DELETE operation tests
- `@pytest.mark.negative`: Negative test cases
- `@pytest.mark.data_validation`: Data validation tests
- `@pytest.mark.performance`: Performance and load tests
- `@pytest.mark.security`: Security and penetration tests
- `@pytest.mark.slow`: Slow-running tests

## Reports

### Generate HTML Report
```bash
pytest --html=reports/report.html --self-contained-html
```

### Generate JUnit XML Report
```bash
pytest --junitxml=reports/junit.xml
```

### Coverage Report
```bash
pytest --cov=tests --cov-report=html --cov-report=term
```

Reports generated:
* HTML test report at `reports/report.html`
* JUnit XML at `reports/junit.xml` for CI integration
* Terminal: summary with missing lines
* XML: `reports/coverage.xml` for CI and tools
* HTML: `reports/htmlcov/index.html` for detailed browser view

## 🔍 Test Examples

### Running Specific Test Files
```bash
# Run only CRUD tests
pytest tests/test_users_crud.py

# Run only smoke tests
pytest tests/test_users_smoke.py

# Run authentication tests
pytest tests/test_auth_login.py
```

### Running Tests with Verbose Output
```bash
pytest -v -s tests/test_users_crud.py::TestUserCreation::test_create_user_with_valid_data
```

### Running Tests with Custom Markers
```bash
# Run all validation tests
pytest -m validation -v

# Run performance tests excluding slow ones
pytest -m "performance and not slow"

# Run negative tests for POST operations only
pytest -m negative -k "create" -v

# Run security tests
pytest -m security -v

# Run security tests excluding slow ones
pytest -m "security and not slow"
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures and configuration
├── test_users_crud.py          # Comprehensive CRUD tests
├── test_users_smoke.py         # Basic smoke tests
├── test_users_security.py      # Security and penetration tests
├── test_auth_login.py          # Authentication tests
├── test_performance.py         # Performance and load tests
├── security_config.py          # Security testing configuration
├── helpers/
│   ├── __init__.py
│   └── validate.py             # Validation helpers
├── schemas/
│   └── json_schemas.py         # JSON schema definitions
# ISTQB test techniques are integrated into the main test files:
# - Domain testing: tests/test_users_crud.py (TestUserValidation class)
# - Combinatorial testing: tests/test_users_crud.py (TestCombinatorialPairs class)  
# - State transition testing: tests/test_users_crud.py (TestStateTransitions class)

resources/
└── data/
    └── test_users.json         # Test data fixtures

perf/
└── locustfile.py              # Performance testing scenarios

reports/                       # Generated test reports
├── junit.xml                 # JUnit XML report
├── report.html               # HTML test report
└── [category]-report.html    # Category-specific reports

.github/workflows/             # CI/CD configuration
└── api-tests.yml             # GitHub Actions workflow
```

## Endpoints Covered

This suite exercises the core HTTP methods, with JSON Schema validation applied in every case:

- **GET**  
  - List users and fetch single user  
  - Assertions: 200 status, basic schema shape, key fields present  
  - See: `tests/test_users_smoke.py`

- **POST**  
  - Create user happy path  
  - Assertions: 201 or 200 status (demo API), `id`, `createdAt`, echo of submitted fields  
  - See: `tests/test_users_crud.py`

- **PUT**  
  - Full update of an existing user  
  - Assertions: 200 status, updated fields, `updatedAt` present  
  - See: `tests/test_users_crud.py`

- **DELETE**  
  - Delete user  
  - Assertions: 204 status  
  - See: `tests/test_users_crud.py`

## Schema Validation

All response payloads are validated against **JSON Schemas** using the `jsonschema` library.  

- Schemas live in `tests/schemas/json_schemas.py`  
- A shared helper (`tests/helpers/validate.py`) wraps `jsonschema.validate`  
- Integrated directly into each test file (smoke, endpoints, negative, auth, misc)  
- Validations cover:
  - Required fields and correct types
  - Formats (`email`, `uri`, `date-time`)
  - No unexpected properties (`additionalProperties: false`)

This ensures **data validation is built into every functional and negative test**, not just separate schema-only files.

## Continuous Integration

Example GitHub Actions workflow:

```yaml
name: API Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run smoke tests
        run: pytest -m smoke
      - name: Run full test suite
        run: pytest -m "not slow"
      - name: Run performance tests
        run: pytest -m performance
```

GitHub Actions runs tests on push and pull request, collecting JUnit, HTML, and coverage reports and uploading them as artifacts.

## Success Criteria

All tests validate:
- Correct HTTP status codes
- Response schema compliance
- Data integrity
- Response times under thresholds
- Error handling
- Edge case behavior
- Performance under load

## Notes about the API

This suite runs against the public demo API at [https://reqres.in/](https://reqres.in/).
Because it is a sample service, some negative calls can return 200 with demo payloads.
Assertions check both status codes and response shapes where appropriate.
