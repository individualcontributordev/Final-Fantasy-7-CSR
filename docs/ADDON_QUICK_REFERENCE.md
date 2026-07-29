# Add-on Creation Quick Reference

Fast commands for **Makou** `FIELD/*.DAT` add-ons. Engine/Ghidra → Modding `docs/06-new-mod-research.md`.

Skills: `ship-makou-addon`, `ship-csr-plus-scene`. Full guide: `docs/CREATE_ADDON_FROM_MAKOU.md`.

## Baselines

| Goal | `--pristine` (diff baseline) | `--compatible-bases` |
|------|------------------------------|----------------------|
| CSR+ scene | `workspace/csr/...` | `csr-v0.14.1` |
| On CSR | `workspace/csr/...` | `csr-v0.14.1` |
| On Unmodified | `workspace/pristine/...` | `clean` |
| On Highwind | `workspace/csr-plusplus/...` | `csr-plusplus-v0.1.1` |

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

## Verify

```bash
mkdir -p temp
python3 scripts/apply_layer.py \
  workspace/pristine/FINALFANTASY7_D1.bin \
  builder/csr-v0.14.1/layers/disc1.layer.json \
  -o temp/csr-base.bin

python3 scripts/apply_layer.py \
  temp/csr-base.bin \
  builder/my-addon-v0.1.0/layers/disc1.layer.json \
  --expect workspace/my-addon/FINALFANTASY7_D1.bin
```

Expect: `Output matches expected image exactly.`

## Publish

```bash
git add builder/my-addon-v0.1.0/ builder/manifest.json
git commit -m "Add my-addon-v0.1.0."
git push origin main
```

## Multi-disc / multi-base

- Multi-disc: same `--pack-id`, `--disc 2` or `--disc 3`.
- Multi-base: multiple `--compatible-bases` only if bytes match on each; else per-base packs.

## Base IDs

| Base | ID |
|------|-----|
| Unmodified | `clean` |
| CSR | `csr-v0.14.1` |
| Highwind | `csr-plusplus-v0.1.1` |

Latest: `builder/manifest.json` → `bases[].id`. CSR+ is **not** a base.

## Paths

| Path | What |
|------|------|
| `workspace/pristine/` | Retail NTSC-U (never edit masters carelessly) |
| `workspace/csr/` | CSR base images |
| `workspace/csr-plus/` | CSR+ increment **source** (not a publish base) |
| `workspace/csr-plusplus/` | Highwind images |
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

