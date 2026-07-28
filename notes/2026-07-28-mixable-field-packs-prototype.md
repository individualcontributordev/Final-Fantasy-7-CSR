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

- `compatibleBases: ["clean"]`
- Separate `exclusiveGroup` per scene
- Layer byte ranges: **no overlap**
- Programmatic stack apply: injected `.DAT` payloads match CSR flavor

## Tooling (`scripts/`)

1. `psx_mode2_iso.py` — ISO list/extract/pad-inject + overlap helper  
2. `list_changed_field_maps.py` — pristine vs patched `FIELD/*` catalog  
3. `field_jump_graph.py` — gateways + MAPJUMP scan → components among changed maps  
4. `build_field_map_pack.py` — inject maps onto pristine → `ic-layer-v1` addon  
5. `lzs.py` / `field_maplist.py` — DAT decompress + field ID names  

Catalog (CSR Disc1): **174** changed maps. Jump graph: **15** components; `SHIP_1`/`SHIP_2` is a clean size-2 component. `MD1STIN`/`MD1_1` likewise.

## Aerith house (blocked)

CSR+ changelog target `EALS_1.DAT` is **plus-only**, but the ISO directory size grew **10192 → 10200** (same LBA, same sector count). `replace_file_padded` refuses growth past pristine slot. Next step: update the ISO9660 size field when sector span is unchanged, then retry Aerith as pack B.

## Builder playtest checklist (Windows)

1. Open https://individualcontributor.dev/builder/ (after Pages).  
2. Load pristine NTSC-U Disc 1 `.bin`.  
3. Base: **Unmodified**.  
4. Add-ons: enable both CSR scene packs + Field encounter (any density).  
5. Build zip → DuckStation:  
   - Opening Midgar (`MD1STIN` / `MD1_1`) shows CSR edits  
   - Junon boat (`SHIP_*`) shows CSR skip/shorten  
   - Field encounters still fire  

## Next-step recommendation

Scale: auto-build one pack per **small** jump component that fits ISO slots; keep giant Midgar-linked component as optional “CSR core” base or further split with human changelog labels. Do not drop monolithic CSR bases until playtest coverage is broad.
