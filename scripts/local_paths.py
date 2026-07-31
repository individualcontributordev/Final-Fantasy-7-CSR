"""Resolve local disc paths: pristine/ (retail) and cache/ (optional rebuilds).

Mental model
------------
  pristine/                 retail ground truth (store once)
  builder zip .bin          session working disc (edit in Makou)
  builder/                  published layers (git)
  cache/csr|highwind|…      optional reconstructed bases — not the workflow owner

Legacy ``workspace/pristine`` and ``workspace/<flavor>`` still resolve if present.
"""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent

PRISTINE_DIR = _ROOT / "pristine"
CACHE_DIR = _ROOT / "cache"
# Legacy (pre rename) — still accepted when reading
_LEGACY_WORKSPACE = _ROOT / "workspace"


def repo_root() -> Path:
	return _ROOT


def pristine_dir() -> Path:
	if PRISTINE_DIR.is_dir():
		return PRISTINE_DIR
	legacy = _LEGACY_WORKSPACE / "pristine"
	if legacy.is_dir():
		return legacy
	return PRISTINE_DIR


def cache_dir() -> Path:
	if CACHE_DIR.is_dir():
		return CACHE_DIR
	if _LEGACY_WORKSPACE.is_dir():
		return _LEGACY_WORKSPACE
	return CACHE_DIR


def pristine_bin(disc: int) -> Path:
	"""Path to retail FINALFANTASY7_DN.bin (may not exist yet)."""
	name = f"FINALFANTASY7_D{disc}.bin"
	primary = pristine_dir() / name
	if primary.is_file():
		return primary
	legacy = _LEGACY_WORKSPACE / "pristine" / name
	if legacy.is_file():
		return legacy
	return primary


def cache_bin(flavor: str, disc: int) -> Path | None:
	"""Optional cached reconstructed image, or None if missing."""
	name = f"FINALFANTASY7_D{disc}.bin"
	for base in (cache_dir(), _LEGACY_WORKSPACE):
		p = base / flavor / name
		if p.is_file():
			return p
	return None


def default_pristine_arg(disc: int = 1) -> Path:
	"""Default --pristine path for argparse (existence not required)."""
	return pristine_bin(disc)
