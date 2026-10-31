"""Regression cases for the reviewed release candidate's lockfile edits."""

from __future__ import annotations

import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from release_version import update_lockfile  # noqa: E402


class UpdateLockfileTests(unittest.TestCase):
    def test_qualified_local_reference_changes_without_touching_registry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Cargo.lock"
            path.write_text(
                '''version = 4

[[package]]
name = "helper"
version = "0.1.0"

[[package]]
name = "helper"
version = "0.9.0"
source = "registry+https://github.com/rust-lang/crates.io-index"

[[package]]
name = "app"
version = "0.1.0"
dependencies = ["helper 0.1.0", "helper 0.9.0"]
''',
                encoding="utf-8",
            )

            self.assertTrue(update_lockfile(path, "1.2.3", {"app", "helper"}))

            packages = tomllib.loads(path.read_text(encoding="utf-8"))["package"]
            self.assertEqual(packages[0]["version"], "1.2.3")
            self.assertEqual(packages[1]["version"], "0.9.0")
            self.assertEqual(packages[2]["version"], "1.2.3")
            self.assertEqual(packages[2]["dependencies"], ["helper 1.2.3", "helper 0.9.0"])

    def test_ambiguous_local_and_registry_reference_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Cargo.lock"
            path.write_text(
                '''version = 4

[[package]]
name = "helper"
version = "0.1.0"

[[package]]
name = "helper"
version = "0.1.0"
source = "registry+https://github.com/rust-lang/crates.io-index"

[[package]]
name = "app"
version = "0.1.0"
dependencies = ["helper 0.1.0"]
''',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(SystemExit, "ambiguous local/registry dependency"):
                update_lockfile(path, "1.2.3", {"app", "helper"})


if __name__ == "__main__":
    unittest.main()
