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

1. Update files under `csr/`, `csr+/`, `csr++/`
2. Copy short names into this folder:

```bash
cp "csr/Final Fantasy VII (Disc 1) CSR Patch vX.Y.Z.ppf" patcher/csr-disc1-vX.Y.Z.ppf
# …same for other discs/variants…
```

3. Update the `PATCHES` array in `../index.html` (`file`, `name`, `outputName`, versions).
4. Commit and push — GitHub Pages redeploys from `main`.
