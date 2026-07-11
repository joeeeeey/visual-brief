#!/usr/bin/env python3
"""Create a local Slack Block Kit draft from a Visual Brief manifest. Never sends it."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a local-only Slack Block Kit draft.")
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--summary", required=True, help="One concise conclusion for the reader.")
    parser.add_argument("--output", type=Path, help="Defaults to packages/slack-block-kit.json")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    package = args.package.resolve()
    manifest_path = package / "source-manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("package is missing source-manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output = (args.output or package / "packages" / "slack-block-kit.json").resolve()
    try:
        output.relative_to(package)
    except ValueError as exc:
        raise ValueError("--output must stay inside the package") from exc
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
                lines.append(f"- <{source.get('url')}|{source.get('title')}> ({claim.get('id')})")
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
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"draft": str(output), "sent": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, FileExistsError, ValueError, json.JSONDecodeError) as exc:
        print(f"create_slack_draft: {exc}", file=sys.stderr)
        raise SystemExit(2)
