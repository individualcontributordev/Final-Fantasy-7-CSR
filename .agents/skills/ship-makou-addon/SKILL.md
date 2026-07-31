---
name: ship-makou-addon
description: >-
  Build and publish a general Makou FIELD/*.DAT add-on for any stack base
  (clean, CSR, Highwind). Use for non-CSR+ scene map packs, multi-disc FIELD
  add-ons, or choosing exclusiveGroup vs free checkbox. Not for CSR+
  increments (ship-csr-plus-scene) or engine binary work (Modding research-new-mod).
---

# Ship a Makou FIELD add-on

**Runner:** Windows (Git Bash + local bins). Mac agent instructs only; optional post-publish verify of `builder/` JSON.

## 1. Scope check

| Edit type | Where |
|-----------|--------|
| Makou `FIELD/*.DAT` | **This skill** (CSR repo) |
| CSR+ trim from `cache/csr-plus` | `ship-csr-plus-scene` |
| Engine `FIELD.BIN` / `WORLD.BIN` (Ghidra) | Modding `research-new-mod` |

## 2. Choose stack base

| Goal | Diff baseline | `compatibleBases` |
|------|---------------|-------------------|
| On Unmodified | `pristine` | `clean` |
| On CSR | `cache/csr` | `csr-v0.14.1` (check manifest) |
| On Highwind | `cache/highwind` | `highwind-v0.1.1` |
| CSR+ scene | stop → `ship-csr-plus-scene` | `csr-v0.14.1` only |

Missing baseline bins → `apply_layer.py` pristine + published base layer (see `AGENTS.md`).

## 3. Multi-base strategy

- **One pack, multiple `compatibleBases`:** only if changed map **bytes are identical** when injected on each base.
- **Else:** per-base packs (same pattern as encounter density `-on-csr-*` / `-on-clean-*`).

## 4. Pipeline

```bash
# Diff
python3 scripts/list_changed_field_maps.py \
  --pristine <baseline-dir>/FINALFANTASY7_DN.bin \
  --patched <addon-dir>/FINALFANTASY7_DN.bin \
  -o temp/<name>-diff-dN.json

# Optional graph
python3 scripts/field_jump_graph.py \
  --image <addon-dir>/FINALFANTASY7_DN.bin \
  --changed temp/<name>-diff-dN.json \
  -o temp/<name>-graph-dN.json

# Build
python3 scripts/build_field_map_pack.py \
  --pristine <baseline-dir>/FINALFANTASY7_DN.bin \
  --edited-image <addon-dir>/FINALFANTASY7_DN.bin \
  --files FIELD/<MAP>.DAT \
  --pack-id <id>-v0.1.0 \
  --disc N \
  --name "..." --group-label "..." --blurb "..." \
  --no-exclusive-group \
  --compatible-bases <base-id>
```

Flags detail: `docs/ADDON_QUICK_REFERENCE.md`. Order of ops owned by this skill.

## 5. exclusiveGroup policy

| Situation | Flag |
|-----------|------|
| Independent option / free scene | `--no-exclusive-group` (omit key → checkbox) |
| Mutually exclusive variants | `--exclusive-group <shared-id>` (dropdown) |

## 6. Multi-disc

Same `--pack-id`, re-run with `--disc 2` or `--disc 3`.

## 7. Verify (required before publish)

**Builder config stack** (site-equivalent; always run):

```bash
python3 scripts/verify_builder_config.py \
  --pristine pristine/FINALFANTASY7_DN.bin \
  --disc N \
  --base <compatibleBase-id> \
  --addon <pack-id>
# PASS required. Fails if disc missing, wrong compatibleBases, or bad layer.
```

Optional: `apply_layer … --expect` against the Makou image when you need byte-identical maps (see `docs/CREATE_ADDON_FROM_MAKOU.md`).

## 8. Ship

Commit `builder/<pack-id>/` + `manifest.json` (+ changelog if you keep one). Human playtest = one atomic task; **check results**.

## Do not

- Default invent `exclusiveGroup` for free options
- Diff CSR+ scenes against pristine
- Put Highwind-only edits on `compatibleBases: csr-v0.14.1` without verifying bytes
- Engine patches in this repo
