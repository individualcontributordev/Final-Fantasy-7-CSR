#!/usr/bin/env python3
"""Build and locally publish one CSR-style disc layer from an edited BIN.

  python3 scripts/build_csr_base_layer.py cache/csr/FINALFANTASY7_D1.bin --version 0.14.0
  python3 scripts/build_csr_base_layer.py /path/to/FINALFANTASY7_D1.bin --slug csr --version 0.14.0

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
import json
import re
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_ROOT = _SCRIPTS.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from apply_layer import apply_layer  # noqa: E402
from bin_diff_to_layer import build_layer  # noqa: E402
from local_paths import pristine_bin  # noqa: E402

BASES = {
    "csr": {
        "slug": "csr",
        "name": "CSR",
        "blurb": "CutScenes Removed — skill checks kept.",
        "cache_key": "csr",
    },
    "csr-plus": {
        "slug": "csr-plus",
        "name": "CSR+",
        "blurb": "More aggressive cutscene removal.",
        "cache_key": "csr-plus",
    },
    "highwind": {
        "slug": "highwind",
        "name": "Highwind",
        "blurb": "Aggressively trimmed playthrough. Story mechanics, choices, and dialogue cut.",
        "cache_key": "highwind",
    },
}

MANIFEST_PATH = _ROOT / "builder" / "manifest.json"
DISC_BIN_NAME = re.compile(
    r"^FINALFANTASY7_D([123])(?: \(patched\))?\.bin$",
    re.IGNORECASE,
)


def disc_from_bin_path(patched: Path) -> int:
    """Read disc number from a FINALFANTASY7_DN.bin filename."""
    match = DISC_BIN_NAME.match(patched.name)
    if not match:
        raise SystemExit(
            f"Cannot infer disc from {patched.name} — "
            "expected FINALFANTASY7_D1.bin (or D2/D3, optional ' (patched)')."
        )
    return int(match.group(1))


def resolve_info(patched: Path, slug: str | None) -> dict:
    """Map an edited BIN to a known base, or require --slug for other folders."""
    key = (slug or patched.parent.name).strip()
    if key in BASES:
        return BASES[key]
    if slug:
        return {
            "slug": slug,
            "name": slug,
            "blurb": "",
            "cache_key": slug,
        }
    raise SystemExit(
        f"Unknown base folder '{patched.parent.name}'. "
        "Pass --slug (csr | csr-plus | highwind | custom-id)."
    )


def sorted_disc_map(discs: dict) -> dict[str, str]:
    """Keep disc keys in 1, 2, 3 order for stable JSON."""
    return {k: discs[k] for k in sorted(discs, key=lambda d: int(d))}


def upsert_pack_json(pack_dir: Path, info: dict, version: str, disc: int) -> None:
    """Write or merge one disc into pack-local metadata and VERSION."""
    pack_path = pack_dir / "pack.json"
    disc_rel = f"./layers/disc{disc}.layer.json"
    if pack_path.is_file():
        pack = json.loads(pack_path.read_text(encoding="utf-8"))
        discs = dict(pack.get("discs") or {})
        discs[str(disc)] = disc_rel
        pack["id"] = info["slug"]
        pack["name"] = info["name"]
        pack["kind"] = "base"
        pack["exclusiveGroup"] = "cutscenes"
        pack["version"] = version
        pack["blurb"] = info["blurb"]
        pack["format"] = "ic-layer-v1"
        pack["discs"] = sorted_disc_map(discs)
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
    pack_dir.mkdir(parents=True, exist_ok=True)
    pack_path.write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")
    (pack_dir / "VERSION").write_text(version + "\n", encoding="utf-8")


def update_manifest(info: dict, version: str, disc: int) -> None:
    """Merge one disc into the matching enabled base, preserving other entries."""
    if not MANIFEST_PATH.is_file():
        raise SystemExit(f"Missing {MANIFEST_PATH}")
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    pack_id = info["slug"]
    disc_rel = f"./{pack_id}/layers/disc{disc}.layer.json"

    bases = data.setdefault("bases", [])
    existing_discs: dict[str, str] = {}
    existing_index = None
    for i, existing in enumerate(bases):
        if str(existing.get("id", "")) == pack_id:
            existing_discs = dict(existing.get("discs") or {})
            existing_index = i
            break
    existing_discs[str(disc)] = disc_rel

    entry = {
        "id": pack_id,
        "name": info["name"],
        "kind": "base",
        "version": version,
        "exclusiveGroup": "cutscenes",
        "blurb": info["blurb"],
        "format": "ic-layer-v1",
        "discs": sorted_disc_map(existing_discs),
        "enabled": True,
    }
    if existing_index is None:
        bases.append(entry)
    else:
        bases[existing_index] = entry

    MANIFEST_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def verify(pristine: Path, layer_path: Path, patched: Path) -> None:
    """Require an exact pristine + layer = patched round trip."""
    image = bytearray(pristine.read_bytes())
    layer = json.loads(layer_path.read_text(encoding="utf-8"))
    apply_layer(image, layer)
    expect = patched.read_bytes()
    if bytes(image) != expect:
        lim = min(len(image), len(expect))
        for i in range(lim):
            if image[i] != expect[i]:
                raise SystemExit(f"VERIFY FAIL at offset {i} (0x{i:X}) for {layer_path.name}")
        raise SystemExit(
            f"VERIFY FAIL size {len(image)} vs {len(expect)} for {layer_path.name}"
        )


def build_one_disc(
    *,
    info: dict,
    version: str,
    disc: int,
    patched: Path,
    skip_verify: bool,
) -> Path:
    """Diff, write, and optionally round-trip one disc layer."""
    pristine = pristine_bin(disc)
    if not pristine.is_file():
        raise SystemExit(f"Missing pristine: {pristine}")
    if not patched.is_file():
        raise SystemExit(f"Missing patched: {patched}")

    pack_id = info["slug"]
    out_dir = _ROOT / "builder" / pack_id / "layers"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"disc{disc}.layer.json"

    layer_id = f"{info['slug']}-disc{disc}"
    description = f"{info['name']} v{version} — NTSC-U Disc {disc}"
    print(f"=== Disc {disc}: diff ===")
    print(f"  pristine: {pristine}")
    print(f"  patched:  {patched}")
    layer = build_layer(
        pristine,
        patched,
        layer_id=layer_id,
        description=description,
    )
    out_path.write_text(json.dumps(layer, indent=2) + "\n", encoding="utf-8")
    stats = layer["stats"]
    print(
        f"  wrote {out_path.relative_to(_ROOT)}  "
        f"records={stats['records']} changedBytes={stats['changedBytes']}"
    )

    if not skip_verify:
        print(f"=== Disc {disc}: verify ===")
        verify(pristine, out_path, patched)
        print("  OK — layer apply matches patched image")

    return out_path


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build one CSR or Highwind disc layer for the browser builder."
    )
    ap.add_argument(
        "image",
        type=Path,
        help="Edited BIN, e.g. cache/csr/FINALFANTASY7_D1.bin",
    )
    ap.add_argument(
        "--version",
        required=True,
        help="Version string, e.g. 0.14.0 or 0.1.0",
    )
    ap.add_argument(
        "--slug",
        default=None,
        help="Builder pack id when the BIN's parent folder is not csr / csr-plus / highwind",
    )
    ap.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip apply_layer --expect checks (not recommended)",
    )
    args = ap.parse_args()

    version = args.version.strip()
    if not re.fullmatch(r"[0-9]+(\.[0-9]+)*", version):
        raise SystemExit(f"Weird version '{version}' — expected like 0.14.0")

    patched = args.image.expanduser().resolve()
    disc = disc_from_bin_path(patched)
    info = resolve_info(patched, args.slug)
    pack_id = info["slug"]
    pack_dir = _ROOT / "builder" / pack_id

    print(f"Base:    {info['name']} ({info['slug']})")
    print(f"Version: {version}")
    print(f"Image:   {patched}")
    print(f"Disc:    {disc}")
    print(f"Output:  builder/{pack_id}/")

    build_one_disc(
        info=info,
        version=version,
        disc=disc,
        patched=patched,
        skip_verify=args.skip_verify,
    )

    upsert_pack_json(pack_dir, info, version, disc)
    update_manifest(info, version, disc)
    print(f"Updated {pack_dir / 'pack.json'}")
    print(f"Updated {MANIFEST_PATH.relative_to(_ROOT)} (enabled=true)")
    print("Commit JSON under builder/ only — not .bin/.cue.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
