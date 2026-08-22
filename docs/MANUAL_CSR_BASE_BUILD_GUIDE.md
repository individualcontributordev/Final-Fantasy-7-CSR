# Manual CSR/Highwind base build guide

Runbook for editing a CSR or Highwind base disc and publishing a new
version. Run everything from the repo root (`Final-Fantasy-7-CSR`) with
Python 3. Never commit `.bin`/`.cue`.

## Tools

- **Makou Reactor** — field script/map editor (all `FIELD/*.DAT` edits)
- **DuckStation** (or RetroArch + SwanStation) — playtest, open the `.cue`
- Python 3 + this repo's `scripts/`

## 0. Pick target and get a starting image

| Target | Working dir | Changelog | Builder slug |
|--------|-------------|-----------|--------------|
| CSR | `cache/csr/` | `bases/csr/CHANGELOG.md` | `csr-vX.Y.Z` |
| Highwind | `cache/highwind/` | `bases/highwind/CHANGELOG.md` | `highwind-vX.Y.Z` |

`git pull --ff-only` first. If `cache/<flavor>/FINALFANTASY7_DN.bin` is
missing for the disc you need, rebuild it from the last published layer:

```bash
mkdir -p cache/csr cache/highwind
python3 scripts/apply_layer.py \
  pristine/FINALFANTASY7_D1.bin \
  builder/csr-v0.14.1/layers/disc1.layer.json \
  -o cache/csr/FINALFANTASY7_D1.bin
# repeat per disc (2/3) and per flavor (swap csr -> highwind, use its own
# current published version's layer)
```

## 1. Edit in Makou Reactor

Open `cache/csr/FINALFANTASY7_DN.bin` (or `cache/highwind/...`) in Makou,
make your field edits, **File → Save** back into that same file. Repeat for
every disc you're touching.

## 2. Repair EDC footers (required, every disc you touched)

Makou/CDmage injects zeroed Mode2 Form1 sector footers. Skipping this bakes
EDC-zero noise into the published layer diff.

```bash
python3 scripts/repair_mode2_edc.py \
  --pristine pristine/FINALFANTASY7_D1.bin \
  --input cache/csr/FINALFANTASY7_D1.bin \
  --in-place
# repeat for each disc you edited (swap D1->D2/D3, csr->highwind as needed)
```

## 3. Build the layer(s)

Diffs `pristine/` vs. your edited `cache/<flavor>/` images and writes a new
versioned builder folder. Pick a new `X.Y.Z` — this never overwrites an
existing published version in place.

```bash
python3 scripts/build_csr_base_layers.py cache/csr --version X.Y.Z
# Highwind:
# python3 scripts/build_csr_base_layers.py cache/highwind --version X.Y.Z
# limit to specific discs if only some changed:
#   --discs 2        (or 1,2,3)
```

This writes `builder/<slug>-v<version>/layers/discN.layer.json` +
`pack.json`, and updates `builder/manifest.json`. It only writes layers for
discs it finds a pristine+patched pair for — if you only edited Disc 2, copy
the other discs' layer files from the previous version's folder and merge
`pack.json`'s `discs` map by hand so the new version still covers all three
discs.

The script self-verifies (reapplies the layer onto pristine and byte-compares
against your patched image) and aborts with `VERIFY FAIL` if something's
wrong.

## 4. Verify against the builder stack (required before publish)

Proves the exact stack the live site uses (pristine + this base id) applies
cleanly:

```bash
python3 scripts/verify_builder_config.py \
  --pristine pristine/FINALFANTASY7_D1.bin \
  --disc 1 \
  --base csr-vX.Y.Z
# repeat --disc 2 / --disc 3 for every disc that base now covers
```

Must print `PASS`. If it prints thousands of zero-footer/junk records, EDC
repair (step 2) was skipped or didn't take.

## 5. CSR only — scene add-on regression (required)

Only for a **CSR** release (skip for Highwind — CSR+ scenes never apply to
Highwind):

```bash
python3 scripts/verify_csr_addon_compat.py
```

Must print `PASS`. On failure, either this base broke a scene pack (fix the
base) or a scene pack needs its `compatibleBases`/layer updated to match —
fix and re-run until green. Then add the new `csr-vX.Y.Z` id to
`compatibleBases` on every enabled `csr-plus-scene-*` pack.

## 6. Changelog, commit, push

Update `bases/csr/CHANGELOG.md` or `bases/highwind/CHANGELOG.md` (newest
entry at top). Commit only JSON/markdown:

```bash
git add builder/ bases/
git commit -m "CSR vX.Y.Z: <one-line summary>" \
  --author="individualcontributordev <contributorindividual@gmail.com>"
git push
```

Live on Pages CDN in ~2 minutes.

## 7. If the published base id changed

Downstream repos/packs pin `compatibleBases` to the old id and need a bump:

- **This repo:** every enabled `csr-plus-scene-*` pack's `compatibleBases`
  (done in step 5 for CSR; for Highwind there are none to update).
- **`Final-Fantasy-7-Modding`:** Field/World encounter packs
  (`ship-field-encounters` / `ship-world-encounters` skills) and anything
  under `mods/single-disc/` that hardcodes the old `csr-v*`/`highwind-v*`
  string (e.g. `scripts/disc_sources.py`, pack/manifest `compatibleBases`).
  Rebuild and republish those after this base is live.

## Never

- Commit `.bin` / `.cue`
- Publish a monolithic `csr-plus` base (`cache/csr-plus` is CSR+ scene
  source material only — see `docs/CREATE_ADDON_FROM_MAKOU.md`)
- Skip EDC repair or the two verify scripts before publishing
