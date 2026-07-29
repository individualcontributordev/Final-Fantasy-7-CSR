# CSR — Agent guide

Cutscene-removed **bases** for the disc builder. Players use https://individualcontributor.dev/builder/.

This repo is one part of the stack:

| Repo | Role |
|------|------|
| `individualcontributordev.github.io` | Player site + builder UI |
| **This repo** | CSR base + Highwind base + CSR+ scene add-ons (Pages CDN) |
| `Final-Fantasy-7-Modding` | Add-ons (e.g. Field encounter density) + RE notes |

## How we work

- **Mac (this chat):** agent — full Windows steps in chat; do not send the user hunting through docs.
- **Windows:** human — Makou / disc images / DuckStation / Git Bash.
- Never commit `.bin` / `.cue`. Never ask to paste large outputs into chat.
- `git pull --ff-only` before acting.
- Commits: author `individualcontributordev <contributorindividual@gmail.com>`; no Cursor trailers; auto commit/push when work lands.

## Base definitions (keep copy consistent)

Builder bases (published in `builder/manifest.json`): **Unmodified** (built into the site) and **CSR** — skill checks kept; FMVs/long sequences cut or shortened.

**CSR+** is no longer a monolithic base. Its extra trims are decomposed into individual `csr-plus-scene-*` add-ons (`compatibleBases: ["csr-v0.14.1"]`) so a CSR-base player can pick only the scenes they want beyond CSR. First one shipped: `csr-plus-scene-aerith-house`.

**Highwind** (`csr-plusplus-v0.1.1`) — an aggressively trimmed playthrough. Its own separate mod, not a bigger CSR+: some story mechanics, option choices, and complete dialogue removal. Selectable in the builder (`bases/csr-plusplus/`, `builder/csr-plusplus-v0.1.1/`) alongside Unmodified and CSR. Doesn't stack with CSR+ scene add-ons (different, incompatible edits to the same scenes).

Changelogs: `bases/csr|csr-plus|csr-plusplus/CHANGELOG.md` — update when shipping that base or a new CSR+ scene add-on. (The `csr-plusplus` directory name stays as-is; only the display name changed.)

## Building a CSR+ scene add-on

Diff `workspace/csr` vs `workspace/csr-plus` (not pristine) to find what CSR+ still changes beyond CSR, then build one addon per component with `compatibleBases: ["csr-v0.14.1"]`:

```bash
python scripts/list_changed_field_maps.py \
  --pristine workspace/csr/FINALFANTASY7_DN.bin \
  --patched workspace/csr-plus/FINALFANTASY7_DN.bin \
  --flavor csr-plus-increment -o workspace/csr-plus-increment-field-diff.json

python scripts/build_field_map_pack.py \
  --pristine workspace/csr/FINALFANTASY7_D1.bin \
  --flavor-image workspace/csr-plus/FINALFANTASY7_D1.bin \
  --files FIELD/<MAP>.DAT \
  --pack-id csr-plus-scene-<name>-v0.1.0 \
  --name "CSR+ scene — <Name>" --group-label "CSR+ scene — <Name>" \
  --blurb "..." --exclusive-group csr-plus-scene-<name> \
  --compatible-bases csr-v0.14.1
```

`build_field_map_pack.py` allows a patched map file to grow past the pristine byte count as long as it still fits the already-allocated ISO sector span — it patches the ISO9660 directory record's size field via `psx_mode2_iso.replace_file`. Growth needing more sectors still raises (real ISO rebuild required).

## Day-to-day

Release steps: **root README** (“Release a base”). Skill: `.cursor/skills/release-csr-base`.

```bash
python scripts/build_csr_base_layers.py workspace/csr --version X.Y.Z
# then builder/ + bases/<base>/CHANGELOG.md → commit → push
```

## Paths

| What | Where |
|------|--------|
| Pristine discs | `workspace/pristine/FINALFANTASY7_DN.bin` |
| Patched images | `workspace/csr/`, `workspace/csr-plus/`, `workspace/csr-plusplus/` |
| Published layers | `builder/<slug>-v<ver>/` + `builder/manifest.json` |
| Build script | `scripts/build_csr_base_layers.py` |
| Scene-pack prototype | `scripts/list_changed_field_maps.py`, `field_jump_graph.py`, `build_field_map_pack.py` |
| Empty workspace dirs | `.gitkeep` (not README.md) |

## After a CSR base id changes

Tell the user to rebuild Field encounters in **Final-Fantasy-7-Modding** so add-ons stay compatible with the new `csr-*-vX.Y.Z` ids.

## Repo hygiene

- Pages publishes only redirect `index.html` + `builder/`.
- No PPF / RomPatcher / WINDOWS-INSTRUCTIONS sprawl.
- Builder blurbs stay short; match homepage Highwind wording when editing copy.
