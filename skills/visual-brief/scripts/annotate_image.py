#!/usr/bin/env python3
"""Create a cropped, annotated, shareable WebP from a local source image."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont, ImageOps


def parse_box(value: str) -> tuple[int, int, int, int]:
    try:
        parts = tuple(int(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "box must use x,y,width,height with integer values"
        ) from exc
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("box must contain exactly four values")
    x, y, width, height = parts
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("box width and height must be positive")
    return x, y, width, height


def require_inside(
    box: tuple[int, int, int, int], image_size: tuple[int, int], label: str
) -> None:
    x, y, width, height = box
    image_width, image_height = image_size
    if x < 0 or y < 0 or x + width > image_width or y + height > image_height:
        raise ValueError(
            f"{label} {box} is outside the input image bounds {image_size}"
        )


def translate(
    box: tuple[int, int, int, int], crop: tuple[int, int, int, int]
) -> tuple[int, int, int, int]:
    x, y, width, height = box
    crop_x, crop_y, _, _ = crop
    return x - crop_x, y - crop_y, width, height


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "Arial.ttf",
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_redactions(
    image: Image.Image, boxes: Iterable[tuple[int, int, int, int]]
) -> None:
    draw = ImageDraw.Draw(image)
    font = load_font(max(12, min(image.width, image.height) // 30))
    for x, y, width, height in boxes:
        draw.rectangle((x, y, x + width, y + height), fill=(31, 41, 55, 255))
        label = "REDACTED"
        bbox = draw.textbbox((0, 0), label, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        if text_width + 12 <= width and text_height + 8 <= height:
            draw.text(
                (x + (width - text_width) / 2, y + (height - text_height) / 2),
                label,
                fill=(255, 255, 255, 255),
                font=font,
            )


def draw_highlights(
    image: Image.Image,
    boxes: list[tuple[int, int, int, int]],
    labels: list[str],
) -> None:
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    line_width = max(3, min(image.width, image.height) // 180)
    font = load_font(max(12, min(image.width, image.height) // 28))
    for index, (x, y, width, height) in enumerate(boxes):
        draw.rectangle(
            (x, y, x + width, y + height),
            fill=(245, 158, 11, 68),
            outline=(217, 119, 6, 255),
            width=line_width,
        )
        if index >= len(labels) or not labels[index]:
            continue
        label = labels[index]
        bbox = draw.textbbox((0, 0), label, font=font)
        label_width = bbox[2] - bbox[0]
        label_height = bbox[3] - bbox[1]
        padding_x, padding_y = 8, 5
        label_x = max(0, min(x, image.width - label_width - padding_x * 2))
        label_y = max(0, y - label_height - padding_y * 2 - 4)
        draw.rounded_rectangle(
            (
                label_x,
                label_y,
                label_x + label_width + padding_x * 2,
                label_y + label_height + padding_y * 2,
            ),
            radius=4,
            fill=(146, 64, 14, 255),
        )
        draw.text(
            (label_x + padding_x, label_y + padding_y),
            label,
            fill=(255, 255, 255, 255),
            font=font,
        )
    image.alpha_composite(overlay)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Crop, redact, highlight, and encode a local image as WebP."
    )
    parser.add_argument("--input", required=True, type=Path, help="Source PNG/JPEG/WebP.")
    parser.add_argument("--output", required=True, type=Path, help="Final .webp path.")
    parser.add_argument(
        "--crop",
        type=parse_box,
        help="Optional source-image crop as x,y,width,height.",
    )
    parser.add_argument(
        "--highlight",
        action="append",
        default=[],
        type=parse_box,
        help="Source-image box to highlight; repeat for multiple boxes.",
    )
    parser.add_argument(
        "--label",
        action="append",
        default=[],
        help="Label paired by order with --highlight; repeat when needed.",
    )
    parser.add_argument(
        "--redact",
        action="append",
        default=[],
        type=parse_box,
        help="Source-image box to irreversibly cover; repeat for multiple boxes.",
    )
    parser.add_argument(
        "--quality", type=int, default=86, help="Lossy WebP quality from 0 to 100."
    )
    parser.add_argument(
        "--lossless", action="store_true", help="Use lossless WebP encoding."
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output.suffix.lower() != ".webp":
        raise ValueError("--output must end in .webp; do not rename another format")
    if not args.input.is_file():
        raise FileNotFoundError(f"input image does not exist: {args.input}")
    if not 0 <= args.quality <= 100:
        raise ValueError("--quality must be between 0 and 100")
    if len(args.label) > len(args.highlight):
        raise ValueError("each --label must correspond to a preceding --highlight")

    with Image.open(args.input) as opened:
        source = ImageOps.exif_transpose(opened).convert("RGBA")
    source_size = source.size

    crop = args.crop or (0, 0, source.width, source.height)
    require_inside(crop, source_size, "crop")
    for index, box in enumerate(args.highlight, start=1):
        require_inside(box, source_size, f"highlight {index}")
    for index, box in enumerate(args.redact, start=1):
        require_inside(box, source_size, f"redact {index}")

    crop_x, crop_y, crop_width, crop_height = crop
    output = source.crop((crop_x, crop_y, crop_x + crop_width, crop_y + crop_height))
    translated_redactions = [translate(box, crop) for box in args.redact]
    translated_highlights = [translate(box, crop) for box in args.highlight]
    draw_redactions(output, translated_redactions)
    draw_highlights(output, translated_highlights, args.label)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.convert("RGB").save(
        args.output,
        format="WEBP",
        quality=args.quality,
        method=6,
        lossless=args.lossless,
    )

    report = {
        "input_size": {"width": source_size[0], "height": source_size[1]},
        "output_size": {"width": output.width, "height": output.height},
        "format": "WEBP",
        "crop": {"x": crop_x, "y": crop_y, "width": crop_width, "height": crop_height},
        "highlights": len(translated_highlights),
        "redactions": len(translated_redactions),
        "lossless": args.lossless,
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"annotate_image: {exc}", file=sys.stderr)
        raise SystemExit(2)
