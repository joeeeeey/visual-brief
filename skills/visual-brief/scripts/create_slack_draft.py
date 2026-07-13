#!/usr/bin/env python3
"""Create a local Slack Block Kit draft from a Visual Brief manifest. Never sends it."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from path_safety import atomic_write_text, resolve_package, safe_package_path
from url_safety import http_url_issues


def slack_label(value: object) -> str:
    text = " ".join(str(value or "").split()).replace("|", "/")
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def slack_link_url(value: object) -> str:
    if not isinstance(value, str) or any(character in value for character in "<>|\r\n"):
        raise ValueError("Slack source URL contains unsafe link syntax")
    issues = http_url_issues(value)
    if issues:
        raise ValueError(f"Slack source URL {issues[0]}")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a local-only Slack Block Kit draft.")
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--summary", required=True, help="One concise conclusion for the reader.")
    parser.add_argument("--output", type=Path, help="Defaults to packages/slack-block-kit.json")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


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
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    outputs = manifest.setdefault("outputs", {})
    if not isinstance(outputs, dict):
        raise ValueError("manifest outputs must be an object")
    output = safe_package_path(
        package,
        args.output or package / "packages" / "slack-block-kit.json",
        "Slack draft output",
    )
    relative_output = output.relative_to(package).as_posix()
    if not relative_output.startswith("packages/") or output.suffix.lower() != ".json":
        raise ValueError("Slack draft output must be a .json file under packages/")
    if output.exists() and not args.force:
        raise FileExistsError(f"draft already exists: {output}; use --force to replace it")

    source_by_id = {source.get("id"): source for source in manifest.get("sources", [])}
    lines = [args.summary.strip(), "", "*Sources*"]
    for claim in manifest.get("claims", []):
        if claim.get("kind") == "illustrative":
            continue
        for source_id in claim.get("source_ids", []):
            source = source_by_id.get(source_id)
            if source:
                source_url = slack_link_url(source.get("url"))
                source_title = slack_label(source.get("title"))
                claim_id = slack_label(claim.get("id"))
                lines.append(f"- <{source_url}|{source_title}> ({claim_id})")
    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"[DRAFT] {manifest.get('title', 'Visual Brief')}"},
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(lines)}},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Local draft only. Images and claim boundaries remain in the visual brief package.",
                    }
                ],
            },
        ]
    }
    atomic_write_text(
        package,
        output,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        "Slack draft output",
    )
    outputs["slack_block_kit"] = relative_output
    atomic_write_text(
        package,
        manifest_path,
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        "source manifest",
    )
    print(json.dumps({"draft": str(output), "sent": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, FileExistsError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"create_slack_draft: {exc}", file=sys.stderr)
        raise SystemExit(2)
