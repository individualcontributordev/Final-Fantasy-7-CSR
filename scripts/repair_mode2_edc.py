#!/usr/bin/env python3
"""Repair MODE2/2352 Form-1 EDC/ECC on a patched CSR working image.

Before rebuilding ic-layer packs, run this on each workspace/<base>/FINALFANTASY7_DN.bin
so diffs do not bake zeroed footers into the layer JSON.

  # restore unchanged footers from pristine + recompute ECC where user data changed
  python3 scripts/repair_mode2_edc.py \\
    --pristine workspace/pristine/FINALFANTASY7_D1.bin \\
    --input workspace/csr-plus/FINALFANTASY7_D1.bin \\
    --output workspace/csr-plus/FINALFANTASY7_D1.bin --in-place

Neill Corlett / ECM public-domain Mode2 Form1 algorithm (verified vs retail).
"""

from __future__ import annotations

import argparse
from pathlib import Path

SECTOR = 2352
USER_OFF = 24
USER = 2048
EDC_OFF = 2072
FOOTER_LEN = 280
OFFSET_MODE2_SUBHEADER = 0x10
MODE2_EDC_LEN = 0x808
OFFSET_ECC_P = 0x81C
OFFSET_ECC_Q = 0x8C8
ECC_DATA_OFFSET = 0x0C

ECC_P_MAJOR, ECC_P_MINOR, ECC_P_MULT, ECC_P_INC = 86, 24, 2, 86
ECC_Q_MAJOR, ECC_Q_MINOR, ECC_Q_MULT, ECC_Q_INC = 52, 43, 86, 88

_ecc_f = [0] * 256
_ecc_b = [0] * 256
_edc = [0] * 256
for _i in range(256):
	_j = (_i << 1) ^ (0x11D if (_i & 0x80) else 0)
	_ecc_f[_i] = _j & 0xFF
	_ecc_b[_i ^ _j] = _i
	_edc_v = _i
	for _ in range(8):
		_edc_v = (_edc_v >> 1) ^ (0xD8018001 if (_edc_v & 1) else 0)
	_edc[_i] = _edc_v & 0xFFFFFFFF


def _is_mode2_form1(sec: bytes | bytearray) -> bool:
	if sec[0] != 0 or sec[11] != 0 or sec[15] != 2:
		return False
	return all(sec[i] == 0xFF for i in range(1, 11))


def generate_mode2_form1_edc_ecc(sector: bytearray) -> None:
	edc = 0
	for b in sector[OFFSET_MODE2_SUBHEADER : OFFSET_MODE2_SUBHEADER + MODE2_EDC_LEN]:
		edc = (_edc[(edc ^ b) & 0xFF] ^ (edc >> 8)) & 0xFFFFFFFF
	sector[EDC_OFF : EDC_OFF + 4] = edc.to_bytes(4, "little")

	saved = bytes(sector[12:16])
	sector[12:16] = b"\x00\x00\x00\x00"
	src = sector[ECC_DATA_OFFSET:]

	def ecc_block(major_count, minor_count, major_mult, minor_inc, dest_off):
		size = major_count * minor_count
		for major in range(major_count):
			index = (major >> 1) * major_mult + (major & 1)
			a = b = 0
			for _ in range(minor_count):
				t = src[index]
				index += minor_inc
				if index >= size:
					index -= size
				a ^= t
				b ^= t
				a = _ecc_f[a]
			a = _ecc_b[_ecc_f[a] ^ b]
			sector[dest_off + major] = a
			sector[dest_off + major + major_count] = a ^ b

	ecc_block(ECC_P_MAJOR, ECC_P_MINOR, ECC_P_MULT, ECC_P_INC, OFFSET_ECC_P)
	ecc_block(ECC_Q_MAJOR, ECC_Q_MINOR, ECC_Q_MULT, ECC_Q_INC, OFFSET_ECC_Q)
	sector[12:16] = saved


def repair(pristine: Path, inp: Path, out: Path) -> dict:
	p = pristine.read_bytes()
	b = bytearray(inp.read_bytes())
	if len(p) != len(b):
		raise SystemExit(f"size mismatch: pristine {len(p)} vs input {len(b)}")
	if len(b) % SECTOR:
		raise SystemExit("image length not multiple of 2352")

	nsect = len(b) // SECTOR
	restored = recomputed = already_ok = skipped = 0

	for lba in range(nsect):
		off = lba * SECTOR
		sec_p = p[off : off + SECTOR]
		sec_b = b[off : off + SECTOR]
		pu = sec_p[USER_OFF : USER_OFF + USER]
		bu = sec_b[USER_OFF : USER_OFF + USER]
		pf = sec_p[EDC_OFF : EDC_OFF + FOOTER_LEN]
		bf = sec_b[EDC_OFF : EDC_OFF + FOOTER_LEN]

		if bf == pf:
			already_ok += 1
			continue

		if pu == bu:
			b[off + EDC_OFF : off + EDC_OFF + FOOTER_LEN] = pf
			restored += 1
			continue

		if not _is_mode2_form1(sec_b):
			skipped += 1
			continue

		sector = bytearray(sec_b)
		generate_mode2_form1_edc_ecc(sector)
		b[off : off + SECTOR] = sector
		recomputed += 1

	out.parent.mkdir(parents=True, exist_ok=True)
	out.write_bytes(b)
	return {
		"sectors": nsect,
		"footer_already_ok": already_ok,
		"footer_restored_from_pristine": restored,
		"footer_recomputed": recomputed,
		"non_form1_left_alone": skipped,
		"output": str(out),
	}


def main() -> None:
	ap = argparse.ArgumentParser(
		description="Fix MODE2 Form1 EDC/ECC on a patched image before layer rebuild"
	)
	ap.add_argument("--pristine", type=Path, required=True)
	ap.add_argument("--input", type=Path, required=True)
	ap.add_argument("--output", type=Path, default=None, help="Output path (default: --in-place)")
	ap.add_argument(
		"--in-place",
		action="store_true",
		help="Overwrite --input (backup first if unsure)",
	)
	args = ap.parse_args()
	out = args.input if args.in_place else args.output
	if out is None:
		raise SystemExit("Pass --output PATH or --in-place")
	stats = repair(args.pristine.expanduser(), args.input.expanduser(), out.expanduser())
	for k, v in stats.items():
		print(f"{k}: {v}")


if __name__ == "__main__":
	main()
