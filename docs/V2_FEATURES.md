# Repeat-Runner v2 Features Documentation

This document provides detailed information about the new features introduced in Repeat-Runner v2.

## Table of Contents
1. [Per-Macro Environment Variables](#per-macro-environment-variables)
2. [Macro Chaining](#macro-chaining)
3. [Command Execution Logging](#command-execution-logging)
4. [Advanced Usage Examples](#advanced-usage-examples)

## Per-Macro Environment Variables

### Overview
In v2, you can now define environment variables that are specific to each macro. This allows you to create isolated execution contexts for different workflows without affecting other macros.

### Syntax
```yaml
macroName:
  commands:
    - command1
    - command2
  env:
    VARIABLE_NAME: "value"
    ANOTHER_VAR: "another_value"
```

### Example
```yaml
devSetup:
  commands:
    - echo "Setting up for environment: $NODE_ENV"
    - echo "Database: $DATABASE_URL"
    - npm install
  env:
    NODE_ENV: development
    DATABASE_URL: "postgresql://localhost/myapp_dev"
```

### Key Features
- Environment variables are isolated between macros
- Variables are only available during the execution of that specific macro
- Variables can reference other variables defined in the same macro
- Environment variables are passed to subprocesses when executing commands

### Variable Expansion
Environment variables defined in a macro are expanded in commands using standard shell syntax (`$VARIABLE_NAME` or `${VARIABLE_NAME}`).

## Macro Chaining

### Overview
Macro chaining allows one macro to call another macro, enabling you to create complex workflows by combining simpler, reusable components.

### Syntax
```yaml
macroName:
  commands:
    - call: anotherMacroName
    - echo "Additional command"
    - call: thirdMacro
```

### Example
```yaml
setup:
  commands:
    - echo "Setting up environment"
    - npm install

test:
  commands:
    - echo "Running tests"
    - npm test

build:
  commands:
    - echo "Building project"
    - npm run build

fullWorkflow:
  commands:
    - call: setup
    - call: test
    - call: build
```

### Key Features
- Macros can call other macros using the `call` syntax
- Circular macro calls are detected and prevented
- Each called macro executes in its own context
- Error handling propagates up from called macros
- Environment variables from the calling macro are inherited by called macros (but can be overridden)

### Circular Call Detection
Repeat-Runner v2 includes protection against infinite loops by detecting circular macro calls. If a macro calls itself directly or indirectly through a chain of other macros, an error will be raised.

## Command Execution Logging

### Overview
You can now log all command executions to a file using the `--log-file` command line option. This provides detailed records of workflow execution for debugging and auditing purposes.

### Usage
```bash
# Log to a specific file
runner run myMacro --log-file execution.log

# Combine with other options
runner run myMacro --verbose --log-file execution.log
runner run myMacro --continue --log-file workflow.log
```

### Log Format
The log file contains entries in the following format:
```
--- Logging started at YYYY-MM-DD HH:MM:SS ---

[YYYY-MM-DD HH:MM:SS] EXECUTED: command text
[YYYY-MM-DD HH:MM:SS] OUTPUT: command output (if any)
[YYYY-MM-DD HH:MM:SS] ERROR: error message (if any)
```

### Key Features
- Automatic timestamping of all events
- Separate tracking of commands, output, and errors
- Automatic directory creation for log files
- Appending to existing log files
- Concurrent console output and file logging

## Advanced Usage Examples

### Complex Workflow with Environment Variables and Chaining
```yaml
# Database setup with environment-specific variables
dbSetup:
  commands:
    - echo "Setting up database for $ENVIRONMENT"
    - echo "Connecting to: $DATABASE_URL"
    - createdb $DATABASE_NAME
  env:
    DATABASE_NAME: "myapp_dev"
    DATABASE_URL: "postgresql://localhost/myapp_dev"

# Frontend build with environment-specific configuration
frontendBuild:
  commands:
    - echo "Building frontend for $NODE_ENV"
    - echo "API endpoint: $API_ENDPOINT"
    - npm run build
  env:
    NODE_ENV: production
    API_ENDPOINT: "https://api.myapp.com"

# Backend build with environment-specific configuration
backendBuild:
  commands:
    - echo "Building backend for $BUILD_ENV"
    - echo "Port: $PORT"
    - npm run build
  env:
    BUILD_ENV: production
    PORT: "3000"

# Complete deployment workflow
deploy:
  commands:
    - echo "Starting deployment to $DEPLOY_ENV"
    - call: dbSetup
    - call: frontendBuild
    - call: backendBuild
    - echo "Deploying to: $DEPLOY_TARGET"
    - echo "Deployment completed in $DEPLOY_ENV"
  env:
    DEPLOY_ENV: production
    DEPLOY_TARGET: "aws-ec2-prod"
```

### Testing Workflow with Different Environments
```yaml
# Unit tests with test-specific environment
unitTests:
  commands:
    - echo "Running unit tests in $NODE_ENV"
    - npm run test:unit
  env:
    NODE_ENV: test
    TEST_SUITE: unit

# Integration tests with different environment
integrationTests:
  commands:
    - echo "Running integration tests in $NODE_ENV"
    - npm run test:integration
  env:
    NODE_ENV: test
    TEST_SUITE: integration
    TEST_DATABASE: "sqlite://test.db"

# Complete test suite
allTests:
  commands:
    - call: unitTests
    - call: integrationTests
    - echo "All tests completed in $NODE_ENV"
  env:
    NODE_ENV: test
```

### CI/CD Workflow Example
```yaml
# Linting with environment-specific configuration
lint:
  commands:
    - echo "Linting code in $CI_ENVIRONMENT"
    - npm run lint
  env:
    CI_ENVIRONMENT: github-actions

# Security checks
securityCheck:
  commands:
    - echo "Running security checks in $SECURITY_ENV"
    - npm run security:audit
  env:
    SECURITY_ENV: ci

# Build process
build:
  commands:
    - echo "Building for $BUILD_TYPE in $CI_ENVIRONMENT"
    - npm run build
  env:
    BUILD_TYPE: production
    CI_ENVIRONMENT: github-actions

# CI workflow combining all steps
ciWorkflow:
  commands:
    - call: lint
    - call: securityCheck
    - call: build
    - echo "CI workflow completed successfully in $CI_ENVIRONMENT"
  env:
    CI_ENVIRONMENT: github-actions
    NODE_ENV: production
```

## Best Practices

### Environment Variables
- Use descriptive variable names
- Store sensitive information in environment variables rather than hardcoding
- Keep environment variable values as strings
- Use environment variables for configuration that changes between environments

### Macro Chaining
- Create small, focused macros that do one thing well
- Use macro chaining to build complex workflows from simple components
- Avoid deep nesting of macro calls (keep the call chain reasonable)
- Document the expected behavior of chained macros

### Logging
- Use logging for production workflows or complex debugging
- Choose meaningful log file names
- Regularly clean up old log files
- Combine logging with other options like `--verbose` for maximum information

## Migration from v1

If you're upgrading from v1, your existing `runner.yaml` files will continue to work without changes. The new features are additive and don't break existing functionality. To take advantage of the new features, simply add the `env` section to your macros or use the `call` syntax to chain macros.