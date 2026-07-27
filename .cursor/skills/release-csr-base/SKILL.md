---
name: release-csr-base
description: >-
  Builds and publishes CSR / CSR+ / CSR++ ic-layer base packs for the disc
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

```bash
cd /path/to/Final-Fantasy-7-CSR
git pull --ff-only

# one base at a time
python scripts/build_csr_base_layers.py workspace/csr --version X.Y.Z
# python scripts/build_csr_base_layers.py workspace/csr-plus --version X.Y.Z
# python scripts/build_csr_base_layers.py workspace/csr-plusplus --version X.Y.Z
```

1. Update the matching `bases/<base>/CHANGELOG.md`
2. Confirm `builder/<slug>-vX.Y.Z/` + `builder/manifest.json`
3. Commit `builder/` + `bases/` and push (Pages CDN)
4. If the published **id** changed, rebuild Field encounter packs in **Final-Fantasy-7-Modding**

## Copy

Keep builder blurbs short. CSR++ = very aggressively trimmed CSR+ (story mechanics, option choices, complete dialogue removal).

## Do not

- Ship PPF or revive RomPatcher
- Commit `.bin` / `.cue`
- Scatter release instructions into new markdown files — root README owns the human steps
