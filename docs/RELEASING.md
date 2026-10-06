# Releasing

<!--
  RELEASING.md — What makes this document good:

  This is a maintainer runbook for cutting releases. It removes guesswork from
  a high-stakes, infrequent operation and prevents "only Alice knows how to
  release" situations.

  Best practices:
  - Write as a numbered checklist a maintainer can follow step-by-step.
  - Include pre-release validation steps (CI green, changelog updated, etc.).
  - Document both the automated path and the manual fallback.
  - State which secrets / permissions are required and who holds them.
  - Explain what happens after the release (crates.io, Docker, GitHub Release).
  - Keep this under ~100 lines — it should be a runbook, not a tutorial.

  Standard name: RELEASING.md (root or docs/)
  When to include: Any project with a release workflow or published artifacts.
-->

## Automated Release (default)

Releases are driven by [Conventional Commits](https://www.conventionalcommits.org/). When CI and security checks pass on `main`, the `auto-release.yml` workflow:

1. Analyzes commits since the last tag.
2. Determines the version bump (patch / minor / major) from commit prefixes.
3. Commits the version bump, creates a new Git tag (`v*`), and creates the GitHub Release with generated notes.
4. Dispatches `release.yml` (build, package, SBOM, crates.io) and `docker.yml` (image build, scan, sign, SBOM) for that tag. Tags pushed with the workflow `GITHUB_TOKEN` do not trigger other workflows on their own, so this explicit dispatch is required.

Auto Release starts in three ways: when a CI or Security run completes, on its weekly schedule, and by manual dispatch. For completed runs it reacts only to successful `push` runs on this repository's `main`, never to pull-request runs (including fork pull requests from a branch named `main`). Completed-run and scheduled triggers evaluate the current tip of `main` and release only when CI and Security have both succeeded on a push for that exact commit. A manual dispatch skips that check and releases with the bump type you choose. Its workflow token is read-only except in the job that pushes the release commit and tag, creates the GitHub Release and dispatches the tag workflows.

**No manual steps are required for routine releases.**

## Manual Release

Use this when the automated flow is insufficient (e.g., pre-release versions, hotfixes from a release branch).

### Pre-flight

1. Ensure `main` is green:

   ```bash
   make ci
   ```

2. Update `CHANGELOG.md` — move items from `[Unreleased]` to a new version header.
3. Bump the version in `Cargo.toml`.
4. Commit:

   ```bash
   git add Cargo.toml docs/CHANGELOG.md
   git commit -m "chore: release v1.2.3"
   ```

5. Tag, either by pushing it yourself:

   ```bash
   git tag v1.2.3
   git push origin main --tags
   ```

   or, once the bump is on `main`, by dispatching `release.yml`, which creates the
   annotated `v1.2.3` tag through the API. A tag created with the workflow token
   starts no other workflows, so dispatch the container build for it too:

   ```bash
   gh workflow run release.yml --ref main -f version=1.2.3
   gh workflow run docker.yml --ref v1.2.3   # once the tag exists
   ```

### Dry Run

To exercise the release build without tagging, creating a GitHub Release or publishing,
dispatch `release.yml` with `dry_run` enabled and the current manifest version:

```bash
gh workflow run release.yml --ref main -f version="$(python3 scripts/release_version.py current)" -f dry_run=true
```

This runs every build target, packaging, the release SBOM and `cargo publish --dry-run`,
including when `prerelease` is set or the version has a suffix; artifacts are kept on the
workflow run only.

### What Happens Next

A `v*` tag pushed by a maintainer triggers `release.yml` (auto-release dispatches it instead):

| Step | Artifact |
|------|----------|
| Build | Linux x86_64 (gnu and musl), Linux aarch64, macOS arm64, macOS x86_64, Windows x86_64 (MSVC) |
| Package | `.tar.gz` plus `.sha256` (Unix) and `.zip` (Windows), each holding the binary only |
| SBOM | CycloneDX release SBOM (`<binary>-v<version>.cdx.json`) |
| Publish | crates.io (if `CRATES_IO_TOKEN` or `CARGO_REGISTRY_TOKEN` is set; skipped for `-rc`-style versions and `prerelease` dispatches; a dry run only runs `cargo publish --dry-run`) |
| GitHub Release | Archives, Unix checksums and the release SBOM attached; a release that `release.yml` creates gets the matching `CHANGELOG.md` (root or `docs/`) section as its notes |

The `docker.yml` workflow also runs for the tag (on a maintainer push, dispatched by auto-release, or dispatched by hand after a `release.yml` dispatch), producing:

| Step | Artifact |
|------|----------|
| Build | `linux/amd64` and `linux/arm64` image |
| Scan | Trivy vulnerability scan |
| Sign | Cosign keyless image signature |
| SBOM | SPDX image SBOM (workflow artifact) |
| Push | `ghcr.io/threatflux/<image>` and `docker.io/<namespace>/<image>` with semver tags (`1.2.3`, `1.2`, `1`) and the short SHA |
| Base toolchain tags | `ghcr.io/threatflux/rust-cicd-template:base-rust-1.99.0` (`base-rust-latest` on `main` only) |

### Required Permissions

| Secret | Holder | Purpose |
|--------|--------|---------|
| `GITHUB_TOKEN` | Automatic | Tags, release assets, workflow dispatch, GHCR push |
| `CRATES_IO_TOKEN` or `CARGO_REGISTRY_TOKEN` | Repo or org admin | crates.io publish; an org-level secret also counts |
| `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` | Repo or org admin | Docker Hub push |

### Rollback

If a release is defective:

1. Delete the GitHub Release (draft state or full delete).
2. Delete the Git tag: `git push --delete origin v1.2.3`
3. Yank from crates.io if published: `cargo yank --version 1.2.3`
4. Fix, then re-release with the next patch version.
