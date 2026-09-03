#!/usr/bin/env python3
"""Validate the local builder catalog before publishing it.

Default path is ``builder/manifest.json``. Every base and add-on must have a
unique id and a ``discs`` map whose paths exist next to the manifest; each
published ``discDigests`` entry must still hash the layer it names and agree
with the pack's own ``pack.json``; and no published JSON may contain CRLF,
because the digests describe the LF bytes git serves. ``autoIncludeWhen`` ids
must name another entry in this file (unless they start with DISABLED-).

Every problem carries a fix, and identical fixes are printed once no matter how
many entries hit them. Fixes name the cheap causes first -- a stale clone or a
CRLF checkout -- so that a misconfigured workstation does not read as a reason
to rebuild. Returns nonzero on any problem. Does not fetch the network or
rewrite files."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "builder" / "manifest.json"


class Problem(NamedTuple):
    """One validation failure and the way out of it."""

    message: str
    fix: str


FIX_CRLF = """\
CRLF in published JSON. This is a checkout problem, not a build problem: the
digests on main are correct, so nothing here needs rebuilding.

First get the commit that pins LF, and confirm the rule reaches these files.
Expect "eol: lf"; "unspecified" means the commit is still missing:
    git pull
    git check-attr eol -- builder/manifest.json

Files checked out before that commit keep their CRLF, because pulling it does
not rewrite them. Restore them from the committed bytes:
    git checkout HEAD -- builder

That discards uncommitted changes under builder/, so commit or stash any
layers you have just built first."""

FIX_STALE_DIGEST = """\
Stale digest. The builder refuses a layer whose bytes do not hash to the
checksum published beside it, so the entry goes offline with no other warning.

Rule out the cheap causes before rebuilding anything:
    git pull                                      published digests move too
    git status --short builder                    local edits to a layer?
    git check-attr eol -- builder/manifest.json   expect "eol: lf"

If the clone is current and clean, the layer really has drifted from its
checksum. Republish the pack to restamp pack.json and manifest.json:
    Final-Fantasy-7-CSR      python3 scripts/build_base_layer.py IMAGE
    Final-Fantasy-7-Modding  python3 scripts/rebuild_on_base.py BASE"""

FIX_DIGEST_AFTER_CRLF = """\
Stale digests, listed above alongside CRLF files. Almost certainly the same
fault: a CRLF working copy hashes differently from the bytes git serves.

Fix the line endings, then re-run this check. Do not republish anything yet:
these digests are most likely correct on main already."""

FIX_MISSING_LAYER = """\
Missing layer file. The manifest points at a layer that is not on disk, so
the entry cannot be built at all. Either republish the pack to regenerate the
layer, or delete the entry from manifest.json if it is retired."""

FIX_PACK_DISAGREES = """\
pack.json and manifest.json disagree. Both are published, so a half-finished
release leaves them describing different bytes. Pull first, in case you are
looking at one half of someone else's release:
    git pull
