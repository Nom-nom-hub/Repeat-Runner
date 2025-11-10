# Repeat-Runner

**Run your repetitive dev workflows with a single command.**

Repeat-Runner is a lightweight CLI tool that allows developers to define, execute, and manage reusable task sequences (macros) in a simple YAML format. It is designed to minimize friction, accelerate common development workflows, and scale incrementally.

## Installation

### Using uv (recommended)

```bash
# Install uv if you don't have it
pip install uv

# Install repeat-runner with uv
uv pip install repeat-runner

# Or install in development mode
uv pip install -e .
```

### Using pip (traditional method)

```bash
pip install repeat-runner
```

### uv Benefits

Using uv provides faster dependency resolution and installation compared to pip. It's a modern Python package installer that offers significant performance improvements.

### Backward Compatibility

The project maintains full backward compatibility with pip. All installation methods work as before:

- `pip install repeat-runner` - Traditional installation
- `pip install -e .` - Development installation
- `pip install -e '.[dev]'` - Development with extra dependencies

### Development Setup

For development, you can install with development dependencies:

```bash
# With uv (recommended)
uv pip install -e '.[dev]'

# With pip (traditional)
pip install -e '.[dev]'
```

## Usage

1. Create a `runner.yaml` file in your project directory:

```yaml
devSetup:
  commands:
    - echo "Setting up development environment"
    - npm install
    - echo "Dev environment ready!"

buildProject:
  commands:
    - echo "Building project..."
    - npm run build
    - echo "Build completed!"
```

1.1. Run a macro:

```bash
# List available macros
runner list

# Run a specific macro
runner run devSetup

# Dry run - show commands without executing
runner run devSetup --dry-run

# Verbose output - show command output in real-time
runner run devSetup --verbose

# Continue on error - keep running even if a command fails
runner run devSetup --continue

# Log command execution to a file
runner run devSetup --log-file execution.log
```

## Features

- Define macros in simple YAML format
- Execute macros sequentially with a single command
- Dry run functionality to preview commands
- Verbose output for real-time feedback
- Continue on error option for resilient execution
- List all available macros
- **NEW in v2:** Per-macro environment variable support
- **NEW in v2:** Macro chaining (calling one macro from another)
- **NEW in v2:** Command execution logging to file

## Configuration

### Basic runner.yaml structure

```yaml
macroName:
  commands:
    - command1
    - command2
    - command3
```

Each macro can contain a list of shell commands that will be executed sequentially.

### Per-Macro Environment Variables

You can now define environment variables that are specific to each macro using the `env` property:

```yaml
devSetup:
  commands:
    - echo "Setting up development environment with NODE_ENV=$NODE_ENV"
    - echo "Database: $DATABASE_URL"
  env:
    NODE_ENV: development
    DATABASE_URL: "postgresql://localhost/myapp_dev"

buildProject:
  commands:
    - echo "Building project for environment: $NODE_ENV"
    - npm run build
  env:
    NODE_ENV: production
    BUILD_OUTPUT: "./dist"
```

Environment variables defined in one macro do not affect other macros, providing isolation between different workflow steps.

### Macro Chaining

Macros can call other macros using the `call` syntax within the commands list:

```yaml
devSetup:
  commands:
    - echo "Setting up development environment"
    - npm install

runTests:
  commands:
    - echo "Running tests"
    - npm test

buildProject:
  commands:
    - echo "Building project"
    - npm run build

fullWorkflow:
  commands:
    - call: devSetup
    - echo "Running additional setup steps..."
    - call: runTests
    - call: buildProject
```

In this example, the `fullWorkflow` macro will execute the `devSetup`, `runTests`, and `buildProject` macros in sequence. When chaining macros, each called macro will have access to its own environment variables if defined.

### Combining Environment Variables and Macro Chaining

You can combine both features to create complex workflows:

```yaml
devSetup:
  commands:
    - echo "Setting up development environment with NODE_ENV=$NODE_ENV"
    - npm install
  env:
    NODE_ENV: development

runTests:
  commands:
    - echo "Running tests in $NODE_ENV mode"
    - npm run test
  env:
    NODE_ENV: test

deploy:
  commands:
    - echo "Deploying with environment: $DEPLOY_ENV"
    - npm run deploy
  env:
    DEPLOY_ENV: production

fullWorkflow:
  commands:
    - call: devSetup
    - call: runTests
    - call: deploy
  env:
    DEPLOY_ENV: staging  # This will override the DEPLOY_ENV in the deploy macro
```

## Command Line Interface

### Options

- `--dry-run`: Print commands without execution
- `--verbose`: Show real-time command output
- `--continue`: Continue on command failure
- `--log-file`: Path to log file for command execution

### Examples

```bash
# Run macro with logging to file
runner run devSetup --log-file execution.log

# Run macro with verbose output and logging
runner run devSetup --verbose --log-file execution.log

# Run macro with continue on error and logging
runner run fullWorkflow --continue --log-file workflow.log
```

## Logging

Command execution can be logged to a file using the `--log-file` option. The log file will contain:

- Timestamps for each command execution
- The command that was executed
- Command output (if any)
- Command errors (if any)

Example log file content:

```text
--- Logging started at 2023-10-15 14:30:45 ---
[2023-10-15 14:30:45] EXECUTED: echo "Setting up development environment"
[2023-10-15 14:30:45] OUTPUT: Setting up development environment
[2023-10-15 14:30:46] EXECUTED: npm install
[2023-10-15 14:31:23] OUTPUT: added 123 packages in 37s
```

## Development

This tool is designed with extensibility in mind. Future versions may include:

- CI/CD integration
- AI-assisted macro suggestions
- More advanced error handling and reporting

## Documentation

For more detailed information about Repeat-Runner v2 features, see:

- [V2 Features Guide](docs/V2_FEATURES.md) - Comprehensive guide to all new v2 features
- [CLI Reference](docs/CLI_REFERENCE.md) - Complete command line interface reference
- [Quick Start Tutorial](docs/TUTORIAL.md) - Step-by-step tutorial for new users

## Contributing

Contributions are welcome! Please see the project roadmap for planned features.

### Development Setup

1. Fork and clone the repository
2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install in development mode:

   ```bash
   pip install -e .
   pip install -r requirements-dev.txt
   ```

### CI/CD Pipeline

This project uses GitHub Actions for continuous integration and deployment:

- **Automated Testing**: All tests run on pushes and pull requests
- **Code Quality**: Linting and type checking enforced
- **Security Scanning**: Regular vulnerability checks
- **Cross-Platform Testing**: Tests run on Linux, Windows, and macOS
- **Multiple Python Versions**: Tested on Python 3.11+
- **Coverage Tracking**: Code coverage reports generated
- **Package Building**: Automated package builds and validation
- **Documentation Validation**: Ensures docs stay up-to-date

See the [`.github/workflows`](.github/workflows/) directory for all workflow configurations.

## License

MIT License
