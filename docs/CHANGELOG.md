# Changelog

<!--
  CHANGELOG.md — What makes this document good:

  A changelog communicates what changed, when, and why — for users deciding
  whether to upgrade and for maintainers tracking regression sources.

  Best practices:
  - Follow https://keepachangelog.com/en/1.1.0/ format.
  - Group entries under: Added, Changed, Deprecated, Removed, Fixed, Security.
  - Use past tense ("Added X") not imperative ("Add X").
  - Link each version header to the GitHub compare or release URL.
  - Never delete entries — changelogs are append-only history.
  - Include the date in YYYY-MM-DD format for every release.
  - For pre-1.0 projects, note breaking changes explicitly.
  - For monorepos / workspaces, consider per-crate changelogs.
  - Automate with tools like git-cliff when commit discipline is strong.

  Standard name: CHANGELOG.md (root)
  When to include: Every project that ships versioned releases.
-->

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Docker Hub publishing is opt-in: `docker.yml` pushes to GHCR only unless the
  `RUST_TEMPLATE_PUBLISH_DOCKERHUB` variable is `true`, and then also Cosign-signs the
  Docker Hub image with the same keyless identity as the GHCR image

## [0.5.1] - 2026-10-06

### Added

- ARCHITECTURE.md with component map and design decision rationale
- CHANGELOG.md following Keep a Changelog format
- RELEASING.md with maintainer release runbook
- FAQ.md covering common setup and customization questions
- Expanded README_STANDARDS.md with comprehensive style guide
- Mermaid CI/CD pipeline diagram in README.md
- Table of contents and back-to-top navigation in all READMEs
- Centered header blocks with badge rows and quick navigation links

### Changed

