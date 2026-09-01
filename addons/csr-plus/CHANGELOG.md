# CSR+ scene add-ons — changelog

## 2026-09-01 — base csr-plus v0.2.0

- The published layer now contains the ENDING2E sectors, so a builder-site disc
  can play its own ending. The Disc 3 ending alias previously ran after the
  layer was diffed, so end users got a disc with no ending at all.
- Ending is truncated to 1106 sectors to fit the MOVIE/ slot it reuses; the
  MOVIE_ID size field stops playback cleanly at the cut.

## 2026-09-01 — base csr-plus v0.1.1

- Adds the City of the Ancients trim (BLIN70_4, LOSLAKE1) to the collapsed base.
  The retired `build_collapsed_bases.py` merged the hojo and endgame scenes but
  silently omitted cota, so v0.1.0 shipped untrimmed COTA maps while Highwind
  shipped trimmed ones. The staged pipeline includes all four scenes.
- Rebuilt from `build_csrplus_staged.py`; no other map content changed.

## 2026-08-01

- csr-plus-scene-endgame-fd-manip-v0.1.0 (disc 3): Sliding down the cliff from the Highwind removed, trimmed green gas screen (FD manip list increments), removed Tifa jumping down from ledge at the top of FD spiral, conversation before final descent removed.

- csr-plus-scene-cota-fd-manip-v0.1.0 (disc 2): when leaving the waterfall with Bugen the gang no longer gets a phone call and the FMV is removed. This impacts the existing Final Descent manipulation, specfically the List value increments will be altered.

## 2026-07-31

- csr-plus-scene-aerith-house-v0.1.1 (disc 1): on enter, Elmyra talks; after
  dialogue you can leave and continue.

## 2026-07 (initial scene split)

- Scenes publish as free add-ons on CSR (csr-v0.14.1), not a monolithic CSR+ base.
- csr-plus-scene-aerith-house-v0.1.0 (disc 1): Aerith house cutscene trim.
- csr-plus-scene-hojo-fd-manip-v0.1.0 (disc 2): Hojo FD manip cutscene trim.
- Retired builder pack csr-plus-v0.1.1 (base); use preset CSR+ (all scenes) or
  individual checkboxes.
