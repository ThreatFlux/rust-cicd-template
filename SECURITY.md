# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

### How to Report

1. **Email**: Send details to security@threatflux.com
2. **GitHub Security Advisories**: Use the [Security tab](https://github.com/threatflux/PROJECT_NAME/security/advisories) to report privately

### What to Include

- Type of vulnerability
- Full paths of affected source files
- Location of affected code (tag/branch/commit or direct URL)
- Step-by-step reproduction instructions
- Proof-of-concept or exploit code (if possible)
- Impact assessment

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 5 business days
- **Resolution Target**: Within 90 days (complexity dependent)

### What to Expect

1. Acknowledgment of your report
2. Assessment of the vulnerability
3. Development of a fix
4. Coordinated disclosure

### Safe Harbor

We consider security research conducted in good faith to be authorized. We will not pursue legal action against researchers who:

- Make good faith efforts to avoid privacy violations
- Avoid data destruction or service disruption
- Report vulnerabilities promptly
- Allow reasonable time for remediation before disclosure

## Security Measures

### Dependencies

- Regular dependency audits with `cargo audit`
- Automated updates via Dependabot
- License compliance with `cargo deny`

### Code Quality

- Static analysis with Clippy (pedantic + nursery)
- Comprehensive test coverage
- Code review required for all changes

### CI/CD Security

- Pinned GitHub Action versions (SHA)
- Secret scanning enabled
- SBOM generation for releases
- Container image signing

## Security Features

If this project has security-relevant features, document them here.

## Acknowledgments

We thank the following security researchers for responsibly disclosing vulnerabilities:

*None yet - be the first!*
