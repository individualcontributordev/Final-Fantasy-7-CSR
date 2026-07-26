# Windows (Git Bash): build CSR base layers for the disc builder

## This release

| Base | Version | Builder id | PPF short name |
|------|---------|------------|----------------|
| CSR | `0.14.1` | `csr-v0.14.1` | `patcher/csr-discN-v0.14.1.ppf` |
| CSR+ | `0.1.1` | `csr-plus-v0.1.1` | `patcher/csrplus-discN-v0.1.1.ppf` |
| CSR++ | `0.1.1` | `csr-plusplus-v0.1.1` | `patcher/csrplusplus-discN-v0.1.1.ppf` |

## Rebuild layers from your patched images

```bash
cd /c/path/to/Final-Fantasy-7-CSR
git pull

python scripts/build_csr_base_layers.py workspace/csr --version 0.14.1
python scripts/build_csr_base_layers.py workspace/csr-plus --version 0.1.1
python scripts/build_csr_base_layers.py workspace/csr-plusplus --version 0.1.1
```

Needs:

| Role | Path |
|------|------|
| Pristine Disc N | `workspace/pristine/FINALFANTASY7_DN.bin` |
| CSR | `workspace/csr/FINALFANTASY7_DN (patched).bin` |
| CSR+ | `workspace/csr-plus/… (patched).bin` |
| CSR++ | `workspace/csr-plusplus/… (patched).bin` |

## PPFs + site

Long names under `csr/`, `csr+/`, `csr++/` and short names under `patcher/` must match the versions above. `index.html` `PATCHES` entries must point at the short names.

If you regenerate PPFs from pristine→patched, overwrite those files; then:

```bash
git add builder/ csr/ csr+/ csr++/ patcher/ index.html
git status
git commit -m "Release CSR v0.14.1, CSR+ v0.1.1, CSR++ v0.1.1."
git push
```

Wait for Pages, then build Encounter in **Final-Fantasy-7-Modding** (`builder/WINDOWS-INSTRUCTIONS.md`).
