#!/usr/bin/env python3
"""Shared fail-closed path helpers for local Visual Brief package scripts."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def resolve_package(package: Path) -> Path:
    """Return a canonical package directory and reject a symlink root."""
    lexical = Path(os.path.abspath(package))
    if lexical.is_symlink():
        raise ValueError(f"package directory must not be a symlink: {lexical}")
    if not lexical.is_dir():
        raise FileNotFoundError(f"package directory does not exist: {lexical}")
    return lexical.resolve(strict=True)


def safe_package_path(
    package: Path,
    candidate: Path,
    label: str,
    *,
    must_exist: bool = False,
    require_file: bool = False,
) -> Path:
    """Resolve a lexical package path while rejecting every symlink component."""
    lexical = Path(os.path.abspath(candidate))
    alias_root: Path | None = None
    current = lexical
    while True:
        if current.is_symlink():
            try:
                resolved_current = current.resolve(strict=True)
                resolved_current.relative_to(package)
            except (FileNotFoundError, ValueError):
                pass
            else:
                raise ValueError(f"{label} must not use symlinks: {current}")
        if current.exists():
            try:
                if current.resolve(strict=True) == package:
                    alias_root = current
                    break
            except FileNotFoundError:
                pass
        if current == current.parent:
            break
        current = current.parent
    if alias_root is None:
        raise ValueError(f"{label} must stay inside the package")

    relative = lexical.relative_to(alias_root)
    mapped = package / relative
    current = alias_root
    missing = False
    for part in relative.parts:
        current = current / part
        if missing:
            continue
        if current.is_symlink():
            raise ValueError(f"{label} must not use symlinks: {current}")
        if not current.exists():
            missing = True

    if must_exist and not mapped.exists():
        raise FileNotFoundError(f"{label} does not exist: {mapped}")
    if require_file and (not mapped.exists() or not mapped.is_file()):
        raise FileNotFoundError(f"{label} must be a regular file: {mapped}")
    return mapped


def ensure_safe_parent(package: Path, output: Path, label: str) -> None:
    """Create missing parent directories one at a time without following symlinks."""
    safe_package_path(package, output, label)
    relative_parent = output.parent.relative_to(package)
    current = package
    for part in relative_parent.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"{label} must not use symlinks: {current}")
        if current.exists():
            if not current.is_dir():
                raise ValueError(f"{label} parent is not a directory: {current}")
            continue
        current.mkdir()


def atomic_write_text(package: Path, output: Path, content: str, label: str) -> None:
    """Atomically replace a package text file without following an output symlink."""
    safe_package_path(package, output, label)
    ensure_safe_parent(package, output, label)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
