# Plan — pin arXiv revisions (`id@vN`), fix the `--index` digest wipe (#33)

Delivery ticket #33. Follow-up to the gate decision on #16 and the mutability study on
`research/arxiv-mutability`; sequenced after #29 (route families) and #37 (the
`preserve_fetch()` half of the digest wipe).

## What the measurement established

From `research/arxiv-mutability.md` (#20, probes 2026-10-29):

- `/src/<id>` and `/pdf/<id>` track **latest**. The bare URL served byte-for-byte the
  latest revision's bundle in 3/3 mulit-version picks; every earlier revision has a
  distinct digest and a past-the-last revision 404s.
- `/src/<id>vN` and `/pdf/<id>vN` are pinned by construction: distinct digest per version,
  404 past the last version, byte-identical on repeat, and arXiv's own policy says a
  published version is permanent.
- The export API reports the current revision in the Atom entry's `<id>`:
  `id_list=2102.10154` → `<id>http://arxiv.org/abs/2102.10154v3</id>`. Re-verified
  2026-10-31 for this change.
- #37's `preserve_fetch()` already stops a payload-less `--index` from erasing fetch
  metadata; the remaining half is the *semantics*: the fetcher still asks for the moving
  URL, and nothing records which revision a digest belongs to.

Population at the start of this change: **383 entries, 323 with an arXiv id, 340 fetched
(317 LaTeX, 18 PDF, 5 HTML/XML)**; 115 entries carry a non-empty `sha256` (98 arXiv +
17 route), 225 fetched rows have none — all of them `cached`, because the old cached
branch never recovered a digest.

## Schema

- `arxiv_id` stays **unversioned** and unchanged. Slugs, licence carry-forward and
  `match_year` all key off it, and `normalise_arxiv_id()` already strips a `vN` on ingest.
- New manifest field **`arxiv_rev: int`** beside it: the pinned revision number `N`
  (`arxiv_rev: 3` means `id@v3`). `0`/absent means unpinned and only ever appears on rows
  that have no arXiv id or that could not be resolved; after the migration no id-bearing
  row is in that state.
- Serialisation omits `arxiv_rev` when it is `0`, so id-less rows keep exactly the shape
  they had.
- `.fetched` markers gain a third line (`tex\n<sha256>\nv3\n`); older two-line markers
  stay readable. `reconcile()` restores the revision from disk when the payload is
  present.

## Behaviour

1. **Resolve.** `resolve_arxiv_rev(id, limiter)` calls
   `https://export.arxiv.org/api/query?id_list=<id>` at arXiv's existing 3 req/s limiter,
   reads the first `<entry><id>…/abs/<id>vN</id>`, and returns `N`. It never constructs a
   version number, and a transport/parse failure returns `0` rather than guessing.
2. **Fetch pinned.** `fetch_arxiv()` resolves first when the row has no revision, then
   builds `https://arxiv.org/src/<id>vN` (and the PDF fallback `…/pdf/<id>vN`). A stored
   pinned revision is used as-is: a newer upstream revision is **never** silently adopted.
3. **Report drift, bump deliberately.** New `--check-revisions` resolves every pinned id
   and prints how many are behind their pinned revision (`id pinned v2, current v3`); it
   writes nothing. `--fetch --force` re-resolves and moves the pin to the current revision
   — the documented bump, one paper or all. PROVENANCE records both.
4. **`--index` preserves id, revision and digest.** `arxiv_rev` joins `FETCH_FIELDS`, so a
   payload-less rebuild restores it from the prior manifest exactly as `sha256` is now;
   with payload on disk `reconcile()` reads it from the marker.
5. **Gate.** `arxiv_rev` is added to `PAYLOAD_FIELDS` in `check_reproducibility.py` — it is
   payload/network-derived, so it is excluded from the README-derived comparison rather
   than reported as an unclassified key. Check 3 still holds the counts.

## Migration

All 323 id-bearing entries are resolved and refetched in this worktree, so each records a
revision and a digest: 225 rows gain their first digest, and the 98 existing arXiv digests
are re-recorded against the now-explicit revision. `papers/` stays gitignored; only the
manifest's metadata is committed. Failures are reported and counted, not looped on.

Expected result: 383 / 323 / 340 counts unchanged; 323 id-bearing rows with `arxiv_rev`
and `sha256`; digests overall 115 → 340 (323 arXiv + the 17 non-arXiv route payloads that
already had one).

## Docs

- `PROVENANCE.md`: what a `sha256` promises (the pinned revision, byte for byte), that
  earlier versions are permanent and later ones are not adopted, the `--check-revisions` /
  `--fetch --force` bump procedure, and the schema change in the manifest record sentence.
- `references/README.md`: the manifest layout line gains the revision field.
- No other figure changes — the corpus counts are untouched by this migration.

## Verification

- Every id-bearing row has `arxiv_rev > 0` and a 64-hex `sha256`; counts are 383 / 323 /
  340 and agree with `fm4sd_search.py stats`.
- `--index` run twice on a payload-less copy is idempotent and preserves id + revision +
  digest (the regression).
- `python3 scripts/check_reproducibility.py` — 3/3.
- Three spot checks: refetch the pinned URL for one LaTeX, one PDF and one recent entry
  and compare the digest byte-for-byte with the manifest.

## Risks

- A handful of ids may not resolve or may 404 on `/src/<id>vN`; each is recorded with the
  count and the slug, and stays honest rather than being papered over.
- The API's reported revision is the latest *now*: this pins what was current at
  migration time, which is exactly what the ticket asks for, and drift afterwards is
  surfaced by `--check-revisions`.
- Fetching 323 papers takes ~10–15 minutes at 3 req/s plus extraction; run once, resume
  from markers if interrupted (a marker only exists after a successful extraction).

## Delivery note — the export API's 429s, and how they were handled

The first full `--fetch` (323 ids, 2026-10-31) resolved 37 revisions through the export API,
then `export.arxiv.org` answered **HTTP 429 to every uncached query** for the next ~20 minutes
— the single-id-per-worker pattern is too fast for that host even at 3 req/s. Those 286 rows
still fetched, but from the bare URL, and the run reported "version resolution failed" per id
rather than pretending they were pinned.

The resolver gained two things as a result, both in the delivered code:

- **Batched resolution.** `id_list` accepts a comma-separated list, so a full pass is ~7
  requests (`ARXIV_API_BATCH = 50`) instead of 323, done once before the worker pool starts.
- **Abs-page fallback.** When the API refuses, the paper's `/abs/<id>` submission history
  lists every `/abs/<id>vN`; the highest N is the same fact from the same record. The
  fallback runs at the web limiter (1 req/s) and prints what it is doing.

Second pass: 60 ids resolved by the API, the other 226 from abs pages, then
`--fetch --force --only <286 ids>` refetched all 286 at their pinned URLs (18m42s). Final
state: **323/323 id-bearing rows pinned with a digest, 0 unresolved**. Three spot checks
(LaTeX, PDF, a 2026 paper) reproduce the manifest digest byte-for-byte from the pinned URL.
A fresh tree with no payload rebuilds those three rows from their pins with no API call.
