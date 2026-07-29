# CSR — Agent guide

Cutscene-removed **bases** + CSR+ **scene add-ons** for the disc builder. Players: https://individualcontributor.dev/builder/.

| Repo | Role |
|------|------|
| `individualcontributordev.github.io` | Player site + builder UI |
| **This repo** | CSR base + Highwind base + CSR+ scene add-ons (Pages CDN) |
| `Final-Fantasy-7-Modding` | Engine/RE + encounter density packs |

## How we work

- **Mac (this chat):** agent — full Windows steps in chat; see `.agents/rules/mac-human-workflow.mdc`.
- **Windows:** human — Makou / disc images / DuckStation / Git Bash.
- One atomic Windows task per reply; user says **check results**.
- Never commit `.bin` / `.cue`. Never ask to paste large outputs into chat.
- `git pull --ff-only` before acting.
- Commits: author `individualcontributordev <contributorindividual@gmail.com>`; no Cursor trailers; auto commit/push when work lands.

## Workflows (pick a skill)

| ID | Workflow | Skill |
|----|----------|--------|
| A | CSR base update → build → release | `.agents/skills/release-csr-base` (target **CSR**) |
| B | CSR+ scene add-on → build → release | `.agents/skills/ship-csr-plus-scene` |
| C | Highwind base update → build → release | `.agents/skills/release-csr-base` (target **Highwind**) |
| D | General Makou FIELD add-on | `.agents/skills/ship-makou-addon` |
| D′ | Engine binary (Ghidra) | **Modding** `research-new-mod` |

Short flags: `docs/ADDON_QUICK_REFERENCE.md`. Full Makou guide: `docs/CREATE_ADDON_FROM_MAKOU.md`. Player + thin maintainer: root `README.md`.

## Product rules

- **Bases in builder:** Unmodified (`clean`), **CSR** (`csr-v0.14.1`), **Highwind** (`csr-plusplus-v0.1.1`).
- **CSR+** is **not** a base. Extra trims ship as `csr-plus-scene-*` add-ons on `csr-v0.14.1` only.
- **Highwind** = separate aggressive mod, not a bigger CSR+. Does **not** stack with CSR+ scene add-ons.
- Free independent scenes: **omit** `exclusiveGroup` (builder → checkbox). Set `exclusiveGroup` only for mutually exclusive variants.
- Diff **bases** against `workspace/pristine`. Diff **CSR+ scenes** against `workspace/csr` (not pristine).
- Multi-base general add-ons: multiple `compatibleBases` only if bytes are identical on each base; else **per-base packs**.

| Goal | Diff baseline | compatibleBases |
|------|---------------|-----------------|
| CSR / Highwind **base** release | `workspace/pristine` | n/a (`kind=base`) |
| CSR+ **scene** add-on | `workspace/csr` | `csr-v0.14.1` |
| Add-on on Unmodified | `workspace/pristine` | `clean` |
| Add-on on Highwind only | `workspace/csr-plusplus` | `csr-plusplus-v0.1.1` |

Changelogs: `bases/csr|csr-plus|csr-plusplus/CHANGELOG.md`.

## Workspace images missing?

Reconstruct published base images (no new dump):

```bash
mkdir -p workspace/csr workspace/csr-plusplus
python3 scripts/apply_layer.py \
  workspace/pristine/FINALFANTASY7_D1.bin \
  builder/csr-v0.14.1/layers/disc1.layer.json \
  -o workspace/csr/FINALFANTASY7_D1.bin
# Disc 2/3 and Highwind: same pattern with discN + csr-plusplus-v0.1.1
```

`workspace/csr-plus/` = Makou source for scene **increments** only. Do **not** run `build_csr_base_layers.py` on it for a normal publish.

## Paths

| What | Where |
|------|--------|
| Pristine discs | `workspace/pristine/FINALFANTASY7_DN.bin` |
| Patched images | `workspace/csr/`, `workspace/csr-plus/` (increment source), `workspace/csr-plusplus/` |
| Published layers | `builder/<slug>-v<ver>/` + `builder/manifest.json` |
| Skills | `.agents/skills/*` |
| Evidence (optional) | `docs/windows-last-output.txt` |

## After a CSR / Highwind base id changes

Rebuild Field/World encounter packs in **Final-Fantasy-7-Modding** (`ship-field-encounters` / `ship-world-encounters`) so `compatibleBases` match the new ids.

## Repo hygiene

- Pages publishes only redirect `index.html` + `builder/`.
- No PPF / RomPatcher / WINDOWS-INSTRUCTIONS sprawl.
- Builder blurbs stay short; Highwind wording = separate mod, not CSR+.
- Skills own checklists; keep this file as an index.
