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

## Upstream relationship

- **Posture:** this fork **merges** `upstream/main`; it does not re-sync. Replacing the
  README with upstream's would destroy the 28 local actuarial entries, their manifest
  records and the three actuarial sub-categories, and buys nothing — no shared entry has
  been patched. Details: `docs/RESEARCH.md`.
- **Drift trigger:** merge when upstream is roughly **25 entries ahead** (about two weeks at
  its current ~3.5/day), or whenever a decision session needs fresher data. No calendar tick.
- **Local actuarial block:** 28 entries stay in this fork's `README.md` while their upstream
  PR ([borawhocodess/fm4sd#5](https://github.com/borawhocodess/fm4sd/pull/5), opened
  2026-10-30) is open. The local category is authoritative here until it lands; acceptance
  upstream is unknown (no fork PR has ever been merged there).
- **On landing:** drop the local block from `README.md`, re-run `--index`, and add a row to
  the corrections log. After that every sync is a pure merge.
- **Mechanics:** `git merge upstream/main`, then `--index` (fetch metadata is recovered from
  payload on disk; licence records are carried forward keyed by arXiv id), then `--fetch`
  the newly added papers. Divergence point: `62382d2` (2026-10-05).

## Corpus

"Entries parsed" counts the README's **paper** rows. The non-paper sections — `extras`,
`cookbooks`, `blog`, the setup preamble — are catalogue links and are deliberately not
parsed; a non-paper link inside a parsed section is an entry with `skipped:not-paper` instead.
`GLOSSARY.md` fixes the distinction.

| Field | Value |
|---|---|
| Index parsed | **`README.md` in this fork** since 2026-10-08 (was upstream `main/README.md` at `62382d2`) |
| Entries parsed | 383 (355 upstream + 28 actuarial) |
| With an arXiv id | 323 (84%) |
| Linking released code | 138 |
| Fetched locally | 340 — 317 LaTeX source bundles, 18 PDF, 5 HTML/XML (4 web-native papers + 1 PMC full-text XML) |
| Extracted text | 43.6 MB |
| Source preference | `arxiv.org/src/<id>`, falling back to `arxiv.org/pdf/<id>`; non-arXiv entries by route family (see below) |
| PDF extractor | PyMuPDF 1.28.2 |
| Rate limit | arXiv 3 req/s; non-arXiv web routes ~1 req/s, same real User-Agent |
| Not fetched | 43 entries, each with a reason: 22 `skipped:unreachable:captcha`, 7 `...:paywall`, 5 `...:unknown`, 2 `...:dead`, 7 `skipped:not-paper` |

`references/manifest.json` is the machine-readable record: id, title, category, section,
subcategory, citation, links, licence, `licence_source`, `shareable`, sha256, source type,
byte counts, fetch status, and for non-arXiv payloads the route used. Its header records which
index source was used.

### Non-arXiv routes — added 2026-10-31

Decision and policy: see *Corpus scope* above. Evidence: `research/no-arxiv-payload.md` on
branch `research/no-arxiv-payload` (probes 2026-10-29), refreshed for the post-merge index in
the #29 triage comment. These are the entries without an arXiv id that a plain HTTP client
could reach:

| Route | n | Entries |
|---|---|---|
| direct PDF | 7 | `tfm-agents-humans`, `era-of-experience`, `pfnsyn`, `good-bad-controls`, `cdc-prompt`, `mit-ai-report`, `dfs` |
| publisher PDF | 3 | `tabpfnv2` (Nature → PMC PDF → Europe PMC full-text XML fallback), `tabssldataselect` (Springer), `schemapile` (CWI/ACM) |
| PMLR | 3 | `ptnas`, `baguan-ts`, `pf-ges` |
| NeurIPS proceedings | 1 | `wikidbs` |
| web-native HTML | 4 | `circuits-framework`, `monosemanticity`, `nonergodic-geometry`, `dust` |

**Observed 2026-10-31, two days after the audit:** Nature and Springer served a JavaScript
"Client Challenge" to a plain HTTP client, so `tabssldataselect` is recorded as
`skipped:unreachable:captcha` rather than fetched, and `tabpfnv2` comes from Europe PMC's
full-text JATS XML instead of the Nature PDF. The reason is recorded, not hidden.

**Licence records.** The route entries carry `licence`, `licence_source` and `shareable`:
verified CC BY 4.0 for `tabpfnv2`, `tabssldataselect` and `schemapile`; `pfnsyn` is
CC BY-NC-ND 4.0, so its text stays local. The 70 arXiv rows added by the 2026-10-30 merge
still have no `fm4sd_licences.py` record; that gap is unchanged here.

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
| `fetch_status` | empty on the 49 entries with no arXiv id, so `--status` called them `(pending)` forever | `skipped:no-arxiv-id`, stamped at index time — itself retired 2026-10-31 for reason-flavoured statuses (see "Non-arXiv route families") |

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
were never fetched. *(Superseded 2026-10-31 — see Corpus scope below.)*

## Corpus scope

The corpus is deliberately incomplete, and the line is a capability line, not a judgement
about which papers matter. Living figures — how many entries, how many fetched — are not
repeated here: the Corpus table above and `python3 scripts/fm4sd_search.py stats` are the
record, and they move as entries are added or fetched.

### In scope — non-arXiv payload a plain HTTP client can reach

Non-arXiv papers that a plain HTTP client can reach are in scope, across these route
families (plus the arXiv source/PDF route the fetcher already served):

- **direct PDF** — a PDF URL in the index, e.g. a lab or funder copy
- **publisher PDF** — the version of record from a publisher, with a PMC mirror as fallback
- **PMLR proceedings** — the PMLR landing page, then its PDF
- **NeurIPS proceedings** — the NeurIPS landing page, then its PDF
- **web-native HTML** — a complete paper served as a web page, not a landing page or abstract
- **arXiv** — `arxiv.org/src/<id>`, then `arxiv.org/pdf/<id>`, as before

No scraping, credentials, JavaScript execution or CAPTCHA solving, ever. Reachability probes
use one plain HTTP client at about one request per second with a real User-Agent. A row that
is free in a browser but challenges an HTTP client stays out; CAPTCHA-gated papers may be
perfectly readable by a human and are still out of scope. "Unreachable" below therefore means
unreachable *to this fetcher*, not unavailable to a reader.

### Out of scope — everything else, with a reason

Each remaining entry carries a reason-flavoured status rather than `skipped:no-arxiv-id`
(retired):

- `skipped:unreachable:<captcha|paywall|dead|unknown>` — no plain-HTTP route served it:
  browser verification (OpenReview, ACM DL, SSRN, ResearchGate), a subscription paywall, a
  dead link, or a landing page with no payload to test
- `skipped:not-paper` — the link is a code repository or blog post, not a paper

The reason records what the route did, not what the paper is worth. Re-probing may move an
entry between reasons without moving the line.

### Licence and sharing

Per entry the manifest records `licence` (what the source declares), `licence_source` (the
URL that claim came from) and `shareable: yes | no | unknown`. An unstated, API-omitted or
unverifiable licence is recorded as unknown and treated as **not permission**. The arXiv
licence script writes the same `licence` under an older companion field, `redistributable`
(a boolean derived from that licence); where both are present they must agree.

Only `shareable: yes` entries are published: an extracted `text.txt` plus a citation and
licence header (source URL, licence, retrieval date) under `corpus-shared/<slug>/`.
Everything else stays in gitignored `papers/`, local to the clone. Open access is not the
same as shareable — free to read grants no right to redistribute — and a non-derivative
licence keeps even a fetchable paper's text local.

The probes behind this line are recorded in `research/no-arxiv-payload.md` on the unmerged
`research/no-arxiv-payload` branch; this section is the policy that outlives it. Vocabulary
used here is fixed in [GLOSSARY.md](GLOSSARY.md).

### Published extracts — added 2026-10-31

[`corpus-shared/`](corpus-shared/) is the only paper text this repo redistributes: the
extracted text of entries whose manifest record is `shareable: yes` **and** whose payload is
fetched, with the attribution each licence requires. It is written by
`scripts/fm4sd_publish_shared.py` and committed. The fetcher never writes there, so a re-run
of `--fetch` cannot widen the redistributed set on its own: an entry appears only after a
licence has been verified and the manifest records `yes`.

| Entry | Licence | Licence evidence | Published |
|---|---|---|---|
| `tabpfnv2` | CC BY 4.0 | <https://www.nature.com/articles/s41586-024-08328-6> | `text.txt` + `LICENSE.txt` |
| `schemapile` | CC BY 4.0 | <https://ir.cwi.nl/pub/34763/34763.pdf> | `text.txt` + `LICENSE.txt` |
| `tabssldataselect` | CC BY 4.0 | <https://link.springer.com/article/10.1007/s10994-026-07133-8> | **pending** — `skipped:unreachable:captcha`, no payload |

Each published directory holds `text.txt`, byte-identical to the `papers/<slug>/text.txt` the
digests were written from, and a `LICENSE.txt` naming the paper, its citation, its source URL,
the licence, the URL that licence was verified at, and the retrieval date.
[`corpus-shared/README.md`](corpus-shared/README.md) is generated alongside them and lists
the published, pending and withheld sets.

`pfnsyn` (CC BY-NC-ND 4.0) and `wikidbs` (its CC BY line covers the dataset and code, not the
paper, so `unknown`) stay local despite being fetched: non-derivative is not shareable, and
unknown is not permission.

Re-running is safe and idempotent:

```bash
python3 scripts/fm4sd_publish_shared.py           # write / update corpus-shared/
python3 scripts/fm4sd_publish_shared.py --check   # diff against the committed set, write nothing
```

The publisher republishes only from the manifest's recorded licence — it never re-probes a
licence and never invents text for an entry without payload. What it does with the awkward
cases:

- **Pending.** `tabssldataselect` is shareable but not fetched; it is reported, the run exits
  0, and it publishes on the first run after a fetch succeeds. The CAPTCHA is not bypassed.
- **Payload absent from this clone.** The committed files are kept and the generated README is
  unchanged, so a payload-less checkout cannot empty the directory.
- **Payload disagrees with the manifest.** The entry is refused and the run exits 1 rather than
  publishing a stale or truncated extract.
- **Licence re-checked and downgraded.** `<slug>/` is removed on the next run, which is what
  keeps the directory exactly the shareable-and-fetched set.
- **Retrieval date.** Stamped from the payload's mtime on first publish, then read back out of
  the committed `LICENSE.txt` while the text's sha256 is unchanged, so a re-run on another
  clone reproduces the committed bytes; a re-extracted text re-stamps it.

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

`--index` is safe to re-run: it reconciles against payload already on disk, restores recorded
fetch metadata when the payload is not on this tree, and carries forward the licence records
`fm4sd_licences.py` and the non-arXiv fetcher wrote rather than deleting them. `--force`
refetches deliberately. `--index --remote` only diffs against upstream and writes nothing.

`--fetch` resolves arXiv entries through `/src` → `/pdf`, and every other entry through its
route family; `--only <slug> …` restricts a run (used to fetch the 18 non-arXiv papers without
rebuilding the 323 arXiv payloads). `--status` prints the fetched total and the reason tally.

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
| 2026-10-31 | `skipped:no-arxiv-id` was retired: 18 non-arXiv entries now resolve through direct-PDF, publisher-PDF, PMLR, NeurIPS and web-native HTML routes, and the remaining 42 id-less entries carry `skipped:not-paper` or `skipped:unreachable:<reason>`. Fetched 323 → 340 (317 LaTeX, 18 PDF, 5 HTML/XML). Nature and Springer answered the 2026-10-31 probe with a JS challenge, so `tabssldataselect` is recorded as captcha and `tabpfnv2` comes from Europe PMC XML. See "Non-arXiv route families" (#29). |
