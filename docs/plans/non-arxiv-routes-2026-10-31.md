# Plan — non-arXiv route families, reason-flavoured statuses, licence records (#29)

Delivery ticket #29. Decision: the resolution recorded on #9
(https://github.com/IFoA-ADSWP/fm4sd/issues/9#issuecomment-6535519313). Evidence:
`research/no-arxiv-payload.md` on branch `research/no-arxiv-payload`, refreshed for the
post-merge population in the #29 triage comment.

## What

1. **Split `fetch_one()` by route family.** arXiv entries keep the existing
   `/src/<id>` → `/pdf/<id>` path. Entries with no arXiv id get a route list derived from
   the index links: direct PDF (`pdf`), publisher PDF (`nature`, `pmc`, `springer`, plus
   `pdf` on the three publisher mirrors), PMLR (`pmlr`/`icml` landing → proceedings PDF),
   NeurIPS proceedings (link is already a PDF), and web-native HTML (`blog`/`site`, four
   slugs, extracted with a stdlib HTML parser). No scraping, credentials, JS or CAPTCHA
   solving. Web routes are throttled at ~1 req/s with the project's real User-Agent,
   separate from arXiv's 3 req/s.
2. **Retire `skipped:no-arxiv-id`.** Id-less entries are stamped at index time as
   `skipped:not-paper` (7 repo/blog rows) or `skipped:unreachable:<captcha|paywall|dead|unknown>`
   (35 rows from the audit's probe). Fetch failures on a live route are classified the same
   way, so a route that dies tomorrow reports a reason instead of an identifier gap.
3. **Manifest gains `licence`, `licence_source`, `shareable`** for the 18 new rows, seeded
   from the audit table and confirmed against the fetched payload. `shareable` is `yes` only
   for an explicit permissive grant (`tabpfnv2`, `tabssldataselect`, both CC BY 4.0);
   `no` where the content is © with no grant; `unknown` where nothing is stated. Unknown is
   never permission.
4. **Manifest record of the route used** (`route`: `direct-pdf`, `publisher-pdf`, `pmlr`,
   `neurips`, `web-native`) so a payload can be re-derived without re-reading the audit.
5. **Counts** in `README.md`, `references/README.md`, `PROVENANCE.md` from
   `fm4sd_search.py stats` (which gains a status tally), plus a PROVENANCE section and
   corrections-log row.

## Why

`skipped:no-arxiv-id` conflates "not on arXiv" with "cannot be fetched". 18 of the 60
id-less entries are fetchable by a plain HTTP client: seven direct PDFs, three publisher
PDFs, three PMLR, one NeurIPS and four web-native HTML papers. Fetching them makes the
corpus 340/383 instead of 323/383 and makes every remaining absence say why. Licence
fields are the precondition for publishing anything (#30): the manifest must be able to
answer "may this payload be shared?" before a shared extract exists.

## Manifest preservation (the #33 hazard)

`--index` on a payload-less tree drops fetch metadata for entries with no `.fetched`
marker (#33). This worktree has no payload for the 323 arXiv entries, so:

- new route payloads are fetched with a targeted `--fetch --only <18 slugs>`; it patches
  only those rows in place and never touches the other 365;
- `--index` now restores the eight fetch fields from the prior manifest when the identity
  is unchanged and the prior status was `ok`/`cached` — so a full pass is churn-free here
  and on a payload-present tree, and licence records are carried as before;
- `.fetched` markers now record the sha256 on their second line, so a payload-present
  `--index` can rebuild `sha256` from disk (old markers stay readable).

Revision pinning itself (recording *which* arXiv revision a sha256 belongs to) stays in
#33.

## Expected state

- 383 entries; 340 fetched (317 LaTeX, 18 PDF, 5 HTML/XML); 0 `skipped:no-arxiv-id`.
- Statuses: 7 `skipped:not-paper`; 22 `skipped:unreachable:captcha`, 7 `...:paywall`,
  2 `...:dead`, 5 `...:unknown`.
- 18 route entries carry a route record; 17 have payload + sha256, and the 18th
  (`tabssldataselect`) carries a recorded reason.
- 18 new rows carry `licence`, `licence_source`, `shareable`.
- No payload in the diff (`papers/` gitignored).

## Delivery note — the 18th row

The audit (2026-10-29) fetched the Nature and Springer PDFs with a plain client. On
2026-10-31 both served a JavaScript "Client Challenge" instead. `tabssldataselect` therefore
ends as `skipped:unreachable:captcha`, which the ticket allows ("or fail with a recorded
reason"), and `tabpfnv2` falls back to Europe PMC's full-text JATS XML for the same PMC
article (both PMC PDF endpoints also challenged). That is one fetched entry fewer than the
plan assumed, and one more recorded reason.

## Verification

- `--status` and `fm4sd_search.py stats` agree with PROVENANCE/README.
- Re-run `--index` after the targeted fetch: the 18 keep status/sha256, the 323 arXiv rows
  are byte-identical to `origin/main`'s manifest, only the 42 reason statuses change.
- Targeted `--fetch --only` re-run is a no-op (`cached`), no refetch.
- `git status` shows no payload; `git diff` touches scripts, manifest, docs, plan only.

## Risks

- Publisher routes rot (Nature/Springer block non-browser clients intermittently); each
  route has a fallback (Nature → PMC) and a recorded reason on failure.
- The four web-native pages are rendered server-side today; if one becomes a JS shell the
  HTML extractor's minimum-length guard fails it as `skipped:unreachable:unknown` rather
  than storing a stub.
