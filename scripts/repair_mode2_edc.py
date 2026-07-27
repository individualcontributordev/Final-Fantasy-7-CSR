#!/usr/bin/env python3
"""Repair MODE2/2352 Form-1 sector footers after ic-layer apply.

CSR working images often zero EDC/ECC (Makou/ff7tk/CDmage inject). Diff→layer
ships those zeros; browser apply onto a good rip zeros footers. ImgBurn then
reports miscompare at offset 2072 (image 0x00 vs drive 0xCC).

This restores footers from pristine wherever **user data still matches**.
Sectors where CSR actually changed the 2048-byte payload keep needing a full
EDC/ECC recompute (follow-up) — but footer-only damage (e.g. LBA 614 YAMADA)
is fixed here.

  python3 scripts/repair_mode2_edc.py \\
    --pristine workspace/pristine/'Final Fantasy VII (Disc 1).bin' \\
    --input ~/Downloads/ff7-builder-d1+csr-plus-v0.1.1/ff7-builder-d1+csr-plus-v0.1.1.bin \\
    --output ~/Downloads/ff7-builder-d1+csr-plus-v0.1.1/ff7-d1-csr-plus-edc-fixed.bin
"""

from __future__ import annotations

import argparse
from pathlib import Path

SECTOR = 2352
USER_OFF = 24
USER = 2048
EDC_OFF = 2072
FOOTER_LEN = 280


def repair(pristine: Path, inp: Path, out: Path) -> dict:
	p = pristine.read_bytes()
	b = bytearray(inp.read_bytes())
	if len(p) != len(b):
		raise SystemExit(f"size mismatch: pristine {len(p)} vs input {len(b)}")
	if len(b) % SECTOR:
		raise SystemExit("image length not multiple of 2352")

	nsect = len(b) // SECTOR
	restored = already_ok = user_changed_bad = 0

	for lba in range(nsect):
		off = lba * SECTOR
		pu = p[off + USER_OFF : off + USER_OFF + USER]
		bu = b[off + USER_OFF : off + USER_OFF + USER]
		pf = p[off + EDC_OFF : off + EDC_OFF + FOOTER_LEN]
		bf = b[off + EDC_OFF : off + EDC_OFF + FOOTER_LEN]

		if bf == pf:
			already_ok += 1
			continue
		if pu == bu:
			b[off + EDC_OFF : off + EDC_OFF + FOOTER_LEN] = pf
			restored += 1
		else:
			user_changed_bad += 1

	out.parent.mkdir(parents=True, exist_ok=True)
	out.write_bytes(b)
	return {
		"sectors": nsect,
		"footer_already_ok": already_ok,
		"footer_restored_from_pristine": restored,
		"user_changed_still_bad_footer": user_changed_bad,
		"output": str(out),
	}


def main() -> None:
	ap = argparse.ArgumentParser(
		description="Restore MODE2 Form1 footers from pristine where user data matches"
	)
	ap.add_argument("--pristine", type=Path, required=True)
	ap.add_argument("--input", type=Path, required=True)
	ap.add_argument("--output", type=Path, required=True)
	args = ap.parse_args()
	stats = repair(args.pristine.expanduser(), args.input.expanduser(), args.output.expanduser())
	for k, v in stats.items():
		print(f"{k}: {v}")
	print(
		"\nFixed footer-only damage (includes ImgBurn LBA 614 / YAMADA). "
		"Remaining user-changed sectors still have bad footers — try this image "
		"on PS2; add full ECC recompute later if those sectors mis-read."
	)


if __name__ == "__main__":
	main()
