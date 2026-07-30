---
name: ship-csr-plus-scene
description: >-
  Build and publish a CSR+ scene trim as a free checkbox add-on on CSR base
  (csr-v0.14.1). Use when shipping csr-plus-scene-* packs, decomposing CSR+
  increments from workspace/csr-plus, or updating the csr-plus preset. Not for
  Highwind bases or engine binary mods.
---

# Ship a CSR+ scene add-on

**Runner:** Windows (Git Bash + local `workspace/csr` + `workspace/csr-plus` bins). Mac agent instructs only; optional post-publish verify of `builder/` JSON.

## When

New **or updated** CSR+ field-map trim as a **checkbox** add-on on **CSR only**. Not Highwind. Not a new base.

| Goal | Start at |
|------|----------|
| First-time scene pack | [New scene](#new-scene) |
| Change maps/bytes of an existing published pack (e.g. Aerith house) | [Update existing](#update-existing) |
| Blurb / display name only | Edit `builder/<pack-id>/pack.json` + matching manifest entry; no layer rebuild |

---

## Update existing

Use this when the pack already lives under `builder/csr-plus-scene-*-v…/` (example: `csr-plus-scene-aerith-house-v0.1.0` → `FIELD/EALS_1.DAT`).

### U0. Baseline images

- Diff baseline = **CSR**, not pristine: `workspace/csr/FINALFANTASY7_DN.bin`
- Edited image = your Makou save: usually `workspace/csr-plus/FINALFANTASY7_DN.bin` (or a dedicated workspace copy)
- Reconstruct CSR if missing:

```bash
python3 scripts/apply_layer.py \
  workspace/pristine/FINALFANTASY7_DN.bin \
  builder/csr-v0.14.1/layers/discN.layer.json \
  -o workspace/csr/FINALFANTASY7_DN.bin
```

### U1. Edit in Makou

1. Open the **CSR** (or current csr-plus working) disc image in Makou.
2. Edit only maps that belong to this scene (see `pack.json` → `files`, e.g. `FIELD/EALS_1.DAT`).
3. Save the image to `workspace/csr-plus/` (or your working path). Do **not** overwrite `workspace/pristine` or publish CSR-plus as a base.

### U2. Confirm which maps changed (optional if scope unchanged)

```bash
python3 scripts/list_changed_field_maps.py \
  --pristine workspace/csr/FINALFANTASY7_DN.bin \
  --patched workspace/csr-plus/FINALFANTASY7_DN.bin \
  --flavor csr-plus-increment \
  -o workspace/csr-plus-increment-field-diff-dN.json
```

Keep `--files` to this scene’s maps only (do not swallow unrelated csr-plus deltas into one pack).

### U3. Version bump + rebuild

**Bump the pack id** (semver in the id). Do not silently overwrite a shipped `…-v0.1.0` id if players may have old zips — new folder, new id.

```bash
# Example: Aerith house v0.1.0 → v0.1.1
OLD=csr-plus-scene-aerith-house-v0.1.0
NEW=csr-plus-scene-aerith-house-v0.1.1

python3 scripts/build_field_map_pack.py \
  --pristine workspace/csr/FINALFANTASY7_DN.bin \
  --flavor-image workspace/csr-plus/FINALFANTASY7_DN.bin \
  --files FIELD/EALS_1.DAT \
  --pack-id "$NEW" \
  --version 0.1.1 \
  --disc 1 \
  --name "CSR+ Aerith's house" \
  --group-label "CSR+ Aerith's house" \
  --blurb "CSR+ trim of Aerith's house cutscene." \
  --no-exclusive-group \
  --compatible-bases csr-v0.14.1
```

Rules unchanged: omit `exclusiveGroup`; `compatibleBases` = `csr-v0.14.1` only.

### U4. Manifest + preset

`build_field_map_pack.py` registers `$NEW` in `builder/manifest.json`. Then:

1. Set old pack `"enabled": false` (or remove) so the builder does not list two Aerith checkboxes.
2. In preset `csr-plus` → `addons`, replace `$OLD` with `$NEW`.
3. Leave other scene ids untouched.

### U5. Verify (required)

```bash
python3 scripts/verify_builder_config.py \
  --pristine workspace/pristine/FINALFANTASY7_DN.bin \
  --disc N \
  --base csr-v0.14.1 \
  --addon csr-plus-scene-<name>-vX.Y.Z
# PASS required. Must fail on --base highwind-v… / clean if someone mistakes baselines.
```

Optional: extract `FIELD/<MAP>.DAT` from csr + new layer and compare to Makou output bytes.

### U6. Changelog + ship

- Note the bump in `bases/csr-plus/CHANGELOG.md`
- Commit `builder/` (+ changelog). Push. Pages picks up CDN.
- One atomic DuckStation check on CSR + this checkbox (human **check**).

---

## New scene

### Preconditions

- `workspace/csr/` + `workspace/csr-plus/` images for needed discs
- Reconstruct CSR if missing (see U0).

### 1. Diff CSR → CSR+ (not pristine)

```bash
python3 scripts/list_changed_field_maps.py \
  --pristine workspace/csr/FINALFANTASY7_DN.bin \
  --patched workspace/csr-plus/FINALFANTASY7_DN.bin \
  --flavor csr-plus-increment \
  -o workspace/csr-plus-increment-field-diff-dN.json
```

### 2. Optional jump graph

```bash
python3 scripts/field_jump_graph.py \
  --image workspace/csr-plus/FINALFANTASY7_DN.bin \
  --changed workspace/csr-plus-increment-field-diff-dN.json \
  -o workspace/csr-plus-increment-graph-dN.json
```

One connected component ⇒ one pack. Split packs if multiple components.

### 3. Build pack — free checkbox

```bash
python3 scripts/build_field_map_pack.py \
  --pristine workspace/csr/FINALFANTASY7_DN.bin \
  --flavor-image workspace/csr-plus/FINALFANTASY7_DN.bin \
  --files FIELD/<MAP>.DAT \
  --pack-id csr-plus-scene-<name>-v0.1.0 \
  --disc N \
  --name "CSR+ scene — <Name>" \
  --group-label "CSR+ scene — <Name>" \
  --blurb "CSR+ trim of <scene> on top of CSR." \
  --no-exclusive-group \
  --compatible-bases csr-v0.14.1
```

Confirm `pack.json` / manifest **omit** `exclusiveGroup`. Never set Highwind in `compatibleBases`.

### 4. Verify (required before publish)

```bash
python3 scripts/verify_builder_config.py \
  --pristine workspace/pristine/FINALFANTASY7_DN.bin \
  --disc N \
  --base csr-v0.14.1 \
  --addon csr-plus-scene-<name>-v0.1.0
```

### 5. Changelog + preset

- Update `bases/csr-plus/CHANGELOG.md`
- If “CSR+ (all scenes)” should include it, add pack id to preset `csr-plus` in `builder/manifest.json`

### 6. Commit / push / playtest

Commit `builder/` + changelog. One atomic DuckStation playtest task for human (**check results**).

---

## Do not

- `compatibleBases` Highwind / `clean` for CSR+ increments
- `exclusiveGroup` for independent free scenes
- Diff against pristine for CSR+ increments
- Publish `workspace/csr-plus` via `build_csr_base_layers.py`
- Overwrite a shipped pack id in place when the change is a real release (bump version id instead)
- Merge unrelated csr-plus map deltas into an existing scene’s `--files` list
