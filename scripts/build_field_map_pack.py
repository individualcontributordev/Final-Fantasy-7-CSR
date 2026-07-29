#!/usr/bin/env python3
"""Build an ic-layer addon pack from selected FIELD map files on a flavor image.

Free checkbox (omit exclusiveGroup — preferred for independent CSR+ scenes):

  python3 scripts/build_field_map_pack.py \\
    --pristine workspace/csr/FINALFANTASY7_D1.bin \\
    --flavor-image workspace/csr-plus/FINALFANTASY7_D1.bin \\
    --files FIELD/EALS_1.DAT \\
    --pack-id csr-plus-scene-aerith-house-v0.1.0 \\
    --name "CSR+ scene — Aerith's house" \\
    --group-label "CSR+ scene — Aerith's house" \\
    --blurb "CSR+ trim of Aerith's house on CSR." \\
    --no-exclusive-group \\
    --compatible-bases csr-v0.14.1

Mutually exclusive variants: pass --exclusive-group <id> (dropdown in builder).
Without either flag, defaults to csr-scene-<pack-id-without-version> for back-compat.
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
	replace_file,
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
		try:
			replace_file(img, path, new_data)
		except ValueError as exc:
			raise SystemExit(str(exc)) from exc
		grew = f" (record patched {meta.size} → {len(new_data)})" if len(new_data) != meta.size else ""
		print(f"  inject {path} ({len(new_data)} → slot {meta.size}){grew}")
	return bytes(img)


def write_pack(
	*,
	pack_id: str,
	version: str,
	name: str,
	blurb: str,
	group_label: str,
	option_label: str,
	exclusive_group: str | None,
	compatible_bases: list[str],
	disc: int,
	layer: dict,
	files: list[str],
	update_manifest: bool,
) -> Path:
	pack_dir = _ROOT / "builder" / pack_id
	layer_dir = pack_dir / "layers"
	layer_dir.mkdir(parents=True, exist_ok=True)
	layer_name = f"disc{disc}.layer.json"
	layer_path = layer_dir / layer_name
	layer_path.write_text(json.dumps(layer, indent=2) + "\n", encoding="utf-8")

	pack_path = pack_dir / "pack.json"
	prev_discs: dict = {}
	prev_files: list[str] = []
	if pack_path.exists():
		prev = json.loads(pack_path.read_text(encoding="utf-8"))
		if isinstance(prev.get("discs"), dict):
			prev_discs = dict(prev["discs"])
		if isinstance(prev.get("files"), list):
			prev_files = list(prev["files"])

	discs = prev_discs
	discs[str(disc)] = f"./layers/{layer_name}"
	merged_files = list(dict.fromkeys([*prev_files, *files]))

	pack = {
		"id": pack_id,
		"name": name,
		"kind": "addon",
		"version": version,
		"blurb": blurb,
		"format": "ic-layer-v1",
		"groupLabel": group_label,
		"optionLabel": option_label,
		"compatibleBases": compatible_bases,
		"files": merged_files,
		"discs": discs,
	}
	# Missing exclusiveGroup → builder free checkbox; set only for mutex variants.
	if exclusive_group is not None:
		pack["exclusiveGroup"] = exclusive_group
	pack_path.write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")

	if update_manifest:
		data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
		entry = {
			"id": pack_id,
			"name": name,
			"kind": "addon",
			"blurb": blurb,
			"format": "ic-layer-v1",
			"groupLabel": group_label,
			"optionLabel": option_label,
			"compatibleBases": compatible_bases,
			"discs": {str(disc): f"./{pack_id}/layers/{layer_name}"},
			"enabled": True,
		}
		if exclusive_group is not None:
			entry["exclusiveGroup"] = exclusive_group
		addons = data.setdefault("addons", [])
		existing = next((a for a in addons if a.get("id") == pack_id), None)
		if existing and isinstance(existing.get("discs"), dict):
			merged = dict(existing["discs"])
			merged.update(entry["discs"])
			entry["discs"] = merged
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
	ap.add_argument("--disc", type=int, default=1, help="Disc number (1/2/3). Default: 1")
	ap.add_argument("--version", default="0.1.0")
	ap.add_argument("--name", required=True)
	ap.add_argument("--blurb", required=True)
	ap.add_argument("--group-label", required=True)
	ap.add_argument("--option-label", default="On")
	ap.add_argument(
		"--exclusive-group",
		default=None,
		help="Mutex group id (builder dropdown). Default if neither flag: "
		"csr-scene-<pack-id without version>",
	)
	ap.add_argument(
		"--no-exclusive-group",
		action="store_true",
		help="Omit exclusiveGroup (builder free checkbox). Preferred for independent scenes.",
	)
	ap.add_argument(
		"--compatible-bases",
		nargs="+",
		default=["clean"],
		help="Base ids this addon may be applied on top of. Default: clean",
	)
	ap.add_argument("--no-manifest", action="store_true")
	ap.add_argument(
		"--assert-no-overlap-with",
		type=Path,
		default=None,
		help="Another disc1.layer.json that must not overlap",
	)
	args = ap.parse_args()

	if args.no_exclusive_group and args.exclusive_group:
		raise SystemExit("Pass only one of --no-exclusive-group or --exclusive-group")

	files = [f.replace("\\", "/").upper() for f in args.files]
	for i, f in enumerate(files):
		if not f.startswith("FIELD/"):
			files[i] = f"FIELD/{f}"

	if args.no_exclusive_group:
		exclusive = None
	elif args.exclusive_group:
		exclusive = args.exclusive_group
	else:
		# Back-compat default (dropdown). New free scenes should pass --no-exclusive-group.
		exclusive = f"csr-scene-{args.pack_id.rsplit('-v', 1)[0]}"

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
			layer_id=f"{args.pack_id}-disc{args.disc}",
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
		compatible_bases=args.compatible_bases,
		disc=args.disc,
		layer=layer,
		files=files,
		update_manifest=not args.no_manifest,
	)
	print(f"Wrote {pack_dir.relative_to(_ROOT)}")

	if args.assert_no_overlap_with:
		assert_no_overlap(pack_dir / "layers" / f"disc{args.disc}.layer.json", args.assert_no_overlap_with)

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
