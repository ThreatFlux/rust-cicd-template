#!/usr/bin/env python3

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


ROOT_MANIFEST = Path("Cargo.toml")
SKIP_DIRS = {".git", "target"}
RELEASE_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
VERIFIABLE_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+)?$")
DEPENDENCY_SECTION_PREFIXES = (
    "dependencies",
    "dev-dependencies",
    "build-dependencies",
)
PACKAGE_TABLES = {("package",), ("workspace", "package")}


def load_toml(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def workspace_member_manifests(root_manifest: Path) -> list[Path]:
    root = load_toml(root_manifest)
    workspace = root.get("workspace", {})
    manifests: list[Path] = [root_manifest]
    for pattern in workspace.get("members", []):
        for candidate in sorted(root_manifest.parent.glob(pattern)):
            manifest = candidate / "Cargo.toml" if candidate.is_dir() else candidate
            if manifest.is_file() and manifest not in manifests:
                manifests.append(manifest)
    return manifests


def package_names(manifests: list[Path]) -> set[str]:
    names: set[str] = set()
    for manifest in manifests:
        package = load_toml(manifest).get("package", {})
        name = package.get("name")
        if name:
            names.add(name)
    return names


def dependency_groups(manifest: dict) -> list[tuple[tuple[str, ...], dict]]:
    groups: list[tuple[tuple[str, ...], dict]] = []
    for scope_path, scope in (((), manifest), (("workspace",), manifest.get("workspace", {}))):
        for kind in DEPENDENCY_SECTION_PREFIXES:
            dependencies = scope.get(kind, {})
            if isinstance(dependencies, dict):
                groups.append((scope_path + (kind,), dependencies))
    for target_name, target in manifest.get("target", {}).items():
        for kind in DEPENDENCY_SECTION_PREFIXES:
            dependencies = target.get(kind, {})
            if isinstance(dependencies, dict):
                groups.append((("target", target_name, kind), dependencies))
    return groups


def internal_dependency_aliases(manifest: dict, internal_names: set[str]) -> dict[tuple[str, ...], set[str]]:
    aliases: dict[tuple[str, ...], set[str]] = {}
    for section, dependencies in dependency_groups(manifest):
        for alias, spec in dependencies.items():
            name = spec.get("package", alias) if isinstance(spec, dict) else alias
            version = spec.get("version") if isinstance(spec, dict) else spec
            if name in internal_names and isinstance(version, str):
                aliases.setdefault(section, set()).add(alias)
    return aliases


def current_version(root_manifest: Path) -> str:
    root = load_toml(root_manifest)
    package = root.get("package", {})
    if isinstance(package, dict) and isinstance(package.get("version"), str):
        return package["version"]
    workspace_pkg = root.get("workspace", {}).get("package", {})
    if isinstance(workspace_pkg, dict) and "version" in workspace_pkg:
        return workspace_pkg["version"]
    raise SystemExit("unable to determine current version from Cargo.toml")


TOML_KEY = r"""(?:[A-Za-z0-9_-]+|"(?:\\.|[^"\\])*"|'[^']*')"""
ASSIGNMENT = re.compile(rf"^[ \t]*(?P<key>{TOML_KEY}(?:[ \t]*\.[ \t]*{TOML_KEY})*)[ \t]*=[ \t]*")
STRING_VALUE = re.compile(r"""(?P<quote>["'])(?P<value>[^"'\r\n]*)(?P=quote)""")
INLINE_VERSION = re.compile(
    r"""(?:\{|,)[ \t]*(?:version|"version"|'version')[ \t]*=[ \t]*(?P<quote>["'])(?P<value>[^"'\r\n]*)(?P=quote)"""
)


def toml_key_path(raw_key: str) -> tuple[str, ...]:
    node = tomllib.loads(f"{raw_key} = 0")
    path: list[str] = []
    while isinstance(node, dict):
        key, node = next(iter(node.items()))
        path.append(key)
    return tuple(path)


def toml_section_path(line: str) -> tuple[str, ...] | None:
    header = line.strip()
    if not header.startswith("["):
        return None
    marker = "__release_version_section_marker__"
    try:
        node = tomllib.loads(f"{header}\n{marker} = true")
    except tomllib.TOMLDecodeError:
        return None

    def find_marker(value: object, path: tuple[str, ...]) -> tuple[str, ...] | None:
        if isinstance(value, dict):
            if marker in value:
                return path
            for key, child in value.items():
                found = find_marker(child, path + (key,))
                if found is not None:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = find_marker(child, path)
                if found is not None:
                    return found
        return None

    return find_marker(node, ())


def replace_string_value(line: str, start: int, new_version: str) -> str:
    match = STRING_VALUE.match(line, start)
    if match is None:
        return line
    return line[: match.start("value")] + new_version + line[match.end("value") :]


def replace_inline_version(line: str, start: int, new_version: str) -> str:
    end = line.find("}", start)
    match = INLINE_VERSION.search(line, start, end) if end >= 0 else None
    if match is None:
        return line
    return line[: match.start("value")] + new_version + line[match.end("value") :]


def replace_dependency_assignment(
    line: str, key: tuple[str, ...], start: int, aliases: set[str], new_version: str
) -> str:
    if len(key) == 1 and key[0] in aliases:
        if line[start:].startswith("{"):
            return replace_inline_version(line, start, new_version)
        return replace_string_value(line, start, new_version)
    if len(key) == 2 and key[0] in aliases and key[1] == "version":
        return replace_string_value(line, start, new_version)
    return line


def replace_manifest_assignment(
    line: str,
    section: tuple[str, ...],
    new_version: str,
    aliases: dict[tuple[str, ...], set[str]],
    dependency_tables: set[tuple[str, ...]],
) -> str:
    assignment = ASSIGNMENT.match(line)
    if assignment is None:
        return line
    key = toml_key_path(assignment["key"])
    start = assignment.end()
    if section in PACKAGE_TABLES or section in dependency_tables:
        return replace_string_value(line, start, new_version) if key == ("version",) else line
    if section in aliases:
        return replace_dependency_assignment(line, key, start, aliases[section], new_version)
    return line


def replace_manifest_versions(content: str, new_version: str, internal_names: set[str]) -> str:
    aliases = internal_dependency_aliases(tomllib.loads(content), internal_names)
    dependency_tables = {section + (alias,) for section, names in aliases.items() for alias in names}
    lines = content.splitlines(keepends=True)
    section: tuple[str, ...] = ()
    for idx, line in enumerate(lines):
        header = toml_section_path(line)
        if header is not None:
            section = header
        else:
            lines[idx] = replace_manifest_assignment(line, section, new_version, aliases, dependency_tables)
    return "".join(lines)


def update_manifest(path: Path, new_version: str, internal_names: set[str]) -> bool:
    original = path.read_text(encoding="utf-8")
    content = replace_manifest_versions(original, new_version, internal_names)
    if content != original:
        path.write_text(content, encoding="utf-8")
        return True
    return False


def update_lockfile(path: Path, new_version: str, internal_names: set[str]) -> bool:
    if not path.is_file():
        return False
    original = path.read_text(encoding="utf-8")
    blocks = re.split(r"(?m)(?=^[ \t]*\[\[[ \t]*package[ \t]*\]\][ \t]*(?:#.*)?$)", original)
    packages = [tomllib.loads(block).get("package", []) for block in blocks]
    local_refs = {
        f"{package['name']} {package['version']}": f"{package['name']} {new_version}"
        for group in packages
        for package in group
        if package.get("name") in internal_names and "source" not in package
    }
    registry_refs = {
        f"{package['name']} {package['version']}"
        for group in packages
        for package in group
        if "source" in package
    }
    for idx, block in enumerate(blocks):
        if not packages[idx]:
            continue
        package = packages[idx][0]
        if package.get("name") in internal_names and "source" not in package:
            block, count = re.subn(
                r'(?m)^([ \t]*version[ \t]*=[ \t]*)(["\'])([^"\'\r\n]+)\2',
                lambda match: f"{match[1]}{match[2]}{new_version}{match[2]}",
                block,
                count=1,
            )
            if count != 1:
                raise SystemExit(f"{path} has no version for {package['name']}")
        for dependency in package.get("dependencies", []):
            if dependency not in local_refs:
                continue
            if dependency in registry_refs:
                raise SystemExit(f"{path} has ambiguous local/registry dependency {dependency}")
            old_ref = f'"{dependency}"'
            if block.count(old_ref) != 1:
                raise SystemExit(f"{path} cannot locate dependency reference {dependency}")
            block = block.replace(old_ref, f'"{local_refs[dependency]}"')
        blocks[idx] = block
    updated = "".join(blocks)
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def set_version(root_manifest: Path, new_version: str) -> int:
    if not RELEASE_VERSION.fullmatch(new_version):
        raise SystemExit("release version must be MAJOR.MINOR.PATCH")
    manifests = workspace_member_manifests(root_manifest)
    internal_names = package_names(manifests)
    changed = False
    for manifest in manifests:
        if any(part in SKIP_DIRS for part in manifest.parts):
            continue
        changed = update_manifest(manifest, new_version, internal_names) or changed
    changed = update_lockfile(root_manifest.parent / "Cargo.lock", new_version, internal_names) or changed
    # cargo check --workspace does not refresh the separate fuzz workspace lockfile.
    changed = update_lockfile(root_manifest.parent / "fuzz" / "Cargo.lock", new_version, internal_names) or changed
    if not changed:
        raise SystemExit("no Cargo.toml or Cargo.lock files were updated")
    return 0


def verify_package_versions(manifest: Path, data: dict, expected: str) -> None:
    for package in (data.get("package", {}), data.get("workspace", {}).get("package", {})):
        version = package.get("version")
        if isinstance(version, str) and version != expected:
            raise SystemExit(f"{manifest} has package version {version}, expected {expected}")


def verify_dependency_versions(manifest: Path, data: dict, expected: str, internal_names: set[str]) -> None:
    for _, dependencies in dependency_groups(data):
        for alias, spec in dependencies.items():
            name = spec.get("package", alias) if isinstance(spec, dict) else alias
            if name not in internal_names:
                continue
            version = spec.get("version") if isinstance(spec, dict) else spec
            if version is not None and version != expected:
                raise SystemExit(
                    f"{manifest} has internal dependency {alias} at {version}, expected {expected}"
                )


def verify_lockfile_versions(lockfile: Path, expected: str, internal_names: set[str]) -> None:
    if not lockfile.is_file():
        return
    for package in load_toml(lockfile).get("package", []):
        if (
            package.get("name") in internal_names
            and "source" not in package
            and package.get("version") != expected
        ):
            raise SystemExit(f"{lockfile} has {package['name']} at {package.get('version')}, expected {expected}")


def verify_version(root_manifest: Path, expected: str) -> int:
    """Check the reviewed tree without changing it before making a release tag."""
    if not VERIFIABLE_VERSION.fullmatch(expected):
        raise SystemExit("release version must be MAJOR.MINOR.PATCH with an optional pre-release suffix")
    if current_version(root_manifest) != expected:
        raise SystemExit(f"Cargo.toml does not declare release version {expected}")

    manifests = workspace_member_manifests(root_manifest)
    internal_names = package_names(manifests)
    for manifest in manifests:
        data = load_toml(manifest)
        verify_package_versions(manifest, data, expected)
        verify_dependency_versions(manifest, data, expected, internal_names)

    for lockfile in (root_manifest.parent / "Cargo.lock", root_manifest.parent / "fuzz" / "Cargo.lock"):
        verify_lockfile_versions(lockfile, expected, internal_names)
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        raise SystemExit("usage: release_version.py <current|set|verify> [version]")
    command = argv[1]
    if command == "current":
        print(current_version(ROOT_MANIFEST))
        return 0
    if command == "set":
        if len(argv) != 3:
            raise SystemExit("usage: release_version.py set <version>")
        return set_version(ROOT_MANIFEST, argv[2])
    if command == "verify":
        if len(argv) != 3:
            raise SystemExit("usage: release_version.py verify <version>")
        return verify_version(ROOT_MANIFEST, argv[2])
    raise SystemExit(f"unknown command: {command}")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
