# Browser patcher

Static site powered by [Rom Patcher JS](https://github.com/marcrobledo/RomPatcher.js).

| Path | Role |
|------|------|
| `../index.html` | Patcher UI |
| `../site.css` | Page styling |
| `../rom-patcher-js/` | Vendored Rom Patcher JS |
| `*.ppf` | Individual CSR / CSR+ / CSR++ disc patches (loaded on demand) |

## Update patches

When you release new `.ppf` files:

1. Keep long names under `csr/`, `csr+/`, `csr++/` if you like.
2. Copy **short names** into `patcher/` (these are what `index.html` loads):

```bash
# CSR (example bump 0.14.0 → 0.14.1)
cp "csr/….ppf" patcher/csr-disc1-v0.14.1.ppf
cp "csr/….ppf" patcher/csr-disc2-v0.14.1.ppf
cp "csr/….ppf" patcher/csr-disc3-v0.14.1.ppf

# CSR+ / CSR++ (unchanged example 0.1.0)
# patcher/csrplus-disc1-v0.1.0.ppf
# patcher/csrplusplus-disc1-v0.1.0.ppf
```

Short-name pattern: `csr-disc{N}-v{ver}.ppf`, `csrplus-disc{N}-v{ver}.ppf`, `csrplusplus-disc{N}-v{ver}.ppf`.

3. Update the `PATCHES` array in `../index.html` (`file`, `name`, `outputName`, versions).
4. Rebuild builder layers with the **same** version string:
   `python scripts/build_csr_base_layers.py workspace/csr --version 0.14.1`
5. Commit and push — GitHub Pages redeploys from `main`.

Encounter stacks are built in **Final-Fantasy-7-Modding** (`build_encounter_on_base.py`); they pin `compatibleBases` to these builder ids (e.g. `csr-v0.14.1`, `csr-plus-v0.1.0`).
