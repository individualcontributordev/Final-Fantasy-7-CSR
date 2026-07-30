# Task: CSR+ Aerith house — Elmyra dialogue + game moment on entry

## Goal

Update existing add-on csr-plus-scene-aerith-house-v0.1.0 so that when the player
**enters Aerith's house**, **Elmyra (mom)** shows dialogue the player must close;
closing it **advances Game Moment** enough that the player can **leave and continue**
the story (no softlock / blocked exit).

Makou field-script change on FIELD/EALS_1.DAT, then pack rebuild to v0.1.1.

Skill: .agents/skills/ship-csr-plus-scene → Update existing.

## Success

1. Makou: on enter house, Elmyra window appears; player must dismiss it.
2. After dismiss, Game Moment set so exit / next progression works (record GM value).
3. Pack csr-plus-scene-aerith-house-v0.1.1 shipped; old v0.1.0 disabled; preset csr-plus uses new id.
4. verify_builder_config.py PASS for CSR + new addon.
5. DuckStation one-liner under Evidence. Commit + push. Say **check**.

## Preconditions

    cd "$(git rev-parse --show-toplevel)"
    git pull --ff-only

    test -f workspace/csr/FINALFANTASY7_D1.bin || python3 scripts/apply_layer.py \
      workspace/pristine/FINALFANTASY7_D1.bin \
      builder/csr-v0.14.1/layers/disc1.layer.json \
      -o workspace/csr/FINALFANTASY7_D1.bin

    mkdir -p workspace/csr-plus
    # CSR + current Aerith scene as Makou starting point (if you need a fresh working image):
    python3 scripts/apply_layer.py \
      workspace/csr/FINALFANTASY7_D1.bin \
      builder/csr-plus-scene-aerith-house-v0.1.0/layers/disc1.layer.json \
      -o workspace/csr-plus/FINALFANTASY7_D1.bin

## Makou edit (EALS_1)

Open workspace/csr-plus/FINALFANTASY7_D1.bin → field EALS_1 (Aerith house).

1. On field entry (script that runs when Cloud enters at this story beat).
2. Show Elmyra (mom) dialogue; player must close the window (not auto-only).
3. After close: set Game Moment to the value that unlocks leave/continue.
   - Prefer the GM written in vanilla or CSR EALS_1 at house-exit / playground beat.
   - Open CSR or pristine EALS_1 in a second Makou window if needed; copy that GM. Write the number in Evidence.
4. Confirm door/exit is not blocked by a GM check that never becomes true.
5. Scope: EALS_1 only unless a second map is required (document if so).

Save ISO to workspace/csr-plus/FINALFANTASY7_D1.bin.

## Rebuild (copy-paste)

    cd "$(git rev-parse --show-toplevel)"

    OLD=csr-plus-scene-aerith-house-v0.1.0
    NEW=csr-plus-scene-aerith-house-v0.1.1

    python3 scripts/build_field_map_pack.py \
      --pristine workspace/csr/FINALFANTASY7_D1.bin \
      --flavor-image workspace/csr-plus/FINALFANTASY7_D1.bin \
      --files FIELD/EALS_1.DAT \
      --pack-id "$NEW" \
      --version 0.1.1 \
      --disc 1 \
      --name "CSR+ Aerith's house" \
      --group-label "CSR+ Aerith's house" \
      --blurb "CSR+ Aerith's house: Elmyra dialogue on entry; advances game moment so you can leave." \
      --no-exclusive-group \
      --compatible-bases csr-v0.14.1

    python3 scripts/verify_builder_config.py \
      --pristine workspace/pristine/FINALFANTASY7_D1.bin \
      --disc 1 \
      --base csr-v0.14.1 \
      --addon "$NEW"

Manifest: enable NEW; disable OLD; preset csr-plus addons swap OLD → NEW.
Changelog: bases/csr-plus/CHANGELOG.md. Then git add builder/ + changelog + this file, commit, push.

## Playtest

CSR + CSR+ Aerith house v0.1.1. Enter house → Elmyra talks → close → leave/continue OK.

## Evidence

    (GM value + which script group)
    (verify PASS)
    (playtest one-liner)
