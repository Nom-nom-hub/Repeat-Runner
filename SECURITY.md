# Security Policy

## Supported Versions

The following versions of Repeat-Runner are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in Repeat-Runner, please follow these steps:

1. **Do not open a public issue** - this could expose the vulnerability to others
2. Contact the maintainers directly via security report through GitHub
3. Include the following information in your report:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested remediation (if any)

## Security Practices

### Our Commitment
- We take security seriously and respond promptly to reported vulnerabilities
- We follow security best practices in our development process
- We use automated security scanning in our CI/CD pipeline

### Automated Security Scanning
Our CI/CD pipeline includes:
- Static code analysis with Bandit
- Dependency vulnerability scanning with Safety
- Regular security checks on a weekly schedule

### Dependency Management
- We keep dependencies up-to-date
- We monitor for known vulnerabilities in our dependencies
- We use tools like Safety to check for vulnerabilities

## Security Measures

### Code Review Process
- All code changes require review before merging
- Security-relevant changes receive additional scrutiny
- Branch protection rules enforce status checks

### Testing
- Comprehensive test suite covering all functionality
- Security-relevant test cases included
- Automated testing on multiple platforms and Python versions

## Security in Releases

- Security fixes are released as quickly as possible
- Security advisories are published when appropriate
- Users are encouraged to keep their installations up-to-date

## Contact

For security concerns, please use GitHub's security reporting feature or contact the maintainers directly.