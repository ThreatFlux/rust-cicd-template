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
- `RUST_TEMPLATE_PUBLISH_PACKAGES`: crates.io publish order, space separated (required when the root manifest has no `[package]`)

Runner defaults:

- CI, security, docker, auto-release, and release workflows use GitHub-hosted runners out of the box.
- Only set runner repository variables if you need custom labels:
- `RUST_TEMPLATE_RUNNER_UBUNTU`
- `RUST_TEMPLATE_RUNNER_MACOS`
- `RUST_TEMPLATE_RUNNER_WINDOWS`
- `RUST_TEMPLATE_RUNNER_MACOS_ARM64`
- `RUST_TEMPLATE_RUNNER_MACOS_X64`

## Release Token

Auto Release works with the workflow `GITHUB_TOKEN` and no setup. To have a GitHub App push
release commits and tags (so the tag push itself starts `release.yml` and `docker.yml`),
install an App with **Contents: read and write** on the repository and set both:

- variable `RUST_TEMPLATE_RELEASE_APP_ID`: the App ID or client ID
- secret `RUST_TEMPLATE_RELEASE_APP_PRIVATE_KEY`: a private key of that App

ThreatFlux repositories that can see the organization's `TF_AUTOMATION_APP_ID` variable and
`TF_AUTOMATION_APP_PRIVATE_KEY` secret use that App without either setting. Set both values
or neither, then rehearse with
`gh workflow run auto-release.yml --ref main -f version_bump=patch -f dry_run=true`.
[RELEASING.md](RELEASING.md#release-token) has the details.

## crates.io Publishing

`release.yml` publishes through crates.io trusted publishing (GitHub OIDC); no registry
secret is needed or read.

- Library or CLI published to crates.io: set the `CRATES_IO_PUBLISH` repository variable to
  `false`, publish the first version by hand, configure the crate's trusted publisher
  (workflow `release.yml`, environment `crates-io`) and the `crates-io` environment, then
  remove the variable. [RELEASING.md](RELEASING.md#cratesio-publishing) has the steps.
- Never published to crates.io: set `CRATES_IO_PUBLISH` to `false` and leave it.

## Validation

Run locally:

```bash
make dev-setup
make hooks-install
make template-check
make ci-local
make docker-build
```

Development uses the pinned Rust 1.99.0 toolchain. The default package MSRV is
1.97.1; keep `Cargo.toml`, `Makefile` and the CI MSRV job aligned when changing it.
Hooks are installed for the current Git worktree: pre-commit runs formatting,
Clippy and doc tests, and pre-push runs `make ci-local`. The full local gate also
checks strict Clippy, the feature powerset, coverage, benchmarks, MSRV and SBOMs.
