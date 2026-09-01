#!/usr/bin/env python3
"""Build, stabilize, and package the independent Highwind Disc 1 release.

Normal workflow:

  python3 scripts/build_highwind_staged.py prepare \
    --run-name my-highwind-edit

  # Open 03-working/HIGHWIND_D1.bin in Makou Reactor. Save to a new filename.

  python3 scripts/build_highwind_staged.py finalize \
    --run-dir build/highwind/my-highwind-edit \
    --edited-image /path/to/makou-saved.bin \
    --version 0.2.1

``prepare`` reconstructs shared CSR/trim sources, applies Highwind's tracked
Disc 1 field set after collapse, repairs embedded lookup tables, and creates a
hash-recorded Makou checkpoint. ``finalize`` requires a separately saved Makou
image, then performs stabilization, SNOVA/ending injection, Form 1 EDC/ECC
repair, exact layer round-trip verification, and console BIN/CUE generation.

All outputs stay under ``build/highwind/<run>/`` until the separate publish
command. Resume accepts only SHA-256-matching stages; forced rebuilds preserve
replaced directories under ``recovery/``. Pristine images and tracked layers
are never modified, and Highwind does not consume a published CSR+ pack.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from build_csrplus_staged import (
    ENDING_ALIAS_OVERLAPS,
    ROOT,
    build_release_artifacts,
    configure_sources,
    copy_new,
    cue_for,
    inject_ending_alias_image,
    inject_snova_image,
    pristine,
    sha256,
    stabilize_working_image,
    verify_changed_edc_ecc,
    verify_disc_bounds,
    verify_iso_layout,
    write_json,
    write_new,
)
from highwind_pipeline import (
    build_highwind_source_artifacts,
    collapse_highwind_disc1,
)
from pipeline_cache import archive_path, cached_artifacts, cached_output, load_report


def prepare(args: argparse.Namespace) -> None:
    """Run or safely resume Highwind source, collapse, and working stages."""
    csr = ROOT
    configure_sources(csr)
    run_name = args.run_name or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = csr / "build" / "highwind" / run_name
    sources_dir = run_dir / "01-sources"
    collapse_dir = run_dir / "02-collapse"
    working_dir = run_dir / "03-working"
    collapsed = collapse_dir / "08-field-world-tables-fixed.bin"
    working_image = working_dir / "HIGHWIND_D1.bin"

    if run_dir.exists() and not (args.resume or args.rebuild_from):
        raise SystemExit(
            f"Build run already exists: {run_dir}\n"
            "Use --resume to reuse verified stages, or --rebuild-from "
            "sources|collapse|working to force a stage and everything after it."
        )

    rebuild_from = args.rebuild_from
    if rebuild_from:
        stage_names = ("sources", "collapse", "working")
        first = stage_names.index(rebuild_from)
        stage_dirs = {
            "sources": sources_dir,
            "collapse": collapse_dir,
            "working": working_dir,
        }
        for stage_name in reversed(stage_names[first:]):
            archived = archive_path(stage_dirs[stage_name], run_dir)
            if archived:
                print(f"[recovery] preserved {stage_name} at {archived}")

    sources_valid, sources, sources_reason = cached_artifacts(
        report_path=sources_dir / "stage-report.json",
        stage_dir=sources_dir,
        sha256_file=sha256,
    )
    collapse_valid, collapse_report, collapse_reason = cached_output(
        report_path=collapse_dir / "stage-report.json",
        output_path=collapsed,
        sha256_file=sha256,
    )
    working_valid, working, working_reason = cached_output(
        report_path=working_dir / "stage-report.json",
        output_path=working_image,
        sha256_file=sha256,
    )

    if working_valid and not rebuild_from:
        print(f"[cache] 03-working: {working_reason}")
        print(f"\nMakou-safe Highwind image: {working_image}")
        return

    if not collapse_valid:
        print(f"[cache] 02-collapse: {collapse_reason}")
        if not sources_valid:
            if sources_dir.exists():
                raise SystemExit(
                    f"Cannot safely reuse 01-sources: {sources_reason}\n"
                    "Run again with --rebuild-from sources. Existing artifacts "
                    "will be preserved under recovery/."
                )
            sources = build_highwind_source_artifacts(csr, sources_dir)
        else:
            print(f"[cache] 01-sources: {sources_reason}")
        archive_path(collapse_dir, run_dir)
        archive_path(working_dir, run_dir)
        collapsed, collapse_report = collapse_highwind_disc1(
            sources_dir,
            collapse_dir,
        )
    else:
        print(f"[cache] 02-collapse: {collapse_reason}")
        if sources is None:
            sources = load_report(sources_dir / "stage-report.json") or {}

    if working_dir.exists():
        archived = archive_path(working_dir, run_dir)
        print(f"[recovery] preserved changed 03-working at {archived}")

    working = stabilize_working_image(
        input_image=collapsed,
        table_baseline=collapsed,
        edc_reference=pristine(csr, 1),
        output_image=working_image,
        report_path=run_dir / "03-working" / "stage-report.json",
    )

    report = {
        "runDir": str(run_dir),
        "sources": sources or {},
        "collapse": collapse_report or {},
        "working": working,
        "next": (
            "Edit 03-working/HIGHWIND_D1.bin in Makou, save to a new file, "
            "then run this script's finalize command."
        ),
    }
    prepare_report = run_dir / "prepare-report.json"
    archive_path(prepare_report, run_dir)
    write_json(prepare_report, report)
    print(f"\nMakou-safe Highwind image: {working_image}")
    print("Keep this checkpoint unchanged and save Makou's result to a new file.")


def finalize(args: argparse.Namespace) -> None:
    """Turn a separate Makou save into validated release and test artifacts."""
    csr = ROOT
    configure_sources(csr)
    run_dir = args.run_dir.expanduser().resolve()
    edited = args.edited_image.expanduser().resolve()
    if not run_dir.is_dir():
        raise SystemExit(f"Missing run directory: {run_dir}")
    if not edited.is_file():
        raise SystemExit(f"Missing Makou-saved image: {edited}")
    finalize_dir = run_dir / "04-finalize"
    if finalize_dir.exists():
        raise SystemExit(f"Finalize output already exists: {finalize_dir}")

    working_baseline = run_dir / "03-working" / "HIGHWIND_D1.bin"
    baseline_valid, _baseline_report, baseline_reason = cached_output(
        report_path=run_dir / "03-working" / "stage-report.json",
        output_path=working_baseline,
        sha256_file=sha256,
    )
    if not baseline_valid:
        raise SystemExit(
            f"03-working is not the unchanged Makou baseline: {baseline_reason}\n"
            "Run prepare again with the same --run-name and --resume. The edited "
            "directory will be preserved under recovery/ before the baseline is rebuilt."
        )
    stabilized = finalize_dir / "01-stabilized.bin"
    stabilize_report = stabilize_working_image(
        input_image=edited,
        table_baseline=working_baseline,
        edc_reference=pristine(csr, 1),
        output_image=stabilized,
        report_path=finalize_dir / "01-stage-report.json",
    )

    # SNOVA appends a new directory and changes BATTLE.X. Keeping it after
    # Makou prevents the editor from repacking this custom end-of-disc layout.
    snova = finalize_dir / "02-snova.bin"
    snova_report = inject_snova_image(
        input_image=stabilized,
        disc3=pristine(csr, 3),
        output_image=snova,
        report_path=finalize_dir / "02-stage-report.json",
    )

    # Must precede the layer diff: the ending's Disc 3 sectors have to be in
    # the published layer, or builder-built discs cannot play their own ending.
    publish_input = snova
    ending_report = None
    if args.ending_alias:
        endings = finalize_dir / "03-endings.bin"
        ending_report = inject_ending_alias_image(
            input_image=snova,
            disc3=pristine(csr, 3),
            edc_reference=pristine(csr, 1),
            output_image=endings,
            report_path=finalize_dir / "03-stage-report.json",
        )
        publish_input = endings

    release_report = build_release_artifacts(
        input_image=publish_input,
        layer_base=pristine(csr, 1),
        edc_reference=pristine(csr, 1),
        output_dir=run_dir / "05-release-candidate",
        pack_id="highwind",
        name="Highwind",
        version=args.version,
        kind="base",
        compatible_bases=[],
        disc=1,
        blurb=(
            "Heavily shortened story, collapsed onto Disc 1. "
            "Many dialogue choices and scenes are cut."
        ),
        allowed_overlaps=ENDING_ALIAS_OVERLAPS if args.ending_alias else frozenset(),
    )

    # Straight copy of the publish source, so the burned disc and the
    # builder-site reconstruction are byte-identical.
    release_image = Path(release_report["releaseImage"])
    console_dir = run_dir / "06-console-check"
    console_image = console_dir / "FINALFANTASY7_D1_HIGHWIND.bin"
    copy_new(release_image, console_image)
    retail = pristine(csr, 1).read_bytes()
    write_new(console_image.with_suffix(".cue"), cue_for(console_image))

    console_bytes = console_image.read_bytes()
    report = {
        "editedInput": str(edited),
        "stabilize": stabilize_report,
        "snova": snova_report,
        "endingAlias": ending_report,
        "endingAliasInPublishedLayer": bool(args.ending_alias),
        "release": release_report,
        "consoleImage": str(console_image),
        "consoleImageSha256": sha256(console_image),
        "consoleEdcEccSectorsVerified": verify_changed_edc_ecc(console_bytes, retail),
        "consoleDiscBounds": verify_disc_bounds(console_bytes),
        "consoleIsoLayout": verify_iso_layout(
            console_bytes, ENDING_ALIAS_OVERLAPS if args.ending_alias else frozenset()
        ),
        "hardwareValidation": "pending DuckStation, MiSTer, burn verify, and console playtest",
    }
    write_json(run_dir / "finalize-report.json", report)
    print(f"\nCandidate pack: {release_report['pack']}")
    print(f"Builder reconstruction: {release_report['builderRebuildImage']}")
    print(f"Console test image: {console_image}")


def parser() -> argparse.ArgumentParser:
    """Define the stable Highwind prepare/finalize command contract."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(dest="command", required=True)

    prepare_command = commands.add_parser(
        "prepare",
        help="Create a Makou-safe Highwind working BIN",
    )
    prepare_command.add_argument("--run-name")
    prepare_mode = prepare_command.add_mutually_exclusive_group()
    prepare_mode.add_argument(
        "--resume",
        action="store_true",
        help="Reuse hash-verified stages and rebuild only the first changed output",
    )
    prepare_mode.add_argument(
        "--rebuild-from",
        choices=("sources", "collapse", "working"),
        help="Preserve then rebuild this stage and every later prepare stage",
    )
    prepare_command.set_defaults(action=prepare)

    finalize_command = commands.add_parser(
        "finalize",
        help="Process a Makou save into release artifacts",
    )
    finalize_command.add_argument("--run-dir", type=Path, required=True)
    finalize_command.add_argument("--edited-image", type=Path, required=True)
    finalize_command.add_argument("--version", required=True)
    # On by default so the published layer always carries the ending sectors.
    finalize_command.add_argument(
        "--no-ending-alias",
        dest="ending_alias",
        action="store_false",
        help="Skip the ENDING2E Disc 3 alias (publishes a disc with no ending movie)",
    )
    finalize_command.set_defaults(action=finalize)
    return parser


def main() -> None:
    args = parser().parse_args()
    args.action(args)


if __name__ == "__main__":
    main()
