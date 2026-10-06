#!/usr/bin/env python3
"""Write the GitHub Release notes for a version.

The notes start with a "## Release vVERSION" heading. Their body is the
"## [VERSION]" section of CHANGELOG.md or docs/CHANGELOG.md when one exists;
otherwise it lists the commits since the previous release tag, grouped by
Conventional Commit type. A "Full Changelog" compare link to the previous
release tag ends the notes.

Run it from a checkout with full history and tags (fetch-depth: 0). HEAD is the
commit being released or the release commit itself; "chore: release vX.Y.Z"
commits are left out of the commit list either way.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

CHANGELOG_CANDIDATES = (Path("CHANGELOG.md"), Path("docs/CHANGELOG.md"))
TAG_PATTERN = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
SUBJECT_PATTERN = re.compile(r"^(?P<type>[A-Za-z][A-Za-z0-9-]*)(?:\([^)]*\))?(?P<bang>!)?: ")
RELEASE_COMMIT_PATTERN = re.compile(r"^chore: release v\d")
BREAKING_FOOTER_PATTERN = re.compile(r"^BREAKING[ -]CHANGE: ", re.MULTILINE)
SECTIONS = (
    ("breaking", "Breaking Changes"),
    ("feat", "Features"),
    ("fix", "Bug Fixes"),
    ("other", "Other Changes"),
)


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout


def version_key(version: str) -> tuple[int, int, int] | None:
    match = TAG_PATTERN.match(f"v{version}")
    if not match:
        return None
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def previous_tag(version: str) -> str | None:
    """The highest vX.Y.Z tag reachable from HEAD that is lower than VERSION."""
    current = version_key(version.split("-", 1)[0])
    candidates = []
    for tag in git("tag", "--merged", "HEAD", "--list", "v*").split():
        match = TAG_PATTERN.match(tag)
        if not match:
            continue
        key = tuple(int(part) for part in match.groups())
        if current is None or key < current:
            candidates.append((key, tag))
    return max(candidates)[1] if candidates else None


def changelog_section(version: str) -> tuple[Path, str] | None:
    """The body of the first "## [VERSION]" section, without surrounding blank lines."""
    header = f"## [{version}]"
    for path in CHANGELOG_CANDIDATES:
        if not path.is_file():
            continue
        body: list[str] = []
        found = False
        for line in path.read_text(encoding="utf-8").splitlines():
            if not found:
                found = line.startswith(header)
                continue
            if line.startswith("## ") or re.match(r"^\[[^\]]+\]: ", line):
                break
            body.append(line)
        text = "\n".join(body).strip("\n")
        if found and text.strip():
            return path, text
    return None


def commit_list(since: str | None) -> tuple[int, str]:
    """Commits in since..HEAD (all of HEAD's history without a tag), grouped by type."""
    revision = f"{since}..HEAD" if since else "HEAD"
    log = git("log", "--no-merges", "--format=%h%x1f%s%x1f%b%x1e", revision)
    groups: dict[str, list[str]] = {key: [] for key, _ in SECTIONS}
    count = 0
    for record in log.split("\x1e"):
        record = record.strip("\n")
        if not record:
            continue
        short_sha, subject, body = (record.split("\x1f") + ["", ""])[:3]
        if RELEASE_COMMIT_PATTERN.match(subject):
            continue
        count += 1
        match = SUBJECT_PATTERN.match(subject)
        commit_type = match.group("type").lower() if match else ""
        if (match and match.group("bang")) or BREAKING_FOOTER_PATTERN.search(body):
            group = "breaking"
        elif commit_type in ("feat", "fix"):
            group = commit_type
        else:
            group = "other"
        groups[group].append(f"- {subject} ({short_sha})")

    parts = []
    for key, title in SECTIONS:
        if groups[key]:
            parts.append(f"### {title}\n\n" + "\n".join(groups[key]))
    return count, "\n\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("version", help="version being released, without the leading v")
    parser.add_argument("--output", type=Path, help="write the notes here instead of stdout")
    args = parser.parse_args()

    version = args.version.removeprefix("v")
    previous = previous_tag(version)
    since = previous or "the first commit"

    section = changelog_section(version)
    if section:
        path, body = section
        source = f"the [{version}] section of {path}"
    else:
        count, body = commit_list(previous)
        source = f"{count} commit(s) since {since}"
        if not body:
            body = f"No changes since {since}."

    notes = f"## Release v{version}\n\n{body}\n"
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if previous and repository:
        server = os.environ.get("GITHUB_SERVER_URL", "https://github.com").rstrip("/")
        notes += f"\n**Full Changelog**: {server}/{repository}/compare/{previous}...v{version}\n"

    if args.output:
        args.output.write_text(notes, encoding="utf-8")
    else:
        sys.stdout.write(notes)
    print(f"Release notes for v{version} come from {source}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
