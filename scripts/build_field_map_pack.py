#!/usr/bin/env python3
"""Build an ic-layer addon pack from selected FIELD map files on a flavor image.

  python scripts/build_field_map_pack.py \\
    --pristine workspace/pristine/FINALFANTASY7_D1.bin \\
    --flavor-image workspace/csr/FINALFANTASY7_D1.bin \\
    --files FIELD/SHIP_1.DAT FIELD/SHIP_2.DAT \\
    --pack-id csr-scene-boat-v0.1.0 \\
    --name "CSR scene — Boat to Costa" \\
    --group-label "CSR scene — Boat to Costa" \\
    --option-label "On" \\
    --blurb "Removes the boat trip to Costa del Sol (prototype map pack)."
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_ROOT = _SCRIPTS.parent
if str(_SCRIPTS) not in sys.path:
	sys.path.insert(0, str(_SCRIPTS))

from bin_diff_to_layer import build_layer  # noqa: E402
from psx_mode2_iso import (  # noqa: E402
	byte_ranges_overlap,
	extract_file,
	find_file,
	replace_file_padded,
)

MANIFEST_PATH = _ROOT / "builder" / "manifest.json"


def build_patched_image(
	pristine: bytes,
	flavor_image: bytes,
	files: list[str],
) -> bytes:
	img = bytearray(pristine)
	for path in files:
		path = path.replace("\\", "/").upper()
		if not path.startswith("FIELD/"):
			path = f"FIELD/{path}"
		new_data = extract_file(flavor_image, path)
		meta = find_file(pristine, path)
		if len(new_data) > meta.size:
			raise SystemExit(
				f"{path}: flavor file {len(new_data)} bytes > ISO slot {meta.size}"
			)
		replace_file_padded(img, path, new_data)
		print(f"  inject {path} ({len(new_data)} → slot {meta.size})")
	return bytes(img)


def write_pack(
	*,
	pack_id: str,
	version: str,
	name: str,
	blurb: str,
	group_label: str,
	option_label: str,
	exclusive_group: str,
	layer: dict,
	files: list[str],
	update_manifest: bool,
) -> Path:
	pack_dir = _ROOT / "builder" / pack_id
	layer_dir = pack_dir / "layers"
	layer_dir.mkdir(parents=True, exist_ok=True)
	layer_path = layer_dir / "disc1.layer.json"
	layer_path.write_text(json.dumps(layer, indent=2) + "\n", encoding="utf-8")

	pack = {
		"id": pack_id,
		"name": name,
		"kind": "addon",
		"version": version,
		"blurb": blurb,
		"format": "ic-layer-v1",
		"exclusiveGroup": exclusive_group,
		"groupLabel": group_label,
		"optionLabel": option_label,
		"compatibleBases": ["clean"],
		"files": files,
		"discs": {"1": "./layers/disc1.layer.json"},
	}
	(pack_dir / "pack.json").write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")

	if update_manifest:
		data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
		entry = {
			"id": pack_id,
			"name": name,
			"kind": "addon",
			"blurb": blurb,
			"format": "ic-layer-v1",
			"exclusiveGroup": exclusive_group,
			"groupLabel": group_label,
			"optionLabel": option_label,
			"compatibleBases": ["clean"],
			"discs": {"1": f"./{pack_id}/layers/disc1.layer.json"},
			"enabled": True,
		}
		addons = data.setdefault("addons", [])
		addons[:] = [a for a in addons if a.get("id") != pack_id]
		addons.append(entry)
		MANIFEST_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
		print(f"Updated {MANIFEST_PATH.relative_to(_ROOT)}")

	return pack_dir


def assert_no_overlap(layer_a: Path, layer_b: Path) -> None:
	a = json.loads(layer_a.read_text(encoding="utf-8"))
	b = json.loads(layer_b.read_text(encoding="utf-8"))
	hits = byte_ranges_overlap(a["records"], b["records"])
	if hits:
		raise SystemExit(
			f"OVERLAP between {layer_a.name} and {layer_b.name}: "
			f"{len(hits)} colliding spans (first {hits[0]})"
		)
	print(f"Overlap OK: {layer_a.parent.parent.name} ∩ {layer_b.parent.parent.name} = ∅")


def main() -> int:
	ap = argparse.ArgumentParser(description="Build FIELD map-file addon pack")
	ap.add_argument("--pristine", type=Path, required=True)
	ap.add_argument("--flavor-image", type=Path, required=True)
	ap.add_argument("--files", nargs="+", required=True, help="ISO paths e.g. FIELD/SHIP_1.DAT")
	ap.add_argument("--pack-id", required=True)
	ap.add_argument("--version", default="0.1.0")
	ap.add_argument("--name", required=True)
	ap.add_argument("--blurb", required=True)
	ap.add_argument("--group-label", required=True)
	ap.add_argument("--option-label", default="On")
	ap.add_argument(
		"--exclusive-group",
		default=None,
		help="Default: csr-scene-<pack-id without version>",
	)
	ap.add_argument("--no-manifest", action="store_true")
	ap.add_argument(
		"--assert-no-overlap-with",
		type=Path,
		default=None,
		help="Another disc1.layer.json that must not overlap",
	)
	args = ap.parse_args()

	files = [f.replace("\\", "/").upper() for f in args.files]
	for i, f in enumerate(files):
		if not f.startswith("FIELD/"):
			files[i] = f"FIELD/{f}"

	exclusive = args.exclusive_group or f"csr-scene-{args.pack_id.rsplit('-v', 1)[0]}"

	print("=== inject maps onto pristine ===")
	pristine = args.pristine.read_bytes()
	flavor = args.flavor_image.read_bytes()
	patched = build_patched_image(pristine, flavor, files)

	with tempfile.TemporaryDirectory(prefix="csr-map-pack-") as tmp:
		tmp_path = Path(tmp)
		pr_bin = tmp_path / "pristine.bin"
		pt_bin = tmp_path / "patched.bin"
		# Avoid rewriting 700MB twice from Python if possible — write patched only,
		# diff against original path on disk.
		pt_bin.write_bytes(patched)
		shutil.copyfile(args.pristine, pr_bin)

		print("=== diff → layer ===")
		layer = build_layer(
			pr_bin,
			pt_bin,
			layer_id=f"{args.pack_id}-disc1",
			description=args.blurb,
		)

	stats = layer["stats"]
	print(f"  records={stats['records']} changedBytes={stats['changedBytes']}")
	if stats["records"] == 0:
		raise SystemExit("Empty layer — files identical to pristine?")

	pack_dir = write_pack(
		pack_id=args.pack_id,
		version=args.version,
		name=args.name,
		blurb=args.blurb,
		group_label=args.group_label,
		option_label=args.option_label,
		exclusive_group=exclusive,
		layer=layer,
		files=files,
		update_manifest=not args.no_manifest,
	)
	print(f"Wrote {pack_dir.relative_to(_ROOT)}")

	if args.assert_no_overlap_with:
		assert_no_overlap(pack_dir / "layers" / "disc1.layer.json", args.assert_no_overlap_with)

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
