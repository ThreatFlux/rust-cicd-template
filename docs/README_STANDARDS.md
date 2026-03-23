# ThreatFlux README Standards

Best practices for README files in ThreatFlux repositories.

## Required Sections

Every README must include:

1. Title and badges
2. Description
3. Features
4. Installation
5. Quick start
6. License

## Badge Order

```markdown
[![Crates.io](https://img.shields.io/crates/v/PROJECT.svg)](https://crates.io/crates/PROJECT)
[![Documentation](https://docs.rs/PROJECT/badge.svg)](https://docs.rs/PROJECT)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Rust](https://img.shields.io/badge/rust-1.94%2B-orange.svg)](https://www.rust-lang.org)
[![CI](https://github.com/ThreatFlux/PROJECT/actions/workflows/ci.yml/badge.svg)](https://github.com/ThreatFlux/PROJECT/actions/workflows/ci.yml)
[![Security](https://github.com/ThreatFlux/PROJECT/actions/workflows/security.yml/badge.svg)](https://github.com/ThreatFlux/PROJECT/actions/workflows/security.yml)
```

## Anti-Patterns to Avoid

1. No runnable code examples
2. Missing license
3. No CI badge
4. Outdated Rust version
5. Missing installation section
6. Shipping unresolved template placeholders

## Template Files

- `README_TEMPLATE.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `LICENSE`
- `docs/TEMPLATE_BOOTSTRAP_CHECKLIST.md`
