# Plan — publish licence-verified shareable extracts (2026-10-31)

Ticket #30, whose latest comment widens the shareable set from two entries to three after
#29 landed. Follows the licence policy already recorded in `PROVENANCE.md` → *Corpus scope* →
*Licence and sharing*; this ticket is the publisher that section promised and nothing there
changes.

## What

- **`scripts/fm4sd_publish_shared.py`** (new, stdlib only). Reads
  `references/manifest.json` and writes `corpus-shared/` for entries that are **both**
  `shareable: yes` **and** fetched:
  - `corpus-shared/<slug>/text.txt` — byte-identical copy of `papers/<slug>/text.txt`, the
    text the digests were written from, never re-extracted
  - `corpus-shared/<slug>/LICENSE.txt` — title, entry slug, citation, source URL, `licence`,
    `licence_source`, retrieval date, published-text sha256, and a pointer to the licence text
  - `corpus-shared/README.md` — what is published and why, one line per entry, plus the
    pending and withheld sets
- **`corpus-shared/`** — the generated directory, committed.
- **`PROVENANCE.md`** — a *Published extracts* subsection recording what is published, under
  which licence, how to re-run the publisher, and why a fetcher re-run cannot add a file here.
- **`README.md`** — one pointer to `corpus-shared/` beside the existing "why the corpus is
  gitignored" paragraph, so the published set is discoverable from the index.

## Why a separate entry point

Publication is a licence decision, not a fetch side effect. Keeping it in its own script means
`--fetch` can never widen the redistributed set on its own, which is the ticket's fourth
acceptance criterion. It also keeps `scripts/fm4sd_fetch.py` untouched — #33 owns that file
and the manifest, so this branch does not rebase onto a moving target.

## Decisions

- **Scope is licence ∧ payload**, not licence alone. `tabssldataselect` is `shareable: yes`
  but `skipped:unreachable:captcha` with no payload: it is reported *pending* and the run still
  exits 0, as the brief asks. Nothing here probes the captcha; #9's rule stands. It publishes
  automatically on the first run after a fetch succeeds.
- **No re-check, no invention.** The publisher never re-probes a licence and never writes text
  for an entry without payload. If a fetched entry's `text.txt` disagrees with the manifest's
  `text_bytes`, it refuses that entry and exits non-zero rather than publishing a stale extract.
- **Deterministic and idempotent.** Output depends on the manifest plus the payload bytes, with
  one exception that is deliberately sticky: the retrieval date. It is stamped from the
  payload's mtime on first publish and then read back out of the committed `LICENSE.txt`, so a
  re-run on another clone reproduces the committed bytes instead of re-dating them. Files are
  written only when their bytes differ, so a second run changes nothing.
- **Removal is licence-driven only.** A `<slug>/` directory is removed when the manifest no
  longer says `shareable: yes` (or the entry is gone), which is what makes "`corpus-shared/`
  holds exactly the shareable-and-fetched entries" true after a licence re-check. A *payload*
  that is merely absent from this clone never deletes anything — a payload-less clone must not
  be able to empty the published set.
- **Title source.** The index carries a slug and a citation, not a title, and
  `fm4sd_licences.py` records `arxiv_title` for arXiv entries only. The published set therefore
  carries its titles in a small table in the script, transcribed from each paper's first page
  and checked against its extracted text. A shareable entry with no title still publishes under
  its slug, with a warning.
- **`--check`** compares the planned files against what is on disk and writes nothing, so
  idempotency has a one-command proof. It also flags a `<slug>/` directory the manifest no
  longer justifies and any file under `corpus-shared/` that the plan does not produce.
- **Refuse rather than publish a short set.** A fetched shareable entry with no payload here
  *and* no committed copy stops the run before anything is written: a README that lists a
  directory nobody has is worse than an error. Stray files are reported, never deleted —
  removal stays tied to a licence decision.

## Not doing

- No `.gitignore` exception: only `papers/` is ignored, `corpus-shared/` is tracked by
  default. Verified with `git check-ignore` and stated in the PR, per the brief.
- No PDFs or source bundles published — text plus metadata only.
- No change to `scripts/fm4sd_fetch.py`, `references/manifest.json`, or
  `scripts/check_reproducibility.py`.
- No re-deciding shareability: `wikidbs` stays `unknown` (its CC BY line covers the dataset,
  not the paper), `pfnsyn` stays `no` (CC BY-NC-ND).

## Verification

- `python3 scripts/fm4sd_publish_shared.py` twice; second run reports no changes and
  `git status --short corpus-shared/` is empty.
- `python3 scripts/fm4sd_publish_shared.py --check` exits 0.
- Published `text.txt` files match `papers/<slug>/text.txt` by sha256.
- `git check-ignore -v corpus-shared/README.md` (no match → tracked) and
  `git check-ignore -v papers/tabpfnv2/text.txt` (still ignored).
- `python3 scripts/check_reproducibility.py` → 3/3, unchanged.
