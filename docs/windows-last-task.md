# Task: CSR+ Aerith house — Elmyra dialogue via builder-zip update flow

## Goal

When the player enters Aerith's house, Elmyra (mom) shows dialogue the player must
close; closing it advances Game Moment so they can leave and continue.

Use the **builder zip → Makou → update_addon_from_builder_zip.py** workflow
(skill ship-csr-plus-scene → Update existing).

## Success

1. Builder zip: CSR + CSR+ Aerith's house only; edited in Makou; APPLIED.txt intact.
2. update_addon_from_builder_zip.py → new pack (default v0.1.1); old disabled; preset ok.
3. verify_builder_config.py PASS.
4. Playtest via apply_layer stack (or DuckStation on play bin): enter house → Elmyra
   dialogue → close → leave OK. Record Game Moment value.
5. Changelog + commit builder/ + push. Say **check**.

## Steps

### 1. Pull

    cd "$(git rev-parse --show-toplevel)"
    git pull --ff-only

### 2. Builder → unzip

1. https://individualcontributor.dev/builder/ — load pristine **Disc 1**.
2. Base **CSR**. Enable **CSR+ Aerith's house** only (or preset if that is fine).
3. Build → unzip to a folder. Keep .bin + APPLIED.txt together.

### 3. Makou

Open the extract .bin → field **EALS_1**.

- On enter: Elmyra dialogue (must close).
- After close: set Game Moment so exit/continue works (copy GM from CSR/vanilla
  EALS_1 if unsure). Write GM in Evidence.
- Save .bin back into the **same extract folder**.

### 4. Rebuild pack from zip (copy-paste)

    cd "$(git rev-parse --show-toplevel)"
    git pull --ff-only

    BUILT="/c/path/to/ff7-builder-d1+csr-v0.14.1+csr-plus-scene-aerith-house-v0.1.0"

    python3 scripts/update_addon_from_builder_zip.py "$BUILT"
    # optional: --version 0.2.0   or   --addon csr-plus-scene-aerith-house

    NEW=csr-plus-scene-aerith-house-v0.1.1   # use id the script printed if different

    python3 scripts/verify_builder_config.py \
      --pristine workspace/pristine/FINALFANTASY7_D1.bin \
      --disc 1 \
      --base csr-v0.14.1 \
      --addon "$NEW"

### 5. Playtest (layer stack — no re-download)

    mkdir -p temp
    python3 scripts/apply_layer.py \
      workspace/pristine/FINALFANTASY7_D1.bin \
      builder/csr-v0.14.1/layers/disc1.layer.json \
      -o temp/csr-d1.bin
    python3 scripts/apply_layer.py \
      temp/csr-d1.bin \
      builder/$NEW/layers/disc1.layer.json \
      -o temp/play-d1.bin

Open temp/play-d1.bin in DuckStation (.cue if you need one). Iterate Makou on
the extract → re-run update script → re-apply if needed.

### 6. Ship

- bases/csr-plus/CHANGELOG.md note for this bump.
- git add builder/ changelog docs/windows-last-task.md → commit → push.

## Evidence

    (GM value + script notes)
    (update_addon_from_builder_zip stdout: new pack id)
    (verify PASS)
    (playtest one-liner)
