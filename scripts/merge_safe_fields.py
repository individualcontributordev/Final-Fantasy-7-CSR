#!/usr/bin/env python3
"""Copy unambiguous later-disc CSR field edits onto collapsed Disc 1.

Rework collisions are handled by merge_rework_fields.py instead. RCKTIN7 is
treated as a safe D2 whole-file swap. JUNAIR is excluded (slot patch).

The scanner compares pristine and reconstructed CSR discs and selects a field
only when exactly one present disc changed it and that disc is D2 or D3.
Configured collision/rework fields are excluded because they require
slot-level ownership. Whole FIELD.DAT payloads are copied into the destination
only when they fit its existing sector allocation. Output is a new or
explicitly in-place BIN; EDC/ECC and embedded FIELD.BIN tables are repaired by
later pipeline stages.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from disc_sources import load_csr_image, load_pristine_image  # noqa: E402
from psx_mode2_iso import extract_file, replace_file_within_sectors, walk_tree  # noqa: E402

EXTRA_SAFE_WHOLE_FILE: dict[str, int] = {"RCKTIN7": 2}

# Fields fully owned by the 8-field rework merge -- must not be touched here.
REWORK_FIELDS = {
    "BLACKBGB", "BUGIN1A", "COS_BTM", "COS_BTM2", "DEL1",
    "JUNAIR2", "NIVGATE", "RCKTIN2",
}

EXCLUDE_WHOLE_FILE = {"JUNAIR"}


def list_field_dir(img: bytes) -> dict[str, tuple[int, int]]:
    """Return {NAME: (lba, size)} for every FIELD/*.DAT on the image."""
    out: dict[str, tuple[int, int]] = {}
    for path, info in walk_tree(img).items():
        if not path.startswith("FIELD/") or not path.endswith(".DAT"):
            continue
        name = path[len("FIELD/") : -len(".DAT")]
        out[name] = (info.lba, info.size)
    return out


def find_safe_whole_file_merges() -> dict[str, int]:
    """Return ``{field: disc}`` for single-owner non-D1 CSR edits."""
    pristine = {d: bytes(load_pristine_image(d)) for d in (1, 2, 3)}
    csr = {d: bytes(load_csr_image(d)) for d in (1, 2, 3)}
    listings = {d: list_field_dir(csr[d]) for d in (1, 2, 3)}
    all_names = sorted(set(listings[1]) | set(listings[2]) | set(listings[3]))

    out: dict[str, int] = dict(EXTRA_SAFE_WHOLE_FILE)
    for name in all_names:
        if name in REWORK_FIELDS or name in out or name in EXCLUDE_WHOLE_FILE:
            continue
        present = [d for d in (1, 2, 3) if name in listings[d]]
        if len(present) < 2:
            continue
        path = f"FIELD/{name}.DAT"
        edited = {}
        for d in present:
            data = extract_file(csr[d], path)
            try:
                pdata = extract_file(pristine[d], path)
                edited[d] = pdata != data
            except FileNotFoundError:
                edited[d] = True
        edited_discs = [d for d in present if edited[d]]
        if len(edited_discs) == 1 and edited_discs[0] != 1:
            out[name] = edited_discs[0]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bin", type=Path, required=True, help="work image: CSR D1 base + rework merge already applied")
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--in-place", action="store_true")
    args = ap.parse_args()

    if not args.in_place and not args.output:
        raise SystemExit("pass --in-place or -o/--output")

    print("Scanning CSR D1/D2/D3 for safe single-disc-edited fields...")
    merges = find_safe_whole_file_merges()
    print(f"Found {len(merges)} safe whole-file merges to apply.")

    print("Loading CSR D2/D3 reference images...")
    src_imgs = {2: bytes(load_csr_image(2)), 3: bytes(load_csr_image(3))}

    img = bytearray(args.bin.read_bytes())

    applied = 0
    for field, disc in sorted(merges.items()):
        path = f"FIELD/{field}.DAT"
        data = extract_file(src_imgs[disc], path)
        current = extract_file(img, path)
        if data == current:
            continue
        replace_file_within_sectors(img, path, data)
        print(f"  {field}: replaced with CSR D{disc} ({len(data)} bytes)")
        applied += 1

    out = args.bin if args.in_place else args.output
    out.write_bytes(img)
    print(f"\nApplied {applied}/{len(merges)} merges (rest already matched D1 base).")
    print(f"Wrote {out} ({len(img):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
