# Template Bootstrap Checklist

Run this checklist immediately after generating a new repository from the template.

## Required

1. Replace all placeholders:
   - `PROJECT_NAME`
   - `PROJECT_DESCRIPTION`
   - `YOUR_USERNAME`
   - `PROJECT_REPOSITORY`
2. Update `.github/CODEOWNERS`.
3. Update `README.md`, `Cargo.toml`, and package metadata.
4. Update `SECURITY.md` advisory links if the repository is not under ThreatFlux.
5. Run `make template-check`.

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

## Validation

Run locally:

```bash
make dev-setup
make template-check
make ci
make docker-build
```
