"""Serialize guarded script/text edits back into an FF7 FIELD.DAT.

Given a FieldDat (from field_dat.load_field_dat) and a set of (entity, slot)
-> new raw bytes overrides, rebuild the compressed FIELD/*.DAT bytes with
only those script slots replaced. Handles:

  - Growing/shrinking individual script blobs (offset table + text/akao
    start addresses shift accordingly).
  - Re-deriving the 7-section VRAM pointer header when section 0's total
    size changes.
  - Recompressing with the game's LZS + u32le-size header.

Does NOT touch walkmesh/background/camera/inf/encounter/model_loader
(sections 1-6) or the text/akao byte content itself -- only script bytes
and the offset tables/headers that locate them.

Output is a new LZS-wrapped byte string; this module does not write an ISO.
Aliased slots sharing one body must receive identical edits, offset and AKAO
tables are shifted with any size delta, and the original per-field VRAM base
is reused when rebuilding all seven section pointers. Empty replacement slots
and unsupported text/AKAO ordering fail closed. Callers must enforce the
destination ISO sector budget and repair sector EDC/ECC after injection.

Usage:
    from field_dat import load_field_dat
    from field_dat_write import write_field_dat

    fd = load_field_dat(raw_bytes)
    new_bytes = write_field_dat(fd, {("init", 0): new_script_bytes})
"""
from __future__ import annotations

import struct

from field_dat import FieldDat, ScriptSlot, decompress_dat, slice_sections, load_field_dat
from lzs import compress_all_with_header


