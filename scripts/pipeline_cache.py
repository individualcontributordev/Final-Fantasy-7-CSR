"""Validate and recover staged CSR+/Highwind build artifacts.

A file existing is not enough to call it cached: Makou or another editor may
have changed it in place. A reusable stage must have a report containing the
SHA-256 of its output, and the current bytes must still match that hash.
Reports and artifacts under one run directory are the only inputs. These
helpers never rebuild content. Invalid or changed stages are rejected, while
``archive_path`` moves them into the run's timestamped ``recovery/`` directory
before a caller replaces them. Recovery therefore preserves operator edits
instead of treating an existing filename as disposable cache.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_report(report_path: Path) -> dict[str, Any] | None:
    """Load a JSON object report, returning ``None`` for missing/invalid data."""
    if not report_path.is_file():
        return None
    try:
        value = json.loads(report_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return value if isinstance(value, dict) else None


def cached_output(
    *,
    report_path: Path,
    output_path: Path,
    sha256_file,
) -> tuple[bool, dict[str, Any] | None, str]:
    """Return whether one stage output still matches its recorded hash."""
    report = load_report(report_path)
    if report is None:
        return False, None, "stage report is missing or invalid"
    expected = report.get("outputSha256")
    if not isinstance(expected, str) or not expected:
        return False, report, "stage report has no outputSha256"
    if not output_path.is_file():
        return False, report, f"output is missing: {output_path}"
    actual = sha256_file(output_path)
    if actual != expected:
        return False, report, f"output hash changed ({actual} != {expected})"
    return True, report, "hash matches"


def cached_artifacts(
    *,
    report_path: Path,
    stage_dir: Path,
    sha256_file,
) -> tuple[bool, dict[str, Any] | None, str]:
    """Validate every artifact named in a source-stage cache report."""
    report = load_report(report_path)
    if report is None:
        return False, None, "stage report is missing or invalid"
    artifacts = report.get("cacheArtifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        return False, report, "stage report has no cacheArtifacts"
    for relative_path, expected in artifacts.items():
        path = stage_dir / relative_path
        if not path.is_file():
            return False, report, f"cached artifact is missing: {relative_path}"
        actual = sha256_file(path)
        if actual != expected:
            return False, report, f"cached artifact changed: {relative_path}"
    return True, report, "all artifact hashes match"


def archive_path(path: Path, run_dir: Path) -> Path | None:
    """Move a stage aside before rebuilding it; never discard user edits."""
    if not path.exists():
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    recovery_dir = run_dir / "recovery"
    recovery_dir.mkdir(parents=True, exist_ok=True)
    destination = recovery_dir / f"{stamp}-{path.name}"
    suffix = 2
    while destination.exists():
        destination = recovery_dir / f"{stamp}-{path.name}-{suffix}"
        suffix += 1
    shutil.move(str(path), str(destination))
    return destination
