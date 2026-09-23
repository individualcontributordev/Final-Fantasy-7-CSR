#!/usr/bin/env python3
"""Force SCUS_941.63 to always require / accept Disc 1 (single-disc bases).

CSR+ and Highwind already collapse field/movie disc changes onto Disc 1, but
the main executable still compares the save's required-disc byte against
\\MINT\\DISKINFO.CNF after a reset+load. This patches those compares so a
Disc 2/3 save never prompts for another disc.

  python scripts/patch_force_disc1.py cache/csr-plus/FINALFANTASY7_D1.bin
  python scripts/patch_force_disc1.py cache/highwind/FINALFANTASY7_D1.bin \\
      --pristine pristine/FINALFANTASY7_D1.BIN

ISO helpers come from the sibling Final-Fantasy-7-Modding repo (or
FF7_MODDING_ROOT). After patching, repair footers and republish the base layer
so pristine + disc1.layer.json includes these bytes.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _modding_scripts() -> Path:
	env = os.environ.get("FF7_MODDING_ROOT")
	if env:
		path = Path(env).expanduser().resolve() / "scripts"
	else:
		path = ROOT.parent / "Final-Fantasy-7-Modding" / "scripts"
	if not (path / "psx_mode2_iso.py").is_file():
		raise SystemExit(
			f"Missing psx_mode2_iso.py under {path}. "
			"Clone Final-Fantasy-7-Modding next to this repo, or set FF7_MODDING_ROOT."
		)
	return path


_MODDING = _modding_scripts()
if str(_MODDING) not in sys.path:
	sys.path.insert(0, str(_MODDING))
if str(ROOT / "scripts") not in sys.path:
	sys.path.insert(0, str(ROOT / "scripts"))

from psx_mode2_iso import extract_file, find_file, replace_file_padded  # noqa: E402
from repair_mode2_edc import repair  # noqa: E402

SCUS_PATH = "SCUS_941.63"
# PS-EXE: code at file 0x800 maps to RAM 0x80010000.
EXE_LOAD = 0x80010000
EXE_HDR = 0x800

# (file_offset, expected_or_already_patched, new_bytes, label)
# expected accepts vanilla or already-patched so re-runs are safe.
PATCHES: list[tuple[int, tuple[bytes, ...], bytes, str]] = [
	# Site A: after title/load — force required disc = 1, then always match.
	(
		0x25CC,
		(bytes.fromhex("0000d092"), bytes.fromhex("01001034")),
		bytes.fromhex("01001034"),
		"siteA lbu->ori s0,1",
	),
	(
		0x25D4,
		(bytes.fromhex("ff001032"), bytes.fromhex("0000d0a2")),
		bytes.fromhex("0000d0a2"),
		"siteA andi->sb s0,DAT_8009d588",
	),
	(
		0x25D8,
		(bytes.fromhex("0c000212"), bytes.fromhex("0c000010")),
		bytes.fromhex("0c000010"),
		"siteA beq s0,v0 -> beq zero,zero",
	),
	# Site B: mode 0xB second gate (branch offset differs from site A).
	(
		0x2C88,
		(bytes.fromhex("0000d092"), bytes.fromhex("01001034")),
		bytes.fromhex("01001034"),
		"siteB lbu->ori s0,1",
	),
	(
		0x2C90,
		(bytes.fromhex("ff001032"), bytes.fromhex("0000d0a2")),
		bytes.fromhex("0000d0a2"),
		"siteB andi->sb s0,DAT_8009d588",
	),
	(
		0x2C94,
		(bytes.fromhex("10000212"), bytes.fromhex("10000010")),
		bytes.fromhex("10000010"),
		"siteB beq s0,v0 -> beq zero,zero",
	),
	# FUN_80034350: always report inserted disc = 1 from DISKINFO parse.
	(
		0x24BDC,
		(bytes.fromhex("d0ff4224"), bytes.fromhex("01000234")),
		bytes.fromhex("01000234"),
		"DISKINFO parse -> ori v0,1",
	),
]


def _file_off(ram: int) -> int:
	return EXE_HDR + (ram - EXE_LOAD)


def patch_scus(scus: bytes) -> bytes:
	"""Return SCUS_941.63 with force-disc-1 instruction patches."""
	if scus[:8] != b"PS-X EXE":
		raise SystemExit(f"{SCUS_PATH}: missing PS-X EXE header ({scus[:8]!r})")
	data = bytearray(scus)
	for offset, accepted, new, label in PATCHES:
		got = bytes(data[offset : offset + 4])
		if got not in accepted:
			raise SystemExit(
				f"{label} @ 0x{offset:X}: found {got.hex()}, "
				f"expected one of {', '.join(a.hex() for a in accepted)}"
			)
		if got != new:
			data[offset : offset + 4] = new
			print(f"  {label} @ 0x{offset:X}: {got.hex()} -> {new.hex()}")
		else:
			print(f"  {label} @ 0x{offset:X}: already patched")
	return bytes(data)


def verify_scus(scus: bytes) -> None:
	"""Require every patch site to hold the force-disc-1 bytes."""
	for offset, _accepted, new, label in PATCHES:
		got = scus[offset : offset + 4]
		if got != new:
			raise SystemExit(
				f"verify failed: {label} @ 0x{offset:X} is {got.hex()}, want {new.hex()}"
			)
	print(f"  verified: {len(PATCHES)} sites in {SCUS_PATH}")


def main() -> int:
	ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
	ap.add_argument("image", type=Path, help="Disc 1 BIN (MODE2/2352)")
	ap.add_argument(
		"-o",
		"--output",
		type=Path,
		default=None,
		help="Output BIN (default: overwrite input)",
	)
	ap.add_argument(
		"--pristine",
		type=Path,
		default=None,
		help="Unmodified Disc 1 BIN; repairs MODE2 Form 1 footers when given",
	)
	args = ap.parse_args()

	image_path = args.image.expanduser()
	out_path = (args.output or image_path).expanduser()

	image = bytearray(image_path.read_bytes())
	print(f"read {image_path} ({len(image)} bytes)")

	meta = find_file(image, SCUS_PATH)
	print(f"=== {SCUS_PATH}: LBA {meta.lba}, {meta.size} bytes ===")
	patched = patch_scus(extract_file(image, SCUS_PATH))
	replace_file_padded(image, SCUS_PATH, patched)

	out_path.parent.mkdir(parents=True, exist_ok=True)
	out_path.write_bytes(bytes(image))
	print(f"wrote {out_path}")

	if args.pristine is not None:
		print("=== repair MODE2 Form 1 footers ===")
		stats = repair(args.pristine.expanduser(), out_path, out_path)
		for key, value in stats.items():
			print(f"  {key}: {value}")

	print("=== verify ===")
	verify_scus(extract_file(out_path.read_bytes(), SCUS_PATH))
	meta2 = find_file(out_path.read_bytes(), SCUS_PATH)
	if meta2.lba != meta.lba:
		raise SystemExit(f"{SCUS_PATH} moved from LBA {meta.lba} to {meta2.lba}")
	print(f"  {SCUS_PATH} still at LBA {meta2.lba}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
