#!/usr/bin/env python3

from pathlib import Path
import sys


PLACEHOLDERS = {
    "PROJECT_NAME",
    "PROJECT_DESCRIPTION",
    "YOUR_USERNAME",
    "PROJECT_REPOSITORY",
}

SKIP_DIRS = {
    ".git",
    "target",
}

SKIP_FILES = {
    "README_TEMPLATE.md",
    "docs/TEMPLATE_BOOTSTRAP_CHECKLIST.md",
    "scripts/check_template_placeholders.py",
}


def main() -> int:
    matches = []
    for path in Path(".").rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        rel = path.as_posix()
        if rel in SKIP_FILES:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for placeholder in PLACEHOLDERS:
            if placeholder in content:
                matches.append((rel, placeholder))

    if matches:
        print("Unresolved template placeholders found:")
        for rel, placeholder in matches:
            print(f"  {rel}: {placeholder}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
