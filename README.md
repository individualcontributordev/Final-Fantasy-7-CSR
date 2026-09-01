![](images/banner.png)
*Artist: @Cronosart99*

# Final Fantasy VII CutScenes Removed

CSR shortens Final Fantasy VII while retaining skill checks, movement, choices,
skips, and RNG manipulation. CSR+ adds scene trims and collapses the run onto
Disc 1. Highwind is an independent, more aggressive Disc 1 route.

All commands run from this repository's root and require Python 3.10 or newer.
Builds require clean NTSC-U raw MODE2/2352 images:

```text
pristine/FINALFANTASY7_D1.bin
pristine/FINALFANTASY7_D2.bin
pristine/FINALFANTASY7_D3.bin
```

Never edit `pristine/`. Build outputs stay under `cache/` or `build/`; published
browser-builder metadata and layers are under `builder/`.

## CSR: build, edit, repair, publish

Materialize all three current CSR images:

```bash
mkdir -p cache/csr
for disc in 1 2 3; do
  python3 scripts/apply_layer.py \
    pristine/FINALFANTASY7_D${disc}.bin \
    builder/csr/layers/disc${disc}.layer.json \
    -o cache/csr/FINALFANTASY7_D${disc}.bin
done
```

Edit `cache/csr/FINALFANTASY7_D1.bin` through `D3.bin` in Makou Reactor. Before
an in-place footer repair, keep one backup:

```bash
image=cache/csr/FINALFANTASY7_D1.bin
test -e "$image.bak" || cp "$image" "$image.bak"
python3 scripts/repair_mode2_edc.py \
  --pristine pristine/FINALFANTASY7_D1.bin \
  --input "$image" \
  --in-place
```

Repeat the repair for each edited disc, then regenerate the published layers,
pack metadata, version, and manifest entry:

```bash
python3 scripts/build_csr_base_layers.py cache/csr \
  --version X.Y.Z --discs 1,2,3
for disc in 1 2 3; do
  python3 scripts/verify_builder_config.py --disc "$disc" --base csr --no-cache
done
```

Outputs are `builder/csr/layers/disc{1,2,3}.layer.json`,
`builder/csr/pack.json`, `builder/csr/VERSION`, and `builder/manifest.json`.

## CSR+: prepare, Makou save, finalize, publish

```bash
python3 scripts/build_csrplus_staged.py prepare --run-name my-csrplus
```

Open `build/csr-plus/my-csrplus/03-working/CSRPLUS_D1.bin` in Makou Reactor.
Keep that hash-checked checkpoint unchanged and save Makou's result to a
different path.

```bash
python3 scripts/build_csrplus_staged.py finalize \
  --run-dir build/csr-plus/my-csrplus \
  --edited-image /path/to/makou-saved.bin \
  --version X.Y.Z
python3 scripts/publish_release_candidate.py \
  --run-dir build/csr-plus/my-csrplus \
  --pack-id csr-plus
python3 scripts/verify_builder_config.py \
  --disc 1 --base csr-plus --no-cache
```

The publish candidate is
`build/csr-plus/my-csrplus/05-release-candidate/pack/csr-plus/`. The
builder-round-trip image is under `05-release-candidate/verification/`; the
BIN/CUE for emulator, burn, and console checks is
`06-console-check/FINALFANTASY7_D1_CSRPLUS.{bin,cue}`.

Resume only reuses stages whose report hashes still match:

```bash
python3 scripts/build_csrplus_staged.py prepare \
  --run-name my-csrplus --resume
```

To intentionally rebuild a stage and all later prepare stages:

```bash
python3 scripts/build_csrplus_staged.py prepare \
  --run-name my-csrplus --rebuild-from collapse
```

Changed stage directories are moved under
`build/csr-plus/my-csrplus/recovery/`; they are not discarded.

## Highwind

Highwind uses the same checkpoint, finalize, publish, and recovery contract:

```bash
python3 scripts/build_highwind_staged.py prepare --run-name my-highwind
# Edit 03-working/HIGHWIND_D1.bin; save to another file.
python3 scripts/build_highwind_staged.py finalize \
  --run-dir build/highwind/my-highwind \
  --edited-image /path/to/makou-saved.bin \
  --version X.Y.Z
python3 scripts/publish_release_candidate.py \
  --run-dir build/highwind/my-highwind \
  --pack-id highwind
python3 scripts/verify_builder_config.py \
  --disc 1 --base highwind --no-cache
```

