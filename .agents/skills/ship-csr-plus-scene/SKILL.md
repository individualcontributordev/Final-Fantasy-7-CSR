---
name: ship-csr-plus-scene
description: >-
  Build and publish a CSR+ scene trim as a free checkbox add-on on CSR base
  (csr-v0.14.1). Use when shipping csr-plus-scene-* packs, decomposing CSR+
  increments from cache/csr-plus, or updating the csr-plus preset. Not for
  Highwind bases or engine binary mods.
---

# Ship a CSR+ scene add-on

**Runner:** Windows (Git Bash + local `cache/csr` + `cache/csr-plus` bins). Mac agent instructs only; optional post-publish verify of `builder/` JSON.

## When

New **or updated** CSR+ field-map trim as a **checkbox** add-on on **CSR only**. Not Highwind. Not a new base.

| Goal | Start at |
|------|----------|
| First-time scene pack | [New scene](#new-scene) |
| Change maps/bytes of an existing published pack (e.g. Aerith house) | [Update existing](#update-existing) |
| Blurb / display name only | Edit `builder/<pack-id>/pack.json` + matching manifest entry; no layer rebuild |

---

## Update existing (preferred: builder zip)

Use when the pack already lives under `builder/csr-plus-scene-*-v…/`
(example: `csr-plus-scene-aerith-house-v0.1.0` → `FIELD/EALS_1.DAT`).

### U1. Builder → Makou

1. https://individualcontributor.dev/builder/ — pristine disc N, base **CSR**,
   enable **only** the scene add-on you are updating (or CSR+ preset if that is the only change you need).
2. Build → unzip. Keep `.bin` + `APPLIED.txt` in the same folder.
3. Open the `.bin` in Makou. Edit maps for that scene only. **Save back into the same extract folder.**

### U2. Rebuild pack from the edited zip

Config comes **only** from `APPLIED.txt` (same idea as Modding `verify_built_disc.py`).
Diff baseline = the **base** named in APPLIED (CSR), not pristine and not “base + other addons”.
Map list comes from the old pack’s `pack.json` `files`. Version defaults to **patch +1**.

```bash
cd "$(git rev-parse --show-toplevel)"
git pull --ff-only

# path = extract folder or the edited .bin (APPLIED.txt must sit next to the .bin)
python3 scripts/update_addon_from_builder_zip.py "/path/to/ff7-builder-d1+csr-…+aerith-…/"

# major/minor bump instead of patch:
# python3 scripts/update_addon_from_builder_zip.py "/path/to/extract" --version 0.2.0

# several add-ons in APPLIED — pick which to bump:
# python3 scripts/update_addon_from_builder_zip.py "/path/to/extract" --addon csr-plus-scene-aerith-house
```

Script writes `builder/<stem>-vNEW/`, updates `manifest.json`, sets old pack
`enabled: false`, swaps id in preset `csr-plus`.

### U3. Verify (required)

```bash
python3 scripts/verify_builder_config.py \
  --pristine pristine/FINALFANTASY7_DN.bin \
  --disc N \
  --base csr-v0.14.1 \
  --addon csr-plus-scene-<name>-vX.Y.Z
# PASS required
```

### U4. Playtest without the site builder (layer stack)

Same stack the site will apply: pristine → base layer → **new** add-on layer only.

```bash
mkdir -p temp
python3 scripts/apply_layer.py \
  pristine/FINALFANTASY7_D1.bin \
  builder/csr-v0.14.1/layers/disc1.layer.json \
  -o temp/csr-d1.bin
python3 scripts/apply_layer.py \
  temp/csr-d1.bin \
  builder/csr-plus-scene-<name>-vX.Y.Z/layers/disc1.layer.json \
  -o temp/play-d1.bin
# open temp/play-d1.bin (make a .cue if needed) in DuckStation
```

Iterate: fix in Makou on the **builder extract** again → re-run
`update_addon_from_builder_zip.py` (bump again or pass `--version`) → re-apply layers.

### U5. Changelog + ship

- Note the bump in `addons/csr-plus/CHANGELOG.md` (pack id + one line). See `CHANGELOGS.md`.
- Commit `builder/` (+ changelog). Push. Pages CDN.
- Optional: one more DuckStation pass from builder zip after Pages updates.

### Manual fallback (no builder zip)

Still valid: Makou on `cache/csr-plus`, then
`build_field_map_pack.py` with `--pristine cache/csr/…`, explicit
`--files` / `--pack-id` / version, then hand-edit manifest/preset. Prefer
`update_addon_from_builder_zip.py` for day-to-day updates.

---

## New scene

### Preconditions

- `cache/csr/` + `cache/csr-plus/` images for needed discs
- Reconstruct CSR if missing (see U0).

### 1. Diff CSR → CSR+ (not pristine)

```bash
python3 scripts/list_changed_field_maps.py \
  --pristine cache/csr/FINALFANTASY7_DN.bin \
  --patched cache/csr-plus/FINALFANTASY7_DN.bin \
  -o temp/csr-plus-increment-field-diff-dN.json
```

### 2. Optional jump graph

```bash
python3 scripts/field_jump_graph.py \
  --image cache/csr-plus/FINALFANTASY7_DN.bin \
  --changed temp/csr-plus-increment-field-diff-dN.json \
  -o temp/csr-plus-increment-graph-dN.json
```

One connected component ⇒ one pack. Split packs if multiple components.

### 3. Build pack — free checkbox

```bash
python3 scripts/build_field_map_pack.py \
  --pristine cache/csr/FINALFANTASY7_DN.bin \
  --edited-image cache/csr-plus/FINALFANTASY7_DN.bin \
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

Single stack (this pack on the CSR id you built against):

```bash
python3 scripts/verify_builder_config.py \
  --pristine pristine/FINALFANTASY7_DN.bin \
  --disc N \
  --base csr-v0.14.1 \
  --addon csr-plus-scene-<name>-v0.1.0
```

`compatibleBases` must list **every live `csr-v*` base** in `builder/manifest.json` (backward compatible). After shipping a scene **or** a new CSR base:

```bash
python3 scripts/verify_csr_addon_compat.py
# PASS = all live CSR bases × all enabled csr-plus-scene-* packs apply cleanly
```

If this fails after a CSR base bump: fix the **base** or the **add-on**, then re-run. Do not leave a silent break.

### 5. Changelog + preset

- Update `addons/csr-plus/CHANGELOG.md` (see `CHANGELOGS.md`)
- If “CSR+ (all scenes)” should include it, add pack id to preset `csr-plus` in `builder/manifest.json`

### 6. Commit / push / playtest

Commit `builder/` + changelog. One atomic DuckStation playtest task for human (**check results**).

---

## Do not

- `compatibleBases` Highwind / `clean` for CSR+ increments
- `exclusiveGroup` for independent free scenes
- Diff against pristine for CSR+ increments
- Publish `cache/csr-plus` via `build_csr_base_layers.py`
- Overwrite a shipped pack id in place when the change is a real release (bump version id instead)
- Merge unrelated csr-plus map deltas into an existing scene’s `--files` list
