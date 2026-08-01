# Task: CSR+ disc 3 endgame FD pack (new)

**Goal:** Ship a new **CSR+ checkbox** pack that trims the **disc 3 endgame FD-related**
scene(s) on **CSR only** (same pattern as Hojo FD / CoTA FD).
**Not** a CSR base change. **Not** Highwind.

**Suggested pack id:** `csr-plus-scene-endgame-fd-manip-v0.1.0`
(rename stem if you prefer — keep `csr-plus-scene-` prefix + `-v0.1.0`)

**Disc:** 3 only
**Base:** `csr-v0.14.1`
**Skill:** `.agents/skills/ship-csr-plus-scene` → **New scene**

Changelog **must** note any **List / FD / manip** impact (same bar as CoTA).

After this pack ships and you say **check**, next scenes are separate tasks
(one pack at a time).

---

## Copy-paste

```bash
cd "$(git rev-parse --show-toplevel)"
git pull --ff-only
```

### 1. Builder → Makou (disc 3)

1. https://individualcontributor.dev/builder/
2. Pristine **disc 3** `.bin`
3. Base **CSR** only — **no** other packs/mods for the first ship of this scene
4. Build → unzip. Keep `.bin` + `APPLIED.txt` together
5. Open disc 3 `.bin` in Makou
6. Trim the **endgame FD** scene(s) only (very end of the run / FD-related)
7. Save back into the **same extract folder**
8. Note the **FIELD/*.DAT** map id(s) you changed (for `--files` / evidence)

### 2. List changed maps (CSR baseline → your edit)

Diff baseline = **CSR disc 3**, not pristine:

```bash
# If cache/csr/FINALFANTASY7_D3.bin is missing, populate once:
# python3 scripts/apply_layer.py \
#   pristine/FINALFANTASY7_D3.bin \
#   builder/csr-v0.14.1/layers/disc3.layer.json \
#   -o cache/csr/FINALFANTASY7_D3.bin

python3 scripts/list_changed_field_maps.py \
  --pristine cache/csr/FINALFANTASY7_D3.bin \
  --patched "/path/to/your-edited-extract/FINALFANTASY7_D3.bin" \
  -o temp/endgame-fd-field-diff-d3.json
```

### 3. Build pack (free checkbox)

```bash
python3 scripts/build_field_map_pack.py \
  --edited-image "/path/to/your-edited-extract/FINALFANTASY7_D3.bin" \
  --changed-maps temp/endgame-fd-field-diff-d3.json \
  --pack-id csr-plus-scene-endgame-fd-manip-v0.1.0 \
  --name "CSR+ Endgame FD manip" \
  --blurb "CSR+ trim of disc 3 endgame FD-related scene(s). Check changelog for List/FD impact."

# If auto map list is wrong, pass explicit maps, e.g.:
#   --files FIELD/SOME_MAP.DAT FIELD/OTHER.DAT
```

Confirm `builder/csr-plus-scene-endgame-fd-manip-v0.1.0/pack.json`:

- no `exclusiveGroup`
- `compatibleBases` includes every live `csr-v*` (at least `csr-v0.14.1`)
- `discs` has `"3"` only
- `kind` pack / enabled true

### 4. Preset + changelog

Edit `builder/manifest.json` preset `csr-plus` → add
`csr-plus-scene-endgame-fd-manip-v0.1.0` to its `addons` list
(with Aerith / Hojo / CoTA).

`addons/csr-plus/CHANGELOG.md` — newest at top:

```markdown
## 2026-08-01

- csr-plus-scene-endgame-fd-manip-v0.1.0 (disc 3): <what you cut>. FD/List: <impact or none>.
```

### 5. Verify (required)

```bash
python3 scripts/verify_builder_config.py \
  --pristine pristine/FINALFANTASY7_D3.bin \
  --disc 3 \
  --base csr-v0.14.1 \
  --addon csr-plus-scene-endgame-fd-manip-v0.1.0

python3 scripts/verify_csr_addon_compat.py
```

Optional playtest stack:

```bash
mkdir -p temp
python3 scripts/apply_layer.py \
  pristine/FINALFANTASY7_D3.bin \
  builder/csr-v0.14.1/layers/disc3.layer.json \
  -o temp/csr-d3.bin
python3 scripts/apply_layer.py \
  temp/csr-d3.bin \
  builder/csr-plus-scene-endgame-fd-manip-v0.1.0/layers/disc3.layer.json \
  -o temp/play-d3.bin
```

### 6. Commit + push (Windows)

```bash
git add builder/ addons/csr-plus/CHANGELOG.md
git status -sb
git commit -m "Ship csr-plus-scene-endgame-fd-manip-v0.1.0 (disc 3 FD)."
git push
git status -sb
```

---

## Evidence (paths / PASS lines — not huge logs)

- FIELD maps in pack:
- verify_builder_config:
- verify_csr_addon_compat:
- FD/List note (changelog line):
- commit:

## After Mac **check**

Next CSR+ scene (your call): name + disc → new task.
