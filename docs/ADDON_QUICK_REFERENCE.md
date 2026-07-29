# Add-on Creation Quick Reference

Fast commands for creating builder add-ons from Makou Reactor edits.

**Note:** These commands work in Git Bash (Windows) and Zsh/Bash (Mac/Linux). On Windows Git Bash, use `python` instead of `python3`.

## Setup

```bash
cd /path/to/Final-Fantasy-7-CSR/workspace
mkdir my-addon
cp /path/to/edited/FINALFANTASY7_D1.bin my-addon/
cd /path/to/Final-Fantasy-7-CSR
```

## Find changed maps

```bash
python scripts/list_changed_field_maps.py \
  --pristine workspace/csr/FINALFANTASY7_D1.bin \
  --patched workspace/my-addon/FINALFANTASY7_D1.bin \
  --flavor my-addon \
  -o workspace/my-addon-diff.json
```

Output shows which FIELD/*.DAT files changed.

## Build add-on

```bash
python scripts/build_field_map_pack.py \
  --pristine workspace/csr/FINALFANTASY7_D1.bin \
  --flavor-image workspace/my-addon/FINALFANTASY7_D1.bin \
  --files FIELD/MAP1.DAT FIELD/MAP2.DAT \
  --pack-id my-addon-v0.1.0 \
  --disc 1 \
  --name "Display Name" \
  --group-label "Display Name" \
  --blurb "Short description." \
  --exclusive-group my-addon \
  --compatible-bases csr-v0.14.1
```

**Change `--compatible-bases clean` if you edited against pristine/Unmodified instead of CSR.**

## Verify

```bash
# Reconstruct CSR base
python scripts/apply_layer.py \
  workspace/pristine/FINALFANTASY7_D1.bin \
  builder/csr-v0.14.1/layers/disc1.layer.json \
  -o temp/csr-base.bin

# Apply addon and verify
python scripts/apply_layer.py \
  temp/csr-base.bin \
  builder/my-addon-v0.1.0/layers/disc1.layer.json \
  --expect workspace/my-addon/FINALFANTASY7_D1.bin
```

Should output: `Output matches expected image exactly.`

## Publish

```bash
git add builder/my-addon-v0.1.0/ builder/manifest.json
git commit -m "Add my-addon-v0.1.0."
git push origin main
```

Live at https://individualcontributor.dev/builder/ in ~2 minutes.

---

## Common Scenarios

### Editing against CSR base
Most common - you start with a CSR disc and make changes:
- `--pristine workspace/csr/FINALFANTASY7_D1.bin`
- `--compatible-bases csr-v0.14.1`

### Editing against Unmodified/pristine
You start with a clean retail disc:
- `--pristine workspace/pristine/FINALFANTASY7_D1.bin`
- `--compatible-bases clean`

### Editing against Highwind
You start with Highwind and make changes:
- `--pristine workspace/csr-plusplus/FINALFANTASY7_D1.bin`
- `--compatible-bases csr-plusplus-v0.1.1`

### Multi-disc addon
Run `build_field_map_pack.py` once per disc with `--disc 2` or `--disc 3`.
Pack ID stays the same, it updates `pack.json` to add discs 2/3.

---

## Base IDs (for --compatible-bases)

| Base | ID |
|------|-----|
| Unmodified | `clean` |
| CSR | `csr-v0.14.1` |
| Highwind | `csr-plusplus-v0.1.1` |

Check latest in `builder/manifest.json` → `bases[].id`

---

## Troubleshooting

**"new file is X bytes but ISO slot is Y"**
- Map grew too much. The ISO9660 patch handles growth within the same sector span.
- If it truly needs more sectors, you need a full ISO rebuild (not supported by layer system).

**Mismatch at offset X**
- Your addon layer doesn't reproduce the Makou disc exactly.
- Re-run `build_field_map_pack.py` with correct `--pristine` base.
- Check you listed all changed maps in `--files`.

**"Module not found"**
- Run from repo root: `cd /path/to/Final-Fantasy-7-CSR`
- Scripts use relative imports.

---

## File Paths Reference

| Path | What |
|------|------|
| `workspace/pristine/` | Retail NTSC-U discs (never edit) |
| `workspace/csr/` | CSR base discs (built from pristine + CSR layers) |
| `workspace/csr-plus/` | CSR+ discs (built from pristine + CSR + CSR+ layers) |
| `workspace/csr-plusplus/` | Highwind discs |
| `workspace/my-addon/` | Your edited discs from Makou Reactor |
| `builder/csr-v0.14.1/` | Published CSR base layers |
| `builder/my-addon-v0.1.0/` | Your new addon (created by script) |
| `builder/manifest.json` | Builder catalog (auto-updated by script) |

---

## See Also

- Full guide: `docs/CREATE_ADDON_FROM_MAKOU.md`
- CSR+ scene addon example: `notes/2026-07-28-csr-plus-increment-pivot.md`
- Field map tools: `scripts/list_changed_field_maps.py`, `field_jump_graph.py`