If they still disagree, republish the pack to rewrite the pair together."""

FIX_AUTOINCLUDE = """\
Dangling autoIncludeWhen. Auto-included entries are hidden from the UI, so a
typo silently drops the pack instead of erroring. Point addonSelected at an id
that exists in this manifest, or prefix it with DISABLED- to retire the rule."""

FIX_STRUCTURE = """\
Malformed entry. Every base and add-on needs a unique, non-empty string id and
an object 'discs' map. Edit manifest.json by hand."""

FIX_UNREADABLE = """\
Unreadable JSON, usually a partial write or a bad merge. Restore the committed
copy:
    git checkout -- builder"""


def crlf_offenders(builder_dir: Path) -> list[Path]:
    """Published JSON whose line endings would not survive a round trip.

    Digests are taken from the file on disk, but Pages serves the committed
    bytes, so a CRLF working copy publishes a hash nobody can match. Windows
    does this silently when ``core.autocrlf`` is on and no ``.gitattributes``
    rule overrides it.
    """
    return [p for p in sorted(builder_dir.rglob("*.json")) if b"\r\n" in p.read_bytes()]


def validate(manifest_path: Path) -> list[Problem]:
    """Return every problem found; an empty list means the catalog is valid."""
    problems: list[Problem] = []

    try:
        text = manifest_path.read_text(encoding="utf-8")
    except OSError as e:
        return [Problem(f"cannot read {manifest_path}: {e}", FIX_UNREADABLE)]

    try:
        manifest = json.loads(text)
    except json.JSONDecodeError as e:
        return [Problem(f"invalid JSON in {manifest_path}: {e}", FIX_UNREADABLE)]

    builder_dir = manifest_path.parent

    crlf_paths = crlf_offenders(builder_dir)
    for p in crlf_paths:
        problems.append(
            Problem(f"{p.relative_to(builder_dir)}: CRLF line endings", FIX_CRLF)
        )

    # A CRLF checkout makes every digest look stale, so pointing at the publish
    # scripts here would send the reader on a rebuild that cannot help.
    digest_fix = FIX_DIGEST_AFTER_CRLF if crlf_paths else FIX_STALE_DIGEST

    entries: list[tuple[str, dict]] = []
    for section in ("bases", "addons"):
        items = manifest.get(section) or []
        if not isinstance(items, list):
            problems.append(Problem(f"{section!r} is not a list", FIX_STRUCTURE))
            continue
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                problems.append(
                    Problem(f"{section}[{i}] is not an object", FIX_STRUCTURE)
                )
            elif not item.get("id"):
                problems.append(
                    Problem(f"{section}[{i}] missing 'id'", FIX_STRUCTURE)
                )
            else:
                entries.append((section, item))

    seen: set[str] = set()
    for section, entry in entries:
        eid = entry["id"]
        if eid in seen:
            problems.append(
                Problem(f"duplicate {section} id: {eid}", FIX_STRUCTURE)
            )
        seen.add(eid)

        discs = entry.get("discs") or {}
        if not isinstance(discs, dict):
            problems.append(Problem(f"{eid}: 'discs' is not an object", FIX_STRUCTURE))
            discs = {}
        digests = entry.get("discDigests") or {}

        for disc, rel in discs.items():
            if not rel:
                problems.append(
                    Problem(f"{eid}: discs[{disc!r}] is empty", FIX_STRUCTURE)
                )
                continue
            layer_path = (builder_dir / str(rel).lstrip("./")).resolve()
            if not layer_path.is_file():
                problems.append(
                    Problem(
                        f"{eid}: discs[{disc!r}] -> {rel!r} does not exist",
                        FIX_MISSING_LAYER,
                    )
                )
                continue
            want = digests.get(str(disc))
            if want:
                got = hashlib.sha256(layer_path.read_bytes()).hexdigest()
                if got != want:
                    problems.append(
                        Problem(
                            f"{eid}: disc {disc} digest is stale "
                            f"(manifest {want[:12]}..., file {got[:12]}...)",
                            digest_fix,
                        )
                    )

        pack_path = builder_dir / eid / "pack.json"
        if digests and pack_path.is_file():
            try:
                pack = json.loads(pack_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                problems.append(
                    Problem(f"{eid}: invalid pack.json: {e}", FIX_UNREADABLE)
                )
            else:
                for disc, want in (pack.get("discDigests") or {}).items():
                    if digests.get(disc) and digests[disc] != want:
                        problems.append(
                            Problem(
                                f"{eid}: pack.json disc {disc} digest disagrees "
                                f"with manifest",
                                FIX_PACK_DISAGREES,
                            )
                        )

    for section, entry in entries:
        aiw = entry.get("autoIncludeWhen") or {}
        if not isinstance(aiw, dict) or not entry.get("enabled", True):
            continue
        parent = aiw.get("addonSelected")
        if parent and not str(parent).startswith("DISABLED-") and parent not in seen:
            problems.append(
                Problem(
                    f"{entry['id']}: autoIncludeWhen.addonSelected={parent!r} "
                    f"matches no id in manifest",
                    FIX_AUTOINCLUDE,
                )
            )

    return problems


def report(manifest_path: Path, problems: list[Problem]) -> None:
    """Print each problem, then each distinct fix once."""
    noun = "problem" if len(problems) == 1 else "problems"
    print(f"INVALID: {manifest_path} ({len(problems)} {noun})", file=sys.stderr)
    for p in problems:
        print(f"  - {p.message}", file=sys.stderr)

    # One cause can produce dozens of problems (a bad checkout hits every
    # pack), so collapse the advice instead of repeating it per line.
    fixes = list(dict.fromkeys(p.fix for p in problems))
    label = "fix" if len(fixes) == 1 else "fixes"
    print(f"\n{len(fixes)} {label}:", file=sys.stderr)
    for n, fix in enumerate(fixes, 1):
        print("", file=sys.stderr)
        for i, line in enumerate(fix.splitlines()):
            bullet = f"  {n}. " if i == 0 else "     "
            print(f"{bullet}{line}" if line else "", file=sys.stderr)


def main(argv: list[str]) -> int:
    manifest_path = Path(argv[1]).resolve() if len(argv) > 1 else DEFAULT_MANIFEST
    problems = validate(manifest_path)
    if problems:
        report(manifest_path, problems)
        return 1
    print(f"OK: {manifest_path} is valid ({manifest_path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
