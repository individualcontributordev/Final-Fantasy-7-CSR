#!/usr/bin/env python3
"""Patch FIELD.BIN's/WORLD.BIN's embedded (location, size) lookup table so it
matches the actual ISO9660 directory-record sizes after field merges resize
FIELD/*.DAT files.

Root cause of Makou Reactor's "Invalid archive" (Cannot update game
binaries) on any save of our built .bin: ff7tk's IsoArchiveFF7::updateBin()
runs unconditionally on every pack() and rewrites FIELD.BIN's/WORLD.BIN's
compressed payload by searching it for each field's *current*
`(location, size)` 8-byte pair (see maplist()/updateBin() in
IsoArchiveFF7.cpp). Our build pipeline resizes several FIELD/*.DAT files in
place via replace_file_within_sectors() -- which patches the ISO9660
directory record -- but never touches FIELD.BIN's own embedded table, which
still has the pristine/CSR pre-merge size for that LBA. Any save then fails:
searching for the *new* size at that LBA finds nothing ("Error not found!"),
updateFieldBin() returns nullptr, reorganizeModifiedFilesAfter() fails, and
pack() reports InvalidError.

This patches every FIELD/*.DAT entry (and, symmetrically, every WORLD/*
entry actually present in WORLD.BIN's table) whose current directory-record
size differs from the single occurrence of its LBA found in the
decompressed FIELD.BIN/WORLD.BIN payload, then recompresses within the
original ISO slot's byte budget.

The destination BIN and current reconstructed CSR reference are inputs.
Only embedded little-endian ``(LBA,size)`` rows and the containing overlay's
ISO size are changed. Ambiguous LBA matches are resolved with the reference
size or rejected; overlays that cannot recompress inside their existing
sector allocation are rejected. Use an output path or back up before
``--in-place``. Form 1 EDC/ECC is repaired by a later stabilization stage.

Usage (from repo root):
  python3 scripts/fix_field_bin_table.py --bin work.bin --in-place
"""
from __future__ import annotations

import argparse
import gzip
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from compress_gzipps import compress_gzipps  # noqa: E402
from disc_sources import load_csr_image  # noqa: E402
from psx_mode2_iso import (  # noqa: E402
    USER,
    _list_dir,
    _u32_le,
    _user,
    extract_file,
    find_file,
    replace_file_within_sectors,
)


def _dir_entries(img: bytes, dir_path: str) -> list[tuple[str, int, int, bool]]:
    """Return direct ISO9660 children of a repository-known directory path."""
    pvd = _user(img, 16)
    root = pvd[156:190]
    lba, size = _u32_le(root, 2), _u32_le(root, 10)
    for part in dir_path.split("/"):
        entries = _list_dir(img, lba, size)
        match = next(e for e in entries if e[0] == part)
        lba, size = match[1], match[2]
    return _list_dir(img, lba, size)


