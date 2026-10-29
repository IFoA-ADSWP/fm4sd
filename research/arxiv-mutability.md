# What does a `sha256` in `references/manifest.json` promise?

Research for issue #20, feeding the reproducibility decision in #16.
Branch: `research/arxiv-mutability`. All measurements taken **2026-10-29** against live arXiv.

## Method note

- **Rate and identity.** All requests sequential, ≥1.15 s apart, one User-Agent
  (`fm4sd-research/1.0 (mutability study; https://github.com/IFoA-ADSWP/fm4sd)`). No parallel
  fetching, no `--index` ever run in the working clone.
- **Scripts and raw results** live outside the repo, in a scratch directory
  (`run_experiments.py`, `run_followup.py`, `results.json`, `results2.json`); nothing from there
  is committed. Two `--index` runs *were* executed, but only in throwaway `git archive` /
  `cp -R` copies of the repo, to measure what `--index` does to the digest column (see
  "Side finding").
- **Endpoints hit:** `https://arxiv.org/src/<id>[vN]`, `https://arxiv.org/pdf/<id>[vN]`,
  `https://arxiv.org/abs/<id>` (version list only), `http://export.arxiv.org/api/query`.
- **Baseline:** `references/manifest.json` at `53b82c9` (clean `main`), parsed at the
  `--- entries ---` delimiter.

### Correction to the ticket's premise

#20 says the manifest "records a `sha256` for 247 fetched bundles". **It records 28.**

| | count |
|---|---|
| manifest entries | 303 |
| fetched (`ok` + `cached`) | 253 (247 LaTeX source + 6 PDF — this is where "247" comes from) |
| entries with a **non-empty** `sha256` | **28** (all `fetch_status: ok`) |
| fetched entries with an **empty** `sha256` | 225 (all `fetch_status: cached`) |
| `skipped:no-arxiv-id` | 50 |

The 225 `cached` entries never carry a digest: `reconcile()` in `scripts/fm4sd_fetch.py`
recovers `fetch_status` and `text_bytes` from the `.fetched` marker on disk, but not `sha256`.
So the "pins" available to compare against are 28, not 247. Every refetch result below is over
those 28 — I refetched **all of them**, not a ~10 sample, because the population was small
enough to take whole.

## (a) Does `/src/<id>` pin a version or track latest?

