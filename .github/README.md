# CI/CD Configuration

This directory contains the GitHub Actions workflows that implement the CI/CD pipeline for Repeat-Runner.

## Workflows

### [CI](workflows/ci.yml)
- Runs on every push and pull request
- Tests the application on multiple Python versions (3.11, 3.12, 3.13) and operating systems (Ubuntu, Windows, macOS)
- Performs linting with flake8
- Runs security scans with bandit and safety
- Executes all 158 test cases
- Generates and uploads code coverage reports

### [Code Quality](workflows/code-quality.yml)
- Runs on every push and pull request
- Performs linting with flake8 and pylint
- Runs type checking with mypy
- Ensures code quality standards are maintained

### [Security](workflows/security.yml)
- Runs on every push and pull request, and weekly
- Performs security scanning with bandit and safety
- Uploads security reports as artifacts

### [Build](workflows/build.yml)
- Runs on every push and pull request
- Builds the Python package
- Tests package installation
- Uploads package distributions as artifacts

### [Publish](workflows/publish.yml)
- Runs on release publication
- Builds and publishes the package to PyPI
- Uses trusted publishing with OIDC

### [Documentation Validation](workflows/docs-validation.yml)
- Runs on every push and pull request
- Validates documentation files
- Checks for broken links
- Ensures documentation stays up-to-date

## Branch Protection Rules

The following branch protection rules should be configured for the `main` branch:

1. Require pull request reviews before merging
2. Require status checks to pass before merging (all CI workflows must pass)
3. Require branches to be up to date before merging
4. Require code coverage to remain above a threshold (e.g., 80%)
5. Restrict who can push to matching branches

## Secrets Management

The following secrets should be configured in the repository:

- `PYPI_API_TOKEN`: API token for publishing to PyPI (used in publish workflow)