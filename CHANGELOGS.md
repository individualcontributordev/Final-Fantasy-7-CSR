# Changelogs (CSR repo)

Where release notes live. **Builder pack id** is what the disc builder / CDN use.

## Layout

| Product | Kind | Changelog | Live builder ids (see `builder/manifest.json`) |
|---------|------|-----------|-----------------------------------------------|
| **CSR** | base | [bases/csr/CHANGELOG.md](bases/csr/CHANGELOG.md) | `csr-v0.14.1` |
| **Highwind** | base | [bases/highwind/CHANGELOG.md](bases/highwind/CHANGELOG.md) | `highwind-v0.1.1` |
| **CSR+ scenes** | add-ons (+ preset) | [addons/csr-plus/CHANGELOG.md](addons/csr-plus/CHANGELOG.md) | `csr-plus-scene-*`, preset `csr-plus` |

```text
bases/<name>/CHANGELOG.md     one file per published base (csr, highwind)
addons/<family>/CHANGELOG.md  one file per add-on family (csr-plus scenes today)
builder/<pack-id>/            layers + pack.json (no long prose here)
```

## What goes where

| Change | File | Versioning |
|--------|------|------------|
| CSR field/engine trims on the CSR base | `bases/csr/CHANGELOG.md` | bump when you ship `csr-vX.Y.Z` |
| Highwind base trims | `bases/highwind/CHANGELOG.md` | bump when you ship `highwind-vX.Y.Z` |
| New/updated CSR+ scene pack | `addons/csr-plus/CHANGELOG.md` | note pack id (`…-v0.1.1`); family section date or pack version |
| Name/blurb-only manifest tweak | optional one-liner in the matching log | no pack bump required |

Do **not** put scene notes only in `bases/` — CSR+ is not a base anymore.

## Entry format (keep short)

```markdown
## vX.Y.Z (YYYY-MM-DD)

- One line per player-visible change. Prefer pack id for add-ons.
- Disc 1 / 2 / 3 only when it helps (multi-disc packs).
```

Oldest history stays at the **bottom**. Newest release at the **top**.

## Who updates the file

| Workflow | Skill | Changelog |
|----------|-------|-----------|
| Ship CSR or Highwind base | `release-csr-base` | `bases/csr` or `bases/highwind` |
| Ship CSR+ scene (new or update) | `ship-csr-plus-scene` | `addons/csr-plus` |
| Other Makou add-on | `ship-makou-addon` | `addons/<family>/` if you add a family log; else skip |

Commit changelog in the **same** push as `builder/` for that release.