The export API's `published` ≠ `updated` field marks a paper with more than one version.
Surveying all 253 ids in the manifest: **121 (48%) are multi-version**. I picked three with
2, 3 and 4 versions (version counts confirmed on each abs page's `[vN]` markers):

**`1208.5384` — 2 versions**

| fetch | HTTP | bytes | sha256 |
|---|---|---|---|
| `/src/1208.5384` (bare) | 200 | 1019479 | `7f52bdbb4682a6d5461ce8482f6c8182e703020115e54953f24144edc1279a58` |
| `/src/1208.5384v1` | 200 | 1021176 | `29baaf1baf71ac3ccceb9c000025dba103f4386c69977487136652fc64d7bffe` |
| `/src/1208.5384v2` | 200 | 1019479 | `7f52bdbb4682a6d5461ce8482f6c8182e703020115e54953f24144edc1279a58` ← **same as bare** |
| `/src/1208.5384v3`, `v4` | 404 | 0 | — |
| `/pdf/1208.5384` (bare) | 200 | 775839 | `b72916770142fa614946eecb23dbadaea966dd1a0e09cfd12efb34fc86f2a6c9` |
| `/pdf/1208.5384v1` | 200 | 846481 | `bd0994352c41e8adce2c4b091906a706361a4005284d73e4a57e4dffe9d1d935` |
| `/pdf/1208.5384v2` | 200 | 775839 | `b72916770142fa614946eecb23dbadaea966dd1a0e09cfd12efb34fc86f2a6c9` ← **same as bare** |

**`1508.06378` — 3 versions**

| fetch | HTTP | bytes | sha256 |
|---|---|---|---|
| `/src/1508.06378` (bare) | 200 | 1483949 | `575f93573ffa59e29384418d6dc8a10f92784d21ad2f88fc9612b6401f6d0fd5` |
| `/src/…v1` | 200 | 1635554 | `984cdeb152fc08e1df22364e190af4a2e8c2cb59db8d9bfbc315cd5b3e181f3a` |
| `/src/…v2` | 200 | 1489806 | `57fd7100bb163a9ba995c684fa0968640f9a53ee37604fbe51a8408eb160bba3` |
| `/src/…v3` | 200 | 1483949 | `575f93573ffa59e29384418d6dc8a10f92784d21ad2f88fc9612b6401f6d0fd5` ← **same as bare** |
| `/src/…v4` | 404 | 0 | — |
| `/pdf/…` bare vs `v3` | 200 | 1721109 | `d13bce402ee7a6ed706030ec5759a14da7e18e00c6d48291558d0e76a3acad0d` ← **identical**; `v1`/`v2` differ |

**`1804.09253` — 4 versions**

| fetch | HTTP | bytes | sha256 |
|---|---|---|---|
| `/src/1804.09253` (bare) | 200 | 229080 | `55a1e3a15186a165a941afda23e44529a4c2913746c109f9a8d3846c33e3ce28` |
| `/src/…v1` | 200 | 161357 | `d0b68af40f71bdd713aaab813dc17e16e26017639169feb33e2584cb6fa03b32` |
| `/src/…v2` | 200 | 130755 | `3134d773193f4b7307d4148b9c82f94ebcd9ec42736ab3c5260e8db0e0ffef9c` |
| `/src/…v3` | 200 | 461226 | `ebb6348973bcdb247e93ba0b96daad4c89fedb9b7ff056dd18011462810f1f89` |
| `/src/…v4` | 200 | 229080 | `55a1e3a15186a165a941afda23e44529a4c2913746c109f9a8d3846c33e3ce28` ← **same as bare** |
| `/pdf/…` bare vs `v4` | 200 | 324544 | `896368079dc8b1a150c33c3f361d317fc096e1a877a89c93354f5aa8b09a2c62` ← **identical** (verified in a separate probe) |

**Answer: `/src/<id>` tracks latest.** In 3/3 cases the bare URL served byte-for-byte the
latest version's bundle (`final_url` did not redirect — arXiv answers on the bare path
directly). Every earlier version has a distinct digest and a distinct size; a version past the
last one 404s. The fetcher (`fm4sd_fetch.py:348`) requests exactly this bare URL, so every
recorded digest is a digest *of whichever revision was current at fetch time* — for these
three, the recorded manifest digest equals the latest version (`1508.06378` → v3,
`1804.09253` → v4, `1208.5384` → v2).

## (b) Would the recorded pins survive a refetch today?

All 28 entries that have a recorded `sha256` were refetched from the same URL class the
fetcher uses (`/src/<id>` for `source: tex`, `/pdf/<id>` for `source: pdf`), 2026-10-29.

