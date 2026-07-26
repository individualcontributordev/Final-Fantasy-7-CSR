# Local disc images (gitignored)

Put NTSC-U `.bin` / `.cue` here for layer building on Windows. Nothing in this tree is committed.

Suggested layout:

```
workspace/
  pristine/       disc1.bin, disc2.bin, disc3.bin (+ .cue)
  csr/            CSR-patched images (one set per disc)
  csr-plus/       CSR+ patched images
  csr-plusplus/   CSR++ patched images
```

Keep a pristine backup you never overwrite. Diff pristine vs patched with `scripts/bin_diff_to_layer.py` (see `builder/WINDOWS-INSTRUCTIONS.md`).