def write_field_dat(
    fd: FieldDat,
    edits: dict[tuple[str, int], bytes],
    new_texts_raw: bytes | None = None,
) -> bytes:
    """Return new compressed FIELD/*.DAT bytes with the given script slots replaced.

    `edits` keys are (entity, slot) matching FieldDat.scripts entries; values
    are the new raw opcode bytes for that slot (any length, including 0 is
    not supported -- a slot must remain non-empty).

    `new_texts_raw`, if given, replaces the entire text-table blob (offset
    table + entries, same format as FieldDat.texts_raw) with a new one that
    may be a different length. Only supported when texts precede akao in
    section 0 (the common layout); akao content itself is never modified,
    only shifted to follow the new text blob.
    """
    if not edits:
        # No-op: re-serialize unchanged (useful for round-trip testing).
        edits = {}

    sec1 = fd.sections[0]
    nb, sc = fd.nb, fd.sc
    pos_scripts = fd.pos_scripts
    old_pos_texts = fd.pos_texts_val
    old_pos_akao = fd.pos_akao_val
    old_pos_after = fd.pos_after
    akao_tbl_off = fd.akao_tbl_off
    nb_akao = fd.nb_akao

    # Map (entity, slot) -> ScriptSlot, and find missing keys early.
    by_key: dict[tuple[str, int], ScriptSlot] = {(s.entity, s.slot): s for s in fd.scripts}
    for key in edits:
        if key not in by_key:
            raise KeyError(f"no such script slot in this FieldDat: {key!r}")

    # Sort all real (non-empty) script slots by their absolute start offset.
    # NOTE: multiple (entity, slot) indices can ALIAS the same underlying
    # blob -- the engine's offset table stores an identical start offset for
    # a run of slot numbers (e.g. LOSLAKE1 `cl` slots 9-30 all alias `cl`
    # slot 31's CANONON.MOV body). field_dat.py now emits a ScriptSlot for
    # every aliased index, so grouping by `start` here is required: writing
    # each alias's bytes independently would duplicate the shared blob once
    # per alias and corrupt the offset table.
    ordered_all = sorted(fd.scripts, key=lambda s: s.start)
    if not ordered_all:
        raise ValueError("FieldDat has no script slots to splice")

    groups: list[list] = []
    for slot in ordered_all:
        if groups and groups[-1][0].start == slot.start:
            groups[-1].append(slot)
        else:
            groups.append([slot])

    blob_region_start = groups[0][0].start

    # Boundaries: old_start of group i, old_end of group i (= old_start of
    # group i+1, or pos_after for the last one).
    old_boundaries: list[int] = [g[0].start for g in groups] + [old_pos_after]

    # Build the new contiguous blob region, applying edits, and record the
    # remapping from every old boundary value -> new boundary value. Each
    # aliased group is written exactly once; if edits touch more than one
    # alias of the same group with conflicting bytes, that's ambiguous
    # (they physically share storage) and we reject it.
    new_blob = bytearray()
    new_boundaries: list[int] = [blob_region_start]
    for group in groups:
        # NOTE: (entity, slot) is not always unique -- some fields (e.g.
        # NIVGATE) have two entities sharing the same name at different
        # entity-table indices. `by_key` above resolves each (entity, slot)
        # key to exactly one ScriptSlot object (last-duplicate-wins, same
        # resolution order dict-based callers like merge_rework_fields.py's
        # merge_slots() use to look up edit source bytes). Only apply an
        # edit to the slot object `by_key` actually resolved that key to --
        # matching purely by name tuple would also match an unrelated
        # same-named entity's aliased slots and falsely flag them as
        # "edited", producing spurious conflicts.
        edited = {
            edits[(s.entity, s.slot)]
            for s in group
            if (s.entity, s.slot) in edits and by_key.get((s.entity, s.slot)) is s
        }
        if len(edited) > 1:
            raise ValueError(
                f"conflicting edits for aliased script slots sharing offset "
                f"{group[0].start}: {[(s.entity, s.slot) for s in group]}"
            )
        data = next(iter(edited)) if edited else group[0].raw
        new_blob.extend(data)
        new_boundaries.append(blob_region_start + len(new_blob))

    # boundary_map: old absolute offset -> new absolute offset, for every
    # distinct boundary value (covers real slot starts + shared "empty slot"
    # duplicates + the trailing pos_after sentinel).
    boundary_map: dict[int, int] = {}
    for old_b, new_b in zip(old_boundaries, new_boundaries):
        boundary_map[old_b] = new_b

    new_pos_after = new_boundaries[-1]
    delta = new_pos_after - old_pos_after

    # --- Rebuild section 1 header + tables on a mutable copy ---
    sec1_new = bytearray(sec1)

    # 1) Script offset table: nb * sc u16 entries at pos_scripts.
    for i in range(nb):
        for j in range(sc):
            off = pos_scripts + 2 * (sc * i + j)
            (val,) = struct.unpack_from("<H", sec1_new, off)
            if val in boundary_map:
                struct.pack_into("<H", sec1_new, off, boundary_map[val])
            elif val >= old_pos_after:
                # Value points past the scripts region entirely (rare, but
                # keep consistent) -- shift by the same global delta.
                struct.pack_into("<H", sec1_new, off, val + delta)
            # else: unexpected value inside scripts region not on a boundary
            # -- leave as-is (shouldn't happen for well-formed files).

    # 2) AKAO pointer table (nb_akao u32 entries) just before pos_scripts.
    for i in range(nb_akao):
        off = akao_tbl_off + 4 * i
        (val,) = struct.unpack_from("<I", sec1_new, off)
        struct.pack_into("<I", sec1_new, off, val + delta)

    # 3) Header pos_texts field (u16 @ offset 4).
    new_pos_texts = old_pos_texts + delta if old_pos_texts else old_pos_texts
    struct.pack_into("<H", sec1_new, 4, new_pos_texts)

    # 4) Splice in the new blob region, keeping header/tables (already
    # patched) before it and text/akao raw bytes (unchanged content) after.
    sec1_final = bytes(sec1_new[:blob_region_start]) + bytes(new_blob) + bytes(sec1_new[old_pos_after:])

    # 5) Optionally replace the whole text-table blob (offset table +
    # entries) with a new one of possibly different length. This shifts
    # everything from pos_texts onward (i.e. akao, if present) by the size
    # delta, and the akao pointer table (already shifted above for the
    # script-splice delta) needs an additional shift for this delta too.
    if new_texts_raw is not None:
        if not old_pos_texts:
            raise ValueError("FieldDat has no text section to replace")
        texts_start = old_pos_texts + delta
        texts_end = old_pos_akao + delta if old_pos_akao >= old_pos_texts else len(sec1_final)
        old_texts_len = texts_end - texts_start
        text_delta = len(new_texts_raw) - old_texts_len
        sec1_final = (
            sec1_final[:texts_start] + new_texts_raw + sec1_final[texts_end:]
        )
        if text_delta:
            sec1_final = bytearray(sec1_final)
            for i in range(nb_akao):
                off = akao_tbl_off + 4 * i
                (val,) = struct.unpack_from("<I", sec1_final, off)
                if val >= texts_end:
                    struct.pack_into("<I", sec1_final, off, val + text_delta)
            sec1_final = bytes(sec1_final)

    # --- Reassemble the full decompressed DAT with recomputed section header ---
    new_sections = [sec1_final] + list(fd.sections[1:])
    # Section pointers are relative to each field's VRAM load base.
    vbase = fd.vbase
    offs = []
    cur_pos = 28
    for s in new_sections:
        offs.append(vbase + cur_pos)
        cur_pos += len(s)
    header = struct.pack("<7I", *offs)
    new_dat = header + b"".join(new_sections)

    return compress_all_with_header(new_dat)


def round_trip_check(raw: bytes) -> bool:
    """Sanity check: load, re-serialize with no edits, and re-parse to
    confirm the resulting FieldDat has byte-identical script slots, entity
    list, and text/akao content as the original. Does NOT require the
    recompressed bytes to be byte-identical to the input (LZS encoding is
    not unique), only semantically identical.
    """
    fd = load_field_dat(raw)
    new_raw = write_field_dat(fd, {})
    fd2 = load_field_dat(new_raw)

    if fd.entities != fd2.entities:
        return False
    if fd.texts_raw != fd2.texts_raw:
        return False
    if fd.akao != fd2.akao:
        return False
    slots1 = {(s.entity, s.slot): s.raw for s in fd.scripts}
    slots2 = {(s.entity, s.slot): s.raw for s in fd2.scripts}
    return slots1 == slots2
