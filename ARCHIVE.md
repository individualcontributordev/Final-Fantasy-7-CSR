# Archive

Scripts, docs, and releases this repo used to carry. Nothing here is
maintained; the links go to the commit that removed each set, which is where
the last working copy lives. `git show <sha>^:<path>` prints a file as it was.

## Releases

The last PPF release of old CSR is v0.14.1 (CSR+ / CSR++ v0.1.1), in
[`a0fd3f2`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/a0fd3f229073363911f376ac07f310285db23186).
Current releases are `ic-layer-v1` JSON only.

| Removed | Was | Commit |
|---|---|---|
| `v0.1.1/` … `v0.4.010/` PPFs | One directory per patch version | [`16e7d01`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/16e7d01) |
| `csr/`, `csr+/`, `csr++/` PPFs | Long-name duplicates of the v0.14.1 / v0.1.1 patches | [`fc7c421`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/fc7c421) |
| `patcher/` site, `patches.zip`, `notes.md` | Browser PPF patcher, replaced by the disc builder | [`b33652c`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/b33652c), [`8a90364`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/8a90364) |

## Docs

| Removed | Was | Commit |
|---|---|---|
| `docs/INSTRUCTIONS.md`, `MANUAL_CSR_BASE_BUILD_GUIDE.md`, `CREATE_ADDON_FROM_MAKOU.md`, `ADDON_QUICK_REFERENCE.md`, `SUGGESTIONS.md` | Hand-build and addon-authoring guides, now the README's build/edit/repair/publish loop | [`c88dd41`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/c88dd41) |
| `CHANGELOGS.md`, `bases/*/CHANGELOG.md`, `addons/csr-plus/CHANGELOG.md` | Per-base changelogs; `VERSION` plus git log covers it | [`c88dd41`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/c88dd41), [`e57802d`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/e57802d) |
| `notes/2026-07-*.md` | ImgBurn verification, CSR+ pivot, mixable field packs | [`c88dd41`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/c88dd41) |
| `docs/windows-last-task.md`, `windows-last-output.txt` | Windows handoff scratch files | [`e07eb9d`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/e07eb9d), [`710d431`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/710d431) |
| Nested `README.md` files under `builder/`, `workspace/` | Per-directory instructions | [`c5ee694`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/c5ee694) |
| `.agents/`, `.augment/`, `.cursor/` skills, `AGENTS.md` | Release and ship-scene agent skills | [`d38a935`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/d38a935), [`2ac5ca7`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/2ac5ca7) |
| `images/leaderboard.PNG` | Orphaned asset | [`f233a6d`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/f233a6d) |

## Scripts

| Removed | Was | Commit |
|---|---|---|
| `build_csrplus_staged.py`, `build_highwind_staged.py`, `highwind_pipeline.py`, `pipeline_cache.py`, `merge_safe_fields.py`, `merge_rework_fields.py`, `inject_movies_by_disc_id.py`, `inject_snova_d3_to_d1.py`, `alias_d3_ending_lbas_on_d1.py`, `fix_field_bin_table.py`, `fix_junair_air0_slot3.py` | Staged disc-collapse pipeline that produced CSR+ and Highwind before the layer workflow | [`dbe22a3`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/dbe22a3) |
| `field_dat.py`, `field_dat_write.py`, `ff7_opcodes.py`, `lzs.py`, `disc_sources.py` | Field script parsing, opcode tables, LZS codec | [`dbe22a3`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/dbe22a3) |
| `field_maplist.py`, `field_jump_graph.py`, `list_changed_field_maps.py`, `build_field_map_pack.py` | Field map inventory and per-map packs | [`c88dd41`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/c88dd41) |
| `compress_gzipps.py`, `psx_mode2_iso.py`, `verify_iso_integrity.py`, `bin_diff_to_layer.py`, `edc_ecc.py` | Overlay and ISO tooling | moved to the Modding repo in [`dbe22a3`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/dbe22a3) |
| `publish_release_candidate.py`, `build_csr_base_layers.py`, `update_addon_from_builder_zip.py`, `verify_csr_addon_compat.py` | Release and compat helpers, replaced by `build_base_layer.py` plus `verify_builder_config.py` | [`dbe22a3`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/dbe22a3), [`c9a8d02`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/c9a8d02), [`c88dd41`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/c88dd41) |
| `local_paths.py` (top level) | Moved under `scripts/libs/` | [`dbe22a3`](https://github.com/individualcontributordev/Final-Fantasy-7-CSR/commit/dbe22a3) |
