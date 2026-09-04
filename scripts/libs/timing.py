"""Wall-clock stage timings printed to stdout.

Commands print ``time <stage>: 1.23s`` so a slow publish shows which step
dominated without a profiler. Times are process wall clock, not CPU.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager


def _fmt(seconds: float) -> str:
    return f"{seconds:.2f}s"


@contextmanager
def stage(name: str) -> Iterator[None]:
    started = time.perf_counter()
    yield
    print(f"time {name}: {_fmt(time.perf_counter() - started)}")


class Timer:
    """One instance per command; call ``total()`` before exit."""

    def __init__(self) -> None:
        self._t0 = time.perf_counter()

    def stage(self, name: str):
        return stage(name)

    def total(self) -> None:
        print(f"time total: {_fmt(time.perf_counter() - self._t0)}")
