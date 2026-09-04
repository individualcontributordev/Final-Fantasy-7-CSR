![](images/banner.png)
*Artist: @Cronosart99*

# Final Fantasy VII CutScenes Removed

CSR shortens Final Fantasy VII while retaining skill checks, movement, choices,
skips, and RNG manipulation. CSR+ adds scene trims and collapses the run onto
Disc 1. Highwind is an independent, more aggressive Disc 1 route. The three
bases are mutually exclusive: editing one does not rebuild another.

## Setup

Python 3.10+, all commands from the repo root. Retail NTSC-U MODE2/2352 images
go at `pristine/FINALFANTASY7_D{1,2,3}.bin` and are never edited. Working BINs
stay in `cache/<base>/`; published metadata and layers in `builder/`.

```bash
BASE=csr          # or csr-plus, highwind
DISCS=(1 2 3)     # csr-plus and highwind are Disc 1 only
```

## Build, edit, repair, publish

Materialize the currently published base:

```bash
mkdir -p "cache/$BASE"
for disc in "${DISCS[@]}"; do
  python3 scripts/apply_layer.py \
    "pristine/FINALFANTASY7_D${disc}.bin" \
    "builder/$BASE/layers/disc${disc}.layer.json" \
    -o "cache/$BASE/FINALFANTASY7_D${disc}.bin"
done
```

Edit those BINs in Makou Reactor, then repair footers and publish each disc:

```bash
VERSION=X.Y.Z
for disc in "${DISCS[@]}"; do
  image="cache/$BASE/FINALFANTASY7_D${disc}.bin"
  test -e "$image.bak" || cp "$image" "$image.bak"

  python3 scripts/repair_mode2_edc.py \
    "pristine/FINALFANTASY7_D${disc}.bin" "$image" -o "$image" || break

  python3 scripts/build_base_layer.py "$image" --version "$VERSION" || break

  python3 scripts/verify_builder_config.py \
    --disc "$disc" --base "$BASE" --no-cache || break
done
```

Keep the `|| break`. Without it a failed publish is followed by a verify of the
*previously* published layer, which prints `PASS` and hides the failure.

Outputs are `builder/<base>/layers/discN.layer.json`, `pack.json`, `VERSION`,
and `builder/manifest.json`. CSR+ and Highwind Disc 1 images are longer than
retail; repair uses pristine Disc 1 for overlapping sectors and recomputes
Form 1 footers on appended sectors.

## Verify

```bash
python3 scripts/apply_layer.py \
  "pristine/FINALFANTASY7_D1.bin" \
  "builder/$BASE/layers/disc1.layer.json" \
  --expect "cache/$BASE/FINALFANTASY7_D1.bin"
```

Not a substitute for DuckStation/MiSTer, optical-media verification, or a
console playtest.

## Publish

```bash
python3 scripts/validate_manifest.py
```

Run this before pushing. The builder refuses any layer whose bytes do not hash
to the checksum published beside it, so a stale or mistaken `discDigests` entry
takes that base offline with no other warning. Failures print the fix for each
problem.

Push `main`. GitHub Pages deploys `builder/` to
`https://individualcontributor.dev/Final-Fantasy-7-CSR/builder/`, which is what
the hosted builder reads.

Checksums cover the exact bytes git serves, so `builder/*.json` is pinned to LF
by `.gitattributes` and `.editorconfig`, and `build_base_layer.py` refuses to
start without that rule. Building bases on Windows and mods on a Mac is fine;
publishing from a CRLF checkout is not.

**Bumping a base version hides every Modding pack pinned to the old version**
until those packs are recut (`rebuild_on_base.py` in the Modding repo).

## Script reference

| Command                                                    | Purpose                                                                 |
| ----------------------------------------------------------- | ------------------------------------------------------------------------ |
| `apply_layer.py IMAGE LAYER [-o OUT\|--expect BIN]`         | Apply or byte-verify an `ic-layer-v1` disc patch.                        |
| `build_base_layer.py IMAGE --version X.Y.Z`                | Publish one base disc layer and merge pack/manifest metadata.            |
| `repair_mode2_edc.py PRISTINE IMAGE -o OUT`                | Restore or recompute MODE2 Form 1 footers after editing.                 |
| `verify_builder_config.py --disc N --base ID [--addon ID]` | Reconstruct and validate the selected builder stack.                     |
| `validate_manifest.py [PATH]`                              | Check ids, layer paths, published checksums, and LF line endings.        |

Shared code lives in `scripts/libs/`; files directly under `scripts/` are
supported commands.

Commit as `individualcontributordev <contributorindividual@gmail.com>`.

## Archive

Retired scripts, docs, and the old PPF releases are indexed in
[`ARCHIVE.md`](ARCHIVE.md) with the commit that removed each one. Current
releases are `ic-layer-v1` JSON only.
