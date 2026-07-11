#!/usr/bin/env python3
"""Generate only synthetic assets used by the checked-in training examples."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ANNOTATE = ROOT / "skills" / "visual-brief" / "scripts" / "annotate_image.py"


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
        if bold
        else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "Arial Bold.ttf" if bold else "Arial.ttf",
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str | None = None) -> None:
    draw.rounded_rectangle(box, radius=18, fill=fill, outline=outline, width=2)


def screen(title: str, eyebrow: str, rows: list[tuple[str, str, str]]) -> Image.Image:
    image = Image.new("RGB", (1600, 900), "#edf2f7")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1600, 86), fill="#17212b")
    draw.text((82, 26), "Synthetic training portal", fill="white", font=font(29, True))
    rounded(draw, (100, 128, 1500, 800), "#ffffff", "#d8e1ea")
    draw.text((170, 190), eyebrow.upper(), fill="#607080", font=font(18, True))
    draw.text((170, 232), title, fill="#17212b", font=font(42, True))
    y = 350
    for label, value, tone in rows:
        rounded(draw, (170, y, 1430, y + 112), "#f8fafc", "#dbe5ef")
        draw.text((214, y + 27), label, fill="#405166", font=font(25, True))
        value_width = draw.textbbox((0, 0), value, font=font(28, True))[2]
        value_x = 1358 - value_width
        rounded(draw, (value_x - 24, y + 22, 1382, y + 78), tone)
        draw.text((value_x, y + 35), value, fill="white", font=font(28, True))
        y += 138
    return image


def diagram() -> Image.Image:
    image = Image.new("RGB", (1400, 760), "#f5f7fb")
    draw = ImageDraw.Draw(image)
    draw.text((88, 66), "Synthetic explanatory diagram", fill="#17212b", font=font(40, True))
    nodes = [
        ((110, 270, 420, 460), "Canonical\nsource", "#1d4ed8"),
        ((545, 270, 855, 460), "Decisive\nvisual", "#0f766e"),
        ((980, 270, 1290, 460), "Reader\nbrief", "#a16207"),
    ]
    for index in range(len(nodes) - 1):
        left = nodes[index][0]
        right = nodes[index + 1][0]
        draw.line((left[2], 365, right[0], 365), fill="#8294a8", width=8)
        draw.polygon(((right[0], 365), (right[0] - 24, 351), (right[0] - 24, 379)), fill="#8294a8")
    for box, label, color in nodes:
        rounded(draw, box, color)
        lines = label.split("\n")
        for offset, line in enumerate(lines):
            width = draw.textbbox((0, 0), line, font=font(30, True))[2]
            draw.text(
                ((box[0] + box[2] - width) / 2, box[1] + 52 + offset * 46),
                line,
                fill="white",
                font=font(30, True),
            )
    draw.text(
        (176, 580),
        "Illustration only: it explains a relationship and proves no external fact.",
        fill="#536270",
        font=font(23),
    )
    return image


def annotate(raw: Path, output: Path, highlight: tuple[int, int, int, int], label: str) -> None:
    command = [
        sys.executable,
        str(ANNOTATE),
        "--input",
        str(raw),
        "--output",
        str(output),
        "--crop",
        "100,128,1400,672",
        "--highlight",
        ",".join(str(value) for value in highlight),
        "--label",
        label,
    ]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)


def main() -> int:
    examples = ROOT / "examples"
    with tempfile.TemporaryDirectory(prefix="visual-brief-fixtures-") as temporary:
        temporary_path = Path(temporary)
        jobs = [
            (
                screen(
                    "Sync settings",
                    "Training fixture",
                    [("Sync status", "Enabled", "#047857"), ("Sync interval", "15 minutes", "#1d4ed8")],
                ),
                examples / "sanitized-evidence-reply" / "assets" / "01-sync-status.webp",
                (170, 350, 1260, 250),
                "Decisive state",
            ),
            (
                screen(
                    "Device check",
                    "Training fixture",
                    [("Helper package", "Download helper", "#1d4ed8"), ("Next action", "Read install notes", "#475569")],
                ),
                examples / "sanitized-visual-procedure" / "assets" / "01-download-helper.webp",
                (170, 350, 1260, 112),
                "Start here",
            ),
            (
                screen(
                    "Install confirmation",
                    "Training fixture",
                    [("Package", "Training profile", "#7c3aed"), ("Confirmation", "Review first", "#a16207")],
                ),
                examples / "sanitized-visual-procedure" / "assets" / "02-install-confirmation.webp",
                (170, 350, 1260, 112),
                "Review before install",
            ),
            (
                screen(
                    "Device check",
                    "Training fixture",
                    [("Status", "Device check complete", "#047857"), ("Last result", "Training only", "#475569")],
                ),
                examples / "sanitized-visual-procedure" / "assets" / "03-complete-state.webp",
                (170, 350, 1260, 112),
                "Visible success",
            ),
            (
                screen(
                    "Evidence screen",
                    "Training fixture",
                    [("State", "Reviewable state", "#0f766e"), ("Purpose", "Visual proof demo", "#475569")],
                ),
                examples / "sanitized-public-explainer" / "assets" / "01-reviewable-state.webp",
                (170, 350, 1260, 112),
                "Observed state",
            ),
        ]
        for index, (image, output, highlight, label) in enumerate(jobs, start=1):
            raw = temporary_path / f"fixture-{index}.png"
            image.save(raw, format="PNG")
            output.parent.mkdir(parents=True, exist_ok=True)
            annotate(raw, output, highlight, label)
        generated_output = examples / "sanitized-public-explainer" / "assets" / "02-evidence-explanation-diagram.webp"
        generated_output.parent.mkdir(parents=True, exist_ok=True)
        diagram().save(generated_output, format="WEBP", quality=88, method=6)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
