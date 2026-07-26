# Browser patcher

Static site powered by [Rom Patcher JS](https://github.com/marcrobledo/RomPatcher.js).

| Path | Role |
|------|------|
| `../index.html` | Patcher UI |
| `../site.css` | Page styling |
| `../rom-patcher-js/` | Vendored Rom Patcher JS |
| `patches.zip` | All CSR / CSR+ / CSR++ disc PPFs |

## Update patches

When you release new `.ppf` files:

1. Update files under `csr/`, `csr+/`, `csr++/`
2. Rebuild the zip:

```bash
STAGE=$(mktemp -d)
cp "csr/Final Fantasy VII (Disc 1) CSR Patch vX.Y.Z.ppf" "$STAGE/csr-disc1-vX.Y.Z.ppf"
# …same for other discs/variants with matching names in index.html…
(cd "$STAGE" && zip -9 -q "$OLDPWD/patcher/patches.zip" *.ppf)
```

3. Update the `patches: [...]` entries in `index.html` (`file`, `name`, `outputName`, versions).
4. Commit and push — GitHub Pages redeploys from `main`.
