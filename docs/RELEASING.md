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
5. Tag:
   ```bash
   git tag v1.2.3
   git push origin main --tags
   ```

### Dry Run

To exercise the release build without tagging, creating a GitHub Release or publishing,
dispatch `release.yml` with `dry_run` enabled and the current manifest version:

```bash
gh workflow run release.yml --ref main -f version="$(python3 scripts/release_version.py current)" -f dry_run=true
```

This runs every build target, packaging, the release SBOM and `cargo publish --dry-run`;
artifacts are kept on the workflow run only.

### What Happens Next

A `v*` tag pushed by a maintainer triggers `release.yml` (auto-release dispatches it instead):

| Step | Artifact |
|------|----------|
| Cross-compile | Linux x86_64, Linux aarch64, macOS universal, Windows x86_64 |
| Package | `.tar.gz` (Unix) and `.zip` (Windows) with binary + LICENSE + README |
| Publish | crates.io (if `CRATES_IO_TOKEN` secret is set) |
| GitHub Release | Checksums + packaged assets attached |

The `docker.yml` workflow also runs for the tag (on push, or dispatched by auto-release), producing:

| Step | Artifact |
|------|----------|
| Build | Multi-arch Docker image |
| Scan | Trivy vulnerability scan |
| Sign | Cosign image signature |
| SBOM | CycloneDX image SBOM |
| Push | `ghcr.io/threatflux/<image>:<tag>` |
| Base toolchain tags | `ghcr.io/threatflux/rust-cicd-template:base-rust-1.99.0`, `ghcr.io/threatflux/rust-cicd-template:base-rust-latest` |

### Required Permissions

| Secret | Holder | Purpose |
|--------|--------|---------|
| `GITHUB_TOKEN` | Automatic | Release assets, GHCR push |
| `CRATES_IO_TOKEN` | Repo admin | crates.io publish |

### Rollback

If a release is defective:

1. Delete the GitHub Release (draft state or full delete).
2. Delete the Git tag: `git push --delete origin v1.2.3`
3. Yank from crates.io if published: `cargo yank --version 1.2.3`
4. Fix, then re-release with the next patch version.
