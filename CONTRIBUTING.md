# Contributing to ThreatFlux Projects

Thank you for your interest in contributing! This document provides guidelines for contributing to ThreatFlux projects.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/PROJECT_NAME.git`
3. Create a branch: `git checkout -b feat/your-feature`
4. Make your changes
5. Run checks: `make ci`
6. Push and create a Pull Request

## Development Setup

```bash
# Install development tools
make dev-setup

# Install git hooks
make install-hooks

# Run all checks
make ci
```

## Commit Guidelines

We use [Conventional Commits](https://www.conventionalcommits.org/):

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Code style (formatting, etc.) |
| `refactor` | Code refactoring |
| `perf` | Performance improvement |
| `test` | Adding/updating tests |
| `chore` | Maintenance tasks |

### Examples

```
feat: add support for custom patterns
fix: resolve memory leak in parser
docs: update installation instructions
refactor: simplify error handling
```

### Breaking Changes

For breaking changes, add `BREAKING CHANGE:` in the commit body:

```
feat: change API response format

BREAKING CHANGE: Response now returns objects instead of arrays
```

## Pull Request Process

1. **Title**: Use conventional commit format
2. **Description**: Explain what and why
3. **Tests**: Add tests for new functionality
4. **Documentation**: Update relevant docs
5. **Changelog**: Breaking changes should be noted

### PR Checklist

- [ ] Code follows project style (`make fmt`)
- [ ] All tests pass (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] Documentation updated if needed
- [ ] Commit messages follow conventions

## Code Style

### Rust

- Follow [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- Use `rustfmt` for formatting
- Pass `clippy` with pedantic lints
- Document public APIs

### Clippy Configuration

We use strict clippy settings:

```bash
cargo clippy -- -D warnings -D clippy::pedantic -D clippy::nursery
```

## Testing

```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run specific test
cargo test test_name
```

### Test Guidelines

- Test public API functionality
- Include edge cases
- Use descriptive test names
- Keep tests focused and independent

## Documentation

- Document all public items
- Include examples in doc comments
- Update README for significant changes
- Add doc tests where appropriate

```rust
/// Brief description.
///
/// More detailed explanation if needed.
///
/// # Examples
///
/// ```
/// use crate::function;
/// let result = function();
/// assert!(result.is_ok());
/// ```
pub fn function() -> Result<()> {
    // ...
}
```

## Reporting Issues

### Bug Reports

Include:
- Rust version (`rustc --version`)
- OS and version
- Steps to reproduce
- Expected vs actual behavior
- Error messages if any

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternatives considered

## Security Issues

**Do not open public issues for security vulnerabilities.**

See [SECURITY.md](SECURITY.md) for reporting instructions.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

- Open a [Discussion](https://github.com/threatflux/PROJECT_NAME/discussions)
- Check existing [Issues](https://github.com/threatflux/PROJECT_NAME/issues)

Thank you for contributing!
