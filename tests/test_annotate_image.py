from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "visual-brief" / "scripts" / "annotate_image.py"


class AnnotateImageTests(unittest.TestCase):
    def test_crop_highlight_redact_and_webp_encoding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "source.png"
            output = directory / "result.webp"
            image = Image.new("RGB", (240, 160), "white")
            draw = ImageDraw.Draw(image)
            draw.rectangle((60, 40, 170, 105), fill="#2563eb")
            image.save(source)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(source),
                    "--output",
                    str(output),
                    "--crop",
                    "20,20,180,120",
                    "--highlight",
                    "60,40,110,65",
                    "--label",
                    "Key state",
                    "--redact",
                    "65,45,20,20",
                ],
                check=True,
                text=True,
                capture_output=True,
            )
            report = json.loads(result.stdout)
            self.assertEqual(report["format"], "WEBP")
            self.assertEqual(report["output_size"], {"width": 180, "height": 120})
            with Image.open(output) as rendered:
                self.assertEqual(rendered.format, "WEBP")
                self.assertEqual(rendered.size, (180, 120))
                pixel = rendered.convert("RGB").getpixel((55, 35))
            # Lossy WebP can slightly shift a solid redaction color; it must
            # still remain visibly dark rather than exposing the blue source.
            self.assertLess(sum(pixel), 320)

    def test_rejects_non_webp_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "source.png"
            Image.new("RGB", (40, 40), "white").save(source)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(source),
                    "--output",
                    str(directory / "wrong.png"),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("must end in .webp", result.stderr)


if __name__ == "__main__":
    unittest.main()
