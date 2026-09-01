#!/usr/bin/env python3
"""Place the Disc 3 ending stream at its hardcoded seek LBA on Disc 1.

The post-final-battle path seeks MSF 43:51:67 (ISO LBA 197242), the tracked
NTSC-U Disc 3 start of ENDING2E.MOV. Updating MOVIE_ID alone cannot satisfy an
absolute seek, so the corresponding Form 2 MODE2/2352 sectors must physically
exist at that LBA.

Disc 1 and pristine Disc 3 are inputs. The raw write stops at the next Disc 1
MOVIE extent instead of relocating or overwriting that file, so ENDING2E is
deliberately truncated. Its selected Disc 1 ISO9660 record and MOVIE_ID row
receive the truncated sector count, and the PVD volume size follows any image
growth. Constants are revision-specific; this is not a general relocator.
Unexpected files/rows abort, output is new unless ``--in-place`` is selected,
and finalization must repair changed Form 1 metadata-sector EDC/ECC.

  python3 scripts/alias_d3_ending_lbas_on_d1.py \\
    --d1 workspace/iso-extract/ff7_d1_playtest_ending_test.bin --in-place
"""
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))

from inject_movies_by_disc_id import (  # noqa: E402
    _movie_id_meta_by_lba,
    _patch_dirent_lba_size,
    _patch_movie_id_bin,
)
from psx_mode2_iso import (  # noqa: E402
    SECTOR,
    USER,
    _list_dir,
    _u32_le,
    _user,
    extract_file,
    find_file,
    replace_file_padded,
    set_pvd_volume_space_size,
)

# (MOVIE_ID row, Disc 3 movie, Disc 1 slot to retarget). A captured complete
# post-battle path seeks only ENDING2E's absolute LBA; adding unobserved ending
# aliases would enlarge the layer and risk unrelated Disc 1 movie extents.
JOBS = (
    (29, "ENDING2E.MOV", "MONITOR.STR"),
)

PRISTINE_D3 = _ROOT / "pristine/FINALFANTASY7_D3.bin"


def _raw(src: bytes, lba: int, nsec: int) -> bytes:
    """Slice complete raw sectors without interpreting Form 2 payload bytes."""
    off = lba * SECTOR
    return src[off : off + nsec * SECTOR]


def _write_raw(img: bytearray, lba: int, raw: bytes) -> None:
    """Write sector-aligned bytes at an absolute LBA, growing with zeros."""
    if len(raw) % SECTOR:
        raise ValueError("raw length not multiple of 2352")
    nsec = len(raw) // SECTOR
    need = (lba + nsec) * SECTOR
    if need > len(img):
        if len(img) % SECTOR:
            img.extend(b"\x00" * (SECTOR - (len(img) % SECTOR)))
        img.extend(b"\x00" * (need - len(img)))
    off = lba * SECTOR
    img[off : off + len(raw)] = raw


def _movie_files(img: bytes | bytearray):
    """List file records directly below the Disc 1 MOVIE directory."""
    pvd = _user(img, 16)
    root = pvd[156:190]
    for n, lba, sz, d in _list_dir(img, _u32_le(root, 2), _u32_le(root, 10)):
        if n == "MOVIE" and d:
            return [
                (nn, lb, ss)
                for nn, lb, ss, dd in _list_dir(img, lba, sz)
                if nn not in (".", "..") and not dd
            ]
    raise FileNotFoundError("MOVIE/")


def _relocate_collisions(
    img: bytearray, ranges: list[tuple[int, int]], keep_names: set[str]
) -> list[str]:
    """Move every D1 MOVIE/ file whose sectors overlap `ranges` to EOF.

    `keep_names` are the D1 slots the caller is about to overwrite on purpose
    (the ending-stream targets) -- those are skipped here since clobbering
    them is the intended effect, not a collision to repair. Every other
    overlapping file is relocated so the raw ending-stream write can't
    physically stomp its sectors.
    """
    notes: list[str] = []
    for name, lba, size in sorted(_movie_files(bytes(img)), key=lambda x: x[1]):
        if name.upper() in keep_names:
            continue
        nsec = (size + USER - 1) // USER
        file_end = lba + nsec - 1
        if not any(file_end >= r0 and lba <= r1 for r0, r1 in ranges):
            continue
        path = "MOVIE/" + name
        raw = _raw(bytes(img), lba, nsec)
        new_lba = len(img) // SECTOR if len(img) % SECTOR == 0 else (len(img) // SECTOR) + 1
        _write_raw(img, new_lba, raw)
        _patch_dirent_lba_size(img, path, new_lba, size)
        # MOVIE_ID.BIN's "size" field is the Form2 engine length
        # (nsec*2336, sometimes not exactly that), NOT the ISO9660 dirent
        # byte size -- overwriting it with `size` (ISO bytes) here was the
        # actual root cause of relocated movies not playing (engine size
        # field went from e.g. 5847008 to 5126144 for PLREXP). Preserve the
        # existing engine size + aux fields verbatim; only the LBA changes.
        eng_meta = _movie_id_meta_by_lba(img, lba)
        if eng_meta is not None:
            eng_size, a, b, c = eng_meta
            n = _patch_movie_id_bin(img, lba, new_lba, eng_size, aux=(a, b, c))
        else:
            notes.append(f"WARN {name}: no MOVIE_ID row found for LBA {lba}, using ISO size")
            n = _patch_movie_id_bin(img, lba, new_lba, size)
        notes.append(
            f"RELOCATE {name} LBA {lba}..{file_end} -> EOF LBA {new_lba} "
            f"(MOVIE_ID x{n})"
        )
    return notes


