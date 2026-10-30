# Provenance

Every claim about the corpus in this repo resolves to something here.

## What this repo is

A fork of [borawhocodess/fm4sd](https://github.com/borawhocodess/fm4sd), which curates a
reading index for foundation models on structured data. Upstream's index is preserved verbatim
below our banner in `README.md`.

Upstream ships **no paper content** — `papers/` is gitignored there, and the repo is otherwise
one markdown file. So there was nothing to vendor; the corpus is rebuilt by resolving the
index's links against arXiv.

| Field | Value |
|---|---|
| Upstream | https://github.com/borawhocodess/fm4sd |
| Upstream commit at fork time | `62382d23` "unnest tabpfn versions" |
| Fork created | 2026-10-05 |
| Research layer added | 2026-10-07 |
| Origin of the seminar | [fm4sd seminar, Uni Freiburg, SS 2026](https://ml.informatik.uni-freiburg.de/teaching/summer-semester-2026/seminar-seminar-on-foundation-models-for-structured-data/) |

## Corpus

| Field | Value |
|---|---|
| Index parsed | **`README.md` in this fork** since 2026-10-08 (was upstream `main/README.md` at `62382d2`) |
| Entries parsed | 303 (was 275 before the actuarial category) |
| With an arXiv id | 254 (84%) |
| Linking released code | 117 |
| Fetched locally | 254 — 248 LaTeX source bundles, 6 PDF fallback |
| Extracted text | 33.4 MB |
| Source preference | `arxiv.org/src/<id>`, falling back to `arxiv.org/pdf/<id>` |
| PDF extractor | PyMuPDF 1.28.2 |
| Rate limit | 3 req/s, 5 worker threads |
| Not fetchable | 49 entries — `pmlr`, `doi`, `springer`, `blog`, `lgresearch`, or PDF-only links |

`references/manifest.json` is the machine-readable record: id, title, category, section,
subcategory, citation, links, licence, sha256, source type, byte counts, fetch status. Its
header records which index source was used.

### Index source — changed 2026-10-08

`--index` used to read `INDEX_URL`, the **upstream** `raw.githubusercontent.com/.../README.md`.
This is a fork whose README we took over, so local edits were being silently ignored: 28 papers
were added, `--index` reported 275 again, and only calling `parse_index()` directly (303) exposed
the mismatch. It now defaults to the **local** `README.md`; `--remote` diffs upstream against
that local index and prints the result — it writes nothing, since it previously overwrote
`references/manifest.json` with upstream's index and deleted the actuarial category along with it.

### Parsing — corrected 2026-10-29

Three fields the parser had been getting wrong since the research layer landed, all found by
reviewing the repo against its own manifest:

| Field | Was | Now |
|---|---|---|
| `citation` | empty on **all 303** entries — `CITATION_RE` required an escaped `\[`, and neither this README nor upstream's ever uses one (288 plain `[nie et al. 2023]`, 0 escaped) | 288 populated; links are stripped before matching so `[arxiv]` cannot read as a citation |
| `subcategory` | empty on the 28 actuarial entries — their `severity` / `frequency` / `tail` groupings are *indented* `##` headings, which a line-anchored `##` pattern and a `- ` bullet pattern both missed | `severity` (10), `frequency and count models` (11), `tail metrics, quantiles, reserving` (7); queryable via `fm4sd_search.py --subcategory` |
| `fetch_status` | empty on the 49 entries with no arXiv id, so `--status` called them `(pending)` forever | `skipped:no-arxiv-id`, stamped at index time |

Also corrected here: the research-layer counts in `README.md` and `references/README.md` still
read 275 / 225 / 30.5 MB from before the actuarial category, and the `api-omitted` count below
still read 225. All four documents now agree with `fm4sd_search.py stats`.

`--index` also now carries forward keys it does not derive — the licence, `published` and
`arxiv_title` records written by `fm4sd_licences.py` — instead of discarding them on every
rebuild. Previously the documented setup path (`--index && --fetch`) deleted all 253 of them.

### Legacy arXiv ids — corrected 2026-10-30

The arXiv-id patterns (`ARXIV_RE`, `ARXIV_PDF_RE`, `ARXIV_ABS_RE` in `fm4sd_fetch.py`) only
matched the modern `YYMM.NNNNN` form, so pre-2007 ids of the form `archive[/subclass]/yymmnnn`
were recorded as *no arXiv id at all*. One index entry was affected: `gnr` (*Organization of
Growing Random Networks*, Krapivsky & Redner 2001) links `cond-mat/0011094`, whose `/abs`,
`/pdf` and `/src` all serve 200 — yet it was counted among the entries with no id and skipped
by the fetcher. The patterns now accept both forms through one shared id fragment, and the
stored id is normalised (version suffix stripped, subclass case preserved) so the `/abs/`,
`/src/` and version-suffixed URL builders all resolve from it. Re-fetching `gnr` yields
`papers/gnr/` (LaTeX source, 78 KB of text) with a recorded sha256.

Consequence for the counts: the population is **49 entries genuinely lacking an arXiv id + 1
that was misclassified**, not 50 id-less. Every figure above, in `README.md` and in
`references/summaries/` was recomputed from `fm4sd_search.py stats` after the fix.
`fm4sd_licences.py` has not been re-run, so `gnr` has no licence record yet — its API-id
extractor is still modern-only (the same family of gap as #9).

### Actuarial category — added 2026-10-08

28 papers under `actuarial / loss modelling`, because the original index is ML-methods only: a
sweep across 225 papers for `Tweedie|compound Poisson|loss ratio|actuarial|claim frequency`
returned **two incidental hits**.

IDs came from arXiv API **search results, never constructed**, and authors/years were taken from
the API response rather than written from memory. Digest: `references/summaries/actuarial.md`.

Scope limit: **arXiv-only.** Paywalled actuarial venues (IME, ASTIN) are unreachable, and
`fm4sd_fetch.py` skips any entry without an arXiv ID — the same reason 49 pre-existing entries
were never fetched.

## Licence — recorded as UNKNOWN, deliberately

`scripts/fm4sd_licences.py` queries the arXiv API for a licence per paper. It returns
**`api-omitted` for all 253**.

Verified directly rather than assumed: the API omits the `<arxiv:license>` element entirely.
2511.03634 is CC-BY-4.0 on its `arxiv.org/abs` page, yet carries no licence element in the API
response. The manifest therefore records the licence as **unreported**, not as absent.

`redistributable` is `false` everywhere — an unreported licence is an unknown one, and unknown
is not permission. Hence:

```
papers/                     # gitignored — licence unresolved, and 78 MB
references/manifest.json    # tracked — public metadata only
```

Individually observed while reading (a sample, **not** a census):

| Paper | Licence |
|---|---|
| `nanotabpfn`, `modded-nanotabpfn`, `tabpfnv2closerlook` | CC-BY-4.0 |
| `finetuningtfm` | CC-BY-NC-SA 4.0 — non-commercial, no derivatives |
| `tabicl`, `tabdpt`, `tabpack` | arXiv non-exclusive distribution |

To clear any paper for redistribution, read the licence line on its abs page and add a row here.

## Reproducing the corpus

```bash
python3 scripts/fm4sd_fetch.py --index      # README -> references/manifest.json
python3 scripts/fm4sd_fetch.py --fetch      # fetch + extract, resumable
python3 scripts/fm4sd_licences.py           # licence fields from the arXiv API
python3 scripts/fm4sd_search.py stats
```

`--index` is safe to re-run: it reconciles against payload already on disk and preserves
fetch metadata rather than forcing a refetch, and it carries forward the licence records
`fm4sd_licences.py` wrote rather than deleting them. `--force` refetches deliberately.
`--index --remote` only diffs against upstream and writes nothing.

## Digests

`references/summaries/*.md` are written by an LLM reading `papers/<slug>/text.txt`, and each
cites the extracted text it came from. They are **synthesis, not primary sources** — verify
any load-bearing claim against the paper before relying on it. `SWEEPS.md` records the
`grep` queries used, so a negative result is reproducible rather than anecdotal.

## Corrections log

| Date | Correction |
|---|---|
| 2026-10-07 | `iced` was mislabelled as a model-compression paper in the private repo's notes. It is *In-Context Density Estimation for Tabular Data*. The compression paper is `tacticl` (*Task-Aware Compression of Tabular ICL Models*). |
| 2026-10-08 | The round-1 headline negative — "zero-inflation is unclaimed" — was published and then withdrawn: it was a bad sweep. `--min-hits 3` discarded every relevant paper (they contain 1–2 hits each), and the pattern missed the morphological variant `zero_inflated`. Zero-inflation does appear in tabular/causal FM generators (`tabcausal`, `foundcause`, `avici`, and a cited TabPFN microbiome use-case), so the contribution is narrower than "unclaimed" — it is the calibration and the learnability test, not the mechanism. Full write-up in [SWEEPS.md](references/summaries/SWEEPS.md#correction-2026-10-08-the-zero-inflation-is-unclaimed-result-was-a-bad-sweep); also summarised in [references/summaries/README.md](references/summaries/README.md). |
| 2026-10-08 | The speedrun gap report was withdrawn: the ledger does stack. A round-1 sweep found nothing about composability and reported that as a gap — wrong on two counts: the records are explicitly cumulative (`pr19` vs `pr19+pr20`, 31 runs each), and the paper is two records out of date. A leaderboard's live state lives in its repo, not its paper. Ledger now at 0.76 min / ~98×. Full write-up in [SWEEPS.md](references/summaries/SWEEPS.md#q3-correction-read-the-repo-not-just-the-paper); also summarised in [references/summaries/README.md](references/summaries/README.md). |
| 2026-10-30 | `gnr` was recorded as having no arXiv id because the fetcher's id patterns only matched the modern form; its legacy id `cond-mat/0011094` was misclassified. Id-less count 50 → 49; fetched 253 → 254. See "Legacy arXiv ids" above (#23). |
