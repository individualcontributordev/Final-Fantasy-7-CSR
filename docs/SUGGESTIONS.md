# Suggestions (CSR / CSR+ / Highwind)

Community and playtest ideas for cutscene bases and scene packs.
Not a release promise. **Open items first**; items already shipped are marked **Done** below them.

Gameplay mods (encounters, battle pacing, etc.):
https://github.com/individualcontributordev/Final-Fantasy-7-Modding/blob/main/docs/SUGGESTIONS.md

History / chat archives:
https://individualcontributor.dev/history/

---

## Products (quick map)

| Product | What it is |
|---------|------------|
| **CSR** | Base: skill checks kept; FMVs and long filler trimmed |
| **CSR+ packs** | Optional scene trims on **CSR only** (builder checkboxes / preset) |
| **Highwind** | Separate aggressive short playthrough; not stacked with CSR+ packs |

---

## Open

### CSR+ packs for side / multi-category routes

CSR base keeps Any%-style skill checks (elev manip text, FD-related waits, known
skips). That helps No Slots / FD routes, but All Bosses, NMS, Wutai, Gelnika,
Gongaga Turks, Kalm extras, etc. still sit through scenes those categories do
not use. Ask (2024-2026, e.g. cornfed, zheal, lemon6559): optional packs so
those scenes can drop without changing the CSR base for runners who still need
the skill-check version.

Pack-shaped examples from chat: Gongaga / Gelnika pre-Turks, Wutai, further
Kalm extras, return-to-Midgar / ship dialogue where safe, and similar category
dead time.

Always note List / FD / manip impact in the pack changelog (same bar as
Aerith house / Hojo FD / CoTA FD packs).

### CSR base polish (cues and light over-trims)

Dialogue options and mash cues that still feel off vs retail: wrong box count
before a choice, missing orient box, or turbo held for nothing because text was
cut. Pattern since early CSR: restore a box or slow a move when practice
transfer suffers; trim only when it stays skill-neutral.

Related: small leftover mashing stretches called out on VODs (e.g. Hope clips
2025-06); scene-by-scene notes whenever someone finishes a full category pass.

### All Bosses / full-category trim pass

A dedicated All Bosses CSR playthrough + notes list was still missing when
asked (zheal 2025-07). Base is playable end-to-end; a VOD would unlock the same
kind of trims NMS got after cornfed written notes.

### Highwind depth

Highwind exists as a short separate base on the builder, but is still thin vs
the original pitch: more corridor / mash-only / freer-order Wall Market-style
cuts, shorter prison / stairs filler where safe. Larger structure or order
changes stay Highwind-only (not CSR+ packs).

### Harder optional cuts (pack or Highwind - not CSR default)

Long-standing hard-cut ideas that must not become CSR default:

- Reactor 1 fast-elevator Barret mash (awesomewaves argued cut; kept on CSR
  as skill check - optional pack only if ever revisited)
- Full strip of skill-check tech (elev / FD / parachute / etc.) - that sits at
  the CSR+ everything / Highwind end of the product split, not on CSR base

### Return-to-Midgar / parachute / raid sequencing

Category and skip questions still come up: parachute skip timing vs full FMV
trim, ship dialogue before raid, Sister Ray FMV visibility, Midgar skip with
CSR (theretrojay 2026-04). Some Midgar-return work already landed on base;
remainder is pack-scope or needs a flag/hardware note if FMV is coupled to
game state.

### Gold Saucer / hotel edge cases

Elixir in Gold Saucer hotel after Cait steals black materia (kleinestennis
2026-07 on PC CSR - verify on PSX). Barret faster 2nd option in the hotel,
gondola animation length, date-tube pacing - several touched 2024-25; re-check
on current CSR if still odd.

### Multi-disc / route-order field duplicates

The same field can exist on more than one disc. A route that hits a scene out
of order can still see untrimmed content. Old note: may need duplicate trims
or a systematic pass when new routes appear.

### Console / hardware verification preference

Prefer fixes proven on real disc swap (PS2 etc.), not only DuckStation.
Document FPGA / POPStarter / burn edge cases when a pack hits them.

---

## Done

**Done - CSR base (skill-check line)**  
Multi-year field trims across discs 1-3 with skill checks kept (elev text,
FD-related material, skip-relevant cues). Iterative restores when over-trim
hurt cues (Wall Market, Kalm boxes, Junon locker tutorial bits, flashback
boxes, etc.). Disc 1 to 2 swap after Jenova Life fixed (v0.4.10 era). Break
scene relocated; cleaner Jenova Life disc-1 end. Boat-to-Costa and related
cleanup in 0.13.x-0.14.x. Large NMS-oriented disc 1 trims from cornfed notes
(church, house, reactor 5, train, Kalm flashback arc, Cosmo, etc.).

**Done - CSR+ scene packs (builder)**  
Not a second full base. Individual packs on CSR: Aerith house, Hojo FD manip,
CoTA / waterfall-related FD impact; all-scenes CSR+ preset. Changelogs call out
List/FD where needed.

**Done - Highwind base on builder**  
Separate aggressive short playthrough (does not stack with CSR+ packs).

**Done - Browser disc builder**  
https://individualcontributor.dev/builder/ - base + CSR+ packs + cross-base
mods; zip with .bin / .cue / APPLIED.txt.

**Done - Keep skill checks on CSR (product decision)**  
2024-11 community split (full strip vs route-preserving CSR). Outcome: CSR
keeps skill checks; aggressive removals go to packs / Highwind - matches the
later why-not-both product split (2026).

**Done - Dialogue-choice cue fixes (many shipped)**  
doumeis / awesomewaves / others: options appearing differently than vanilla.
Many scenes restored or re-cued across 0.5-0.12 (pattern: if it surprises a
runner, put a box back).

**Done - Specific early scene requests (examples)**  
Carry Armor / UWR area trims; rocket-town / Highwind-bridge shortening after
escape pod; Fort Condor chatter; Gold Saucer entry speed; clothes shop / date
movement; Reactor 5 / church / Aerith house NMS pass; disc 3 endgame boxes +
naked-Seph FMV; Rufus locker tutorial partial restore; granny Junon speed;
Sample-adjacent trims; Big Shoes / trains / snowboard landing; etc. Versioned
detail: bases/csr/CHANGELOG.md.

**Done - Rocket look-up scroll left in**  
After a 0.5.3 remove, community asked; reverted so scroll with old man stays.

**Done - Kalm post-photoskip soldier boxes kept**  
cornfed: mashing there softlocks; treated as skill check and left in.

**Done - Community history archive**  
Sanitized chats + chronology: https://individualcontributor.dev/history/

---

## Explicitly not CSR-repo work

| Idea | Where it lives |
|------|----------------|
| No-encounter / density / 0% encounters | Modding repo |
| Battle entry / win / fanfare / boss-death speedups | Modding repo |
| Super Nova fight shortened as engine work | Modding / battle work |
| Official SRC boards / category politics | Out of scope here |
| Stripping skill checks from CSR default | CSR+ packs or Highwind |

---

## How to add more

Play from the builder, then a short note: base + packs, disc, scene, and what
felt wrong or slow. A VOD timestamp helps.
