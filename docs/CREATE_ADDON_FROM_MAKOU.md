# Creating Add-ons from Makou Reactor Edits

Complete workflow for turning Makou Reactor field map edits into builder add-on packs.

## Prerequisites

- Makou Reactor on Windows for editing
- Mac with this repo cloned
- Python 3 with required packages

## Workflow

### 1. Edit in Makou Reactor (Windows)

1. Open your disc image in Makou Reactor
2. Navigate to the field maps you want to edit
3. Make your changes (scripts, walkmesh, encounters, models, etc.)
4. **File → Save** (or Ctrl+S) to write changes to the disc image
5. Copy the modified `.bin` file to your Mac

**Tip:** Keep notes of which maps you edited for the next step.

---

### 2. Transfer to Mac workspace

```bash
cd ~/Final-Fantasy-7-CSR/workspace
mkdir my-addon-name  # descriptive name for your changes
cp /path/to/modified/FINALFANTASY7_D1.bin my-addon-name/
```

---

### 3. Identify changed maps

Compare your edited disc against the CSR base to find which FIELD maps changed:

```bash
cd ~/Final-Fantasy-7-CSR

python3 scripts/list_changed_field_maps.py \
  --pristine workspace/csr/FINALFANTASY7_D1.bin \
  --patched workspace/my-addon-name/FINALFANTASY7_D1.bin \
  --flavor my-addon \
  -o workspace/my-addon-field-diff.json
```

This creates a JSON catalog of all changed maps. Example output:
```
Found 3 changed FIELD maps in my-addon:
  MIDEEL_1: pristine=15234 → patched=15891 (+657 bytes)
  MIDEEL_2: pristine=18203 → patched=18203 (same size)
  JUMIN:    pristine=12048 → patched=12066 (+18 bytes)
```

**Important:** The diff is against **CSR base**, not pristine. Your addon will be `compatibleBases: ["csr-v0.14.1"]`.

If you edited against pristine/Unmodified instead, change `--pristine` to `workspace/pristine/FINALFANTASY7_D1.bin` and use `--compatible-bases clean` in step 5.

---

### 4. (Optional) Check connectivity

If your changes span multiple maps, verify they're a connected scene:

```bash
python3 scripts/field_jump_graph.py \
  workspace/my-addon-field-diff.json \
  -o workspace/my-addon-graph.json
```

This shows which maps gateway/MAPJUMP to each other. One connected component = one cohesive scene, perfect for a single add-on.

---

### 5. Build the add-on pack

Extract just the changed maps as an `ic-layer-v1` pack:

```bash
python3 scripts/build_field_map_pack.py \
  --pristine workspace/csr/FINALFANTASY7_D1.bin \
  --flavor-image workspace/my-addon-name/FINALFANTASY7_D1.bin \
  --files FIELD/MIDEEL_1.DAT FIELD/MIDEEL_2.DAT FIELD/JUMIN.DAT \
  --pack-id my-addon-scene-v0.1.0 \
  --disc 1 \
  --name "My Scene Name" \
  --group-label "My Scene Name" \
  --blurb "Brief description of what this addon does." \
  --exclusive-group my-addon-scene \
  --compatible-bases csr-v0.14.1
```

**Parameters explained:**
- `--pristine`: Base disc to diff against (usually CSR)
- `--flavor-image`: Your Makou-edited disc
- `--files`: Space-separated list of changed FIELD/*.DAT files (from step 3)
- `--pack-id`: Unique ID with version (e.g., `my-addon-scene-v0.1.0`)
- `--disc`: Which disc (1, 2, or 3)
- `--name`: Display name in builder
- `--group-label`: Dropdown label in builder
- `--blurb`: Short description (keep under 80 chars)
- `--exclusive-group`: Players can only pick one addon in this group
- `--compatible-bases`: Which base(s) this works on top of (usually `csr-v0.14.1` or `clean`)

**Output:**
- `builder/my-addon-scene-v0.1.0/pack.json`
- `builder/my-addon-scene-v0.1.0/layers/disc1.layer.json`
- Updates `builder/manifest.json`

---

### 6. Verify the pack

Apply your addon on top of CSR base and verify it matches your Makou disc:

```bash
# Reconstruct CSR base from pristine + CSR layer
python3 scripts/apply_layer.py \
  workspace/pristine/FINALFANTASY7_D1.bin \
  builder/csr-v0.14.1/layers/disc1.layer.json \
  -o /tmp/csr-base.bin

# Apply your addon
python3 scripts/apply_layer.py \
  /tmp/csr-base.bin \
  builder/my-addon-scene-v0.1.0/layers/disc1.layer.json \
  --expect workspace/my-addon-name/FINALFANTASY7_D1.bin
```

If `--expect` matches, you'll see:
```
Applied layer OK — 234 records / 45678 changed bytes
Output matches expected image exactly.
```

If there's a mismatch, it reports the first differing byte offset.

---

### 7. Commit and publish

```bash
git add builder/my-addon-scene-v0.1.0/ builder/manifest.json
git commit -m "Add my-addon-scene-v0.1.0 addon."
git push origin main
```

GitHub Pages will auto-publish within ~2 minutes. The builder fetches from:
`https://individualcontributordev.github.io/Final-Fantasy-7-CSR/builder/manifest.json`

---

## Tips

- **Multiple discs?** Repeat steps 3-5 for each disc, using `--disc 2` or `--disc 3`
- **Growth too big?** If a map grows beyond its ISO slot, the script will error. The ISO9660 fix from the CSR+ scene addons handles growth within the same sector span.
- **Testing in builder:** Load pristine disc 1, select CSR base, enable your addon, build zip, test in DuckStation
- **Naming convention:** Use `<category>-<scene>-v<version>` for pack IDs (e.g., `csr-plus-scene-aerith-house-v0.1.0`)

---

## Example: Real CSR+ scene addon

See how Aerith's house was built:
- Notes: `notes/2026-07-28-csr-plus-increment-pivot.md`
- Pack: `builder/csr-plus-scene-aerith-house-v0.1.0/`
- Command used (from notes):

```bash
python scripts/build_field_map_pack.py \
  --pristine workspace/csr/FINALFANTASY7_D1.bin \
  --flavor-image workspace/csr-plus/FINALFANTASY7_D1.bin \
  --files FIELD/EALS_1.DAT \
  --pack-id csr-plus-scene-aerith-house-v0.1.0 \
  --disc 1 \
  --name "CSR+ scene — Aerith's house" \
  --group-label "CSR+ scene — Aerith's house" \
  --blurb "Adds the CSR+ trim of the Aerith's house cutscene on top of the CSR base." \
  --exclusive-group csr-plus-scene-aerith-house \
  --compatible-bases csr-v0.14.1
```
