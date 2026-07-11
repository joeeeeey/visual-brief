from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicCaseStudyTests(unittest.TestCase):
    def test_case_study_is_explicitly_synthetic(self) -> None:
        html = (ROOT / "site" / "case-study" / "index.html").read_text(encoding="utf-8")

        self.assertIn("完全合成演示", html)
        self.assertIn("SYNTHETIC DEMO", html)
        self.assertIn("portal.example", html)
        self.assertNotIn("@", html)
        self.assertNotIn("localhost", html)
        self.assertNotIn("file://", html)

    def test_case_study_has_action_and_success_state(self) -> None:
        html = (ROOT / "site" / "case-study" / "index.html").read_text(encoding="utf-8")

        self.assertIn("Download for macOS", html)
        self.assertIn("Privacy &amp; Security", html)
        self.assertGreaterEqual(html.count("Device check complete"), 3)


if __name__ == "__main__":
    unittest.main()
