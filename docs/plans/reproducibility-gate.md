# Plan — reproducibility gate as a command and a required CI check

Decision #16, delivery ticket #32. Evidence: `research/arxiv-mutability.md` on branch
`research/arxiv-mutability`.

## What

1. `scripts/check_reproducibility.py` (stdlib only, no payload, no dependency installs) runs
   the three checks #16 named and exits non-zero with a per-figure message on any failure.
2. `.github/workflows/reproducibility.yml` runs that one command on every `pull_request` and
   every push to `main`: `ubuntu-latest`, Python 3.12 pinned, nothing installed, one upstream
   fetch (inside check 2), no cron.
3. `AGENTS.md` names the gate as automated, gives the local command, and records the
   branch-protection step (admin, once) that makes a red check block a merge.

## Why

`AGENTS.md` has defined verification as reproducibility-by-hand since the research layer
landed, and the 2026-10-29 review found it silently broken three times: a licence wipe, a
four-way count disagreement, and a field that was empty on every entry. A rule that only a
human can run is not a gate. This turns it into a command, and the command into a required
check.

## The three checks

### 1. Manifest equality on README-derived fields

Copy `README.md`, `references/manifest.json` and `scripts/fm4sd_fetch.py` into a scratch
directory and run `--index` there. Compare the regenerated manifest with the committed one
field by field.

**The #33 hazard shapes this check.** On a payload-less tree `reconcile()` recovers nothing,
so `--index` stamps every payload-derived field empty (and #33 is the ticket for the digest
wipe that follows). A naive whole-file comparison would therefore be red on every CI run, for
a bug this ticket does not own. So the comparison is a projection, not a file diff:

- **Compared exactly** (README-derived): `slug`, `arxiv_id`, `section`, `category`,
  `subcategory`, `citation`, `links`, `has_code`, plus the manifest header
  (`source`, `note`, `count`) and entry order.
- **Excluded by construction** (payload-derived): `source`, `path`, `text_bytes`, `pages`,
  `n_tex_files`, `sha256`, `fetch_status`.
- **Excluded by construction** (written by `fm4sd_licences.py`, carried forward by
  `--index`): `licence`, `licence_url`, `published`, `redistributable`, `arxiv_title`. These
  cannot be regenerated from the README, and because the scratch copy starts from the
  committed manifest, comparing them would only re-read the values under test.

Any key outside all three sets is reported as *not compared* rather than failing the run —
`#29` is adding manifest fields right now, and a gate that goes red the moment the schema
grows would be turned off rather than fixed.

The projection is printed on success (`383 entries × 8 fields`), so the check cannot pass by
comparing nothing.

### 2. `--index --remote` is a no-op

Copy the same three files into a second scratch directory, hash the manifest, run
`--index --remote` (the single upstream fetch), and assert the process exits 0 with the
manifest byte-identical. `--remote` once overwrote the manifest with upstream's index
(#2 in the review); this is the regression test for that, and it also covers upstream being
unreachable, since a failed fetch exits non-zero.

### 3. Published counts agree with the manifest

Derive every figure from the manifest itself — never from `papers/`, which CI does not have:

| Figure | Derivation |
|---|---|
| entries | `len(entries)`, cross-checked against `stats` and the header `count` |
| with / without an arXiv id | `arxiv_id` present / absent |
| fetched | `fetch_status in ("ok", "cached")` |
| LaTeX vs PDF | `source == "tex"` / `source == "pdf"` among fetched |
| code links | `has_code` |
| text bytes | `sum(text_bytes)` among fetched |
| licence records | `licence == "api-omitted"` |

Then read the published figures out of `README.md`, `references/README.md` and
`PROVENANCE.md` with phrase-anchored patterns (`| **383** | entries in the index |`,
`| Extracted text | 42.4 MB |`, `COMMITTED — 383 entries`, …). Nothing is hardcoded: the
numbers under test are the ones the documents currently publish, so #29's count changes move
both sides together as long as the documents are updated in the same commit.

A figure whose pattern no longer matches is a failure, not a skip: a rewrite that drops the
claim has to update the checker in the same change.

**Byte totals are compared at whole-MB granularity (tolerance 0.5 MB).** The published figure
is a rounded summary of a value that legitimately moves a little between fetches (PDF
extraction sizes follow the extractor version), so demanding 0.1 MB equality in prose would
make the gate reject honest rebuilds. All integer counts are exact. Today's `42.4 MB`
claims sit 0.2 MB above the manifest's 42.2 MB; that residual is left for the owners of
`README.md` and `PROVENANCE.md`'s Corpus table rather than edited here.

`fm4sd_search.py stats` is run and its `entries` / `fetched (N latex, M pdf)` / `text on
disk` lines must also agree with the manifest. That catches a `stats` regression, and keeps
the documents' own citation (`Counts above are … stats`) honest.

## Documents this change touches

- `references/README.md`: two stale figures that the checks above caught on a clean
  checkout — `303 entries` (→ 383) and `~33 MB of text` (→ ~42 MB). `README.md` and
  `PROVENANCE.md`'s Corpus table are owned by parallel work (#29) and are not edited here.
- `AGENTS.md`: gate is automated; local command; branch-protection step.

## Verification

- `python3 scripts/check_reproducibility.py` — green on a clean checkout.
- Hand-edit a scratch copy of the manifest (a citation and an `arxiv_id`) → check 1 red.
- Hand-edit a scratch copy of `README.md` (one count in the research-layer table) →
  check 3 red.
- Patch a scratch copy of `fm4sd_fetch.py` so `compare_remote()` writes the manifest →
  check 2 red.
- The workflow itself is exercised on the PR: it should finish in ~2 minutes, since checks 1
  and 3 are local and check 2 is one HTTP GET plus a parse of both READMEs.

## Risks

- **Upstream availability.** Check 2 fails if `raw.githubusercontent.com` is unreachable.
  That is the desired signal (the gate is about reproducing against upstream), but it makes
  CI depend on GitHub's CDN; a retry loop already exists in `http_get()`.
- **Cross-ticket churn.** #29 changes counts, statuses and fetcher routes. The counts check
  reads published figures rather than constants, and the field projection warns instead of
  failing on unknown keys, so #29 should land green as long as it updates the documents it
  already touches.
- **Summaries are not covered.** `references/summaries/` digests are prose about papers, not
  derivable figures; the manual part of the gate still applies to them.

## Out of scope

- Configuring branch protection (an admin act — documented in `AGENTS.md`, not scripted).
- Scheduled runs: upstream drift is inspected on demand with `--index --remote`.
- The revision pinning and `--index` digest wipe (#33), which is sequenced after #29.
