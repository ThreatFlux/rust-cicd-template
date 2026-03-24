# Frequently Asked Questions

<!--
  FAQ.md — What makes this document good:

  A FAQ reduces repeated support questions by answering them in a searchable,
  scannable flat file. It complements the README (which should stay concise)
  and the full docs (which are organized by topic, not by question).

  Best practices:
  - Use actual questions from issues, discussions, or support channels.
  - Write each answer as a self-contained block — readers jump to one Q, not read linearly.
  - Keep answers short (3-5 sentences max). Link to docs for depth.
  - Group questions by theme if the FAQ exceeds ~15 entries.
  - Remove questions that become obsolete after breaking changes.
  - Use a flat H3 structure so GitHub's TOC auto-generates a clickable list.

  Standard name: FAQ.md (root or docs/)
  When to include: Any project that receives recurring questions in issues.
-->

### How do I use this template?

```bash
gh repo create my-project --template ThreatFlux/rust-cicd-template
cd my-project
```

Then follow the [Bootstrap Checklist](TEMPLATE_BOOTSTRAP_CHECKLIST.md) to replace placeholders, swap the README, and validate with `make template-check`.

### Can I use this for a library crate instead of a binary?

Yes. Remove the `[[bin]]` section from `Cargo.toml`, add a `[lib]` section, and delete or adapt the Dockerfile (libraries typically don't ship container images). The CI and security workflows work identically for libraries.

### How do I add a new crate to a workspace?

1. Create the crate directory: `cargo new crates/my-crate --lib`
2. Add it to the root `Cargo.toml` workspace members list.
3. Set `RUST_TEMPLATE_PUBLISH_PACKAGES` to include the new crate in publish order.
4. Run `make ci` to verify everything links.

### Why does `make template-check` fail?

It means unresolved placeholders still exist in your repo. Run:

```bash
grep -rn "PROJECT_NAME\|PROJECT_DESCRIPTION\|REPLACE_WITH\|YOUR_USERNAME\|TEMPLATE_GITHUB_OWNER" .
```

Replace every match, then re-run `make template-check`.

### How do I change the MSRV?

The minimum supported Rust version is declared in seven places. Update all of them:

- `Cargo.toml` → `rust-version`
- `rust-toolchain.toml` → `channel`
- `Makefile` → `RUST_MSRV`
- `.github/workflows/ci.yml` → MSRV job matrix
- `.github/workflows/release.yml` → build toolchain
- `.github/workflows/security.yml` → toolchain pin
- `Dockerfile` → `FROM rust:` tag

See the [Configuration Reference](../README.md#configuration-reference) for details.

### How do I skip crates.io publishing?

Don't set the `CRATES_IO_TOKEN` or `CARGO_REGISTRY_TOKEN` secret. The release workflow will skip the publish step if neither secret is available.

### How do I use custom CI runners?

Set the appropriate repository variable. For example, to use a self-hosted Ubuntu runner:

1. Go to **Settings → Variables → Actions** in your GitHub repo.
2. Create `RUST_TEMPLATE_RUNNER_UBUNTU` with your runner label (e.g., `self-hosted`).

The workflows read these variables at runtime and fall back to GitHub-hosted runners if unset.

### How do I disable a workflow I don't need?

Delete the workflow file from `.github/workflows/`. If you remove `auto-release.yml`, you'll need to tag releases manually — see [RELEASING.md](RELEASING.md).

### The Docker build fails — what's wrong?

Common causes:

1. **Binary name mismatch** — ensure `BINARY_NAME` in the Makefile matches the `[[bin]]` name in `Cargo.toml`.
2. **Missing system dependencies** — if your crate depends on system libraries (e.g., OpenSSL), add them to the Dockerfile's build stage.
3. **Workspace path issues** — for workspaces, set `BINARY_PACKAGE` to the crate that owns the binary.

### How do I add code coverage badges?

1. Enable Codecov or Coveralls for your repository.
2. Add the secret (`CODECOV_TOKEN`) to your repo.
3. Add the badge to your README:
   ```markdown
   [![codecov](https://codecov.io/gh/ThreatFlux/PROJECT_NAME/branch/main/graph/badge.svg)](https://codecov.io/gh/ThreatFlux/PROJECT_NAME)
   ```

The `make coverage` target already generates LCOV output compatible with both services.
