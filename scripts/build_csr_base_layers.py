#!/usr/bin/env python3
"""Build ic-layer-v1 packs for one CSR base (csr / csr-plus / csr-plusplus).

Git Bash examples:

  python scripts/build_csr_base_layers.py workspace/csr --version 0.14.0
  python scripts/build_csr_base_layers.py workspace/csr-plus --version 0.1.0
  python scripts/build_csr_base_layers.py workspace/csr-plusplus --version 0.1.0 --discs 1,2,3

Looks for:
  workspace/pristine/FINALFANTASY7_DN.bin
  <base-dir>/FINALFANTASY7_DN (patched).bin

Writes builder/<slug>-v<version>/layers/discN.layer.json, updates pack.json + manifest.json,
and verifies each layer against the patched image.
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

BASES = {
    "csr": {
        "slug": "csr",
        "name": "CSR",
        "blurb": "CutScenes Removed — skill checks kept.",
        "dir": "workspace/csr",
    },
    "csr-plus": {
        "slug": "csr-plus",
        "name": "CSR+",
        "blurb": "More aggressive cutscene removal.",
        "dir": "workspace/csr-plus",
    },
    "csr-plusplus": {
        "slug": "csr-plusplus",
        "name": "CSR++",
        "blurb": "CSR+ plus filler dialogue trimmed.",
        "dir": "workspace/csr-plusplus",
    },
}

PRISTINE_DIR = _ROOT / "workspace" / "pristine"
MANIFEST_PATH = _ROOT / "builder" / "manifest.json"


def resolve_base(dir_or_slug: str) -> tuple[str, dict, Path]:
    raw = Path(dir_or_slug)
    # Accept workspace/csr, csr, csr-plus, etc.
    key = raw.name if raw.name in BASES else dir_or_slug.strip().strip("/\\")
    if key not in BASES:
        known = ", ".join(BASES)
        raise SystemExit(f"Unknown base '{dir_or_slug}'. Use one of: {known}")
    info = BASES[key]
    base_dir = (_ROOT / info["dir"]).resolve()
    if not base_dir.is_dir():
        raise SystemExit(f"Missing base directory: {base_dir}")
    return key, info, base_dir


def disc_paths(base_dir: Path, disc: int) -> tuple[Path, Path]:
    pristine = PRISTINE_DIR / f"FINALFANTASY7_D{disc}.bin"
    patched = base_dir / f"FINALFANTASY7_D{disc} (patched).bin"
    return pristine, patched


def available_discs(base_dir: Path) -> list[int]:
    found = []
    for disc in (1, 2, 3):
        pristine, patched = disc_paths(base_dir, disc)
        if pristine.is_file() and patched.is_file():
            found.append(disc)
    return found


def parse_discs(spec: str | None, base_dir: Path) -> list[int]:
    if spec:
        discs = []
        for part in spec.split(","):
            part = part.strip()
            if not part:
                continue
            disc = int(part)
            if disc not in (1, 2, 3):
                raise SystemExit(f"Disc must be 1, 2, or 3 — got {disc}")
            discs.append(disc)
        return discs
    found = available_discs(base_dir)
    if not found:
        raise SystemExit(
            f"No disc pairs found under {base_dir} and {PRISTINE_DIR}.\n"
            f"Expected FINALFANTASY7_DN.bin + FINALFANTASY7_DN (patched).bin"
        )
    return found


def write_pack_json(pack_dir: Path, info: dict, version: str, discs: list[int]) -> None:
    pack = {
        "id": f"{info['slug']}-v{version}",
        "name": info["name"],
        "kind": "base",
        "exclusiveGroup": "cutscenes",
        "version": version,
        "blurb": info["blurb"],
        "format": "ic-layer-v1",
        "discs": {str(d): f"./layers/disc{d}.layer.json" for d in discs},
    }
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "pack.json").write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")


def update_manifest(info: dict, version: str, discs: list[int]) -> None:
    if not MANIFEST_PATH.is_file():
        raise SystemExit(f"Missing {MANIFEST_PATH}")
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    pack_id = f"{info['slug']}-v{version}"
    entry = {
        "id": pack_id,
        "name": f"{info['name']} v{version}",
        "kind": "base",
        "exclusiveGroup": "cutscenes",
        "blurb": info["blurb"],
        "format": "ic-layer-v1",
        "discs": {
            str(d): f"./{pack_id}/layers/disc{d}.layer.json" for d in discs
        },
        "enabled": True,
    }

    bases = data.setdefault("bases", [])
    replaced = False
    for i, existing in enumerate(bases):
        ex_id = str(existing.get("id", ""))
        if ex_id == pack_id or ex_id.startswith(f"{info['slug']}-v"):
            bases[i] = entry
            replaced = True
            break
    if not replaced:
        bases.append(entry)

    MANIFEST_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def verify(pristine: Path, layer_path: Path, patched: Path) -> None:
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
    base_dir: Path,
    skip_verify: bool,
) -> Path:
    pristine, patched = disc_paths(base_dir, disc)
    if not pristine.is_file():
        raise SystemExit(f"Missing pristine: {pristine}")
    if not patched.is_file():
        raise SystemExit(f"Missing patched: {patched}")

    pack_id = f"{info['slug']}-v{version}"
    out_dir = _ROOT / "builder" / pack_id / "layers"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"disc{disc}.layer.json"

    layer_id = f"{info['slug']}-disc{disc}-v{version}"
    description = f"{info['name']} v{version} — NTSC-U Disc {disc}"
    print(f"\n=== Disc {disc}: diff ===")
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
        description="Build CSR/CSR+/CSR++ disc layers for the browser builder."
    )
    ap.add_argument(
        "base",
        help="Base directory or slug: workspace/csr | csr | csr-plus | csr-plusplus",
    )
    ap.add_argument(
        "--version",
        required=True,
        help="Version string, e.g. 0.14.0 or 0.1.0",
    )
    ap.add_argument(
        "--discs",
        default=None,
        help="Comma list of discs (default: all pairs that exist). Example: 1 or 1,2,3",
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

    _key, info, base_dir = resolve_base(args.base)
    discs = parse_discs(args.discs, base_dir)
    pack_id = f"{info['slug']}-v{version}"
    pack_dir = _ROOT / "builder" / pack_id

    print(f"Base:    {info['name']} ({info['slug']})")
    print(f"Version: {version}")
    print(f"Dir:     {base_dir}")
    print(f"Discs:   {discs}")
    print(f"Output:  builder/{pack_id}/")

    for disc in discs:
        build_one_disc(
            info=info,
            version=version,
            disc=disc,
            base_dir=base_dir,
            skip_verify=args.skip_verify,
        )

    write_pack_json(pack_dir, info, version, discs)
    update_manifest(info, version, discs)
    print(f"\nUpdated {pack_dir / 'pack.json'}")
    print(f"Updated {MANIFEST_PATH.relative_to(_ROOT)} (enabled=true)")
    print("\nDone. Commit JSON under builder/ only — not .bin/.cue.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
