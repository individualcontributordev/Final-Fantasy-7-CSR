#!/usr/bin/env python3
"""Build an ic-layer addon pack from selected FIELD maps on an edited disc image.

CSR+ scene (most fields inferred — preferred):

  python3 scripts/build_field_map_pack.py \\
    --edited-image /path/to/makou.bin \\
    --changed-maps temp/field-diff.json \\
    --pack-id csr-plus-scene-cota-fd-manip-v0.1.0 \\
    --disc 2

Infers for csr-plus-scene-* packs:
  --compatible-bases  all live csr-v* from builder/manifest.json
  --no-exclusive-group
  --name / --group-label / --blurb / --version from pack-id
  --pristine            cache/csr D{N} (built from pristine + CSR layer if needed)

Explicit --name / --compatible-bases / etc. still override.

General / non-scene packs still need the full flags (defaults stay explicit).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_ROOT = _SCRIPTS.parent
if str(_SCRIPTS) not in sys.path:
	sys.path.insert(0, str(_SCRIPTS))

from bin_diff_to_layer import build_layer  # noqa: E402
from local_paths import ensure_cached_base  # noqa: E402
from psx_mode2_iso import (  # noqa: E402
	byte_ranges_overlap,
	extract_file,
	find_file,
	replace_file,
)

MANIFEST_PATH = _ROOT / "builder" / "manifest.json"


def live_csr_base_ids() -> list[str]:
	"""Enabled csr-v* base ids from builder/manifest.json (sorted)."""
	if not MANIFEST_PATH.is_file():
		return []
	data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
	out = []
	for b in data.get("bases") or []:
		pid = str(b.get("id") or "")
		if not pid.startswith("csr-v"):
			continue
		if b.get("enabled") is False:
			continue
		out.append(pid)
	return sorted(out)


def is_csr_plus_scene_pack(pack_id: str) -> bool:
	return str(pack_id).startswith("csr-plus-scene-")


def parse_pack_id(pack_id: str) -> tuple[str, str | None]:
	"""csr-plus-scene-cota-fd-manip-v0.1.0 → (stem, version or None)."""
	m = re.fullmatch(r"(.+)-v(\d+\.\d+\.\d+)", pack_id)
	if m:
		return m.group(1), m.group(2)
	return pack_id, None


def title_from_scene_stem(stem: str) -> str:
	"""csr-plus-scene-cota-fd-manip → CSR+ Cota Fd Manip (readable enough)."""
	body = stem
	if body.startswith("csr-plus-scene-"):
		body = body[len("csr-plus-scene-") :]
	# Keep known acronyms uppercase when whole token
	parts = []
	for tok in body.replace("_", "-").split("-"):
		if not tok:
			continue
		up = tok.upper()
		if up in {"COTA", "FD", "HQ", "CSR"}:
			parts.append(up)
		else:
			parts.append(tok[:1].upper() + tok[1:].lower() if len(tok) > 1 else up)
	return "CSR+ " + " ".join(parts)


def default_csr_scene_baseline(disc: int) -> Path:
	"""CSR disc image path, creating cache/csr if needed from latest/live csr-v* layer."""
	ids = live_csr_base_ids()
	if not ids:
		raise SystemExit(
			"No live csr-v* bases in builder/manifest.json — pass --pristine explicitly"
		)
	# Prefer highest version string sort (csr-v0.14.1 > csr-v0.9.0 for normal scheme)
	base_id = sorted(ids, key=lambda s: [int(x) for x in s.replace("csr-v", "").split(".")])[-1]
	layer = _ROOT / "builder" / base_id / "layers" / f"disc{disc}.layer.json"
	if not layer.is_file():
		raise SystemExit(f"Missing layer for default baseline: {layer}")
	data, path = ensure_cached_base(
		base_id=base_id,
		disc=disc,
		layer_path=layer,
		write_cache=True,
	)
	if path is None:
		# should not happen with write_cache
		raise SystemExit("ensure_cached_base did not return a path")
	print(f"Baseline (inferred): {base_id} → {path}")
	return path


def files_from_changed_maps_json(path: Path) -> list[str]:
	"""FIELD/*.DAT paths from list_changed_field_maps.py JSON output."""
	data = json.loads(path.read_text(encoding="utf-8"))
	out: list[str] = []
	seen: set[str] = set()
	for m in data.get("maps") or []:
		for p in m.get("files") or []:
			p = str(p).replace("\\", "/").upper()
			if not p.startswith("FIELD/"):
				p = f"FIELD/{p}"
			if not p.endswith(".DAT"):
				continue
			if p not in seen:
				seen.add(p)
				out.append(p)
	if not out:
		raise SystemExit(f"{path}: no FIELD/*.DAT paths in changed-maps JSON")
	return out


def build_patched_image(
	pristine: bytes,
	edited_image: bytes,
	files: list[str],
) -> bytes:
	img = bytearray(pristine)
	for path in files:
		path = path.replace("\\", "/").upper()
		if not path.startswith("FIELD/"):
			path = f"FIELD/{path}"
		new_data = extract_file(edited_image, path)
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
			"version": version,
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
	ap = argparse.ArgumentParser(
		description="Build FIELD map-file addon pack",
		epilog="csr-plus-scene-* packs infer bases, labels, checkbox, and CSR baseline.",
	)
	ap.add_argument(
		"--pristine",
		type=Path,
		default=None,
		help="Baseline disc image (default for csr-plus-scene-*: cache/csr D{disc})",
	)
	ap.add_argument(
		"--edited-image",
		type=Path,
		required=True,
		help="Updated disc .bin after Makou (builder zip extract)",
	)
	ap.add_argument(
		"--files",
		nargs="+",
		default=None,
		help="ISO paths e.g. FIELD/SHIP_1.DAT (or use --changed-maps)",
	)
	ap.add_argument(
		"--changed-maps",
		type=Path,
		default=None,
		help="JSON from list_changed_field_maps.py",
	)
	ap.add_argument("--pack-id", required=True)
	ap.add_argument("--disc", type=int, default=1, help="Disc 1/2/3 (default 1)")
	ap.add_argument("--version", default=None, help="Default: from pack-id -vX.Y.Z or 0.1.0")
	ap.add_argument("--name", default=None, help="Default: from pack-id for scenes")
	ap.add_argument("--blurb", default=None, help="Default: for scenes")
	ap.add_argument("--group-label", default=None, help="Default: same as name")
	ap.add_argument("--option-label", default="On")
	ap.add_argument("--exclusive-group", default=None, help="Mutex dropdown id")
	ap.add_argument(
		"--no-exclusive-group",
		action="store_true",
		help="Checkbox. Default for csr-plus-scene-*",
	)
	ap.add_argument(
		"--compatible-bases",
		nargs="*",
		default=None,
		help="Default: all live csr-v* for scenes; clean otherwise",
	)
	ap.add_argument("--no-manifest", action="store_true")
	ap.add_argument("--assert-no-overlap-with", type=Path, default=None)
	args = ap.parse_args()

	scene = is_csr_plus_scene_pack(args.pack_id)
	stem, ver_from_id = parse_pack_id(args.pack_id)

	if args.no_exclusive_group and args.exclusive_group:
		raise SystemExit("Pass only one of --no-exclusive-group or --exclusive-group")
	if bool(args.files) == bool(args.changed_maps):
		raise SystemExit("Pass exactly one of --files or --changed-maps")

	if args.changed_maps:
		files = files_from_changed_maps_json(args.changed_maps.expanduser().resolve())
		print(f"=== files from {args.changed_maps.name} ({len(files)}) ===")
		for f in files:
			print(f"  {f}")
	else:
		files = [f.replace("\\", "/").upper() for f in args.files]
		for i, f in enumerate(files):
			if not f.startswith("FIELD/"):
				files[i] = f"FIELD/{f}"

	version = args.version or ver_from_id or "0.1.0"
	if scene:
		name = args.name or title_from_scene_stem(stem)
		group_label = args.group_label or name
		blurb = args.blurb or f"{name} on CSR."
		if args.compatible_bases:
			compatible_bases = list(args.compatible_bases)
		else:
			compatible_bases = live_csr_base_ids()
			if not compatible_bases:
				raise SystemExit("No live csr-v* in manifest; pass --compatible-bases")
			print(f"compatibleBases (inferred live CSR): {compatible_bases}")
		if args.exclusive_group:
			exclusive = args.exclusive_group
		else:
			exclusive = None
			if not args.no_exclusive_group:
				print("exclusiveGroup: omitted (csr-plus-scene default checkbox)")
	else:
		if not args.name or not args.blurb or not args.group_label:
			raise SystemExit(
				"Non-scene packs need --name, --group-label, --blurb "
				"(or use pack-id csr-plus-scene-* )"
			)
		name = args.name
		group_label = args.group_label
		blurb = args.blurb
		if args.compatible_bases:
			compatible_bases = list(args.compatible_bases)
		else:
			compatible_bases = ["clean"]
		if args.no_exclusive_group:
			exclusive = None
		elif args.exclusive_group:
			exclusive = args.exclusive_group
		else:
			exclusive = f"csr-scene-{stem}"

	if args.pristine:
		pristine_path = args.pristine.expanduser().resolve()
	elif scene:
		pristine_path = default_csr_scene_baseline(args.disc)
	else:
		raise SystemExit("Pass --pristine (required unless pack-id is csr-plus-scene-*)")
	if not pristine_path.is_file():
		raise SystemExit(f"Missing baseline image: {pristine_path}")

	edited_path = args.edited_image.expanduser().resolve()
	if not edited_path.is_file():
		raise SystemExit(f"Missing edited image: {edited_path}")

	print("=== inject maps onto baseline ===")
	print(f"  baseline={pristine_path}")
	print(f"  edited={edited_path}")
	pristine = pristine_path.read_bytes()
	edited = edited_path.read_bytes()
	patched = build_patched_image(pristine, edited, files)

	with tempfile.TemporaryDirectory(prefix="csr-map-pack-") as tmp:
		tmp_path = Path(tmp)
		pr_bin = tmp_path / "pristine.bin"
		pt_bin = tmp_path / "patched.bin"
		pt_bin.write_bytes(patched)
		shutil.copyfile(pristine_path, pr_bin)
		print("=== diff -> layer ===")
		layer = build_layer(
			pr_bin,
			pt_bin,
			layer_id=f"{args.pack_id}-disc{args.disc}",
			description=blurb,
		)

	stats = layer["stats"]
	print(f"  records={stats['records']} changedBytes={stats['changedBytes']}")
	if stats["records"] == 0:
		raise SystemExit("Empty layer — files identical to baseline?")

	pack_dir = write_pack(
		pack_id=args.pack_id,
		version=version,
		name=name,
		blurb=blurb,
		group_label=group_label,
		option_label=args.option_label,
		exclusive_group=exclusive,
		compatible_bases=compatible_bases,
		disc=args.disc,
		layer=layer,
		files=files,
		update_manifest=not args.no_manifest,
	)
	print(f"Wrote {pack_dir.relative_to(_ROOT)}")
	print(f"  id={args.pack_id} name={name!r} bases={compatible_bases}")

	if args.assert_no_overlap_with:
		assert_no_overlap(
			pack_dir / "layers" / f"disc{args.disc}.layer.json",
			args.assert_no_overlap_with,
		)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
