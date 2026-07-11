#!/usr/bin/env python3
"""Convert Playwright case-study captures into reviewed WebP assets."""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / ".tmp-case-study-renders"
OUTPUT = ROOT / "site" / "assets"
FILENAMES = (
    "05-employee-portal-download",
    "06-employee-guide-preview",
    "07-device-check-complete",
)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)

    for filename in FILENAMES:
        source = INPUT / f"{filename}.png"
        destination = OUTPUT / f"{filename}.webp"
        with Image.open(source) as image:
            image.convert("RGB").save(destination, format="WEBP", quality=90, method=6)

    shutil.rmtree(INPUT)


if __name__ == "__main__":
    main()
