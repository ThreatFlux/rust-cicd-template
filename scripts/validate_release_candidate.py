#!/usr/bin/env python3
"""Validate a release candidate's Cargo data against the checked-out main commit.

Run this file from the trusted main checkout. Candidate files are read as Git
objects and parsed as data; the candidate tree is never checked out or run.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
# B404: git reads commit objects as data using argument lists, never a shell.
import subprocess  # nosec B404
import tomllib
from pathlib import Path

from release_version import dependency_groups, workspace_member_manifests


SHA = re.compile(r"[0-9a-f]{40}\Z")
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\Z")
LOCKFILES = ("Cargo.lock", "fuzz/Cargo.lock")


def git(*args: str) -> bytes:
    # B603/B607: fixed git subcommands, validated commit IDs, and no shell.
    return subprocess.run(  # nosec B603, B607
        ["git", *args], check=True, capture_output=True, shell=False
    ).stdout


def blob(commit: str, path: str) -> bytes | None:
    # B603/B607: read a Git object by validated commit ID and path, without a shell.
    result = subprocess.run(  # nosec B603, B607
        ["git", "show", f"{commit}:{path}"], capture_output=True, shell=False
    )
    if result.returncode:
        return None
    return result.stdout


def parse_toml(data: bytes, label: str) -> dict:
    try:
        value = tomllib.loads(data.decode("utf-8"))
    except (UnicodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"{label} is not valid TOML: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} is not a TOML table")
    return value


def manifest(commit: str, path: str) -> dict:
    data = blob(commit, path)
    if data is None:
        raise ValueError(f"{path} must exist in both main and candidate")
    return parse_toml(data, f"{commit}:{path}")


def package_versions(base: str, root: dict) -> tuple[set[str], dict[str, str]]:
    paths = {path.as_posix() for path in workspace_member_manifests(Path("Cargo.toml"))}
    versions: dict[str, str] = {}
    inherited = root.get("workspace", {}).get("package", {}).get("version")
    for path in paths:
        package = manifest(base, path).get("package", {})
        if not isinstance(package, dict):
            raise ValueError(f"{path} has no valid package table")
        name = package.get("name")
        version = package.get("version")
        if isinstance(version, dict) and version.get("workspace") is True:
            version = inherited
        if name is not None:
            if not isinstance(name, str) or not isinstance(version, str):
                raise ValueError(f"{path} has no concrete package name and version")
            if name in versions and versions[name] != version:
                raise ValueError(f"{name} has conflicting versions in main")
            versions[name] = version
    return paths, versions


def expected_manifest(
    original: dict, path: str, package_paths: set[str], versions: dict[str, str], next_version: str
) -> dict:
    expected = copy.deepcopy(original)
    if path in package_paths:
        package = expected.get("package", {})
        if isinstance(package, dict) and isinstance(package.get("version"), str):
            package["version"] = next_version
        workspace_package = expected.get("workspace", {}).get("package", {})
        if isinstance(workspace_package, dict) and isinstance(workspace_package.get("version"), str):
            workspace_package["version"] = next_version
    for _, dependencies in dependency_groups(expected):
        for alias, spec in dependencies.items():
            if not isinstance(spec, dict) or not isinstance(spec.get("path"), str):
                continue
            name = spec.get("package", alias)
            if isinstance(name, str) and name in versions and isinstance(spec.get("version"), str):
                spec["version"] = next_version
    return expected


def local_lock_packages(packages: list[dict], versions: dict[str, str]) -> tuple[dict[str, int], set[str]]:
    counts: dict[str, int] = {}
    local_names: set[str] = set()
    for package in packages:
        name = package.get("name")
        if not isinstance(name, str) or not isinstance(package.get("version"), str):
            raise ValueError("Cargo.lock has a package without a name and version")
        counts[name] = counts.get(name, 0) + 1
        if name in versions and "source" not in package:
            local_names.add(name)
    return counts, local_names


def canonical_lock_dependency(
    dependency: str,
    expected_versions: dict[str, str],
    counts: dict[str, int],
    local_names: set[str],
) -> str:
    for local_name in local_names:
        qualified = f"{local_name} {expected_versions[local_name]}"
        if dependency == qualified or (counts.get(local_name) == 1 and dependency == local_name):
            return f"{local_name} <local>"
    return dependency


def normalize_lock_package(
    package: dict,
    expected_versions: dict[str, str],
    next_version: str,
    counts: dict[str, int],
    local_names: set[str],
) -> None:
    name = package.get("name")
    if name in local_names and "source" not in package:
        expected = expected_versions[name]
        if package.get("version") != expected:
            raise ValueError(f"local lock package {name} has unexpected version {package.get('version')}")
        package["version"] = next_version
    dependencies = package.get("dependencies")
    if dependencies is None:
        return
    if not isinstance(dependencies, list) or not all(isinstance(item, str) for item in dependencies):
        raise ValueError("Cargo.lock has invalid package dependencies")
    package["dependencies"] = sorted(
        canonical_lock_dependency(dependency, expected_versions, counts, local_names)
        for dependency in dependencies
    )


def normalize_lock(lock: dict, versions: dict[str, str], next_version: str, *, is_base: bool) -> dict:
    normalized = copy.deepcopy(lock)
    packages = normalized.pop("package", None)
    if not isinstance(packages, list) or not all(isinstance(item, dict) for item in packages):
        raise ValueError("Cargo.lock must contain package tables")
    counts, local_names = local_lock_packages(packages, versions)
    expected_versions = versions if is_base else dict.fromkeys(versions, next_version)
    for package in packages:
        normalize_lock_package(package, expected_versions, next_version, counts, local_names)
    normalized["package"] = sorted(packages, key=lambda item: json.dumps(item, sort_keys=True))
    return normalized


def validate_commits_and_version(base: str, candidate: str, next_version: str) -> None:
    if not SHA.fullmatch(base) or not SHA.fullmatch(candidate) or not VERSION.fullmatch(next_version):
        raise ValueError("expected full SHA-1 commits and a MAJOR.MINOR.PATCH version")
    if git("rev-parse", "HEAD").decode().strip() != base:
        raise ValueError("validator must run from the trusted main checkout")


def validate_root_version(root: dict, next_version: str) -> None:
    current = root.get("package", {}).get("version")
    if not isinstance(current, str):
        current = root.get("workspace", {}).get("package", {}).get("version")
    if not isinstance(current, str) or current == next_version:
        raise ValueError("candidate must change the root package version")


def changed_candidate_manifests(base: str, candidate: str) -> set[str]:
    changes = git("diff", "--name-only", "-z", base, candidate).decode("utf-8").split("\0")
    changed_manifests: set[str] = set()
    for path in filter(None, changes):
        if path == "Cargo.toml" or path.endswith("/Cargo.toml"):
            changed_manifests.add(path)
        elif path not in LOCKFILES:
            raise ValueError(f"candidate changes non-release file {path}")
    return changed_manifests


def validate_manifests(
    base: str,
    candidate: str,
    next_version: str,
    root: dict,
) -> dict[str, str]:
    package_paths, versions = package_versions(base, root)
    changed_manifests = changed_candidate_manifests(base, candidate)
    for path in package_paths | changed_manifests:
        original = manifest(base, path)
        actual = manifest(candidate, path)
        if actual != expected_manifest(original, path, package_paths, versions, next_version):
            raise ValueError(f"{path} changes fields other than expected package/path dependency versions")
    return versions


def validate_lockfiles(base: str, candidate: str, next_version: str, versions: dict[str, str]) -> None:
    for path in LOCKFILES:
        original_blob = blob(base, path)
        candidate_blob = blob(candidate, path)
        if (original_blob is None) != (candidate_blob is None):
            raise ValueError(f"{path} cannot be added or removed by a release candidate")
        if original_blob is None:
            continue
        original = parse_toml(original_blob, f"{base}:{path}")
        actual = parse_toml(candidate_blob, f"{candidate}:{path}")
        if normalize_lock(original, versions, next_version, is_base=True) != normalize_lock(
            actual, versions, next_version, is_base=False
        ):
            raise ValueError(f"{path} changes package data beyond local versions/dependency references")


def validate(base: str, candidate: str, next_version: str) -> None:
    validate_commits_and_version(base, candidate, next_version)
    root = manifest(base, "Cargo.toml")
    validate_root_version(root, next_version)
    versions = validate_manifests(base, candidate, next_version, root)
    validate_lockfiles(base, candidate, next_version, versions)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    try:
        validate(args.base, args.candidate, args.version)
    except (ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"release candidate rejected: {error}\n")
    print(f"Validated version-only release candidate {args.candidate} from {args.base}.")


if __name__ == "__main__":
    main()
