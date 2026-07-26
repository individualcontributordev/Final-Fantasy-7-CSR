➜  Final-Fantasy-7-CSR git:(main) python scripts/bin_diff_to_layer.py \
  "workspace/pristine/FINALFANTASY7_D1.bin" \
  "workspace/csr/FINALFANTASY7_D1 (patched).bin" \
  -o builder/csr-v0.14.0/layers/disc1.layer.json \
  --id csr-disc1-v0.14.0 \
  --description "CSR v0.14.0 — NTSC-U Disc 1"
Wrote builder\csr-v0.14.0\layers\disc1.layer.json
  records=94148  changedBytes=3854678  jsonBytes≈13358327
➜  Final-Fantasy-7-CSR git:(main) ✗ python scripts/apply_layer.py \
  "workspace/pristine/FINALFANTASY7_D1.bin" \
  builder/csr-v0.14.0/layers/disc1.layer.json \
  --expect "workspace/csr/FINALFANTASY7_D1 (patched).bin"
OK — layer apply matches --expect
➜  Final-Fantasy-7-CSR git:(main) ✗ python scripts/bin_diff_to_layer.py \
  "workspace/pristine/FINALFANTASY7_D1.bin" \
  "workspace/csr-plus/FINALFANTASY7_D1 (patched).bin" \
  -o builder/csr-plus-v0.1.0/layers/disc1.layer.json \
  --id csr-plus-disc1-v0.1.0 \
  --description "CSR+ v0.1.0 — NTSC-U Disc 1"
Wrote builder\csr-plus-v0.1.0\layers\disc1.layer.json
  records=94439  changedBytes=3865978  jsonBytes≈13398391
➜  Final-Fantasy-7-CSR git:(main) ✗ python scripts/apply_layer.py \
  "workspace/pristine/FINALFANTASY7_D1.bin" \
  builder/csr-plus-v0.1.0/layers/disc1.layer.json \
  --expect "workspace/csr-plus/FINALFANTASY7_D1 (patched).bin"
OK — layer apply matches --expect