| entry (arXiv id) | published | src | recorded sha256 | refetched sha256 | match? |
|---|---|---|---|---|---|
| `0904.1483` | 2009-04-09 | tex | `8af857504ce8efd6d1e683f371fb9ee908f51db7b8a74d0677bf8bc5d061e5ad` | `8af857504ce8efd6d1e683f371fb9ee908f51db7b8a74d0677bf8bc5d061e5ad` | yes |
| `1208.5384` | 2012-08-27 | tex | `7f52bdbb4682a6d5461ce8482f6c8182e703020115e54953f24144edc1279a58` | `7f52bdbb4682a6d5461ce8482f6c8182e703020115e54953f24144edc1279a58` | yes |
| `1508.06378` | 2015-08-26 | tex | `575f93573ffa59e29384418d6dc8a10f92784d21ad2f88fc9612b6401f6d0fd5` | `575f93573ffa59e29384418d6dc8a10f92784d21ad2f88fc9612b6401f6d0fd5` | yes |
| `1607.02623` | 2016-07-09 | tex | `f9022ea1d80978ab370a692c02289af963a6bd460c0f123f1e6fa21b2abf0cd5` | `f9022ea1d80978ab370a692c02289af963a6bd460c0f123f1e6fa21b2abf0cd5` | yes |
| `1701.05452` | 2017-01-19 | pdf | `aeebb1ff84e96cd9701324043993107a6e4ae8e98f9ebc91bb047b7b87f8b042` | `aeebb1ff84e96cd9701324043993107a6e4ae8e98f9ebc91bb047b7b87f8b042` | yes |
| `1804.09253` | 2018-04-24 | tex | `55a1e3a15186a165a941afda23e44529a4c2913746c109f9a8d3846c33e3ce28` | `55a1e3a15186a165a941afda23e44529a4c2913746c109f9a8d3846c33e3ce28` | yes |
| `1805.10854` | 2018-05-28 | tex | `25d6b5ac016f5ed2dbfca692d5c37e16479cf8e4afdaf4f1e2bc16672bdc2e98` | `25d6b5ac016f5ed2dbfca692d5c37e16479cf8e4afdaf4f1e2bc16672bdc2e98` | yes |
| `1811.10192` | 2018-11-26 | tex | `942a21a884ffef8b29c886fb7055fa11129a4213e19679a811c15fc4b3208f8c` | `942a21a884ffef8b29c886fb7055fa11129a4213e19679a811c15fc4b3208f8c` | yes |
| `1812.03432` | 2018-12-09 | tex | `ebfa4dce532ed72b0baf0578d92853601242467a48bc20b12ddbb6ad5f336792` | `ebfa4dce532ed72b0baf0578d92853601242467a48bc20b12ddbb6ad5f336792` | yes |
| `1912.12356` | 2019-12-27 | tex | `2f82a06e3be6087a5829d25b58d1b4ca83d6e8ec0071a4910a86b2d724e9651d` | `2f82a06e3be6087a5829d25b58d1b4ca83d6e8ec0071a4910a86b2d724e9651d` | yes |
| `2008.05693` | 2020-08-13 | tex | `06241faedf6bd7a23732e81fd18dc57d140eb55bff671172d4c2fd5d76197810` | `06241faedf6bd7a23732e81fd18dc57d140eb55bff671172d4c2fd5d76197810` | yes |
| `2102.10154` | 2021-02-19 | tex | `7793c687880a322f46fb400ae735490babe62ef086e33b95c97160722d09c71d` | `7793c687880a322f46fb400ae735490babe62ef086e33b95c97160722d09c71d` | yes |
| `2103.02089` | 2021-03-02 | tex | `f98b7201829faa83b6409d2fcde50eedb5a38c0bd841d919f271c4e5b1d5d51c` | `f98b7201829faa83b6409d2fcde50eedb5a38c0bd841d919f271c4e5b1d5d51c` | yes |
| `2103.07200` | 2021-03-12 | tex | `c5cc6d0961a04288956e05353c01cdea8d4fbbc9c6bb5dfa82bd2321ce8d42ab` | `c5cc6d0961a04288956e05353c01cdea8d4fbbc9c6bb5dfa82bd2321ce8d42ab` | yes |
| `2110.05207` | 2021-10-11 | tex | `a8a9160e80bf7421a0345e2e3c785c9fb0b1881a3049e0f0d7a2c0b89b8c157d` | `a8a9160e80bf7421a0345e2e3c785c9fb0b1881a3049e0f0d7a2c0b89b8c157d` | yes |
| `2111.00581` | 2021-10-31 | tex | `d89b5e8c717557c814f00daa98914605c7b2e8fc05b909063e461911a54c810b` | `d89b5e8c717557c814f00daa98914605c7b2e8fc05b909063e461911a54c810b` | yes |
| `2201.13267` | 2022-01-27 | tex | `a236ee398d6c529387374ceaa37c9f349f995a0378baf6b8cf5a7beecabaea2e` | `a236ee398d6c529387374ceaa37c9f349f995a0378baf6b8cf5a7beecabaea2e` | yes |
| `2202.13000` | 2022-02-25 | tex | `83daaf11e9b3d64618c0b51784895d07093e026d06620b5aca7a4147630646ec` | `83daaf11e9b3d64618c0b51784895d07093e026d06620b5aca7a4147630646ec` | yes |
| `2208.01262` | 2022-08-02 | tex | `4330169f7ccd350ad240e85d49288c1f25de06e9ec1287c2a182dcfdbcc796e9` | `4330169f7ccd350ad240e85d49288c1f25de06e9ec1287c2a182dcfdbcc796e9` | yes |
| `2210.05091` | 2022-10-11 | tex | `2f8fe5ba81bfae7f64cec4df7896ce404108b2fb92fd480de43df5590ad55426` | `2f8fe5ba81bfae7f64cec4df7896ce404108b2fb92fd480de43df5590ad55426` | yes |
| `2212.00985` | 2022-12-02 | pdf | `96aef0d13370ca7e8259eea4a5c0c51d9ac88f33c711b86eaad88c02647c60c2` | `96aef0d13370ca7e8259eea4a5c0c51d9ac88f33c711b86eaad88c02647c60c2` | yes |
| `2301.03005` | 2023-01-08 | tex | `6eb315daef76453f704d7a488dc342cded7ac723a6cb3c9a11636073ec886372` | `6eb315daef76453f704d7a488dc342cded7ac723a6cb3c9a11636073ec886372` | yes |
| `2303.01923` | 2023-03-03 | tex | `c9e0f395597298251a293dc072dad183a0ea412d5f303a407762f9cee4604903` | `c9e0f395597298251a293dc072dad183a0ea412d5f303a407762f9cee4604903` | yes |
| `2307.07771` | 2023-07-15 | tex | `1038d0acfe746a8b79eda88eba61d13f93eb10180974334139b43d113481292c` | `1038d0acfe746a8b79eda88eba61d13f93eb10180974334139b43d113481292c` | yes |
| `2311.03222` | 2023-11-06 | tex | `a5cc0e01c25123657b67f1a0182896c33e2361a06d04dab15d716928d7e1b5da` | `a5cc0e01c25123657b67f1a0182896c33e2361a06d04dab15d716928d7e1b5da` | yes |
| `2411.13822` | 2024-11-21 | tex | `c5fbbe4cf3611d8365a7e0fda8849da265369f2624d30e29b22c5c195cc89b77` | `c5fbbe4cf3611d8365a7e0fda8849da265369f2624d30e29b22c5c195cc89b77` | yes |
| `2608.09725` | 2026-08-10 | tex | `f32d2d345c8aff4857e3cb7d6bfadb0865c29b107a84bfaf789626c302ba8699` | `f32d2d345c8aff4857e3cb7d6bfadb0865c29b107a84bfaf789626c302ba8699` | yes |
| `2608.16137` | 2026-08-17 | tex | `699d249b1502598abd8758b43c53ab914fd410f065e3311deb3fb295797e012b` | `699d249b1502598abd8758b43c53ab914fd410f065e3311deb3fb295797e012b` | yes |

