#!/usr/bin/env python3
"""Overwrite D1 MOVIE slots by per-disc MOVIE_ID.BIN row index (PMVIE id).

Field scripts use a disc-local movie id (PMVIE opcode, 1 byte). That id is
NOT sorted MOVIE/ directory order -- it's the row index into that disc's own
MINT/MOVIE_ID.BIN table (row[id].lba -> dirent lookup by LBA). Copying a
D2/D3 file onto D1 by filename would land at the wrong id. This tool copies
the source-disc file for id N into the existing D1 id N file.

  python3 scripts/inject_movies_by_disc_id.py --d1 work.bin --manifest movies.txt --in-place

Source discs are read from ``pristine/`` and the destination is a supplied
Disc 1 BIN. Movie data is copied as complete MODE2/2352 sectors because XA
Form 2 exposes 2336 payload bytes, not the 2048-byte Form 1 user region used
by ordinary ISO files. ISO9660 directory records are patched in both endian
forms and matching MOVIE_ID rows retain source engine size/auxiliary values.

Streams that fit reuse the destination allocation; growth is appended and
retargeted, and abandoned sectors after shrink are cleared. Use ``-o`` or
back up before ``--in-place``. The command does not regenerate Form 1 EDC/ECC
for modified metadata sectors; staged finalization performs that repair.
"""
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))

from psx_mode2_iso import (  # noqa: E402
    USER,
    _list_dir,
    _u32_le,
    _user,
    _write_user,
    extract_file,
    find_file,
    replace_file_padded,
)

PRISTINE = {
    2: _ROOT / "pristine/FINALFANTASY7_D2.bin",
    3: _ROOT / "pristine/FINALFANTASY7_D3.bin",
}


def _movie_entries(img: bytes):
    """Return Disc-local MOVIE files sorted the way PMVIE ids are indexed."""
    pvd = _user(img, 16)
    root = pvd[156:190]
    for name, lba, size, is_dir in _list_dir(img, _u32_le(root, 2), _u32_le(root, 10)):
        if name != "MOVIE" or not is_dir:
            continue
        ents = []
        for n, lb, sz, d in _list_dir(img, lba, size):
            if n in (".", "..") or d:
                continue
            ents.append((n, lb, sz))
        return sorted(ents, key=lambda x: x[0].upper())
    raise FileNotFoundError("MOVIE/")


def _id_for_name(entries, name: str) -> int:
    """Resolve a movie filename to its disc-local PMVIE row index."""
    u = name.upper()
    for i, (n, _l, _s) in enumerate(entries):
        if n.upper() == u:
            return i
    raise KeyError(name)


