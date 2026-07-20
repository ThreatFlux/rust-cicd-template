//! `ThreatFlux` Rust CI/CD Template
//!
//! Minimal example binary demonstrating the CLI contract every `ThreatFlux`
//! Rust tool is expected to honour:
//!
//!   * `--version` / `-V` prints the version and exits 0. The container
//!     HEALTHCHECK invokes this, so it must stay cheap and side-effect free.
//!   * `--help` / `-h` prints usage and exits 0.
//!   * An unrecognised argument prints usage to stderr and exits non-zero.
//!
//! Implemented without a CLI crate on purpose: this template carries no
//! dependencies, and the contract is small enough not to need one. Real tools
//! are free to use clap so long as the three behaviours above are preserved.

use std::process::ExitCode;

const NAME: &str = env!("CARGO_PKG_NAME");
const VERSION: &str = env!("CARGO_PKG_VERSION");
const DESCRIPTION: &str = env!("CARGO_PKG_DESCRIPTION");

fn usage() -> String {
    format!(
        "{NAME} {VERSION}\n\
         {DESCRIPTION}\n\
         \n\
         USAGE:\n    \
             {NAME} [OPTIONS]\n\
         \n\
         OPTIONS:\n    \
             -h, --help       Print this help and exit\n    \
             -V, --version    Print the version and exit\n"
    )
}

fn main() -> ExitCode {
    // Only post-argv[0] values select ordinary CLI output; no authorization or
    // other security decision depends on process arguments.
    // nosemgrep: rust.lang.security.args.args
    let args: Vec<String> = std::env::args().skip(1).collect();

    match args.first().map(String::as_str) {
        // Bare invocation behaves as --version so the HEALTHCHECK stays valid
        // even if a repo overrides CMD.
        None | Some("-V" | "--version") => {
            println!("{NAME} {VERSION}");
            ExitCode::SUCCESS
        }
        Some("-h" | "--help") => {
            print!("{}", usage());
            ExitCode::SUCCESS
        }
        Some(unknown) => {
            eprintln!("error: unrecognised argument '{unknown}'\n");
            eprint!("{}", usage());
            ExitCode::FAILURE
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn usage_mentions_both_flags() {
        let text = usage();
        assert!(text.contains("--version"));
        assert!(text.contains("--help"));
    }

    #[test]
    fn usage_reports_package_identity() {
        let text = usage();
        assert!(text.contains(NAME));
        assert!(text.contains(VERSION));
    }
}
