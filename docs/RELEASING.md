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

Releases are driven by [Conventional Commits](https://www.conventionalcommits.org/)
and a reviewed version PR. Auto Release starts after successful CI or Security **push**
runs on this repository's `main`, weekly, or by dispatch on `main`. All modes require
successful CI and Security push runs for the exact `main` commit. The state machine is:

1. If the manifest version matches the latest release tag, count commits since that tag.
   A feature, fix or breaking change proposes a patch, minor or major bump. A manual
   dispatch proposes the selected bump even without those commits.
2. From the exact fetched `main` commit, update workspace manifests and existing lockfiles
   (including `fuzz/Cargo.lock`) in a read-only job. A fresh write job verifies the exact
   main and prior candidate-branch SHAs, prepared commit/tree and parsed Cargo data before
   it pushes `automation/release-vX.Y.Z` and opens or updates its PR against `main`. The
   main-sourced validator permits only the expected package and path-dependency version
   updates, including local lockfile entries. The push has an explicit expected-old-SHA
   lease (including branch creation) and an ancestry check, then reads back the exact ref.
   If `main` moved, preparation merges it into the PR branch. A merge conflict or
   unexpected PR file change stops the run.
   If a different release-version PR is already open, reconcile or close it before
   proposing another version.
3. Review the PR independently, let its required CI and Security PR checks pass, and merge
   it under the repository's protection rules. App branch pushes also run raw-head checks;
   `GITHUB_TOKEN` branch pushes do not. Auto Release does not merge or push to `main`.
4. Once CI and Security **push** runs pass on the accepted `main` commit, Auto Release
   verifies the merged PR association, manifest and lockfile versions, and current
   `main` SHA. It creates annotated `vX.Y.Z` at that accepted commit, then the GitHub
   Release with [release notes](#release-notes). An App-created tag starts `release.yml`
   and `docker.yml`; with `GITHUB_TOKEN`, Auto Release dispatches both on the new tag.

If the manifest is behind the latest release tag, the tag points elsewhere, or the
release bump is not the exact merged release PR commit, automation stops. If `main`
advances before tagging, it also stops: [recover manually](#manual-release) after
checking the current SHA and reviews. A retried run never moves an existing tag; with
`GITHUB_TOKEN` it checks for each tag workflow's push and dispatch runs at the exact tag
and SHA. A newly created tag starts missing workflows; an existing tag with no visible
run stops for operator inspection, avoiding a duplicate dispatch after an ambiguous
request. An existing failed run needs a deliberate rerun.

Repository source does not prove that branch rules, approvals or tag restrictions are
effective. A maintainer must verify them in GitHub before relying on this flow.

### Release Token

Auto Release writes only the candidate branch, release PR, tag and GitHub Release with a
GitHub App installation token when configured, and with `GITHUB_TOKEN` otherwise.
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

The App needs **Contents: read and write** and **Pull requests: read and write** on this
repository for the candidate branch and PR. Its tag token requests only Contents write;
the tag job's `GITHUB_TOKEN` also has Actions write for fallback dispatch and Pull
requests read for PR association.
Candidate preparation has only read permissions. The prepared commit is attributed to
`github-actions[bot]`; a separate GitHub-hosted write runner verifies it before using the
App or workflow token to push the branch. The App never pushes to `main` and needs no
bypass of `main` protection. Its tag push starts `release.yml` and `docker.yml`.

With `GITHUB_TOKEN`, repository or organization Actions settings must allow Actions to
create pull requests. A token-created PR's `opened`, `synchronize` or `reopened` event
creates approval-required PR workflow runs; a maintainer with write access must select
**Approve workflows to run**. That workflow approval is separate from independent PR
review. A `workflow_dispatch` check on the PR branch cannot substitute for required PR
checks. `GITHUB_TOKEN` branch and tag pushes start no push workflows, so Auto Release
dispatches tag workflows it just created after checking for existing push and dispatch runs.
An App-created PR runs without that workflow approval. A [dry run](#rehearse-auto-release)
checks the configured App's installation and requested permissions in a separate job;
the minted token is revoked unused. See GitHub's [workflow trigger rules](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)
and [required-check rules](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks).

### Rehearse Auto Release

To see what Auto Release would propose or tag without creating a branch, PR, tag,
GitHub Release or downstream workflow run, dispatch it with `dry_run`:

```bash
gh workflow run auto-release.yml --ref main -f version_bump=patch -f dry_run=true
```

The summary gives the exact `main` SHA, exact push-check decision, selected token and
candidate version or pending tag. For a proposal it lists manifest changes; the hosted
PR preparation job may also update the root and fuzz lockfiles. For a pending tag it
previews the
[release notes](#release-notes). A dry run does not exercise PR review, merge, tag
permissions or the downstream release jobs; rehearse those in GitHub before enabling
automatic releases. Dry runs have a separate concurrency group.

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

Use this for pre-releases, protected release-branch hotfixes, or a stopped automatic
release. This is an operator exception: the workflow validates the existing tag and
manifest version, while the operator verifies review, branch rules and exact checks.

### Pre-flight

1. Identify the protected branch to release and its required review policy. Run the
   repository formatting and lint checks locally: `make fmt-check` and `make lint`.

2. Update `docs/CHANGELOG.md` (or a generated repository's root `CHANGELOG.md`) —
   move items from `[Unreleased]` to a new version header.
3. Bump the version in every affected workspace manifest and update the root and existing
   fuzz lockfiles. Run `python3 scripts/release_version.py verify 1.2.3` on the resulting tree.
4. Commit the bump on a branch, explicitly stage every changed workspace manifest and
   lockfile, and merge it through an independently reviewed PR. For a single crate:

   ```bash
   git add Cargo.toml Cargo.lock docs/CHANGELOG.md
   git commit -m "chore: release v1.2.3"
   ```

5. After the reviewed bump is on the protected target branch, verify the manifests and
   lockfiles, the approved PR, and successful CI and Security push runs for that exact
   commit. Then create and push the tag at that accepted commit:

   ```bash
   git tag -a v1.2.3 -m "Release v1.2.3" <accepted-commit-sha>
   git push origin refs/tags/v1.2.3
   ```

   A maintainer or App tag push starts `release.yml` and `docker.yml` for that tag. If a
   workflow-token tag push did not start them, or one needs an operator retry, dispatch
   the missing workflow on the existing tag:

   ```bash
   gh workflow run release.yml --ref v1.2.3 -f version=1.2.3
   gh workflow run docker.yml --ref v1.2.3
   ```

   A real `release.yml` run requires `--ref` to be the existing matching tag. It checks
   that the local and remote tag resolve to its checked-out commit, creates or updates the
   GitHub Release, and publishes to crates.io under [What Happens Next](#what-happens-next).
   A [dry run](#dry-run) uses protected `main` and skips tag and GitHub Release writes; its
   publish job uses `cargo publish --dry-run` while build and packaging still run. For
   a release-branch hotfix, tag the independently reviewed accepted commit on that
   protected branch first. Read back the tag target and any dispatched run's `headSha`.

### Dry Run

To exercise the release build without tagging, creating a GitHub Release or publishing,
dispatch `release.yml` with `dry_run` enabled and the current manifest version:

```bash
gh workflow run release.yml --ref main -f version=1.2.3 -f dry_run=true
```

Use the version actually declared on the chosen remote ref. This runs every build
target, packaging, the release SBOM and `cargo publish --dry-run`,
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

### Container tags

Docker builds first publish the source SHA and, for a release tag, its full version.
Scanning and SBOM generation use the exact build digest. A separate serialized job
promotes floating aliases only after the scan, signing and SBOM jobs succeed.
It reads main and all stable tags again while holding that publication lock.
`main` and `latest` continue to track current main; major and minor aliases select
the newest stable version in their respective release lines. An older retry cannot
replace a newer alias. Base-image aliases follow current main; source-specific
base tags remain available for historical builds.

Tag builds must match the compiled Cargo version and belong to accepted main history.
This policy applies to workflow versions containing these guards; historical tags
retain their original workflow snapshots. Use the current main workflow when
performing a manual publication recovery.

### Required Permissions

| Secret or setting | Holder | Purpose |
|-------------------|--------|---------|
| `GITHUB_TOKEN` | Automatic | Release candidate branch/PR, tag, GitHub Release, fallback workflow dispatch, GHCR push; Actions must be allowed to create PRs |
| Release GitHub App (`RUST_TEMPLATE_RELEASE_APP_ID` and `RUST_TEMPLATE_RELEASE_APP_PRIVATE_KEY`, or the org's `TF_AUTOMATION_APP_*`) | Repo or org admin | Optional: release candidate branch/PR, tag and GitHub Release, so the tag starts `release.yml` and `docker.yml` ([Release Token](#release-token)) |
| crates.io trusted publisher and `crates-io` environment | Crate owner and repo admin | crates.io publish through OIDC; no registry token |
| `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` | Repo or org admin | Optional: Docker Hub push and signing, read only when `RUST_TEMPLATE_PUBLISH_DOCKERHUB` is `true` ([Docker Hub Publishing](#docker-hub-publishing)) |

### Rollback

If a release is defective:

1. Delete the GitHub Release (draft state or full delete).
2. Delete the Git tag: `git push --delete origin v1.2.3`
3. Yank from crates.io if published: `cargo yank --version 1.2.3`
4. Fix, then re-release with the next patch version.
