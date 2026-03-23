# ThreatFlux Rust CI/CD Template

Standardized CI/CD templates for Rust applications and workspaces. Uses **Rust 1.94.0** as the maintained baseline, defaults new projects to **Rust 2024 edition**, and is designed to be copied into either a single-crate project or a workspace with an explicit CLI package.

## What This Template Includes

- Pinned GitHub Actions by commit SHA
- Hosted-runner CI defaults with cross-platform test coverage
- Strict formatting, clippy, docs, feature, coverage, and MSRV checks
- Security workflows for audit, deny, secret scanning, SBOMs, and Scorecard
- Multi-platform release packaging for Linux, macOS, and Windows
- Docker build, scan, sign, and image SBOM generation
- Auto-release flow based on conventional commits
- Repo governance defaults: `CODEOWNERS`, issue templates, PR template, contributing, security, and code of conduct files
- Bootstrap tooling: `.editorconfig`, `rust-toolchain.toml`, `clippy.toml`, `rustfmt.toml`, and optional `pre-commit`

## Quick Start

```bash
gh repo create my-project --template ThreatFlux/rust-cicd-template
cd my-project

# Replace template placeholders and repo defaults first.
make template-check

# Install local tooling and run CI locally.
make dev-setup
make ci
```

If you are copying files into an existing project instead of generating from the template, copy:

```bash
cp -r .github docs scripts .cargo \
  Makefile Dockerfile deny.toml \
  .editorconfig .pre-commit-config.yaml clippy.toml rustfmt.toml rust-toolchain.toml \
  /path/to/your/project/
```

## Single Crate vs Workspace

The template repo itself is a single binary crate, but the workflows and Makefile are parameterized so downstream repos can support either shape.

Single-crate projects:
- Keep `Cargo.toml` as the root package
- Set `BINARY_NAME` in `Makefile` if the binary differs from the package name

Workspace projects:
- Convert the root manifest into a workspace
- Set these repo variables or Makefile overrides:
  - `RUST_TEMPLATE_BINARY_NAME`
  - `RUST_TEMPLATE_BINARY_PACKAGE`
  - `RUST_TEMPLATE_PUBLISH_PACKAGES`
  - `RUST_TEMPLATE_SBOM_MANIFEST_PATH`

See [docs/TEMPLATE_BOOTSTRAP_CHECKLIST.md](docs/TEMPLATE_BOOTSTRAP_CHECKLIST.md) for the full setup checklist.

## Workflows

| Workflow | Purpose | Trigger |
|----------|---------|---------|
| `ci.yml` | Format, lint, test, docs, coverage smoke, MSRV, feature checks | Push, PR, weekly |
| `security.yml` | Audit, deny, SBOM, secret scanning, Scorecard | Push, PR, weekly |
| `release.yml` | Build, package, publish, and attach release assets | Tags, manual |
| `auto-release.yml` | Conventional-commit-driven release tagging | CI/Security success |
| `docker.yml` | Build, scan, sign, and SBOM container images | Push, PR, weekly |

## Bootstrap Requirements

Before merging a generated repo, replace:
- package, binary, and repository placeholders
- starter description text
- example usernames and repository URLs
- default code owners
- contact emails if they differ from ThreatFlux defaults

Use:

```bash
make template-check
```

That target fails if obvious placeholders are still present.

## Key Configuration

MSRV is set in:
- `Cargo.toml`
- `rust-toolchain.toml`
- `Makefile`
- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`
- `.github/workflows/security.yml`
- `Dockerfile`

Release and packaging behavior can be overridden with:
- `BINARY_NAME`
- `BINARY_PACKAGE`
- `SBOM_MANIFEST_PATH`
- `PUBLISH_PACKAGES`

Equivalent GitHub repository variables:
- `RUST_TEMPLATE_BINARY_NAME`
- `RUST_TEMPLATE_BINARY_PACKAGE`
- `RUST_TEMPLATE_SBOM_MANIFEST_PATH`
- `RUST_TEMPLATE_PUBLISH_PACKAGES`

## Required Secrets

| Secret | Purpose |
|--------|---------|
| `GITHUB_TOKEN` | Release assets, package publishing, container publishing |
| `CRATES_IO_TOKEN` or `CARGO_REGISTRY_TOKEN` | crates.io publishing |

## Documentation Standards

README guidance lives in [docs/README_STANDARDS.md](docs/README_STANDARDS.md). The starter project README lives in [README_TEMPLATE.md](README_TEMPLATE.md).

## License

MIT - ThreatFlux
