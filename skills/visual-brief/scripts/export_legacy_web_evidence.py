#!/usr/bin/env python3
"""Export additive web-evidence-capture v1 compatibility filenames."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from path_safety import atomic_write_text, resolve_package, safe_package_path


LEGACY_DELIVERABLES = {
    "evidence-reply": "evidence-reply.md",
    "visual-procedure": "visual-guide.md",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export legacy web-evidence-capture filenames from a Visual Brief package."
    )
    parser.add_argument("--package", required=True, type=Path)
    return parser.parse_args()


def package_path(
    package: Path,
    relative: str,
    label: str,
    *,
    must_exist: bool = False,
) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ValueError(f"{label} must be a non-empty relative path")
    return safe_package_path(
        package,
        package / relative,
        label,
        must_exist=must_exist,
        require_file=must_exist,
    )


def main() -> int:
    args = parse_args()
    package = resolve_package(args.package)
    manifest_path = package_path(
        package, "source-manifest.json", "source manifest", must_exist=True
    )
    deliverable_path = package_path(
        package, "deliverable.md", "deliverable", must_exist=True
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    request = manifest.get("request")
    if not isinstance(request, dict) or request.get("compatibility_profile") != "web-evidence-capture-v1":
        raise ValueError("request.compatibility_profile must be web-evidence-capture-v1")

    mode = manifest.get("mode")
    legacy_name = LEGACY_DELIVERABLES.get(mode)
    if legacy_name is None:
        raise ValueError(f"legacy profile does not support mode: {mode!r}")

    outputs = manifest.setdefault("outputs", {})
    if not isinstance(outputs, dict):
        raise ValueError("manifest outputs must be an object")
    notion_relative = outputs.get("notion_import")
    destinations = request.get("destinations")
    notion_required = isinstance(destinations, list) and "notion" in destinations
    if mode == "visual-procedure" and notion_required and not isinstance(notion_relative, str):
        raise ValueError("Notion destination requires outputs.notion_import before legacy export")
    notion_source = None
    notion_target = None
    notion_content = None
    if mode == "visual-procedure" and isinstance(notion_relative, str):
        notion_source = package_path(
            package, notion_relative, "Notion import source", must_exist=True
        )
        notion_target = package_path(package, "notion-import.md", "legacy Notion output")
        notion_content = notion_source.read_text(encoding="utf-8").replace("](../", "](")

    legacy_deliverable = package_path(package, legacy_name, "legacy deliverable output")
    deliverable_content = deliverable_path.read_text(encoding="utf-8")
    atomic_write_text(
        package,
        legacy_deliverable,
        deliverable_content,
        "legacy deliverable output",
    )
    outputs["legacy_deliverable"] = legacy_name

    created = [legacy_name]
    if notion_target is not None and notion_content is not None:
        atomic_write_text(
            package,
            notion_target,
            notion_content,
            "legacy Notion output",
        )
        outputs["legacy_notion_import"] = "notion-import.md"
        created.append("notion-import.md")

    atomic_write_text(
        package,
        manifest_path,
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        "source manifest",
    )
    print(json.dumps({"profile": "web-evidence-capture-v1", "created": created}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"export_legacy_web_evidence: {exc}", file=sys.stderr)
        raise SystemExit(2)
