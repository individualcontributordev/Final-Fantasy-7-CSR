# CSR — Agent guide

Cutscene-removed bases for the disc builder. Players use https://individualcontributor.dev/builder/.

## How we work

- **Mac (this chat):** agent — give full Windows steps in chat; do not send the user hunting through docs.
- **Windows:** human — Makou / disc images / DuckStation / Git Bash.
- Never commit `.bin` / `.cue`. Never ask to paste large outputs; use `git` + short status.
- `git pull --ff-only` before acting.

## Day-to-day (also in README)

Release steps live in the **root README** (“Release a base”). Prefer that over inventing a second workflow.

Changelogs: `bases/csr/CHANGELOG.md`, `bases/csr-plus/CHANGELOG.md`, `bases/csr-plusplus/CHANGELOG.md` — update when shipping that base.

## Paths

| What | Where |
|------|--------|
| Pristine discs | `workspace/pristine/FINALFANTASY7_DN.bin` |
| Patched CSR images | `workspace/csr/`, `workspace/csr-plus/`, `workspace/csr-plusplus/` |
| Published layers | `builder/<slug>-v<ver>/` + `builder/manifest.json` |
| Build script | `scripts/build_csr_base_layers.py` |

## After a CSR base id changes

Tell the user to rebuild Field encounters in **Final-Fantasy-7-Modding** so add-ons stay compatible with the new `csr-*-vX.Y.Z` ids.

## Repo hygiene

- Pages workflow publishes only `index.html` redirect + `builder/`.
- No PPF / RomPatcher. No `WINDOWS-INSTRUCTIONS.md` — root README is enough for humans.
