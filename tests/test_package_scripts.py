from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "visual-brief"
VALIDATE = SKILL / "scripts" / "validate_package.py"
RENDER = SKILL / "scripts" / "render_preview.py"
SLACK_DRAFT = SKILL / "scripts" / "create_slack_draft.py"


class PackageScriptTests(unittest.TestCase):
    def copy_example(self, name: str, directory: Path) -> Path:
        target = directory / name
        shutil.copytree(ROOT / "examples" / name, target)
        return target

    def test_sanitized_examples_validate_and_render(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for name in (
                "sanitized-evidence-reply",
                "sanitized-visual-procedure",
                "sanitized-public-explainer",
            ):
                package = self.copy_example(name, directory)
                validation = subprocess.run(
                    [sys.executable, str(VALIDATE), "--package", str(package)],
                    text=True,
                    capture_output=True,
                    check=True,
                )
                report = json.loads(validation.stdout)
                self.assertTrue(report["passed"])
                self.assertTrue(report["warnings"])
                preview = package / "preview" / "index.html"
                render = subprocess.run(
                    [sys.executable, str(RENDER), "--package", str(package)],
                    text=True,
                    capture_output=True,
                    check=True,
                )
                self.assertTrue(preview.is_file())
                self.assertIn("output", json.loads(render.stdout))
                self.assertIn("本地预览", preview.read_text(encoding="utf-8"))

    def test_strict_rejects_fixture_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = self.copy_example("sanitized-evidence-reply", Path(temporary))
            result = subprocess.run(
                [sys.executable, str(VALIDATE), "--package", str(package), "--strict"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("fixture", result.stdout)

    def test_rejects_sensitive_url_and_generated_factual_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = self.copy_example("sanitized-public-explainer", Path(temporary))
            manifest_path = package / "source-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["sources"][0]["url"] += "?token=should-not-be-here"
            manifest["claims"][0]["asset_ids"].append("A-2")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATE), "--package", str(package)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("sensitive-looking query", result.stdout)
            self.assertIn("cannot use generated asset", result.stdout)

    def test_rejects_generated_asset_attached_to_factual_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = self.copy_example("sanitized-public-explainer", Path(temporary))
            manifest_path = package / "source-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["assets"][1]["claim_ids"] = ["C-1"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATE), "--package", str(package)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("can only attach to an illustrative claim", result.stdout)

    def test_rejects_browser_state_inside_package(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = self.copy_example("sanitized-evidence-reply", Path(temporary))
            (package / "storage-state.json").write_text('{"cookies": []}', encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATE), "--package", str(package)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("forbidden credential-like filename", result.stdout)

    def test_creates_local_only_slack_draft(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = self.copy_example("sanitized-evidence-reply", Path(temporary))
            output = package / "packages" / "new-slack-block-kit.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SLACK_DRAFT),
                    "--package",
                    str(package),
                    "--summary",
                    "Synthetic fixture only.",
                    "--output",
                    str(output),
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertFalse(json.loads(result.stdout)["sent"])
            self.assertTrue(output.is_file())


if __name__ == "__main__":
    unittest.main()
