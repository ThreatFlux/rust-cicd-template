#!/usr/bin/env python3
"""Choose floating container tags from fresh refs inside the serialized publisher."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

STABLE = re.compile(r"^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
SHA = re.compile(r"^[0-9a-f]{40}$")


def validate_release(ref: str, version: str) -> None:
    """A Docker tag must identify the version actually compiled from Cargo."""
    if ref.startswith("refs/tags/") and ref != f"refs/tags/v{version}":
        raise ValueError("release tag does not match the checked-out Cargo version")


def aliases(ref: str, source: str, main: str, tags: list[dict]) -> dict:
    """Historical retries publish their immutable tags but never rewind aliases."""
    if not SHA.fullmatch(source) or not SHA.fullmatch(main):
        raise ValueError("expected full source and main commit SHAs")
    stable = []
    for tag in tags:
        match = STABLE.fullmatch(tag["name"])
        if match:
            stable.append((tuple(map(int, match.groups())), tag))
    newest = max(stable, key=lambda item: item[0])[1] if stable else None
    candidate = (
        STABLE.fullmatch(ref.removeprefix("refs/tags/"))
        if ref.startswith("refs/tags/")
        else None
    )
    matched_tag = candidate is not None and any(
        ref == "refs/tags/" + tag["name"] and tag["commit"]["sha"] == source
        for _, tag in stable
    )
    current_main = source == main and (ref == "refs/heads/main" or matched_tag)
    current_stable = (
        newest is not None
        and ref == "refs/tags/" + newest["name"]
        and newest["commit"]["sha"] == source
    )
    runtime = ["main", "latest"] if current_main else []
    if matched_tag:
        version = tuple(map(int, candidate.groups()))
        major_line = [number for number, _ in stable if number[0] == version[0]]
        minor_line = [number for number, _ in stable if number[:2] == version[:2]]
        if version == max(minor_line):
            runtime.append(f"{version[0]}.{version[1]}")
        if version == max(major_line):
            runtime.append(str(version[0]))
    return {"runtime": runtime, "base": bool(current_main or current_stable)}


def api(path: str, *, pages: bool = False):
    command = ["gh", "api", path]
    if pages:
        command.extend(["--paginate", "--slurp"])
    value = json.loads(subprocess.check_output(command, text=True))
    return [item for page in value for item in page] if pages else value


def require_main_ancestry(source: str, head: str, comparison: str) -> None:
    """Version images must come from accepted main history, including retries."""
    if not SHA.fullmatch(source) or not SHA.fullmatch(head):
        raise ValueError("expected full source and main commit SHAs")
    if comparison not in {"ahead", "identical"}:
        raise ValueError("container source is outside accepted main history")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    ref = os.environ["GITHUB_REF"]
    from release_version import current_version

    validate_release(ref, current_version(Path("Cargo.toml")))
    if args.validate and not ref.startswith("refs/tags/"):
        return
    repository = os.environ["GITHUB_REPOSITORY"]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("invalid repository")
    source = os.environ["GITHUB_SHA"]
    head = api(f"repos/{repository}/commits/main")["sha"]
    if not SHA.fullmatch(source) or not SHA.fullmatch(head):
        raise ValueError("expected full source and main commit SHAs")
    comparison = api(f"repos/{repository}/compare/{source}...{head}")["status"]
    require_main_ancestry(source, head, comparison)
    if args.validate:
        return
    # Tags are paginated and sorted numerically; API listing order is not semver.
    tags = api(f"repos/{repository}/tags?per_page=100", pages=True)
    print(json.dumps(aliases(ref, source, head, tags), separators=(",", ":")))


if __name__ == "__main__":
    main()
