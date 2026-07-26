# Windows (Git Bash): build CSR base layers for the disc builder

Use **Git Bash** on the PC that has pristine discs and your CSR-patched images.

## Quick path (recommended)

One command per base. Point at the workspace folder and set the version:

```bash
cd /c/path/to/Final-Fantasy-7-CSR   # or ~/Final-Fantasy-7-CSR
git pull

# CSR — every disc pair that exists under pristine/ + this folder
python scripts/build_csr_base_layers.py workspace/csr --version 0.14.0

# CSR+
python scripts/build_csr_base_layers.py workspace/csr-plus --version 0.1.0

# CSR++
python scripts/build_csr_base_layers.py workspace/csr-plusplus --version 0.1.0

# Only Disc 1:
python scripts/build_csr_base_layers.py workspace/csr --version 0.14.0 --discs 1
```

The script will:

1. Diff `workspace/pristine/FINALFANTASY7_DN.bin` vs `<base>/FINALFANTASY7_DN (patched).bin`
2. Write `builder/<slug>-v<version>/layers/discN.layer.json`
3. Verify each layer applies cleanly
4. Update that pack’s `pack.json` and set `"enabled": true` in `builder/manifest.json`

Then commit **JSON only** and push:

```bash
git add builder/
git status   # confirm no .bin/.cue
git commit -m "Add CSR builder layers."
git push
```

---

## Expected files

| Role | Path |
|------|------|
| Pristine Disc N | `workspace/pristine/FINALFANTASY7_DN.bin` (+ `.cue`) |
| CSR | `workspace/csr/FINALFANTASY7_DN (patched).bin` |
| CSR+ | `workspace/csr-plus/FINALFANTASY7_DN (patched).bin` |
| CSR++ | `workspace/csr-plusplus/FINALFANTASY7_DN (patched).bin` |

Prefer **forward slashes**. Quote paths with spaces if you run the low-level scripts by hand.

---

## Manual commands (optional)

Same as what `build_csr_base_layers.py` runs under the hood — see `notes.md` for past examples.

```bash
python scripts/bin_diff_to_layer.py \
  "workspace/pristine/FINALFANTASY7_D1.bin" \
  "workspace/csr/FINALFANTASY7_D1 (patched).bin" \
  -o builder/csr-v0.14.0/layers/disc1.layer.json \
  --id csr-disc1-v0.14.0 \
  --description "CSR v0.14.0 — NTSC-U Disc 1"

python scripts/apply_layer.py \
  "workspace/pristine/FINALFANTASY7_D1.bin" \
  builder/csr-v0.14.0/layers/disc1.layer.json \
  --expect "workspace/csr/FINALFANTASY7_D1 (patched).bin"
```

---

## Size warning

CSR layers are large (~13MB JSON / disc). Browser download may be slow. Disc 1 first is fine.

---

## Encounter add-on

Built in **Final-Fantasy-7-Modding** — see that repo’s `builder/WINDOWS-INSTRUCTIONS.md`.

- Retail Encounter → Unmodified base only  
- CSR / CSR+ / CSR++ each need their **own** Encounter layer (`--against csr|csr-plus|csr-plusplus`), built from the patched images in this repo’s `workspace/csr*` folders  
