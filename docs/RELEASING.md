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
3. Creates a new Git tag (`v*`).
4. The tag triggers `release.yml`, which builds, packages, publishes, and creates the GitHub Release.

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

### What Happens Next

The `v*` tag triggers `release.yml`:

| Step | Artifact |
|------|----------|
| Cross-compile | Linux x86_64, Linux aarch64, macOS universal, Windows x86_64 |
| Package | `.tar.gz` (Unix) and `.zip` (Windows) with binary + LICENSE + README |
| Publish | crates.io (if `CRATES_IO_TOKEN` secret is set) |
| GitHub Release | Checksums + packaged assets attached |

The `docker.yml` workflow also triggers on the tag, producing:

| Step | Artifact |
|------|----------|
| Build | Multi-arch Docker image |
| Scan | Trivy vulnerability scan |
| Sign | Cosign image signature |
| SBOM | CycloneDX image SBOM |
| Push | `ghcr.io/threatflux/<image>:<tag>` |

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
