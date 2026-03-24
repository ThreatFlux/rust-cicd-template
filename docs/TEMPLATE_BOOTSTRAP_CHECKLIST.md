# Template Bootstrap Checklist

Run this checklist immediately after generating a new repository from the template.

## Required

1. Replace all placeholders:
   - `PROJECT_NAME`
   - `PROJECT_DESCRIPTION`
   - `YOUR_USERNAME`
   - `PROJECT_REPOSITORY`
   - `TEMPLATE_GITHUB_OWNER`
2. Replace `README.md` with `README_TEMPLATE.md`, then remove `README_TEMPLATE.md`.
3. Update `.github/CODEOWNERS`.
4. Update `Cargo.toml`, package metadata, and any inherited org-specific defaults.
5. Update `SECURITY.md` advisory links if the repository is not under ThreatFlux.
6. Run `make template-check`.

## Single-Crate Projects

1. Confirm `BINARY_NAME` in `Makefile`.
2. Confirm release artifacts match the intended binary.
3. Confirm the Docker image starts correctly with `make docker-build`.

## Workspace Projects

Set these repository variables or Makefile overrides:

- `RUST_TEMPLATE_BINARY_NAME`
- `RUST_TEMPLATE_BINARY_PACKAGE`
- `RUST_TEMPLATE_SBOM_MANIFEST_PATH`
- `RUST_TEMPLATE_PUBLISH_PACKAGES`

Recommended values:

- `RUST_TEMPLATE_BINARY_NAME`: the CLI binary to package
- `RUST_TEMPLATE_BINARY_PACKAGE`: the package that owns that binary
- `RUST_TEMPLATE_SBOM_MANIFEST_PATH`: the manifest used for SBOM generation
- `RUST_TEMPLATE_PUBLISH_PACKAGES`: publish order, space separated

Runner defaults:

- CI, security, docker, auto-release, and release workflows use GitHub-hosted runners out of the box.
- Only set runner repository variables if you need custom labels:
- `RUST_TEMPLATE_RUNNER_UBUNTU`
- `RUST_TEMPLATE_RUNNER_MACOS`
- `RUST_TEMPLATE_RUNNER_WINDOWS`
- `RUST_TEMPLATE_RUNNER_MACOS_ARM64`
- `RUST_TEMPLATE_RUNNER_MACOS_X64`

## Validation

Run locally:

```bash
make dev-setup
make template-check
make ci
make docker-build
```
