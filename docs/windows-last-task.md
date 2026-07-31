# Task: build CoTA FD Manip pack (edited image includes Hojo add-on)

## Problem

Your Makou `.bin` is **CSR + Hojo FD manip + CoTA edits**. Diffing against **CSR only**
lists Hojo maps (BLIN66_6, CANON_2, FSHIP_24) as well as CoTA.

**Fix:** baseline = CSR + Hojo layer, then diff your edited image. Only CoTA maps remain.

Do **not** put Hojo maps in the CoTA pack `--files` list.

## Goal

Pack: csr-plus-scene-cota-fd-manip-v0.1.0 (disc 2, CSR only).

## Copy-paste

    cd "$(git rev-parse --show-toplevel)"
    git pull --ff-only

    BUILT="/c/path/to/ff7-builder-d2+csr-v0.14.1+csr-plus-scene-hojo-fd-manip-v0.1.0+..."
    EDITED=$(ls "$BUILT"/*.bin "$BUILT"/*.BIN 2>/dev/null | head -1)
    echo "EDITED=$EDITED"
    test -f "$EDITED"

    mkdir -p cache/csr temp

    # 1) CSR disc 2 (if missing)
    test -f cache/csr/FINALFANTASY7_D2.bin || python3 scripts/apply_layer.py \
      pristine/FINALFANTASY7_D2.bin \
      builder/csr-v0.14.1/layers/disc2.layer.json \
      -o cache/csr/FINALFANTASY7_D2.bin

    # 2) Baseline = CSR + existing Hojo pack (matches how you started in the builder)
    python3 scripts/apply_layer.py \
      cache/csr/FINALFANTASY7_D2.bin \
      builder/csr-plus-scene-hojo-fd-manip-v0.1.0/layers/disc2.layer.json \
      -o temp/csr-plus-hojo-d2.bin

    # 3) Diff: only maps you changed on top of CSR+Hojo
    python3 scripts/list_changed_field_maps.py \
      --pristine temp/csr-plus-hojo-d2.bin \
      --patched "$EDITED" \
      -o temp/cota-fd-manip-d2-diff.json

    python3 -c "
import json
d=json.load(open('temp/cota-fd-manip-d2-diff.json'))
paths=[]
for m in d.get('maps') or []:
    for p in m.get('files') or []:
        if p.upper().endswith('.DAT'):
            paths.append(p)
print('mapCount', d.get('mapCount'))
print(' '.join(paths) if paths else '(none)')
hojo={'FIELD/BLIN66_6.DAT','FIELD/CANON_2.DAT','FIELD/FSHIP_24.DAT'}
bad=[p for p in paths if p.upper() in {h.upper() for h in hojo}]
if bad:
    print('ERROR still includes Hojo maps:', bad)
else:
    print('OK no Hojo maps in diff')
"

# Expect: CoTA FIELD/*.DAT only (no Hojo). Then build from that JSON:

    # CSR+ scene: disc from APPLIED.txt; bases/labels/baseline inferred
    python3 scripts/build_field_map_pack.py \
      --edited-image "$EDITED" \
      --changed-maps temp/cota-fd-manip-d2-diff.json \
      --pack-id csr-plus-scene-cota-fd-manip-v0.1.0

# Pack still diffs those maps against CSR alone (correct).
# Keep Hojo out of the diff JSON (CSR+Hojo baseline above) so they are not packed.

    python3 scripts/verify_builder_config.py \
      --pristine pristine/FINALFANTASY7_D2.bin \
      --disc 2 \
      --base csr-v0.14.1 \
      --addon csr-plus-scene-cota-fd-manip-v0.1.0

# Optional: stack CSR + Hojo + CoTA like your edit session
#   --addon csr-plus-scene-hojo-fd-manip-v0.1.0 \
#   --addon csr-plus-scene-cota-fd-manip-v0.1.0

Then: preset csr-plus append new id; addons/csr-plus/CHANGELOG.md newest-at-top;
git add builder/ changelog; commit; push; say **check**.

## Evidence

    (DAT list from step 3 — no Hojo)
    (verify PASS)