- Refresh development Rust and both Docker builders to 1.99.0 while retaining the tested 1.97.1 MSRV.
- Refresh verified action and tool pins, require real coverage and security artifacts, and install worktree-aware local gates.
- Run OSSF Scorecard only for scheduled scans, default-branch pushes and dispatches, and same-repository pull requests; default CI, Security and Docker workflow tokens to read-only; stop installing pre-commit in `make dev-setup`.
- Auto Release now dispatches `release.yml` and `docker.yml` for the tag it creates, because tags pushed with `GITHUB_TOKEN` start no workflows; `release.yml` gains a `dry_run` input that builds and verifies without tagging, releasing or publishing.
- Run `release.yml` build steps with bash on every runner; the Windows build previously failed under the default pwsh shell.
- Fix the Docker base-image tag version read from `rust-toolchain.toml`; the old `sed` expression never matched and published `base-rust-` instead of `base-rust-<version>`.
- A manual `release.yml` dispatch for a version with no tag now creates the annotated tag through the API; the old `git tag`/`git push` path had no git identity or credentials and failed. A dispatch with `prerelease` set no longer publishes to crates.io. RELEASING.md now lists the real build targets, package contents, SBOM formats and secrets.
- A `release.yml` dry run now runs `cargo publish --dry-run` for `prerelease` dispatches and suffixed versions too; only the real publish skips pre-releases. Release notes for a release that `release.yml` creates now come from the matching section of `CHANGELOG.md` or `docs/CHANGELOG.md`; the old extraction read only a root `CHANGELOG.md` and returned an empty section.
- `auto-release.yml` and `release.yml` now default their workflow tokens to read-only and grant `contents: write` (plus `actions: write` for the auto-release dispatch) only to the jobs that tag, release or dispatch; the unused `pull-requests: write` scope is gone. When started by a completed CI or Security run, Auto Release now reacts only to successful `push` runs on this repository's `main`; scheduled and manual runs are unchanged. It checks out its own default-branch commit instead of the triggering run's head SHA, and keys its concurrency group on the head repository so a fork PR from a branch named `main` cannot cancel a release run. `release.yml` passes dispatch inputs and job outputs to its scripts through `env` instead of interpolating them.
- `release.yml` drops its `source_ref` dispatch input: every job now checks out the workflow's own commit (the pushed tag, or the branch or tag chosen with `--ref`), so a dispatch input can no longer select an unreviewed revision to build with the default-branch cache and a write token. Auto Release already dispatched on the tag it created and no longer passes the input.
- Move both Dockerfiles from Debian 12 (bookworm) to Debian 13 (trixie): the Rust builder is now `rust:1.99.0-trixie`, the default runtime `gcr.io/distroless/cc-debian13:nonroot` and the `Dockerfile.debian` runtime `debian:trixie-slim`. Bookworm has left regular Debian security support, and its OpenSSL (`libssl3` 3.0.20-1~deb12u2, flagged by Trivy as CVE-2026-84782) has no fixed package, while trixie ships the fix in 3.5.7-1~deb13u3.
- `auto-release.yml` gains a `dry_run` dispatch input: the check job reports the version it would release, the next action and the files the release commit would change, and Create Release is skipped. Dry runs use their own concurrency group, so they cannot cancel a real release run. Every run now logs the commits it counted and why it decided to release or not, stops before writing anything if the `Cargo.toml` version is not `MAJOR.MINOR.PATCH` or is lower than the latest `vX.Y.Z` tag, and passes dispatch inputs to its scripts through `env`.
- `release.yml` now publishes to crates.io through trusted publishing: the publish job runs in the `crates-io` environment with `id-token: write`, and `rust-lang/crates-io-auth-action` (pinned to v1.0.5) exchanges the job's OIDC token for a short-lived crates.io token. The `CRATES_IO_TOKEN` and `CARGO_REGISTRY_TOKEN` secrets are no longer read, and a publish failure fails the run. Crate versions already on crates.io are skipped, so a re-run after a partial publish only publishes what is missing; a virtual workspace must list its crates in `RUST_TEMPLATE_PUBLISH_PACKAGES`. The new `CRATES_IO_PUBLISH` repository variable skips crates.io when set to `false` (dry runs still run `cargo publish --dry-run`); this template repository sets it, because its releases must not publish a `rust-cicd-template` crate. Dry runs use neither the environment nor a token.
- Auto Release can cut releases with a GitHub App: when the `RUST_TEMPLATE_RELEASE_APP_ID` variable and `RUST_TEMPLATE_RELEASE_APP_PRIVATE_KEY` secret (or, when neither is set, the ThreatFlux organization's `TF_AUTOMATION_APP_ID` and `TF_AUTOMATION_APP_PRIVATE_KEY`) are set, `actions/create-github-app-token` (pinned to v3.2.0) mints a repository-scoped `contents: write` token just before the writes; it pushes the release commit and tag as the App's bot user and creates the GitHub Release. That tag push starts `release.yml` and `docker.yml` through their tag triggers, so the explicit dispatch is skipped and the run logs why; without an App, `GITHUB_TOKEN` and the dispatch are used as before. The two pairs are never mixed, a pair with only one value set fails the run before anything is written, and a dry run mints the App token too, so a rehearsal proves the App configuration and reports which token a release would use. The release job's checkout no longer persists credentials, so `cargo check` runs without a write token in `.git/config`; only the push step passes one to git.
- Release notes come from the new `scripts/release_notes.py`, which Auto Release and `release.yml` both run: the `## [VERSION]` section of `CHANGELOG.md` or `docs/CHANGELOG.md` when there is one, otherwise every commit since the previous release tag, grouped into breaking changes, features, bug fixes and other changes, then a "Full Changelog" compare link. Auto Release used to list only `feat` and `fix` commits, so a release without them had an empty body, and `release.yml` used to fall back to a bare "See CHANGELOG.md for details" line. An Auto Release dry run now prints the notes it would publish.
- The Windows release archive now gets a `.zip.sha256` checksum file in the same `shasum -a 256 -c` format as the Unix archives; `release.yml` previously only printed its hash in the build log.
- Reframed project identity from "CI/CD Template" to "Rust Project Template"
- Reorganized README.md configuration section into structured tables
- Updated README_TEMPLATE.md to inherit all structural best practices
- Updated Cargo.toml description and keywords

### Maintenance

- Raised the Rust baseline and MSRV to 1.97.1.
- Refreshed pinned Rust builder/runtime image digests and GitHub Actions.
- Consolidated the distroless Docker hardening and CLI contract validation.

## [0.5.0] - 2025-03-24

### Added

- Initial public template release
- GitHub Actions workflows: ci.yml, security.yml, release.yml, auto-release.yml, docker.yml
- Makefile with full build, test, lint, security, and release targets
- Dockerfile with multi-stage build, Trivy scan, Cosign signing
- Template placeholder validation via `make template-check`
- Repository governance files: CODEOWNERS, issue templates, PR template
- CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md
- README_TEMPLATE.md starter for generated projects
- Bootstrap checklist and README standards documentation
- Rust 2024 edition default with 1.96.0 MSRV baseline

[Unreleased]: https://github.com/ThreatFlux/rust-cicd-template/compare/v0.5.1...HEAD
[0.5.1]: https://github.com/ThreatFlux/rust-cicd-template/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/ThreatFlux/rust-cicd-template/releases/tag/v0.5.0
