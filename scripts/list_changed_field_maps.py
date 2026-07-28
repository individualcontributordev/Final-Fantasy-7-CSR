#!/usr/bin/env python3
"""List FIELD/* files that differ between pristine and a patched Disc image.

  python scripts/list_changed_field_maps.py \\
    --pristine workspace/pristine/FINALFANTASY7_D1.bin \\
    --patched workspace/csr/FINALFANTASY7_D1.bin \\
    --flavor csr -o workspace/csr-field-diff.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
	sys.path.insert(0, str(_SCRIPTS))

from psx_mode2_iso import extract_file, list_dir  # noqa: E402

SKIP_NAMES = {"FIELD.BIN"}


def _sha16(blob: bytes) -> str:
	return hashlib.sha256(blob).hexdigest()[:16]


def list_changed(
	pristine: bytes,
	patched: bytes,
	*,
	flavor: str,
) -> dict:
	by_stem: dict[str, list[dict]] = defaultdict(list)
	pr_files = {f.path: f for f in list_dir(pristine, "FIELD")}

	for meta in list_dir(patched, "FIELD"):
		name = meta.path.rsplit("/", 1)[-1]
		if name in SKIP_NAMES:
			continue
		stem, _, ext = name.partition(".")
		if not ext:
			continue
		pr_meta = pr_files.get(meta.path)
		if pr_meta is None:
			by_stem[stem].append(
				{
					"path": meta.path,
					"status": "added",
					"pristineSize": None,
					"patchedSize": meta.size,
					"pristineSha": None,
					"patchedSha": _sha16(extract_file(patched, meta.path)),
				}
			)
			continue
		pr_bytes = extract_file(pristine, meta.path)
		pt_bytes = extract_file(patched, meta.path)
		if pr_bytes == pt_bytes:
			continue
		by_stem[stem].append(
			{
				"path": meta.path,
				"status": "changed",
				"pristineSize": len(pr_bytes),
				"patchedSize": len(pt_bytes),
				"sizeDelta": len(pt_bytes) - len(pr_bytes),
				"pristineSha": _sha16(pr_bytes),
				"patchedSha": _sha16(pt_bytes),
			}
		)

	maps = []
	for stem in sorted(by_stem):
		files = by_stem[stem]
		maps.append(
			{
				"stem": stem,
				"files": [f["path"] for f in files],
				"flavor": flavor,
				"entries": files,
			}
		)

	return {
		"flavor": flavor,
		"mapCount": len(maps),
		"fileCount": sum(len(m["files"]) for m in maps),
		"maps": maps,
	}


def main() -> int:
	ap = argparse.ArgumentParser(description="Diff FIELD maps between two Disc images")
	ap.add_argument("--pristine", type=Path, required=True)
	ap.add_argument("--patched", type=Path, required=True)
	ap.add_argument("--flavor", required=True, help="Label e.g. csr / csr-plus")
	ap.add_argument("-o", "--output", type=Path, required=True)
	args = ap.parse_args()

	pristine = args.pristine.read_bytes()
	patched = args.patched.read_bytes()
	result = list_changed(pristine, patched, flavor=args.flavor)
	args.output.parent.mkdir(parents=True, exist_ok=True)
	args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
	print(
		f"Wrote {args.output}: {result['mapCount']} maps, "
		f"{result['fileCount']} files ({args.flavor})"
	)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
