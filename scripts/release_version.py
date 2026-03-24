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
DEPENDENCY_SECTION_PREFIXES = (
    "dependencies",
    "dev-dependencies",
    "build-dependencies",
)


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


def current_version(root_manifest: Path) -> str:
    root = load_toml(root_manifest)
    package = root.get("package", {})
    if isinstance(package, dict) and "version" in package:
        return package["version"]
    workspace_pkg = root.get("workspace", {}).get("package", {})
    if isinstance(workspace_pkg, dict) and "version" in workspace_pkg:
        return workspace_pkg["version"]
    raise SystemExit("unable to determine current version from Cargo.toml")


def replace_scoped_version(content: str, header: str, new_version: str) -> tuple[str, int]:
    lines = content.splitlines(keepends=True)
    in_section = False
    replacements = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_section = stripped == f"[{header}]"
            continue
        if in_section and re.match(r'^version\s*=\s*"[^"]+"', stripped):
            prefix = line[: len(line) - len(line.lstrip())]
            suffix = "\n" if line.endswith("\n") else ""
            lines[idx] = f'{prefix}version = "{new_version}"{suffix}'
            replacements += 1
            in_section = False
    return "".join(lines), replacements


def replace_inline_dependency_versions(content: str, internal_names: set[str], new_version: str) -> tuple[str, int]:
    replacements = 0
    for name in sorted(internal_names):
        pattern = re.compile(
            rf'(?m)^(\s*{re.escape(name)}\s*=\s*\{{[^#\n]*?\bversion\s*=\s*")([^"]+)(")',
        )
        content, count = pattern.subn(rf"\g<1>{new_version}\g<3>", content)
        replacements += count
    return content, replacements


def replace_table_dependency_versions(content: str, internal_names: set[str], new_version: str) -> tuple[str, int]:
    lines = content.splitlines(keepends=True)
    section: str | None = None
    replacements = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1]
            continue
        if section is None or "." not in section:
            continue
        prefix, name = section.rsplit(".", 1)
        if prefix not in DEPENDENCY_SECTION_PREFIXES and not any(
            prefix.endswith(f".{dep_prefix}") for dep_prefix in DEPENDENCY_SECTION_PREFIXES
        ):
            continue
        if name not in internal_names:
            continue
        if re.match(r'^version\s*=\s*"[^"]+"', stripped):
            indent = line[: len(line) - len(line.lstrip())]
            suffix = "\n" if line.endswith("\n") else ""
            lines[idx] = f'{indent}version = "{new_version}"{suffix}'
            replacements += 1
    return "".join(lines), replacements


def update_manifest(path: Path, new_version: str, internal_names: set[str]) -> bool:
    original = path.read_text(encoding="utf-8")
    content = original
    content, _ = replace_scoped_version(content, "package", new_version)
    content, _ = replace_scoped_version(content, "workspace.package", new_version)
    content, _ = replace_inline_dependency_versions(content, internal_names, new_version)
    content, _ = replace_table_dependency_versions(content, internal_names, new_version)
    if content != original:
        path.write_text(content, encoding="utf-8")
        return True
    return False


def set_version(root_manifest: Path, new_version: str) -> int:
    manifests = workspace_member_manifests(root_manifest)
    internal_names = package_names(manifests)
    changed = False
    for manifest in manifests:
        if any(part in SKIP_DIRS for part in manifest.parts):
            continue
        changed = update_manifest(manifest, new_version, internal_names) or changed
    if not changed:
        raise SystemExit("no Cargo.toml files were updated")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        raise SystemExit("usage: release_version.py <current|set> [version]")
    command = argv[1]
    if command == "current":
        print(current_version(ROOT_MANIFEST))
        return 0
    if command == "set":
        if len(argv) != 3:
            raise SystemExit("usage: release_version.py set <version>")
        return set_version(ROOT_MANIFEST, argv[2])
    raise SystemExit(f"unknown command: {command}")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
