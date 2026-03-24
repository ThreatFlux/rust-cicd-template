#!/usr/bin/env python3

from pathlib import Path
import sys


PLACEHOLDERS = {
    "PROJECT_NAME",
    "PROJECT_DESCRIPTION",
    "YOUR_USERNAME",
    "PROJECT_REPOSITORY",
    "TEMPLATE_GITHUB_OWNER",
    "BRIEF_VALUE_PROPOSITION",
    "REPLACE_WITH_REAL_API",
}

SKIP_DIRS = {
    ".git",
    "target",
}

SKIP_FILES = {
    "README_TEMPLATE.md",
    "docs/TEMPLATE_BOOTSTRAP_CHECKLIST.md",
    "docs/FAQ.md",
    "docs/README_STANDARDS.md",
    "scripts/check_template_placeholders.py",
}

DOWNSTREAM_BLOCKERS = (
    (
        Path("README.md"),
        "# ThreatFlux Rust Project Template",
        "README.md still contains the template repository README; promote and customize README_TEMPLATE.md",
    ),
)


def is_canonical_template_repo() -> bool:
    cargo_toml = Path("Cargo.toml")
    if not cargo_toml.exists():
        return False
    try:
        content = cargo_toml.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False
    return (
        'name = "rust-cicd-template"' in content
        and "ThreatFlux/rust-cicd-template" in content
    )


def main() -> int:
    matches = []
    blockers = []
    canonical_template_repo = is_canonical_template_repo()

    if not canonical_template_repo and Path("README_TEMPLATE.md").exists():
        blockers.append(
            "README_TEMPLATE.md is still present; copy its contents into README.md, customize it, and remove README_TEMPLATE.md"
        )

    if not canonical_template_repo:
        for path, marker, message in DOWNSTREAM_BLOCKERS:
            if path.exists():
                try:
                    content = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                if marker in content:
                    blockers.append(message)

    for path in Path(".").rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        rel = path.as_posix()
        if rel in SKIP_FILES:
            continue
        if canonical_template_repo and rel == ".github/CODEOWNERS":
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for placeholder in PLACEHOLDERS:
            if placeholder in content:
                matches.append((rel, placeholder))

    if blockers or matches:
        if blockers:
            print("Repository bootstrap issues found:")
            for blocker in blockers:
                print(f"  - {blocker}")
        if matches:
            print("Unresolved template placeholders found:")
            for rel, placeholder in matches:
                print(f"  {rel}: {placeholder}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
