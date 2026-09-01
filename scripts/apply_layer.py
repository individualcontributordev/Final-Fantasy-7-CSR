#!/usr/bin/env python3
"""Apply an ``ic-layer-v1`` JSON patch to a raw disc image.

  python scripts/apply_layer.py pristine.bin layer.json -o out.bin
  python scripts/apply_layer.py pristine.bin layer.json --expect patched.bin

Input records are absolute byte offsets and hex payloads. The output is either
a new BIN or a read-only exact comparison; the input BIN is never overwritten.
Growth is zero-filled and rounded to a 2352-byte raw-sector boundary. This
module does not interpret ISO9660 or repair EDC/ECC, so callers must validate
those invariants separately after applying layers that change sector contents.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def apply_layer(image: bytearray, layer: dict) -> None:
    """Apply validated layer records to ``image`` in listed order.

    The layer format permits later records to overwrite earlier records.
    ``stats.originalBytes`` is trusted only when it matches the pre-apply image,
    preventing metadata for another base image from controlling output growth.
    """
    if layer.get("format") != "ic-layer-v1":
        raise SystemExit("expected format ic-layer-v1")
    if layer.get("target") not in (None, "disc-image"):
        raise SystemExit(f"unsupported target: {layer.get('target')}")
    # Growth metadata describes the source image, so compare it with the
    # pre-apply length rather than a length already extended by records.
    baseline_len = len(image)
    for rec in layer["records"]:
        offset = int(rec["offset"])
        data = bytes.fromhex(rec["hex"])
        end = offset + len(data)
        if end > len(image):
            image.extend(b"\x00" * (end - len(image)))
        image[offset:end] = data
    # Grown images: trailing zeros often match zero-pad of a shorter original and
    # are omitted from records. Honor stats.modifiedBytes when this layer was
    # built against an image the same size as our baseline (before records).
    # Always finish on a 2352-byte boundary if we grew (Mode2 safety).
    stats = layer.get("stats") or {}
    original = stats.get("originalBytes")
    target = stats.get("modifiedBytes")
    if (
        isinstance(target, int)
        and target > len(image)
        and isinstance(original, int)
        and original == baseline_len
    ):
        image.extend(b"\x00" * (target - len(image)))
    SECTOR = 2352
    if len(image) > baseline_len and len(image) % SECTOR:
        image.extend(b"\x00" * (SECTOR - (len(image) % SECTOR)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("image", type=Path)
    ap.add_argument("layer", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--expect", type=Path, help="Patched image that must match after apply")
    args = ap.parse_args()

    image = bytearray(args.image.read_bytes())
    layer = json.loads(args.layer.read_text(encoding="utf-8"))
    apply_layer(image, layer)

    if args.expect:
        expect = args.expect.read_bytes()
        # Compare overlapping length; allow trailing pad differences only if sizes match
        if bytes(image) != expect:
            # find first mismatch
            lim = min(len(image), len(expect))
            for i in range(lim):
                if image[i] != expect[i]:
                    print(f"MISMATCH at offset {i} (0x{i:X})", file=sys.stderr)
                    return 1
            if len(image) != len(expect):
                print(
                    f"MISMATCH size {len(image)} vs {len(expect)}",
                    file=sys.stderr,
                )
                return 1
            print("MISMATCH (unknown)", file=sys.stderr)
            return 1
        print("OK — layer apply matches --expect")
    if args.output:
        args.output.write_bytes(image)
        print(f"Wrote {args.output} ({len(image)} bytes)")
    elif not args.expect:
        print(f"Applied OK ({len(layer['records'])} records, {len(image)} bytes) — pass -o to write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
