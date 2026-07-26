# Local disc images (gitignored)

Put NTSC-U `.bin` / `.cue` here for layer building on Windows. Binaries are not committed; small helpers (e.g. `.m3u`) may be.

Suggested layout:

```
workspace/
  pristine/       FINALFANTASY7_D1.bin … D3 (+ .cue)
  csr/            FINALFANTASY7_D1 (patched).bin … (+ .cue), optional .m3u
  csr-plus/       same naming for CSR+
  csr-plusplus/   same naming for CSR++
```

Keep pristine files you never overwrite. Diff with `scripts/bin_diff_to_layer.py` (see `builder/WINDOWS-INSTRUCTIONS.md`). Quote paths that contain spaces.
