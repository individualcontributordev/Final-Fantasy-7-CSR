#!/usr/bin/env python3
"""Apply an ic-layer-v1 JSON to a .bin and optionally compare to an expected image.

  python scripts/apply_layer.py pristine.bin layer.json -o out.bin
  python scripts/apply_layer.py pristine.bin layer.json --expect patched.bin
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def apply_layer(image: bytearray, layer: dict) -> None:
    if layer.get("format") != "ic-layer-v1":
        raise SystemExit("expected format ic-layer-v1")
    if layer.get("target") not in (None, "disc-image"):
        raise SystemExit(f"unsupported target: {layer.get('target')}")
    for rec in layer["records"]:
        offset = int(rec["offset"])
        data = bytes.fromhex(rec["hex"])
        end = offset + len(data)
        if end > len(image):
            image.extend(b"\x00" * (end - len(image)))
        image[offset:end] = data


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
