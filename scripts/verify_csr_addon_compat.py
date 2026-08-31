#!/usr/bin/env python3
"""Regression matrix: every live CSR base x every enabled CSR+ scene add-on.

Policy (AGENTS.md):
  CSR+ scene add-ons must work on **all** enabled csr-v* bases. If a CSR base
  release breaks an add-on, fix the base or the add-on — do not leave packs
  that only list an older base id without verifying the stack.

  python3 scripts/verify_csr_addon_compat.py
  python3 scripts/verify_csr_addon_compat.py --disc 2
  python3 scripts/verify_csr_addon_compat.py --base csr --addon csr-plus-scene-aerith-house

Exit 0 only if every required (base, addon, disc) stack applies cleanly and
each add-on's compatibleBases includes every live CSR base id.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_ROOT = _SCRIPTS.parent
if str(_SCRIPTS) not in sys.path:
	sys.path.insert(0, str(_SCRIPTS))

from local_paths import default_pristine_arg, ensure_cached_base  # noqa: E402
from verify_builder_config import (  # noqa: E402
	_apply_and_check,
	_check_records,
	_index_packs,
	_layer_path,
	_load_manifest,
)


def _enabled(entry: dict) -> bool:
	return entry.get("enabled") is not False


def _live_csr_base_ids(catalog: dict[str, dict]) -> list[str]:
	out = []
	for pid, meta in catalog.items():
		if meta.get("kind") != "base":
			continue
		if not str(pid).startswith("csr-v"):
			continue
		if not _enabled(meta["entry"]):
			continue
		out.append(pid)
	return sorted(out)


def _csr_scene_addon_ids(catalog: dict[str, dict]) -> list[str]:
	"""Enabled add-ons that target CSR (by id or compatibleBases)."""
	out = []
	for pid, meta in catalog.items():
		if meta.get("kind") != "addon":
			continue
		if not _enabled(meta["entry"]):
			continue
		entry = meta["entry"]
		compat = entry.get("compatibleBases") or []
		is_scene = str(pid).startswith("csr-plus-scene-")
		targets_csr = any(str(c).startswith("csr-v") or c == "csr" for c in compat)
		if is_scene or targets_csr:
			out.append(pid)
	return sorted(out)


def main() -> int:
	ap = argparse.ArgumentParser(description="CSR base x scene-addon regression matrix")
	ap.add_argument("--base", action="append", default=[], dest="bases", help="Limit to base id(s)")
	ap.add_argument("--addon", action="append", default=[], dest="addons", help="Limit to addon id(s)")
	ap.add_argument("--disc", type=int, choices=(1, 2, 3), default=None, help="Limit to one disc")
	ap.add_argument(
		"--manifest",
		type=Path,
		default=_ROOT / "builder" / "manifest.json",
	)
	ap.add_argument(
		"--allow-compat-gap",
		action="store_true",
		help="Do not fail when compatibleBases omits a live CSR base (still apply-test listed bases)",
	)
	args = ap.parse_args()

	bdir, data = _load_manifest(args.manifest)
	catalog = _index_packs(bdir, data)

	csr_bases = _live_csr_base_ids(catalog)
	addons = _csr_scene_addon_ids(catalog)
	if args.bases:
		csr_bases = [b for b in csr_bases if b in args.bases]
	if args.addons:
		addons = [a for a in addons if a in args.addons]

	if not csr_bases:
		raise SystemExit("No live csr-v* bases found in manifest")
	if not addons:
		print("No enabled CSR scene add-ons — nothing to check")
		return 0

	print(f"CSR bases: {csr_bases}")
	print(f"Add-ons:   {addons}")
	print()

	failed = False
	checked = 0

	for addon_id in addons:
		meta = catalog[addon_id]
		entry = meta["entry"]
		compat = list(entry.get("compatibleBases") or [])
		discs_map = entry.get("discs") or {}
		disc_nums = sorted(int(d) for d in discs_map if str(d) in ("1", "2", "3"))
		if args.disc is not None:
			disc_nums = [d for d in disc_nums if d == args.disc]
		if not disc_nums:
			print(f"SKIP {addon_id}: no discs to check")
			continue

		missing = [b for b in csr_bases if b not in compat]
		if missing and not args.allow_compat_gap:
			print(
				f"FAIL {addon_id}: compatibleBases={compat} "
				f"missing live CSR bases {missing}"
			)
			print("      Every enabled csr-v* base must be listed (or retire the add-on).")
			failed = True
		# Always apply-test against every live CSR base (regression), not only listed ones.
		bases_to_test = list(csr_bases)

		for base_id in bases_to_test:
			for disc in disc_nums:
				label = f"{base_id} + {addon_id} disc {disc}"
				pristine = default_pristine_arg(disc)
				if not pristine.is_file():
					print(f"FAIL {label}: missing pristine {pristine}")
					failed = True
					continue
				try:
					base_meta = catalog[base_id]
					base_lp = _layer_path(base_meta, disc)
					base_bytes, _ = ensure_cached_base(
						base_id=base_id,
						disc=disc,
						layer_path=base_lp,
						pristine=pristine,
						write_cache=True,
					)
					image = bytearray(base_bytes)
					_check_records(image, base_lp)
					addon_lp = _layer_path(meta, disc)
					n = _apply_and_check(image, addon_lp)
				except SystemExit as exc:
					print(f"FAIL {label}: {exc}")
					failed = True
					continue
				except Exception as exc:
					print(f"FAIL {label}: {exc}")
					failed = True
					continue
				checked += 1
				print(f"  OK {label} ({n} addon records)")

	print()
	if failed:
		print(f"FAIL — CSR addon compat ({checked} stacks OK, see FAIL lines)")
		return 1
	print(f"PASS — {checked} stacks OK (all live CSR bases x enabled scene add-ons)")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
