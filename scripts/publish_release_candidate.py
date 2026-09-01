#!/usr/bin/env python3
"""Publish a finalized CSR+ or Highwind candidate to the local catalog.

The input is ``RUN/05-release-candidate/pack/<pack-id>``. The command copies
its layer, ``pack.json``, and ``VERSION`` into ``builder/<pack-id>/``, then
replaces or appends that base in ``builder/manifest.json``. It does not build
or revalidate a disc, contact the website, or publish remotely; run the staged
finalizer and builder verification first. Only ``csr-plus`` and ``highwind``
are accepted to prevent accidental catalog writes under arbitrary ids.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def publish(run_dir: Path, pack_id: str) -> None:
    """Copy required candidate files and update the enabled manifest entry."""
    candidate = run_dir / "05-release-candidate" / "pack" / pack_id
    pack_path = candidate / "pack.json"
    layer_path = candidate / "layers" / "disc1.layer.json"
    version_path = candidate / "VERSION"
    required = (pack_path, layer_path, version_path)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit(f"Missing release candidate files: {missing}")

    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    if pack.get("id") != pack_id:
        raise SystemExit(f"Pack id is {pack.get('id')!r}, expected {pack_id!r}")

    destination = ROOT / "builder" / pack_id
    (destination / "layers").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pack_path, destination / "pack.json")
    shutil.copyfile(layer_path, destination / "layers" / "disc1.layer.json")
    shutil.copyfile(version_path, destination / "VERSION")

    manifest_path = ROOT / "builder" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    # pack.json paths are relative to the pack directory; manifest paths are
    # relative to builder/, so publication must add the pack-id prefix.
    manifest_entry = dict(pack)
    manifest_entry["discs"] = {
        disc: f"./{pack_id}/{relative.removeprefix('./')}"
        for disc, relative in pack["discs"].items()
    }
    manifest_entry["enabled"] = True

    bases = manifest.get("bases", [])
    for index, entry in enumerate(bases):
        if entry.get("id") == pack_id:
            bases[index] = manifest_entry
            break
    else:
        bases.append(manifest_entry)

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Published {pack_id} {pack['version']} to {destination}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--pack-id", choices=("csr-plus", "highwind"), required=True)
    args = parser.parse_args()
    publish(args.run_dir.expanduser().resolve(), args.pack_id)


if __name__ == "__main__":
    main()
