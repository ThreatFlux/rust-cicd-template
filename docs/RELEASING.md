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
3. Commits the version bump, creates a new Git tag (`v*`), and creates the GitHub Release with [release notes](#release-notes), using the [release token](#release-token).
4. Starts `release.yml` (build, package, SBOM, crates.io) and `docker.yml` (image build, scan, sign, SBOM) for that tag. With a GitHub App release token, the tag push starts them through their `on: push: tags` triggers and nothing is dispatched. With the `GITHUB_TOKEN` fallback, the tag push starts no workflows, so Auto Release dispatches both on the tag.

Auto Release starts in three ways: when a CI or Security run completes, on its weekly schedule, and by manual dispatch. For completed runs it reacts only to successful `push` runs on this repository's `main`, never to pull-request runs (including fork pull requests from a branch named `main`). Completed-run and scheduled triggers evaluate the current tip of `main` and release only when CI and Security have both succeeded on a push for that exact commit. A manual dispatch skips that check and releases with the bump type you choose, unless it is a [dry run](#rehearse-auto-release). Every run stops before writing anything if the `Cargo.toml` version is lower than the latest `vX.Y.Z` tag. Its workflow token is read-only except in the job that pushes the release commit and tag, creates the GitHub Release and dispatches the tag workflows.

**No manual steps are required for routine releases.**

### Release Token

Auto Release writes the release commit, the tag and the GitHub Release with a GitHub App
installation token when one is configured, and with the workflow `GITHUB_TOKEN` otherwise.
It uses the first pair below that has any value set, and that pair must have both:

| Pair | App ID or client ID (variable) | Private key (secret) |
|------|--------------------------------|----------------------|
| Repository | `RUST_TEMPLATE_RELEASE_APP_ID` | `RUST_TEMPLATE_RELEASE_APP_PRIVATE_KEY` |
| ThreatFlux organization | `TF_AUTOMATION_APP_ID` | `TF_AUTOMATION_APP_PRIVATE_KEY` |
| Neither set | `GITHUB_TOKEN` fallback | |

The organization pair lets ThreatFlux repositories use the organization's automation App
without per-repository setup; a repository pair overrides it. The pairs are never mixed: a
pair with only one value set fails the run before anything is written, instead of
borrowing the other pair's value or silently falling back to `GITHUB_TOKEN`.

The App needs **Contents: read and write** on the repository. Its token is limited to this
repository and that permission, and is minted just before the release commit is pushed.
The release job's checkout keeps no credentials, so `cargo check` never sees a write
token; only the step that pushes the commit and tag passes one to git. If `main` is
protected, allow the App to push to it (for example as a ruleset bypass actor). With the
App:

- the release commit and tag are pushed by `<app-slug>[bot]`, so the tag push starts
  `release.yml` and `docker.yml` by itself and Auto Release dispatches nothing
  (dispatching too would run each of them twice); the run logs a notice saying so
- the release commit on `main` runs CI, Security and Docker like any other push; the Auto
  Release run that follows finds no commits since the new tag and does not release again

Without the App, releases work as before: `GITHUB_TOKEN` pushes the commit and tag and
Auto Release dispatches `release.yml` and `docker.yml` on the new tag. A [dry
run](#rehearse-auto-release) mints the App token too, so it proves the configuration
before a real release needs it.

### Rehearse Auto Release

To see what Auto Release would do without committing, tagging, creating a GitHub Release
or starting the tag workflows, dispatch it with `dry_run`:

```bash
gh workflow run auto-release.yml --ref main -f version_bump=patch -f dry_run=true
```

The Check for Release job logs the commits since the last tag, the decision an automatic
run would make and why, and the version this dispatch would release. When a GitHub App is
configured, it mints the App's installation token exactly as a release would, then lets it
be revoked unused, so a misconfigured App ID, key or installation fails the dry run. Its
Report dry run step, also shown in the run summary, names the release token, the next
action (including whether `release.yml` and `docker.yml` would be dispatched or started by
the tag push), lists the files the release commit would change and ends with "nothing was
written to the repository". On a ref whose head is not the tip of `main`, it reports that
Create Release would skip the run as stale instead. It also prints the [release
notes](#release-notes) a release would publish. Create Release is skipped. Dry runs have their own concurrency group, so they never cancel a real run.

### Release Notes

Auto Release and `release.yml` both write the GitHub Release notes with
`scripts/release_notes.py`. Under a `## Release vX.Y.Z` heading, the notes hold:

- the `## [X.Y.Z]` section of `CHANGELOG.md` (or `docs/CHANGELOG.md`) when it exists and is
  not empty;
- otherwise every commit since the previous `vX.Y.Z` tag, grouped into Breaking Changes
  (`type!:` subjects or `BREAKING CHANGE:` footers), Features, Bug Fixes and Other Changes,
  leaving out merge commits and `chore: release` commits;
- then a "Full Changelog" link comparing the previous tag with the new one.

For curated notes, merge the version's changelog section (the `[Unreleased]` items moved
under `## [X.Y.Z] - YYYY-MM-DD`) before the release, and preview the result with
`python3 scripts/release_notes.py X.Y.Z` or an Auto Release dry run. Whichever workflow
creates the GitHub Release writes its notes, normally Auto Release; `release.yml` keeps the
notes of a release that already exists.

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

A `v*` tag pushed by a maintainer or by the release GitHub App triggers `release.yml` (with the `GITHUB_TOKEN` fallback, auto-release dispatches it instead):

| Step | Artifact |
|------|----------|
| Build | Linux x86_64 (gnu and musl), Linux aarch64, macOS arm64, macOS x86_64, Windows x86_64 (MSVC) |
| Package | `.tar.gz` (Unix) or `.zip` (Windows) holding the binary only, each with a `.sha256` checksum file (`shasum -a 256 -c` format) |
| SBOM | CycloneDX release SBOM (`<binary>-v<version>.cdx.json`) |
| Publish | crates.io through [trusted publishing](#cratesio-publishing): each crate version not yet on crates.io is published and versions already there are skipped; nothing is published for `-rc`-style versions, `prerelease` dispatches or when `CRATES_IO_PUBLISH` is `false`; a dry run only runs `cargo publish --dry-run` |
| GitHub Release | Archives, their checksums and the release SBOM attached; a release that `release.yml` creates gets the [release notes](#release-notes) too |

The `docker.yml` workflow also runs for the tag (on a maintainer or App push, dispatched by auto-release with the `GITHUB_TOKEN` fallback, or dispatched by hand after a `release.yml` dispatch), producing:

| Step | Artifact |
|------|----------|
| Build | `linux/amd64` and `linux/arm64` image |
| Scan | Trivy vulnerability scan |
| Sign | Cosign keyless image signature on GHCR, and on Docker Hub when [Docker Hub publishing](#docker-hub-publishing) is on |
| SBOM | SPDX image SBOM (workflow artifact) |
| Push | `ghcr.io/threatflux/<image>` with semver tags (`1.2.3`, `1.2`, `1`) and the short SHA; the same image goes to `docker.io/<namespace>/<image>` only when [Docker Hub publishing](#docker-hub-publishing) is on |
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

### Docker Hub Publishing

GHCR (`ghcr.io/threatflux/<image>`) is the primary registry. Docker Hub publishing is off
unless the `RUST_TEMPLATE_PUBLISH_DOCKERHUB` variable is `true`, the same switch the other
ThreatFlux Rust repositories use. While it is off, `docker.yml` does not log in to
`docker.io`, reads no `DOCKERHUB_*` secret and generates no `docker.io` tags. Turning it
off deletes nothing: images already on Docker Hub stay as they are.

To publish to Docker Hub again:

1. Create the Docker Hub repository `<namespace>/<repo>`: the lowercased GitHub
   repository name under the `RUST_TEMPLATE_DOCKERHUB_NAMESPACE` variable
   (default `threatflux`).
2. Create a Docker Hub personal access token with **Read & Write** access (never
   **Read, Write & Delete**) for an account that can write to only the repositories this
   workflow publishes, for example a bot account in a Docker Hub team that has
   **Read & Write** on just those repositories.
3. Store the token as the `DOCKERHUB_TOKEN` secret and the account name as
   `DOCKERHUB_USERNAME`, either as repository secrets or as organization secrets limited to
   the repositories that publish. The account name must not appear in the lowercased
   GitHub `owner/repo` path (`threatflux/<repo>`): GitHub drops a job output that contains a
   secret's value, and `docker.yml` hands that path from the build job to the scan, sign
   and SBOM jobs. That rules out a Docker Hub organization access token for the
   `threatflux` organization, whose username is the organization name.
4. Turn the switch on:

   ```bash
   gh variable set RUST_TEMPLATE_PUBLISH_DOCKERHUB --repo OWNER/REPO --body true
   ```

The next non-PR `docker.yml` run logs in to Docker Hub, pushes the same multi-arch image
(same digest and tags, plus the `base-rust-*` tags) to `docker.io/<namespace>/<repo>`, and wherever the `Sign Container`
job signs the GHCR image (`main` and `v*` tags) it also signs the Docker Hub copy with the
same keyless identity. If the switch is on but either secret is missing, the run warns and
publishes to GHCR only. Check a signature with:

```bash
cosign verify docker.io/<namespace>/<repo>:<tag> \
  --certificate-identity-regexp '^https://github.com/OWNER/REPO/\.github/workflows/docker\.yml@' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

To stop publishing there, delete the variable or set it to `false`.

### Required Permissions

| Secret or setting | Holder | Purpose |
|-------------------|--------|---------|
| `GITHUB_TOKEN` | Automatic | Tags, release assets, workflow dispatch, GHCR push |
| Release GitHub App (`RUST_TEMPLATE_RELEASE_APP_ID` and `RUST_TEMPLATE_RELEASE_APP_PRIVATE_KEY`, or the org's `TF_AUTOMATION_APP_*`) | Repo or org admin | Optional: Auto Release's release commit, tag and GitHub Release, so the tag starts `release.yml` and `docker.yml` ([Release Token](#release-token)) |
| crates.io trusted publisher and `crates-io` environment | Crate owner and repo admin | crates.io publish through OIDC; no registry token |
| `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` | Repo or org admin | Optional: Docker Hub push and signing, read only when `RUST_TEMPLATE_PUBLISH_DOCKERHUB` is `true` ([Docker Hub Publishing](#docker-hub-publishing)) |

### Rollback

If a release is defective:

1. Delete the GitHub Release (draft state or full delete).
2. Delete the Git tag: `git push --delete origin v1.2.3`
3. Yank from crates.io if published: `cargo yank --version 1.2.3`
4. Fix, then re-release with the next patch version.
