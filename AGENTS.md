# CSR — Agent guide

Cutscene-removed **bases** + CSR+ **scene add-ons** for the disc builder. Players: https://individualcontributor.dev/builder/.

| Repo | Role |
|------|------|
| `individualcontributordev.github.io` | Player site + builder UI |
| **This repo** | CSR base + Highwind base + CSR+ scene add-ons (Pages CDN) |
| `Final-Fantasy-7-Modding` | Engine/RE + encounter density packs |

## How we work

- **Windows (human):** runs **all** ops — Makou, disc images, DuckStation, Git Bash, every `python scripts/…`, builds, commits, pushes, publish.
- **Mac (this chat):** agent only — **commits Windows tasks into the repo first** (`docs/windows-last-task.md` + scripts), short chat pointer. Does **not** run release scripts as the real path (bins live on Windows).
- One atomic Windows task per reply; user says **check** / **check results**.
- On **check**: Mac `git pull`s and reviews **what was committed in the repo**, then next steps. Live builder/CDN verify only when explicitly requested at end of flow.
- Never give a Windows runbook that exists only in chat (see `.agents/rules/mac-human-workflow.mdc`).
- Never commit `.bin` / `.cue`. Never ask to paste large outputs into chat.
- `git pull --ff-only` before acting (both sides).
- Commits: author `individualcontributordev <contributorindividual@gmail.com>`; no Cursor trailers. Agent may auto commit/push **doc/skill** edits from Mac; **builder/base releases** are committed from Windows after scripts succeed. See `.agents/rules/mac-human-workflow.mdc`.

## Workflows (pick a skill)

| ID | Workflow | Skill |
|----|----------|--------|
| A | CSR base update → build → release | `.agents/skills/release-csr-base` (target **CSR**) |
| B | CSR+ scene add-on (new **or update**) → build → release | `.agents/skills/ship-csr-plus-scene` (`scripts/update_addon_from_builder_zip.py` for updates from a builder zip) |
| C | Highwind base update → build → release | `.agents/skills/release-csr-base` (target **Highwind**) |
| D | General Makou FIELD add-on | `.agents/skills/ship-makou-addon` |
| D′ | Engine binary (Ghidra) | **Modding** `research-new-mod` |

Short flags: `docs/ADDON_QUICK_REFERENCE.md`. Full Makou guide: `docs/CREATE_ADDON_FROM_MAKOU.md`. Player + thin maintainer: root `README.md`.

## Product rules

- **Bases in builder:** Unmodified (`clean`), **CSR** (`csr-v0.14.1`), **Highwind** (`highwind-v0.1.1`).
- **CSR+** is **not** a base. Extra trims ship as `csr-plus-scene-*` add-ons on `csr-v0.14.1` only.
- **Highwind** = separate aggressive mod, not a bigger CSR+. Does **not** stack with CSR+ scene add-ons.
- Free independent scenes: **omit** `exclusiveGroup` (builder → checkbox). Set `exclusiveGroup` only for mutually exclusive variants.
- Diff **bases** against **pristine**. Diff **CSR+ scenes** against **CSR baseline** (published CSR layer / cache), not pristine.
- Multi-base general add-ons: multiple `compatibleBases` only if bytes are identical on each base; else **per-base packs**.

| Goal | Diff baseline | compatibleBases |
|------|---------------|-----------------|
| CSR / Highwind **base** release | `pristine/` | n/a (`kind=base`) |
| CSR+ **scene** add-on | CSR image (layer or `cache/csr`) | `csr-v0.14.1` |
| Add-on on Unmodified | `pristine/` | `clean` |
| Add-on on Highwind only | Highwind image | `highwind-v0.1.1` |

Changelogs: index [CHANGELOGS.md](CHANGELOGS.md) — bases in `bases/<name>/`, CSR+ scenes in `addons/csr-plus/`.

## Mental model (local discs)

```text
pristine/                 retail ground truth (store once)
builder zip .bin          session working disc (edit in Makou)
builder/                  published layers (git)
cache/csr|highwind|…      optional reconstructed bases — not the workflow owner
workspace/                LEGACY name for cache/pristine (scripts still accept it)
```

Session work: site builder → unzip → Makou → `update_addon_from_builder_zip.py` (scenes)
or `build_csr_base_layers.py <edited-folder>` (bases). Do **not** treat cache as the product.

## Optional cache (reconstruct published base)

```bash
mkdir -p cache/csr cache/highwind
python3 scripts/apply_layer.py \
  pristine/FINALFANTASY7_D1.bin \
  builder/csr-v0.14.1/layers/disc1.layer.json \
  -o cache/csr/FINALFANTASY7_D1.bin
# Disc 2/3 and Highwind: same pattern
```

Prefer a **builder zip** (CSR-only / Highwind-only) as the Makou starting image when editing bases. Cache only speeds repeats. Never publish `cache/csr-plus` as a base — CSR+ scenes use `ship-csr-plus-scene`.

## Paths

| What | Where |
|------|--------|
| Pristine discs | `pristine/FINALFANTASY7_DN.bin` |
| Optional base cache | `cache/csr/`, `cache/highwind/` |
| Session edits | builder zip extract (e.g. Downloads) |
| Published layers | `builder/<slug>-v<ver>/` + `builder/manifest.json` |
| Skills | `.agents/skills/*` |
| Windows task handoff | `docs/windows-last-task.md` |
| Builder config verify | `scripts/verify_builder_config.py` (required before publish) |
| Path helper | `scripts/local_paths.py` |

## After a CSR / Highwind base id changes

Rebuild Field/World encounter packs in **Final-Fantasy-7-Modding** (`ship-field-encounters` / `ship-world-encounters`) so `compatibleBases` match the new ids.

## Auggie layout

| Path | Role |
|------|------|
| **`.agents/rules/`**, **`.agents/skills/`** | **Canonical copies** in this repo — edit only here |
| **`.augment/rules`**, **`.augment/skills`** | Relative symlinks → `../.agents/rules` / `../.agents/skills` (Auggie load path) |

No machine-absolute paths. Windows **Git Bash**: `git config --global core.symlinks true`, then `git checkout -- .augment`; if still plain text, `cd .augment && rm -rf rules skills && ln -s ../.agents/rules rules && ln -s ../.agents/skills skills`. Do not duplicate content under `.augment/`. Full steps: Modding `docs/windows-last-task.md` when that task is active, or this section.

## Repo hygiene

- Pages publishes only redirect `index.html` + `builder/`.
- No PPF / RomPatcher / WINDOWS-INSTRUCTIONS sprawl.
- Builder blurbs stay short; Highwind wording = separate mod, not CSR+.
- Skills own checklists; keep this file as an index.
