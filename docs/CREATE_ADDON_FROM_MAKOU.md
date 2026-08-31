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
| CSR+ **scene** add-on | `cache/csr` | `csr` |
| Add-on on CSR | `cache/csr` | `csr` |
| Add-on on Unmodified | `pristine` | `clean` |
| Add-on on Highwind only | `cache/highwind` | `highwind` |

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
  --compatible-bases csr
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
  --base csr \
  --addon my-addon-scene-v0.1.0
```

Expect: `PASS — builder config applies cleanly`.

Optional Makou byte expect:

```bash
mkdir -p temp
python3 scripts/apply_layer.py \
  pristine/FINALFANTASY7_D1.bin \
  builder/csr/layers/disc1.layer.json \
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

## Collapsed single-disc bases (csr-plus, highwind)

`csr-plus` and `highwind` are not addons — they are **bases** whose entire
Disc 2/Disc 3 field content has been merged onto a single Disc 1 image, so
players never swap discs. This is a different workflow from the addon
pipeline above and lives in `Final-Fantasy-7-Modding`, not this repo.

**Script:** `Final-Fantasy-7-Modding/mods/single-disc/scripts/build_collapsed_bases.py`

What it does per base (see the script's module docstring for the exact
step order): merges safe D2/D3→D1 field files, applies any base-specific
patches (JUNAIR precision fix, BLACKBGB ask-removal, CSR+ scene trims),
runs `fix_field_and_world_bins()` (**required** — see the "Invalid archive"
row in `docs/reference/layer-engineering.md`'s failure-modes table; this
step resizes many `FIELD/*.DAT` files in one pass), injects SNOVA D3→D1,
then diffs the result against pristine Disc 1 and writes
`builder/<base>/layers/disc1.layer.json` plus updates that base's
`discs` entry in `pack.json` and `builder/manifest.json` to `{"1": ...}`
only (deleting any stale `disc2.layer.json`/`disc3.layer.json`).

```bash
cd /path/to/Final-Fantasy-7-Modding
python3 mods/single-disc/scripts/build_collapsed_bases.py
# or, if csr-plus's intermediate .bin is already cached:
python3 mods/single-disc/scripts/build_collapsed_bases.py --skip-csrplus
```

**COLLISION warnings** (`differs on [2, 3]`) mean a field's D2 and D3
copies both diverge from D1 *and* from each other — the script skips these
rather than guessing which disc's version should win. Resolve manually
(edit the field, or decide which disc source is correct) before
considering the base's D2/D3 merge complete; a collision means that
scene's content on the collapsed disc is still whatever D1 already had,
which may be stale in the collapsed image.

**Publish:** same as any base — commit `builder/<base>/layers/disc1.layer.json`,
`builder/<base>/pack.json`, and `builder/manifest.json` in this repo, then
`git push`.

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
  --compatible-bases csr
```

History: `notes/2026-07-28-csr-plus-increment-pivot.md` (not the runbook).
