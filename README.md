# ThreatFlux Rust CI/CD Template

Standardized CI/CD templates for Rust projects. Uses **Rust 1.92.0** as the minimum supported version.

## Features

- **Pinned GitHub Actions** - All actions use commit SHAs for security
- **Self-hosted runners** - Configured for self-hosted infrastructure
- **Comprehensive CI** - Format, lint, test, coverage, MSRV, feature testing
- **Security scanning** - cargo-audit, cargo-deny, SBOM, secret scanning
- **Multi-platform releases** - Linux (amd64/arm64), macOS (amd64/arm64), Windows
- **Docker support** - Multi-arch builds with security scanning and signing
- **Auto-release** - Automatic releases from conventional commits

## Quick Start

```bash
# Clone this template
gh repo create my-project --template threatflux/rust-cicd-template

# Or copy files to existing project
cp -r .github Makefile deny.toml Dockerfile /path/to/your/project/

# Install development tools
make dev-setup

# Run CI checks locally
make ci
```

## Workflows

| Workflow | Purpose | Trigger |
|----------|---------|---------|
| `ci.yml` | Build, test, lint, coverage | Push, PR, Weekly |
| `security.yml` | Security audit, license check, SBOM | Push, PR, Weekly |
| `release.yml` | Multi-platform release builds | Tags |
| `auto-release.yml` | Automatic version bumps | CI success |
| `docker.yml` | Container builds with scanning | Push, PR, Weekly |

## Makefile Targets

```bash
make help          # Show all targets
make dev-setup     # Install development tools
make ci            # Run full CI checks
make ci-quick      # Run quick checks only
make test          # Run tests
make lint          # Run clippy
make lint-strict   # Run strict clippy (pedantic + nursery)
make coverage      # Generate code coverage
make security      # Run security checks
make docker-build  # Build Docker image
```

## Configuration

### Rust Version

MSRV is set to **1.92.0**. Update in:
- `Cargo.toml` - `rust-version`
- `Makefile` - `RUST_MSRV`
- `.github/workflows/ci.yml` - MSRV job toolchain
- `Dockerfile` - Base image version

### Clippy Flags

Strict configuration (pedantic + nursery):
```
-D warnings
-D clippy::all
-D clippy::pedantic
-D clippy::nursery
-A clippy::multiple_crate_versions
-A clippy::module_name_repetitions
-A clippy::missing_errors_doc
-A clippy::missing_panics_doc
-A clippy::must_use_candidate
```

### Required Secrets

| Secret | Purpose |
|--------|---------|
| `CODECOV_TOKEN` | Coverage uploads |
| `CARGO_REGISTRY_TOKEN` | crates.io publishing |

## Conventional Commits

Use conventional commits for automatic changelog generation:

- `feat:` - New features (bumps minor)
- `fix:` - Bug fixes (bumps patch)
- `BREAKING CHANGE:` - Breaking changes (bumps major)
- `chore:` - Maintenance
- `docs:` - Documentation

## Database Migrations

ThreatFlux projects use **embedded migrations** - all SQL is in Rust code, not separate files:

```rust
// src/migrations.rs - Migrations run automatically on startup
pub const MIGRATIONS: &[&str] = &[
    "CREATE TABLE IF NOT EXISTS users (id UUID PRIMARY KEY, email TEXT UNIQUE);",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS name TEXT;",
];
```

Key principles:
- No separate `.sql` migration files
- Idempotent statements (`IF NOT EXISTS`)
- Auto-run on server startup
- Single binary deployment

See [docs/README_STANDARDS.md](docs/README_STANDARDS.md) for details.

## Contact

- **General**: admin@threatflux.ai
- **Security**: security@threatflux.ai
- **Privacy**: privacy@threatflux.ai

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## License

MIT - ThreatFlux
