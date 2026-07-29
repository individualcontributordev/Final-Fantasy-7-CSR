---
name: ship-makou-addon
description: >-
  Build and publish a general Makou FIELD/*.DAT add-on for any stack base
  (clean, CSR, Highwind). Use for non-CSR+ scene map packs, multi-disc FIELD
  add-ons, or choosing exclusiveGroup vs free checkbox. Not for CSR+
  increments (ship-csr-plus-scene) or engine binary work (Modding research-new-mod).
---

# Ship a Makou FIELD add-on

## 1. Scope check

| Edit type | Where |
|-----------|--------|
| Makou `FIELD/*.DAT` | **This skill** (CSR repo) |
| CSR+ trim from `workspace/csr-plus` | `ship-csr-plus-scene` |
| Engine `FIELD.BIN` / `WORLD.BIN` (Ghidra) | Modding `research-new-mod` |

## 2. Choose stack base

| Goal | Diff baseline | `compatibleBases` |
|------|---------------|-------------------|
| On Unmodified | `workspace/pristine` | `clean` |
| On CSR | `workspace/csr` | `csr-v0.14.1` (check manifest) |
| On Highwind | `workspace/csr-plusplus` | `csr-plusplus-v0.1.1` |
| CSR+ scene | stop → `ship-csr-plus-scene` | `csr-v0.14.1` only |

Missing baseline bins → `apply_layer.py` pristine + published base layer (see `AGENTS.md`).

## 3. Multi-base strategy

- **One pack, multiple `compatibleBases`:** only if changed map **bytes are identical** when injected on each base.
- **Else:** per-base packs (same pattern as encounter density `-on-csr-*` / `-on-clean-*`).

## 4. Pipeline

```bash
# Diff
python3 scripts/list_changed_field_maps.py \
  --pristine workspace/<baseline>/FINALFANTASY7_DN.bin \
  --patched workspace/<addon>/FINALFANTASY7_DN.bin \
  --flavor <name> -o workspace/<name>-diff-dN.json

# Optional graph
python3 scripts/field_jump_graph.py \
  --image workspace/<addon>/FINALFANTASY7_DN.bin \
  --changed workspace/<name>-diff-dN.json \
  -o workspace/<name>-graph-dN.json

# Build
python3 scripts/build_field_map_pack.py \
  --pristine workspace/<baseline>/FINALFANTASY7_DN.bin \
  --flavor-image workspace/<addon>/FINALFANTASY7_DN.bin \
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

## 7. Verify

Stack base layer (if not already the workspace baseline) then addon with `--expect` against Makou image. See `docs/CREATE_ADDON_FROM_MAKOU.md` §5.

## 8. Ship

Commit `builder/<pack-id>/` + `manifest.json` (+ changelog if you keep one). Human playtest = one atomic task; **check results**.

## Do not

- Default invent `exclusiveGroup` for free options
- Diff CSR+ scenes against pristine
- Put Highwind-only edits on `compatibleBases: csr-v0.14.1` without verifying bytes
- Engine patches in this repo
