#!/usr/bin/env python3
"""Rebuild a published FIELD add-on from a builder zip extract you edited in Makou.

Workflow:
  1) Site builder: base + the add-on you are updating → zip
  2) Unzip; open the .bin in Makou; save back into the same folder
  3) Run this script on that folder (or .bin). APPLIED.txt is required.

  python3 scripts/update_addon_from_builder_zip.py path/to/extract-or.bin
  python3 scripts/update_addon_from_builder_zip.py path/to/extract --version 0.2.0

Reads Disc/Base/Add-ons from APPLIED.txt only. Diff baseline = that base image
(CSR for csr-v0.14.1, reconstructed from pristine + base layer if needed).
Injects the old pack's FIELD files from your edited .bin onto the baseline,
builds a new pack id with bumped version, updates manifest + csr-plus preset.

Playtest after (without full builder):

  python3 scripts/apply_layer.py workspace/pristine/FINALFANTASY7_D1.bin \\
    builder/csr-v0.14.1/layers/disc1.layer.json -o temp/csr-d1.bin
  python3 scripts/apply_layer.py temp/csr-d1.bin \\
    builder/<new-pack-id>/layers/disc1.layer.json -o temp/play-d1.bin
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

from apply_layer import apply_layer  # noqa: E402
from bin_diff_to_layer import build_layer  # noqa: E402
from build_field_map_pack import build_patched_image, write_pack  # noqa: E402

MANIFEST_PATH = _ROOT / "builder" / "manifest.json"
_MODDING = _ROOT.parent / "Final-Fantasy-7-Modding"


def _norm_name(s: str) -> str:
	s = s.lower().replace("—", "-").replace("–", "-")
	return re.sub(r"\s+", " ", s).strip()


def _load_catalog() -> dict[str, dict]:
	out: dict[str, dict] = {}
	for man in (MANIFEST_PATH, _MODDING / "builder" / "manifest.json"):
		if not man.is_file():
			continue
		data = json.loads(man.read_text(encoding="utf-8"))
		bdir = man.parent
		for key in ("bases", "addons"):
			for entry in data.get(key) or []:
				pid = entry.get("id")
				if pid:
					out[str(pid)] = {
						"entry": entry,
						"builder_dir": bdir,
						"kind": key[:-1],
					}
	if not out:
		raise SystemExit(f"No packs found (need {MANIFEST_PATH})")
	return out


def _resolve_bin(path: Path) -> Path:
	path = path.expanduser().resolve()
	if path.is_file() and path.suffix.lower() == ".bin":
		return path
	if path.is_dir():
		bins = sorted(path.glob("*.bin")) + sorted(path.glob("*.BIN"))
		if not bins:
			raise SystemExit(f"No .bin in {path}")
		if len(bins) > 1:
			print(f"Note: multiple .bin; using {bins[0].name}", file=sys.stderr)
		return bins[0]
	raise SystemExit(f"Not a .bin or directory: {path}")


def _match_base(label: str, catalog: dict[str, dict]) -> str:
	low = label.lower()
	if "unmodified" in low or "retail" in low or low in ("clean", "none"):
		return "clean"
	bn = _norm_name(label)
	bases = [(p, m) for p, m in catalog.items() if m["kind"] == "base"]
	for pid, meta in bases:
		nn = _norm_name(str(meta["entry"].get("name") or ""))
		if bn == nn or bn in nn or nn in bn:
			return pid
	for pid, _ in bases:
		if "highwind" in bn and "highwind" in pid:
			return pid
		if bn.startswith("csr") and pid.startswith("csr-v") and "highwind" not in bn:
			return pid
	raise SystemExit(f"APPLIED Base not in catalog: {label!r}")


def _match_addon(label: str, catalog: dict[str, dict]) -> str:
	ln = _norm_name(label)
	addons = [(p, m) for p, m in catalog.items() if m["kind"] == "addon"]
	for pid, meta in addons:
		if _norm_name(str(meta["entry"].get("name") or "")) == ln:
			return pid
	cands: list[tuple[int, str]] = []
	for pid, meta in addons:
		nn = _norm_name(str(meta["entry"].get("name") or ""))
		if nn and (nn in ln or ln in nn):
			cands.append((len(nn), pid))
	if cands:
		cands.sort(reverse=True)
		return cands[0][1]
	raise SystemExit(f"APPLIED Add-on not in catalog: {label!r}")


def _parse_applied(text: str, catalog: dict[str, dict]) -> tuple[int, str, list[str]]:
	disc_m = re.search(r"(?im)^\s*Disc:\s*([123])\s*$", text)
	if not disc_m:
		raise SystemExit("APPLIED.txt: missing Disc: 1|2|3")
	disc = int(disc_m.group(1))
	base_m = re.search(r"(?im)^\s*Base:\s*(.+?)\s*$", text)
	if not base_m:
		raise SystemExit("APPLIED.txt: missing Base:")
	base_id = _match_base(base_m.group(1).strip(), catalog)

	labels: list[str] = []
	addons_none = False
	in_addons = False
	for line in text.splitlines():
		if re.match(r"(?i)^\s*Add-ons:\s*$", line):
			in_addons = True
			continue
		if re.match(r"(?i)^\s*Add-ons:\s*none\s*$", line):
			addons_none = True
			in_addons = False
			continue
		if in_addons:
			if re.match(r"(?i)^\s*EDC/ECC", line) or re.match(r"(?i)^\s*Play:", line):
				break
			if not line.strip():
				if labels:
					break
				continue
			m = re.match(r"^\s*-\s+(.+?)\s*$", line)
			if m:
				labels.append(m.group(1).strip())
			else:
				break
	if addons_none:
		addon_ids: list[str] = []
	elif not labels and not re.search(r"(?im)^\s*Add-ons:", text):
		raise SystemExit("APPLIED.txt: missing Add-ons:")
	else:
		addon_ids = [_match_addon(lab, catalog) for lab in labels]
	return disc, base_id, addon_ids


def _parse_semver(version: str) -> tuple[int, int, int]:
	m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version.strip())
	if not m:
		raise SystemExit(f"Version not X.Y.Z: {version!r}")
	return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _bump_patch(version: str) -> str:
	a, b, c = _parse_semver(version)
	return f"{a}.{b}.{c + 1}"


def _stem_and_version(pack_id: str) -> tuple[str, str]:
	"""csr-plus-scene-aerith-house-v0.1.0 → (csr-plus-scene-aerith-house, 0.1.0)."""
	m = re.fullmatch(r"(.+)-v(\d+\.\d+\.\d+)", pack_id)
	if not m:
		raise SystemExit(f"Pack id must end with -vX.Y.Z: {pack_id!r}")
	return m.group(1), m.group(2)


def _layer_path(meta: dict, disc: int) -> Path:
	discs = meta["entry"].get("discs") or {}
	rel = discs.get(str(disc)) or discs.get(disc)
	if not rel:
		raise SystemExit(f"{meta['entry'].get('id')}: no layer for disc {disc}")
	return (meta["builder_dir"] / str(rel).lstrip("./")).resolve()


def _base_image_bytes(base_id: str, disc: int, catalog: dict[str, dict], pristine: Path) -> bytes:
	"""Return baseline disc image for addon diff (CSR for csr-v…, not retail)."""
	if base_id in ("clean", "unmodified"):
		return pristine.read_bytes()
	if base_id not in catalog or catalog[base_id]["kind"] != "base":
		raise SystemExit(f"Unknown base {base_id!r}")
	# Prefer workspace cache if present
	flavor = "csr" if base_id.startswith("csr-v") else (
		"highwind" if "highwind" in base_id else base_id
	)
	cached = _ROOT / "workspace" / flavor / f"FINALFANTASY7_D{disc}.bin"
	if cached.is_file():
		print(f"Baseline image: {cached}")
		return cached.read_bytes()
	print(f"Reconstructing baseline {base_id} disc {disc} → memory")
	img = bytearray(pristine.read_bytes())
	layer = json.loads(_layer_path(catalog[base_id], disc).read_text(encoding="utf-8"))
	apply_layer(img, layer)
	return bytes(img)


def _pick_target_addon(
	addon_ids: list[str],
	catalog: dict[str, dict],
	*,
	which: str | None,
) -> str:
	if not addon_ids:
		raise SystemExit("APPLIED.txt has no add-ons — nothing to update")
	if which:
		if which in addon_ids:
			return which
		# allow stem match
		for a in addon_ids:
			if a == which or a.startswith(which.rstrip("-") + "-v") or which in a:
				return a
		raise SystemExit(f"--addon {which!r} not in APPLIED stack {addon_ids}")
	# Prefer sole CSR+ scene, else sole addon
	scenes = [a for a in addon_ids if a.startswith("csr-plus-scene-")]
	if len(scenes) == 1:
		return scenes[0]
	if len(addon_ids) == 1:
		return addon_ids[0]
	raise SystemExit(
		"Multiple add-ons in APPLIED.txt; pass --addon <id-or-stem>. Got: "
		+ ", ".join(addon_ids)
	)


def _load_old_pack_json(pack_id: str) -> dict:
	p = _ROOT / "builder" / pack_id / "pack.json"
	if not p.is_file():
		raise SystemExit(f"Missing local pack (pull main?): {p}")
	return json.loads(p.read_text(encoding="utf-8"))


def _retire_old_in_manifest(old_id: str, new_id: str) -> None:
	data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
	for a in data.get("addons") or []:
		if a.get("id") == old_id:
			a["enabled"] = False
	for preset in data.get("presets") or []:
		addons = preset.get("addons")
		if not isinstance(addons, list):
			continue
		preset["addons"] = [new_id if x == old_id else x for x in addons]
		# de-dupe preserving order
		seen: set[str] = set()
		out: list[str] = []
		for x in preset["addons"]:
			if x not in seen:
				seen.add(x)
				out.append(x)
		preset["addons"] = out
	MANIFEST_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
	print(f"Retired {old_id} (enabled=false); presets now use {new_id} where listed")


def main() -> int:
	ap = argparse.ArgumentParser(
		description="Update a FIELD add-on from a Makou-edited builder zip extract"
	)
	ap.add_argument(
		"path",
		type=Path,
		help="Edited .bin or extract folder (must contain APPLIED.txt + .bin)",
	)
	ap.add_argument(
		"--version",
		default=None,
		help="New semver X.Y.Z (default: bump patch of pack in APPLIED)",
	)
	ap.add_argument(
		"--addon",
		default=None,
		help="Which APPLIED add-on to update when several are listed",
	)
	ap.add_argument(
		"--pristine",
		type=Path,
		default=_ROOT / "workspace" / "pristine" / "FINALFANTASY7_D1.bin",
		help="Retail disc image for this disc (default workspace/pristine D1; "
		"override path/name for disc 2/3)",
	)
	ap.add_argument("--no-manifest", action="store_true")
	ap.add_argument(
		"--keep-old-enabled",
		action="store_true",
		help="Do not set old pack enabled=false / preset swap",
	)
	args = ap.parse_args()

	catalog = _load_catalog()
	bin_path = _resolve_bin(args.path)
	applied_path = bin_path.parent / "APPLIED.txt"
	if not applied_path.is_file():
		raise SystemExit(f"APPLIED.txt required next to image: {applied_path}")

	disc, base_id, addon_ids = _parse_applied(
		applied_path.read_text(encoding="utf-8", errors="replace"),
		catalog,
	)
	print(f"APPLIED: disc={disc} base={base_id} addons={addon_ids}")

	old_id = _pick_target_addon(addon_ids, catalog, which=args.addon)
	old_pack = _load_old_pack_json(old_id)
	files = list(old_pack.get("files") or [])
	if not files:
		raise SystemExit(f"{old_id}: pack.json has no files[]")
	files = [f.replace("\\", "/").upper() for f in files]
	for i, f in enumerate(files):
		if not f.startswith("FIELD/"):
			files[i] = f"FIELD/{f}"

	stem, old_ver = _stem_and_version(old_id)
	new_ver = args.version.strip() if args.version else _bump_patch(old_ver)
	_parse_semver(new_ver)  # validate
	new_id = f"{stem}-v{new_ver}"
	if new_id == old_id:
		raise SystemExit(f"New id equals old ({new_id}); pass a higher --version")

	# Pristine path: if default D1 but disc!=1, require explicit file
	pristine_path = args.pristine.expanduser().resolve()
	if disc != 1 and pristine_path.name.upper().endswith("D1.BIN"):
		alt = pristine_path.parent / f"FINALFANTASY7_D{disc}.bin"
		if alt.is_file():
			pristine_path = alt
		else:
			raise SystemExit(
				f"Disc {disc}: pass --pristine workspace/pristine/FINALFANTASY7_D{disc}.bin"
			)
	if not pristine_path.is_file():
		raise SystemExit(f"Missing pristine image: {pristine_path}")

	print(f"Updating {old_id} → {new_id}")
	print(f"  files={files}")
	print(f"  diff baseline=base {base_id} (not full multi-addon stack)")

	baseline = _base_image_bytes(base_id, disc, catalog, pristine_path)
	flavor = bin_path.read_bytes()

	print("=== inject maps from edited image onto baseline ===")
	patched = build_patched_image(baseline, flavor, files)

	with tempfile.TemporaryDirectory(prefix="csr-update-addon-") as tmp:
		tmp_path = Path(tmp)
		base_bin = tmp_path / "baseline.bin"
		edit_bin = tmp_path / "edited.bin"
		base_bin.write_bytes(baseline)
		edit_bin.write_bytes(patched)
		print("=== diff → layer ===")
		layer = build_layer(
			base_bin,
			edit_bin,
			layer_id=f"{new_id}-disc{disc}",
			description=str(old_pack.get("blurb") or new_id),
		)

	stats = layer["stats"]
	print(f"  records={stats['records']} changedBytes={stats['changedBytes']}")
	if stats["records"] == 0:
		raise SystemExit("Empty layer — edited maps match baseline?")

	name = str(old_pack.get("name") or new_id)
	blurb = str(old_pack.get("blurb") or name)
	group_label = str(old_pack.get("groupLabel") or name)
	option_label = str(old_pack.get("optionLabel") or "On")
	exclusive = old_pack.get("exclusiveGroup")
	if exclusive is not None:
		exclusive = str(exclusive)
	compat = list(old_pack.get("compatibleBases") or ["csr-v0.14.1"])

	pack_dir = write_pack(
		pack_id=new_id,
		version=new_ver,
		name=name,
		blurb=blurb,
		group_label=group_label,
		option_label=option_label,
		exclusive_group=exclusive,
		compatible_bases=compat,
		disc=disc,
		layer=layer,
		files=files,
		update_manifest=not args.no_manifest,
	)
	print(f"Wrote {pack_dir.relative_to(_ROOT)}")

	if not args.no_manifest and not args.keep_old_enabled:
		_retire_old_in_manifest(old_id, new_id)

	print()
	print("Next — verify stack:")
	print(
		f"  python3 scripts/verify_builder_config.py \\\n"
		f"    --pristine {pristine_path} \\\n"
		f"    --disc {disc} --base {base_id} --addon {new_id}"
	)
	print("Playtest layer-only (example CSR + new scene):")
	print(
		f"  mkdir -p temp\n"
		f"  python3 scripts/apply_layer.py {pristine_path} \\\n"
		f"    builder/{base_id}/layers/disc{disc}.layer.json -o temp/base-d{disc}.bin\n"
		f"  python3 scripts/apply_layer.py temp/base-d{disc}.bin \\\n"
		f"    builder/{new_id}/layers/disc{disc}.layer.json -o temp/play-d{disc}.bin"
	)
	print("Then DuckStation temp/play-dN.bin; commit builder/ when happy.")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
