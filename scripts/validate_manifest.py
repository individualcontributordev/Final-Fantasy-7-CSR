#!/usr/bin/env python3
"""Validate the local builder catalog before publishing it.

Default path is ``builder/manifest.json``. Every base and add-on must have a
unique id and a ``discs`` map whose paths exist next to the manifest; each
published ``discDigests`` entry must still hash the layer it names and agree
with the pack's own ``pack.json``; and no published JSON may contain CRLF,
because the digests describe the LF bytes git serves. ``autoIncludeWhen`` ids
must name another entry in this file (unless they start with DISABLED-).

Prints every error and returns nonzero. Does not fetch the network or rewrite
files."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "builder" / "manifest.json"


def crlf_offenders(builder_dir: Path) -> list[Path]:
    """Published JSON whose line endings would not survive a round trip.

    Digests are taken from the file on disk, but Pages serves the committed
    bytes, so a CRLF working copy publishes a hash nobody can match. Windows
    does this silently when ``core.autocrlf`` is on and no ``.gitattributes``
    rule overrides it.
    """
    return [p for p in sorted(builder_dir.rglob("*.json")) if b"\r\n" in p.read_bytes()]


def validate(manifest_path: Path) -> list[str]:
    """Return a list of error strings; empty list means the catalog is valid."""
    errors: list[str] = []

    try:
        text = manifest_path.read_text(encoding="utf-8")
    except OSError as e:
        return [f"cannot read {manifest_path}: {e}"]

    try:
        manifest = json.loads(text)
    except json.JSONDecodeError as e:
        return [f"invalid JSON in {manifest_path}: {e}"]

    builder_dir = manifest_path.parent

    for p in crlf_offenders(builder_dir):
        errors.append(f"{p.relative_to(builder_dir)}: CRLF line endings (must be LF)")

    entries: list[tuple[str, dict]] = []
    for section in ("bases", "addons"):
        items = manifest.get(section) or []
        if not isinstance(items, list):
            errors.append(f"{section!r} is not a list")
            continue
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"{section}[{i}] is not an object")
            elif not item.get("id"):
                errors.append(f"{section}[{i}] missing 'id'")
            else:
                entries.append((section, item))

    seen: set[str] = set()
    for section, entry in entries:
        eid = entry["id"]
        if eid in seen:
            errors.append(f"duplicate {section} id: {eid}")
        seen.add(eid)

        discs = entry.get("discs") or {}
        if not isinstance(discs, dict):
            errors.append(f"{eid}: 'discs' is not an object")
            discs = {}
        digests = entry.get("discDigests") or {}

        for disc, rel in discs.items():
            if not rel:
                errors.append(f"{eid}: discs[{disc!r}] is empty")
                continue
            layer_path = (builder_dir / str(rel).lstrip("./")).resolve()
            if not layer_path.is_file():
                errors.append(
                    f"{eid}: discs[{disc!r}] -> {rel!r} does not exist "
                    f"(resolved {layer_path})"
                )
                continue
            # The builder refuses a layer whose bytes do not hash to the
            # published digest, so a stale one takes the entry offline.
            want = digests.get(str(disc))
            if want:
                got = hashlib.sha256(layer_path.read_bytes()).hexdigest()
                if got != want:
                    errors.append(
                        f"{eid}: discs[{disc!r}] digest is stale "
                        f"(manifest {want[:12]}..., file {got[:12]}...)"
                    )

        # pack.json ships alongside the manifest, so a half-finished publish
        # leaves the two disagreeing about the same layer.
        pack_path = builder_dir / eid / "pack.json"
        if digests and pack_path.is_file():
            try:
                pack = json.loads(pack_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                errors.append(f"{eid}: invalid pack.json: {e}")
            else:
                pack_digests = pack.get("discDigests") or {}
                for disc, want in pack_digests.items():
                    if digests.get(disc) and digests[disc] != want:
                        errors.append(
                            f"{eid}: pack.json disc {disc} digest disagrees "
                            f"with manifest"
                        )

    # Auto-included entries are hidden, so a typo silently drops the pack.
    for section, entry in entries:
        aiw = entry.get("autoIncludeWhen") or {}
        if not isinstance(aiw, dict) or not entry.get("enabled", True):
            continue
        parent = aiw.get("addonSelected")
        if parent and not str(parent).startswith("DISABLED-") and parent not in seen:
            errors.append(
                f"{entry['id']}: autoIncludeWhen.addonSelected={parent!r} "
                f"does not match any id in manifest"
            )

    return errors


def main(argv: list[str]) -> int:
    manifest_path = Path(argv[1]).resolve() if len(argv) > 1 else DEFAULT_MANIFEST
    errors = validate(manifest_path)
    if errors:
        print(f"INVALID: {manifest_path} ({len(errors)} error(s))", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"OK: {manifest_path} is valid ({manifest_path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
