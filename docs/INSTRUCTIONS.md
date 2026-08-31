# Instructions

## Status: active — release CSR base patch (field 119 NRTHMK dir/31 movie no longer reachable)

You already edited Disc 1 in Makou and saved the fix into your working CSR
image (the copy where you fixed the bug). Run these on the disc host
(Git Bash), from the repo root.

### 1. Pull latest

```bash
cd /c/path/to/Final-Fantasy-7-CSR
git pull --ff-only
```

### 2. Put your edited Disc 1 in place

Make sure your fixed image is at `cache/csr/FINALFANTASY7_D1.bin`
(the file you just edited/saved in Makou). If it's elsewhere, copy it there:

```bash
mkdir -p cache/csr
cp /path/to/your/edited/FINALFANTASY7_D1.bin cache/csr/FINALFANTASY7_D1.bin
```

### 3. Repair EDC before diffing

```bash
python3 scripts/repair_mode2_edc.py \
  --pristine pristine/FINALFANTASY7_D1.bin \
  --input cache/csr/FINALFANTASY7_D1.bin \
  --in-place
```

### 4. Build the new CSR layer (bump patch version)

```bash
python3 scripts/build_csr_base_layers.py cache/csr --version 0.14.2
```

This overwrites `builder/csr/layers/`, `builder/csr/pack.json`, and
`builder/csr/VERSION` in place (base id stays `csr`) — no new versioned
directory is created. Git history is the version log.

### 5. Verify (must print PASS)

```bash
python3 scripts/verify_builder_config.py \
  --pristine pristine/FINALFANTASY7_D1.bin \
  --disc 1 \
  --base csr
```

### 6. Scene add-on regression (required for a CSR base release)

```bash
python3 scripts/verify_csr_addon_compat.py
```

If this FAILS, stop and report back — do not continue to commit.

### 7. Changelog

Add an entry to `bases/csr/CHANGELOG.md` for `0.14.2`, e.g.:

> Fix: field 119 (NRTHMK) `dir/31` movie script is no longer reachable
> (was a dead orphan `MOVIE` opcode never invoked by the engine; now
> genuinely unreachable at the byte level).

### 8. Commit and push

```bash
git add builder/ bases/
git commit --author="individualcontributordev <contributorindividual@gmail.com>" \
  -m "Release CSR v0.14.2: fix NRTHMK dir/31 movie reachability"
git push
```

### 9. Re-verify

`git pull` and re-run the movie-requirements scan against this repo to
confirm NRTHMK's `dir/31` `MOVIE` opcode is now excluded from the disc-1
movie requirement set.

Note: the published base id (`csr`) does not change between releases — only
`builder/csr/VERSION` and the `CHANGELOG.md` entry do. Modding's Field/World
encounter packs' `compatibleBases: ["csr"]` do not need updating for a normal
patch release.
