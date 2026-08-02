# Task: Ship no-swap hub pack (clean / pristine D1)

Operational handoff. Agent overwrites this file and pushes.
You: git pull --ff-only, run steps, fill Evidence, commit+push builder JSON only. Say **check**.

## Goal

Ship a **builder pack** (Makou FIELD **add-on**, not a base, not an engine mod).
It removes the four Ask-for-disc ops in **blackbgb** (#103) S0-Main on
**Unmodified (clean)** Disc 1 only.

RE done in Modding findings; working bin playtested in DuckStation.
This turn = **diff to pack to verify to commit**.

## Product (pack)

| Field | Value |
|-------|--------|
| Kind | pack (add-on checkbox) |
| Pack id | no-swap-blackbgb-hub-v0.1.0 |
| Name | No disc-swap (hub) |
| Disc | 1 only |
| Diff baseline | pristine |
| compatibleBases | clean only (v0.1.0) |
| exclusiveGroup | omit (--no-exclusive-group) |
| Blurb | Skips disc 2/3 prompts at the blackbgb hub; map jumps still run. Unmodified disc 1. Prototype pack. |

Not a CSR/Highwind base bump. Not a Modding encounter/engine mod.
Do not claim full single-disc game yet (other Ask maps + multi-disc movies open).

## Preconditions

- CSR git pull --ff-only
- pristine/FINALFANTASY7_D1.bin
- Edited image, e.g.
  ../Final-Fantasy-7-Modding/workspace/iso-extract/ff7_d1_noswap_re.bin
  or copy: mkdir -p temp/no-swap && cp <edited> temp/no-swap/FINALFANTASY7_D1.bin

## Steps

### 1. Paths

```bash
cd "$(git rev-parse --show-toplevel)"
git pull --ff-only
PRISTINE="pristine/FINALFANTASY7_D1.bin"
EDITED="temp/no-swap/FINALFANTASY7_D1.bin"
# or: EDITED="../Final-Fantasy-7-Modding/workspace/iso-extract/ff7_d1_noswap_re.bin"
test -f "$PRISTINE" && test -f "$EDITED"
```

### 2. Diff FIELD maps

```bash
mkdir -p temp/no-swap
python3 scripts/list_changed_field_maps.py \
  --pristine "$PRISTINE" \
  --patched "$EDITED" \
  -o temp/no-swap/diff-d1.json
cat temp/no-swap/diff-d1.json
```

Expect blackbgb (maybe small Makou side files). Hundreds of maps -> stop, re-check EDITED.

### 3. Build pack

```bash
python3 scripts/build_field_map_pack.py \
  --pristine "$PRISTINE" \
  --edited-image "$EDITED" \
  --files FIELD/BLACKBGB.DAT \
  --pack-id no-swap-blackbgb-hub-v0.1.0 \
  --disc 1 \
  --name "No disc-swap (hub)" \
  --group-label "No disc-swap (hub)" \
  --blurb "Skips disc 2/3 prompts at the blackbgb hub; map jumps still run. Unmodified disc 1. Prototype pack." \
  --no-exclusive-group \
  --compatible-bases clean \
  --version 0.1.0
```

Add any other FIELD/*.DAT from the diff that belong to this edit.

### 4. Verify (required)

```bash
python3 scripts/verify_builder_config.py \
  --pristine "$PRISTINE" \
  --disc 1 \
  --base clean \
  --addon no-swap-blackbgb-hub-v0.1.0
# must PASS
```

### 5. Commit pack JSON only

```bash
git add builder/no-swap-blackbgb-hub-v0.1.0 builder/manifest.json
git status -sb
git commit -m "Pack: no-swap-blackbgb-hub-v0.1.0 (clean D1 hub)."
git push
```

Never commit .bin / temp/ extracts.

## Evidence

```
EDITED path:
Changed maps:
build_field_map_pack: OK / fail
verify clean + pack: PASS / fail
commit:
```

## Done when

- Pack on main under builder/, verify PASS
- Say **check**

## Out of scope

- CSR / Highwind compatibleBases (next: byte-compare or per-base packs)
- blackbg3 / blackbge / multi-disc movies
- Engine work in Final-Fantasy-7-Modding
