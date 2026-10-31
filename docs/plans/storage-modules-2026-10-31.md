# Plan — one manifest format, one payload probe (2026-10-31)

Issue #63, architecture review candidates #1 and #3. Evidence: four readers of
`references/manifest.json` with three delimiter literals, and two answers to "what is in
`papers/<slug>/`" — the fetch path trusted a marker, `--index` demanded marker *and* text.

## What

- `scripts/manifest.py`: `read()` → (header, entries, raw), `write()` preserving the existing
  header byte for byte, `render()`, `build_header()`, `by_slug()`, typed `ManifestError`.
- `scripts/payload.py`: one probe of the payload directory; `payload.ready` (non-empty marker
  plus readable text) is the single rule.
- Five callers rewired: fetch, gate, publisher, search, licences. The gate's scratch copy
  carries the modules via `INDEX_INPUTS`, which now names code as well as data.

## Behaviour deltas, named

- **A marker with no text is not ready.** The fetch path used to credit it; `--index` did not.
  It now refetches on both. A marker alone cannot serve text to search or publish.
- **An empty or truncated marker is not credited.** It used to count (any file did); unknown
  provenance is now refetched.
- **`reconcile` no longer writes `pages = 0`.** That line clobbered a count `carry_forward` had
  just restored. Page counts come from `preserve_fetch()`; the docstring now says so.
- **Publisher and search use `payload.ready`** rather than `text.txt` alone, so all four
  consumers of "is there payload" agree.
- **`by_slug` ignores rows without a slug individually**, where one bad row used to discard the
  whole prior map. Wider acceptance, in a field-preservation path.
- **`load_prior` no longer catches `OSError`**: `manifest.read` translates it at the seam.

## Verification

`--index` byte-identical to `main` and idempotent; gate 3/3; `read → write → read` unchanged;
marker-only vs marker+text exercised in a scratch directory; one `DELIM` definition; every
script imports and its CLI smoke-runs.

## Out of scope

The status vocabulary (#2), the arXiv id vocabulary (#4), the network and gate seams (#5, #6).
