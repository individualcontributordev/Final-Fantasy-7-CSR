# CSR product suggestions (community)

Source: FF7 speedrun Discord CSR channel export (2024-11 → 2026-07),
~1700 messages. Demand = how often runners raised it + whether multiple
people pushed the same idea. This is a **maintainer backlog**, not a promise.

Cross-link: Modding engine/mods list →
[Final-Fantasy-7-Modding `docs/SUGGESTIONS.md`](https://github.com/individualcontributordev/Final-Fantasy-7-Modding/blob/main/docs/SUGGESTIONS.md).

## Product lines (current)

| Product | Role |
|---------|------|
| **CSR** base | Skill checks kept; long/non-essential cutscenes trimmed. Practice-friendly Any%/NMS/etc. |
| **CSR+ packs** | Optional scene trims **on CSR only** (builder checkboxes / preset). |
| **Highwind** base | Aggressive “dad mode” full-game shortener; **not** CSR+; no CSR+ scene packs. |

---

## Done (shipped or settled)

### CSR base (ongoing trims — representative)

Community-driven field trims landed across v0.5–v0.14 (Rocket Town, Carry Armor /
UWR, Midgar raid, trains, Wall Market, NMS paths, Highwind bridge Cosmo, etc.).
Many Doumeis/Phek/Waves/Hope notes were applied or explicitly reverted for muscle
memory (e.g. Wall Market pink guy → 4 boxes; some text restored after JDeath).

### CSR+ scene packs

| Pack | Status | Notes |
|------|--------|--------|
| Aerith house | **Done** v0.1.1 | Long-standing “sit through Elmyra” complaint (Doumeis et al.). |
| Hojo FD manip | **Done** v0.1.0 | Aggressive FD-adjacent trim on CSR. |
| CoTA / waterfall FD | **Done** v0.1.0 | Bugenhagen phone/FMV cut; **changes FD List** — re-route. |
| Preset “CSR+ (all scenes)” | **Done** | Builder preset stacks enabled scene packs. |

### Highwind

| Item | Status |
|------|--------|
| Highwind as separate base (ex-CSR++) | **Done** v0.1.1 on builder |
| Explicit: Highwind ≠ stack of CSR+ packs | **Done** (docs + builder) |

### Tooling (player-facing)

| Item | Status |
|------|--------|
| In-browser disc builder (base + packs + mods) | **Done** |
| Per-disc pack UI / presets | **Done** |

---

## To do — prioritised

Priority = community demand × fit for **this** product line × feasibility.
P1 = do next when capacity; P2 = backlog; P3 = nice-if.

### P1 — CSR+ packs (category-specific optional cuts)

| ID | Suggestion | Demand | Why P1 |
|----|------------|--------|--------|
| P-01 | **More optional scene packs** for cuts that help NMS / All Bosses / Hundo but hurt No Slots skill-check training if forced into CSR | High (Cornfed multi-category; IC “why not both”) | Matches architecture: CSR stays faithful; packs opt in. |
| P-02 | **Gongaga pre-Turks**, **Gelnika pre-Turks**, **Kalm old man**, **Wutai story + pagoda** as separate packs (or one “All Bosses extras” pack) | Med–High (Phek All Bosses) | Clear optional content; don’t put in CSR base. |
| P-03 | **Return-to-Midgar / ship dialogue** further optional pack (keep parachute skill where needed) | Med (Cornfed, Jayrod) | Partly trimmed on CSR; remainder is pack territory. |
| P-04 | Document **FD / List impact** on every FD-touching pack (CoTA done in changelog; extend) | High for runners | Prevents silent route breaks. |

### P2 — CSR base polish (skill-check preserving)

| ID | Suggestion | Demand | Notes |
|----|------------|--------|--------|
| B-01 | Dialogue **option cues = vanilla** (count/timing of boxes before choices) | High (Doumeis Rufus parade, boat, sub friends, JBirth) | Partially addressed; audit remaining hotspots. |
| B-02 | **Post–J-Death** movement cue (enough boxes / clear when to move) | Med (Phek) | Some boxes restored; verify still OK. |
| B-03 | **Post–CoTA → Highwind → Diamond Weapon** further trim without breaking DW | Med (Phek) | CSR base if skill-neutral; else pack. |
| B-04 | NMS-only leftover trims still on CSR that no longer need to block No Slots | Med | Prefer **pack** if category-skewed. |
| B-05 | Vincent recruit / deep side content trim | Low–Med (Teejj) | Better as pack or Highwind, not CSR base. |

### P2 — Highwind

| ID | Suggestion | Demand | Notes |
|----|------------|--------|--------|
| H-01 | Continue “filler” cuts: stairs/prison/WM order freedom, mash-only dialogues | High for **Highwind users** | Aligns with stated Highwind scope. |
| H-02 | Optional **promote** individual Highwind cuts back to CSR+ packs where safe on CSR | Med (IC) | Only if pack stays CSR-compatible. |
| H-03 | Jessie reactor stuck-leg / major order changes | Med | Highwind-only; keep off CSR. |

### P3

| ID | Suggestion | Notes |
|----|------------|--------|
| X-01 | Practice NPC toggles (e.g. “sick guy” predictable elev manip) | Tried; RNG lock on console failed — park unless engine approach. |
| X-02 | Per-category CSR forks (NMS CSR, All Bosses CSR as full bases) | Prefer **packs on CSR** over many bases. |

---

## Deprioritised / reject (for CSR products)

| Suggestion | Why deprioritise |
|------------|------------------|
| Force **all** cutscenes out of **CSR base** (including FD/elev skill scenes) | Community split; solved by **CSR+ packs**, not gutting CSR. |
| **SRC leaderboard** as CSR product goal | Mods explicitly not treating CSR as board category; channel = dev discussion. |
| **Shinra stairs shortened** on CSR (Hope-style) | Rejected after elev comparison — keeps muscle memory (Doumeis agreed). |
| **Remove parachute FMV** with movement | Technically blocked (movement in movie); Midgar raid already heavily trimmed. |
| **No-encounter cheat on CSR itself** | Belongs in **Modding** encounter mods (0% / toggles), not cutscene base. |
| Over-trim to FF9-CSR “constant warp” feel | Cornfed: leaves runners unprepared; CSR should keep some scene breathing room. |
| PC-only shortcuts that break PSX state (e.g. boat→Costa as Chocobo stuck) | Console/disc truth first. |

---

## Suggested next ships (short)

1. One more **CSR+ pack** from P-02 (All Bosses / NMS value).  
2. B-01 cue audit on remaining option dialogues.  
3. Highwind H-01 filler pass when CSR base is quiet.  
4. Keep FD-impact notes on every pack changelog.

Engine/battle/encounter ideas → **Modding** suggestions doc.