The candidate pack is under
`build/highwind/my-highwind/05-release-candidate/pack/highwind/`; the test
BIN/CUE is `build/highwind/my-highwind/06-console-check/FINALFANTASY7_D1_HIGHWIND.{bin,cue}`.
Use `--resume` or `--rebuild-from sources|collapse|working` exactly as for
CSR+; recovery files stay under that run's `recovery/`.

## Verification

Finalization checks sector alignment, PVD bounds, ISO9660 extents, changed
Form 1 EDC/ECC, and an exact layer-apply round trip. Run direct checks when
diagnosing an image or layer:

```bash
python3 scripts/verify_iso_integrity.py /path/to/image.bin
python3 scripts/apply_layer.py \
  pristine/FINALFANTASY7_D1.bin \
  builder/csr-plus/layers/disc1.layer.json \
  --expect build/csr-plus/my-csrplus/06-console-check/FINALFANTASY7_D1_CSRPLUS.bin
```

Automated checks do not replace DuckStation/MiSTer testing, optical-media
verification, or a console playtest.

## Script reference

| Command | Purpose |
|---|---|
| `apply_layer.py IMAGE LAYER [-o OUT\|--expect BIN]` | Apply or byte-verify an `ic-layer-v1` disc patch. |
| `bin_diff_to_layer.py ORIGINAL MODIFIED -o LAYER --id ID` | Encode changed byte runs as a builder layer. |
| `build_csr_base_layers.py BASE --version X.Y.Z` | Publish CSR-style disc layers plus pack and manifest metadata. |
| `build_csrplus_staged.py prepare\|finalize ...` | Build, stabilize, and package the CSR+ single-disc workflow. |
| `build_highwind_staged.py prepare\|finalize ...` | Run the equivalent independent Highwind workflow. |
| `publish_release_candidate.py --run-dir RUN --pack-id ID` | Copy a finalized CSR+/Highwind candidate into `builder/` and update the manifest. |
| `verify_builder_config.py --disc N --base ID [--addon ID]` | Reconstruct and validate the selected builder stack. |
| `verify_iso_integrity.py IMAGE` | Report ISO9660 duplicate LBAs, overlaps, and ff7tk-unsafe gaps. |
| `repair_mode2_edc.py --pristine BIN --input BIN (--in-place\|--output BIN)` | Restore or recompute MODE2 Form 1 footers after editing. |
| `merge_rework_fields.py --bin BIN (--in-place\|-o BIN)` | Splice selected Disc 2 script slots into collapsed Disc 1 fields. |
| `merge_safe_fields.py --bin BIN (--in-place\|-o BIN)` | Copy fields edited on only one later CSR disc. |
| `fix_junair_air0_slot3.py --bin BIN (--in-place\|-o BIN)` | Apply the guarded JUNAIR slot/text-table splice. |
| `fix_field_bin_table.py --bin BIN (--in-place\|-o BIN)` | Repair FIELD.BIN/WORLD.BIN embedded LBA/size lookup rows. |
| `inject_movies_by_disc_id.py --d1 BIN --manifest FILE (--in-place\|-o BIN)` | Inject disc-local PMVIE slots while preserving raw XA sectors and MOVIE_ID metadata. |
| `inject_snova_d3_to_d1.py --d1 BIN --d3 BIN (--in-place\|-o BIN)` | Append SNOVA and patch its ISO and BATTLE.X LBA references. |
| `alias_d3_ending_lbas_on_d1.py --d1 BIN [--d3 BIN] (--in-place\|-o BIN)` | Place the ending stream at the hardcoded Disc 3 seek location. |
| `compress_gzipps.py PATCHED.dec ORIGINAL.bin [OUT]` | Recompress a GZIPPS overlay without silently truncating an oversize result. |

`disc_sources.py`, `local_paths.py`, `pipeline_cache.py`, `psx_mode2_iso.py`,
`edc_ecc.py`, `lzs.py`, `ff7_opcodes.py`, `field_dat.py`,
`field_dat_write.py`, and `highwind_pipeline.py` are support modules used by
the commands above.
