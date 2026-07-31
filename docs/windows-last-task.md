# Task: (idle)

Last ship: **csr-plus-scene-cota-fd-manip-v0.1.0** (2026-08-01).

## Check result (Mac)

- Pack maps: FIELD/BLIN70_4.DAT, FIELD/LOSLAKE1.DAT (disc 2) — no Hojo maps
- compatibleBases: csr-v0.14.1; checkbox (no exclusiveGroup)
- Preset csr-plus includes CoTA + Hojo + Aerith
- verify_builder_config CSR + CoTA D2: PASS
- verify_builder_config CSR + Hojo + CoTA D2: (see latest check)
- verify_csr_addon_compat: PASS (3 stacks)

Changelog notes FD List increments change with this trim — runners should re-validate routes.

## Copy-paste

    cd "$(git rev-parse --show-toplevel)"
    git pull --ff-only

## Evidence

    (none — idle)
