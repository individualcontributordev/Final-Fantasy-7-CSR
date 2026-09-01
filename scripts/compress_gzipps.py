#!/usr/bin/env python3
"""Recompress a patched FF7 GZIPPS overlay such as FIELD.BIN or BATTLE.X.

Inputs are an edited decompressed payload and the original wrapped overlay.
The output preserves the eight-byte GZIPPS envelope, rebuilds a valid gzip
member, and tries several standard-library DEFLATE settings to fit the
original byte budget. Every candidate is decompressed and compared before it
can be selected.

The command writes ``ORIGINAL.bin.new`` unless an output path is supplied. It
never truncates an oversize stream: growth is reported so the caller can
relocate it or reject the build. A shorter stream may be zero-padded by the
ISO insertion layer. The four-byte decompressed-size field is updated, while
the original GZIPPS subheader is retained.
"""

from __future__ import annotations

import binascii
import gzip
import struct
import sys
import zlib
from pathlib import Path

GZIPPS_HEADER_SIZE = 8


def _gzip_wrap(raw_deflate: bytes, uncompressed: bytes, header10: bytes) -> bytes:
    """Build a gzip member from raw DEFLATE + a 10-byte gzip header template."""
    if len(header10) < 10:
        header10 = b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff"
    # Force: method=deflate, no extra flags/fname; keep XFL/OS from template when possible
    header = (
        b"\x1f\x8b\x08\x00"  # magic, method, flags=0
        + b"\x00\x00\x00\x00"  # mtime
        + bytes([header10[8], header10[9]])  # xfl, os
    )
    crc = binascii.crc32(uncompressed) & 0xFFFFFFFF
    trailer = struct.pack("<II", crc, len(uncompressed) & 0xFFFFFFFF)
    return header + raw_deflate + trailer


def _deflate_candidates(uncompressed: bytes) -> list[tuple[str, bytes]]:
    """Generate deterministic stdlib DEFLATE/gzip alternatives for fitting."""
    out: list[tuple[str, bytes]] = []
    strategies = (
        ("default", zlib.Z_DEFAULT_STRATEGY),
        ("filtered", zlib.Z_FILTERED),
        ("huffman", zlib.Z_HUFFMAN_ONLY),
        ("rle", getattr(zlib, "Z_RLE", zlib.Z_DEFAULT_STRATEGY)),
        ("fixed", getattr(zlib, "Z_FIXED", zlib.Z_DEFAULT_STRATEGY)),
    )
    for level in range(10):
        for name, strategy in strategies:
            try:
                co = zlib.compressobj(
                    level,
                    zlib.DEFLATED,
                    -zlib.MAX_WBITS,
                    zlib.DEF_MEM_LEVEL,
                    strategy,
                )
                raw = co.compress(uncompressed) + co.flush()
            except zlib.error:
                continue
            out.append((f"zlib-{level}-{name}", raw))

        # stdlib gzip (full member) as another candidate source of deflate
        full = gzip.compress(uncompressed, compresslevel=level, mtime=0)
        out.append((f"gzip-{level}", full))

    return out


def _payload_from_candidate(
    label: str, blob: bytes, uncompressed: bytes, header10: bytes
) -> bytes:
    """Normalize either raw DEFLATE or gzip output to a complete gzip member."""
    if label.startswith("gzip-"):
        return blob  # already a full gzip member
    return _gzip_wrap(blob, uncompressed, header10)


