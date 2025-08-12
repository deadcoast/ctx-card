# CTX-CARD Generator Test Suite

This directory contains a comprehensive test suite for the CTX-CARD generator, ensuring code quality, functionality, and reliability.

## Test Structure

```text
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── README.md                   # This file
├── unit/                       # Unit tests
│   ├── test_scanner.py         # Repository scanner tests
│   ├── test_call_resolver.py   # Call resolution tests
│   ├── test_card_renderer.py   # CTX-CARD rendering tests
│   └── test_utils.py           # Utility function tests
├── integration/                # Integration tests
│   └── test_full_generation.py # End-to-end generation tests
├── cli/                        # CLI tests
│   └── test_cli.py             # Command-line interface tests
└── test_ast_analyzer.py        # AST analyzer tests
```

## Test Categories

### Unit Tests (`tests/unit/`)

- **test_scanner.py**: Tests for repository scanning and file discovery
- **test_call_resolver.py**: Tests for cross-module function call resolution
- **test_card_renderer.py**: Tests for CTX-CARD format generation
- **test_utils.py**: Tests for utility functions and validation

### Integration Tests (`tests/integration/`)

- **test_full_generation.py**: End-to-end tests for complete CTX-CARD generation
- Tests real project analysis and output generation
- Validates complete workflows and feature combinations

### CLI Tests (`tests/cli/`)

- **test_cli.py**: Tests for command-line interface functionality
- Tests all CLI options and argument combinations
- Validates CLI error handling and output

### AST Analyzer Tests

- **test_ast_analyzer.py**: Tests for the main AST analysis coordination
- Tests two-pass analysis workflow
- Validates analysis statistics and error handling

## Test Markers

Tests are categorized using pytest markers:

- `@pytest.mark.unit`: Unit tests for individual components
- `@pytest.mark.integration`: Integration tests for complete workflows
- `@pytest.mark.cli`: CLI interface tests
- `@pytest.mark.slow`: Tests that take longer to run
- `@pytest.mark.ast`: AST analysis specific tests
- `@pytest.mark.format`: CTX-CARD format validation tests
- `@pytest.mark.performance`: Performance and scalability tests

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src/ctxcard_gen --cov-report=term-missing
```

### Selective Test Execution

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only CLI tests
pytest -m cli

# Run fast tests (skip slow ones)
pytest -m "not slow"

# Run specific test file
pytest tests/unit/test_scanner.py

# Run specific test function
pytest tests/unit/test_scanner.py::TestRepoScanner::test_is_code_file
```

### Using the Test Runner Script

```bash
# Run all checks (tests, format, lint)
python run_tests.py --all

# Run only tests with coverage
python run_tests.py --coverage

# Run only unit tests
python run_tests.py --unit

# Run fast tests only
python run_tests.py --fast

# Run with verbose output
python run_tests.py --verbose
```

## Test Fixtures

### Sample Project Directory (`sample_project_dir`)

Creates a realistic Python project structure for testing:

- Multiple packages with `__init__.py` files
- Service classes with methods and properties
- Data models with `@dataclass` and `pydantic.BaseModel`
- API routes with FastAPI decorators
- Utility functions and error classes
- Files with linting violations for PX testing

### Sample Modules (`sample_modules`)

Provides pre-built module information for testing:

- ModuleInfo objects with symbols, imports, and metadata
- DTOs, errors, routes, and linting violations
- Realistic data structures for renderer testing

### Sample CTX-CARD Content (`sample_ctxcard_content`)

Provides sample CTX-CARD output for testing:

- Complete CTX-CARD format with all required sections
- Realistic data for delta generation testing
- Format validation test cases

## Test Coverage

The test suite aims for **90% code coverage** and covers:

### Core Functionality

- ✅ Repository scanning and file discovery
- ✅ AST parsing and symbol extraction
- ✅ Cross-module call resolution
- ✅ CTX-CARD format generation
- ✅ CLI interface and argument parsing
- ✅ Error handling and validation

### Advanced Features

- ✅ DTO detection (`@dataclass`, `pydantic.BaseModel`)
- ✅ Error taxonomy and custom exceptions
- ✅ API route detection (FastAPI/Flask)
- ✅ Linting rules (PX tags)
- ✅ Property and descriptor detection
- ✅ Raise analysis (`!raises[...]`)
- ✅ Re-export handling
- ✅ Delta generation
- ✅ Per-package CTX-CARD generation
- ✅ Type signature emission

