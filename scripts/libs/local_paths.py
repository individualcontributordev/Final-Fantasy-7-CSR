"""Resolve pristine and cached base images within this repository."""

from __future__ import annotations

import json
from pathlib import Path

from .layer import apply_layer

ROOT = Path(__file__).resolve().parents[2]
PRISTINE_DIR = ROOT / "pristine"
CACHE_DIR = ROOT / "cache"

BASE_FLAVORS = {
    "csr": "csr",
    "csr-plus": "csr-plus",
    "highwind": "highwind",
}


def pristine_bin(disc: int) -> Path:
    return PRISTINE_DIR / f"FINALFANTASY7_D{disc}.bin"


def default_pristine_arg(disc: int = 1) -> Path:
    return pristine_bin(disc)


def cache_bin_path(flavor: str, disc: int) -> Path:
    return CACHE_DIR / flavor / f"FINALFANTASY7_D{disc}.bin"


def ensure_cached_base(
    *,
    base_id: str,
    disc: int,
    layer_path: Path,
    pristine: Path | None = None,
    write_cache: bool = True,
) -> tuple[bytes, Path | None]:
    """Return a cached base image or reconstruct it from pristine."""
    if base_id in ("clean", "unmodified"):
        pristine_path = pristine or pristine_bin(disc)
        if not pristine_path.is_file():
            raise SystemExit(f"Missing pristine: {pristine_path}")
        return pristine_path.read_bytes(), pristine_path

    flavor = BASE_FLAVORS.get(base_id)
    if flavor is None:
        raise SystemExit(f"No cache flavor for base id {base_id!r}")

    cached = cache_bin_path(flavor, disc)
    if write_cache and cached.is_file():
        print(f"  cache hit: {cached}")
        return cached.read_bytes(), cached

    pristine_path = pristine or pristine_bin(disc)
    if not pristine_path.is_file():
        raise SystemExit(f"Missing pristine: {pristine_path}")
    if not layer_path.is_file():
        raise SystemExit(f"Missing base layer: {layer_path}")

    print(f"  cache miss — apply {layer_path.name} onto pristine → cache/{flavor}/D{disc}")
    image = bytearray(pristine_path.read_bytes())
    layer = json.loads(layer_path.read_text(encoding="utf-8"))
    apply_layer(image, layer)
    data = bytes(image)

    if not write_cache:
        return data, None

    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_bytes(data)
    print(f"  wrote {cached} ({len(data)} bytes)")
    return data, cached