def _best_gzip_payload(
    uncompressed: bytes,
    prefer_max_len: int,
    header10: bytes,
) -> tuple[bytes, str]:
    """Choose the smallest verified candidate, preferring the slot budget."""
    best_fit: tuple[int, str, bytes] | None = None
    best_any: tuple[int, str, bytes] | None = None

    for label, blob in _deflate_candidates(uncompressed):
        payload = _payload_from_candidate(label, blob, uncompressed, header10)
        # Sanity: must decompress to the same bytes
        try:
            if gzip.decompress(payload) != uncompressed:
                continue
        except (OSError, zlib.error):
            continue

        size = len(payload)
        if best_any is None or size < best_any[0]:
            best_any = (size, label, payload)
        if size <= prefer_max_len and (best_fit is None or size < best_fit[0]):
            best_fit = (size, label, payload)

    chosen = best_fit or best_any
    if chosen is None:
        raise RuntimeError("no valid gzip candidate produced")
    return chosen[2], chosen[1]


def _original_gzip_header10(original_payload: bytes) -> bytes:
    """Return a usable gzip header template without trusting optional fields."""
    if len(original_payload) >= 10 and original_payload[:2] == b"\x1f\x8b":
        return original_payload[:10]
    return b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff"


def compress_gzipps(
    src_dec: Path,
    original_bin: Path,
    dst: Path | None = None,
) -> Path:
    """Write the smallest verified GZIPPS candidate and return its path."""
    original = original_bin.read_bytes()
    if len(original) < GZIPPS_HEADER_SIZE:
        raise ValueError(f"{original_bin}: invalid GZIPPS source")

    dec_size = struct.unpack("<I", original[0:4])[0]
    gzip_subheader = original[4:8]
    original_payload = original[GZIPPS_HEADER_SIZE:]
    prefer_payload_max = len(original) - GZIPPS_HEADER_SIZE
    header10 = _original_gzip_header10(original_payload)

    uncompressed = src_dec.read_bytes()
    if len(uncompressed) != dec_size:
        print(
            f"Warning: patched size {len(uncompressed)} != original dec size {dec_size}",
            file=sys.stderr,
        )

    compressed_payload, method = _best_gzip_payload(
        uncompressed, prefer_payload_max, header10
    )
    out = struct.pack("<I", len(uncompressed)) + gzip_subheader + compressed_payload

    if dst is None:
        dst = original_bin.with_name(original_bin.name + ".new")

    size_delta = len(out) - len(original)

    # If still slightly over, keep best payload but pad/truncate message — never
    # silently truncate. Optional: if overage is tiny and trailing zeros on `out`
    # aren't valid, just report.
    if size_delta > 0:
        print(
            f"Best method {method} still {size_delta:+d} vs original "
            f"({len(out)} > {len(original)}).",
            file=sys.stderr,
        )

    dst.write_bytes(out)

    print(f"Source (dec):     {src_dec} ({len(uncompressed)} bytes)")
    print(f"Original (bin):   {original_bin} ({len(original)} bytes)")
    print(f"Output:           {dst} ({len(out)} bytes)")
    print(f"Method:           {method}")
    print(f"Size delta:       {size_delta:+d} bytes")
    if size_delta > 0:
        print(
            "WARNING: larger than original — do NOT accept CDmage truncate.\n"
            "Use a tool that can relocate or grow the overlay. Do not truncate it.",
            file=sys.stderr,
        )
    elif size_delta < 0:
        print("Shorter than original — CDmage 'pad with zeros?' → Yes.")

    return dst


# Public alias retained for callers that name the concrete FIELD.BIN use case.
compress_field_bin = compress_gzipps


def main() -> None:
    if len(sys.argv) < 3:
        print(
            f"Usage: {sys.argv[0]} <overlay.dec.patched> <original GZIPPS.bin> [output]",
            file=sys.stderr,
        )
        sys.exit(1)

    src_dec = Path(sys.argv[1]).expanduser().resolve()
    original = Path(sys.argv[2]).expanduser().resolve()
    dst = Path(sys.argv[3]).expanduser().resolve() if len(sys.argv) > 3 else None

    for p in (src_dec, original):
        if not p.is_file():
            print(f"Error: not found: {p}", file=sys.stderr)
            sys.exit(1)

    compress_gzipps(src_dec, original, dst)


if __name__ == "__main__":
    main()
