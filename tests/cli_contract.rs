//! Process-level tests for the template CLI contract.

use std::process::{Command, Output};

fn run_with(argument: &str) -> Output {
    Command::new(env!("CARGO_BIN_EXE_rust-cicd-template"))
        .arg(argument)
        .output()
        .expect("template binary should execute")
}

#[test]
fn version_exits_successfully() {
    let output = run_with("--version");
    let stdout = String::from_utf8(output.stdout).expect("version output should be UTF-8");

    assert!(output.status.success());
    assert_eq!(
        stdout.trim_end(),
        format!("{} {}", env!("CARGO_PKG_NAME"), env!("CARGO_PKG_VERSION"))
    );
    assert!(output.stderr.is_empty());
}

#[test]
fn help_exits_successfully() {
    let output = run_with("--help");
    let stdout = String::from_utf8(output.stdout).expect("help output should be UTF-8");

    assert!(output.status.success());
    assert!(stdout.contains("USAGE:"));
    assert!(stdout.contains("--version"));
    assert!(output.stderr.is_empty());
}

#[test]
fn unknown_argument_exits_unsuccessfully() {
    let output = run_with("--not-a-real-option");

    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("unrecognised argument"));
}
