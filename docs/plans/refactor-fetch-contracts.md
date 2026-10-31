# Plan — review judgement calls in the fetch routes and the reproducibility checker

Ticket #38 (follow-up to the two-axis review of #29 and #32). This is a
**behaviour-preserving refactor**: the contract is `references/manifest.json`, byte for byte.

## The contract before anything moves

Held fixed throughout; every step below is checked against it.

- `python3 scripts/fm4sd_fetch.py --index` leaves `git diff references/manifest.json` empty.
- `python3 scripts/check_reproducibility.py` is 3/3 before and after.
- `--index` run twice is byte-identical (idempotent).
- Counts unchanged: 383 entries, 323 with an arXiv id, 340 fetched.

`--index` on this tree reads `README.md` and the prior `references/manifest.json` and writes
the same manifest back. That is what makes "byte-identical" testable without payload
(`papers/` is absent here and gitignored).

## What changes, and why

### `scripts/fm4sd_fetch.py`

1. **One cached-entry helper.** `fetch_arxiv` and `fetch_route` each carry their own copy of
   the `.fetched` marker short-circuit, and they have already drifted: one recovers the
   pinned revision, the other does not. Add `Marker` + `read_marker()` (kind, sha256, rev —
   the same three lines `marker_text()` writes since #33) and `cached_entry(paper, force)`,
   used by both paths. `reconcile()` reads the same helper, so the marker shape is parsed in
   exactly one place.
   *Equivalence note:* an old marker with no digest line now leaves the manifest's digest
   alone in both paths (`fetch_arxiv` already did; `fetch_route` blanked it). No route marker
   can lack a digest — `marker_text()` has always written it — so output is unchanged.

2. **One name for the minimum-text threshold.** `MIN_TEXT_BYTES = 4000`, replacing
   `n_bytes > 4000` (LaTeX source) and `n_bytes < 4000` (HTML/XML route).

3. **One absence classifier.** `absence_status()` and `fetch_route`'s no-route branch are the
   same cascade in two orders. `fetch_route` now calls `absence_status()` (which returns
   `pending` only when a route exists — impossible in that branch). `recorded_absence(slug)`
   names the static tables once, and `cmd_index`'s "uncovered row" warning uses it instead of
   re-testing the two tables.

4. **One `RouteSpec` per slug.** `NON_PAPER`, `UNREACHABLE`, `HTML_PAPERS`, `PUBLISHER_PDFS`
   and `LICENCE_RECORDS` are five slug-keyed tables describing one entry each. Replace them
   with `ROUTES: dict[str, RouteSpec]`, where a spec holds the note, the absence reason, the
   HTML link key, the publisher flag, and the licence record. `PUBLISHER_PDFS` disappears as a
   set — `publisher` is a fact on the entry. Manifest JSON is untouched: the licence record is
   emitted with the same three keys in the same order.

5. **One documented licence-URL mapping.** 253 arXiv rows carry `licence_url` (written by
   `fm4sd_licences.py`), 18 route rows carry `licence_source`. They name the same fact. A
   rename is **not** available: it would change the committed manifest, which the ticket
   forbids ("no field renames smuggled in"). So the mapping is stated once, as
   `LICENCE_URL_FIELDS`, and the checker imports it rather than repeating the field names.
   `PROVENANCE.md` gets the sentence, since it is the enforcement doc.

6. **`corpus_figures(entries)`** — one definition of the published figures, next to the
   manifest vocabulary in the fetcher. `fm4sd_search.py stats` prints from it and the gate
   compares prose against it, so `fetched`, `tex`, `pdf`, `code` are defined once.
   `FETCHED_STATUSES = ("ok", "cached")` names the "payload is on disk" pair.

### `scripts/check_reproducibility.py`

7. **Import the fetcher's contracts.** `MANIFEST_DELIM` replaced the local `DELIM` (the delimiter now lives in `scripts/manifest.py`, #63);
   `corpus_figures()` replaces `manifest_figures()`; `LICENCE_URL_FIELDS` replaces the
   hardcoded field name. `make_scratch()` asserts every path in `INDEX_INPUTS` (declared by
   the fetcher: `README.md`, `references/manifest.json`) is present in the scratch tree, so a
   new `--index` input is a loud failure rather than a quietly incomplete copy.

8. **Claims bind by group name.** Each `Claim` pattern names its capture groups after the
   figures they carry, and the comparison reads `m.group(name)`. Also drops the
   int/float-guess from prose: everything is compared as a float, with the MB tolerance kept.

## Deliberately not changed

- **`preserve_fetch()` split** — the reason given for splitting was that it would make #33's
  pinning change land once; #33 has landed, so the benefit is gone and splitting now is a
  rename with no behavioural gain.
- **`-v` / `FM4SD_CHECK_KEEP`** — both have consumers in this revision (`verbose` gates the
  per-field and per-figure prints; `keep_scratch()` reads the env var), so the review's "no
  consumer" no longer holds.
- **Manifest schema** — no field added, renamed or reordered. Schema work is #33's.

## Verification

```bash
python3 scripts/check_reproducibility.py          # 3/3
python3 scripts/fm4sd_fetch.py --index            # then: git diff references/manifest.json  (empty)
python3 scripts/fm4sd_fetch.py --index            # twice: byte-identical
python3 scripts/fm4sd_search.py stats             # 383 / 323 / 340 unchanged
```
