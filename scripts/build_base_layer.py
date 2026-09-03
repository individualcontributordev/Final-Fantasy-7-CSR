#!/usr/bin/env python3
"""Build and locally publish one exclusive-base disc layer from an edited BIN.

  python3 scripts/build_base_layer.py cache/csr/FINALFANTASY7_D1.bin --version 0.14.0
  python3 scripts/build_base_layer.py cache/csr-plus/FINALFANTASY7_D1.bin --version 0.2.1

Writes builder/<slug>/layers/discN.layer.json, merges that disc into pack.json
+ VERSION + manifest.json, and verifies the layer against the patched image.

The matching pristine NTSC-U BIN is resolved from the disc number in the
filename. Outputs are JSON layers and catalog metadata only; BINs remain
untouched. The generated layer is applied back to pristine and must match the
edited image byte-for-byte unless ``--skip-verify`` is explicitly used. The
command does not repair MODE2 Form 1 footers, so edited images must be
repaired before this diff step.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

from libs.layer import apply_layer, build_layer
from libs.local_paths import pristine_bin

BASES = {
    # Product copy for a new pack.json. Existing packs keep their own name/blurb.
    "csr": {
        "slug": "csr",
        "name": "CSR",
        "blurb": "CutScenes Removed -- skill checks kept.",
    },
    "csr-plus": {
        "slug": "csr-plus",
        "name": "CSR+",
        "blurb": (
            "CutScenes Removed and collapsed onto one Disc 1 image. Supernova included, ending credits movies removed due to space constraints."
        ),
    },
    "highwind": {
        "slug": "highwind",
        "name": "Highwind",
        "blurb": (
            "Heavily shortened story, collapsed onto one Disc 1 image. Many dialogue choices and scenes are cut. The ending movie plays but is shortened due to space constraints."
        ),
    },
}

DISC_BIN_NAME = re.compile(
    r"^FINALFANTASY7_D([123])(?: \(patched\))?\.bin$",
    re.IGNORECASE,
)


def disc_from_bin_path(patched: Path) -> int:
    """Read disc number from a FINALFANTASY7_DN.bin filename."""
    match = DISC_BIN_NAME.match(patched.name)
    if not match:
        raise SystemExit(
            f"Cannot infer disc from {patched.name} -- "
            "expected FINALFANTASY7_D1.bin (or D2/D3, optional ' (patched)')."
        )
    return int(match.group(1))


def resolve_info(patched: Path) -> dict:
    """Map an edited BIN's parent directory to one exclusive base."""
    key = patched.parent.name
    if key in BASES:
        return dict(BASES[key])
    raise SystemExit(
        f"Unknown base folder '{patched.parent.name}'. "
        "Expected the image under cache/csr, cache/csr-plus, or cache/highwind."
    )


def sorted_disc_map(discs: dict) -> dict[str, str]:
    """Keep disc keys in 1, 2, 3 order for stable JSON."""
    return {k: discs[k] for k in sorted(discs, key=lambda d: int(d))}


def layer_digest(path: Path) -> str:
    """sha256 of a published layer file.

    The builder keys its layer cache on this and refuses a body that does not
    match, so republished bytes always invalidate even when the version string
    does not move. CRLF is fatal here: git publishes LF, so a digest taken
    from a CRLF working copy describes bytes nobody will ever download.
    """
    raw = path.read_bytes()
    if b"\r\n" in raw:
        raise SystemExit(
            f"{path} has CRLF line endings. Git publishes LF, so this digest "
            "would not match what the builder downloads. Check .gitattributes."
        )
    return hashlib.sha256(raw).hexdigest()


def upsert_pack_json(
    pack_dir: Path, info: dict, version: str, disc: int, digest: str
) -> dict:
    """Write or merge one disc; keep existing pack name/blurb when present."""
    pack_path = pack_dir / "pack.json"
    disc_rel = f"./layers/disc{disc}.layer.json"
    if pack_path.is_file():
        pack = json.loads(pack_path.read_text(encoding="utf-8"))
        discs = dict(pack.get("discs") or {})
        discs[str(disc)] = disc_rel
        pack["id"] = info["slug"]
        pack["kind"] = pack.get("kind") or "base"
        pack["exclusiveGroup"] = pack.get("exclusiveGroup") or "cutscenes"
        pack["version"] = version
        pack["format"] = pack.get("format") or "ic-layer-v1"
        pack["discs"] = sorted_disc_map(discs)
        if not pack.get("name"):
            pack["name"] = info["name"]
        if "blurb" not in pack:
            pack["blurb"] = info["blurb"]
    else:
        pack = {
            "id": info["slug"],
            "name": info["name"],
            "kind": "base",
            "exclusiveGroup": "cutscenes",
            "version": version,
            "blurb": info["blurb"],
            "format": "ic-layer-v1",
            "discs": {str(disc): disc_rel},
        }
    digests = dict(pack.get("discDigests") or {})
    digests[str(disc)] = digest
    pack["discDigests"] = sorted_disc_map(digests)
    pack_dir.mkdir(parents=True, exist_ok=True)
    pack_path.write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8", newline="\n")
    (pack_dir / "VERSION").write_text(version + "\n", encoding="utf-8", newline="\n")
    return pack


