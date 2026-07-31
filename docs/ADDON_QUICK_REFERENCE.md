# Add-on Creation Quick Reference

Fast commands for **Makou** `FIELD/*.DAT` add-ons. Engine/Ghidra → Modding `docs/06-new-mod-research.md`.

Skills: `ship-makou-addon`, `ship-csr-plus-scene`. Full guide: `docs/CREATE_ADDON_FROM_MAKOU.md`.

## Baselines

| Goal | `--pristine` (diff baseline) | `--compatible-bases` |
|------|------------------------------|----------------------|
| CSR+ scene | `cache/csr/...` | `csr-v0.14.1` |
| On CSR | `cache/csr/...` | `csr-v0.14.1` |
| On Unmodified | `pristine/...` | `clean` |
| On Highwind | `cache/highwind/...` | `highwind-v0.1.1` |

Missing bins: `apply_layer.py` pristine + `builder/<base-id>/layers/discN.layer.json` → `cache/<flavor>/` (optional), or start from a builder zip.

## exclusiveGroup

| Intent | Flag |
|--------|------|
| Free checkbox (independent scenes) | `--no-exclusive-group` |
| Single-select dropdown (mutex variants) | `--exclusive-group <id>` |

## Find changed maps

```bash
python3 scripts/list_changed_field_maps.py \
  --pristine cache/csr/FINALFANTASY7_D1.bin \
  --patched temp/my-addon/FINALFANTASY7_D1.bin \
  -o temp/my-addon-diff.json
```

## Optional jump graph

```bash
python3 scripts/field_jump_graph.py \
  --image temp/my-addon/FINALFANTASY7_D1.bin \
  --changed temp/my-addon-diff.json \
  -o temp/my-addon-graph.json
```

## Build add-on (free checkbox)

```bash
python3 scripts/build_field_map_pack.py \
  --pristine cache/csr/FINALFANTASY7_D1.bin \
  --edited-image temp/my-addon/FINALFANTASY7_D1.bin \
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
  --pristine pristine/FINALFANTASY7_D1.bin \
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

Skill: `ship-csr-plus-scene` → **Update existing**. Preferred tool:
`scripts/update_addon_from_builder_zip.py`.

1. Builder: pristine disc + **CSR** + **only** that scene add-on → zip → unzip.
2. Makou: open extract `.bin`, edit, save in the same folder (keep `APPLIED.txt`).
3. Rebuild (APPLIED-only config; default **patch** bump):

```bash
python3 scripts/update_addon_from_builder_zip.py "/path/to/extract-or.bin"
# python3 scripts/update_addon_from_builder_zip.py "/path/to/extract" --version 0.2.0
```

4. `verify_builder_config.py --base csr-v0.14.1 --addon <new-id>` → PASS.
5. Playtest layer stack (no site rebuild required):

```bash
mkdir -p temp
python3 scripts/apply_layer.py pristine/FINALFANTASY7_D1.bin \
  builder/csr-v0.14.1/layers/disc1.layer.json -o temp/csr-d1.bin
python3 scripts/apply_layer.py temp/csr-d1.bin \
  builder/<new-id>/layers/disc1.layer.json -o temp/play-d1.bin
```

6. Changelog in `addons/csr-plus/CHANGELOG.md` (or `addons/<family>/` for new families) + commit `builder/` + push. Index: `CHANGELOGS.md`.

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
| `pristine/` | Retail NTSC-U (never edit masters carelessly) |
| `cache/csr/` | CSR base images |
| `cache/csr-plus/` | CSR+ increment **source** (not a publish base) |
| `cache/highwind/` | Highwind images |
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

