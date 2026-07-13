#!/usr/bin/env python3
"""Render a local, dependency-free HTML preview for a Visual Brief package."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

from path_safety import atomic_write_text, resolve_package, safe_package_path


IMAGE_LINE = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)\)\s*$")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
STRONG = re.compile(r"\*\*([^*]+)\*\*")
INLINE_CODE = re.compile(r"`([^`]+)`")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a local Visual Brief HTML preview.")
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--output", type=Path, help="Defaults to <package>/preview/index.html")
    return parser.parse_args()


def relative_target(
    package: Path,
    output: Path,
    target: str,
    *,
    allow_remote: bool,
    require_file: bool = False,
) -> str:
    parsed = urlparse(target)
    if target.startswith("#"):
        return target
    if parsed.scheme in {"http", "https", "mailto"}:
        if allow_remote:
            return target
        raise ValueError(f"preview images must be local package files, not remote URLs: {target}")
    if parsed.scheme:
        raise ValueError(f"preview target uses an unsupported URL scheme: {target}")
    if not parsed.path:
        raise ValueError(f"preview target has no local path: {target}")
    decoded_path = unquote(parsed.path)
    if decoded_path != parsed.path:
        raise ValueError(f"preview local paths must not use percent encoding: {target}")
    if "\\" in decoded_path or "\x00" in decoded_path:
        raise ValueError(f"preview local path is ambiguous or unsafe: {target}")
    candidate = safe_package_path(
        package,
        package / decoded_path,
        f"preview target {target}",
        must_exist=True,
        require_file=require_file,
    )
    relative = quote(Path(os.path.relpath(candidate, output.parent)).as_posix(), safe="/")
    if parsed.query:
        relative += f"?{parsed.query}"
    if parsed.fragment:
        relative += f"#{parsed.fragment}"
    return relative


def inline_markdown(text: str, package: Path, output: Path) -> str:
    escaped = html.escape(text)

    def link(match: re.Match[str]) -> str:
        label = html.escape(html.unescape(match.group(1)))
        target = html.unescape(match.group(2))
        href = html.escape(
            relative_target(package, output, target, allow_remote=True), quote=True
        )
        attrs = ' target="_blank" rel="noopener noreferrer"' if href.startswith("http") else ""
        return f'<a href="{href}"{attrs}>{label}</a>'

    rendered = LINK.sub(link, escaped)
    rendered = STRONG.sub(r"<strong>\1</strong>", rendered)
    return INLINE_CODE.sub(r"<code>\1</code>", rendered)


def render_markdown(content: str, package: Path, output: Path) -> str:
    rendered: list[str] = []
    in_list = False
    in_code = False

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            rendered.append("</ul>")
            in_list = False

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            close_list()
            if in_code:
                rendered.append("</code></pre>")
            else:
                rendered.append("<pre><code>")
            in_code = not in_code
            continue
        if in_code:
            rendered.append(html.escape(line) + "\n")
            continue
        if not stripped:
            close_list()
            continue
        image_match = IMAGE_LINE.match(stripped)
        if image_match:
            close_list()
            alt, target = image_match.groups()
            src = html.escape(
                relative_target(
                    package,
                    output,
                    target,
                    allow_remote=False,
                    require_file=True,
                ),
                quote=True,
            )
            rendered.append(
                f'<figure><img src="{src}" alt="{html.escape(alt, quote=True)}" loading="lazy"><figcaption>{html.escape(alt)}</figcaption></figure>'
            )
            continue
        if stripped.startswith("#"):
            close_list()
            level = min(len(stripped) - len(stripped.lstrip("#")), 6)
            text = stripped[level:].strip()
            rendered.append(f"<h{level}>{inline_markdown(text, package, output)}</h{level}>")
            continue
        if stripped.startswith("> "):
            close_list()
            rendered.append(f"<blockquote>{inline_markdown(stripped[2:], package, output)}</blockquote>")
            continue
        if stripped.startswith(("- ", "* ")):
            if not in_list:
                rendered.append("<ul>")
                in_list = True
            rendered.append(f"<li>{inline_markdown(stripped[2:], package, output)}</li>")
            continue
        ordered = re.match(r"^\d+\.\s+(.+)$", stripped)
        if ordered:
            if not in_list:
                rendered.append("<ul class=\"ordered\">")
                in_list = True
            rendered.append(f"<li>{inline_markdown(ordered.group(1), package, output)}</li>")
            continue
        close_list()
        if stripped == "---":
            rendered.append("<hr>")
        else:
            rendered.append(f"<p>{inline_markdown(stripped, package, output)}</p>")
    close_list()
    if in_code:
        rendered.append("</code></pre>")
    return "\n".join(rendered)


def main() -> int:
    args = parse_args()
    package = resolve_package(args.package)
    manifest_path = safe_package_path(
        package,
        package / "source-manifest.json",
        "source manifest",
        must_exist=True,
        require_file=True,
    )
    deliverable_path = safe_package_path(
        package,
        package / "deliverable.md",
        "deliverable",
        must_exist=True,
        require_file=True,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    outputs = manifest.setdefault("outputs", {})
    if not isinstance(outputs, dict):
        raise ValueError("manifest outputs must be an object")
    output = safe_package_path(
        package,
        args.output or package / "preview" / "index.html",
        "preview output",
    )
    expected_output = package / "preview" / "index.html"
    if output != expected_output:
        raise ValueError("preview output must be exactly preview/index.html")
    relative_output = output.relative_to(package).as_posix()
    title = html.escape(str(manifest.get("title", "Visual Brief")))
    status = html.escape(str(manifest.get("status", "draft")))
    request = manifest.get("request") if isinstance(manifest.get("request"), dict) else {}
    locale = str(request.get("locale", "zh-CN"))
    if locale.lower().startswith("zh"):
        notice = f"本地预览，当前状态：{status}。准备材料不等于获准上传、发送或发布。"
    else:
        notice = f"Local preview. Current status: {status}. Preparing material does not authorize upload, sending, or publication."
    body = render_markdown(deliverable_path.read_text(encoding="utf-8"), package, output)
    document = f"""<!doctype html>
