from __future__ import annotations

import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "visual-brief"
VALIDATE = SKILL / "scripts" / "validate_package.py"
RENDER = SKILL / "scripts" / "render_preview.py"
SLACK_DRAFT = SKILL / "scripts" / "create_slack_draft.py"
LEGACY_EXPORT = SKILL / "scripts" / "export_legacy_web_evidence.py"
EXPORT_PREVIEW = SKILL / "scripts" / "export_preview.mjs"
PLAYWRIGHT_AVAILABLE = subprocess.run(
    ["node", "-e", "import('playwright').then(()=>process.exit(0)).catch(()=>process.exit(1))"],
    cwd=ROOT,
).returncode == 0


class CountingHandler(http.server.BaseHTTPRequestHandler):
    hits = 0

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        type(self).hits += 1
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.end_headers()
        self.wfile.write(b"not-needed")

    def log_message(self, format: str, *args: object) -> None:
        return


class PackageScriptTests(unittest.TestCase):
    def copy_example(self, name: str, directory: Path) -> Path:
        target = directory / name
        shutil.copytree(ROOT / "examples" / name, target)
        return target

    def upgrade_to_v11(
        self,
        package: Path,
        *,
        destinations: list[str],
        compatibility_profile: str | None = None,
        locale: str = "en",
    ) -> dict:
        manifest_path = package / "source-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["schema_version"] = "1.1"
        manifest["request"] = {
            "destinations": destinations,
            "source_access": "provided",
            "capture": "provided-assets",
            "browser_state": "none",
            "locale": locale,
            "compatibility_profile": compatibility_profile,
        }
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return manifest

    def render_v11_preview(self, package: Path) -> Path:
        self.upgrade_to_v11(package, destinations=["local-html"])
        subprocess.run(
            [sys.executable, str(RENDER), "--package", str(package)],
            text=True,
            capture_output=True,
            check=True,
        )
        return package / "preview" / "index.html"

    def start_counting_server(self) -> tuple[http.server.ThreadingHTTPServer, threading.Thread]:
        CountingHandler.hits = 0
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), CountingHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread

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
                rendered_manifest = json.loads(
                    (package / "source-manifest.json").read_text(encoding="utf-8")
                )
                self.assertEqual(rendered_manifest["outputs"]["html_preview"], "preview/index.html")
                recheck = subprocess.run(
                    [sys.executable, str(VALIDATE), "--package", str(package)],
                    text=True,
                    capture_output=True,
                    check=True,
                )
                self.assertTrue(json.loads(recheck.stdout)["passed"])

    def test_v11_local_html_requires_preview_then_renders_and_validates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = self.copy_example("sanitized-evidence-reply", Path(temporary))
            self.upgrade_to_v11(package, destinations=["local-html"])
            before = subprocess.run(
                [sys.executable, str(VALIDATE), "--package", str(package)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(before.returncode, 1)
            self.assertIn("local-html destination requires outputs.html_preview", before.stdout)

            subprocess.run(
                [sys.executable, str(RENDER), "--package", str(package)],
                text=True,
                capture_output=True,
                check=True,
            )
            preview = (package / "preview" / "index.html").read_text(encoding="utf-8")
            self.assertIn('<html lang="en">', preview)
            self.assertIn("Local preview.", preview)
            self.assertIn("<strong>合成训练 fixture</strong>", preview)
            self.assertIn("<code>Enabled</code>", preview)
            after = subprocess.run(
                [sys.executable, str(VALIDATE), "--package", str(package)],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertTrue(json.loads(after.stdout)["passed"])

    def test_v11_requires_request_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = self.copy_example("sanitized-evidence-reply", Path(temporary))
            manifest_path = package / "source-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["schema_version"] = "1.1"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATE), "--package", str(package)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("requires a request object", result.stdout)

    def test_v11_destination_outputs_are_exact_and_type_errors_stay_in_json_report(self) -> None:
        cases = [
            ("sanitized-evidence-reply", ["local-html"], "html_preview", "deliverable.md", "preview/index.html"),
            ("sanitized-evidence-reply", ["slack"], "slack_block_kit", None, "outputs.slack_block_kit"),
            ("sanitized-visual-procedure", ["notion"], "notion_import", None, "outputs.notion_import"),
            ("sanitized-public-explainer", ["v2ex"], "social_drafts", None, "outputs.social_drafts"),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            for index, (example, destinations, key, value, expected) in enumerate(cases):
                with self.subTest(destinations=destinations):
                    package = self.copy_example(example, Path(temporary) / str(index))
                    self.upgrade_to_v11(package, destinations=destinations)
                    manifest_path = package / "source-manifest.json"
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    if value is None:
                        manifest["outputs"].pop(key, None)
                    else:
                        manifest["outputs"][key] = value
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, str(VALIDATE), "--package", str(package)],
                        text=True,
                        capture_output=True,
                    )
                    self.assertEqual(result.returncode, 1)
                    self.assertIn(expected, result.stdout)

            package = self.copy_example("sanitized-evidence-reply", Path(temporary) / "type")
            self.upgrade_to_v11(package, destinations=["local-html"])
            manifest_path = package / "source-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["request"]["destinations"] = [{}]
            manifest["claims"][0]["asset_ids"] = [{}]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATE), "--package", str(package)],
                text=True,
                capture_output=True,
            )
            report = json.loads(result.stdout)
            self.assertEqual(result.returncode, 1)
            self.assertIn("unsupported request destination", "\n".join(report["errors"]))
            self.assertIn("non-string asset ID", "\n".join(report["errors"]))

            manifest["claims"][0]["asset_ids"] = None
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            null_result = subprocess.run(
                [sys.executable, str(VALIDATE), "--package", str(package)],
                text=True,
                capture_output=True,
            )
            null_report = json.loads(null_result.stdout)
            self.assertEqual(null_result.returncode, 1)
            self.assertIn("asset_ids as a list", "\n".join(null_report["errors"]))

            manifest["mode"] = {}
            manifest["assets"][0]["kind"] = []
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            enum_result = subprocess.run(
                [sys.executable, str(VALIDATE), "--package", str(package)],
                text=True,
                capture_output=True,
            )
            enum_report = json.loads(enum_result.stdout)
            self.assertEqual(enum_result.returncode, 1)
            self.assertIn("unsupported mode", "\n".join(enum_report["errors"]))
            self.assertIn("invalid kind", "\n".join(enum_report["errors"]))

    def test_legacy_evidence_profile_exports_old_reader_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = self.copy_example("sanitized-evidence-reply", Path(temporary))
            self.upgrade_to_v11(
                package,
                destinations=["slack"],
                compatibility_profile="web-evidence-capture-v1",
            )
            result = subprocess.run(
                [sys.executable, str(LEGACY_EXPORT), "--package", str(package)],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn("evidence-reply.md", json.loads(result.stdout)["created"])
            self.assertEqual(
                (package / "evidence-reply.md").read_text(encoding="utf-8"),
                (package / "deliverable.md").read_text(encoding="utf-8"),
            )
            validation = subprocess.run(
                [sys.executable, str(VALIDATE), "--package", str(package)],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertTrue(json.loads(validation.stdout)["passed"])

    def test_legacy_visual_procedure_exports_old_reader_and_notion_filenames(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = self.copy_example("sanitized-visual-procedure", Path(temporary))
            self.upgrade_to_v11(
                package,
                destinations=["notion"],
                compatibility_profile="web-evidence-capture-v1",
            )
            first = subprocess.run(
                [sys.executable, str(LEGACY_EXPORT), "--package", str(package)],
                text=True,
                capture_output=True,
                check=True,
            )
            second = subprocess.run(
                [sys.executable, str(LEGACY_EXPORT), "--package", str(package)],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertEqual(json.loads(first.stdout), json.loads(second.stdout))
            self.assertTrue((package / "visual-guide.md").is_file())
            self.assertTrue((package / "notion-import.md").is_file())
            validation = subprocess.run(
                [sys.executable, str(VALIDATE), "--package", str(package)],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertTrue(json.loads(validation.stdout)["passed"])

    def test_legacy_notion_missing_fails_before_partial_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = self.copy_example("sanitized-visual-procedure", Path(temporary))
            self.upgrade_to_v11(
                package,
                destinations=["notion"],
                compatibility_profile="web-evidence-capture-v1",
            )
            manifest_path = package / "source-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["outputs"].pop("notion_import")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(LEGACY_EXPORT), "--package", str(package)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("outputs.notion_import", result.stderr)
            self.assertFalse((package / "visual-guide.md").exists())

    def test_legacy_profile_rejects_public_explainer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = self.copy_example("sanitized-public-explainer", Path(temporary))
            self.upgrade_to_v11(
                package,
                destinations=["v2ex"],
                compatibility_profile="web-evidence-capture-v1",
            )
            result = subprocess.run(
                [sys.executable, str(LEGACY_EXPORT), "--package", str(package)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("does not support mode", result.stderr)

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

    def test_rejects_url_userinfo_signed_queries_and_loopback_variants(self) -> None:
        urls = [
            "https://alice:supersecret@example.com/doc",
            "https://example.com/doc?X-Amz-Credential=value&X-Amz-Signature=value",
            "https://example.com/doc?access_token=value",
            "http://127.1/private",
            "http://2130706433/private",
            "http://[::ffff:127.0.0.1]/private",
            "http://[::1",
            "http://example.com:bad/",
            "http://0x7f000001/",
            "http://%31%32%37.0.0.1/",
            "http://foo.localhost/",
            "http://[not-ip]/",
            "http://\ud800/",
        ]
        with tempfile.TemporaryDirectory() as temporary:
            for index, url in enumerate(urls):
                with self.subTest(url=url):
                    package = self.copy_example(
                        "sanitized-evidence-reply", Path(temporary) / str(index)
                    )
                    manifest_path = package / "source-manifest.json"
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    manifest["sources"][0]["url"] = url
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, str(VALIDATE), "--package", str(package)],
                        text=True,
                        capture_output=True,
                    )
                    self.assertEqual(result.returncode, 1)
                    report = json.loads(result.stdout)
                    combined = "\n".join(report["errors"])
                    self.assertTrue(
                        "embedded credentials" in combined
                        or "sensitive-looking query" in combined
                        or "local URL" in combined
                        or "valid absolute" in combined
                        or "percent-encoded hostname" in combined
                        or "invalid bracketed" in combined
                        or "invalid hostname text" in combined
                    )

            package = self.copy_example(
                "sanitized-evidence-reply", Path(temporary) / "markdown"
            )
            deliverable = package / "deliverable.md"
            deliverable.write_text(
                deliverable.read_text(encoding="utf-8")
                + "\n[unsafe](HTTPS://alice:secret@example.com?X-Amz-Signature=value)\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(VALIDATE), "--package", str(package)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("Markdown link", result.stdout)
            self.assertIn("embedded credentials", result.stdout)

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
            manifest_path = package / "source-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["sources"][0]["title"] = (
                "Trusted title> <!channel> <https://evil.example|click"
            )
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
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
            payload = json.loads(output.read_text(encoding="utf-8"))
            mrkdwn = payload["blocks"][1]["text"]["text"]
            self.assertNotIn("<!channel>", mrkdwn)
            self.assertNotIn("<https://evil.example", mrkdwn)
            self.assertIn("&lt;!channel&gt;", mrkdwn)

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["sources"][0]["url"] = (
                "https://alice:secret@example.com/file?X-Amz-Signature=value"
            )
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            unsafe_output = package / "packages" / "unsafe-slack.json"
            unsafe = subprocess.run(
                [
                    sys.executable,
                    str(SLACK_DRAFT),
                    "--package",
                    str(package),
                    "--summary",
                    "test",
                    "--output",
                    str(unsafe_output),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(unsafe.returncode, 2)
            self.assertIn("embedded credentials", unsafe.stderr)
            self.assertFalse(unsafe_output.exists())

    def test_package_writers_reject_symlink_manifest_and_outputs(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are unavailable")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)

            render_package = self.copy_example("sanitized-evidence-reply", root / "render")
            external_manifest = root / "external-manifest.json"
            original_manifest = (render_package / "source-manifest.json").read_text(encoding="utf-8")
            external_manifest.write_text(original_manifest, encoding="utf-8")
            (render_package / "source-manifest.json").unlink()
            (render_package / "source-manifest.json").symlink_to(external_manifest)
            render = subprocess.run(
                [sys.executable, str(RENDER), "--package", str(render_package)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(render.returncode, 2)
            self.assertEqual(external_manifest.read_text(encoding="utf-8"), original_manifest)

            slack_package = self.copy_example("sanitized-evidence-reply", root / "slack")
            slack_target = root / "slack-target.txt"
            slack_target.write_text("keep-slack", encoding="utf-8")
            slack_output = slack_package / "packages" / "draft.json"
            slack_output.symlink_to(slack_target)
            slack = subprocess.run(
                [
                    sys.executable,
                    str(SLACK_DRAFT),
                    "--package",
                    str(slack_package),
                    "--summary",
                    "test",
                    "--output",
                    str(slack_output),
                    "--force",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(slack.returncode, 2)
            self.assertEqual(slack_target.read_text(encoding="utf-8"), "keep-slack")

            legacy_package = self.copy_example("sanitized-evidence-reply", root / "legacy")
            self.upgrade_to_v11(
                legacy_package,
                destinations=["slack"],
                compatibility_profile="web-evidence-capture-v1",
            )
            legacy_target = root / "legacy-target.txt"
            legacy_target.write_text("keep-legacy", encoding="utf-8")
            (legacy_package / "evidence-reply.md").symlink_to(legacy_target)
            legacy = subprocess.run(
                [sys.executable, str(LEGACY_EXPORT), "--package", str(legacy_package)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(legacy.returncode, 2)
            self.assertEqual(legacy_target.read_text(encoding="utf-8"), "keep-legacy")

    def test_package_writers_cannot_overwrite_core_or_asset_partitions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            render_package = self.copy_example("sanitized-evidence-reply", root / "render")
            deliverable = render_package / "deliverable.md"
            original_deliverable = deliverable.read_bytes()
            render = subprocess.run(
                [
                    sys.executable,
                    str(RENDER),
                    "--package",
                    str(render_package),
                    "--output",
                    str(deliverable),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(render.returncode, 2)
            self.assertIn("exactly preview/index.html", render.stderr)
            self.assertEqual(deliverable.read_bytes(), original_deliverable)

            slack_package = self.copy_example("sanitized-evidence-reply", root / "slack")
            asset = slack_package / "assets" / "01-sync-status.webp"
            original_asset = asset.read_bytes()
            slack = subprocess.run(
                [
                    sys.executable,
                    str(SLACK_DRAFT),
                    "--package",
                    str(slack_package),
                    "--summary",
                    "test",
                    "--output",
                    str(asset),
                    "--force",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(slack.returncode, 2)
            self.assertIn("under packages", slack.stderr)
            self.assertEqual(asset.read_bytes(), original_asset)

    def test_encoded_local_path_traversal_is_rejected_by_renderer_and_validator(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = self.copy_example("sanitized-evidence-reply", Path(temporary))
            encoded_directory = package / "%2e%2e"
            encoded_directory.mkdir()
            shutil.copyfile(
                package / "assets" / "01-sync-status.webp",
                encoded_directory / "outside.webp",
            )
            deliverable = package / "deliverable.md"
            deliverable.write_text(
                deliverable.read_text(encoding="utf-8")
                + "\n\n![encoded traversal](%2e%2e/outside.webp)\n",
                encoding="utf-8",
            )
            render = subprocess.run(
                [sys.executable, str(RENDER), "--package", str(package)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(render.returncode, 2)
            self.assertIn("must not use percent encoding", render.stderr)
            self.assertFalse((package / "preview" / "index.html").exists())

            validation = subprocess.run(
                [sys.executable, str(VALIDATE), "--package", str(package)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(validation.returncode, 1)
            self.assertIn("encoded or ambiguous local path", validation.stdout)

    @unittest.skipUnless(PLAYWRIGHT_AVAILABLE, "Playwright is not installed")
    def test_preview_export_creates_pdf_and_png_without_following_output_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = self.copy_example("sanitized-evidence-reply", root / "valid")
            self.render_v11_preview(package)
            result = subprocess.run(
                ["node", str(EXPORT_PREVIEW), "--package", str(package)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertTrue(json.loads(result.stdout)["exported"])
            self.assertTrue((package / "exports" / "brief.pdf").read_bytes().startswith(b"%PDF"))
            self.assertTrue((package / "exports" / "brief.png").read_bytes().startswith(b"\x89PNG"))
            duplicate = subprocess.run(
                ["node", str(EXPORT_PREVIEW), "--package", str(package)],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(duplicate.returncode, 2)
            self.assertIn("use --force", duplicate.stderr)
            subprocess.run(
                ["node", str(EXPORT_PREVIEW), "--package", str(package), "--force"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            if sys.platform == "darwin" and shutil.which("chflags"):
                pdf_output = package / "exports" / "brief.pdf"
                image_output = package / "exports" / "brief.png"
                original_pdf = pdf_output.read_bytes()
                original_image = image_output.read_bytes()
                subprocess.run(["chflags", "uchg", str(image_output)], check=True)
                try:
                    failed_force = subprocess.run(
                        ["node", str(EXPORT_PREVIEW), "--package", str(package), "--force"],
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                    )
                finally:
                    subprocess.run(["chflags", "nouchg", str(image_output)], check=True)
                self.assertEqual(failed_force.returncode, 2)
                self.assertEqual(pdf_output.read_bytes(), original_pdf)
                self.assertEqual(image_output.read_bytes(), original_image)

            symlink_package = self.copy_example("sanitized-evidence-reply", root / "symlink")
            self.render_v11_preview(symlink_package)
            exports = symlink_package / "exports"
            exports.mkdir()
            outside = root / "outside.txt"
            outside.write_text("keep-export", encoding="utf-8")
            (exports / "brief.pdf").symlink_to(outside)
            blocked = subprocess.run(
                ["node", str(EXPORT_PREVIEW), "--package", str(symlink_package)],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(blocked.returncode, 2)
            self.assertIn("symlink", blocked.stderr)
            self.assertEqual(outside.read_text(encoding="utf-8"), "keep-export")

            partition_package = self.copy_example("sanitized-evidence-reply", root / "partition")
            self.render_v11_preview(partition_package)
            sources = partition_package / "sources"
            sources.mkdir()
            source_pdf = sources / "canonical.pdf"
            source_png = partition_package / "assets" / "raw.png"
            source_pdf.write_bytes(b"keep-pdf")
            source_png.write_bytes(b"keep-png")
            partition = subprocess.run(
                [
                    "node",
                    str(EXPORT_PREVIEW),
                    "--package",
                    str(partition_package),
                    "--pdf",
                    str(source_pdf),
                    "--image",
                    str(source_png),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(partition.returncode, 2)
            self.assertIn("under exports", partition.stderr)
            self.assertEqual(source_pdf.read_bytes(), b"keep-pdf")
            self.assertEqual(source_png.read_bytes(), b"keep-png")

            readonly_package = self.copy_example("sanitized-evidence-reply", root / "readonly")
            self.render_v11_preview(readonly_package)
            (readonly_package / "exports").mkdir()
            try:
                readonly_package.chmod(0o555)
                readonly = subprocess.run(
                    ["node", str(EXPORT_PREVIEW), "--package", str(readonly_package)],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                )
            finally:
                readonly_package.chmod(0o755)
            self.assertEqual(readonly.returncode, 2)
            self.assertFalse((readonly_package / "exports" / "brief.pdf").exists())
            self.assertFalse((readonly_package / "exports" / "brief.png").exists())

    @unittest.skipUnless(PLAYWRIGHT_AVAILABLE, "Playwright is not installed")
    def test_preview_export_blocks_remote_resources_and_disables_javascript(self) -> None:
        server, thread = self.start_counting_server()
        try:
            origin = f"http://127.0.0.1:{server.server_port}"
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                remote_package = self.copy_example("sanitized-evidence-reply", root / "remote")
                remote_preview = self.render_v11_preview(remote_package)
                html = remote_preview.read_text(encoding="utf-8").replace(
                    "</article>", f'<img src="{origin}/pixel.png"></article>'
                )
                remote_preview.write_text(html, encoding="utf-8")
                blocked = subprocess.run(
                    ["node", str(EXPORT_PREVIEW), "--package", str(remote_package)],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(blocked.returncode, 2)
                self.assertIn("blocked external", blocked.stderr)
                self.assertEqual(CountingHandler.hits, 0)
                self.assertFalse((remote_package / "exports" / "brief.pdf").exists())

                print_package = self.copy_example("sanitized-evidence-reply", root / "print")
                print_preview = self.render_v11_preview(print_package)
                html = print_preview.read_text(encoding="utf-8").replace(
                    "</head>",
                    f'<style>@media print {{ body {{ background-image: url("{origin}/print.png"); }} }}</style></head>',
                )
                print_preview.write_text(html, encoding="utf-8")
                print_blocked = subprocess.run(
                    ["node", str(EXPORT_PREVIEW), "--package", str(print_package)],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(print_blocked.returncode, 2)
                self.assertIn("blocked external", print_blocked.stderr)
                self.assertEqual(CountingHandler.hits, 0)
                self.assertFalse((print_package / "exports" / "brief.pdf").exists())

                script_package = self.copy_example("sanitized-evidence-reply", root / "script")
                script_preview = self.render_v11_preview(script_package)
                html = script_preview.read_text(encoding="utf-8").replace(
                    "</article>", f'<script>fetch("{origin}/script")</script></article>'
                )
                script_preview.write_text(html, encoding="utf-8")
                subprocess.run(
                    ["node", str(EXPORT_PREVIEW), "--package", str(script_package)],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=True,
                )
                self.assertEqual(CountingHandler.hits, 0)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