### Edge Cases

- ✅ Invalid Python files
- ✅ Missing files and directories
- ✅ Non-ASCII characters
- ✅ Prefix-free alias validation
- ✅ Large project performance
- ✅ Error conditions and exceptions

## Test Data

### Sample Project Structure

```text
sample_project/
├── main_pkg/
│   ├── __init__.py          # Re-exports
│   ├── service.py           # AuthService with methods
│   ├── models.py            # DTOs and errors
│   └── repository.py        # UserRepository
├── api/
│   ├── __init__.py
│   └── routes.py            # FastAPI routes
├── utils/
│   ├── __init__.py          # Re-exports
│   └── helpers.py           # Utility functions
├── tests/
│   └── test_service.py      # Test files (excluded)
└── bad_code.py              # Linting violations
```

### Test Scenarios

- **Basic Generation**: Simple CTX-CARD generation from a project
- **Type Signatures**: Generation with `--emit-ty` option
- **Include/Exclude**: File filtering with glob patterns
- **Delta Generation**: Computing differences from existing CTX-CARD
- **Per-package**: Separate CTX-CARD files for each package
- **Statistics**: Analysis statistics output
- **Error Handling**: Invalid paths, files, and configurations
- **Performance**: Large project analysis timing
- **Format Validation**: CTX-CARD format compliance

## Continuous Integration

The test suite is designed to run in CI/CD environments:

### GitHub Actions

```yaml
- name: Run tests
  run: |
    python -m pytest --cov=src/ctxcard_gen --cov-report=xml
    python run_tests.py --all
```

### Coverage Requirements

- Minimum 90% code coverage
- Coverage reports in XML format for CI integration
- Coverage exclusion for test files and generated code

### Quality Gates

- All tests must pass
- Code formatting (Black) must be correct
- Import sorting (isort) must be correct
- Linting (flake8) must pass
- Type checking (mypy) must pass

## Debugging Tests

### Verbose Output

```bash
pytest -v -s --tb=long
```

### Debug Specific Test

```bash
pytest tests/unit/test_scanner.py::TestRepoScanner::test_symbol_extraction -v -s
```

### Generate Coverage Report

```bash
pytest --cov=src/ctxcard_gen --cov-report=html
# Open htmlcov/index.html in browser
```

### Test Isolation

```bash
# Run tests in isolation
pytest --dist=no

# Run with random seed for flaky test detection
pytest --randomly-seed=42
```

## Adding New Tests

### Test Naming Convention

- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<description>`

### Test Template

```python
def test_feature_description(self, fixture_name):
    """Test description of what is being tested."""
    # Arrange
    # Act
    # Assert
```

### Adding Fixtures

Add new fixtures to `conftest.py`:

```python
@pytest.fixture
def new_fixture():
    """Description of the fixture."""
    # Setup
    yield value
    # Cleanup (if needed)
```

### Test Variants

Use appropriate markers:

```python
@pytest.mark.unit
def test_unit_functionality():
    pass

@pytest.mark.integration
def test_integration_workflow():
    pass

@pytest.mark.slow
def test_performance():
    pass
```

## Performance Testing

### Large Project Tests

- Creates projects with 10+ modules
- Tests analysis performance (should complete in <5s)
- Validates memory usage and scalability

### Benchmark Tests

- Measures AST parsing speed
- Tests call resolution performance
- Validates rendering efficiency

## Security Testing

### Input Validation

- Tests file path sanitization
- Validates glob pattern handling
- Tests error message security

### File System Safety

- Tests with invalid file paths
- Validates binary file handling
- Tests permission error handling

## Maintenance

### Regular Tasks

- Update test data for new features
- Review and update coverage requirements
- Maintain test performance benchmarks
- Update CI/CD pipeline configurations

### Test Data Updates

When adding new features:

1. Update `sample_project_dir` fixture if needed
2. Add new test scenarios to integration tests
3. Update CLI tests for new options
4. Add unit tests for new components
5. Update coverage expectations

This comprehensive test suite ensures the CTX-CARD generator is reliable, performant, and maintainable.
