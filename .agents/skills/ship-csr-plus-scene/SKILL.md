---
name: ship-csr-plus-scene
description: >-
  Build and publish a CSR+ scene trim as a free checkbox add-on on CSR base
  (csr-v0.14.1). Use when shipping csr-plus-scene-* packs, decomposing CSR+
  increments from workspace/csr-plus, or updating the csr-plus preset. Not for
  Highwind bases or engine binary mods.
---

# Ship a CSR+ scene add-on

## When

New or updated CSR+ field-map trim as a **checkbox** add-on on **CSR only**. Not Highwind. Not a new base.

## Preconditions

- `workspace/csr/` + `workspace/csr-plus/` images for needed discs
- Reconstruct if missing (CSR from published layer; CSR+ from last known image or pristine + retired `builder/csr-plus-v0.1.1` layer if still on disk for source maps):

```bash
python3 scripts/apply_layer.py \
  workspace/pristine/FINALFANTASY7_DN.bin \
  builder/csr-v0.14.1/layers/discN.layer.json \
  -o workspace/csr/FINALFANTASY7_DN.bin
```

## 1. Diff CSR → CSR+ (not pristine)

```bash
python3 scripts/list_changed_field_maps.py \
  --pristine workspace/csr/FINALFANTASY7_DN.bin \
  --patched workspace/csr-plus/FINALFANTASY7_DN.bin \
  --flavor csr-plus-increment \
  -o workspace/csr-plus-increment-field-diff-dN.json
```

## 2. Optional jump graph

```bash
python3 scripts/field_jump_graph.py \
  --image workspace/csr-plus/FINALFANTASY7_DN.bin \
  --changed workspace/csr-plus-increment-field-diff-dN.json \
  -o workspace/csr-plus-increment-graph-dN.json
```

One connected component ⇒ one pack. Split packs if multiple components.

## 3. Build pack — free checkbox

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

## 4. Verify

```bash
mkdir -p temp
python3 scripts/apply_layer.py \
  workspace/pristine/FINALFANTASY7_DN.bin \
  builder/csr-v0.14.1/layers/discN.layer.json \
  -o temp/csr.bin
python3 scripts/apply_layer.py \
  temp/csr.bin \
  builder/csr-plus-scene-<name>-v0.1.0/layers/discN.layer.json \
  --expect workspace/csr-plus/FINALFANTASY7_DN.bin
```

If expect is a full disc, only the injected maps must match flavor contents — prefer comparing extracted `FIELD/*.DAT` if other unrelated deltas exist on the full image.

## 5. Changelog + preset

- Update `bases/csr-plus/CHANGELOG.md`
- If “CSR+ (all scenes)” should include it, add pack id to preset `csr-plus` in `builder/manifest.json`

## 6. Commit / push / playtest

Commit `builder/` + changelog. One atomic DuckStation playtest task for human (**check results**).

## Do not

- `compatibleBases` Highwind / `clean` for CSR+ increments
- `exclusiveGroup` for independent free scenes
- Diff against pristine for CSR+ increments
- Publish `workspace/csr-plus` via `build_csr_base_layers.py`
