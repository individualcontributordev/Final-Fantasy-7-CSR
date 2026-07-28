# Architecture pivot: Unmodified/CSR bases + CSR+ scene add-ons, CSR++ retired

**Date:** 2026-07-28
**Supersedes:** the "mixable per-field CSR packs" direction in
[2026-07-28-mixable-field-packs-prototype.md](2026-07-28-mixable-field-packs-prototype.md)
(pristine-vs-CSR scene packs) — those 6 packs were built, verified (no overlap),
then removed per a scope decision below.

## Decision

The builder now offers exactly two bases — **Unmodified** and **CSR** — instead
of three (CSR / CSR+ / CSR++). CSR+'s extra trims are decomposed into individual
`csr-plus-scene-*` add-ons a CSR-base player can pick and choose. CSR++ is
different enough to be its own project and is being continued in Makou Reactor;
it's removed from `builder/manifest.json` but its files stay in the repo.

## What changed this session

1. **Removed from `builder/manifest.json`:**
   - `bases`: `csr-plus-v0.1.1`, `csr-plusplus-v0.1.1` (files kept on disk under
     `builder/csr-plus-v0.1.1/`, `builder/csr-plusplus-v0.1.1/`, `bases/csr-plus/`,
     `bases/csr-plusplus/` — just unpublished).
   - `addons`: the 6 pristine-vs-CSR scene packs from the prior prototype
     (`csr-scene-boat`, `csr-scene-midgar-start`, `csr-scene-del1-shpin3`,
     `csr-scene-mds7st1`, `csr-scene-nivl3`, `csr-scene-rcktin7`) — deleted from
     `builder/` entirely, since CSR stays a monolithic selectable base and these
     no longer serve a purpose under the new model.
   - Also removed the matching `*-on-csr-plusplus-*` combo packs from
     **Final-Fantasy-7-Modding**'s `builder/manifest.json` (6 packs: field +
     world encounter rate × 25/50/75, pre-combined with the now-retired base).

2. **Cataloged the actual CSR-vs-CSR+ increment** (not pristine-vs-CSR):
   `list_changed_field_maps.py --pristine workspace/csr/... --patched
   workspace/csr-plus/...` → **Disc 1 has exactly one changed FIELD map:
   `EALS_1` (Aerith's house)**, matching `bases/csr-plus/CHANGELOG.md`'s "Aerith's
   house cutscene removed" line exactly. Disc 2 has one more (Hojo FD manip
   cutscene per changelog) but there's no local `workspace/csr`/`workspace/csr-plus`
   Disc 2 `.bin` to diff yet — needs Windows human to supply those. Disc 3: no
   changes per changelog, nothing to do.

3. **Fixed the systemic ISO-slot-growth blocker.** `EALS_1` grows 10192 → 10200
   bytes (8 bytes) from CSR to CSR+ — the same "growth past ISO slot" issue that
   blocked this exact map back when the prototype tried it as pristine-vs-CSR+.
   Root cause: `replace_file_padded` in `psx_mode2_iso.py` refused any growth
   past the *exact* pristine byte count, even though the ISO9660 extent still had
   spare capacity in its last allocated sector (ceil(10192/2048) ==
   ceil(10200/2048) == 5 sectors either way).

   Fix: `psx_mode2_iso.py` now tracks each file's parent directory-record
   location (`IsoFile.dir_lba` / `rec_offset`) and exposes
   `patch_dir_record_size()`, which patches the record's byte-size field (both
   the little-endian and big-endian copies ISO9660 stores) in place — directory
   records never span a sector boundary, so this is a single-sector read/patch/write.
   `replace_file_padded` was replaced by `replace_file()`, which allows growth as
   long as `ceil(new_size/2048) <= ceil(old_size/2048)` and patches the directory
   record when the size actually changes; it still refuses growth that would need
   more sectors (true rebuild case).

   Verified: round-tripped in memory (grow + shrink cases both re-parse to the
   correct size and byte-identical content), and end-to-end via
   `apply_layer.py` on a fresh `workspace/csr` copy — the applied disc's
   `EALS_1` matches the real `workspace/csr-plus` copy byte-for-byte, with
   exactly `changedBytes` (9928) differing from the CSR baseline, nothing else.

4. **Shipped `csr-plus-scene-aerith-house-v0.1.0`** — `compatibleBases:
   ["csr-v0.14.1"]`, so it only shows up when a player picks CSR as the base.
   This is the entire CSR-vs-CSR+ Disc 1 increment.

## `build_field_map_pack.py` changes

- Uses `replace_file` instead of `replace_file_padded` (see above).
- New `--compatible-bases` flag (default `["clean"]`, kept for any future
  pristine-vs-base packs) — pass `--compatible-bases csr-v0.14.1` for
  CSR-vs-CSR+ increment packs.

## Next steps

- **Disc 2 Hojo scene**: need `workspace/csr/FINALFANTASY7_D2.bin` and
  `workspace/csr-plus/FINALFANTASY7_D2.bin` (Windows human to supply / EDC-repair
  per README) to catalog and ship as a second `csr-plus-scene-*` add-on.
- **CSR++ / Makou Reactor**: out of scope here going forward — do not resume
  building it into this builder stack without an explicit decision to revive it.

## Modding repo follow-on cleanup (same session)

`csr-plus-v0.1.1` is retired as a base here, so the 6 Modding packs pinned to it
(`field-encounter-on-csr-plus-{25,50,75}-v0.1.2`,
`world-encounter-on-csr-plus-{25,50,75}-v0.1.0`, `compatibleBases:
["csr-plus-v0.1.1"]`) are now orphaned the same way the `-on-csr-plusplus-*` ones
were — removed alongside them. The `-on-csr-v0.14.1-*` variants (field/world ×
25/50/75) were **already compatible with the CSR base and untouched** — a
CSR-base player can already add encounter-rate mods, nothing to build there.
