# Mixable per-field CSR packs (prototype)

**Date:** 2026-07-28  
**Confidence:** confirmed (tooling + layer stack); playtest pending human DuckStation  

## Goal

Ship cutscene edits as **builder add-ons** (not only monolithic CSR bases) so a player can stack Unmodified + selected scene packs + Field encounter.

## What shipped

| Pack | Maps | Source | Records / bytes |
|------|------|--------|-----------------|
| `csr-scene-boat-v0.1.0` | `SHIP_1`, `SHIP_2` | CSR Disc1 | 737 / ~30KB |
| `csr-scene-midgar-start-v0.1.0` | `MD1STIN`, `MD1_1` | CSR Disc1 | 954 / ~33KB |
| `csr-scene-del1-shpin3-v0.1.0` | `DEL1`, `SHPIN_3` | CSR Disc1 | 1051 / ~35KB |
| `csr-scene-mds7st1-v0.1.0` | `MDS7ST1` | CSR Disc1 | 309 / ~15KB |
| `csr-scene-nivl3-v0.1.0` | `NIVL_3` (Nibelheim) | CSR Disc1 | 583 / ~15KB |
| `csr-scene-rcktin7-v0.1.0` | `RCKTIN7` (Rocket Town) | CSR Disc1 | 555 / ~12KB |

- `compatibleBases: ["clean"]`
- Separate `exclusiveGroup` per scene
- Layer byte ranges: **no overlap** across all six packs (full pairwise check)
- Programmatic stack apply: injected `.DAT` payloads match CSR flavor
- Location names for `DEL1`/`SHPIN_3` are **unconfirmed** (stems alone don't disambiguate) — blurb says so; do not assume the narrative name from the pack name alone.

## Tooling (`scripts/`)

1. `psx_mode2_iso.py` — ISO list/extract/pad-inject + overlap helper  
2. `list_changed_field_maps.py` — pristine vs patched `FIELD/*` catalog  
3. `field_jump_graph.py` — gateways + MAPJUMP scan → components among changed maps  
4. `build_field_map_pack.py` — inject maps onto pristine → `ic-layer-v1` addon  
5. `lzs.py` / `field_maplist.py` — DAT decompress + field ID names  

Catalog (CSR Disc1): **174** changed maps. Jump graph: **15** components; `SHIP_1`/`SHIP_2` is a clean size-2 component. `MD1STIN`/`MD1_1` likewise.

## Scaling attempt (2026-07-28, round 2)

Tried to auto-build one pack per remaining small component (12 attempted, excluding the giant 152-map component). **4 succeeded, 8 blocked** by the same "patched file grows past pristine ISO slot" issue first seen on Aerith house — `build_field_map_pack.py` rejects any `.DAT` whose CSR-flavor byte size exceeds the *exact* pristine file size (the ISO9660 extent is **not** padded to a sector boundary the way we assumed; even a +2 byte growth fails).

| Component | Result |
|---|---|
| `DEL1`/`SHPIN_3` | ✅ shipped (both shrank) |
| `MDS7ST1` | ✅ shipped (shrank) |
| `NIVL_3` | ✅ shipped (shrank) |
| `RCKTIN7` | ✅ shipped (shrank) |
| `JUMIN`/`UJUNON1`/`UJUNON2`/`UJUNON4` | ❌ blocked — `JUMIN` +18 bytes |
| `CLSIN2_1`/`CLSIN2_2` | ❌ blocked — `CLSIN2_2` +2 bytes |
| `JAILIN2`/`MTCRL_3` | ❌ blocked — `MTCRL_3` +4 bytes |
| `BLINST_2` | ❌ blocked — +2 bytes |
| `DYNE` | ❌ blocked — +8 bytes |
| `MKT_W` | ❌ blocked — +6 bytes |
| `MRKT4` | ❌ blocked — +5 bytes |
| `PSDUN_1` | ❌ blocked — +34 bytes |

**This means the "growth past ISO slot" problem is systemic, not an Aerith-only edge case** — roughly two-thirds of the remaining small components are blocked by it. Scaling further without fixing the ISO9660 size-field update (per the original Aerith next-step) has a low ceiling: we've likely shipped most/all of the CSR maps that happen to shrink or stay the same size, and everything that grows (even by a few bytes) needs the harder fix.

Failed builds wrote **no artifacts** (script raises before any file is written) — repo stayed clean, no partial packs to clean up.

## Aerith house (blocked) — same root cause as above

CSR+ changelog target `EALS_1.DAT` is **plus-only**, but the ISO directory size grew **10192 → 10200** (same LBA, same sector count). `replace_file_padded` refuses growth past pristine slot.

## Next-step decision point

Two paths forward, not yet chosen:

1. **Fix the ISO9660 size-field update** (update the directory record's byte-size field when the new file still fits within the same sector span) — unblocks Aerith + all 8 components above. More invasive: touches raw ISO9660 directory records shared by every pack, so a bug here risks corrupting discs across the board, not just one pack. Should get a real DuckStation boot test before shipping broadly.
2. **Stop here at 6 packs** and treat the giant 152-map component as the "CSR core" base (unsplit), shipping only maps that fit as-is. Lower risk, but caps standalone scene-pack coverage well short of full CSR parity.

## Builder playtest checklist (Windows)

1. Open https://individualcontributor.dev/builder/ (after Pages).  
2. Load pristine NTSC-U Disc 1 `.bin`.  
3. Base: **Unmodified**.  
4. Add-ons: enable all six CSR scene packs + Field encounter (any density).  
5. Build zip → DuckStation:  
   - Opening Midgar (`MD1STIN` / `MD1_1`) shows CSR edits  
   - Junon boat (`SHIP_*`) shows CSR skip/shorten  
   - `DEL1`/`SHPIN_3`, `MDS7ST1`, `NIVL_3` (Nibelheim), `RCKTIN7` (Rocket Town) scenes show CSR edits  
   - Field encounters still fire  
   - No two add-ons enabled together cause a map-load glitch
