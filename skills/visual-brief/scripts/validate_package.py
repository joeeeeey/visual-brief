#!/usr/bin/env python3
"""Validate a Visual Brief package without uploading, sending, or publishing it."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from PIL import Image


MODES = {"evidence-reply", "visual-procedure", "public-explainer"}
STATUSES = {"draft", "review", "approved", "published"}
SOURCE_KINDS = {"canonical", "secondary", "fixture"}
CLAIM_KINDS = {"observed", "documented", "inference", "illustrative"}
ASSET_KINDS = {"screenshot", "diagram", "generated"}
ASSET_ROLES = {"evidence", "instruction", "illustration"}
SENSITIVE_QUERY_KEYS = {"token", "key", "signature", "sig", "authorization", "credential"}
FORBIDDEN_NAME = re.compile(
    r"(^|[-_.])(\.env(?:\.|$)|cookies?|storage[-_]?state|auth(?:entication)?|.*\.(?:pem|key|p12))",
    re.IGNORECASE,
)
SENSITIVE_PATTERNS = {
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    "OpenAI-style API key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "authorization credential": re.compile(
        r"(?i)authorization\s*[:=]\s*(?:bearer|basic)\s+[A-Za-z0-9._~+/=-]{12,}"
    ),
    "session cookie": re.compile(
        r"(?i)(?:session|cookie)\s*[:=]\s*[A-Za-z0-9._~+/=-]{16,}"
    ),
}
TEXT_SUFFIXES = {".md", ".json", ".html", ".txt", ".yaml", ".yml"}
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)")


@dataclass
class Findings:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def check(self, message: str) -> None:
        self.checks.append(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a local Visual Brief package.")
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings and fixture sources as failures."
    )
    return parser.parse_args()


def safe_relative(package: Path, relative: str, findings: Findings, label: str) -> Path | None:
    if not isinstance(relative, str) or not relative:
        findings.error(f"{label} must be a non-empty relative path")
        return None
    candidate = (package / relative).resolve()
    try:
        candidate.relative_to(package)
    except ValueError:
        findings.error(f"{label} escapes the package: {relative}")
        return None
    return candidate


def validate_url(url: object, label: str, findings: Findings) -> None:
    if not isinstance(url, str):
        findings.error(f"{label} must be a URL string")
        return
    parsed = urlparse(url)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        findings.error(f"{label} must use an absolute http(s) URL")
        return
    if parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
        findings.error(f"{label} must not expose a local URL")
    query_keys = {key.lower() for key in parse_qs(parsed.query)}
    exposed = sorted(query_keys & SENSITIVE_QUERY_KEYS)
    if exposed:
        findings.error(f"{label} contains sensitive-looking query keys: {', '.join(exposed)}")


def scan_text(package: Path, findings: Findings) -> None:
    for path in package.rglob("*"):
        if not path.is_file():
            continue
        if FORBIDDEN_NAME.search(path.name):
            findings.error(f"forbidden credential-like filename: {path.relative_to(package)}")
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.warn(f"could not UTF-8 scan text candidate: {path.relative_to(package)}")
            continue
        for label, pattern in SENSITIVE_PATTERNS.items():
            if pattern.search(content):
                findings.error(f"{label} pattern found in {path.relative_to(package)}")


def validate_markdown_links(package: Path, findings: Findings) -> None:
    for path in package.rglob("*.md"):
        content = path.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK.findall(content):
            if target.startswith(("https://", "http://", "mailto:", "#")):
                continue
            candidate = (path.parent / target).resolve()
            try:
                candidate.relative_to(package)
            except ValueError:
                findings.error(
                    f"Markdown link escapes package in {path.relative_to(package)}: {target}"
                )
                continue
            if not candidate.exists():
                findings.error(
                    f"broken Markdown link in {path.relative_to(package)}: {target}"
                )


def validate_manifest(package: Path, manifest: object, strict: bool, findings: Findings) -> None:
    if not isinstance(manifest, dict):
        findings.error("source-manifest.json must contain a JSON object")
        return

    for key in ("schema_version", "title", "mode", "audience", "status", "publication", "sources", "claims", "assets", "outputs"):
        if key not in manifest:
            findings.error(f"manifest is missing required field: {key}")

    if manifest.get("schema_version") != "1.0":
        findings.error("manifest schema_version must be 1.0")
    if manifest.get("mode") not in MODES:
        findings.error(f"unsupported mode: {manifest.get('mode')!r}")
    if manifest.get("status") not in STATUSES:
        findings.error(f"unsupported status: {manifest.get('status')!r}")
    for key in ("title", "audience"):
        if not isinstance(manifest.get(key), str) or not manifest[key].strip():
            findings.error(f"manifest {key} must be a non-empty string")

    publication = manifest.get("publication")
    if not isinstance(publication, dict) or not isinstance(publication.get("approved"), bool):
        findings.error("publication.approved must be a boolean")

    sources = manifest.get("sources")
    source_by_id: dict[str, dict] = {}
    if not isinstance(sources, list) or not sources:
        findings.error("manifest sources must be a non-empty list")
        sources = []
    for index, source in enumerate(sources, start=1):
        label = f"source {index}"
        if not isinstance(source, dict):
            findings.error(f"{label} must be an object")
            continue
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id:
            findings.error(f"{label} needs a non-empty id")
            continue
        if source_id in source_by_id:
            findings.error(f"duplicate source id: {source_id}")
            continue
        source_by_id[source_id] = source
        if not isinstance(source.get("title"), str) or not source["title"].strip():
            findings.error(f"source {source_id} needs a title")
        validate_url(source.get("url"), f"source {source_id} URL", findings)
        if source.get("kind") not in SOURCE_KINDS:
            findings.error(f"source {source_id} has invalid kind: {source.get('kind')!r}")
        if source.get("kind") == "fixture":
            message = f"source {source_id} is a fixture and cannot support a real decision"
            (findings.error if strict else findings.warn)(message)
        if not isinstance(source.get("captured_at"), str) or not source["captured_at"].strip():
            findings.error(f"source {source_id} needs captured_at")
        if not isinstance(source.get("access_assumptions"), list):
            findings.error(f"source {source_id} needs access_assumptions as a list")

    claims = manifest.get("claims")
    claim_by_id: dict[str, dict] = {}
    if not isinstance(claims, list) or not claims:
        findings.error("manifest claims must be a non-empty list")
        claims = []
    for index, claim in enumerate(claims, start=1):
        label = f"claim {index}"
        if not isinstance(claim, dict):
            findings.error(f"{label} must be an object")
            continue
        claim_id = claim.get("id")
        if not isinstance(claim_id, str) or not claim_id:
            findings.error(f"{label} needs a non-empty id")
            continue
        if claim_id in claim_by_id:
            findings.error(f"duplicate claim id: {claim_id}")
            continue
        claim_by_id[claim_id] = claim
        kind = claim.get("kind")
        if kind not in CLAIM_KINDS:
            findings.error(f"claim {claim_id} has invalid kind: {kind!r}")
        if not isinstance(claim.get("statement"), str) or not claim["statement"].strip():
            findings.error(f"claim {claim_id} needs a statement")
        if not isinstance(claim.get("boundary"), str) or not claim["boundary"].strip():
            findings.error(f"claim {claim_id} needs a boundary")
        source_ids = claim.get("source_ids")
        if not isinstance(source_ids, list):
            findings.error(f"claim {claim_id} needs source_ids as a list")
            source_ids = []
        if kind != "illustrative" and not source_ids:
            findings.error(f"claim {claim_id} needs at least one source ID")
        for source_id in source_ids:
            if source_id not in source_by_id:
                findings.error(f"claim {claim_id} refers to unknown source: {source_id}")
        asset_ids = claim.get("asset_ids")
        if not isinstance(asset_ids, list):
            findings.error(f"claim {claim_id} needs asset_ids as a list")

    assets = manifest.get("assets")
    asset_by_id: dict[str, dict] = {}
    if not isinstance(assets, list) or not assets:
        findings.error("manifest assets must be a non-empty list")
        assets = []
    for index, asset in enumerate(assets, start=1):
        label = f"asset {index}"
        if not isinstance(asset, dict):
            findings.error(f"{label} must be an object")
            continue
        asset_id = asset.get("id")
        if not isinstance(asset_id, str) or not asset_id:
            findings.error(f"{label} needs a non-empty id")
            continue
        if asset_id in asset_by_id:
            findings.error(f"duplicate asset id: {asset_id}")
            continue
        asset_by_id[asset_id] = asset
        relative = asset.get("path")
        asset_path = safe_relative(package, relative, findings, f"asset {asset_id} path")
        if isinstance(relative, str) and not relative.startswith("assets/"):
            findings.error(f"asset {asset_id} must live under assets/: {relative}")
        if isinstance(relative, str) and not relative.lower().endswith(".webp"):
            findings.error(f"asset {asset_id} must end in .webp: {relative}")
        if asset_path and asset_path.is_file():
            try:
                with Image.open(asset_path) as image:
                    if image.format != "WEBP":
                        findings.error(f"asset {asset_id} is not a real WebP: {relative}")
                    if image.width <= 0 or image.height <= 0:
                        findings.error(f"asset {asset_id} has invalid dimensions: {relative}")
            except OSError as exc:
                findings.error(f"asset {asset_id} is not decodable: {relative} ({exc})")
        elif asset_path:
            findings.error(f"asset {asset_id} is missing: {relative}")
        if asset.get("kind") not in ASSET_KINDS:
            findings.error(f"asset {asset_id} has invalid kind: {asset.get('kind')!r}")
        if asset.get("role") not in ASSET_ROLES:
            findings.error(f"asset {asset_id} has invalid role: {asset.get('role')!r}")
        if asset.get("inspected") is not True:
            findings.warn(f"asset {asset_id} is not marked as human-inspected")
        asset_claim_ids = asset.get("claim_ids")
        if not isinstance(asset_claim_ids, list) or not asset_claim_ids:
            findings.error(f"asset {asset_id} needs at least one claim ID")
            asset_claim_ids = []
        for source_id in asset.get("source_ids", []):
            if source_id not in source_by_id:
                findings.error(f"asset {asset_id} refers to unknown source: {source_id}")
        for claim_id in asset_claim_ids:
            if claim_id not in claim_by_id:
                findings.error(f"asset {asset_id} refers to unknown claim: {claim_id}")
            elif asset.get("kind") == "generated" and claim_by_id[claim_id].get("kind") != "illustrative":
                findings.error(
                    f"generated asset {asset_id} can only attach to an illustrative claim, not {claim_id}"
                )

    for claim_id, claim in claim_by_id.items():
        for asset_id in claim.get("asset_ids", []):
            if asset_id not in asset_by_id:
                findings.error(f"claim {claim_id} refers to unknown asset: {asset_id}")
                continue
            if claim.get("kind") != "illustrative" and asset_by_id[asset_id].get("kind") == "generated":
                findings.error(
                    f"factual claim {claim_id} cannot use generated asset {asset_id} as evidence"
                )

    outputs = manifest.get("outputs")
    if not isinstance(outputs, dict):
        findings.error("manifest outputs must be an object")
        outputs = {}
    for required_key in ("deliverable", "evidence_index"):
        output_path = safe_relative(package, outputs.get(required_key), findings, f"output {required_key}")
        if output_path and not output_path.is_file():
            findings.error(f"required output is missing: {outputs.get(required_key)}")
    for key, relative in outputs.items():
        output_path = safe_relative(package, relative, findings, f"output {key}")
        if output_path and not output_path.is_file():
            findings.error(f"declared output is missing: {relative}")


def main() -> int:
    args = parse_args()
    package = args.package.resolve()
    findings = Findings()
    if not package.is_dir():
        findings.error(f"package directory does not exist: {package}")
    else:
        manifest_path = package / "source-manifest.json"
        if not manifest_path.is_file():
            findings.error("package is missing source-manifest.json")
        else:
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                findings.error(f"source-manifest.json is invalid JSON: {exc}")
            else:
                validate_manifest(package, manifest, args.strict, findings)
        scan_text(package, findings)
        validate_markdown_links(package, findings)

    findings.check("No external action was attempted; this validator is local-only.")
    report = {
        "package": str(package),
        "passed": not findings.errors and (not args.strict or not findings.warnings),
        "errors": findings.errors,
        "warnings": findings.warnings,
        "checks": findings.checks,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
