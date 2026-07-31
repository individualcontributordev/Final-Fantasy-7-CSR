# Task: build CSR+ CoTA FD Manip pack from your Makou disc 2 edit

## Goal

You already trimmed Forgotten Capital / Bugenhagen (CoTA FD Manip) on a CSR disc 2
builder zip. Now discover FIELD maps, build pack, verify, preset, changelog, push.

Pack: csr-plus-scene-cota-fd-manip-v0.1.0  
Not Hojo (BLIN66_6 / CANON_2 / FSHIP_24).

## Success

1. list_changed_field_maps shows CoTA maps only (paste list under Evidence).
2. build_field_map_pack + verify_builder_config PASS.
3. preset csr-plus includes new id; changelog newest-at-top.
4. Optional DuckStation one-liner. Commit + push. Say **check**.

## Copy-paste

Set BUILT to your unzipped builder folder (must contain .bin + APPLIED.txt).

    cd "$(git rev-parse --show-toplevel)"
    git pull --ff-only

    BUILT="/c/path/to/ff7-builder-d2+csr-v0.14.1+..."
    # .bin inside that folder:
    EDITED=$(ls "$BUILT"/*.bin "$BUILT"/*.BIN 2>/dev/null | head -1)
    echo "EDITED=$EDITED"
    test -f "$EDITED" && test -f "$BUILT/APPLIED.txt"

    mkdir -p cache/csr temp
    test -f cache/csr/FINALFANTASY7_D2.bin || python3 scripts/apply_layer.py \
      pristine/FINALFANTASY7_D2.bin \
      builder/csr-v0.14.1/layers/disc2.layer.json \
      -o cache/csr/FINALFANTASY7_D2.bin

    # Which FIELD maps differ from CSR baseline?
    python3 scripts/list_changed_field_maps.py \
      --pristine cache/csr/FINALFANTASY7_D2.bin \
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
print('mapCount', d.get('mapCount'), 'DAT files:')
print(' '.join(paths) if paths else '(none — is EDITED really different from CSR D2?)')
"

Copy those FIELD/....DAT paths into --files below (space-separated). Expect CoTA maps only; if you see BLIN66_6/CANON_2/FSHIP_24 you edited the Hojo pack by mistake.

    python3 scripts/build_field_map_pack.py \
      --pristine cache/csr/FINALFANTASY7_D2.bin \
      --flavor-image "$EDITED" \
      --files FIELD/REPLACE_ME.DAT \
      --pack-id csr-plus-scene-cota-fd-manip-v0.1.0 \
      --version 0.1.0 \
      --disc 2 \
      --name "CSR+ CoTA FD Manip" \
      --group-label "CSR+ CoTA FD Manip" \
      --blurb "CSR+ trim of Forgotten Capital / Bugenhagen (CoTA FD manip) on CSR." \
      --no-exclusive-group \
      --compatible-bases csr-v0.14.1

    python3 scripts/verify_builder_config.py \
      --pristine pristine/FINALFANTASY7_D2.bin \
      --disc 2 \
      --base csr-v0.14.1 \
      --addon csr-plus-scene-cota-fd-manip-v0.1.0

Then hand-edit if needed:

- builder/manifest.json preset csr-plus → append csr-plus-scene-cota-fd-manip-v0.1.0
- addons/csr-plus/CHANGELOG.md — new section at **top**

    git add builder/ addons/csr-plus/CHANGELOG.md docs/windows-last-task.md
    git commit -m "CSR+ CoTA FD Manip v0.1.0 (disc 2)."
    git push

## Evidence

    (diff map list)
    (verify PASS)
    (playtest optional)
