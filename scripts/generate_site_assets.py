#!/usr/bin/env python3
"""Render reproducible synthetic showcase graphics for the GitHub Pages site."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "site" / "assets"

PAPER = "#f3f8f6"
WHITE = "#ffffff"
INK = "#17211d"
MUTED = "#55655e"
LINE = "#c8d6d0"
TEAL = "#006d77"
CORAL = "#e6533f"
YELLOW = "#f4c74d"
BLUE = "#2864dc"


def font(size: int, bold: bool = False, serif: bool = False) -> ImageFont.ImageFont:
    candidates = []
    if serif:
        candidates.extend(
            [
                "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
                if bold
                else "/System/Library/Fonts/Supplemental/Georgia.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
                if bold
                else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            ]
        )
    else:
        candidates.extend(
            [
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
                if bold
                else "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
                if bold
                else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
        )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


DISPLAY = font(102, bold=True, serif=True)
DISPLAY_MEDIUM = font(64, bold=True, serif=True)
DISPLAY_SMALL = font(44, bold=True, serif=True)
BODY = font(24)
BODY_BOLD = font(24, bold=True)
MONO = font(18, bold=True)
MONO_SMALL = font(16, bold=True)


def canvas(background: str = PAPER, foreground: str = INK) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (1600, 900), background)
    return image, ImageDraw.Draw(image)


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str | None = None, width: int = 2) -> None:
    draw.rounded_rectangle(box, radius=7, fill=fill, outline=outline, width=width)


def multiline(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fill: str, selected_font: ImageFont.ImageFont, spacing: int = 8) -> None:
    draw.multiline_text(xy, text, fill=fill, font=selected_font, spacing=spacing)


def header(draw: ImageDraw.ImageDraw, light: bool = False) -> None:
    color = WHITE if light else TEAL
    edge = WHITE if light else INK
    draw.text((82, 52), "VISUAL BRIEF", fill=color, font=MONO)
    rounded(draw, (1304, 42, 1518, 84), fill="" if False else (INK if light else PAPER), outline=edge, width=1)
    draw.text((1321, 55), "SYNTHETIC SHOWCASE", fill=edge, font=MONO_SMALL)


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str) -> None:
    draw.line((*start, *end), fill=color, width=4)
    direction = 1 if end[0] >= start[0] else -1
    draw.polygon(
        [(end[0], end[1]), (end[0] - direction * 18, end[1] - 11), (end[0] - direction * 18, end[1] + 11)],
        fill=color,
    )


def save(image: Image.Image, filename: str) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT / filename, format="WEBP", quality=90, method=6)


def context_gap() -> None:
    image, draw = canvas()
    header(draw)
    draw.text((110, 172), "THE REAL COLLABORATION GAP", fill=CORAL, font=MONO)
    multiline(draw, (110, 220), "Not missing\ninformation.\nMissing context.", INK, font(76, bold=True, serif=True), spacing=0)
    multiline(
        draw,
        (116, 456),
        "One person has the investigation. Everyone else\ngets a conclusion and a link dump.",
        MUTED,
        BODY,
        spacing=10,
    )
    rounded(draw, (870, 152, 1490, 766), WHITE, INK, width=2)
    rounded(draw, (912, 214, 1114, 398), INK)
    draw.text((936, 242), "Researcher", fill=WHITE, font=BODY_BOLD)
    multiline(draw, (936, 291), "Sources\nscreens\ndetails", WHITE, font(18), spacing=7)
    rounded(draw, (1242, 524, 1450, 710), YELLOW)
    draw.text((1270, 551), "Reader", fill=INK, font=BODY_BOLD)
    multiline(draw, (1270, 599), "Fast inspection\nwithout blind trust", INK, font(17), spacing=7)
    draw.line((1118, 422, 1240, 422), fill=CORAL, width=4)
    for x in range(1118, 1240, 17):
        draw.ellipse((x, 417, x + 7, 424), fill=CORAL)
    draw.text((1094, 378), "Context gap", fill=CORAL, font=MONO_SMALL)
    rounded(draw, (1016, 458, 1350, 518), "#e3f2ef", TEAL, width=3)
    draw.text((1042, 478), "Claim + visual + source", fill=TEAL, font=MONO_SMALL)
    draw.line((1182, 519, 1182, 554), fill=TEAL, width=4)
    draw.polygon([(1182, 568), (1170, 548), (1194, 548)], fill=TEAL)
    draw.text((82, 834), "A brief makes the handoff inspectable.", fill=MUTED, font=MONO_SMALL)
    save(image, "01-context-gap.webp")


def claim_visual_source() -> None:
    image, draw = canvas(WHITE)
    header(draw)
    draw.text((110, 142), "A REVIEWABLE CHAIN", fill=TEAL, font=MONO)
    draw.text((110, 190), "Three artifacts. Three different jobs.", fill=INK, font=DISPLAY_MEDIUM)
    draw.text((114, 293), "Keep the claim narrow, the visual decisive, and the source accountable.", fill=MUTED, font=BODY)
    nodes = [
        (110, "01", "Claim", "The specific statement\na reader is being asked\nto accept.", PAPER),
        (590, "02", "Visual", "The smallest readable region\nthat makes the decisive state\neasy to inspect.", YELLOW),
        (1070, "03", "Source", "The canonical record a reader\ncan open, verify, or challenge.", "#dbe7ff"),
    ]
    for index, (x, number, label, body, background) in enumerate(nodes):
        rounded(draw, (x, 420, x + 420, 714), background, INK, width=2)
        draw.text((x + 32, 452), number, fill=CORAL, font=MONO)
        draw.text((x + 32, 525), label, fill=INK, font=DISPLAY_SMALL)
        multiline(draw, (x + 32, 588), body, INK if index > 0 else MUTED, font(20), spacing=8)
        if index < 2:
            arrow(draw, (x + 420, 567), (x + 469, 567), CORAL)
    draw.text((110, 794), "Generated art can explain this relationship. It cannot become factual proof.", fill=MUTED, font=MONO_SMALL)
    save(image, "02-claim-visual-source.webp")


def three_modes() -> None:
    image, draw = canvas()
    header(draw)
    draw.text((110, 140), "THREE READER JOURNEYS", fill=BLUE, font=MONO)
    draw.text((110, 190), "Start from what the next reader needs to do.", fill=INK, font=DISPLAY_MEDIUM)
    modes = [
        (110, CORAL, "01", "Evidence\nreply", "Answer a decision question with\nthe conclusion first, then only\nthe proof that changes it.", "CONCLUSION\nPROOF\nSOURCE\nBOUNDARY"),
        (590, TEAL, "02", "Visual\nprocedure", "Place each image after the\naction it clarifies, and finish\non a visible success state.", "ACTION\nIMAGE\nEXPECTED STATE\nSUCCESS CHECK"),
        (1070, BLUE, "03", "Public\nexplainer", "Teach with source-backed visuals\nand clearly labeled diagrams or\ngenerated art.", "THESIS\nEXPLANATION\nSOURCES AND LIMITS\nCHANNEL DRAFT"),
    ]
    for x, color, number, title, body, sequence in modes:
        rounded(draw, (x, 354, x + 420, 786), WHITE, INK, width=2)
        draw.rectangle((x, 354, x + 420, 366), fill=color)
        draw.text((x + 31, 397), number, fill=MUTED, font=MONO)
        multiline(draw, (x + 31, 472), title, INK, DISPLAY_SMALL, spacing=0)
        multiline(draw, (x + 31, 584), body, MUTED, font(20), spacing=8)
        multiline(draw, (x + 31, 697), sequence, INK, font(14, bold=True), spacing=5)
    save(image, "03-three-modes.webp")


def lightweight_install() -> None:
    image, draw = canvas(INK)
    header(draw, light=True)
    draw.text((110, 142), "A SMALL PAYLOAD. A COMPLETE WORKFLOW.", fill=YELLOW, font=MONO)
    multiline(draw, (110, 190), "Install the skill.\nKeep the showcase separate.", WHITE, DISPLAY_MEDIUM, spacing=1)
    rounded(draw, (110, 436, 748, 715), YELLOW, YELLOW)
    draw.text((143, 468), "INSTALLED INTO THE AGENT", fill=INK, font=MONO_SMALL)
    multiline(draw, (143, 515), "skills/\nvisual-brief", INK, DISPLAY_SMALL, spacing=0)
    multiline(draw, (143, 623), "Workflow, templates, references, scripts,\nand the Python dependency declaration.", INK, font(18), spacing=6)
    rounded(draw, (780, 436, 1490, 715), "#264a45", "#6a8f89", width=2)
    draw.text((814, 468), "STAYS IN THE REPOSITORY", fill=WHITE, font=MONO_SMALL)
    multiline(draw, (814, 515), "Site, examples,\nevaluations", WHITE, DISPLAY_SMALL, spacing=0)
    multiline(draw, (814, 623), "README visuals, teaching fixtures, and\ndevelopment evidence stay out of the payload.", "#d7eee8", font(18), spacing=6)
    rounded(draw, (110, 778, 1490, 846), WHITE, WHITE)
    draw.rectangle((110, 778, 120, 846), fill=CORAL)
    draw.text((144, 800), "npx skills add joeeeeey/visual-brief --skill visual-brief --agent '*'", fill=INK, font=font(18, bold=True))
    save(image, "04-lightweight-install.webp")


def main() -> None:
    context_gap()
    claim_visual_source()
    three_modes()
    lightweight_install()


if __name__ == "__main__":
    main()