<html lang=\"{html.escape(locale, quote=True)}\"><head><meta charset=\"utf-8\"><meta name=\"visual-brief-preview\" content=\"1.1\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<title>{title}</title><style>
:root {{ color-scheme: light; font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif; color: #17212b; background: #f7f8fa; }}
body {{ margin: 0; }} main {{ max-width: 760px; margin: 0 auto; padding: 28px 20px 60px; }}
.notice {{ color: #5f4b08; background: #fff7d6; border-left: 4px solid #d99a00; padding: 10px 12px; margin-bottom: 20px; }}
article {{ background: #fff; border: 1px solid #dbe1e8; padding: 28px; }} h1 {{ font-size: 30px; }} h2 {{ margin-top: 34px; }}
p, li {{ line-height: 1.65; }} a {{ color: #0b65c2; }} figure {{ margin: 20px 0 28px; }} img {{ display: block; max-width: 100%; height: auto; border: 1px solid #dbe1e8; }} figcaption {{ color: #536270; font-size: 14px; margin-top: 8px; }}
blockquote {{ border-left: 3px solid #b7c4d3; color: #455565; margin: 18px 0; padding: 3px 14px; }} code {{ border-radius: 3px; padding: 2px 4px; background: #eef2f6; }} pre {{ overflow-x: auto; background: #12202f; color: #e8eff7; padding: 14px; }} pre code {{ padding: 0; background: transparent; }} .ordered {{ list-style: decimal; }}
</style></head><body><main><div class=\"notice\">{notice}</div><article>{body}</article></main></body></html>"""
    atomic_write_text(package, output, document, "preview output")
    outputs["html_preview"] = relative_output
    atomic_write_text(
        package,
        manifest_path,
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        "source manifest",
    )
    print(
        json.dumps(
            {
                "output": str(output),
                "status": manifest.get("status", "draft"),
                "manifest_updated": True,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"render_preview: {exc}", file=sys.stderr)
        raise SystemExit(2)
