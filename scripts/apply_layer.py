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

from libs.layer import apply_layer

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
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(image)
        print(f"Wrote {args.output} ({len(image)} bytes)")
    elif not args.expect:
        print(f"Applied OK ({len(layer['records'])} records, {len(image)} bytes) — pass -o to write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
