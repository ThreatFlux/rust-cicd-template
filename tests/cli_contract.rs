//! Process-level tests for the template CLI contract.

use std::process::Command;

#[test]
fn unknown_argument_exits_unsuccessfully() {
    let output = Command::new(env!("CARGO_BIN_EXE_rust-cicd-template"))
        .arg("--not-a-real-option")
        .output()
        .expect("template binary should execute");

    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("unrecognised argument"));
}
