# Browser patcher (legacy CSR-only)

Prefer the **[disc builder](https://individualcontributor.dev/builder/)** for CSR + Encounter stacks.

This folder feeds the legacy Rom Patcher JS UI on `../index.html` (CSR / CSR+ / CSR++ alone).

| Path | Role |
|------|------|
| `../index.html` | Legacy patcher UI |
| `*.ppf` | Short-name CSR disc patches loaded on demand |

## Update patches

1. Generate PPFs (pristine → patched) into short names here:

```bash
# pattern: csr-disc{N}-v{ver}.ppf, csrplus-disc{N}-v{ver}.ppf, csrplusplus-disc{N}-v{ver}.ppf
```

2. Update the `PATCHES` array in `../index.html`.
3. Rebuild builder layers with the **same** version:
   `python scripts/build_csr_base_layers.py workspace/csr --version 0.14.2`
4. Commit and push.

Encounter packs are built in **Final-Fantasy-7-Modding** and pin `compatibleBases` to these builder ids.
