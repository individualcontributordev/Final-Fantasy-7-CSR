"""Parse PSX ``FIELD/*.DAT`` payloads for safe script-level merges.

Inputs may be LZS data with the four-byte compressed-size header or an already
decompressed field. The decompressed file begins with seven VRAM pointers to
scripts/text/AKAO, walkmesh, background, camera, INF, encounter, and model
sections. This module exposes physical entity script slots, text/AKAO bytes,
and gateway records without mutating data.

Opcode sizes and Init/Main splitting follow tracked Makou Reactor sources.
Unknown or truncated opcodes are kept visible rather than interpreted.
Per-field VRAM bases and aliased script offsets are preserved as invariants
for ``field_dat_write``; guessing either would produce a structurally valid
file with incorrect runtime pointers.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path

from ff7_opcodes import OPCODE_LENGTH, OPCODE_NAMES
from lzs import decompress_all_with_header

SECTION_NAMES = (
    "scripts",  # 0 scripts+texts+akao
    "walkmesh",
    "background",
    "camera",
    "inf",
    "encounter",
    "model_loader",
)

# SPECIAL subkey param extras (Makou Opcode::fixedSize)
_SPECIAL_PLUS1 = {0xF5, 0xF6, 0xF7, 0xFB, 0xFC}  # ARROW PNAME GMSPD BTLCK MVLCK
_SPECIAL_PLUS2 = {0xF8, 0xFD}  # SMSPD SPCNM


def op_size(data: bytes, pos: int) -> int:
    """Return the tracked encoded size of the opcode at ``pos``."""
    if pos >= len(data):
        return 1
    op = data[pos]
    if op == 0x28:  # KAWAI
        return max(data[pos + 1], 1) if pos + 1 < len(data) else 1
    if op == 0x0F:  # SPECIAL
        if pos + 1 >= len(data):
            return 2
        sub = data[pos + 1]
        if sub in _SPECIAL_PLUS1:
            return 3
        if sub in _SPECIAL_PLUS2:
            return 4
        return 2
    if op == 0x1C:
        base = OPCODE_LENGTH[op]
        return base + min(data[pos + 1], 128) if pos + 1 < len(data) else base
    if op < len(OPCODE_LENGTH):
        return max(OPCODE_LENGTH[op], 1)
    return 1


def decode_ops(blob: bytes) -> list[tuple[bytes, str]]:
    """Decode instruction boundaries while retaining unknown/truncated bytes."""
    ops: list[tuple[bytes, str]] = []
    pos = 0
    while pos < len(blob):
        op = blob[pos]
        sz = max(op_size(blob, pos), 1)
        trunc = pos + sz > len(blob)
        raw = blob[pos:] if trunc else blob[pos : pos + sz]
        name = OPCODE_NAMES[op] if op < len(OPCODE_NAMES) else f"OP{op:02X}"
        if trunc:
            name += "?TRUNC"
        ops.append((raw, name))
        if trunc:
            break
        pos += sz
    return ops


def fmt_op(raw: bytes, name: str) -> str:
    """Render one decoded opcode for diagnostics without interpreting operands."""
    if name.startswith("SPECIAL") and len(raw) > 1:
        return f"{name}.{raw[1]:02X} {raw.hex()}"
    return f"{name} {raw.hex()}"


# Forward-jump opcode families: op -> (jump_field_offset, jump_field_size,
# jumpShift, is_back). Offsets/sizes/shift verified against Makou Reactor's
# Opcode::jumpShift()/Opcode::jump() and the fixed-size opcode length table
# (Opcode.cpp). Only forward jumps matter for splitScriptAtReturn (back jumps
# are excluded via is_back).
_JUMP_FIELDS: dict[int, tuple[int, int, int, bool]] = {
    0x10: (1, 1, 1, False),  # JMPF
    0x11: (1, 2, 1, False),  # JMPFL
    0x12: (1, 1, 0, True),  # JMPB
    0x13: (1, 2, 0, True),  # JMPBL
    0x1B: (1, 2, 1, False),  # Unused1B (long forward jump)
    0x14: (5, 1, 5, False),  # IFUB
    0x15: (5, 2, 5, False),  # IFUBL
    0x16: (7, 1, 7, False),  # IFSW
    0x17: (7, 2, 7, False),  # IFSWL
    0x18: (7, 1, 7, False),  # IFUW
    0x19: (7, 2, 7, False),  # IFUWL
    0x30: (3, 1, 3, False),  # IFKEY
    0x31: (3, 1, 3, False),  # IFKEYON
    0x32: (3, 1, 3, False),  # IFKEYOFF
    0xCB: (2, 1, 2, False),  # IFPRTYQ
    0xCC: (2, 1, 2, False),  # IFMEMBQ
}
_RET_OPS = {0x00, 0x07}  # RET, RETTO


def split_script_at_return(blob: bytes) -> int:
    """Port of Makou Reactor's Script::splitScriptAtReturn.

    Walks opcodes in byte order, skipping over any region reached only via a
    forward jump (matching Makou's gotoLabel skip-state), until it reaches a
    top-level RET/RETTO. Returns the byte offset just after that RET/RETTO
    (the S0-Init/S0-Main boundary). If no top-level RET is found, returns
    len(blob) (the whole blob is Init, Main is empty) -- matching Makou's
    fallback when the loop runs off the end of the opcode list.
    """
    pos = 0
    skip_target: int | None = None
    n = len(blob)
    while pos < n:
        op = blob[pos]
        size = max(op_size(blob, pos), 1)
        if skip_target is not None:
            if pos == skip_target:
                skip_target = None
            else:
                pos += size
                continue
        if op in _JUMP_FIELDS:
            joff, jsz, shift, is_back = _JUMP_FIELDS[op]
            if not is_back and pos + joff + jsz <= n:
                raw = int.from_bytes(blob[pos + joff : pos + joff + jsz], "little")
                skip_target = pos + raw + shift
        elif op in _RET_OPS:
            return pos + size
        pos += size
    return n


def decompress_dat(raw: bytes) -> bytes:
    """LZS FIELD DAT, or already-decompressed if header looks like VRAM ptrs."""
    if len(raw) >= 28:
        p0 = struct.unpack_from("<I", raw, 0)[0]
        # decompressed PS header: ptr0 is VRAM-ish (>= 0x80000000-ish or large)
        if p0 > len(raw) and (p0 & 0xFFF00000) != 0:
            return raw
        # compressed: first u32 is compressed payload size
        if 4 < p0 + 4 <= len(raw) + 4 and p0 < len(raw):
            try:
                return decompress_all_with_header(raw)
            except ValueError:
                pass
    return decompress_all_with_header(raw)


def section_offsets(dat: bytes) -> list[int]:
    """Convert seven field VRAM pointers into decompressed-file offsets."""
    ptrs = list(struct.unpack_from("<7I", dat, 0))
    vdiff = ptrs[0] - 28
    return [p - vdiff for p in ptrs]


def slice_sections(dat: bytes) -> list[bytes]:
    """Slice all seven sections using the field's translated pointer header."""
    offs = section_offsets(dat)
    ends = offs[1:] + [len(dat)]
    return [dat[a:b] for a, b in zip(offs, ends)]


@dataclass
class ScriptSlot:
    """One physical entity/slot table entry and its shared script body."""
    entity: str
    slot: int
    raw: bytes
    start: int = 0  # byte offset within section1 (scripts section); 0 if unknown

    def ops(self) -> list[str]:
        return [fmt_op(r, n) for r, n in decode_ops(self.raw)]

    def makou_label(self) -> str:
        """Human label matching Makou Reactor's GrpScript::scriptName for
        this raw table slot -- NOT the Init/Main split (see
        makou_init_main())."""
        if self.slot == 0:
            return "S0 - Init/Main (raw, unsplit -- see makou_init_main())"
        return f"Script {self.slot - 1}"

    def makou_init_main(self) -> tuple[bytes, bytes]:
        """Only meaningful when self.slot == 0. Returns (init_bytes,
        main_bytes) by replicating Makou Reactor's
        Script::splitScriptAtReturn: physical slot 0 is ONE blob that Makou
        splits into logical 'S0 - Init' (bytes up to and including the
        first top-level RET/RETTO, skipping over any region only reached by
        a forward jump) and 'S0 - Main' (the remainder). This is a read-only
        display helper -- field_dat_write.py and every (entity, slot) key
        elsewhere in this codebase still use the raw physical slot number
        (slot 0 == the whole unsplit blob), so do NOT use this to renumber
        ScriptSlot.slot.
        """
        if self.slot != 0:
            raise ValueError("makou_init_main() only applies to physical slot 0")
        split = split_script_at_return(self.raw)
        return self.raw[:split], self.raw[split:]


@dataclass
class FieldDat:
    """Parsed field data plus layout metadata required for serialization."""
    path: str | None
    raw_size: int
    dec_size: int
    sections: list[bytes]
    entities: list[str]
    scripts: list[ScriptSlot]
    texts_raw: bytes
    text_entries: list[bytes]  # through 0xFF
    text_pad_total: int
    akao: bytes
    author: str
    version: int
    # Layout metadata (byte offsets within sections[0]) needed by field_dat_write.py
    # to splice script slots without reparsing everything from scratch.
    nb: int = 0
    sc: int = 0
    nb_akao: int = 0
    akao_tbl_off: int = 0
    pos_scripts: int = 0
    pos_texts_val: int = 0
    pos_akao_val: int = 0
    pos_after: int = 0
    vbase: int = 0x80000000

    @property
    def section_sizes(self) -> dict[str, int]:
        return {SECTION_NAMES[i]: len(self.sections[i]) for i in range(7)}


def _parse_section1(sec: bytes) -> tuple[
    int, str, list[str], list[ScriptSlot], bytes, list[bytes], int, bytes, dict
]:
    """Parse scripts, texts, AKAO, and serializer layout metadata.

    Physical slots may share an offset and therefore one script body. Each
    alias is emitted with the same ``start`` so serialization can preserve
    that ownership instead of duplicating bytes.
    """
    version = struct.unpack_from("<H", sec, 0)[0]
    nb = sec[2]
    pos_texts = struct.unpack_from("<H", sec, 4)[0]
    nb_akao = struct.unpack_from("<H", sec, 6)[0]
    demo = version == 0x0301
    cur = 8 if demo else 16
    author = sec[cur : cur + 8].split(b"\x00")[0].decode("latin1", "replace")
    cur += 16
    sc = 16 if demo else 32
    pos_scripts = cur + 8 * nb + 4 * nb_akao
    pos_akao = struct.unpack_from("<I", sec, cur + 8 * nb)[0] if nb_akao else len(sec)
    pos_after = min(pos_akao, pos_texts) if pos_texts else pos_akao

    entities: list[str] = []
    slots: list[ScriptSlot] = []
    empty = 0
    for i in range(nb):
        name = sec[cur + 8 * i : cur + 8 * i + 8].split(b"\x00")[0].decode(
            "latin1", "replace"
        )
        entities.append(name)
        if empty > 1:
            empty -= 1
            continue
        positions = list(
            struct.unpack_from(f"<{sc}H", sec, pos_scripts + sc * 2 * i)
        )
        if i == nb - 1:
            positions.append(pos_after)
        else:
            pos = struct.unpack_from("<H", sec, pos_scripts + sc * 2 * (i + 1))[0]
            if pos > positions[sc - 1]:
                positions.append(pos)
            else:
                empty = 1
                while pos <= positions[sc - 1] and i + empty < nb - 1:
                    pos = struct.unpack_from(
                        "<H", sec, pos_scripts + sc * 2 * (i + empty + 1)
                    )[0]
                    empty += 1
                positions.append(pos_after if i + empty == nb else pos)
        for j in range(sc):
            start = positions[j]
            # Multiple slot indices can alias the SAME script body: the
            # engine's offset table stores identical start offsets for a
            # run of slot numbers, with the blob only ending at the next
            # DISTINCT (larger) offset -- e.g. LOSLAKE1 `cl` slots 9-30 all
            # read 2315 while slot 31 (CANONON.MOV) is also 2315, meaning
            # REQ'ing slot 9 runs the exact same bytes as slot 31. Checking
            # only positions[j+1] > positions[j] misses every aliased slot
            # in the run except the last one before the real gap. Search
            # forward for the next strictly-greater offset instead.
            end = None
            for k in range(j + 1, len(positions)):
                if positions[k] > start:
                    end = positions[k]
                    break
            if end is not None:
                blob = sec[start:end]
                slots.append(ScriptSlot(name, j, blob, start=start))

    texts_blob = (
        sec[pos_texts:pos_akao] if pos_akao >= pos_texts else sec[pos_texts:]
    )
    entries, pad = _parse_texts(texts_blob)
    akao = sec[pos_akao:] if pos_akao < len(sec) else b""
    meta = dict(
        nb=nb,
        sc=sc,
        nb_akao=nb_akao,
        akao_tbl_off=cur + 8 * nb,
        pos_scripts=pos_scripts,
        pos_texts_val=pos_texts,
        pos_akao_val=pos_akao,
        pos_after=pos_after,
    )
    return version, author, entities, slots, texts_blob, entries, pad, akao, meta


def _parse_texts(blob: bytes) -> tuple[list[bytes], int]:
    """Split the text offset table into terminated entries and trailing pad."""
    if len(blob) < 4:
        return [], 0
    pos_beg = struct.unpack_from("<H", blob, 2)[0]
    if pos_beg < 4:
        return [], 0
    count = pos_beg // 2 - 1
    offs = [struct.unpack_from("<H", blob, 2 + i * 2)[0] for i in range(count)]
    entries: list[bytes] = []
    pad = 0
    for i, o in enumerate(offs):
        end = offs[i + 1] if i + 1 < count else len(blob)
        if o >= len(blob):
            entries.append(b"")
            continue
        span = blob[o:end]
        if 0xFF in span:
            cut = span.index(0xFF) + 1
            entries.append(span[:cut])
            pad += len(span) - cut
        else:
            entries.append(span)
    return entries, pad


def load_field_dat(data: bytes, path: str | None = None) -> FieldDat:
    """Decompress and parse one FIELD.DAT payload."""
    raw_size = len(data)
    dat = decompress_dat(data)
    sections = slice_sections(dat)
    ver, author, ents, slots, texts, entries, pad, akao, meta = _parse_section1(
        sections[0]
    )
    # Real VRAM base this field's engine code expects section 0 to be
    # loaded at (varies per file, e.g. 0x80115000) -- NOT a fixed constant.
    # write_field_dat() must reuse this exact base when recomputing the
    # section-pointer header, or every pointer in the file becomes wrong
    # (silently loads, corrupts field logic/pointers at runtime).
    vbase = struct.unpack_from("<I", dat, 0)[0] - 28
    return FieldDat(
        path=path,
        raw_size=raw_size,
        dec_size=len(dat),
        sections=sections,
        entities=ents,
        scripts=slots,
        texts_raw=texts,
        text_entries=entries,
        text_pad_total=pad,
        akao=akao,
        author=author,
        version=ver,
        vbase=vbase,
        **meta,
    )


def load_field_dat_path(path: Path) -> FieldDat:
    """Read and parse one FIELD.DAT while retaining its diagnostic path."""
    return load_field_dat(path.read_bytes(), str(path))


# ---------------------------------------------------------------------------
# Section 4 (INF): gateway/trigger-line records.
#
# Ground truth: makoureactor/src/core/field/InfFile.h (struct InfData /
# Exit / Trigger) and InfFile.cpp::open() (size check: 740 bytes with
# occidental arrow fields, 536 bytes without). Layout verified byte-by-byte
# below; do not hand-adjust offsets without re-checking against InfFile.h.
#
#   offset 0   name[9] + control[1]                         = 10
#   offset 10  cameraFocusHeight (i16)                       = 2   -> 12
#   offset 12  camera_range (4x i16)                         = 8   -> 20
#   offset 20  bg_layer1..4_flag (4x u8)                     = 4   -> 24
#   offset 24  bg_layer3/4 width/height (4x i16)             = 8   -> 32
#   offset 32  bg_layer3/4 x/y_related (4x i16)              = 8   -> 40
#   offset 40  bg_layer3/4 x/y_multiplier_related (4x i16)   = 8   -> 48
#   offset 48  unused[8]                                     = 8   -> 56
#   offset 56  doors[12]  (Exit, 24 bytes each)               = 288 -> 344
#   offset 344 triggers[12] (Trigger, 16 bytes each)          = 192 -> 536
#   offset 536 display_arrow[12] (occidental only)            = 12  -> 548
#   offset 548 arrows[12] (Arrow, 16 bytes each, occidental)  = 192 -> 740
_INF_DOORS_OFF = 56
_INF_EXIT_SIZE = 24  # exit_line[2] Vertex_s(6B) + destination Vertex_s(6B) + fieldID(u16) + 4x u8
_INF_NUM_DOORS = 12
_INF_TRIGGERS_OFF = _INF_DOORS_OFF + _INF_EXIT_SIZE * _INF_NUM_DOORS  # 344
_INF_TRIGGER_SIZE = 16
_INF_NUM_TRIGGERS = 12


@dataclass
class Exit:
    """A walk-through-a-doorway field transition ("gateway"). Triggered when
    the player crosses exit_line while walking; jumps to fieldID at
    destination (Makou Reactor calls this section 'Gateways')."""

    index: int
    field_id: int
    dest_x: int
    dest_y: int
    dest_z: int
    dir: int


def parse_inf_doors(inf_section: bytes) -> list[Exit]:
    """Parse section 4 (INF) door/gateway records. Returns [] if the section
    is missing/too short (some minimal fields, e.g. black-background utility
    maps, may not carry a full 536/740-byte INF block)."""
    doors: list[Exit] = []
    if len(inf_section) < _INF_TRIGGERS_OFF:
        return doors
    for i in range(_INF_NUM_DOORS):
        off = _INF_DOORS_OFF + i * _INF_EXIT_SIZE
        if off + _INF_EXIT_SIZE > len(inf_section):
            break
        # exit_line[2] (12 bytes) skipped -- only destination matters here.
        dest_x, dest_y, dest_z, field_id, dir_ = struct.unpack_from(
            "<hhhHB", inf_section, off + 12
        )
        doors.append(Exit(i, field_id, dest_x, dest_y, dest_z, dir_))
    return doors
