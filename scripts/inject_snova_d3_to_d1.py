#!/usr/bin/env python3
"""Copy D3 SNOVA onto D1 and remap BATTLE.X hardcoded LBAs.

Root cause of Supernova freeze after SNOVA file inject: BATTLE.X embeds
absolute D3 sector numbers for SNOVA0-15 and LASBOSS3. Files on D1 at a
new LBA are never read for the effect; audio path may still tick.

  python3 scripts/inject_snova_d3_to_d1.py \
    --d1 workspace/iso-extract/ff7_d1_snova_test.bin \
    --d3 pristine/FINALFANTASY7_D3.bin \
    --in-place

The command verifies the tracked Disc 3 SNOVA directory LBA and contiguous
570-sector layout, appends that raw MODE2/2352 block to Disc 1, and creates
matching ISO9660 directory/path-table records. It then changes only the
verified little-endian LBA words at the listed decompressed BATTLE.X offsets
and recompresses within BATTLE.X's existing slot.

The constants are revision-specific assumptions, not a general SNOVA locator;
unexpected source layout or MIPS-data words abort. Output is new unless
``--in-place`` is requested. Metadata Form 1 footers are zeroed or stale after
this operation and must be repaired by staged finalization before publishing.
"""
from __future__ import annotations

import argparse
import gzip
import struct
import sys
import tempfile
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS))

from compress_gzipps import compress_gzipps  # noqa: E402
from psx_mode2_iso import (  # noqa: E402
    SECTOR,
    USER,
    _list_dir,
    _read_extent,
    _u32_le,
    _user,
    extract_file,
    find_file,
    replace_file_padded,
)

D3_SNOVA_DIR_LBA = 127100
D3_SNOVA_SECTORS = 570

# Decompressed BATTLE.X offsets: (D3_LBA, file_off_of_u32_lba)
# Pairs at 0x48d78+: SNOVA0..SNOVA15 as (lba, padded_size); sizes unchanged.
BATTLE_SNOVA_LBA_OFF = [
    (127254, 0x48D78),  # SNOVA0
    (127293, 0x48D80),  # SNOVA1
    (127320, 0x48D88),  # SNOVA2
    (127354, 0x48D90),  # SNOVA3
    (127373, 0x48D98),  # SNOVA4
    (127394, 0x48DA0),  # SNOVA5
    (127430, 0x48DA8),  # SNOVA6
    (127442, 0x48DB0),  # SNOVA7
    (127464, 0x48DB8),  # SNOVA8
    (127503, 0x48DC0),  # SNOVA9
    (127544, 0x48DC8),  # SNOVA10
    (127555, 0x48DD0),  # SNOVA11
    (127562, 0x48DD8),  # SNOVA12
    (127571, 0x48DE0),  # SNOVA13
    (127618, 0x48DE8),  # SNOVA14
    (127649, 0x48DF0),  # SNOVA15
]
BATTLE_LASBOSS3_OFF = (127101, 0x4F5A8)


def both_u32(v: int) -> bytes:
    """Encode an ISO9660 32-bit field in little- then big-endian order."""
    return struct.pack("<I", v) + struct.pack(">I", v)


