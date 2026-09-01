"""Materialize pristine or current CSR disc images for collapse helpers.

Inputs are the three read-only ``pristine/FINALFANTASY7_DN.bin`` files and
``builder/csr/layers/discN.layer.json``. ``load_csr_image`` returns an
in-memory image; this module writes no files and does not repair or validate
the layer result. Disc numbers are restricted to 1..3, and field names are
normalized before being turned into ISO paths.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def pristine_dir() -> Path:
    return ROOT / "pristine"


def csr_root() -> Path:
    return ROOT


def pristine_bin(disc: int) -> Path:
    if disc not in (1, 2, 3):
        raise ValueError(f"disc must be 1..3, got {disc}")
    return pristine_dir() / f"FINALFANTASY7_D{disc}.bin"


def csr_layer(disc: int) -> Path:
    if disc not in (1, 2, 3):
        raise ValueError(f"disc must be 1..3, got {disc}")
    return (
        csr_root()
        / "builder/csr/layers"
        / f"disc{disc}.layer.json"
    )


def load_pristine_image(disc: int) -> bytearray:
    """Read pristine disc ``disc`` as a mutable in-memory image."""
    path = pristine_bin(disc)
    if not path.is_file():
        raise FileNotFoundError(f"missing pristine disc image: {path}")
    return bytearray(path.read_bytes())


def load_csr_image(disc: int) -> bytearray:
    """Apply the current local CSR layer to pristine disc N."""
    from apply_layer import apply_layer  # local import: scripts/ on path

    img = load_pristine_image(disc)
    layer_path = csr_layer(disc)
    if not layer_path.is_file():
        raise FileNotFoundError(f"missing CSR layer: {layer_path}")
    apply_layer(img, json.loads(layer_path.read_text(encoding="utf-8")))
    return img


def normalize_field_name(name: str) -> str:
    """DEL1 or DEL1.DAT → DEL1."""
    n = name.strip().upper()
    if n.endswith(".DAT"):
        n = n[: -len(".DAT")]
    if not n or "/" in n or "\\" in n:
        raise ValueError(f"bad field map name: {name!r}")
    return n


def field_iso_path(name: str) -> str:
    """Return the canonical ISO9660 path for one normalized field name."""
    return f"FIELD/{normalize_field_name(name)}.DAT"
