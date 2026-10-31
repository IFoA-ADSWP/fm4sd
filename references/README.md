# Paper corpus

A local, greppable corpus of the papers listed in the [fm4sd](https://github.com/borawhocodess/fm4sd)
index, built so the research question can be asked of the literature instead of
recalled from memory.

## Why this exists

fm4sd is a README of links. Its `papers/` directory is gitignored, so there is
nothing in that repo to vendor — the value is in the URLs, and the URLs point at
arXiv. Cloning it yields one markdown file.

So the corpus is rebuilt locally by resolving those links. What gets committed is
the *index* and the *digests*; the paper payload stays on disk.

## Layout

```
references/manifest.json   COMMITTED — 431 entries: id, pinned revision, title, category,
                            subcategory, citation, licence, shareable, sha256, fetch status,
                            published date
references/summaries/      COMMITTED — digests and sweep findings
papers/<slug>/text.txt     GITIGNORED — extracted plain text
scripts/fm4sd_fetch.py     parse the index, fetch (arXiv + non-arXiv routes), extract
scripts/fm4sd_licences.py  resolve licences from the arXiv API
scripts/fm4sd_search.py    query the manifest, grep the text
```

Start at [`summaries/`](summaries/) — `README.md` there indexes the digests, and
[`summaries/SWEEPS.md`](summaries/SWEEPS.md) records the targeted `grep` sweeps, including the
negative results.

## Usage

```bash
python3 scripts/fm4sd_fetch.py --index      # README -> manifest.json
python3 scripts/fm4sd_fetch.py --fetch      # fetch + extract all missing
python3 scripts/fm4sd_fetch.py --status     # what is on disk, and why not
python3 scripts/fm4sd_fetch.py --check-revisions  # pins that have moved upstream
python3 scripts/fm4sd_licences.py           # fill in licences via the arXiv API

python3 scripts/fm4sd_search.py stats
python3 scripts/fm4sd_search.py list --has-code --since 2025
python3 scripts/fm4sd_search.py show nanotabpfn
python3 scripts/fm4sd_search.py grep "zero.inflation" --context 2
```

Fetch is resumable (`--force` to refetch) and cached via a `.fetched` marker per
paper. The corpus is ~52 MB of text for the fetched subset: 381 of 431 entries
(354 LaTeX, 22 PDF, 5 HTML/XML).

## Why 50 entries are not in the corpus

Entries with no arXiv id are not simply skipped. Each one records the reason it is
absent, and `--status` prints the tally:

| Status | n | Meaning |
|---|---|---|
| `skipped:unreachable:captcha` | 22 | browser-verification challenge (OpenReview, ACM, SSRN, ResearchGate, and Nature/Springer on the day this was built) |
| `skipped:unreachable:paywall` | 13 | subscription full text (Elsevier, IEEE, Springer chapter, and the journal-only actuarial canon added for #47) |
| `skipped:unreachable:unknown` | 6 | landing page only, or bot-defence with no observable paywall |
| `skipped:unreachable:dead` | 2 | 404/DNS failure, or a stub redirect to something else |
| `skipped:not-paper` | 7 | repo/blog rows with no paper behind the link |

No scraping, credentials, JavaScript or CAPTCHA solving is used: a route either
answers a plain HTTP GET at ~1 req/s or it is recorded as unreachable. The audit
behind those reasons is `research/no-arxiv-payload.md` on branch
`research/no-arxiv-payload` (decision on #9).

## Two design decisions worth knowing

**LaTeX source, not PDF.** For every paper the fetcher tries
`arxiv.org/src/<id>` (the `.tar.gz` of `.tex` sources) before falling back to
`arxiv.org/pdf/<id>`. Source bundles are plain text with section structure and
math intact, so they are greppable and cheap for a model to read; PDF extraction
loses both and is only a fallback for papers with no source available. The PDF
path is implemented with PyMuPDF (`pip install pymupdf`).

**The payload is gitignored, partly on licensing grounds.** Licences in this index are not
uniformly permissive — individually-checked entries include arXiv non-exclusive-distrib and
CC-BY-NC-SA. `scripts/fm4sd_licences.py` queries the arXiv API for a per-paper licence, but
the API omits the licence element entirely (verified: 2511.03634 is CC-BY-4.0 on its abs page
yet has no `<arxiv:license>` in the API response), so it reports `api-omitted` for all 253.
The manifest therefore records the licence as *unreported* rather than guessing, and
`redistributable` is False everywhere — an unknown licence is not permission. To clear a
paper for redistribution, read the licence line on its abs page and add it to `PROVENANCE.md`.

Non-arXiv entries carry the same decision in three manifest fields: `licence`,
`licence_source` (the URL the claim was read from) and `shareable: yes|no|unknown`. Three are
verified CC BY 4.0 — `tabpfnv2`, `tabssldataselect`, `schemapile` — and the rest either state
nothing (`unknown`) or reserve rights (`no`). Unknown is never permission.

## Reading the corpus

`text.txt` is the raw concatenation of a paper's `.tex` files (LaTeX included) or
its extracted PDF text. It is intended to be grepped and read in slices by the
search tool, not read end to end. `--context` returns line neighbourhoods;
`--min-hits N` requires a paper to mention the term N times before it surfaces,
which keeps one incidental match from drowning out a paper that keeps returning
to the topic.

Full digests live in
`summaries/` — see that directory for what has been read closely.