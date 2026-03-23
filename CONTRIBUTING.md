# Contributing to ThreatFlux Projects

This repository is the canonical Rust CI/CD template used across ThreatFlux projects. Changes here should improve the reusable template surface rather than one downstream application.

## Getting Started

1. Fork the repository
2. Clone your fork of this repository
3. Create a branch: `git checkout -b feat/your-change`
4. Make your changes
5. Run checks: `make ci`
6. Open a Pull Request

## Development Setup

```bash
make dev-setup
make install-hooks
make ci
```

## Commit Guidelines

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat`: new feature
- `fix`: bug fix
- `docs`: documentation only
- `refactor`: code refactoring
- `test`: adding or updating tests
- `chore`: maintenance

## Pull Request Process

- Use a conventional-commit title
- Explain what changed and why
- Add tests or validation where applicable
- Update template bootstrap docs when setup requirements change

### PR Checklist

- [ ] Code follows project style (`make fmt`)
- [ ] All tests pass (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] Bootstrap docs updated if needed
- [ ] Commit messages follow conventions

## Documentation

- Keep [README.md](README.md) accurate for the template repo
- Keep [README_TEMPLATE.md](README_TEMPLATE.md) accurate for generated repos
- Keep [docs/TEMPLATE_BOOTSTRAP_CHECKLIST.md](docs/TEMPLATE_BOOTSTRAP_CHECKLIST.md) aligned with required setup

## Security Issues

Do not open public issues for security vulnerabilities. See [SECURITY.md](SECURITY.md).
