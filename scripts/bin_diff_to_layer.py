#!/usr/bin/env python3
"""Diff two disc images into an ic-layer-v1 JSON file for the browser builder.

Example (Windows):
  python scripts/bin_diff_to_layer.py ^
    workspace\\iso-extract\\ff7_disc1_pristine.bin ^
    workspace\\iso-extract\\ff7_disc1_encounter.bin ^
    -o builder\\encounter-v0.1.0\\layers\\disc1.layer.json ^
    --id encounter-disc1-v0.1.0 ^
    --description "Encounter FORCE stub Disc 1"

Does not read or write game content into git — only the layer JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CHUNK = 1024 * 1024
# Keep individual records from becoming giant single JSON strings
MAX_RECORD_BYTES = 4096


def iter_runs(original: Path, modified: Path):
    """Yield (offset, modified_bytes) for contiguous changed regions."""
    with original.open("rb") as fo, modified.open("rb") as fm:
        offset = 0
        run_off: int | None = None
        run = bytearray()

        def flush():
            nonlocal run_off, run
            if run_off is None or not run:
                run_off = None
                run = bytearray()
                return
            # Split long runs for manageable JSON
            pos = 0
            while pos < len(run):
                piece = bytes(run[pos : pos + MAX_RECORD_BYTES])
                yield run_off + pos, piece
                pos += len(piece)
            run_off = None
            run = bytearray()

        while True:
            a = fo.read(CHUNK)
            b = fm.read(CHUNK)
            if not a and not b:
                break
            if len(a) < len(b):
                a = a + b"\x00" * (len(b) - len(a))
            elif len(b) < len(a):
                b = b + b"\x00" * (len(a) - len(b))

            for i, (ca, cb) in enumerate(zip(a, b)):
                if ca != cb:
                    if run_off is None:
                        run_off = offset + i
                    run.append(cb)
                elif run_off is not None:
                    yield from flush()
            offset += len(a)

        yield from flush()


def build_layer(
    original: Path,
    modified: Path,
    *,
    layer_id: str,
    description: str,
) -> dict:
    records = []
    total_bytes = 0
    for off, data in iter_runs(original, modified):
        records.append({"offset": off, "hex": data.hex()})
        total_bytes += len(data)

    return {
        "format": "ic-layer-v1",
        "id": layer_id,
        "description": description,
        "target": "disc-image",
        "stats": {
            "originalBytes": original.stat().st_size,
            "modifiedBytes": modified.stat().st_size,
            "changedBytes": total_bytes,
            "records": len(records),
        },
        "records": records,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Create ic-layer-v1 from pristine vs patched .bin")
    ap.add_argument("original", type=Path, help="Pristine retail .bin")
    ap.add_argument("modified", type=Path, help="Patched .bin")
    ap.add_argument("-o", "--output", type=Path, required=True, help="Output .layer.json")
    ap.add_argument("--id", required=True, help="Layer id string")
    ap.add_argument("--description", default="", help="Short description")
    args = ap.parse_args()

    if not args.original.is_file():
        print(f"Missing original: {args.original}", file=sys.stderr)
        return 1
    if not args.modified.is_file():
        print(f"Missing modified: {args.modified}", file=sys.stderr)
        return 1

    layer = build_layer(
        args.original,
        args.modified,
        layer_id=args.id,
        description=args.description or args.id,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(layer, indent=2) + "\n", encoding="utf-8")

    stats = layer["stats"]
    print(f"Wrote {args.output}")
    print(
        f"  records={stats['records']}  changedBytes={stats['changedBytes']}  "
        f"jsonBytes≈{args.output.stat().st_size}"
    )
    if stats["changedBytes"] > 5_000_000:
        print(
            "WARNING: large layer (>5MB changed). Browser download/apply may be slow; "
            "file-pack format may be better later for cutscene packs.",
            file=sys.stderr,
        )
    if stats["records"] == 0:
        print("WARNING: no differences found.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
