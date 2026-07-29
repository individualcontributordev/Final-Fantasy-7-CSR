#!/usr/bin/env python3
"""Verify a builder configuration by stacking ic-layer packs like the site builder.

SRP: read-only resolve + apply + check. Does not publish or patch workspace bins.

  python scripts/verify_builder_config.py \\
    --pristine workspace/pristine/FINALFANTASY7_D1.bin \\
    --disc 1 \\
    --base csr-v0.14.1 \\
    --addon csr-plus-scene-aerith-house-v0.1.0

  # Cross-repo (Modding add-ons on CSR/Highwind/clean):
  python scripts/verify_builder_config.py \\
    --pristine workspace/pristine/FINALFANTASY7_D1.bin \\
    --disc 1 --base clean \\
    --addon field-encounter-25-v0.1.2 \\
    --manifest builder/manifest.json \\
    --extra-manifest /path/to/Final-Fantasy-7-Modding/builder/manifest.json

Exit 0 only if every selected pack has a disc layer, compatibleBases match,
and each layer's records match the image after apply (builder-equivalent stack).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_ROOT = _SCRIPTS.parent
if str(_SCRIPTS) not in sys.path:
	sys.path.insert(0, str(_SCRIPTS))

from apply_layer import apply_layer  # noqa: E402


def _load_manifest(path: Path) -> tuple[Path, dict]:
	path = path.expanduser().resolve()
	data = json.loads(path.read_text(encoding="utf-8"))
	return path.parent, data


def _index_packs(builder_dir: Path, data: dict) -> dict[str, dict]:
	"""id -> {entry, builder_dir}"""
	out: dict[str, dict] = {}
	for key in ("bases", "addons"):
		for entry in data.get(key) or []:
			pid = entry.get("id")
			if not pid:
				continue
			out[str(pid)] = {"entry": entry, "builder_dir": builder_dir, "kind": key[:-1]}
	return out


def _layer_path(meta: dict, disc: int) -> Path:
	entry = meta["entry"]
	discs = entry.get("discs") or {}
	rel = discs.get(str(disc)) or discs.get(disc)
	if not rel:
		raise SystemExit(f"{entry.get('id')}: no layer for disc {disc}")
	return (meta["builder_dir"] / str(rel).lstrip("./")).resolve()


def _apply_and_check(image: bytearray, layer_path: Path) -> int:
	layer = json.loads(layer_path.read_text(encoding="utf-8"))
	if layer.get("format") != "ic-layer-v1":
		raise SystemExit(f"{layer_path}: expected ic-layer-v1")
	records = layer.get("records") or []
	apply_layer(image, layer)
	# Confirm every record landed (builder success condition).
	for rec in records:
		off = int(rec["offset"])
		data = bytes.fromhex(rec["hex"])
		if bytes(image[off : off + len(data)]) != data:
			raise SystemExit(f"post-apply mismatch in {layer_path.name} @ {off:#x}")
	return len(records)


def main() -> int:
	ap = argparse.ArgumentParser(description="Verify builder base+addon stack on a pristine disc")
	ap.add_argument("--pristine", type=Path, required=True, help="Retail NTSC-U disc .bin")
	ap.add_argument("--disc", type=int, required=True, choices=(1, 2, 3))
	ap.add_argument(
		"--base",
		required=True,
		help="Base id: clean | csr-v… | highwind-v…",
	)
	ap.add_argument(
		"--addon",
		action="append",
		default=[],
		dest="addons",
		help="Addon pack id (repeatable), in apply order",
	)
	ap.add_argument(
		"--manifest",
		type=Path,
		default=_ROOT / "builder" / "manifest.json",
		help="Primary builder/manifest.json (default: this repo)",
	)
	ap.add_argument(
		"--extra-manifest",
		action="append",
		default=[],
		type=Path,
		help="Additional manifest(s) e.g. other repo builder/manifest.json",
	)
	ap.add_argument(
		"-o",
		"--output",
		type=Path,
		default=None,
		help="Optional write stacked image (gitignored temp)",
	)
	args = ap.parse_args()

	catalog: dict[str, dict] = {}
	for man in [args.manifest, *args.extra_manifest]:
		bdir, data = _load_manifest(man)
		catalog.update(_index_packs(bdir, data))

	base_id = args.base.strip()
	print(f"Config: base={base_id} addons={args.addons or []} disc={args.disc}")
	print(f"Pristine: {args.pristine}")

	image = bytearray(Path(args.pristine).expanduser().resolve().read_bytes())
	total_recs = 0
	stack: list[str] = []

	if base_id not in ("clean", "unmodified"):
		if base_id not in catalog:
			raise SystemExit(f"Unknown base id {base_id!r}. Known: {sorted(catalog)[:20]}…")
		meta = catalog[base_id]
		if meta["entry"].get("kind") not in (None, "base") and meta["kind"] != "base":
			# bases list entries usually kind=base
			pass
		lp = _layer_path(meta, args.disc)
		n = _apply_and_check(image, lp)
		total_recs += n
		stack.append(f"base:{base_id} ({lp.name}, {n} records)")
		print(f"  OK base {base_id} ← {lp.relative_to(meta['builder_dir'])} ({n} records)")
	else:
		stack.append("base:clean (pristine only)")
		print("  OK base clean (no base layer)")

	for addon_id in args.addons:
		if addon_id not in catalog:
			raise SystemExit(f"Unknown addon id {addon_id!r}")
		meta = catalog[addon_id]
		entry = meta["entry"]
		compat = entry.get("compatibleBases") or []
		if base_id in ("clean", "unmodified"):
			need = "clean"
		else:
			need = base_id
		if compat and need not in compat:
			raise SystemExit(
				f"{addon_id}: compatibleBases={compat} does not include base {need!r}"
			)
		lp = _layer_path(meta, args.disc)
		n = _apply_and_check(image, lp)
		total_recs += n
		stack.append(f"addon:{addon_id} ({lp.name}, {n} records)")
		print(f"  OK addon {addon_id} ← {lp.relative_to(meta['builder_dir'])} ({n} records)")

	if args.output:
		args.output.parent.mkdir(parents=True, exist_ok=True)
		args.output.write_bytes(image)
		print(f"Wrote {args.output} ({len(image)} bytes)")

	print("Stack:")
	for line in stack:
		print(f"  - {line}")
	print(f"PASS — builder config applies cleanly ({total_recs} total records)")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
