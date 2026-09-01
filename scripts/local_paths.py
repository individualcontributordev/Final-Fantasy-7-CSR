"""Resolve and, when requested, cache repository-local base images.

Pristine BINs and builder layer JSON are inputs. ``ensure_cached_base`` either
returns a verified path hit or reconstructs bytes into
``cache/<flavor>/FINALFANTASY7_DN.bin``. Cache hits are existence-based here,
not hash-based; staged CSR+/Highwind workflows use ``pipeline_cache`` when
mutation detection is required. No path may resolve to another repository,
and this module performs no network or source-control operations.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
	sys.path.insert(0, str(_SCRIPTS))

PRISTINE_DIR = _ROOT / "pristine"
CACHE_DIR = _ROOT / "cache"

_BASE_FLAVOR = (
	("highwind", "highwind"),
	("csr-plus", "csr-plus"),
	("csr-v", "csr"),
	("csr", "csr"),
)


def repo_root() -> Path:
	return _ROOT


def pristine_dir() -> Path:
	return PRISTINE_DIR


def cache_dir() -> Path:
	return CACHE_DIR


def flavor_for_base_id(base_id: str) -> str | None:
	"""Map a builder base id to its local cache directory name."""
	bid = (base_id or "").strip().lower()
	if bid in ("clean", "unmodified", ""):
		return None
	for prefix, flavor in _BASE_FLAVOR:
		if bid.startswith(prefix) or (prefix == "highwind" and "highwind" in bid):
			return flavor
	return None


def pristine_bin(disc: int) -> Path:
	name = f"FINALFANTASY7_D{disc}.bin"
	return PRISTINE_DIR / name


def cache_bin_path(flavor: str, disc: int) -> Path:
	return CACHE_DIR / flavor / f"FINALFANTASY7_D{disc}.bin"


def cache_bin(flavor: str, disc: int) -> Path | None:
	path = cache_bin_path(flavor, disc)
	return path if path.is_file() else None


def default_pristine_arg(disc: int = 1) -> Path:
	return pristine_bin(disc)


def ensure_cached_base(
	*,
	base_id: str,
	disc: int,
	layer_path: Path,
	pristine: Path | None = None,
	write_cache: bool = True,
) -> tuple[bytes, Path | None]:
	"""Return base bytes and the cache path used or created.

	``clean``/``unmodified`` reads pristine directly. Other ids must map to a
	known flavor and are reconstructed from the supplied layer on cache miss.
	The caller remains responsible for semantic and EDC/ECC validation.
	"""
	from apply_layer import apply_layer

	if base_id in ("clean", "unmodified"):
		p = pristine or pristine_bin(disc)
		if not p.is_file():
			raise SystemExit(f"Missing pristine: {p}")
		return p.read_bytes(), p

	flavor = flavor_for_base_id(base_id)
	if not flavor:
		raise SystemExit(f"No cache flavor for base id {base_id!r}")

	hit = cache_bin(flavor, disc)
	if hit is not None:
		print(f"  cache hit: {hit}")
		return hit.read_bytes(), hit

	pr = pristine or pristine_bin(disc)
	if not pr.is_file():
		raise SystemExit(f"Missing pristine (needed to build cache/{flavor}): {pr}")
	if not layer_path.is_file():
		raise SystemExit(f"Missing base layer: {layer_path}")

	print(f"  cache miss — apply {layer_path.name} onto pristine → cache/{flavor}/D{disc}")
	img = bytearray(pr.read_bytes())
	layer = json.loads(layer_path.read_text(encoding="utf-8"))
	apply_layer(img, layer)
	data = bytes(img)

	out_path = None
	if write_cache:
		out_path = cache_bin_path(flavor, disc)
		out_path.parent.mkdir(parents=True, exist_ok=True)
		out_path.write_bytes(data)
		print(f"  wrote {out_path} ({len(data)} bytes)")
	return data, out_path
