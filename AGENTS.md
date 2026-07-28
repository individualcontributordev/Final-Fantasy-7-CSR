# CSR — Agent guide

Cutscene-removed **bases** for the disc builder. Players use https://individualcontributor.dev/builder/.

This repo is one part of the stack:

| Repo | Role |
|------|------|
| `individualcontributordev.github.io` | Player site + builder UI |
| **This repo** | CSR / CSR+ / CSR++ base layers (Pages CDN) |
| `Final-Fantasy-7-Modding` | Add-ons (e.g. Field encounter density) + RE notes |

## How we work

- **Mac (this chat):** agent — full Windows steps in chat; do not send the user hunting through docs.
- **Windows:** human — Makou / disc images / DuckStation / Git Bash.
- Never commit `.bin` / `.cue`. Never ask to paste large outputs into chat.
- `git pull --ff-only` before acting.
- Commits: author `individualcontributordev <contributorindividual@gmail.com>`; no Cursor trailers; auto commit/push when work lands.

## Base definitions (keep copy consistent)

- **CSR** — skill checks kept; FMVs/long sequences cut or shortened.
- **CSR+** — more aggressive cutscene removal (can affect familiar strats).
- **CSR++** — very aggressively trimmed CSR+: some story mechanics, option choices, and complete dialogue removal.

Changelogs: `bases/csr|csr-plus|csr-plusplus/CHANGELOG.md` — update when shipping that base.

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
- Builder blurbs stay short; match homepage CSR++ wording when editing copy.
