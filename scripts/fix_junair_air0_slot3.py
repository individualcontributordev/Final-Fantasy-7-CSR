#!/usr/bin/env python3
"""Apply the guarded CSR Disc 2 JUNAIR script/text fix to Disc 1.

Usage:
  python3 scripts/fix_junair_air0_slot3.py \\
    --bin workspace/iso-extract/work.bin --in-place

The destination BIN and reconstructed CSR Disc 2 are inputs. The command
replaces physical script slot ``air0/3`` and the complete Disc 2 text-table
blob, then reparses and verifies both before replacing ``FIELD/JUNAIR.DAT``.
Exact expected old/new opcode bytes make the patch revision-specific and
idempotent; unknown bytes abort rather than being guessed. The rewritten DAT
must fit its existing ISO sector allocation. Back up before ``--in-place``;
footer and embedded-table repair happen in later stages.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from disc_sources import load_csr_image  # noqa: E402
from field_dat import load_field_dat  # noqa: E402
from field_dat_write import write_field_dat  # noqa: E402
from psx_mode2_iso import extract_file, replace_file_within_sectors  # noqa: E402

FIELD = "FIELD/JUNAIR.DAT"

ENTITY, SLOT = "air0", 3
# CSR D1 / pristine D1+D2 (air0,3): IFSW.., MAPJUMP, RET
SLOT_ORIGINAL = bytes.fromhex("16200000f803050b60810111f1f6fb41000000")
# CSR D2 (air0,3): IFSW.., AKAO, PRTYE, PRTYE, MMBLK, BITON, MAPJUMP, MAPJUMP, RET
SLOT_PATCHED = bytes.fromhex(
    "16200000f8030531f2000000c1780000000000000000cafefefeca02fefece"
    "028210e206609201b000250001008060810111f1f6fb41000000"
)

# Disc 2 includes one additional empty text-table entry.


def _fix_slot(fd) -> dict:
    """Return the guarded slot edit or an empty mapping when already applied.

    Exact-byte comparison prevents applying this revision-specific patch to a
    field whose script ownership or opcode sequence has changed.
    """
    slot = next((s for s in fd.scripts if s.entity == ENTITY and s.slot == SLOT), None)
    if slot is None:
        raise SystemExit(f"{FIELD}: no {ENTITY}/{SLOT} script slot found")
    if slot.raw == SLOT_PATCHED:
        print(f"  {ENTITY}/{SLOT} already patched, nothing to do")
        return {}
    if slot.raw != SLOT_ORIGINAL:
        raise SystemExit(
            f"{FIELD} {ENTITY}/{SLOT}: unexpected script bytes {slot.raw.hex()}, "
            f"expected {SLOT_ORIGINAL.hex()}"
        )
    print(f"  {FIELD} {ENTITY}/{SLOT}: applied CSR D2 fix "
          f"({len(SLOT_ORIGINAL)} -> {len(SLOT_PATCHED)} bytes)")
    return {(ENTITY, SLOT): SLOT_PATCHED}


def _d2_texts_raw() -> bytes:
    """Load the complete CSR Disc 2 text-table blob paired with the slot edit."""
    c2 = bytes(load_csr_image(2))
    fd2 = load_field_dat(extract_file(c2, FIELD))
    return fd2.texts_raw


def fix_junair(img: bytearray) -> bool:
    """Patch and verify JUNAIR in memory; return whether bytes changed."""
    raw = extract_file(bytes(img), FIELD)
    fd = load_field_dat(raw)

    edits = _fix_slot(fd)
    if not edits:
        return False

    new_texts_raw = _d2_texts_raw()
    if new_texts_raw == fd.texts_raw:
        new_texts_raw = None  # already matches (e.g. re-running on a patched image)

    new_raw = write_field_dat(fd, edits, new_texts_raw=new_texts_raw)
    fd2 = load_field_dat(new_raw)
    for (entity, slot_idx), expected in edits.items():
        new_slot = next(s for s in fd2.scripts if s.entity == entity and s.slot == slot_idx)
        if new_slot.raw != expected:
            raise SystemExit(f"post-write verification failed: {entity}/{slot_idx} not patched as expected")
    if new_texts_raw is not None and fd2.texts_raw != new_texts_raw:
        raise SystemExit("post-write verification failed: texts_raw not spliced as expected")
    replace_file_within_sectors(img, FIELD, new_raw)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bin", type=Path, required=True)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--in-place", action="store_true")
    args = ap.parse_args()
    if not args.in_place and not args.output:
        raise SystemExit("pass --in-place or -o/--output")

    img = bytearray(args.bin.read_bytes())
    print("Applying CSR JUNAIR air0/3 fix (field 384, Junon airfield)...")
    fix_junair(img)

    out = args.bin if args.in_place else args.output
    out.write_bytes(img)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
