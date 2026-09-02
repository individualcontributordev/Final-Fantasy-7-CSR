"""Read, apply, and build ``ic-layer-v1`` disc-image patches.

A layer is a list of ``{offset, hex}`` writes with no expected-before bytes.
Apply order is the record list order. Callers must repair MODE2 Form 1 footers
after editing a BIN and before publishing a new layer.
"""

from __future__ import annotations

from pathlib import Path

CHUNK = 1024 * 1024
MAX_RECORD_BYTES = 4096
SECTOR = 2352


def apply_layer(image: bytearray, layer: dict) -> None:
    """Apply validated layer records to ``image`` in listed order."""
    if layer.get("format") != "ic-layer-v1":
        raise SystemExit("expected format ic-layer-v1")
    if layer.get("target") not in (None, "disc-image"):
        raise SystemExit(f"unsupported target: {layer.get('target')}")

    baseline_len = len(image)
    for record in layer["records"]:
        offset = int(record["offset"])
        data = bytes.fromhex(record["hex"])
        end = offset + len(data)
        if end > len(image):
            image.extend(b"\x00" * (end - len(image)))
        image[offset:end] = data

    stats = layer.get("stats") or {}
    original = stats.get("originalBytes")
    target = stats.get("modifiedBytes")
    growth_matches_baseline = isinstance(original, int) and original == baseline_len
    target_extends_image = isinstance(target, int) and target > len(image)
    if growth_matches_baseline and target_extends_image:
        image.extend(b"\x00" * (target - len(image)))

    if len(image) > baseline_len and len(image) % SECTOR:
        image.extend(b"\x00" * (SECTOR - (len(image) % SECTOR)))


def _iter_changed_runs(original: Path, modified: Path):
    """Yield bounded runs of bytes that differ between two images."""
    with original.open("rb") as original_stream, modified.open("rb") as modified_stream:
        offset = 0
        run_offset: int | None = None
        run = bytearray()

        def flush():
            nonlocal run_offset, run
            if run_offset is None or not run:
                run_offset = None
                run = bytearray()
                return
            position = 0
            while position < len(run):
                piece = bytes(run[position : position + MAX_RECORD_BYTES])
                yield run_offset + position, piece
                position += len(piece)
            run_offset = None
            run = bytearray()

        while True:
            original_chunk = original_stream.read(CHUNK)
            modified_chunk = modified_stream.read(CHUNK)
            if not original_chunk and not modified_chunk:
                break

            chunk_size = max(len(original_chunk), len(modified_chunk))
            original_chunk = original_chunk.ljust(chunk_size, b"\x00")
            modified_chunk = modified_chunk.ljust(chunk_size, b"\x00")

            for index, (before, after) in enumerate(zip(original_chunk, modified_chunk)):
                if before != after:
                    if run_offset is None:
                        run_offset = offset + index
                    run.append(after)
                elif run_offset is not None:
                    yield from flush()
            offset += chunk_size

        yield from flush()


def build_layer(
    original: Path,
    modified: Path,
    *,
    layer_id: str,
    description: str,
) -> dict:
    """Return a byte-exact layer document for ``original`` to ``modified``."""
    records = []
    changed_bytes = 0
    for offset, data in _iter_changed_runs(original, modified):
        records.append({"offset": offset, "hex": data.hex()})
        changed_bytes += len(data)

    return {
        "format": "ic-layer-v1",
        "id": layer_id,
        "description": description,
        "target": "disc-image",
        "stats": {
            "originalBytes": original.stat().st_size,
            "modifiedBytes": modified.stat().st_size,
            "changedBytes": changed_bytes,
            "records": len(records),
        },
        "records": records,
    }
