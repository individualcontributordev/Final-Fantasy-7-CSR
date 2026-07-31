# Creating Add-ons from Makou Reactor Edits

Complete workflow for turning **Makou Reactor field map edits** into builder add-on packs.

**Scope:** `FIELD/*.DAT` via Makou. **Engine binary** (`FIELD.BIN` / `WORLD.BIN`, Ghidra) → `Final-Fantasy-7-Modding` (`research-new-mod`, `docs/06-new-mod-research.md`).

Agent checklists: `ship-makou-addon` (general), `ship-csr-plus-scene` (CSR+ increments). Flags: `docs/ADDON_QUICK_REFERENCE.md`.

## Prerequisites

- Makou Reactor; this repo; Python 3
- Baseline disc image for the stack you target (see table)

## Choose baseline

| Goal | Diff baseline (`--pristine` / inject base) | `compatibleBases` |
|------|--------------------------------------------|-------------------|
| CSR+ **scene** add-on | `cache/csr` | `csr-v0.14.1` |
| Add-on on CSR | `cache/csr` | `csr-v0.14.1` |
| Add-on on Unmodified | `pristine` | `clean` |
| Add-on on Highwind only | `cache/highwind` | `highwind-v0.1.1` |

Multi-base: one pack with several `compatibleBases` **only if** map bytes are identical on each base; otherwise **per-base packs**.

Missing baseline bins → reconstruct via `apply_layer.py` (pristine + `builder/<base>/layers/discN.layer.json`). See `AGENTS.md`.

## exclusiveGroup (checkbox vs dropdown)

| Case | What to do |
|------|------------|
| Independent free option (most CSR+ scenes) | `--no-exclusive-group` — **omit** key → builder checkbox |
| Mutually exclusive variants (e.g. density tiers) | `--exclusive-group <id>` → single-select dropdown |

Do **not** invent an exclusive group for free CSR+ scenes.

## Workflow

### 1. Edit in Makou Reactor

1. Open the correct baseline image (CSR / pristine / Highwind)
2. Edit field maps → **File → Save** into `temp/<your-folder> or a builder zip extract/FINALFANTASY7_DN.bin`

### 2. Identify changed maps

```bash
cd /path/to/Final-Fantasy-7-CSR

python3 scripts/list_changed_field_maps.py \
  --pristine cache/csr/FINALFANTASY7_D1.bin \
  --patched temp/my-addon-name/FINALFANTASY7_D1.bin \
  -o temp/my-addon-field-diff.json
```

`--pristine` here means **diff baseline**, not always retail pristine.

### 3. (Optional) Jump graph

Real CLI needs `--image` + `--changed`:

```bash
python3 scripts/field_jump_graph.py \
  --image temp/my-addon-name/FINALFANTASY7_D1.bin \
  --changed temp/my-addon-field-diff.json \
  -o temp/my-addon-graph.json
```

One connected component ⇒ one pack. Multiple components ⇒ consider split packs.

### 4. Build the pack

Free checkbox (default recommendation for independent scenes):

```bash
python3 scripts/build_field_map_pack.py \
  --pristine cache/csr/FINALFANTASY7_D1.bin \
  --edited-image temp/my-addon-name/FINALFANTASY7_D1.bin \
  --files FIELD/MIDEEL_1.DAT FIELD/MIDEEL_2.DAT FIELD/JUMIN.DAT \
  --pack-id my-addon-scene-v0.1.0 \
  --disc 1 \
  --name "My Scene Name" \
  --group-label "My Scene Name" \
  --blurb "Brief description of what this addon does." \
  --no-exclusive-group \
  --compatible-bases csr-v0.14.1
```

Mutually exclusive variants: replace `--no-exclusive-group` with `--exclusive-group my-addon-scene`.

**Flags:**
- `--pristine` — inject/diff baseline image
- `--edited-image` — Makou-edited disc
- `--files` — changed `FIELD/*.DAT`
- `--pack-id` — unique id with version
- `--disc` — 1 / 2 / 3 (same pack-id across discs)
- `--compatible-bases` — which builder bases show this add-on
- `--no-exclusive-group` / `--exclusive-group` — checkbox vs dropdown

**Output:** `builder/<pack-id>/pack.json`, `layers/discN.layer.json`, updates `builder/manifest.json`.

Map growth within the same ISO sector span is allowed (`replace_file` patches the directory size). Growth needing more sectors still errors.

### 5. Verify (required)

**Builder config** (same stack as the site — always run before publish):

```bash
python3 scripts/verify_builder_config.py \
  --pristine pristine/FINALFANTASY7_D1.bin \
  --disc 1 \
  --base csr-v0.14.1 \
  --addon my-addon-scene-v0.1.0
```

Expect: `PASS — builder config applies cleanly`.

Optional Makou byte expect:

```bash
mkdir -p temp
python3 scripts/apply_layer.py \
  pristine/FINALFANTASY7_D1.bin \
  builder/csr-v0.14.1/layers/disc1.layer.json \
  -o temp/csr-base.bin

python3 scripts/apply_layer.py \
  temp/csr-base.bin \
  builder/my-addon-scene-v0.1.0/layers/disc1.layer.json \
  --expect temp/my-addon-name/FINALFANTASY7_D1.bin
```

### 6. Commit and publish

```bash
git add builder/my-addon-scene-v0.1.0/ builder/manifest.json
git commit -m "Add my-addon-scene-v0.1.0 addon."
git push origin main
```

Live via Pages in ~2 minutes.

## Tips

- **Multi-disc:** same `--pack-id`, run again with `--disc 2|3`
- **Playtest:** pristine → CSR base → enable add-on → DuckStation
- **Naming:** `<category>-<scene>-v<version>` (e.g. `csr-plus-scene-aerith-house-v0.1.0`)

## Example: CSR+ scene (free checkbox)

Checklist skill: `ship-csr-plus-scene`. Diff is **csr → csr-plus**, not pristine.

```bash
python3 scripts/build_field_map_pack.py \
  --pristine cache/csr/FINALFANTASY7_D1.bin \
  --edited-image cache/csr-plus/FINALFANTASY7_D1.bin \
  --files FIELD/EALS_1.DAT \
  --pack-id csr-plus-scene-aerith-house-v0.1.0 \
  --disc 1 \
  --name "CSR+ scene — Aerith's house" \
  --group-label "CSR+ scene — Aerith's house" \
  --blurb "CSR+ trim of the Aerith's house cutscene on top of CSR." \
  --no-exclusive-group \
  --compatible-bases csr-v0.14.1
```

History: `notes/2026-07-28-csr-plus-increment-pivot.md` (not the runbook).
