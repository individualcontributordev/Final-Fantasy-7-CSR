# ImgBurn verify miscompare on CSR+ Disc 1 burn

**Date:** 2026-07-27  
**Confidence:** likely  
**Status:** open  
**Related:** [docs/07-hardware-burn.md](../07-hardware-burn.md), `notes/Capture.PNG`

## Summary

Burn of builder zip `ff7-builder-d1+csr-plus-v0.1.1` completed; **ImgBurn verify failed** at LBA **614**, file `\INIT\YAMADA.BIN`.

## Evidence (screenshot)

- Source: `…\ff7-builder-d1+csr-plus-v0.1.1.cue` (MODE2/FORM1/2352, 317787 sectors)
- Drive: TSSTcorp CDDVDW SH-222AB
- Dialog: Miscompare at LBA 614, **Offset 2072**
  - Device byte: `0xCC`
  - Image byte: `0x00`
  - Total errors in sector: 192

## Interpretation

In a MODE2/2352 sector, user data is bytes **24–2071**. Offset **2072** is the start of the **EDC** (checksum footer), not the `YAMADA.BIN` payload.

So verify is complaining about **sector EDC/ECC**, with the **image containing `0x00`** at that footer byte. That matches the known pipeline risk: tools often rewrite Form 1 user data and leave or zero footers; drives/ImgBurn then disagree on verify even when the 2048-byte payload may be fine.

`YAMADA.BIN` is an early INIT file — unlikely to be a CSR+-specific patch target; this may be image-wide EDC health or drive verify quirk.

## Next tests

1. **Try the burned disc on PS2 MechaPwn anyway** (user data may still be good).
2. If console fails: reburn at **4x DAO** on better media; do not use MAX write speed.
3. If still failing: rebuild EDC/ECC on the `.bin` before burn (CDmage / Mode2 repair) and document which tool worked.
4. Optional: hex-check source `.bin` at `LBA*2352+2072` — expect non-zero EDC on a clean Redump-style rip.

## Follow-ups

- [ ] PS2 boot result for this disc
- [ ] Confirm ImgBurn write speed used
- [ ] If needed, add EDC repair step to builder/burn docs
