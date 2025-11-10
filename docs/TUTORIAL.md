# Repeat-Runner v2 Quick Start Tutorial

This tutorial will guide you through setting up and using the new v2 features in Repeat-Runner.

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Basic knowledge of YAML syntax

## Step 1: Installation

First, install Repeat-Runner:

```bash
pip install repeat-runner
```

## Step 2: Create Your First Configuration with Environment Variables

Create a file named `runner.yaml` in your project directory:

```yaml
# Basic development setup with environment variables
devSetup:
  commands:
    - echo "Setting up for environment: $NODE_ENV"
    - echo "Database: $DATABASE_URL"
    - npm install
  env:
    NODE_ENV: development
    DATABASE_URL: "postgresql://localhost/myapp_dev"

# Test execution with test-specific environment
runTests:
  commands:
    - echo "Running tests in $NODE_ENV mode"
    - npm run test
  env:
    NODE_ENV: test
    TEST_DATABASE: "sqlite://test.db"
```

## Step 3: Run Your First Macro

Try running the `devSetup` macro:

```bash
runner run devSetup
```

You should see the environment variables being used in the commands.

## Step 4: Add Macro Chaining

Update your `runner.yaml` to include a workflow that chains multiple macros:

```yaml
# Basic development setup with environment variables
devSetup:
  commands:
    - echo "Setting up for environment: $NODE_ENV"
    - echo "Database: $DATABASE_URL"
    - npm install
  env:
    NODE_ENV: development
    DATABASE_URL: "postgresql://localhost/myapp_dev"

# Test execution with test-specific environment
runTests:
  commands:
    - echo "Running tests in $NODE_ENV mode"
    - npm run test
  env:
    NODE_ENV: test
    TEST_DATABASE: "sqlite://test.db"

# Build process
buildProject:
  commands:
    - echo "Building for environment: $NODE_ENV"
    - npm run build
  env:
    NODE_ENV: production

# Full workflow that chains the above macros
fullWorkflow:
  commands:
    - call: devSetup
    - call: runTests
    - call: buildProject
```

## Step 5: Run the Chained Workflow

Run the full workflow:

```bash
runner run fullWorkflow
```

You'll see that it executes all three macros in sequence, each with their own environment variables.

## Step 6: Enable Logging

Run the same workflow with logging to see all command executions:

```bash
runner run fullWorkflow --log-file workflow.log
```

Check the `workflow.log` file to see the detailed execution log.

## Step 7: Try Different Combinations

Try different combinations of the new features:

```bash
# Verbose output with logging
runner run fullWorkflow --verbose --log-file verbose_workflow.log

# Dry run to see what would be executed
runner run fullWorkflow --dry-run

# Continue on error (useful for workflows where some steps might fail)
runner run fullWorkflow --continue --log-file workflow.log
```

## Step 8: Advanced Example

Here's a more complex example that combines all features:

```yaml
# Database setup with environment variables
dbSetup:
  commands:
    - echo "Setting up database: $DATABASE_NAME"
    - echo "Environment: $NODE_ENV"
    - createdb $DATABASE_NAME
  env:
    DATABASE_NAME: "myapp_dev"
    NODE_ENV: development

# Frontend build
frontendBuild:
  commands:
    - echo "Building frontend for: $BUILD_TARGET"
    - npm run build
  env:
    BUILD_TARGET: "production"

# Backend build
backendBuild:
  commands:
    - echo "Building backend for: $NODE_ENV"
    - npm run build
  env:
    NODE_ENV: production

# Deployment workflow with environment-specific variables
deploy:
  commands:
    - echo "Starting deployment to $DEPLOY_ENV"
    - call: dbSetup
    - call: frontendBuild
    - call: backendBuild
    - echo "Deploying to: $DEPLOY_TARGET"
  env:
    DEPLOY_ENV: production
    DEPLOY_TARGET: "aws-ec2-prod"
```

## Troubleshooting Tips

1. **Environment variables not expanding**: Make sure you're using the correct syntax (`$VARIABLE_NAME` or `${VARIABLE_NAME}`)

2. **Circular macro calls**: If you get a "Circular macro call detected" error, check your macro chaining for loops

3. **Log file permissions**: If logging fails, check that you have write permissions to the log file location

4. **Invalid YAML syntax**: Use a YAML validator if you encounter parsing errors

## Next Steps

- Review the [V2 Features Guide](docs/V2_FEATURES.md) for detailed information
- Check the [CLI Reference](docs/CLI_REFERENCE.md) for all available options
- Look at the [runner.yaml.example](runner.yaml.example) file for more examples