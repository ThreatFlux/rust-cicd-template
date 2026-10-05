# Stable toolchain and CI refresh, 2026-10-05

The development toolchain and both container builders use Rust 1.99.0. The
package still supports Rust 1.97.1: its locked all-target check and complete
unit, CLI integration and documentation tests passed using that compiler.
Package version 0.5.0, edition 2024, the default feature graph and the public
library and CLI contracts remain unchanged. There are no registry dependencies
in the manifest or lockfile to upgrade.

| Surface | Selected stable version | Primary evidence |
| --- | --- | --- |
| Development Rust | 1.99.0 | [Rust distribution manifest](https://static.rust-lang.org/dist/channel-rust-stable.toml) |
| Package MSRV | 1.97.1, retained | Actual `RUSTUP_TOOLCHAIN=1.97.1` check and complete test run |
| Cargo Audit / Deny | 0.22.2 / 0.20.2 | [Cargo Audit](https://crates.io/crates/cargo-audit), [Cargo Deny](https://crates.io/crates/cargo-deny) |
| Cargo LLVM Cov / Hack | 0.9.1 / 0.6.45 | [Cargo LLVM Cov](https://crates.io/crates/cargo-llvm-cov), [Cargo Hack](https://crates.io/crates/cargo-hack) |
| Cargo CycloneDX / Cross | 0.5.9 / 0.2.5 | [Cargo CycloneDX](https://crates.io/crates/cargo-cyclonedx), [Cross](https://crates.io/crates/cross) |
| TruffleHog / Gitleaks | 3.98.0 / 8.30.1 | [TruffleHog release](https://github.com/trufflesecurity/trufflehog/releases/tag/v3.98.0), [Gitleaks release](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1) |

All five workflows were reviewed. Their 74 action uses are pinned to verified
upstream commits, and their supplied inputs were checked against those exact
action schemas. Updated action versions include Build Push 7.4.0, Buildx 4.4.1,
QEMU 4.4.0, Install Action 2.87.25, SBOM Action 0.24.3 and CodeQL bundle 2.27.1.
Already current checkout, artifact, cache, login, metadata, Trivy, Cosign and
Scorecard actions retain their verified pins.

Both Dockerfiles use the current Rust 1.99.0 Bookworm image index digest
`59037199c44290f2befcdd58dcc540164763fc296950255aaefeef096a1866b0`.
The current Debian slim runtime digest is
`3783cc01769c7b2b1b83a5c5ad96c815348e28ed7da68e2e3687004faa906251`;
the already current distroless runtime digest remains
`9dac0a79194e45a7da0158a9c6da57b217585af0786db3845d1f0ec1a0dd182f`.
Native ARM64 builds and version, help, non-root user and healthcheck contract
checks passed for both runtime variants. Hosted PR Docker validation exercises
the existing AMD64 image build without publishing it.

The matrix now selects its actual compiler explicitly, including beta, nightly
and the retained MSRV. Each Rust job prints compiler and Cargo versions. A
coverage job retains required LCOV output on pull requests. SBOM generation
excludes its destination directory and requires a nonempty report. The full
local gate adds strict Clippy, feature powerset, MSRV, coverage, benchmark
compilation and SBOM validation; hooks apply only to the current worktree.

Security report generation and scanner execution failures now fail their jobs.
TruffleHog still reports verified findings informationally, while its documented
finding exit code 183 is distinguished from execution failures. Gitleaks still
fails on findings. Trivy still reports HIGH/CRITICAL findings informationally;
its native SARIF must be valid and present. Scorecard retains its existing
publication and scan policy, with Rust environment variables moved into the
other jobs to meet its [publication restrictions](https://github.com/ossf/scorecard-action/blob/2d1146689b8cda280b9bc96326124645441f03bc/README.md#workflow-restrictions).
No security exceptions, lint suppressions or ignored tests were added.

Local validation passed `make ci-local`, actual Rust 1.97.1 tests, package
verification, all 202 applicable API compatibility checks, action input
validation, actionlint, ShellCheck and YAML syntax/style checks. The seven
ordinary Rust tests and six coverage tests passed without failures or ignored
tests; the compatibility checker reported 58 inapplicable checks. Both current
secret scanners completed with zero findings against the fetched base history.
Cargo Deny retains informational unmatched license allowances because this
reusable template intentionally has no dependencies.

Release workflow triggers, inputs, outputs and ownership remain unchanged.
The previously broken crates.io publication polling heredoc now reads metadata
from a separate file. Releases, tags, registry uploads, signing, deployments
and crates.io publication were not executed. Hosted conclusions are recorded
in the pull request once those checks finish.
