#!/usr/bin/env python3
"""Build a jump/gateway graph among changed FIELD maps.

  python scripts/field_jump_graph.py \\
    --image cache/csr/FINALFANTASY7_D1.bin \\
    --changed temp/csr-field-diff.json \\
    -o temp/csr-field-graph.json
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from collections import defaultdict
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
	sys.path.insert(0, str(_SCRIPTS))

from field_maplist import MAPLIST, stem_for_field_id  # noqa: E402
from lzs import decompress_all_with_header  # noqa: E402
from psx_mode2_iso import extract_file  # noqa: E402

# PSX DAT section index for triggers/gateways (wiki Field Module).
TRIGGERS_SECTION = 4
GATEWAY_COUNT = 12
GATEWAY_STRIDE = 24
GATEWAY_FIELD_ID_OFF = 18
TRIGGERS_GATEWAYS_OFF = 56
MAPJUMP_OPCODE = 0x60
INVALID_FIELD = 0x7FFF


def dat_section_offsets(dec: bytes) -> list[int]:
	if len(dec) < 28:
		raise ValueError("DAT too small for section table")
	ptrs = struct.unpack_from("<7I", dec, 0)
	base = ptrs[0]
	return [p - base + 28 for p in ptrs]


def parse_gateway_destinations(dec: bytes) -> list[int]:
	offs = dat_section_offsets(dec)
	trig = offs[TRIGGERS_SECTION]
	if trig < 0 or trig + TRIGGERS_GATEWAYS_OFF + GATEWAY_COUNT * GATEWAY_STRIDE > len(dec):
		return []
	dests: list[int] = []
	base = trig + TRIGGERS_GATEWAYS_OFF
	for i in range(GATEWAY_COUNT):
		off = base + i * GATEWAY_STRIDE
		(field_id,) = struct.unpack_from("<H", dec, off + GATEWAY_FIELD_ID_OFF)
		if field_id != INVALID_FIELD and field_id < len(MAPLIST):
			dests.append(field_id)
	return dests


def scan_mapjump_destinations(dec: bytes) -> list[int]:
	"""Heuristic scan of script section for MAPJUMP (0x60) + u16 field id."""
	offs = dat_section_offsets(dec)
	script_off = offs[0]
	# Script runs until walkmesh (section 1)
	end = offs[1] if len(offs) > 1 else len(dec)
	if script_off < 0 or end > len(dec) or script_off >= end:
		return []
	blob = dec[script_off:end]
	dests: list[int] = []
	i = 0
	while i + 3 <= len(blob):
		if blob[i] == MAPJUMP_OPCODE:
			(field_id,) = struct.unpack_from("<H", blob, i + 1)
			if field_id < len(MAPLIST) and MAPLIST[field_id]:
				dests.append(field_id)
			i += 10  # opcode + mapID + x + y + z + dir (approx MAPJUMP size)
			continue
		i += 1
	return dests


def connected_components(nodes: set[str], edges: list[tuple[str, str]]) -> list[list[str]]:
	adj: dict[str, set[str]] = defaultdict(set)
	for a, b in edges:
		if a in nodes and b in nodes and a != b:
			adj[a].add(b)
			adj[b].add(a)
	seen: set[str] = set()
	comps: list[list[str]] = []
	for n in sorted(nodes):
		if n in seen:
			continue
		stack = [n]
		comp: list[str] = []
		seen.add(n)
		while stack:
			cur = stack.pop()
			comp.append(cur)
			for nxt in sorted(adj[cur]):
				if nxt not in seen:
					seen.add(nxt)
					stack.append(nxt)
		comps.append(sorted(comp))
	comps.sort(key=lambda c: (-len(c), c[0]))
	return comps


def build_graph(image: bytes, changed: dict) -> dict:
	stems = {m["stem"].upper() for m in changed["maps"]}
	edges: list[dict] = []
	edge_set: set[tuple[str, str]] = set()
	errors: list[dict] = []

	for m in changed["maps"]:
		stem = m["stem"].upper()
		dat_path = next((p for p in m["files"] if p.upper().endswith(".DAT")), None)
		if not dat_path:
			continue
		try:
			raw = extract_file(image, dat_path)
			dec = decompress_all_with_header(raw)
		except Exception as exc:  # noqa: BLE001 — collect and continue
			errors.append({"stem": stem, "error": str(exc)})
			continue

		for field_id in parse_gateway_destinations(dec) + scan_mapjump_destinations(dec):
			dest = stem_for_field_id(field_id)
			if not dest or dest not in stems:
				continue
			key = (stem, dest)
			if key in edge_set:
				continue
			edge_set.add(key)
			edges.append({"from": stem, "to": dest, "fieldId": field_id})

	undirected = [(e["from"], e["to"]) for e in edges]
	comps = connected_components(stems, undirected)
	return {
		"flavor": changed.get("flavor"),
		"nodeCount": len(stems),
		"edgeCount": len(edges),
		"edges": edges,
		"components": [{"stems": c, "size": len(c)} for c in comps],
		"errors": errors,
	}


def main() -> int:
	ap = argparse.ArgumentParser(description="Gateway/MAPJUMP graph for changed maps")
	ap.add_argument("--image", type=Path, required=True, help="Patched Disc .bin")
	ap.add_argument("--changed", type=Path, required=True, help="list_changed_field_maps JSON")
	ap.add_argument("-o", "--output", type=Path, required=True)
	args = ap.parse_args()

	changed = json.loads(args.changed.read_text(encoding="utf-8"))
	image = args.image.read_bytes()
	result = build_graph(image, changed)
	args.output.parent.mkdir(parents=True, exist_ok=True)
	args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
	print(
		f"Wrote {args.output}: {result['nodeCount']} nodes, "
		f"{result['edgeCount']} edges, {len(result['components'])} components"
	)
	if result["errors"]:
		print(f"  ({len(result['errors'])} DAT parse errors)", file=sys.stderr)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
