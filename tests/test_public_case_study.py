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

    def test_english_case_study_is_ready_for_public_sharing(self) -> None:
        html = (ROOT / "site" / "case-study" / "en.html").read_text(encoding="utf-8")
        social_card = html.split('<section id="guide-social-card-en"', 1)[1].split("</section>", 1)[0]

        self.assertIn("Fully synthetic demo", html)
        self.assertIn("guide-social-card-en", html)
        self.assertIn("Complete the device check on macOS", html)
        self.assertIn("Human review before sending", html)
        self.assertNotRegex(social_card, r"[\u4e00-\u9fff]")
        self.assertNotIn("@", html)
        self.assertNotIn("localhost", html)

    def test_readme_leads_with_the_english_example_without_product_names(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("08-employee-guide-preview-en.webp", readme)
        self.assertNotIn("06-employee-guide-preview.webp", readme)
        for product_name in ("Codex", "Claude Code", "Cursor"):
            self.assertNotIn(product_name, readme)


if __name__ == "__main__":
    unittest.main()
