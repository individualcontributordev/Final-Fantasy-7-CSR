![](images/banner.png)
*Artist: @Cronosart99*

# Final Fantasy VII CutScenes Removed

CSR shortens Final Fantasy VII while retaining skill checks, movement, choices,
skips, and RNG manipulation. CSR+ adds scene trims and collapses the run onto
Disc 1. Highwind is an independent, more aggressive Disc 1 route. The three
bases are mutually exclusive: editing one does not rebuild another.

All commands run from this repository's root and require Python 3.10 or newer.
Builds require clean NTSC-U raw MODE2/2352 images:

```text
pristine/FINALFANTASY7_D1.bin
pristine/FINALFANTASY7_D2.bin
pristine/FINALFANTASY7_D3.bin
```

Never edit `pristine/`. Working BINs stay under `cache/<base>/`; published
browser-builder metadata and layers are under `builder/`.

## Build, edit, repair, publish

Every base uses the same loop: apply the published layer onto pristine, edit
the BIN, repair Form 1 footers, then publish a replacement layer.

Choose the base and its discs:

```bash
# CSR
base=csr
discs=(1 2 3)

# CSR+ (use instead of the two lines above)
# base=csr-plus
# discs=(1)

# Highwind (use instead of the two lines above)
# base=highwind
# discs=(1)
```

Materialize the currently published base:

```bash
mkdir -p "cache/$base"
for disc in "${discs[@]}"; do
  python3 scripts/apply_layer.py \
    "pristine/FINALFANTASY7_D${disc}.bin" \
    "builder/$base/layers/disc${disc}.layer.json" \
    -o "cache/$base/FINALFANTASY7_D${disc}.bin"
done
```

Edit the `cache/<base>/FINALFANTASY7_DN.bin` files in Makou Reactor. Before
overwriting an edited BIN, keep one backup. Repair and publish every edited
disc with the same loop:

```bash
version=X.Y.Z
for disc in "${discs[@]}"; do
  image="cache/$base/FINALFANTASY7_D${disc}.bin"
  test -e "$image.bak" || cp "$image" "$image.bak"

  python3 scripts/repair_mode2_edc.py \
    "pristine/FINALFANTASY7_D${disc}.bin" \
    "$image" \
    -o "$image"

  python3 scripts/build_base_layer.py \
    "$image" \
    --version "$version"

  python3 scripts/verify_builder_config.py \
    --disc "$disc" \
    --base "$base" \
    --no-cache
done
```

Outputs are `builder/<base>/layers/discN.layer.json`, `pack.json`, `VERSION`,
and `builder/manifest.json`. CSR+ and Highwind Disc 1 images are longer than
retail; repair uses pristine Disc 1 for overlapping sectors and recomputes
Form 1 footers on appended sectors.

## Verification

```bash
python3 scripts/apply_layer.py \
  "pristine/FINALFANTASY7_D${disc}.bin" \
  "builder/$base/layers/disc${disc}.layer.json" \
  --expect "cache/$base/FINALFANTASY7_D${disc}.bin"
```

Automated checks do not replace DuckStation/MiSTer testing, optical-media
verification, or a console playtest.

## Script reference


| Command                                                    | Purpose                                                                 |
| ---------------------------------------------------------- | ----------------------------------------------------------------------- |
| `apply_layer.py IMAGE LAYER [-o OUT|--expect BIN]`         | Apply or byte-verify an `ic-layer-v1` disc patch.                       |
| `build_base_layer.py IMAGE --version X.Y.Z`                | Publish one exclusive-base disc layer and merge pack/manifest metadata. |
| `repair_mode2_edc.py PRISTINE IMAGE -o OUT`                | Restore or recompute MODE2 Form 1 footers after editing.                |
| `verify_builder_config.py --disc N --base ID [--addon ID]` | Reconstruct and validate the selected builder stack.                    |


Shared implementation lives under `scripts/libs/`; files directly under
`scripts/` are supported commands.