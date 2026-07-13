from __future__ import annotations

import http.server
import json
import os
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "visual-brief"
CAPTURE = SKILL / "scripts" / "capture_playwright.mjs"
PLAYWRIGHT_AVAILABLE = subprocess.run(
    ["node", "-e", "import('playwright').then(()=>process.exit(0)).catch(()=>process.exit(1))"],
    cwd=ROOT,
).returncode == 0


class CaptureHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        body = b"<!doctype html><html><body><main>capture target</main></body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


class SkillContractTests(unittest.TestCase):
    def test_public_repository_exposes_exactly_one_skill(self) -> None:
        self.assertEqual(list(ROOT.glob("skills/*/SKILL.md")), [SKILL / "SKILL.md"])

    def test_request_resolution_contract_has_safe_defaults(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        resolution = (SKILL / "references" / "request-resolution.md").read_text(
            encoding="utf-8"
        )
        capture = (SKILL / "references" / "capture-and-annotation.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("default to", skill)
        self.assertIn("local-html", skill)
        self.assertIn("Ask only when the answer materially changes execution", skill)
        self.assertIn("Never ask for cookies, tokens, passwords", resolution)
        self.assertIn("Use an ephemeral context for public pages", capture)
        self.assertIn("search, fetch, APIs, CLIs", capture)

    def test_manifest_template_uses_v11_local_html_request(self) -> None:
        manifest = json.loads(
            (SKILL / "templates" / "source-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["schema_version"], "1.1")
        self.assertEqual(manifest["request"]["destinations"], ["local-html"])
        self.assertEqual(manifest["request"]["browser_state"], "ephemeral")
        self.assertEqual(manifest["outputs"]["html_preview"], "preview/index.html")

    def test_legacy_shim_template_is_explicit_only_and_has_no_implementation(self) -> None:
        shim = (SKILL / "templates" / "web-evidence-capture-shim.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("name: web-evidence-capture", shim)
        self.assertIn("explicitly invokes web-evidence-capture", shim)
        self.assertIn("../visual-brief/SKILL.md", shim)
        self.assertIn("contains no research, capture, image-processing", shim)
        self.assertIn("web-evidence-capture-v1", shim)
        self.assertIn("../visual-brief/scripts/export_legacy_web_evidence.py", shim)
        self.assertIn("legacy name for a public explainer", shim)
        self.assertIn("0.2.x", shim)
        self.assertIn("0.3.0", shim)
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(package["version"], "0.2.0")

    def test_capture_rejects_storage_state_outside_credential_root_before_import(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "capture.png"
            result = subprocess.run(
                [
                    "node",
                    str(CAPTURE),
                    "--url",
                    "https://example.com",
                    "--selector",
                    "main",
                    "--output",
                    str(output),
                    "--storage-state",
                    str(Path(temporary) / "state.json"),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("external browser-state root", result.stderr)
            self.assertNotIn("Playwright is not installed", result.stderr)

    def test_capture_rejects_unknown_or_duplicate_options(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "capture.png"
            base = [
                "node",
                str(CAPTURE),
                "--url",
                "https://example.com",
                "--selector",
                "main",
                "--output",
                str(output),
            ]
            unknown = subprocess.run(
                base + ["--storage_state", str(Path(temporary) / "state.json")],
                text=True,
                capture_output=True,
            )
            self.assertEqual(unknown.returncode, 2)
            self.assertIn("Unknown option", unknown.stderr)

            duplicate = subprocess.run(
                base + ["--selector", "body"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(duplicate.returncode, 2)
            self.assertIn("Duplicate option", duplicate.stderr)

    def test_capture_rejects_credential_root_inside_active_project(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            state_root = Path(temporary) / "browser-state"
            state = state_root / "state.json"
            env = os.environ.copy()
            env["VISUAL_BRIEF_BROWSER_STATE_ROOT"] = str(state_root)
            result = subprocess.run(
                [
                    "node",
                    str(CAPTURE),
                    "--url",
                    "https://example.com",
                    "--selector",
                    "main",
                    "--output",
                    str(Path(temporary) / "capture.png"),
                    "--storage-state",
                    str(state),
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("outside the active project", result.stderr)

    def test_capture_rejects_state_inside_any_git_repo_even_from_external_cwd(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as state_directory, tempfile.TemporaryDirectory() as cwd:
            state = Path(state_directory) / "state.json"
            state.write_text('{"cookies": [], "origins": []}', encoding="utf-8")
            env = os.environ.copy()
            env["VISUAL_BRIEF_BROWSER_STATE_ROOT"] = str(ROOT.parent)
            result = subprocess.run(
                [
                    "node",
                    str(CAPTURE),
                    "--url",
                    "https://example.com",
                    "--selector",
                    "main",
                    "--output",
                    str(Path(cwd) / "capture.png"),
                    "--storage-state",
                    str(state),
                ],
                cwd=cwd,
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("Git worktree", result.stderr)
            self.assertNotIn(str(state), result.stderr)

    def test_capture_rejects_symlink_root_state_and_output_without_touching_targets(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are unavailable")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            real_state_root = root / "real-state"
            real_state_root.mkdir()
            state = real_state_root / "state.json"
            state.write_text('{"cookies": [], "origins": []}', encoding="utf-8")
            linked_root = root / "linked-state"
            linked_root.symlink_to(real_state_root, target_is_directory=True)
            env = os.environ.copy()
            env["VISUAL_BRIEF_BROWSER_STATE_ROOT"] = str(linked_root)
            linked_state = linked_root / "state.json"
            root_result = subprocess.run(
                [
                    "node",
                    str(CAPTURE),
                    "--url",
                    "https://example.com",
                    "--selector",
                    "main",
                    "--output",
                    str(project / "unused.png"),
                    "--storage-state",
                    str(linked_state),
                ],
                cwd=project,
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertEqual(root_result.returncode, 2)
            self.assertIn("real external directory", root_result.stderr)

            target = root / "target.txt"
            target.write_text("keep-capture", encoding="utf-8")
            output = root / "capture.png"
            output.symlink_to(target)
            output_result = subprocess.run(
                [
                    "node",
                    str(CAPTURE),
                    "--url",
                    "https://example.com",
                    "--selector",
                    "main",
                    "--output",
                    str(output),
                ],
                cwd=root,
                text=True,
                capture_output=True,
            )
            self.assertEqual(output_result.returncode, 2)
            self.assertIn("already exists", output_result.stderr)
            self.assertEqual(target.read_text(encoding="utf-8"), "keep-capture")

    def test_capture_invalid_state_does_not_leak_credential_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            state_root = root / "browser-state"
            project.mkdir()
            state_root.mkdir()
            state = state_root / "private-state.json"
            state.write_text("not-json", encoding="utf-8")
            env = os.environ.copy()
            env["VISUAL_BRIEF_BROWSER_STATE_ROOT"] = str(state_root)
            result = subprocess.run(
                [
                    "node",
                    str(CAPTURE),
                    "--url",
                    "https://example.com",
                    "--selector",
                    "main",
                    "--output",
                    str(project / "capture.png"),
                    "--storage-state",
                    str(state),
                ],
                cwd=project,
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("not valid JSON", result.stderr)
            self.assertNotIn(str(state), result.stderr)

    def test_capture_rejects_browser_state_inside_non_git_working_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "plain-project"
            state_root = project / "browser-state"
            state_root.mkdir(parents=True)
            state = state_root / "state.json"
            state.write_text('{"cookies": [], "origins": []}', encoding="utf-8")
            env = os.environ.copy()
            env["VISUAL_BRIEF_BROWSER_STATE_ROOT"] = str(state_root)
            result = subprocess.run(
                [
                    "node",
                    str(CAPTURE),
                    "--url",
                    "https://example.com",
                    "--selector",
                    "main",
                    "--output",
                    str(project / "capture.png"),
                    "--storage-state",
                    str(state),
                ],
                cwd=project,
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("outside the active project", result.stderr)

    @unittest.skipUnless(PLAYWRIGHT_AVAILABLE, "Playwright is not installed")
    def test_capture_supports_ephemeral_and_valid_external_state(self) -> None:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), CaptureHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/"
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                project = root / "project"
                project.mkdir()
                for name, with_state in (("ephemeral", False), ("authenticated", True)):
                    with self.subTest(with_state=with_state):
                        output = root / f"{name}.png"
                        command = [
                            "node",
                            str(CAPTURE),
                            "--url",
                            url,
                            "--selector",
                            "main",
                            "--output",
                            str(output),
                        ]
                        env = os.environ.copy()
                        if with_state:
                            state_root = root / "browser-state"
                            state_root.mkdir(exist_ok=True)
                            state = state_root / "state.json"
                            state.write_text('{"cookies": [], "origins": []}', encoding="utf-8")
                            env["VISUAL_BRIEF_BROWSER_STATE_ROOT"] = str(state_root)
                            command.extend(["--storage-state", str(state)])
                        result = subprocess.run(
                            command,
                            cwd=project,
                            env=env,
                            text=True,
                            capture_output=True,
                            check=True,
                        )
                        self.assertTrue(json.loads(result.stdout)["captured"])
                        self.assertTrue(output.read_bytes().startswith(b"\x89PNG"))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
