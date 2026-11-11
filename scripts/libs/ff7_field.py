"""Read FIELD/*.DAT from an FF7 PSX disc image and analyse its scripts.

Covers the ISO9660 walk over a MODE2/2352 image, the Okumura LZS stream, the
field section layout (scripts, texts, INF gateways), Makou Reactor's opcode
lengths, jump arithmetic, Init/Main split and label/line numbering, the
FF7 text encoding, and a small dataflow that prunes code which cannot run at a
given main-story moment (``Var[1|2][0]``, savemap 0xBA4, as a u16).

The moment model is per script: every script is assumed to start at the entry
moment, and only writes made by that same script change it. Scripts that move
the story from another entity or another field are not modelled, and any
non-literal write to the variable makes the moment unknown (all branches kept).
"""

from __future__ import annotations

import operator
import struct
from dataclasses import dataclass, field as dc_field

from .ff7_field_data import MAPLIST, OPCODE_LENGTH, OPCODE_NAMES

SECTOR, USER, USER_OFF = 2352, 2048, 24
OP = {n: i for i, n in enumerate(OPCODE_NAMES)}
FIELD_ID: dict[str, int] = {}
for _i, _n in enumerate(MAPLIST):
    FIELD_ID.setdefault(_n, _i)

# --- disc -------------------------------------------------------------------


def _u32(b, i: int) -> int:
    return struct.unpack_from("<I", b, i)[0]