def fix_bin_table(
    img: bytearray,
    bin_path: str,
    entries: list[tuple[str, int, int, bool]],
    skip_names: set[str],
    baseline_sizes: dict[str, int],
    target_offsets: dict[str, int] | None = None,
) -> int:
    """Patch bin_path's embedded (lba,size) table for entries whose current
    size mismatches the table. Returns count of entries patched.

    Disambiguates repeated 4-byte LBA matches (the table's 8-byte
    (lba,size) records aren't distinguishable from incidental 4-byte
    matches elsewhere in the payload) using each field's known pre-merge
    (CSR D1 baseline) size -- LBA never changes across our merges, only
    size, so (lba, baseline_size) is the unique key ff7tk's own
    updateBin() would have searched for before our edits.
    """
    raw = extract_file(bytes(img), bin_path)
    if raw[8:10] != b"\x1f\x8b":
        raise SystemExit(f"{bin_path} not gzipps @8")
    ungz = bytearray(gzip.decompress(raw[8:]))

    patched = 0
    for name, lba, size, is_dir in entries:
        if is_dir or name in skip_names:
            continue

        inferred_offset = (target_offsets or {}).get(name)
        if inferred_offset is not None:
            recorded_lba, recorded_size = struct.unpack_from(
                "<II",
                ungz,
                inferred_offset,
            )
            if recorded_lba != lba:
                raise SystemExit(
                    f"{bin_path}: inferred table offset {inferred_offset} "
                    f"contains LBA {recorded_lba}, expected {lba}"
                )
            if recorded_size == size:
                continue
            target_idx = inferred_offset
            old_size = recorded_size
            struct.pack_into("<I", ungz, target_idx + 4, size)
            print(f"  {bin_path} table: {name} @{lba} size {old_size} -> {size}")
            patched += 1
            continue

        lba_key = struct.pack("<I", lba)
        idxs = [i for i in range(len(ungz) - 4) if ungz[i:i + 4] == lba_key]
        if not idxs:
            continue  # not referenced by this bin's table (e.g. WORLD.BIN)
        matching = [i for i in idxs if struct.unpack_from("<I", ungz, i + 4)[0] == size]
        if matching:
            continue  # already correct
        target_idx: int
        if len(idxs) == 1:
            target_idx = idxs[0]
        else:
            baseline = baseline_sizes.get(name)
            baseline_hits = [
                i for i in idxs if baseline is not None
                and struct.unpack_from("<I", ungz, i + 4)[0] == baseline
            ]
            if len(baseline_hits) != 1:
                raise SystemExit(
                    f"{bin_path}: {name} LBA {lba} has {len(idxs)} ambiguous table "
                    f"occurrences; baseline size {baseline} matched {len(baseline_hits)}"
                )
            target_idx = baseline_hits[0]
        old_size = struct.unpack_from("<I", ungz, target_idx + 4)[0]
        struct.pack_into("<I", ungz, target_idx + 4, size)
        print(f"  {bin_path} table: {name} @{lba} size {old_size} -> {size}")
        patched += 1

    if patched == 0:
        return 0

    meta = find_file(img, bin_path)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        dec_path = td / "bin.dec"
        orig_path = td / "bin.orig"
        out_path = td / "bin.new"
        dec_path.write_bytes(bytes(ungz))
        orig_path.write_bytes(raw)
        compress_gzipps(dec_path, orig_path, out_path)
        new_raw = out_path.read_bytes()

    cap = ((meta.size + USER - 1) // USER) * USER
    if len(new_raw) > cap:
        raise SystemExit(f"{bin_path}: recompressed {len(new_raw)} > slot capacity {cap}")
    replace_file_within_sectors(img, bin_path, new_raw)
    return patched


def _baseline_sizes(dir_path: str, ref_disc: int = 1) -> dict[str, int]:
    """name -> size in the pristine CSR reference disc (LBA is stable across
    our field merges; this disambiguates repeated raw LBA matches)."""
    ref = bytes(load_csr_image(ref_disc))
    return {name: size for name, _lba, size, is_dir in _dir_entries(ref, dir_path) if not is_dir}


def fix_field_and_world_bins(img: bytearray) -> int:
    """Repair both embedded tables and return the number of changed rows."""
    field_entries = _dir_entries(bytes(img), "FIELD")
    total = fix_bin_table(
        img, "FIELD/FIELD.BIN", field_entries, skip_names={"FIELD.BIN"},
        baseline_sizes=_baseline_sizes("FIELD"),
    )
    world_entries = _dir_entries(bytes(img), "WORLD")
    total += fix_bin_table(
        img, "WORLD/WORLD.BIN", world_entries, skip_names={"WORLD.BIN"},
        baseline_sizes=_baseline_sizes("WORLD"),
    )
    return total


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bin", type=Path, required=True)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--in-place", action="store_true")
    args = ap.parse_args()
    if not args.in_place and not args.output:
        raise SystemExit("pass --in-place or -o/--output")

    img = bytearray(args.bin.read_bytes())
    print("Fixing FIELD.BIN/WORLD.BIN embedded (location,size) tables...")
    total = fix_field_and_world_bins(img)
    print(f"Total table entries patched: {total}")

    out = args.bin if args.in_place else args.output
    out.write_bytes(img)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
