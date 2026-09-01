#!/usr/bin/env python3
"""Repair MODE2/2352 Form 1 footers using a pristine same-disc reference.

Before rebuilding ic-layer packs, run this on each edited FINALFANTASY7_DN.bin
so diffs do not bake zeroed footers into the layer JSON.

  python3 scripts/repair_mode2_edc.py \\
    pristine/FINALFANTASY7_D1.bin \\
    cache/csr/FINALFANTASY7_D1.bin \\
    -o cache/csr/FINALFANTASY7_D1.bin

Neill Corlett / ECM public-domain Mode2 Form1 algorithm (verified vs retail).

The input image must be sector-aligned and at least as long as pristine
(CSR+ and Highwind Disc 1 images grow past retail). Overlapping sectors
restore a known retail footer when user data is unchanged, and recompute
Form 1 EDC/P/Q when user data changed. Sectors past the pristine length
have no retail footer to copy, so Form 1 footers are recomputed there.
Form 2 sectors are left untouched. The pristine image is never overwritten;
``-o`` may point at the input image. Make a backup before overwriting an
edited BIN.
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
	"""Recognize the raw sync/mode envelope accepted by this repair pass."""
	if sec[0] != 0 or sec[11] != 0 or sec[15] != 2:
		return False
	has_sync = all(sec[i] == 0xFF for i in range(1, 11))
	is_form2 = bool(sec[18] & 0x20)
	return has_sync and not is_form2


def generate_mode2_form1_edc_ecc(sector: bytearray) -> None:
	"""Regenerate one 2352-byte Form 1 sector's EDC and P/Q parity."""
	edc = 0
	for b in sector[OFFSET_MODE2_SUBHEADER : OFFSET_MODE2_SUBHEADER + MODE2_EDC_LEN]:
		edc = (_edc[(edc ^ b) & 0xFF] ^ (edc >> 8)) & 0xFFFFFFFF
	sector[EDC_OFF : EDC_OFF + 4] = edc.to_bytes(4, "little")

	saved = bytes(sector[12:16])
	sector[12:16] = b"\x00\x00\x00\x00"

	def ecc_block(src: bytes, major_count, minor_count, major_mult, minor_inc) -> bytes:
		size = major_count * minor_count
		dest = bytearray(major_count * 2)
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
			dest[major] = a
			dest[major + major_count] = a ^ b
		return bytes(dest)

	# Freeze src windows so writing P does not disturb Q's input mid-pass.
	src_p = bytes(sector[12 : 12 + ECC_P_MAJOR * ECC_P_MINOR])
	sector[OFFSET_ECC_P : OFFSET_ECC_P + ECC_P_MAJOR * 2] = ecc_block(
		src_p, ECC_P_MAJOR, ECC_P_MINOR, ECC_P_MULT, ECC_P_INC
	)
	src_q = bytes(sector[12 : 12 + ECC_Q_MAJOR * ECC_Q_MINOR])
	sector[OFFSET_ECC_Q : OFFSET_ECC_Q + ECC_Q_MAJOR * 2] = ecc_block(
		src_q, ECC_Q_MAJOR, ECC_Q_MINOR, ECC_Q_MULT, ECC_Q_INC
	)
	sector[12:16] = saved


def _recompute_form1(sec_b: bytes | bytearray) -> bytearray | None:
	"""Return a Form 1 sector with a fresh footer, or None to leave it alone."""
	if not _is_mode2_form1(sec_b):
		return None
	sector = bytearray(sec_b)
	generate_mode2_form1_edc_ecc(sector)
	return sector


def repair(pristine: Path, inp: Path, out: Path) -> dict:
	"""Repair one image and return sector-count diagnostics."""
	p = pristine.read_bytes()
	b = bytearray(inp.read_bytes())
	if len(p) % SECTOR:
		raise SystemExit("pristine length not multiple of 2352")
	if len(b) % SECTOR:
		raise SystemExit("image length not multiple of 2352")
	if len(b) < len(p):
		raise SystemExit(f"input shorter than pristine: {len(b)} vs {len(p)}")

	nsect = len(b) // SECTOR
	pristine_sectors = len(p) // SECTOR
	restored = recomputed = already_ok = skipped = 0

	for lba in range(nsect):
		off = lba * SECTOR
		sec_b = b[off : off + SECTOR]

		if lba >= pristine_sectors:
			repaired = _recompute_form1(sec_b)
			if repaired is None:
				skipped += 1
				continue
			b[off : off + SECTOR] = repaired
			recomputed += 1
			continue

		sec_p = p[off : off + SECTOR]
		if sec_b == sec_p:
			already_ok += 1
			continue
		if not _is_mode2_form1(sec_b):
			skipped += 1
			continue

		pf = sec_p[EDC_OFF : EDC_OFF + FOOTER_LEN]
		bf = sec_b[EDC_OFF : EDC_OFF + FOOTER_LEN]
		if bf == pf:
			already_ok += 1
			continue

		pristine_edc_data = sec_p[OFFSET_MODE2_SUBHEADER:EDC_OFF]
		image_edc_data = sec_b[OFFSET_MODE2_SUBHEADER:EDC_OFF]
		edc_data_is_unchanged = pristine_edc_data == image_edc_data
		if edc_data_is_unchanged:
			b[off + EDC_OFF : off + EDC_OFF + FOOTER_LEN] = pf
			restored += 1
			continue

		repaired = _recompute_form1(sec_b)
		assert repaired is not None
		b[off : off + SECTOR] = repaired
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
	ap.add_argument("pristine", type=Path, help="Unmodified same-disc BIN")
	ap.add_argument("image", type=Path, help="Edited BIN to repair")
	ap.add_argument("-o", "--output", type=Path, required=True, help="Repaired BIN")
	args = ap.parse_args()
	stats = repair(
		args.pristine.expanduser(),
		args.image.expanduser(),
		args.output.expanduser(),
	)
	for k, v in stats.items():
		print(f"{k}: {v}")


if __name__ == "__main__":
	main()
