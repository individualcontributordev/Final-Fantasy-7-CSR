# Windows: build CSR base layers for the disc builder

Do this on the PC that has pristine discs and your CSR-patched images.

Goal: one `ic-layer-v1` JSON per disc flavor (CSR / CSR+ / CSR++), Diffed from **pristine**.

These layers can be large (many field files). That is OK for a first cut; we may switch to file-packs later.

---

## 0. Setup

```bat
cd C:\path\to\Final-Fantasy-7-CSR
git pull
```

Python 3 on PATH. Keep images **outside** git (e.g. `D:\ff7\`).

You need, for each disc you ship:

| Role | Example path |
|------|----------------|
| Pristine Disc N | `D:\ff7\pristine\disc1.bin` |
| CSR Disc N | `D:\ff7\csr\disc1.bin` |
| CSR+ Disc N | `D:\ff7\csr+\disc1.bin` |
| CSR++ Disc N | `D:\ff7\csr++\disc1.bin` |

Use the same region (NTSC-U) everywhere.

---

## 1. Diff one flavor (example: CSR Disc 1)

```bat
cd C:\path\to\Final-Fantasy-7-CSR

python scripts\bin_diff_to_layer.py ^
  D:\ff7\pristine\disc1.bin ^
  D:\ff7\csr\disc1.bin ^
  -o builder\csr-v0.14.0\layers\disc1.layer.json ^
  --id csr-disc1-v0.14.0 ^
  --description "CSR v0.14.0 — NTSC-U Disc 1"
```

Adjust version folder / id to match the CSR version you are shipping.

### Verify

```bat
python scripts\apply_layer.py ^
  D:\ff7\pristine\disc1.bin ^
  builder\csr-v0.14.0\layers\disc1.layer.json ^
  --expect D:\ff7\csr\disc1.bin
```

Must print `OK — layer apply matches --expect`.

Repeat for Disc 2 / Disc 3 into the same pack folder (`disc2.layer.json`, `disc3.layer.json`).

---

## 2. CSR+ and CSR++

Same pattern into:

- `builder\csr-plus-v0.1.0\layers\discN.layer.json`  
- `builder\csr-plusplus-v0.1.0\layers\discN.layer.json`  

Update `pack.json` version strings if yours differ.

---

## 3. Enable in manifest

Edit `builder\manifest.json`:

- Set `"enabled": true` on packs that have real `disc*.layer.json` files  
- Remove or leave `enabled: false` for unfinished flavors  

---

## 4. Commit and push (JSON only)

```bat
git add builder scripts
git status
git commit -m "Add CSR builder layers for disc builder."
git push
```

Do **not** add `.bin` / `.cue`.

---

## 5. Size warning

If the script prints `WARNING: large layer`, the browser can still apply it, but download may be slow. Ship Disc 1 first if needed; tell the agent so the main builder can start with Disc 1 only.

---

## Encounter add-on

Built in **Final-Fantasy-7-Modding** — see that repo’s `builder\WINDOWS-INSTRUCTIONS.md`.