def update_manifest(pack: dict, disc: int, builder_dir: Path) -> None:
    """Merge one disc into the matching enabled base, preserving other entries."""
    manifest_path = builder_dir / "manifest.json"
    if manifest_path.is_file():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        data = {
            "version": 1,
            "source": "Final-Fantasy-7-CSR",
            "bases": [],
        }
    pack_id = pack["id"]
    disc_rel = f"./{pack_id}/layers/disc{disc}.layer.json"

    bases = data.setdefault("bases", [])
    existing_discs: dict[str, str] = {}
    existing_digests: dict[str, str] = {}
    existing_index = None
    existing = None
    for i, candidate in enumerate(bases):
        if str(candidate.get("id", "")) == pack_id:
            existing_discs = dict(candidate.get("discs") or {})
            existing_digests = dict(candidate.get("discDigests") or {})
            existing_index = i
            existing = candidate
            break
    existing_discs[str(disc)] = disc_rel
    existing_digests.update(pack.get("discDigests") or {})

    entry = {
        "id": pack_id,
        "name": pack.get("name") or (existing or {}).get("name") or pack_id,
        "kind": pack.get("kind") or "base",
        "version": pack["version"],
        "exclusiveGroup": pack.get("exclusiveGroup") or "cutscenes",
        "blurb": pack.get("blurb") if "blurb" in pack else (existing or {}).get("blurb", ""),
        "format": pack.get("format") or "ic-layer-v1",
        "discs": sorted_disc_map(existing_discs),
        "discDigests": sorted_disc_map(existing_digests),
        "enabled": True,
    }
    if existing_index is None:
        bases.append(entry)
    else:
        bases[existing_index] = entry

    manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def verify(pristine: Path, layer: dict, patched: Path) -> None:
    """Require an exact pristine + layer = patched round trip."""
    image = bytearray(pristine.read_bytes())
    apply_layer(image, layer)
    expect = patched.read_bytes()
    if bytes(image) != expect:
        lim = min(len(image), len(expect))
        for i in range(lim):
            if image[i] != expect[i]:
                raise SystemExit(f"VERIFY FAIL at offset {i} (0x{i:X})")
        raise SystemExit(
            f"VERIFY FAIL size {len(image)} vs {len(expect)}"
        )


def build_one_disc(
    *,
    info: dict,
    version: str,
    disc: int,
    patched: Path,
    builder_dir: Path,
    skip_verify: bool,
) -> Path:
    """Diff, write, and optionally round-trip one disc layer."""
    pristine = pristine_bin(disc)
    if not pristine.is_file():
        raise SystemExit(f"Missing pristine: {pristine}")
    if not patched.is_file():
        raise SystemExit(f"Missing patched: {patched}")

    pack_id = info["slug"]
    out_dir = builder_dir / pack_id / "layers"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"disc{disc}.layer.json"

    layer_id = f"{info['slug']}-disc{disc}"
    description = f"{info['name']} v{version} -- NTSC-U Disc {disc}"
    print(f"=== Disc {disc}: diff ===")
    print(f"  pristine: {pristine}")
    print(f"  patched:  {patched}")
    layer = build_layer(
        pristine,
        patched,
        layer_id=layer_id,
        description=description,
    )
    stats = layer["stats"]

    if not skip_verify:
        print(f"=== Disc {disc}: verify ===")
        verify(pristine, layer, patched)
        print("  OK -- layer apply matches patched image")

    out_path.write_text(json.dumps(layer, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        f"  wrote {out_path}  "
        f"records={stats['records']} changedBytes={stats['changedBytes']}"
    )
    return out_path


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build one exclusive-base disc layer for the browser builder."
    )
    ap.add_argument(
        "image",
        type=Path,
        help="Edited BIN, e.g. cache/csr/FINALFANTASY7_D1.bin",
    )
    ap.add_argument(
        "--version",
        required=True,
        help="Version string, e.g. 0.14.0 or 0.2.1",
    )
    ap.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip apply_layer --expect checks (not recommended)",
    )
    ap.add_argument(
        "--builder-dir",
        type=Path,
        default=ROOT / "builder",
        help=argparse.SUPPRESS,
    )
    args = ap.parse_args()

    version = args.version.strip()
    if not re.fullmatch(r"[0-9]+(\.[0-9]+)*", version):
        raise SystemExit(f"Weird version '{version}' -- expected like 0.14.0")

    patched = args.image.expanduser().resolve()
    disc = disc_from_bin_path(patched)
    info = resolve_info(patched)
    pack_id = info["slug"]
    builder_dir = args.builder_dir.expanduser().resolve()
    pack_dir = builder_dir / pack_id

    print(f"Base:    {info['name']} ({info['slug']})")
    print(f"Version: {version}")
    print(f"Image:   {patched}")
    print(f"Disc:    {disc}")
    print(f"Output:  {pack_dir}")

    out_path = build_one_disc(
        info=info,
        version=version,
        disc=disc,
        patched=patched,
        builder_dir=builder_dir,
        skip_verify=args.skip_verify,
    )

    pack = upsert_pack_json(pack_dir, info, version, disc, layer_digest(out_path))
    update_manifest(pack, disc, builder_dir)
    print(f"Updated {pack_dir / 'pack.json'}")
    print(f"Updated {builder_dir / 'manifest.json'} (enabled=true)")
    print("Commit JSON under builder/ only -- not .bin/.cue.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
