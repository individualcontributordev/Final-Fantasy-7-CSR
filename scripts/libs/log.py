"""Chatter for recut scripts: shown only with FF7_VERBOSE=1; results use plain print."""

import os

VERBOSE = bool(os.environ.get("FF7_VERBOSE"))


def vprint(*args, **kwargs) -> None:
    if VERBOSE:
        print(*args, **kwargs)
