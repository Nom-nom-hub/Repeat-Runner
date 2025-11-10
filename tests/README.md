# Repeat-Runner v2 Tests

This directory contains comprehensive tests for the v2 features of Repeat-Runner:

## Test Structure

### Unit Tests (in `unit/` directory)
- `test_macros.py` - Tests for the macros module (loading and validation)
- `test_executor.py` - Tests for the executor module (macro execution)
- `test_logger.py` - Tests for the logger module (logging functionality)
- `test_runner.py` - Tests for the runner module (CLI interface)

### Feature-Specific Tests
- `test_env_vars.py` - Tests for per-macro environment variable support
- `test_macro_chaining.py` - Tests for macro chaining functionality
- `test_logging.py` - Tests for command execution logging to file
- `test_error_handling.py` - Tests for improved error handling
- `test_edge_cases.py` - Tests for edge cases like invalid environment variables
- `test_circular_calls.py` - Tests for circular macro call detection
- `test_file_permissions.py` - Tests for file permission issues in logging

### Integration Tests
- `test_integration.py` - Tests for complete workflow integration

## Test Coverage

The tests cover:

1. **Per-macro environment variable support**:
   - Environment variables are properly set and passed to commands
   - Environment variables are isolated between macros
   - Environment variable validation and error handling
   - Complex environment variable values (special characters, unicode, etc.)

2. **Macro chaining functionality**:
   - One macro calling another macro
   - Nested macro calls
   - Error handling for missing macros
   - Circular reference detection
   - Environment variable inheritance in chained macros

3. **Command execution logging to file**:
   - Proper log format with timestamps
   - Logging of command execution, output, and errors
   - File creation and directory creation
   - Appending to existing log files

4. **Improved error handling**:
   - Descriptive error messages for various error conditions
   - Proper error propagation and handling
   - Validation error messages
   - Command execution error handling

5. **Edge cases**:
   - Invalid environment variables
   - Circular macro calls
   - File permission issues for logging
   - Special character handling
   - Large environment variables
   - Unicode and special character support

## Running Tests

To run all tests:
```bash
python -m pytest tests/ -v
```

Or using the test suite:
```bash
python tests/test_suite.py
```

To run specific test modules:
```bash
python -m pytest tests/unit/test_macros.py -v
```

## Test Categories

- **Positive tests**: Verify correct functionality
- **Negative tests**: Verify proper error handling
- **Edge case tests**: Verify behavior at boundaries
- **Integration tests**: Verify complete workflows
- **Error handling tests**: Verify descriptive error messages