---
name: release-csr-base
description: >-
  Builds and publishes CSR or Highwind ic-layer base packs for the disc builder.
  Use when releasing a CSR base, Highwind (highwind), bumping csr-v /
  highwind versions, running build_csr_base_layers.py, or updating
  builder/manifest.json in Final-Fantasy-7-CSR. Not for CSR+ scene add-ons
  (use ship-csr-plus-scene) and not for publishing a monolithic CSR+ base.
---

# Release CSR or Highwind base

**Runner:** Runner (shell + local `workspace/` bins). Agent turns this checklist into one atomic chat task; does not run the build as the publish path.

## 1. Choose target

| Target | Workspace images | Changelog | Builder slug |
|--------|------------------|-----------|--------------|
| **CSR** | `workspace/csr/` | `bases/csr/CHANGELOG.md` | `csr-vX.Y.Z` |
| **Highwind** | `workspace/highwind/` | `bases/highwind/CHANGELOG.md` | `highwind-vX.Y.Z` |

Do **not** publish a new monolithic CSR+ base (`workspace/csr-plus` + `build_csr_base_layers.py`). CSR+ trims → skill `ship-csr-plus-scene`.

## 2. Preconditions

- `workspace/pristine/FINALFANTASY7_DN.bin` for needed discs
- Patched images named `FINALFANTASY7_DN.bin` under the flavor dir
- Changelog draft for the new version

## 3. If patched bin missing — reconstruct last published

```bash
mkdir -p workspace/csr workspace/highwind
python3 scripts/apply_layer.py \
  workspace/pristine/FINALFANTASY7_D1.bin \
  builder/csr-v0.14.1/layers/disc1.layer.json \
  -o workspace/csr/FINALFANTASY7_D1.bin
# Highwind: builder/highwind-v0.1.1/layers/discN.layer.json → workspace/highwind/
# Repeat for disc 2/3 as needed
```

Then human edits **that** image in Makou (saves stay under `workspace/<flavor>/`).

## 4. Human (Makou) — one atomic chat task

Open flavor image → edit → save into `workspace/csr/` or `workspace/highwind/`. Full steps in chat per `agent-human-workflow`. Never commit bins.

## 5. EDC repair each disc

```bash
python3 scripts/repair_mode2_edc.py \
  --pristine workspace/pristine/FINALFANTASY7_D1.bin \
  --input workspace/csr/FINALFANTASY7_D1.bin \
  --in-place
# D2/D3; use workspace/highwind for Highwind
```

## 6. Build layers (one base at a time)

```bash
git pull --ff-only
python3 scripts/build_csr_base_layers.py workspace/csr --version X.Y.Z
# Highwind:
# python3 scripts/build_csr_base_layers.py workspace/highwind --version X.Y.Z
```

## 7. Verify (required before publish)

`build_csr_base_layers.py` already self-checks layers. **Also** prove the builder can stack the new base id on pristine (same path the site uses):

```bash
# after build; use the new id you just wrote (example highwind-v0.1.2)
python3 scripts/verify_builder_config.py \
  --pristine workspace/pristine/FINALFANTASY7_D1.bin \
  --disc 1 \
  --base highwind-vX.Y.Z
# repeat --disc 2 and 3 when those discs shipped
```

Must print `PASS`. Sanity: record counts not thousands of zero-footer junk.

## 8. Changelog + commit/push

Update `bases/csr/CHANGELOG.md` or `bases/highwind/CHANGELOG.md`. Commit `builder/` + `bases/`; push Pages CDN.

## 9. If published **id** changed

Rebuild Modding Field/World packs: `ship-field-encounters` / `ship-world-encounters` with new `compatibleBases`.

## Copy rules

- Highwind blurb = aggressively trimmed playthrough; **separate mod**, not a bigger CSR+.
- Do not imply Highwind stacks with CSR+ scene add-ons.

## Do not

- Commit `.bin` / `.cue`
- Ship PPF / RomPatcher
- Publish `csr-plus` as a base
- Use this skill for FIELD scene add-ons (use `ship-csr-plus-scene` or `ship-makou-addon`)
