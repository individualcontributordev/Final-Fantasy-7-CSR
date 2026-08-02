# ImgBurn verify miscompare on CSR+ Disc 1 burn

**Date:** 2026-07-27  
**Confidence:** confirmed  
**Status:** closed — disc plays on PS2 despite verify fail  
**Related:** `notes/Capture.PNG`, `scripts/repair_mode2_edc.py`

## Summary

Burn of `ff7-builder-d1+csr-plus-v0.1.1` failed ImgBurn verify at LBA **614** / `\INIT\YAMADA.BIN` / offset **2072**. **Same CD-R boots and loads fine on PS2 Slim 77003 (MechaPwn).**

## Verified (pristine vs builder bin)

| | LBA 614 @ offset 2072 (EDC) | User data vs pristine |
|--|------------------------------|------------------------|
| Pristine | `cca1b464` | — |
| Builder output | `00000000` (footer zeroed) | **identical** |
| ImgBurn dialog | Device `0xCC` / Image `0x00` | matches exactly |

Cause: CSR+ layer includes EDC/ECC zeroing (workspace image used for diff had zeroed footers). ~2933 footer-only sectors; ~1514 with real CSR user-data changes.

## Hardware result

- Console: PS2 Slim 77003 + MechaPwn  
- Disc: original ImgBurn burn (verify error, **not** the edc-fixed reburn)  
- Result: **loads fine**

Likely the burner/drive wrote usable sectors (or regenerated checksums on write) even though the source image footers were zero — ImgBurn verify compares against the zeroed image and complains.

## Practical rule

1. ImgBurn verify fail at offset **2072** with image `0x00` vs device `0xCC` → try the disc on PS2 before reburning.
2. Still prefer fixing layers long-term (`repair_mode2_edc.py` / rebuild layers with valid EDC) so verifies pass and picky drives/media are safer.
3. `repair_mode2_edc.py` remains useful when a burn *doesn't* boot or when you want clean verifies.

## Builder fix (2026-07-27)

Homepage builder regenerates Mode2 Form1 EDC/ECC for every sector changed by layers (`builder/edc.js`). Re-download from https://individualcontributor.dev/builder/ for a verify-clean burn.

## Hardware confirm (2026-07-27)

Fresh builder zip (post-EDC repair) burned and tested on **PS2 Slim 77003 + MechaPwn**:

- Disc loads
- Fields load
- **Later same day:** latest CSR+ burn successful — plays on console

Treat builder EDC repair + 4x DAO burn as the working ship path for CSR+ Disc 1.