def bcd(x: int) -> int:
    return ((x // 10) << 4) | (x % 10)


def lba_to_msf(lba: int) -> bytes:
    """Convert an ISO LBA to the BCD absolute address stored in raw headers."""
    a = lba + 150
    m, s, f = a // 4500, (a % 4500) // 75, a % 75
    return bytes([bcd(m), bcd(s), bcd(f)])


def fix_sector_msf(img: bytearray, lba: int) -> None:
    """Update one copied sector header for its new physical LBA."""
    base = lba * SECTOR
    img[base + 12 : base + 15] = lba_to_msf(lba)


def dir_rec(name: str, lba: int, size: int, is_dir: bool) -> bytes:
    """Build the minimal ISO9660 directory record used by the SNOVA extent."""
    if name == ".":
        nm = bytes([0])
    elif name == "..":
        nm = bytes([1])
    else:
        nm = name.encode("ascii")
    nlen = len(nm)
    length = 33 + nlen + (nlen % 2)
    rec = bytearray(length)
    rec[0] = length
    rec[2:10] = both_u32(lba)
    rec[10:18] = both_u32(size)
    rec[25] = 0x02 if is_dir else 0x00
    rec[28:32] = struct.pack("<H", 1) + struct.pack(">H", 1)
    rec[32] = nlen
    rec[33 : 33 + nlen] = nm
    return bytes(rec)


def write_user_sector(img: bytearray, lba: int, user: bytes, hdr_from: int) -> None:
    """Write Form 1 user bytes using a template header and cleared footer.

    Clearing the footer prevents stale parity from appearing valid; the
    staged builder regenerates EDC/ECC after all metadata writes finish.
    """
    assert len(user) == USER
    base = lba * SECTOR
    src = hdr_from * SECTOR
    img[base : base + 24] = img[src : src + 24]
    img[base + 24 : base + 24 + USER] = user
    img[base + 24 + USER : base + SECTOR] = b"\x00" * (SECTOR - 24 - USER)
    fix_sector_msf(img, lba)


def path_L(name: str, lba: int, parent: int) -> bytes:
    """Build one little-endian ISO9660 path-table record."""
    if name == "\x00":
        nm = bytes([0])
    elif name == "\x01":
        nm = bytes([1])
    else:
        nm = name.encode("ascii")
    di = len(nm)
    rec = bytes([di, 0]) + struct.pack("<I", lba) + struct.pack("<H", parent) + nm
    return rec + (b"\x00" if di % 2 else b"")


def path_M(name: str, lba: int, parent: int) -> bytes:
    """Build one big-endian ISO9660 path-table record."""
    if name == "\x00":
        nm = bytes([0])
    elif name == "\x01":
        nm = bytes([1])
    else:
        nm = name.encode("ascii")
    di = len(nm)
    rec = bytes([di, 0]) + struct.pack(">I", lba) + struct.pack(">H", parent) + nm
    return rec + (b"\x00" if di % 2 else b"")


def parse_path_L(blob: bytes) -> list:
    """Split a little-endian path table into records without reinterpreting it."""
    out, i = [], 0
    while i < len(blob):
        di = blob[i]
        if di == 0:
            break
        n = 8 + di + (di % 2)
        out.append(blob[i : i + n])
        i += n
    return out


def ent_name_L(e: bytes) -> str:
    """Decode a path-table identifier, including root/current sentinels."""
    di = e[0]
    raw = e[8 : 8 + di]
    if di == 1 and raw[0] in (0, 1):
        return "\x00" if raw[0] == 0 else "\x01"
    return raw.decode("ascii")


def patch_dir_lbas(user: bytearray, delta: int, new_self: int, new_parent: int) -> None:
    """Relocate every extent in a copied directory sector by one LBA delta.

    ``.`` and ``..`` are structural links and therefore receive explicit
    self/parent LBAs instead of the file-extent delta.
    """
    i = 0
    while i < len(user):
        ln = user[i]
        if ln == 0:
            break
        name_len = user[i + 32]
        name = bytes(user[i + 33 : i + 33 + name_len])
        if name_len == 1 and name[0] == 0:
            user[i + 2 : i + 10] = both_u32(new_self)
            user[i + 10 : i + 18] = both_u32(USER)
        elif name_len == 1 and name[0] == 1:
            user[i + 2 : i + 10] = both_u32(new_parent)
        else:
            old = struct.unpack_from("<I", user, i + 2)[0]
            user[i + 2 : i + 10] = both_u32(old + delta)
        i += ln


def patch_battle_x_lbas(img: bytearray, delta: int) -> None:
    """Rewrite only expected D3 SNOVA LBA words, then recompress BATTLE.X."""
    raw = extract_file(img, "BATTLE/BATTLE.X")
    if raw[8:10] != b"\x1f\x8b":
        raise SystemExit("BATTLE.X not gzipps @8")
    dec = bytearray(gzip.decompress(raw[8:]))
    patches = list(BATTLE_SNOVA_LBA_OFF) + [BATTLE_LASBOSS3_OFF]
    for d3_lba, off in patches:
        cur = struct.unpack_from("<I", dec, off)[0]
        if cur != d3_lba:
            raise SystemExit("BATTLE.X LBA mismatch at 0x%X: got %s want %s" % (off, cur, d3_lba))
        new = d3_lba + delta
        struct.pack_into("<I", dec, off, new)
        print("  BATTLE.X LBA 0x%X: %s -> %s" % (off, d3_lba, new))
    # recompress into original size budget
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        dec_path = td / "BATTLE.X.dec"
        orig_path = td / "BATTLE.X.orig"
        out_path = td / "BATTLE.X.new"
        dec_path.write_bytes(dec)
        orig_path.write_bytes(raw)
        compress_gzipps(dec_path, orig_path, out_path)
        new_raw = out_path.read_bytes()
    if len(new_raw) > len(raw):
        raise SystemExit("BATTLE.X recompress %s > original %s" % (len(new_raw), len(raw)))
    print("  BATTLE.X recompress %s -> %s (pad %s)" % (len(raw), len(new_raw), len(raw) - len(new_raw)))
    replace_file_padded(img, "BATTLE/BATTLE.X", new_raw)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--d1", type=Path, required=True)
    ap.add_argument("--d3", type=Path, required=True)
    ap.add_argument("--in-place", action="store_true")
    ap.add_argument("-o", type=Path)
    ap.add_argument("--skip-battle-patch", action="store_true")
    args = ap.parse_args()

    img = bytearray(args.d1.read_bytes())
    d3 = args.d3.read_bytes()
    try:
        find_file(img, "SNOVA/SNOVA0.LZS")
        raise SystemExit("D1 already has SNOVA/ — abort (rebuild from pristine/bak)")
    except FileNotFoundError:
        pass

    pvd3 = _user(d3, 16)
    root3 = pvd3[156:190]
    snova_meta = None
    for name, lb, sz, isdir in _list_dir(d3, _u32_le(root3, 2), _u32_le(root3, 10)):
        if name == "SNOVA" and isdir:
            snova_meta = (lb, sz)
            break
    if not snova_meta or snova_meta[0] != D3_SNOVA_DIR_LBA:
        raise SystemExit("unexpected D3 SNOVA dir LBA %r" % (snova_meta,))

    files = sorted(
        (n, lb, sz)
        for n, lb, sz, isd in _list_dir(d3, snova_meta[0], snova_meta[1])
        if n not in (".", "..") and not isd
    )
    first_file_lba = min(lb for _, lb, _ in files)
    last = max(lb + (sz + USER - 1) // USER for _, lb, sz in files)
    if first_file_lba != D3_SNOVA_DIR_LBA + 1 or last - D3_SNOVA_DIR_LBA != D3_SNOVA_SECTORS:
        raise SystemExit("D3 SNOVA not contiguous as expected")
    print("D3 SNOVA raw block LBA %s+%s files=%s" % (D3_SNOVA_DIR_LBA, D3_SNOVA_SECTORS, len(files)))

    old_sec = len(img) // SECTOR
    new_dir = old_sec
    delta = new_dir - D3_SNOVA_DIR_LBA
    new_sec = old_sec + D3_SNOVA_SECTORS
    img.extend(b"\x00" * (D3_SNOVA_SECTORS * SECTOR))
    print("grow sectors %s -> %s (delta LBA %s)" % (old_sec, new_sec, delta))

    src = D3_SNOVA_DIR_LBA * SECTOR
    dst = new_dir * SECTOR
    img[dst : dst + D3_SNOVA_SECTORS * SECTOR] = d3[src : src + D3_SNOVA_SECTORS * SECTOR]
    for s in range(new_dir, new_sec):
        fix_sector_msf(img, s)

    pvd = bytearray(_user(img, 16))
    root = pvd[156:190]
    root_lba = _u32_le(bytes(root), 2)
    root_size = _u32_le(bytes(root), 10)
    if root_size != USER:
        raise SystemExit("unexpected root size %s" % root_size)

    dir_user = bytearray(img[new_dir * SECTOR + 24 : new_dir * SECTOR + 24 + USER])
    patch_dir_lbas(dir_user, delta, new_dir, root_lba)
    img[new_dir * SECTOR + 24 : new_dir * SECTOR + 24 + USER] = dir_user
    img[new_dir * SECTOR + 24 + USER : new_dir * SECTOR + SECTOR] = b"\x00" * (SECTOR - 24 - USER)

    root_blob = bytearray(_read_extent(img, root_lba, root_size))
    rec = dir_rec("SNOVA", new_dir, USER, True)
    i, ins = 0, None
    while i < len(root_blob):
        ln = root_blob[i]
        if ln == 0:
            ins = i
            break
        i += ln
    if ins is None or ins + len(rec) > len(root_blob):
        raise SystemExit("no root dir padding for SNOVA record")
    root_blob[ins : ins + len(rec)] = rec
    write_user_sector(img, root_lba, bytes(root_blob), hdr_from=root_lba)

    pt_size = _u32_le(bytes(pvd), 132)
    pt_l = _u32_le(bytes(pvd), 140)
    pt_l2 = _u32_le(bytes(pvd), 144)
    pt_m = struct.unpack(">I", bytes(pvd[148:152]))[0]
    ents = parse_path_L(_read_extent(img, pt_l, pt_size))
    new_e = path_L("SNOVA", new_dir, 1)
    idx = len(ents)
    for j, e in enumerate(ents):
        nm = ent_name_L(e)
        if nm in ("\x00", "\x01"):
            continue
        parent = struct.unpack_from("<H", e, 6)[0]
        if parent == 1 and nm > "SNOVA":
            idx = j
            break
    ents = ents[:idx] + [new_e] + ents[idx:]
    pt_new = b"".join(ents)
    if len(pt_new) > USER:
        raise SystemExit("L path table > 2048")
    pt_pad = pt_new + b"\x00" * (USER - len(pt_new))
    for lba in {pt_l, pt_l2}:
        if lba:
            write_user_sector(img, lba, pt_pad, hdr_from=pt_l)
    ments = []
    for e in ents:
        nm = ent_name_L(e)
        lba = struct.unpack_from("<I", e, 2)[0]
        parent = struct.unpack_from("<H", e, 6)[0]
        ments.append(path_M(nm, lba, parent))
    mt = b"".join(ments)
    if len(mt) > USER:
        raise SystemExit("M path table > 2048")
    if pt_m:
        write_user_sector(img, pt_m, mt + b"\x00" * (USER - len(mt)), hdr_from=pt_l)

    pvd[132:140] = both_u32(len(pt_new))
    pvd[80:88] = both_u32(new_sec)
    write_user_sector(img, 16, bytes(pvd), hdr_from=16)

    if not args.skip_battle_patch:
        print("patch BATTLE.X hardcoded SNOVA LBAs (delta %s)" % delta)
        patch_battle_x_lbas(img, delta)

    out = args.d1 if args.in_place or not args.o else args.o
    if not args.in_place and not args.o:
        raise SystemExit("pass --in-place or -o OUT.bin")
    out.write_bytes(img)
    print("wrote %s (raw-copy + BATTLE.X LBA patch v3)" % out)

    for n, _lb, sz in files:
        got = extract_file(bytes(img), "SNOVA/%s" % n)
        exp = extract_file(d3, "SNOVA/%s" % n)
        if got != exp or len(got) != sz:
            raise SystemExit("verify fail %s" % n)
    # verify battle patch
    if not args.skip_battle_patch:
        braw = extract_file(bytes(img), "BATTLE/BATTLE.X")
        bdec = gzip.decompress(braw[8:])
        for d3_lba, off in list(BATTLE_SNOVA_LBA_OFF) + [BATTLE_LASBOSS3_OFF]:
            got = struct.unpack_from("<I", bdec, off)[0]
            want = d3_lba + delta
            if got != want:
                raise SystemExit("battle verify fail 0x%X got %s want %s" % (off, got, want))
        print("verify: BATTLE.X 17 LBA entries remapped")
    print("verify: all SNOVA files match D3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
