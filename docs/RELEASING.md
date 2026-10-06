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

Auto Release starts in three ways: when a CI or Security run completes, on its weekly schedule, and by manual dispatch. For completed runs it reacts only to successful `push` runs on this repository's `main`, never to pull-request runs (including fork pull requests from a branch named `main`). Completed-run and scheduled triggers evaluate the current tip of `main` and release only when CI and Security have both succeeded on a push for that exact commit. A manual dispatch skips that check and releases with the bump type you choose, unless it is a [dry run](#rehearse-auto-release). Every run stops before writing anything if the `Cargo.toml` version is lower than the latest `vX.Y.Z` tag. Its workflow token is read-only except in the job that pushes the release commit and tag, creates the GitHub Release and dispatches the tag workflows.

**No manual steps are required for routine releases.**

### Rehearse Auto Release

To see what Auto Release would do without committing, tagging, creating a GitHub Release
or dispatching the tag workflows, dispatch it with `dry_run`:

```bash
gh workflow run auto-release.yml --ref main -f version_bump=patch -f dry_run=true
```

The Check for Release job logs the commits since the last tag, the decision an automatic
run would make and why, and the version this dispatch would release. Its Report dry run
step, also shown in the run summary, names the next action, lists the files the release
commit would change and ends with "nothing was written to the repository". On a ref whose
head is not the tip of `main`, it reports that Create Release would skip the run as stale
instead. Create Release is skipped. Dry runs have their own concurrency group, so they never cancel a real run.

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

   `release.yml` always builds the commit at the `--ref` it was dispatched on (a branch
   head or an existing tag). A real run makes sure the release tag points at that commit,
   creates or updates the GitHub Release, and publishes to crates.io under the rules in
   [What Happens Next](#what-happens-next). A [dry run](#dry-run) skips the tag and the
   GitHub Release and only runs `cargo publish --dry-run`. To release from a release
   branch, dispatch on that branch.

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
| Publish | crates.io through [trusted publishing](#cratesio-publishing): each crate version not yet on crates.io is published and versions already there are skipped; nothing is published for `-rc`-style versions, `prerelease` dispatches or when `CRATES_IO_PUBLISH` is `false`; a dry run only runs `cargo publish --dry-run` |
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

### crates.io Publishing

The publish job uses [crates.io trusted publishing](https://crates.io/docs/trusted-publishing)
and stores no registry secret. A real run requests `id-token: write`, runs in the `crates-io`
environment, and [`rust-lang/crates-io-auth-action`](https://github.com/rust-lang/crates-io-auth-action)
exchanges the job's GitHub OIDC token for a crates.io token that expires after 30 minutes and
is revoked when the job ends. A failed publish fails the run. Dry runs use neither the
environment nor a token.

Set it up once per crate:

1. Set the `CRATES_IO_PUBLISH` repository variable to `false` until the crate exists.
   Trusted publishing only publishes new versions of an existing crate, and crates.io
   rejects its tokens for a crate that has never been published.
2. Publish the first version by hand from its release tag with your own crates.io API
   token: `cargo publish --locked` (for a workspace, `-p <crate>` in
   `RUST_TEMPLATE_PUBLISH_PACKAGES` order).
3. On crates.io, open each crate's **Settings → Trusted Publishing**, choose **Add →
   GitHub** and enter the repository owner, the repository name, workflow filename
   `release.yml` and environment `crates-io`.
4. In GitHub **Settings → Environments**, create `crates-io` and limit its deployment
   branches and tags to `main` and tags matching `v*` (plus any release branch you
   dispatch from); add required reviewers if releases need an approval. Without this,
   the first real run creates the environment with no restrictions.
5. Delete `CRATES_IO_PUBLISH` or set it to `true`. Once a release has published through
   the workflow, consider enabling **Require trusted publishing for all new versions** in
   the crate's crates.io settings so API tokens can no longer publish it.

| `CRATES_IO_PUBLISH` | Real release | Dry run |
|---------------------|--------------|---------|
| unset or `true` | Publishes through trusted publishing | `cargo publish --dry-run` |
| `false` | Skips crates.io and logs why | `cargo publish --dry-run` |
| anything else | Fails the publish job | Fails the publish job |

A repository that never publishes to crates.io (an application, or the
`ThreatFlux/rust-cicd-template` repository itself) sets `CRATES_IO_PUBLISH=false`
permanently:

```bash
gh variable set CRATES_IO_PUBLISH --repo OWNER/REPO --body false
```

### Required Permissions

| Secret or setting | Holder | Purpose |
|-------------------|--------|---------|
| `GITHUB_TOKEN` | Automatic | Tags, release assets, workflow dispatch, GHCR push |
| crates.io trusted publisher and `crates-io` environment | Crate owner and repo admin | crates.io publish through OIDC; no registry token |
| `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` | Repo or org admin | Docker Hub push |

### Rollback

If a release is defective:

1. Delete the GitHub Release (draft state or full delete).
2. Delete the Git tag: `git push --delete origin v1.2.3`
3. Yank from crates.io if published: `cargo yank --version 1.2.3`
4. Fix, then re-release with the next patch version.
