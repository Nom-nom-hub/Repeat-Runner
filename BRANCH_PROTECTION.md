# Branch Protection Rules Setup

To ensure code quality and security, configure the following branch protection rules for the `main` branch in your GitHub repository:

## Required Status Checks

The following status checks must pass before merging:

- CI (all tests passing on all platforms and Python versions)
- Code Quality (linting and type checking)
- Security Scan (no critical vulnerabilities)
- Documentation Validation (docs are up-to-date)
- Build (package builds successfully)

## Other Protection Settings

- [x] Require pull request reviews before merging
  - Required number of reviewers: 1
  - Allow specified actors to bypass required reviews
  - Allow specified actors to bypass pull request reviews

- [x] Require status checks to pass before merging
  - Require branches to be up to date before merging
  - Include administrators: enabled (optional, depending on your policy)

- [x] Require conversation resolution before merging
  - All conversations must be resolved before merging

- [x] Restrict who can push to matching branches (optional)
  - Only allow specific teams/users to push to main

## Code Coverage Requirements

- Set up Codecov integration to track test coverage
- Maintain minimum coverage threshold (e.g., 80%)
- Require coverage not to drop below threshold

## Additional Recommendations

1. Set up required review settings to prevent self-approval of PRs
2. Consider requiring multiple reviewers for critical changes
3. Enable branch deletion after merge to keep repository clean
4. Consider using protected branch rules for develop branch as well

## Required Repository Secrets

Add these secrets to your repository settings:

- `PYPI_API_TOKEN`: API token for publishing to PyPI (for publish workflow)

To create a PyPI API token:

1. Go to your PyPI account settings
2. Create a new API token
3. Add it as a repository secret named `PYPI_API_TOKEN`
4. Use trusted publishing with OIDC for enhanced security (recommended)
