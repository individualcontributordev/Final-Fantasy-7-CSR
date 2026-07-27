# Windows (Git Bash): build CSR base layers for the disc builder

## This release

| Base | Version | Builder id |
|------|---------|------------|
| CSR | `0.14.1` | `csr-v0.14.1` |
| CSR+ | `0.1.1` | `csr-plus-v0.1.1` |
| CSR++ | `0.1.1` | `csr-plusplus-v0.1.1` |

Players use https://individualcontributor.dev/builder/ (stackable layers).

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
| CSR | `workspace/csr/FINALFANTASY7_DN.bin` |
| CSR+ | `workspace/csr-plus/FINALFANTASY7_DN.bin` |
| CSR++ | `workspace/csr-plusplus/FINALFANTASY7_DN.bin` |

New builds **do not** auto-disable older base versions. Set `"enabled": false` in `builder/manifest.json` yourself when you want to hide one.

## Commit + push

```bash
git add builder/
git status
git commit -m "Release CSR v0.14.1, CSR+ v0.1.1, CSR++ v0.1.1."
git push
```

Wait for Pages, then rebuild Encounter in **Final-Fantasy-7-Modding** against the new base ids if needed.
