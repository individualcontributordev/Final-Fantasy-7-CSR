---
name: release-csr-base
description: >-
  Builds and publishes CSR / CSR+ / Highwind ic-layer base packs for the disc
  builder. Use when releasing a CSR base, bumping csr-v / csr-plus / csr-plusplus
  versions, running build_csr_base_layers.py, or updating builder/manifest.json
  in Final-Fantasy-7-CSR.
---

# Release a CSR base

## Preconditions

- Patched disc images at `workspace/csr/` / `workspace/csr-plus/` / `workspace/csr-plusplus/`
  (`FINALFANTASY7_DN.bin` per disc naming used by the script)
- Pristine reference under `workspace/pristine/` as required by the build script
- Changelog entry ready for `bases/<base>/CHANGELOG.md`

## Steps

1. Ensure pristine + patched bins use names `FINALFANTASY7_DN.bin`
2. **Repair EDC/ECC on patched images** (avoids zero-footer junk in layers):

```bash
python scripts/repair_mode2_edc.py \
  --pristine workspace/pristine/FINALFANTASY7_D1.bin \
  --input workspace/csr-plus/FINALFANTASY7_D1.bin \
  --in-place
# D2/D3 likewise
```

3. Build layers:

```bash
cd /path/to/Final-Fantasy-7-CSR
git pull --ff-only

# one base at a time
python scripts/build_csr_base_layers.py workspace/csr --version X.Y.Z
# python scripts/build_csr_base_layers.py workspace/csr-plus --version X.Y.Z
# python scripts/build_csr_base_layers.py workspace/csr-plusplus --version X.Y.Z
```

4. Update the matching `bases/<base>/CHANGELOG.md`
5. Confirm `builder/<slug>-vX.Y.Z/` + `builder/manifest.json` (record count should drop vs old zero-footer layers)
6. Commit `builder/` + `bases/` and push (Pages CDN)
7. If the published **id** changed, rebuild Field encounter packs in **Final-Fantasy-7-Modding**

## Copy

Keep builder blurbs short. Highwind = an aggressively trimmed playthrough, its own separate mod (story mechanics, option choices, complete dialogue removal).

## Do not

- Ship PPF or revive RomPatcher
- Commit `.bin` / `.cue`
- Scatter release instructions into new markdown files — root README owns the human steps