def _extent(img, lba: int, size: int) -> bytes:
    out = bytearray()
    for s in range((size + USER - 1) // USER):
        off = (lba + s) * SECTOR + USER_OFF
        out += img[off : off + USER]
    return bytes(out[:size])


def _records(img, lba: int, size: int) -> dict[str, tuple[int, int, bool]]:
    """Directory extent -> {NAME: (lba, size, is_dir)}."""
    blob, out, i = _extent(img, lba, size), {}, 0
    while i < len(blob):
        n = blob[i]
        if n == 0:
            i = (i // USER + 1) * USER
            continue
        rec, i = blob[i : i + n], i + n
        name = rec[33 : 33 + rec[32]]
        if name not in (b"\0", b"\1"):
            key = name.split(b";")[0].decode("ascii", "replace").upper()
            out[key] = (_u32(rec, 2), _u32(rec, 10), bool(rec[25] & 2))
    return out


def iso_dir(img, path: str = "") -> dict[str, tuple[int, int, bool]]:
    """Entries of one ISO9660 directory, e.g. ``iso_dir(img, "FIELD")``."""
    pvd = 16 * SECTOR + USER_OFF
    if img[pvd + 1 : pvd + 6] != b"CD001":
        raise ValueError("no ISO9660 primary volume descriptor at LBA 16")
    entries = _records(img, _u32(img, pvd + 158), _u32(img, pvd + 166))
    for part in filter(None, path.upper().split("/")):
        entries = _records(img, *entries[part][:2])
    return entries


def lzs(data: bytes) -> bytes:
    """Okumura LZSS, 4096-byte ring, initial cursor 4078 (no size header)."""
    out, ring, cur, i, flags = bytearray(), bytearray(4096), 4078, 0, 0
    while i < len(data):
        flags >>= 1
        if not flags & 256:
            flags, i = data[i] | 0xFF00, i + 1
            if i >= len(data):
                break
        if flags & 1:
            b = data[i]
            i += 1
            ring[cur] = b
            out.append(b)
            cur = (cur + 1) & 4095
        else:
            if i + 1 >= len(data):
                break
            b1, b2 = data[i], data[i + 1]
            i += 2
            start = b1 | (b2 & 0xF0) << 4
            for p in range(start, (b2 & 15) + 2 + start + 1):
                b = ring[p & 4095]
                ring[cur] = b
                out.append(b)
                cur = (cur + 1) & 4095
    return bytes(out)


# --- text -------------------------------------------------------------------

_CHARS = (
    " !\"#$%&'()*+,-./01234"
    "56789:;<=>?@ABCDEFGHI"
    "JKLMNOPQRSTUVWXYZ[\\]^"
    "_`abcdefghijklmnopqrs"
    "tuvwxyz{|}~ ÄÅÇÉÑÖÜáà"
    "âäãåçéèêëíìîïñóòôöõúù"
    "ûü♥°¢£↔→♪ßα  ´¨≠ÆØ∞±≤"
    "≥¥µ∂ΣΠπ⌡ªºΩæø¿¡¬√ƒ≈∆«"
    "»… ÀÃÕŒœ–—“”‘’÷◊ÿŸ⁄ ‹"
    "›ﬁﬂ■‧‚„‰ÂÊÁËÈÍÎÏÌÓÔ Ò"
    "ÚÛÙıˆ˜¯˘˙˚¸˝˛ˇ       "
)
_SPECIAL = {
    0xE0: "{CHOICE}", 0xE1: "\t", 0xE2: ", ", 0xE3: '."', 0xE4: '…"', 0xE6: "⑬",
    0xE7: "\n", 0xE8: "{NEW}\n", 0xF3: "{PARTY #1}", 0xF4: "{PARTY #2}",
    0xF5: "{PARTY #3}", 0xF6: "〇", 0xF7: "△", 0xF8: "☐", 0xF9: "✕",
}
_SPECIAL.update(
    zip(range(0xEA, 0xF3), ("{CLOUD}", "{BARRET}", "{TIFA}", "{AERITH}", "{RED XIII}",
                            "{YUFFIE}", "{CAIT SITH}", "{VINCENT}", "{CID}"))
)
_EXT = {0xDA: "{FLASH}", 0xDB: "{RAINBOW}", 0xDC: "{PAUSE}", 0xDE: "{NUM}",
        0xDF: "{HEX}", 0xE0: "{SCROLL}", 0xE1: "{RNUM}", 0xE9: "{FIXED}"}
_EXT.update(zip(range(0xD2, 0xDA), ("{GRAY}", "{BLUE}", "{RED}", "{PURPLE}", "{GREEN}",
                                   "{CYAN}", "{YELLOW}", "{WHITE}")))


def decode_text(b: bytes) -> str:
    """FF7 field string (up to the 0xFF terminator) -> unicode; never raises."""
    out, i = [], 0
    while i < len(b) and b[i] != 0xFF:
        c, i = b[i], i + 1
        if c == 0xFE and i < len(b):
            k, i = b[i], i + 1
            if k == 0xDD:
                out.append("{WAIT %d}" % int.from_bytes(b[i : i + 2], "little"))
                i += 2
            elif k == 0xE2:
                out.append("{STR %04x %04x}" % struct.unpack_from("<HH", b.ljust(i + 4, b"\0"), i))
                i += 4
            else:
                out.append(_EXT.get(k, "{FE %02X}" % k))
        elif c < 0xE0:
            out.append(_CHARS[c])
        else:
            out.append(_SPECIAL.get(c, "{%02X}" % c))
    return "".join(out)


# --- bytecode ---------------------------------------------------------------

_SPECIAL_3, _SPECIAL_4 = {0xF5, 0xF6, 0xF7, 0xFB, 0xFC}, {0xF8, 0xFD}
# op -> (jump field offset, size, shift, is_back); target = pos + raw + shift,
# back jumps pos - raw (Makou Opcode::jumpShift). IF true falls through.
JUMPS = {
    0x10: (1, 1, 1, False), 0x11: (1, 2, 1, False), 0x12: (1, 1, 0, True),
    0x13: (1, 2, 0, True), 0x1B: (1, 2, 1, False),
    0x14: (5, 1, 5, False), 0x15: (5, 2, 5, False),
    0x16: (7, 1, 7, False), 0x17: (7, 2, 7, False),
    0x18: (7, 1, 7, False), 0x19: (7, 2, 7, False),
    0x30: (3, 1, 3, False), 0x31: (3, 1, 3, False), 0x32: (3, 1, 3, False),
    0xCB: (2, 1, 2, False), 0xCC: (2, 1, 2, False),
}
UNCONDITIONAL = {0x10, 0x11, 0x12, 0x13, 0x1B}
RETURNS = {0x00, 0x07}  # RET, RETTO
CMP = ("==", "!=", ">", "<", ">=", "<=", "&", "^", "|", "bit on", "bit off")
_CMP_OPS = (operator.eq, operator.ne, operator.gt, operator.lt, operator.ge, operator.le)


def op_size(code: bytes, pos: int) -> int:
    op = code[pos]
    nxt = code[pos + 1] if pos + 1 < len(code) else 0
    if op == 0x28:  # KAWAI
        return max(nxt, 1)
    if op == 0x0F:  # SPECIAL
        return 3 if nxt in _SPECIAL_3 else 4 if nxt in _SPECIAL_4 else 2
    if op == 0x1C:
        return OPCODE_LENGTH[op] + min(nxt, 128)
    return max(OPCODE_LENGTH[op], 1)


def decode(code: bytes) -> list[tuple[int, bytes]]:
    """(pos, raw) per opcode; a truncated final opcode is kept as-is."""
    out, pos = [], 0
    while pos < len(code):
        size = min(op_size(code, pos), len(code) - pos)
        out.append((pos, code[pos : pos + size]))
        pos += size
    return out


def jump_target(pos: int, raw: bytes) -> int | None:
    """Absolute target of a jump/IF opcode, else None."""
    f = JUMPS.get(raw[0])
    if f is None or len(raw) < f[0] + f[1]:
        return None
    off, size, shift, back = f
    j = int.from_bytes(raw[off : off + size], "little")
    return pos - j if back else pos + j + shift


def split_init_main(code: bytes) -> int:
    """Makou Script::splitScriptAtReturn: end of Init in physical slot 0."""
    pos, skip = 0, None
    while pos < len(code):
        size = op_size(code, pos)
        if skip is not None and pos != skip:
            pos += size
            continue
        skip = None
        op = code[pos]
        if op in JUMPS:
            f = JUMPS[op]
            if not f[3] and pos + f[0] + f[1] <= len(code):
                skip = jump_target(pos, code[pos : pos + size])
        elif op in RETURNS:
            return pos + size
        pos += size
    return len(code)


_SLOTS = ("Talk", "Contact", "Move", "Go", "Go 1x", "Go away")


def script_name(slot: int) -> str:
    return f"S{slot} - {_SLOTS[slot - 1]}" if 1 <= slot <= len(_SLOTS) else f"Script {slot}"


@dataclass
class Script:
    """One logical script: Init/Main halves of slot 0, or one slot >= 1."""

    entity: str
    group: int  # entity index, the REQ group id
    name: str
    code: bytes
    ops: dict[int, bytes] = dc_field(init=False)  # pos -> raw opcode
    label: dict[int, int] = dc_field(init=False)  # jump-target pos -> Makou label no.
    line: dict[int, int] = dc_field(init=False)  # op pos -> 1-based line (labels count)
    label_line: dict[int, int] = dc_field(init=False)  # target pos -> its label row

    def __post_init__(self) -> None:
        self.ops = dict(decode(self.code))
        ends = set(self.ops) | {len(self.code)}
        targets = {jump_target(p, r) for p, r in self.ops.items()} & ends
        self.label = {p: n for n, p in enumerate(sorted(targets), 1)}
        self.line, self.label_line, n = {}, {}, 0
        for pos in self.ops:
            if pos in self.label:
                n += 1
                self.label_line[pos] = n
            n += 1
            self.line[pos] = n
        if len(self.code) in self.label:
            self.label_line[len(self.code)] = n + 1


# --- moment dataflow --------------------------------------------------------


def if_parts(raw: bytes):
    """(width, signed, (bank, v), (bank, v), cmp) of IFUB/IFSW/IFUW (+L)."""
    if raw[0] in (0x14, 0x15):
        return 1, False, (raw[1] >> 4, raw[2]), (raw[1] & 15, raw[3]), raw[4]
    return (2, raw[0] in (0x16, 0x17), (raw[1] >> 4, raw[2] | raw[3] << 8),
            (raw[1] & 15, raw[4] | raw[5] << 8), raw[6])


def _cond(raw: bytes, m: int | None) -> bool | None:
    """Outcome of an IF at moment ``m``; None when it is not fixed by it."""
    if not 0x14 <= raw[0] <= 0x19:
        return None
    width, signed, a, b, c = if_parts(raw)
    vals = []
    for bank, v in (a, b):
        x = None
        if bank == 0:
            x = v
        elif bank in (1, 2) and m is not None:
            if width == 2 and v & 0xFF == 0:
                x = m
            elif width == 1 and v & 0xFF < 2:
                x = m >> 8 * (v & 0xFF) & 0xFF
        if signed and x is not None and x >= 0x8000:
            x -= 0x10000
        vals.append(x)
    if None in vals or c >= len(_CMP_OPS):
        return None
    return _CMP_OPS[c](*vals)


_BINARY = set(range(0x76, 0x7A)) | set(range(0x82, 0x95))
_UNARY = set(range(0x7A, 0x7E)) | set(range(0x95, 0x9A))


def _after(raw: bytes, m: int | None) -> int | None:
    """Moment after one opcode (unknown when a non-literal write may hit it)."""
    op = raw[0]
    if len(raw) < 3:
        return m
    hit = raw[2] < 2
    if op in (0x80, 0x81):  # SETBYTE / SETWORD
        if raw[1] >> 4 not in (1, 2) or not hit:
            return m
        if raw[1] & 15:
            return None
        v = raw[3] if op == 0x80 else int.from_bytes(raw[3:5], "little")
        if op == 0x81:
            return v if raw[2] == 0 else None
        if m is None:
            return None
        sh = 8 * raw[2]
        return m & ~(0xFF << sh) | v << sh
    if op in _BINARY:
        return None if hit and raw[1] >> 4 in (1, 2) else m
    if op in _UNARY:
        return None if hit and {raw[1] >> 4, raw[1] & 15} & {1, 2} else m
    if 0x9A <= op <= 0x9F:
        banks = {raw[1] >> 4, raw[1] & 15}
        if op == 0x9C:
            banks |= {raw[2] >> 4, raw[2] & 15}
        return None if banks & {1, 2} else m
    return m


def walk(sc: Script, m0: int | None) -> dict[int, set]:
    """Reachable positions of ``sc`` started at moment ``m0`` -> moments there."""
    seen: dict[int, set] = {}
    stack = [(0, m0)]
    while stack:
        pos, m = stack.pop()
        if pos not in sc.ops and pos != len(sc.code):
            continue
        if m in seen.setdefault(pos, set()):
            continue
        if len(seen[pos]) >= 8:  # shortcut: counter loops; collapse to unknown, raise if pruning is too coarse
            m = None
            if m in seen[pos]:
                continue
        seen[pos].add(m)
        if pos == len(sc.code):
            continue
        raw = sc.ops[pos]
        if raw[0] in RETURNS:
            continue
        tgt = jump_target(pos, raw)
        if raw[0] in UNCONDITIONAL:
            stack.append((tgt, m))
        elif tgt is not None:  # IF: true falls through, false jumps
            r = _cond(raw, m)
            if r is not False:
                stack.append((pos + len(raw), m))
            if r is not True:
                stack.append((tgt, m))
        else:
            stack.append((pos + len(raw), _after(raw, m)))
    return seen


# --- fields -----------------------------------------------------------------


@dataclass
class Field:
    stem: str
    fid: int  # -1 when the stem is not in MAPLIST
    entities: list[str]
    scripts: list[Script]
    texts: list[str]  # decoded, by text id
    exits: list[tuple[int, int]]  # (gateway index, destination field id)


def _texts(blob: bytes) -> list[str]:
    if len(blob) < 4 or (beg := struct.unpack_from("<H", blob, 2)[0]) < 4:
        return []
    offs = struct.unpack_from(f"<{beg // 2 - 1}H", blob, 2)
    return [decode_text(blob[o:]) if o < len(blob) else "" for o in offs]


def _slot_blobs(sec: bytes, nb: int, pos_after: int, tbl: int):
    """Yield (entity index, slot, blob) for every non-empty slot (Makou layout)."""
    empty = 0
    for i in range(nb):
        if empty > 1:
            empty -= 1
            continue
        pos = list(struct.unpack_from("<32H", sec, tbl + 64 * i))
        if i == nb - 1:
            pos.append(pos_after)
        else:
            nxt = struct.unpack_from("<H", sec, tbl + 64 * (i + 1))[0]
            if nxt > pos[31]:
                pos.append(nxt)
            else:
                empty = 1
                while nxt <= pos[31] and i + empty < nb - 1:
                    nxt = struct.unpack_from("<H", sec, tbl + 64 * (i + empty + 1))[0]
                    empty += 1
                pos.append(pos_after if i + empty == nb else nxt)
        for j in range(32):
            # aliased slots share a body: end at the next strictly greater offset
            end = next((p for p in pos[j + 1 :] if p > pos[j]), None)
            if end is not None:
                yield i, j, sec[pos[j] : end]


def parse_field(dat: bytes, stem: str) -> Field:
    """Parse one FIELD/*.DAT file (u32 size header + LZS)."""
    raw = lzs(dat[4 : 4 + _u32(dat, 0)])
    ptrs = struct.unpack_from("<7I", raw, 0)
    offs = [p - ptrs[0] + 28 for p in ptrs] + [len(raw)]
    sec, inf = raw[offs[0] : offs[1]], raw[offs[4] : offs[5]]
    if len(sec) < 0x24 or offs != sorted(offs):  # placeholder DAT with no real sections
        return Field(stem, FIELD_ID.get(stem, -1), [], [], [], [])
    nb, pos_texts, nb_akao = sec[2], *struct.unpack_from("<HH", sec, 4)
    names = [sec[0x20 + 8 * i : 0x28 + 8 * i].split(b"\0")[0].decode("latin1") for i in range(nb)]
    pos_akao = _u32(sec, 0x20 + 8 * nb) if nb_akao else len(sec)
    pos_after = min(pos_akao, pos_texts) if pos_texts else pos_akao
    scripts = []
    for i, j, blob in _slot_blobs(sec, nb, pos_after, 0x20 + 8 * nb + 4 * nb_akao):
        if j == 0:
            cut = split_init_main(blob)
            scripts.append(Script(names[i], i, "S0 - Init", blob[:cut]))
            scripts.append(Script(names[i], i, "S0 - Main", blob[cut:]))
        else:
            scripts.append(Script(names[i], i, script_name(j), blob))
    end = pos_akao if pos_akao >= pos_texts else len(sec)
    exits = []
    if len(inf) >= 344:
        for g in range(12):
            fid = struct.unpack_from("<H", inf, 56 + 24 * g + 18)[0]
            if fid != 0x7FFF:
                exits.append((g, fid))
    return Field(stem, FIELD_ID.get(stem, -1), names, scripts, _texts(sec[pos_texts:end]), exits)


class Disc:
    """The FIELD directory of one disc image; fields parse on first use."""

    def __init__(self, img) -> None:
        self.img = img
        self.files = {n[:-4].lower(): v for n, v in iso_dir(img, "FIELD").items() if n.endswith(".DAT")}
        self._cache: dict[str, Field] = {}

    def field(self, key: str | int) -> Field | None:
        """By stem or field id; None when this disc has no such field."""
        stem = MAPLIST[key] if isinstance(key, int) and 0 <= key < len(MAPLIST) else key
        if stem not in self.files:
            return None
        if stem not in self._cache:
            lba, size, _ = self.files[stem]
            self._cache[stem] = parse_field(_extent(self.img, lba, size), stem)
        return self._cache[stem]


def analyse(f: Field, moments: set) -> list[dict[int, set]]:
    """Per script of ``f``: reachable pos -> moments, over all entry ``moments``."""
    moments = {None} if None in moments else moments
    out = []
    for sc in f.scripts:
        seen: dict[int, set] = {}
        for m in moments:
            for pos, ms in walk(sc, m).items():
                seen.setdefault(pos, set()).update(ms)
        out.append(seen)
    return out


def map_dest(raw: bytes) -> int | None:
    """Destination field id of MAPJUMP / MINIGAME / PMJMP."""
    if raw[0] in (OP["MAPJUMP"], OP["MINIGAME"], OP["PMJMP"]) and len(raw) >= 3:
        return int.from_bytes(raw[1:3], "little")
    return None


def explore(disc: Disc, start: str | int, moment: int | None) -> dict[str, set]:
    """Fields reachable from ``start`` at ``moment`` via gateways and map jumps.

    Returns stem -> entry moments. World-map exits are not followed.
    """
    first = disc.field(start)
    if first is None:
        raise KeyError(f"field {start!r} is not on this disc")
    entry, todo = {first.stem: {moment}}, [first.stem]
    while todo:
        f = disc.field(todo.pop())
        reach = analyse(f, entry[f.stem])
        all_m = {m for r in reach for ms in r.values() for m in ms}
        nxt = {(d, m) for _, d in f.exits for m in all_m}
        for sc, r in zip(f.scripts, reach):
            for pos, ms in r.items():
                d = map_dest(sc.ops[pos]) if pos in sc.ops else None
                nxt |= {(d, m) for m in ms} if d is not None else set()
        for d, m in nxt:
            g = disc.field(d)
            if g is None:
                continue
            cur = entry.setdefault(g.stem, set())
            if len(cur) >= 4 and m is not None:  # shortcut: collapse to unknown to bound re-analysis
                cur.clear()
                m = None
            if None not in cur and m not in cur:
                cur.add(m)
                todo.append(g.stem)
    return entry


def selftest() -> None:
    assert decode_text(bytes([0x21, 0xE7, 0x22, 0xFE, 0xDD, 5, 0, 0xFF, 0x21])) == "A\nB{WAIT 5}"
    # IFUW Var[2][0] < 100 (false jumps over the MESSAGE to RET), MESSAGE, RET
    guard = bytes.fromhex("18 20 00 00 64 00 03 04  40 00 00  00")
    sc = Script("t", 0, "S1", guard)
    assert sc.label == {11: 1} and sc.label_line[11] == 3 and sc.line[11] == 4, (sc.label, sc.line)
    assert 8 in walk(sc, 50) and 8 not in walk(sc, 150) and 8 in walk(sc, None)
    # SETWORD Var[2][0] = 200 first: the guard fails whatever the entry moment
    sc = Script("t", 0, "S1", bytes.fromhex("81 20 00 c8 00") + guard)
    assert 13 not in walk(sc, 50) and 13 not in walk(sc, None) and 16 in walk(sc, 50)