**Match rate: 28/28 = 100%** (span 2009–2026; 26 source-bundle, 2 PDF entries; the 12-row
sample first run and the remaining 16 in a second run agree). Two of the 28 were additionally
refetched through the real fetcher (`fm4sd_fetch.py --fetch --only …` in a scratch copy) and
matched the manifest too.

**Caveat on what 100% means.** 14 of these 28 ids are multi-version papers (surveyed via the
API), and 121/253 of the whole corpus are. Nothing in the measurement challenged the pins
today; nothing in the measurement can stop a pin from breaking the day an author posts
`v(N+1)`. The 100% is a same-day observation, not a stability guarantee.

## (c) Is anything arXiv offers actually immutable?

| candidate | verdict | evidence |
|---|---|---|
| `/src/<id>` (bare) | **mutable — tracks latest** | 3/3 picks: bare digest == latest `vN` digest; earlier versions differ |
| `/pdf/<id>` (bare) | **mutable — tracks latest** | 3/3 picks: bare digest == latest `vN` digest |
| `/src/<id>vN`, `/pdf/<id>vN` | **pinned by construction; immutability is arXiv policy, not just observed** | distinct digest per version, 404 past the last version, byte-identical on repeat fetch within this session. arXiv's own docs: *"Once made public, each version of a work is considered a permanent part of the scientific record and may not be removed"* ([Version Availability](https://info.arxiv.org/help/versions.html)) — replacements increment `vN`, they never rewrite it |
| export API, bare id | mutable metadata | `id_list=1208.5384` returned `<id>…/abs/1208.5384v2</id>`, `updated` = v2 date |
| export API, `id_list=1208.5384v1` | **pins metadata to that version** | returned `<id>…/abs/1208.5384v1</id>`, `updated` = 2012-08-27 (v1 date), `published` = same; one `<entry>`; distinct response bytes from the bare query. Metadata only — the API does not serve bundle bytes |
| `abs/<id>` page | shows latest, lists all versions | `[v1]…[v4]` markers matched the version counts used above |

