# Task: Ship no-swap hub pack (clean / pristine D1)

Operational handoff. Agent overwrites this file and pushes.
You: git pull --ff-only, run steps, fill Evidence, commit+push builder JSON only. Say **check**.

## Goal

Publish a **checkbox** Makou FIELD add-on that removes the four `Ask for disc`
ops in **blackbgb** (#103) S0-Main on **Unmodified (clean)** Disc 1.

RE is done (Modding findings 2026-08-02-noswap-*). Working edit already
playtested in DuckStation. This turn = **diff → pack → verify → commit**.

## Product

| Field | Value |
|-------|--------|
| Pack id | `no-swap-blackbgb-hub-v0.1.0` |
| Name | No disc-swap (hub) |
| Disc | **1** only |
| Baseline | **pristine** |
| `compatibleBases` | `clean` only for v0.1.0 |
| `exclusiveGroup` | none (`--no-exclusive-group`) |
| Blurb | Skips disc 2/3 prompts at the blackbgb hub; map jumps still run. Unmodified disc 1. Prototype. |

Do **not** claim full single-disc game yet (other Ask maps + multi-disc movies still open).

## Preconditions

- CSR repo pull
- Pristine: `pristine/FINALFANTASY7_D1.bin`
- Edited image (from Modding RE machine), e.g. sibling path:
  `../Final-Fantasy-7-Modding/workspace/iso-extract/ff7_d1_noswap_re.bin`
  Copy into CSR if easier:
  `mkdir -p temp/no-swap && cp <edited> temp/no-swap/FINALFANTASY7_D1.bin`

## Steps

1. `git pull --ff-only` (CSR)
2. Set paths (adjust EDITED if needed):

```bash
cd "$(git rev-parse --show-toplevel)"
git pull --ff-only
PRISTINE="pristine/FINALFANTASY7_D1.bin"
# prefer local copy under temp/
EDITED="temp/no-swap/FINALFANTASY7_D1.bin"
# or:
# EDITED="../Final-Fantasy-7-Modding/workspace/iso-extract/ff7_d1_noswap_re.bin"
test -f "$PRISTINE" && test -f "$EDITED"
```

3. List changed FIELD maps:

```bash
mkdir -p temp/no-swap
python3 scripts/list_changed_field_maps.py \
  --pristine "$PRISTINE" \
  --patched "$EDITED" \
  -o temp/no-swap/diff-d1.json
# paste or summarize the map list under Evidence
cat temp/no-swap/diff-d1.json
```

Expect **blackbgb** (and maybe small Makou side files). If hundreds of maps, stop and re-check EDITED vs pristine.

4. Build pack (use exact changed files from the JSON if more than one DAT):

```bash
# If only blackbgb.DAT changed:
python3 scripts/build_field_map_pack.py \
  --pristine "$PRISTINE" \
  --edited-image "$EDITED" \
  --files FIELD/BLACKBGB.DAT \
  --pack-id no-swap-blackbgb-hub-v0.1.0 \
  --disc 1 \
  --name "No disc-swap (hub)" \
  --group-label "No disc-swap (hub)" \
  --blurb "Skips disc 2/3 prompts at the blackbgb hub; map jumps still run. Unmodified disc 1. Prototype." \
  --no-exclusive-group \
  --compatible-bases clean \
  --version 0.1.0
```

If `list_changed_field_maps` shows other `FIELD/*.DAT` that Makou rewrote for the same edit, include them in `--files` (space-separated). Prefer only maps required for the hub fix.

5. Verify (required):

```bash
python3 scripts/verify_builder_config.py \
  --pristine "$PRISTINE" \
  --disc 1 \
  --base clean \
  --addon no-swap-blackbgb-hub-v0.1.0
# must PASS
```

6. Changelog / docs (short):
   - If you keep a pack-adjacent note, one line in Evidence is enough this turn.
   - Do **not** commit `.bin` / `temp/` extracts.

7. Commit and push:

```bash
git add builder/no-swap-blackbgb-hub-v0.1.0 builder/manifest.json
git status -sb   # no .bin
git commit -m "Add no-swap-blackbgb-hub-v0.1.0 (clean D1 hub Ask removal)."
git push
```

## Evidence

```
EDITED path:
Changed maps (from diff-d1.json):
build_field_map_pack: OK / fail
verify_builder_config clean + addon: PASS / fail
commit:
```

## Done when

- Pack on `main`, verify PASS
- Say **check**

## Out of scope this turn

- CSR / Highwind compatibleBases (next: byte-compare or per-base packs)
- blackbg3 / blackbge / multi-disc movies
- Modding engine packs
