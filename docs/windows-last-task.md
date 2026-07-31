# Task: adopt pristine/ + cache/ layout (one-time)

## Goal

Match the new local-disc mental model. Bins stay gitignored; only path names change.

## Mental model

    pristine/                 retail ground truth (store once)
    builder zip .bin          session working disc (edit in Makou)
    builder/                  published layers (git)
    cache/csr|highwind|…      optional reconstructed bases — not the workflow owner
    workspace/                LEGACY (still works; scripts fall back)

## Success

1. git pull
2. Move or copy retail bins to pristine/
3. Optionally move reconstructed bases to cache/
4. Smoke: python3 -c import local_paths; print pristine_bin(1)
5. Say check (optional note under Evidence)

## Copy-paste (Git Bash)

    cd "$(git rev-parse --show-toplevel)"
    git pull --ff-only

    mkdir -p pristine cache/csr cache/highwind

    # If you still have workspace/pristine (common):
    if [ -d workspace/pristine ]; then
      cp -n workspace/pristine/FINALFANTASY7_D*.bin pristine/ 2>/dev/null || true
      # or: mv workspace/pristine/FINALFANTASY7_D*.bin pristine/
    fi

    # Optional caches:
    if [ -d workspace/csr ]; then
      cp -n workspace/csr/FINALFANTASY7_D*.bin cache/csr/ 2>/dev/null || true
    fi
    if [ -d workspace/highwind ]; then
      cp -n workspace/highwind/FINALFANTASY7_D*.bin cache/highwind/ 2>/dev/null || true
    fi

    python3 -c "import sys; sys.path.insert(0,"scripts"); import local_paths as lp; print(lp.pristine_bin(1), lp.pristine_bin(1).is_file()); print("cache csr", lp.cache_bin("csr", 1))"

# You may delete workspace/ after copies verify. Not required — fallback remains.

## Evidence

    (paths that exist + local_paths printout)