What I did **not** establish: I repeated a version-suffixed fetch twice *within one session*
(identical bytes both times), but a version-suffixed URL's stability across months or years is
a claim about arXiv's operations, which a same-day test cannot prove — the evidence for it is
the quoted permanence policy plus the observed fact that v1 bytes for a 2012 paper differ
cleanly from v2 and neither has been rewritten into the other.

## Side finding: the digest column is fragile inside the repo too

Measured in throwaway copies of the repo (never the working clone):

- **`--index` wipes every digest.** A copy with payload on disk for 3 papers: 28 non-empty
  `sha256` before, **0 after** `--index`. `reconcile()` restores `fetch_status` (the 3 came back
  as `ok`) but not `sha256`; `carry_forward()` only carries keys that are not `Paper` fields,
  and `sha256` is one.
- **A fresh clone has nothing to restore.** `git archive HEAD` → `--index` → 253 entries with
  empty `fetch_status`, 0 digests. The committed manifest is the *only* copy of the 28 digests.
- The git history agrees: `32f26d2` (research layer) had **0 of 275** digests despite 225
  entries marked `ok`; the 28 that exist today all arrived with the actuarial batch
  (`4f96367`), which is the last fetch that ran without a subsequent `--index` losing them.

So the digest record is not just upstream-mutable; it is one documented command away from
being emptied in-repo.

## Enough to decide #16?

**What a `sha256` in this manifest means today: a snapshot of one moment** — the bytes that
`arxiv.org/src/<id>` (or `/pdf/<id>`) happened to serve on the fetch date, i.e. whatever
revision was then current. It is not a pin of a version (the fetcher never asks for one), not a
promise of a stable rebuild (a new `v(N+1)` on 48% of the corpus changes the answer with no
change on our side), and not even a durable record (225 of 253 fetched entries have no digest,
and `--index` deletes the 28 that exist).

**What "reproducible" can credibly mean for this repo — two different things, and #16 has to
pick one:**

1. **Same-IDs-current-content (weakest, matches what the repo does now).** A rebuild fetches
   the same 253 ids and gets *current* text; content may have moved to a newer version than
   the recorded snapshot. An automated check can verify ids, counts, categories and
   README-derived fields — exactly #16's proposed 15-line job — but **must not compare
   recorded `sha256` against a bare-URL refetch**, because that check would fail whenever an
   author posts a new version: it would be testing arXiv's version history, not this repo.
2. **Bit-identical snapshot (strong, available but not implemented).** arXiv *does* offer an
   immutable handle: record the resolved version (`1508.06378v3`) in the manifest and fetch
   `/src/<id>vN`. Digests taken that way can be re-asserted forever, per arXiv's stated
   permanence of versions. Nothing in the repo does this today.

Plainly: **a `sha256` here is currently a dated provenance snapshot, not a verification
target.** If #16 wants an automated check that stays green, either (a) scope it to
README-derived and metadata fields and leave `sha256` documented in `PROVENANCE.md` as
"digest of the revision current at fetch time, verified on 2026-10-29 for 28/28 entries", or
(b) make the manifest version-aware (store `id@vN`, fetch the suffixed URL) and only then can
a check assert digest equality. Option (b) also fixes the fragility above, since `--index`
would need to carry the resolved version forward to keep its own check honest.

**Limits of this study, stated outright:** all refetches are same-day (2026-10-29); no
longitudinal test of version-suffixed URL stability was possible; the 225 digest-less entries
could not be refetch-compared (no baseline exists for them); and only 2 of the 28 refetches
went through the actual fetcher rather than a direct GET of the same URL.