def apply(img: bytearray, d3: bytes) -> list[str]:
    """Apply configured ending aliases in memory and return audit messages."""
    blob3 = extract_file(d3, "MINT/MOVIE_ID.BIN")
    notes: list[str] = []

    # The active policy avoids relocation because changing unrelated file
    # LBAs expands the mutation surface. The write below is instead capped at
    # the next Disc 1 MOVIE extent.

    blob = bytearray(extract_file(img, "MINT/MOVIE_ID.BIN"))
    for mid, d3name, d1name in JOBS:
        m3 = find_file(d3, f"MOVIE/{d3name}")
        nsec = (m3.size + USER - 1) // USER
        r3 = struct.unpack_from("<IIIII", blob3, mid * 20)
        d3_lba = m3.lba
        if r3[0] != d3_lba:
            notes.append(
                f"WARN id{mid}: MOVIE_ID LBA {r3[0]} != file {d3_lba}; using file"
            )
        # Cap the write at the nearest later movie LBA. This makes the
        # incomplete ending an explicit tradeoff and preserves every
        # unrelated Disc 1 movie extent.
        other_lbas = [
            lb for nm, lb, _sz in _movie_files(bytes(img))
            if lb > d3_lba and nm.upper() != d1name.upper()
        ]
        max_nsec = min(other_lbas) - d3_lba if other_lbas else nsec
        eng_nsec = min(nsec, max_nsec)
        if eng_nsec < nsec:
            notes.append(
                f"TRUNCATE id{mid} {d3name}: {nsec} -> {eng_nsec} sectors "
                f"(next MOVIE/ file at LBA {d3_lba + eng_nsec})"
            )
        raw = _raw(d3, d3_lba, eng_nsec)
        _write_raw(img, d3_lba, raw)
        eng_size = eng_nsec * 2336
        _patch_dirent_lba_size(img, f"MOVIE/{d1name}", d3_lba, eng_nsec * USER)
        struct.pack_into(
            "<IIIII", blob, mid * 20, d3_lba, eng_size, r3[2], r3[3], r3[4]
        )
        notes.append(
            f"OK id{mid} {d3name} -> {d1name} LBA={d3_lba} nsec={eng_nsec} eng={eng_size}"
        )
    replace_file_padded(img, "MINT/MOVIE_ID.BIN", bytes(blob))
    if len(img) % SECTOR:
        img.extend(b"\x00" * (SECTOR - (len(img) % SECTOR)))
    # Relocation + the raw D3 write can grow the image past the PVD's
    # original volume space size. Update it so the ISO9660 driver doesn't
    # treat the new EOF sectors (relocated MOVIE/ files, ENDING2E) as past
    # end-of-disc and refuse to read them.
    new_nsectors = len(img) // SECTOR
    old_nsectors = _u32_le(_user(img, 16), 80)
    if new_nsectors != old_nsectors:
        set_pvd_volume_space_size(img, new_nsectors)
        notes.append(f"PVD volume space size {old_nsectors} -> {new_nsectors}")
    return notes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--d1", type=Path, required=True)
    ap.add_argument("--d3", type=Path, default=PRISTINE_D3)
    ap.add_argument("--in-place", action="store_true")
    ap.add_argument("-o", "--output", type=Path)
    args = ap.parse_args()
    if not args.d1.is_file():
        print("missing", args.d1, file=sys.stderr)
        return 1
    if not args.d3.is_file():
        print("missing", args.d3, file=sys.stderr)
        return 1
    img = bytearray(args.d1.read_bytes())
    d3 = args.d3.read_bytes()
    for line in apply(img, d3):
        print(line)
    out = args.d1 if args.in_place else args.output
    if out is None:
        print("pass --in-place or -o", file=sys.stderr)
        return 2
    out.write_bytes(img)
    print("wrote", out, len(img), "bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
