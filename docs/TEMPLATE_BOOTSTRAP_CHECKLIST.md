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

## Reviewed Changes and Releases

1. Inspect the effective rulesets, branch protection, bypass actors and approval history
   for `main` and any active release branch. Require PRs, an independent approval,
   stale-approval dismissal, resolved conversations and appropriate required checks;
   block force pushes and deletion. Do not give the release App a bypass of PR review.
2. Confirm the owner in `.github/CODEOWNERS` can review and that another maintainer is
   available to approve release PRs. Replace the inherited owner for a new project.
3. Use check contexts from observed GitHub runs. `ci.yml` and `security.yml` run on all
   `main` pushes and PRs, including documentation changes; required jobs must not be
   conditional or absent. If using a merge queue, verify its `merge_group` runs too.
   Verify an unapproved PR is blocked and an approved PR can merge.
4. Protect `v*` tags so only authorized release actors can create them. Rehearse a
   release PR, its required checks, approval, merge and exact-commit tag before relying
   on automatic releases. See [RELEASING.md](RELEASING.md#automated-release-default).

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

Auto Release proposes a version PR and tags its accepted merge commit after exact-commit
CI and Security push runs pass. It never pushes a release commit to `main`. With the
workflow `GITHUB_TOKEN`, allow Actions to create pull requests in repository/organization
Actions settings; a maintainer with write access must approve the resulting waiting PR
workflow runs after an `opened`, `synchronize` or `reopened` event. This is separate from
independent PR review. Its candidate-branch push does not start push workflows; the PR
checks run after approval. To use a GitHub App instead, install it with **Contents: read
and write** and **Pull requests: read and write** on this repository and set both:

- variable `RUST_TEMPLATE_RELEASE_APP_ID`: the App ID or client ID
- secret `RUST_TEMPLATE_RELEASE_APP_PRIVATE_KEY`: a private key of that App

ThreatFlux repositories that can see the organization's `TF_AUTOMATION_APP_ID` variable and
`TF_AUTOMATION_APP_PRIVATE_KEY` secret use that App when neither repository value is set.
Set both values of a pair or neither (a half-set pair fails the run), then rehearse with
`gh workflow run auto-release.yml --ref main -f version_bump=patch -f dry_run=true`.
The App needs no bypass of `main`; its candidate-branch push starts raw-head CI and
Security checks, its PR event starts PR checks, and its tag push starts `release.yml`
and `docker.yml`. [RELEASING.md](RELEASING.md#release-token)
has the details. Verify the effective settings; this checklist cannot establish them.

## crates.io Publishing

`release.yml` publishes through crates.io trusted publishing (GitHub OIDC); no registry
secret is needed or read.

- Library or CLI published to crates.io: set the `CRATES_IO_PUBLISH` repository variable to
  `false`, publish the first version by hand, configure the crate's trusted publisher
  (workflow `release.yml`, environment `crates-io`) and the `crates-io` environment, then
  remove the variable. [RELEASING.md](RELEASING.md#cratesio-publishing) has the steps.
- Never published to crates.io: set `CRATES_IO_PUBLISH` to `false` and leave it.

## Docker Hub (optional)

`docker.yml` publishes to GHCR only. To also push and sign the image on Docker Hub, create
a token that can push to only this image's Docker Hub repository, store it as the
`DOCKERHUB_TOKEN` secret with its username as `DOCKERHUB_USERNAME`, and set the
`RUST_TEMPLATE_PUBLISH_DOCKERHUB` variable to `true` (`RUST_TEMPLATE_DOCKERHUB_NAMESPACE`
picks the namespace, default `threatflux`). Leave the variable unset to stay on GHCR only.
[RELEASING.md](RELEASING.md#docker-hub-publishing) has the steps.

## Validation

Run locally:

```bash
make dev-setup
make template-check
make fmt-check
make lint
```

Development uses the pinned Rust 1.99.0 toolchain. The default package MSRV is
1.97.1; keep `Cargo.toml`, `Makefile` and the CI MSRV job aligned when changing it.
The optional hooks still run broader local suites; GitHub runners perform the required
tests, builds, coverage, generated-contract checks and security checks. Inspect their
results on the exact pushed commit before merging or claiming a release is ready.
