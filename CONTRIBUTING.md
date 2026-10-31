# Contributing to ThreatFlux Projects

This repository is the canonical Rust CI/CD template used across ThreatFlux projects. Changes here should improve the reusable template surface rather than one downstream application.

## Getting Started

1. Fork the repository
2. Clone your fork of this repository
3. Create a branch: `git checkout -b feat/your-change`
4. Make your changes
5. Run checks: `make ci-local`
6. Open a Pull Request

## Development Setup

```bash
make dev-setup
make install-hooks
make ci-local
```

## Commit Guidelines

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat`: new feature
- `fix`: bug fix
- `docs`: documentation only
- `refactor`: code refactoring
- `test`: adding or updating tests
- `chore`: maintenance

## Pull Request Process

- Use a conventional-commit title
- Explain what changed and why
- Add tests or validation where applicable
- Update template bootstrap docs when setup requirements change

### PR Checklist

- [ ] Code follows project style (`make fmt`)
- [ ] All tests pass (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] Bootstrap docs updated if needed
- [ ] Commit messages follow conventions

## Documentation

- Keep [README.md](README.md) accurate for the template repo
- Keep [README_TEMPLATE.md](README_TEMPLATE.md) accurate for generated repos
- Keep [docs/TEMPLATE_BOOTSTRAP_CHECKLIST.md](docs/TEMPLATE_BOOTSTRAP_CHECKLIST.md) aligned with required setup

## Fuzzing

The isolated [`fuzz/`](fuzz/) cargo-fuzz package checks only the public library
`add(i32, i32)`. Each input is exactly eight bytes: two little-endian signed
32-bit integers. For sums representable as `i32`, the harness compares `add`
with `checked_add`. Overflowing pairs are skipped: this target neither defines
nor verifies overflow behavior, and production arithmetic is unchanged. It does
not cover the CLI, other APIs, or downstream projects.

`fuzz/seeds/add/` contains committed inputs for zero, negative sums, cancellation,
and representable integer boundaries. Copy them into the generated corpus before
running a campaign. Keep useful regression inputs in `fuzz/seeds/add/`; generated
`fuzz/corpus/`, `fuzz/artifacts/`, `fuzz/coverage/`, and `fuzz/target/` are ignored.
The nested workspace and `fuzz/Cargo.lock` keep fuzz dependencies out of the root
application's dependency graph. Refresh that lockfile separately when updating
the harness or root package version.

GitHub's **Fuzz / Fuzz add** job builds the instrumented harness and runs it with
AddressSanitizer for 60 seconds on PRs, pushes, and manual runs, or 600 seconds on
the weekly schedule. It pins nightly `2026-10-25` and cargo-fuzz `0.13.2`; update
these deliberately together and validate them on GitHub. Local formatting uses
`cargo fmt --manifest-path fuzz/Cargo.toml --all -- --check`; the hosted job also
lints the isolated harness. Tests, builds, fuzz campaigns, and security suites
run on GitHub under the current contribution policy.

When a campaign fails, download the `fuzz-add-<commit>-<attempt>` artifact within
30 days. It contains the failure reproducers under `artifacts/add/` and the
generated corpus under `corpus/add/`. On a Linux host with the pinned toolchain,
reproduce a crash from the repository root with:

```bash
rustup toolchain install nightly-2026-10-25 --profile minimal
cargo +nightly-2026-10-25 install cargo-fuzz --version 0.13.2 --locked
cargo +nightly-2026-10-25 fetch --locked --manifest-path fuzz/Cargo.toml
CARGO_NET_OFFLINE=true cargo +nightly-2026-10-25 fuzz run add /path/to/crash-file
```

Keep the failing input, fix the cause, and require a successful hosted campaign
on the corrected commit. A green campaign demonstrates this narrow oracle only.
Scorecard recognition depends on its deployed version; after merging, inspect a
fresh default-branch Scorecard report and alert #301 before claiming remediation.

## Security Issues

Do not open public issues for security vulnerabilities. See [SECURITY.md](SECURITY.md).