def _find_dirent(img: bytes, path: str):
    """Locate a file's raw ISO9660 record within its parent directory extent.

    The returned parent LBA/size and byte position let mutators update both
    endian copies without rebuilding or relocating the directory.
    """
    parts = [p for p in path.replace("\\", "/").upper().split("/") if p]
    pvd = _user(img, 16)
    root = pvd[156:190]
    dir_lba = _u32_le(root, 2)
    dir_size = _u32_le(root, 10)
    for idx, part in enumerate(parts):
        data = bytearray()
        remaining = dir_size
        sector = dir_lba
        while remaining > 0:
            take = min(USER, remaining)
            data.extend(_user(img, sector)[:take])
            remaining -= take
            sector += 1
        pos = 0
        found = None
        while pos < len(data):
            rlen = data[pos]
            if rlen == 0:
                pos = ((pos // USER) + 1) * USER
                continue
            name_len = data[pos + 32]
            flags = data[pos + 25]
            raw = bytes(data[pos + 33 : pos + 33 + name_len])
            if b";" in raw:
                raw = raw.split(b";")[0]
            try:
                sname = raw.decode("ascii")
            except Exception:
                sname = ""
            is_dir = bool(flags & 2)
            flba = _u32_le(bytes(data[pos : pos + rlen]), 2)
            fsize = _u32_le(bytes(data[pos : pos + rlen]), 10)
            if sname.upper() == part and idx == len(parts) - 1 and not is_dir:
                found = (dir_lba, dir_size, pos, bytes(data))
                break
            if sname.upper() == part and is_dir:
                dir_lba, dir_size = flba, fsize
                break
            pos += rlen
        else:
            if found is None and idx < len(parts) - 1:
                raise FileNotFoundError(path)
        if idx == len(parts) - 1:
            if found is None:
                raise FileNotFoundError(path)
            return found
    raise FileNotFoundError(path)


def _patch_dirent_lba_size(img: bytearray, path: str, new_lba: int, new_size: int) -> None:
    """Rewrite ISO9660 directory record LBA + size for path (both endian fields)."""
    dir_lba, dir_size, pos, _ = _find_dirent(bytes(img), path)
    remaining = dir_size
    sector = dir_lba
    data = bytearray()
    secs = []
    while remaining > 0:
        take = min(USER, remaining)
        secs.append(sector)
        data.extend(_user(img, sector)[:take])
        remaining -= take
        sector += 1
    # LBA at +2 LE / +6 BE; size at +10 LE / +14 BE
    struct.pack_into("<I", data, pos + 2, new_lba)
    struct.pack_into(">I", data, pos + 6, new_lba)
    struct.pack_into("<I", data, pos + 10, new_size)
    struct.pack_into(">I", data, pos + 14, new_size)
    off = 0
    rem = dir_size
    for s in secs:
        take = min(USER, rem)
        chunk = bytes(data[off : off + take])
        if take < USER:
            user = bytearray(_user(img, s))
            user[:take] = chunk
            _write_user(img, s, bytes(user))
        else:
            _write_user(img, s, chunk)
        off += take
        rem -= take
    meta = find_file(img, path)
    if meta.lba != new_lba or meta.size != new_size:
        raise RuntimeError(
            "dirent patch failed for %s (got lba=%s size=%s)"
            % (path, meta.lba, meta.size)
        )


def _set_file_size(img: bytearray, path: str, new_size: int) -> None:
    """Shrink a dirent size without allowing its sector allocation to grow."""
    meta = find_file(img, path)
    old_sec = (meta.size + USER - 1) // USER
    new_sec = (new_size + USER - 1) // USER
    if new_sec > old_sec:
        raise ValueError("%s needs more sectors" % path)
    _patch_dirent_lba_size(img, path, meta.lba, new_size)


def _raw_sectors(img: bytes | bytearray, lba: int, size: int) -> bytes:
    """Full MODE2/2352 slice for an ISO file (Form1 or Form2)."""
    from psx_mode2_iso import SECTOR

    nsec = (size + USER - 1) // USER
    off = lba * SECTOR
    return bytes(img[off : off + nsec * SECTOR])


def _write_raw_sectors(img: bytearray, dest_lba: int, raw: bytes) -> None:
    """Write complete 2352-byte sectors, extending only at sector boundaries."""
    from psx_mode2_iso import SECTOR

    if len(raw) % SECTOR:
        raise ValueError("raw length not multiple of 2352")
    nsec = len(raw) // SECTOR
    need = (dest_lba + nsec) * SECTOR
    if need > len(img):
        if len(img) % SECTOR:
            img.extend(b"\x00" * (SECTOR - (len(img) % SECTOR)))
        img.extend(b"\x00" * (need - len(img)))
    off = dest_lba * SECTOR
    img[off : off + len(raw)] = raw


def _zero_residual_sectors(
    img: bytearray, lba: int, old_iso_size: int, new_iso_size: int
) -> int:
    """Zero leftover MODE2 sectors after shrinking a MOVIE slot.

    Shrink injects leave the old stream's tail on disc. The XA player can still
    pick up residual audio (flicker/double audio) if size/aux is wrong or the
    decoder overruns. Always silence the abandoned tail.
    """
    from psx_mode2_iso import SECTOR

    old_nsec = (old_iso_size + USER - 1) // USER
    new_nsec = (new_iso_size + USER - 1) // USER
    if new_nsec >= old_nsec:
        return 0
    n = old_nsec - new_nsec
    off = (lba + new_nsec) * SECTOR
    end = off + n * SECTOR
    if end > len(img):
        end = len(img)
        n = max(0, (end - off) // SECTOR)
    img[off:end] = b"\x00" * (end - off)
    return n


def _append_file_grow(img: bytearray, path: str, data: bytes) -> int:
    """Deprecated Form1 path — use _append_raw_grow for FMV."""
    from psx_mode2_iso import SECTOR, USER_OFF

    new_sec = (len(data) + USER - 1) // USER
    if len(img) % SECTOR:
        img.extend(b"\x00" * (SECTOR - (len(img) % SECTOR)))
    new_lba = len(img) // SECTOR
    template = bytes(img[0:SECTOR])
    for i in range(new_sec):
        chunk = data[i * USER : (i + 1) * USER]
        if len(chunk) < USER:
            chunk = chunk + b"\x00" * (USER - len(chunk))
        sec = bytearray(template)
        sec[USER_OFF : USER_OFF + USER] = chunk
        img.extend(sec)
    _patch_dirent_lba_size(img, path, new_lba, len(data))
    return new_lba


def _append_raw_grow(img: bytearray, path: str, raw: bytes, size: int) -> int:
    """Append raw 2352 sectors and point dirent at them (Form2-safe FMV grow)."""
    from psx_mode2_iso import SECTOR

    if len(raw) % SECTOR:
        raise ValueError("raw length not multiple of 2352")
    if len(img) % SECTOR:
        img.extend(b"\x00" * (SECTOR - (len(img) % SECTOR)))
    new_lba = len(img) // SECTOR
    img.extend(raw)
    _patch_dirent_lba_size(img, path, new_lba, size)
    return new_lba



def _movie_id_meta_by_lba(img: bytes | bytearray, lba: int):
    """Return (size, a, b, c) from the first MOVIE_ID row with this LBA, or None.

    Rows are 20 bytes: LBA(4), size(4), auxA(4), auxB(4), auxC(4).
    For Form2 FMVs, size is usually sectors*2336 (not ISO 2048*sectors).
    """
    blob = extract_file(img, "MINT/MOVIE_ID.BIN")
    want = struct.pack("<I", lba)
    start = 0
    while True:
        pos = blob.find(want, start)
        if pos < 0:
            return None
        # Align to 20-byte records when possible
        if pos % 20 == 0 and pos + 20 <= len(blob):
            _l, size, a, b, c = struct.unpack_from("<IIIII", blob, pos)
            return (size, a, b, c)
        start = pos + 1


def _form2_size_field(iso_size: int) -> int:
    """Engine length used by most Form2 streams: nsec * 2336."""
    nsec = (iso_size + USER - 1) // USER
    return nsec * 2336


def _patch_movie_id_bin(
    img: bytearray,
    old_lba: int,
    new_lba: int,
    new_size: int,
    aux: tuple[int, int, int] | None = None,
) -> int:
    """Update MINT/MOVIE_ID.BIN engine table (20-byte rows: lba, size, a, b, c).

    The field movie player resolves streams via this table, not only ISO9660
    dirents. Growing a MOVIE slot without patching leaves the engine on the
    old LBA (wrong/short clip). Size must be the engine length (often
    sectors*2336), not the ISO9660 byte size — copy from source MOVIE_ID when
    injecting cross-disc Form2 streams or the player freezes mid-play.
    Returns number of LBA fields patched.
    """
    path = "MINT/MOVIE_ID.BIN"
    meta = find_file(img, path)
    blob = bytearray(extract_file(img, path))
    old_lba_b = struct.pack("<I", old_lba)
    patched = 0
    start = 0
    while True:
        pos = blob.find(old_lba_b, start)
        if pos < 0:
            break
        if pos + 8 <= len(blob):
            struct.pack_into("<I", blob, pos, new_lba)
            struct.pack_into("<I", blob, pos + 4, new_size)
            if aux is not None and pos + 20 <= len(blob) and pos % 20 == 0:
                a, b, c = aux
                struct.pack_into("<III", blob, pos + 8, a, b, c)
            patched += 1
        start = pos + 1
    if patched:
        if len(blob) != meta.size:
            raise RuntimeError("MOVIE_ID size changed unexpectedly")
        replace_file_padded(img, path, bytes(blob))
    return patched


def inject_one(
    d1: bytearray,
    src_img: bytes,
    movie: str,
    src_disc: int,
    target_d1=None,
    force_append: bool = False,
) -> dict:
    """Inject one source movie into its selected Disc 1 PMVIE slot.

    Returns source/destination metadata for the manifest report. A stream is
    never converted between Form 1 and Form 2 layouts.
    """
    src_ents = _movie_entries(src_img)
    d1_ents = _movie_entries(bytes(d1))
    # Always locate source file by name on the source disc (correct bytes).
    src_mid = _id_for_name(src_ents, movie)
    src_name, _slba, src_size = src_ents[src_mid]
    data = extract_file(src_img, "MOVIE/" + src_name)
    if len(data) != src_size:
        raise RuntimeError("extract size mismatch")

    # Destination on D1: explicit target (name or id), else same id as source disc.
    if target_d1 is None or target_d1 == "":
        mid = src_mid
    elif str(target_d1).isdigit():
        mid = int(target_d1)
    else:
        mid = _id_for_name(d1_ents, str(target_d1))
    if mid < 0 or mid >= len(d1_ents):
        raise SystemExit(
            "%s target D1 id %s invalid (D1 has %d movies)"
            % (movie, target_d1, len(d1_ents))
        )
    d1_name, _dlba, d1_size = d1_ents[mid]
    path = "MOVIE/" + d1_name
    grew = False
    movie_id_patches = 0
    old_meta = find_file(d1, path)
    old_lba, old_sz = old_meta.lba, old_meta.size
    # Always copy full MODE2/2352 sectors from source (Form2 FMV-safe).
    src_meta = find_file(src_img, "MOVIE/" + src_name)
    raw = _raw_sectors(src_img, src_meta.lba, src_meta.size)
    # Engine MOVIE_ID size/aux: prefer source-disc table (Form2-correct).
    src_mid_meta = _movie_id_meta_by_lba(src_img, src_meta.lba)
    if src_mid_meta is not None:
        eng_size, eng_a, eng_b, eng_c = src_mid_meta
        eng_aux: tuple[int, int, int] | None = (eng_a, eng_b, eng_c)
    else:
        eng_size = _form2_size_field(src_size)
        eng_aux = None
    src_nsec = (src_size + USER - 1) // USER
    dst_nsec = (d1_size + USER - 1) // USER
    # force_append: always new EOF LBA (avoid clobbering sibling movie slots that
    # already own this range, e.g. JAIROFAL/CANONON vs NRCRL path injects).
    if force_append or src_nsec > dst_nsec:
        new_lba = _append_raw_grow(d1, path, raw, src_size)
        grew = True
        note_lba = new_lba
        movie_id_patches = _patch_movie_id_bin(
            d1, old_lba, new_lba, eng_size, aux=eng_aux
        )
        if movie_id_patches < 1:
            raise SystemExit(
                "MOVIE_ID.BIN has no LBA entry for %s (old_lba=%s); engine would keep old stream"
                % (d1_name, old_lba)
            )
    else:
        # Shrink or same slot: write source 2352s, then silence abandoned tail.
        if src_size != d1_size:
            _set_file_size(d1, path, src_size)
        _write_raw_sectors(d1, old_lba, raw)
        # Residual zeroing is optional: correct Form2 eng_size is what stops
        # the player. Zeroing abandoned tails helps safety but makes huge layers.
        zapped = 0
        if __import__("os").environ.get("FF7_ZERO_MOVIE_RESIDUAL", "") == "1":
            zapped = _zero_residual_sectors(d1, old_lba, d1_size, src_size)
        note_lba = find_file(d1, path).lba
        # Engine length must be Form2-style (nsec*2336) from source table when
        # available — ISO byte size alone leaves wrong aux and can mix streams.
        if eng_size < _form2_size_field(src_size):
            # Source row missing or ISO-sized; force Form2 length.
            eng_size = _form2_size_field(src_size)
        movie_id_patches = _patch_movie_id_bin(
            d1, old_lba, note_lba, eng_size, aux=eng_aux
        )
    return {
        "movie": movie.upper(),
        "src_disc": src_disc,
        "id": mid,
        "d1_slot": d1_name,
        "src_bytes": len(data),
        "old_slot_bytes": d1_size,
        "grew": grew,
        "lba": note_lba,
        "movie_id_patches": movie_id_patches,
        "engine_size": eng_size,
        "residual_sectors_zeroed": locals().get("zapped", 0),
    }


def parse_manifest(path: Path):
    """Manifest lines:

      2 CANONON.MOV
      3 LASTFLOR.MOV
      2 CANONON.MOV ->JAIROFAL.MOV
      2 CANONON.MOV ->36

    Optional -> target is D1 movie name or PMVIE id (sorted MOVIE/ index on D1).
    With no target, the destination uses the source disc's movie id.
    """
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        target = None
        if "->" in line:
            left, right = line.split("->", 1)
            line = left.strip()
            target = right.strip()
        parts = line.split()
        if len(parts) == 1:
            rows.append((None, parts[0], target))
        elif len(parts) >= 2 and parts[0] in ("2", "3", "D2", "D3"):
            d = 2 if str(parts[0]).endswith("2") else 3
            rows.append((d, parts[1], target))
        else:
            raise SystemExit("bad manifest line: %r" % line)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--d1", type=Path, required=True)
    ap.add_argument("--from-disc", type=int, choices=(2, 3))
    ap.add_argument("--movie", action="append", default=[])
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--d2", type=Path, default=PRISTINE[2])
    ap.add_argument("--d3", type=Path, default=PRISTINE[3])
    ap.add_argument("--in-place", action="store_true")
    ap.add_argument("-o", "--output", type=Path)
    args = ap.parse_args()

    jobs = []
    for m in args.movie:
        if not args.from_disc:
            raise SystemExit("--from-disc required with --movie")
        jobs.append((args.from_disc, m, None))
    if args.manifest:
        for d, m, target in parse_manifest(args.manifest):
            if d is None:
                if not args.from_disc:
                    raise SystemExit("manifest line without disc needs --from-disc")
                d = args.from_disc
            jobs.append((d, m, target))
    if not jobs:
        raise SystemExit("provide --movie and/or --manifest")

    if not args.d1.is_file():
        raise SystemExit("missing d1: %s" % args.d1)
    d1 = bytearray(args.d1.read_bytes())
    cache = {}
    for disc, movie, target in jobs:
        if disc not in cache:
            src_path = args.d2 if disc == 2 else args.d3
            if not src_path.is_file():
                raise SystemExit("missing D%d: %s" % (disc, src_path))
            cache[disc] = src_path.read_bytes()
        info = inject_one(d1, cache[disc], movie, disc, target_d1=target)
        extra = ""
        if info.get("grew"):
            extra += " [GREW lba=%s]" % info["lba"]
        if info.get("movie_id_patches"):
            extra += " [MOVIE_ID x%s]" % info["movie_id_patches"]
        print(
            "OK D1 id=%d %s <- D%d %s (%d bytes; was %d; eng_size=%d)%s"
            % (
                info["id"],
                info["d1_slot"],
                info["src_disc"],
                info["movie"],
                info["src_bytes"],
                info["old_slot_bytes"],
                info.get("engine_size", 0),
                extra,
            )
        )

    out = args.d1 if args.in_place else args.output
    if out is None:
        raise SystemExit("pass --in-place or -o")
    out.write_bytes(bytes(d1))
    print("wrote %s (%d bytes)" % (out, len(d1)))
    print("injected %d movie(s)" % len(jobs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
