![](images/banner.png)
*Artist: @Cronosart99*

## Final Fantasy VII PSX & PC CutScenes Removed (CSR)

Category | CSR | CSR+ | Highwind
-------- | ------ | ------ | ------
any% | 🟢 Done | 🔄 WIP | 🔄 WIP
any% No Slots | 🟢 Done | 🔄 WIP | 🔄 WIP
any% Slots | 🟢 Done | 🔄 WIP | 🔄 WIP
any% No Major Skips | 🟢 Done | 🔄 WIP | 🔄 WIP
any% All Bosses | 🔄 WIP | 🔄 WIP | 🔄 WIP
100% No Slots | 🔄 WIP | 🔄 WIP | 🔄 WIP

*Est. Completion Time: 1 bazillion years*

Platforms: PS1 / PS2 disc, emulator, or PC via TMD's [PC installer](https://drive.google.com/file/d/1VXQtJZD6TrG3RXO6kPYduW5EGEBmQsAP/view?usp=drive_link).

## Definitions

### CSR (base)

Skill checks stay (dialogue choices, movement in cutscenes, skips, RNG manip, etc.). Most FMVs removed, some cutscenes shortened, long mash sequences reduced. Plays like a normal run, shorter. Selectable in the builder as a base, alongside Unmodified.

### CSR+ scene add-ons

Individual, mixable trims that go further than CSR for a specific scene — pick and choose only the ones you want on top of the CSR base, instead of committing to a whole extra tier. Currently ships one: `csr-plus-scene-aerith-house` (Aerith's house cutscene). More will be added as they're decomposed from the old monolithic CSR+ pack.

### Highwind (base)

An aggressively trimmed playthrough — its own separate mod, not a bigger CSR+. Story mechanics, option choices, and complete dialogue are cut. Selectable in the builder as a base alongside Unmodified and CSR, but **doesn't stack with CSR+ scene add-ons** — those are different, incompatible edits to the same scenes.

## Changelogs

Full map: **[CHANGELOGS.md](CHANGELOGS.md)**.

| Product | Changelog | Builder ids |
|---------|-----------|-------------|
| CSR (base) | [bases/csr/CHANGELOG.md](bases/csr/CHANGELOG.md) | `csr-v0.14.1` |
| Highwind (base) | [bases/highwind/CHANGELOG.md](bases/highwind/CHANGELOG.md) | `highwind-v0.2.0` |
| CSR+ scenes (add-ons) | [addons/csr-plus/CHANGELOG.md](addons/csr-plus/CHANGELOG.md) | `csr-plus-scene-*`, preset `csr-plus` |

## Play

https://individualcontributor.dev/builder/

1. Clean **NTSC-U** `.bin` (disc auto-detected)
2. Pick a base: Unmodified, CSR, or Highwind
3. On CSR: add any CSR+ scene add-ons and/or Field/World encounter density
4. Build zip → `.bin` + `.cue` + `APPLIED.txt`

Emulator: [DuckStation](https://github.com/stenzek/duckstation/releases) or RetroArch + SwanStation — open the `.cue`.

PSX: soft-mod (e.g. [MechaPwn](https://github.com/MechaResearch/MechaPwn)), burn from the `.cue`.

## Release a base (maintainers)

Run these steps on the machine that has the disc images. Agent chat supplies the checklist; it does not own the publish path when bins are only on the disc host.

Publishable bases: **CSR** and **Highwind** only. CSR+ scene trims are add-ons (see `docs/ADDON_QUICK_REFERENCE.md` / skill `ship-csr-plus-scene`), not a third base.

Local discs (gitignored):

| Role | Path |
|------|------|
| Retail (required) | `pristine/FINALFANTASY7_DN.bin` |
| CSR base cache | `cache/csr/FINALFANTASY7_DN.bin` (auto-built by verify/scripts) |
| Highwind base cache | `cache/highwind/FINALFANTASY7_DN.bin` |
| Session edits | builder zip extract (not under pristine/) |

`cache/` holds reconstructed **bases** for faster verify and add-on rebuilds. First
`verify_builder_config --base csr-v…` writes `cache/csr/` if missing.

Missing CSR/Highwind images? Reconstruct from pristine + published layer:

```bash
python scripts/apply_layer.py \
  pristine/FINALFANTASY7_D1.bin \
  builder/csr-v0.14.1/layers/disc1.layer.json \
  -o cache/csr/FINALFANTASY7_D1.bin
```

### Clean EDC before layer rebuild (important)

Makou/CDmage injects often **zero Mode2 Form1 footers**. Diffing that bakes EDC zeros into `builder/` layers.

Before `build_csr_base_layers.py`, repair each **base** disc against pristine:

```bash
# names must be FINALFANTASY7_D1.bin … (rename Redump titles if needed)
python scripts/repair_mode2_edc.py \
  --pristine pristine/FINALFANTASY7_D1.bin \
  --input cache/csr/FINALFANTASY7_D1.bin \
  --in-place
# repeat for D2/D3 and for cache/highwind
```

Then rebuild **one** base at a time. Expect far fewer records (no thousands of footer-only zeros).

```bash
cd /c/path/to/Final-Fantasy-7-CSR   # shell on the disc host
git pull

# CSR or Highwind only — bump version, update bases/<base>/CHANGELOG.md
python scripts/build_csr_base_layers.py cache/csr --version 0.14.2
# python scripts/build_csr_base_layers.py cache/highwind --version 0.1.2

git add builder/ bases/
git commit -m "Release CSR v0.14.2."
git push
```

Do **not** run `build_csr_base_layers.py cache/csr-plus` for a normal publish — that folder is Makou source for CSR+ scene increments.

Pages serves `builder/` JSON for the disc builder. Older packs stay enabled until you set `"enabled": false` in `builder/manifest.json`.

If the published base **id** changed (e.g. `csr-v0.14.2`), rebuild Field/World encounter packs in **Final-Fantasy-7-Modding** against the new ids.

Agent checklists: `.agents/skills/release-csr-base`, `ship-csr-plus-scene`, `ship-makou-addon`.

## Layout

```
bases/           base changelogs (csr, highwind)
addons/          add-on family changelogs (csr-plus scenes)
builder/         published layers + manifest.json (Pages CDN)
scripts/         layer helpers + local_paths.py
pristine/        retail discs (gitignored)
cache/           optional reconstructed bases (gitignored)
temp/            playtest apply_layer outputs (gitignored)
images/          README assets
CHANGELOGS.md    index of all release notes
```

## Contributors

IndividualContributor, Okamikaze, AwesomeWaves, Teeejj, Shoutblaster, HopeDRG, Doumeis, Cornfed69, Phek1200, MuscleBelt, Rendall, Expans3, Katombaz, Jayrod, TMD

## Leaderboard / feedback

- [Submit time](https://forms.gle/byFWCT85gFWS2Vtp6) · [Leaderboard](https://docs.google.com/spreadsheets/d/19y6yHtODjS5R-VyvtHUKjAo3FL9Fif56p1REQsUzGWg)
- [Feature requests / bugs](https://forms.gle/dW9rMCD9kQ3eBPSM8)

![](images/leaderboard.PNG)

## Troubleshooting

Keep each disc’s `.bin` and `.cue` in the same folder with the same stem. The `.cue` `FILE` line must match the `.bin` name. Update any `.m3u` to the patched cues.
## Suggestions backlog

Community-prioritised CSR / CSR+ / Highwind ideas: [docs/SUGGESTIONS.md](docs/SUGGESTIONS.md)
## History

Community development story (archived chats):
https://individualcontributor.dev/history/
