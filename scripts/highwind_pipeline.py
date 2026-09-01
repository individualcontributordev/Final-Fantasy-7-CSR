"""Highwind-specific sources: same collapse as CSR+, plus Disc 1 extras.

Highwind is not a second D2/D3 merge. It rebuilds the CSR+-shaped Disc 1 from
CSR discs and scene trims (the same functions CSR+ uses, not the published
csr-plus pack), then copies a fixed list of early Disc 1 field payloads from
Highwind's own pre-collapse Disc 1 layer.

Do not read builder/csr-plus/ or a CSR+ build/ directory. The two bases stay
independent catalogs; they only share collapse/safety code.

SNOVA, FIELD.BIN headroom, EDC/ECC, and layer round-trip stay in the shared
stages used by both bases.

Inputs are tracked Highwind/CSR layers plus pristine discs; outputs are
write-once source and collapse artifacts under the caller's run directory.
Only the named FIELD.DAT payloads are taken from Highwind's pre-collapse D1,
and each copy is extracted back for equality before embedded FIELD/WORLD
tables are repaired. This module does not publish, inject endgame assets, or
perform final sector repair; the staged driver owns those boundaries.
"""
from __future__ import annotations

import json
from pathlib import Path

from build_csrplus_staged import (
    ROOT,
    apply_layer,
    build_source_artifacts,
    collapse_to_disc1,
    fix_field_and_world_bins,
    pristine,
    save_stage,
    sha256,
    source_json,
    write_json,
    write_new,
)
from psx_mode2_iso import extract_file, replace_file_within_sectors

HIGHWIND_D1_LAYER = "sources/highwind-3disc/layers/disc1.layer.json"

# FIELD/*.DAT that differ between that Highwind Disc 1 and CSR Disc 1, except
# EALS_1.DAT (CSR+ Aerith-house trim owns that file after collapse).
HIGHWIND_D1_EXTRA_FIELDS = (
    "COLNE_1",
    "ELEVTR1",
    "JUNDOC1A",
    "LOST2",
    "MD1_1",
    "MD8_1",
    "MD8_2",
    "MDS7",
    "MDS7PB_1",
    "MDS7PB_2",
    "MKTINN",
    "MKTPB",
    "MKT_M",
    "MKT_S1",
    "MRKT2",
    "MRKT3",
    "NMKIN_1",
    "NMKIN_3",
    "NMKIN_5",
    "NRTHMK",
    "SHPIN_3",
)


def build_highwind_source_artifacts(csr: Path, output_dir: Path) -> dict:
    """CSR+ source discs plus Highwind's own Disc 1 extras image."""
    report = build_source_artifacts(csr, output_dir)
    csr = csr.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()

    layer = source_json(HIGHWIND_D1_LAYER)
    layer_path = output_dir / "00-inputs" / "highwind-d1-extras" / "disc1.layer.json"
    write_json(layer_path, layer)

    extras_image = bytearray(pristine(csr, 1).read_bytes())
    apply_layer(extras_image, layer)
    extras_path = output_dir / "06-highwind-d1-extras" / "FINALFANTASY7_D1.bin"
    write_new(extras_path, bytes(extras_image))

    report["stage"] = "highwind-sources"
    report["highwindD1ExtrasLayer"] = {
        "path": str(layer_path),
        "sha256": sha256(layer_path),
    }
    report["highwindD1ExtrasImage"] = str(extras_path)
    report["highwindD1ExtrasSha256"] = sha256(extras_path)
    report["highwindD1ExtraFields"] = list(HIGHWIND_D1_EXTRA_FIELDS)
    report["cacheArtifacts"][
        str(extras_path.relative_to(output_dir))
    ] = report["highwindD1ExtrasSha256"]
    # build_source_artifacts already wrote stage-report.json; refresh it.
    report_path = output_dir / "stage-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def collapse_highwind_disc1(
    sources_dir: Path,
    output_dir: Path,
) -> tuple[Path, dict]:
    """CSR+ collapse, then surgical Highwind Disc 1 field copies."""
    sources_dir = sources_dir.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    extras_path = sources_dir / "06-highwind-d1-extras" / "FINALFANTASY7_D1.bin"
    if not extras_path.is_file():
        raise SystemExit(f"Missing Highwind Disc 1 extras image: {extras_path}")

    collapsed = collapse_to_disc1(sources_dir, output_dir)
    image = bytearray(collapsed.read_bytes())
    extras = extras_path.read_bytes()

    applied: list[str] = []
    for field in HIGHWIND_D1_EXTRA_FIELDS:
        path = f"FIELD/{field}.DAT"
        payload = extract_file(extras, path)
        replace_file_within_sectors(image, path, payload)
        if extract_file(image, path) != payload:
            raise SystemExit(f"Highwind extra did not round-trip: {path}")
        applied.append(path)
    extras_applied_path = save_stage(output_dir, "07-highwind-d1-extras.bin", image)

    table_patches = fix_field_and_world_bins(image)
    final_path = save_stage(output_dir, "08-field-world-tables-fixed.bin", image)
    report = {
        "stage": "highwind-collapse",
        "sourcesDir": str(sources_dir),
        "csrplusShapedCollapse": str(collapsed),
        "highwindD1ExtrasImage": str(extras_path),
        "appliedExtraFields": applied,
        "tableEntriesPatchedAfterExtras": table_patches,
        "artifacts": {
            "afterExtras": str(extras_applied_path),
            "tableFixed": str(final_path),
        },
        "outputSha256": sha256(final_path),
    }
    write_json(output_dir / "stage-report.json", report)
    return final_path, report


def default_csr() -> Path:
    return ROOT
