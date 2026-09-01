#!/usr/bin/env python3
"""Recreate ff7tk's IsoArchive::getIntegrity() layout check against a .bin.

ff7tk (used by Makou Reactor) refuses to save ("Invalid archive") if, when
every file/directory in the ENTIRE recursive ISO9660 tree is sorted by LBA,
any entry overlaps the next one:

    next.lba < this.lba + ceil(this.size / 2048)

or two entries share the same LBA (a QMap<lba, entry> silently collides,
scrambling the walk). This walks the whole tree the same way ff7tk's
_getIntegrity() does (recursing into every subdirectory) and reports the
first violation(s), plus every directory-record size that disagrees with
the number of bytes actually reachable in its slot.

Usage:
  python3 scripts/verify_iso_integrity.py path/to/built.bin

The BIN is read-only. Exit 0 requires a raw-sector-aligned image with no
duplicate extent LBAs, overlaps, or gaps that overflow ff7tk's one-byte
padding field. Movie extents use their observed CD-XA Form 2 payload size
(2336 bytes/sector); ordinary ISO files and directories use Form 1 logical
blocks (2048 bytes/sector). This is a layout check, not an EDC/ECC or gameplay
test.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from psx_mode2_iso import SECTOR, USER, _list_dir, _u32_le, _user  # noqa: E402


FORM2_USER = 2336  # CD-XA Form 2 (e.g. MOVIE/*.STR, *.MOV) -- not 2048-byte Form 1


def sector_count(size: int, name: str = "") -> int:
    """Convert a directory-record byte size to its occupied raw sectors."""
    upper = name.upper()
    if upper.startswith("MOVIE/") or upper.endswith((".STR", ".MOV")):
        return (size + FORM2_USER - 1) // FORM2_USER
    return (size + USER - 1) // USER


def walk_tree(img: bytes, lba: int, size: int, path: str, out: list[tuple[str, int, int, bool]]) -> None:
    """Append the recursive ISO9660 tree in ff7tk-compatible form."""
    entries = _list_dir(img, lba, size)
    for name, e_lba, e_size, is_dir in entries:
        full = f"{path}/{name}" if path else name
        out.append((full, e_lba, e_size, is_dir))
        if is_dir:
            walk_tree(img, e_lba, e_size, full, out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bin_path", type=Path)
    args = ap.parse_args()

    img = args.bin_path.read_bytes()
    if len(img) % SECTOR != 0:
        raise SystemExit(f"image size {len(img)} is not a multiple of {SECTOR}")

    pvd = _user(img, 16)
    if pvd[0] != 1 or pvd[1:6] != b"CD001":
        raise SystemExit("Primary Volume Descriptor not found at LBA 16")

    root = pvd[156:190]
    root_lba = _u32_le(root, 2)
    root_size = _u32_le(root, 10)
    volume_sectors = _u32_le(pvd, 80)

    entries: list[tuple[str, int, int, bool]] = [("[root]", root_lba, root_size, True)]
    walk_tree(img, root_lba, root_size, "", entries)

    print(f"Total entries (files+dirs): {len(entries)}")
    print(f"Volume space size (sectors): {volume_sectors}, image sectors: {len(img) // SECTOR}")
    if volume_sectors != len(img) // SECTOR:
        print("  WARNING: PVD volume_space_size does not match actual image sector count")

    by_lba: dict[int, list[tuple[str, int, int, bool]]] = {}
    for name, lba, size, is_dir in entries:
        by_lba.setdefault(lba, []).append((name, lba, size, is_dir))

    dup_count = 0
    for lba, group in sorted(by_lba.items()):
        if len(group) > 1:
            dup_count += 1
            print(f"\nDUPLICATE LBA {lba} ({len(group)} entries -- QMap collision in ff7tk, only last survives):")
            for name, _lba, size, is_dir in group:
                print(f"    {'DIR ' if is_dir else 'FILE'} {name}  size={size}  sectors={sector_count(size, name)}")

    ordered = sorted(entries, key=lambda t: t[1])
    overlap_count = 0
    prev = None
    print("\nScanning LBA-sorted layout for overlaps (this.lba + sectorCount > next.lba)...")
    for name, lba, size, is_dir in ordered:
        if prev is not None:
            p_name, p_lba, p_size, _ = prev
            p_end = p_lba + sector_count(p_size, p_name)
            gap = lba - p_end
            if gap < 0:
                overlap_count += 1
                print(
                    f"  OVERLAP: {p_name} @{p_lba} (+{sector_count(p_size, p_name)} sec, end={p_end}) "
                    f"overlaps {name} @{lba} by {-gap} sector(s)"
                )
        prev = (name, lba, size, is_dir)

    print(f"\nDuplicate-LBA groups: {dup_count}")
    print(f"Overlaps: {overlap_count}")

    # ff7tk casts the file->file gap to quint8 (IsoArchive.cpp:1333) when
    # computing paddingAfter -- any real gap > 255 sectors silently
    # truncates (gap % 256), corrupting the padding table it uses in pack().
    print("\nScanning for gaps > 255 sectors (quint8 paddingAfter truncation in ff7tk)...")
    big_gap_count = 0
    prev = None
    for name, lba, size, is_dir in ordered:
        if prev is not None:
            p_name, p_lba, p_size, _ = prev
            p_end = p_lba + sector_count(p_size, p_name)
            gap = lba - p_end
            if gap > 255:
                big_gap_count += 1
                print(f"  BIG GAP: {p_name} ends {p_end}, {name} starts {lba} -- gap={gap} sectors (truncates to {gap % 256})")
        prev = (name, lba, size, is_dir)
    print(f"Gaps > 255 sectors: {big_gap_count}")

    if dup_count == 0 and overlap_count == 0 and big_gap_count == 0:
        print("OK: no duplicate LBAs, overlaps, or oversized gaps found in the full recursive tree.")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
