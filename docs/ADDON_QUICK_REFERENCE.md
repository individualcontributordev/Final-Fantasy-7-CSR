# Add-on Creation Quick Reference

Fast commands for **Makou** `FIELD/*.DAT` add-ons. Engine/Ghidra → Modding `docs/06-new-mod-research.md`.

Skills: `ship-makou-addon`, `ship-csr-plus-scene`. Full guide: `docs/CREATE_ADDON_FROM_MAKOU.md`.

## Baselines

| Goal | `--pristine` (diff baseline) | `--compatible-bases` |
|------|------------------------------|----------------------|
| CSR+ scene | `workspace/csr/...` | `csr-v0.14.1` |
| On CSR | `workspace/csr/...` | `csr-v0.14.1` |
| On Unmodified | `workspace/pristine/...` | `clean` |
| On Highwind | `workspace/highwind/...` | `highwind-v0.1.1` |

Missing bins: `apply_layer.py` pristine + `builder/<base-id>/layers/discN.layer.json` → `workspace/<flavor>/`.

## exclusiveGroup

| Intent | Flag |
|--------|------|
| Free checkbox (independent scenes) | `--no-exclusive-group` |
| Single-select dropdown (mutex variants) | `--exclusive-group <id>` |

## Find changed maps

```bash
python3 scripts/list_changed_field_maps.py \
  --pristine workspace/csr/FINALFANTASY7_D1.bin \
  --patched workspace/my-addon/FINALFANTASY7_D1.bin \
  --flavor my-addon \
  -o workspace/my-addon-diff.json
```

## Optional jump graph

```bash
python3 scripts/field_jump_graph.py \
  --image workspace/my-addon/FINALFANTASY7_D1.bin \
  --changed workspace/my-addon-diff.json \
  -o workspace/my-addon-graph.json
```

## Build add-on (free checkbox)

```bash
python3 scripts/build_field_map_pack.py \
  --pristine workspace/csr/FINALFANTASY7_D1.bin \
  --flavor-image workspace/my-addon/FINALFANTASY7_D1.bin \
  --files FIELD/MAP1.DAT FIELD/MAP2.DAT \
  --pack-id my-addon-v0.1.0 \
  --disc 1 \
  --name "Display Name" \
  --group-label "Display Name" \
  --blurb "Short description." \
  --no-exclusive-group \
  --compatible-bases csr-v0.14.1
```

## Verify (builder config — required)

```bash
python3 scripts/verify_builder_config.py \
  --pristine workspace/pristine/FINALFANTASY7_D1.bin \
  --disc 1 \
  --base csr-v0.14.1 \
  --addon my-addon-v0.1.0
```

Expect: `PASS — builder config applies cleanly`.

Optional map byte expect vs Makou image: `apply_layer.py` chain with `--expect` (see full guide).

## Publish

```bash
git add builder/my-addon-v0.1.0/ builder/manifest.json
git commit -m "Add my-addon-v0.1.0."
git push origin main
```

## Update an existing CSR+ scene

Skill detail: `ship-csr-plus-scene` → **Update existing**.

1. Makou-edit maps on CSR / `workspace/csr-plus` (scope = `pack.json` `files`).
2. Diff baseline remains **CSR** (`workspace/csr`), not pristine.
3. **Bump pack id** (`…-v0.1.0` → `…-v0.1.1`), rebuild with `build_field_map_pack.py`.
4. Disable/remove old id in `builder/manifest.json`; swap id in preset `csr-plus`.
5. `verify_builder_config.py --base csr-v0.14.1 --addon <new-id>` → PASS.
6. Changelog + commit `builder/` + push.

Do not overwrite a shipped pack id in place for a real release.

## Multi-disc / multi-base

- Multi-disc: same `--pack-id`, `--disc 2` or `--disc 3`.
- Multi-base: multiple `--compatible-bases` only if bytes match on each; else per-base packs.

## Base IDs

| Base | ID |
|------|-----|
| Unmodified | `clean` |
| CSR | `csr-v0.14.1` |
| Highwind | `highwind-v0.1.1` |

Latest: `builder/manifest.json` → `bases[].id`. CSR+ is **not** a base.

## Paths

| Path | What |
|------|------|
| `workspace/pristine/` | Retail NTSC-U (never edit masters carelessly) |
| `workspace/csr/` | CSR base images |
| `workspace/csr-plus/` | CSR+ increment **source** (not a publish base) |
| `workspace/highwind/` | Highwind images |
| `builder/<pack-id>/` | Published pack |
| `builder/manifest.json` | Builder catalog |

## Troubleshooting

- **ISO slot too small** — growth beyond allocated sectors needs a full ISO rebuild.
- **Mismatch at offset** — wrong baseline `--pristine`, or missing maps in `--files`.
- **Module not found** — run from repo root.

## Makou vs Ghidra

| | Makou (this repo) | Ghidra (Modding repo) |
|--|-------------------|------------------------|
| Files | `FIELD/*.DAT` | `FIELD.BIN` / `WORLD.BIN` |
| Example | CSR+ scene add-ons | Field encounter density |
| Skill | `ship-makou-addon` / `ship-csr-plus-scene` | `research-new-mod` |

