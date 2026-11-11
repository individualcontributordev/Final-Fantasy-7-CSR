"""Dump FF7 field dialogue, choices, gotos/labels and map jumps for review.

One flat row per opcode: ``field | entity | script | L<line> | detail``, so the
output greps and diffs cleanly. ``--moment N`` prunes code that cannot run once
the main-story variable (Var[1|2][0], savemap 0xBA4) equals N; ``--from FIELD``
also limits output to fields reachable from there via gateways and map jumps.
Reads the user's own disc image only; nothing is written to the repo.
"""

from __future__ import annotations

import argparse
import mmap
import sys
from pathlib import Path

from libs.ff7_field import (CMP, FIELD_ID, JUMPS, UNCONDITIONAL, Disc, analyse, explore,
                            if_parts, jump_target, map_dest)
from libs.ff7_field_data import MAPLIST, OPCODE_NAMES
from libs.local_paths import cache_bin_path

NOTABLE = {"MESSAGE", "ASK", "MPNAM", "MAPJUMP", "MINIGAME", "PMJMP", "BATTLE", "MENU",
           "MENU2", "PMVIE", "MOVIE", "STITM", "GOLDu", "GOLDd"}


def fname(i: int) -> str:
    return f"{MAPLIST[i]}({i})" if i < len(MAPLIST) else f"?({i})"


def operand(bank: int, v: int) -> str:
    return str(v) if bank == 0 else f"Var[{bank}][{v & 0xFF}]"


def detail(f, sc, pos: int, raw: bytes) -> str:
    op, name = raw[0], OPCODE_NAMES[raw[0]]

    def txt(i: int) -> str:
        return f.texts[i].replace("\n", "\\n") if i < len(f.texts) else f"<text {i} out of range>"

    if op in JUMPS:
        t = jump_target(pos, raw)
        dest = f"label {sc.label[t]} (L{sc.label_line[t]})" if t in sc.label else f"bad jump @{t}"
        if op in UNCONDITIONAL:
            return f"GOTO {dest}"
        if 0x14 <= op <= 0x19:
            _, _, a, b, c = if_parts(raw)
            cond = f"{operand(*a)} {CMP[c] if c < len(CMP) else c} {operand(*b)}"
        else:
            cond = raw[1:].hex()
        return f"{name} {cond} else GOTO {dest}"
    if name == "MESSAGE":
        return f'SAY #{raw[2]} "{txt(raw[2])}"'
    if name == "MPNAM":
        return f'MAPNAME "{txt(raw[1])}"'
    if name == "ASK":
        lines = f.texts[raw[3]].split("\n") if raw[3] < len(f.texts) else []
        opts = " | ".join(f"{k}) {s}" for k, s in enumerate(lines[raw[4] : raw[5] + 1], 1))
        return f'ASK #{raw[3]} "{" ".join(lines[: raw[4]])}" -> {opts}'
    if name == "MAPJUMP":
        return f"MAPJUMP -> {fname(map_dest(raw))} dir={raw[9]}"
    if name in ("MINIGAME", "PMJMP"):
        return f"{name} -> {fname(map_dest(raw))}"
    if name == "BATTLE":
        return f"BATTLE {int.from_bytes(raw[2:4], 'little')}"
    return f"{name} {raw[1:].hex()}"


def review(f, moments: set, everything: bool):
    """Rows for one field, pruned to code reachable from any entry moment."""
    for g, d in f.exits:
        yield f"{f.stem} | INF | gateway {g} | - | -> {fname(d)}"
    for sc, seen in zip(f.scripts, analyse(f, moments)):
        if len(sc.code) <= 1:  # lone RET
            continue
        for pos in sorted(seen):
            pre = f"{f.stem} | {sc.entity} | {sc.name} | L"
            if pos in sc.label:
                yield f"{pre}{sc.label_line[pos]} | label {sc.label[pos]}"
            raw = sc.ops.get(pos)
            if raw and (everything or OPCODE_NAMES[raw[0]] in NOTABLE or raw[0] in JUMPS):
                yield f"{pre}{sc.line[pos]} | {detail(f, sc, pos, raw)}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--image", type=Path, default=cache_bin_path("csr-plus", 1))
    ap.add_argument("--moment", type=int, help="story variable value to prune by (default: unknown)")
    ap.add_argument("--from", dest="start", help="only fields reachable from this field (name or id)")
    ap.add_argument("--field", action="append", help="only this field (name or id); repeatable")
    ap.add_argument("--all", action="store_true", help="every opcode, not just the notable ones")
    ap.add_argument("-o", "--out", type=Path, help="output file (default: stdout)")
    a = ap.parse_args()
    key = lambda s: int(s) if s.isdigit() else s  # noqa: E731

    out = a.out.open("w", encoding="utf-8", newline="\n") if a.out else sys.stdout
    if not a.out:
        sys.stdout.reconfigure(encoding="utf-8")
    with a.image.open("rb") as fh, mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ) as img:
        disc = Disc(img)
        if a.start:
            entry = explore(disc, key(a.start), a.moment)
        else:
            fields = [disc.field(key(s)) for s in a.field] if a.field else [disc.field(s) for s in disc.files]
            if None in fields:
                sys.exit(f"field not on this disc: {a.field}")
            entry = {f.stem: {a.moment} for f in fields}
        for stem in sorted(entry, key=lambda s: FIELD_ID.get(s, 9999)):
            f, ms = disc.field(stem), entry[stem]
            out.write(f"# {stem} ({f.fid}) entry moment: {'any' if None in ms else sorted(ms)}\n")
            for row in review(f, ms, a.all):
                out.write(row + "\n")
    if a.out:
        out.close()


if __name__ == "__main__":
    main()
