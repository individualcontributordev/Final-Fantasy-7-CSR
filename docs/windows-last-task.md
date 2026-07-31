# Task: NEW CSR+ scene — CoTA FD Manip (Bugenhagen / Forgotten Capital, disc 2)

## Goal

New free checkbox on **CSR** only, **disc 2**:

- Forgotten Capital — Bugenhagen + Cloud (waterfall / shell-city), CoTA FD Manip trim.
- **Not** Shinra / helicopter / Hojo. **Not** csr-plus-scene-hojo-fd-manip-v0.1.0
  (BLIN66_6, CANON_2, FSHIP_24).

| | |
|--|--|
| pack-id | csr-plus-scene-cota-fd-manip-v0.1.0 |
| name | CSR+ CoTA FD Manip |
| bases | csr-v0.14.1 only |
| disc | 2 |
| exclusiveGroup | omit (checkbox) |

Skill: ship-csr-plus-scene → New scene.

## Success

1. Makou trim on CSR D2; FIELD map names in Evidence.
2. Pack built; verify_builder_config PASS (disc 2 + CSR + new addon).
3. Preset csr-plus lists new id with Aerith + Hojo.
4. addons/csr-plus/CHANGELOG.md newest-at-top.
5. DuckStation one-liner. Commit builder/ + changelog. Push. Say **check**.

## Steps

### 1. Pull

    cd "$(git rev-parse --show-toplevel)"
    git pull --ff-only

### 2. Builder zip + Makou

1. Builder: pristine **Disc 2**, Base **CSR**, Preset **None**.
2. Build, unzip (keep APPLIED.txt + .bin).
3. Makou: Forgotten Capital / Bugenhagen waterfall beat (Key of the Ancients path).
4. Trim CoTA FD manip cutscene(s) only.
5. Record every edited FIELD/*.DAT name.
6. Save .bin into the same extract folder.

### 3. CSR D2 cache (if missing)

    mkdir -p cache/csr
    test -f cache/csr/FINALFANTASY7_D2.bin || python3 scripts/apply_layer.py \
      pristine/FINALFANTASY7_D2.bin \
      builder/csr-v0.14.1/layers/disc2.layer.json \
      -o cache/csr/FINALFANTASY7_D2.bin

### 4. Build pack (replace MAP names)

    python3 scripts/build_field_map_pack.py \
      --pristine cache/csr/FINALFANTASY7_D2.bin \
      --flavor-image "/c/path/to/extract/your-d2.bin" \
      --files FIELD/MAP1.DAT FIELD/MAP2.DAT \
      --pack-id csr-plus-scene-cota-fd-manip-v0.1.0 \
      --version 0.1.0 \
      --disc 2 \
      --name "CSR+ CoTA FD Manip" \
      --group-label "CSR+ CoTA FD Manip" \
      --blurb "CSR+ trim of Forgotten Capital / Bugenhagen (CoTA FD manip) on CSR." \
      --no-exclusive-group \
      --compatible-bases csr-v0.14.1

### 5. Verify

    python3 scripts/verify_builder_config.py \
      --pristine pristine/FINALFANTASY7_D2.bin \
      --disc 2 \
      --base csr-v0.14.1 \
      --addon csr-plus-scene-cota-fd-manip-v0.1.0

### 6. Preset + changelog + ship

- manifest preset csr-plus: append csr-plus-scene-cota-fd-manip-v0.1.0
- CHANGELOG newest section at top of addons/csr-plus/CHANGELOG.md
- git add builder/ addons/csr-plus/CHANGELOG.md docs/windows-last-task.md
- commit + push

## Evidence

    (FIELD maps)
    (verify PASS)
    (playtest one-liner)
