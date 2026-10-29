# This fork's relationship with upstream (borawhocodess/fm4sd)

Research for decision ticket #17, filed under research ticket #21. Branch
`research/upstream-relationship`; this file is the only thing on it.

## Method note

- Upstream's index is `README.md` at `borawhocodess/fm4sd` `main` (there is no
  manifest there — the repo is one markdown file plus a `scripts/` dir added
  2026-10-21). Fetched two ways that agreed byte-for-byte: `gh api
  repos/borawhocodess/fm4sd/contents` + `raw.githubusercontent.com`, and
  `git show upstream/main:README.md` after adding upstream as a read-only remote
  and fetching (upstream `main` = `13b8240`, 2026-10-28).
- Both indexes were parsed **read-only** with this repo's own
  `scripts/fm4sd_fetch.py::parse_index()` — the same parser that built
  `references/manifest.json`. `--index` was never run; the committed manifest was
  only read. The merge test below ran in a throwaway `cp -R` copy outside the
  repo, deleted afterwards.
- Fork point: merge-base `62382d2` (2026-10-05, "unnest tabpfn versions").
  Fork is 6 commits ahead, 16 behind.

## (a) Verified diff counts — prior analysis confirmed exactly

| | total | with arXiv id | without |
|---|---|---|---|
| upstream `main` index | **355** | 294 | 61 |
| this fork's index | **303** | 253 | 50 |
| only upstream | **80** | 68 | 12 |
| only here | **28** | 28 | 0 |
| in common | **275** | | |

All four headline numbers (355 / 303 / 80 / 28 / 275) reproduce exactly. The
fork's manifest header (`"count": 303`) and `references/README.md` agree with
each other and with a fresh parse of the local `README.md`. The 28 local-only
entries are exactly the `actuarial / loss modelling` category added in PR #3
(`4f96367`). Upstream has **removed nothing** since the fork point — every
common entry still exists upstream, so the 80 are purely upstream's additions
in 16 commits over 23 days (2026-10-20 → 2026-10-28 plus the relational merge).

## (b) The 80 upstream-only entries

Topic spread (parsed section/category):

| section | category | n |
|---|---|---|
| papers | relational | 13 |
| papers | general | 2 |
| papers | tabular | 2 |
| papers | time series (forecasting) | 1 |
| queue | tabular | 31 |
| queue | relational | 12 |
| queue | time series | 6 |
| queue | general | 6 |
| queue | causal | 3 |
| queue | other | 3 |
| queue | mechanistic interpretability | 1 |

- **Actuarial: zero.** Not one of the 80 touches loss modelling, severity,
  frequency, or tail risk. Upstream's index is still ML-methods-only, exactly as
  the actuarial PR's justification stated. There is no upstream section the 28
  local entries could be said to duplicate.
- **No arXiv id: 12 of 80** — so a sync grows the non-arXiv population from 50
  to 61. Overlap with decision #9 is direct: 6 of the 12 are in `papers`
  (i.e. entries upstream treats as settled, not queued): `principled-datagen`,
  `dfs`, `rt-j`, `tabpfn-rel`, `limix2-contamination`, `tfm-systematic-survey`;
  the other 6 are in `queue`: `dust`, `schemapile`, `wikidbs`, `tabiclr`,
  `timestral`, `turkforecast`. If #9 lands "arXiv-only is a deliberate scope
  line", these 12 are index-visible but permanently unfetchable — the same
  status as the current 50.
- Roughly two-thirds (53/80) are in `queue`, which upstream treats as a
  reading shortlist, not the settled corpus. The `papers`-section share is 18.

### Upstream-only table

Upstream's index carries no paper titles (slugs + link + citation only), and
these 80 are not in our manifest (so no `arxiv_title`); "short title" is
therefore the slug and its author-year citation. `arXiv?` = has an arXiv id
(fetchable by our toolchain).

| id | short title (slug — citation) | actuarial? | arXiv? |
|---|---|---|---|
| pfn-amortization | pfn-amortization — hülskamp et al. 2026 | no | yes (2610.13764) |
| principled-datagen | principled-datagen — (no citation) | no | **no** (openreview) |
| dfs | dfs — kanter and veeramachaneni 2015 | no | **no** (mit pdf) |
| graphpfn | graphpfn — eremeev et al. 2025 | no | yes (2509.21489) |
| graphsage | graphsage — hamilton et al. 2017 | no | yes (1706.02216) |
| griffin | griffin — wang et al. 2025 | no | yes (2505.05568) |
| modded-nanort | modded-nanort — veloso et al. 2026 | no | yes (2610.28855) |
| plurel-to-rdb-pfn | plurel-to-rdb-pfn — abolhasani and ganapathy 2026 | no | yes (2607.29129) |
| rdb-pfn | rdb-pfn — wang et al. 2026 | no | yes (2603.03805) |
| rdl | rdl — fey et al. 2023 | no | yes (2312.04615) |
| relbench | relbench — robinson et al. 2024 | no | yes (2407.20060) |
| relgnn | relgnn — chen et al. 2025 | no | yes (2502.06784) |
| relgt | relgt — dwivedi et al. 2025 | no | yes (2505.10960) |
| rt-j | rt-j — ranjan et al. 2026 | no | **no** (openreview + site) |
| tabpfn-rel | tabpfn-rel — (no citation) | no | **no** (github only) |
| limix2-contamination | limix2-contamination — (no citation) | no | **no** (github issue) |
| tfm-systematic-survey | tfm-systematic-survey — archetti et al. 2026 | no | **no** (ssrn) |
| timersi | timersi — liu et al. 2026 | no | yes (2610.19725) |
| market-impact-cfm | market-impact-cfm — thumm and chen 2026 | no | yes (2610.12537) |
| proximalfm | proximalfm — muller et al. 2026 | no | yes (2610.08078) |
| tiger | tiger — faouzi 2026 | no | yes (2610.06156) |
| adaptive-mean-icl | adaptive-mean-icl — eppert et al. 2026 | no | yes (2610.07804) |
| dust | dust — dahal et al. 2026 | no | **no** (site + github) |
| fim-pp | fim-pp — berghaus et al. 2026 | no | yes (2509.24762) |
| illusion-of-replacement | illusion-of-replacement — rezaee 2026 | no | yes (2608.28980) |
| retrieval-icl | retrieval-icl — zhu et al. 2026 | no | yes (2610.05717) |
| softmax-ce-fix | softmax-ce-fix — barron et al. 2026 | no | yes (2610.31642) |
| standardization-trap | standardization-trap — nguyen et al. 2026 | no | yes (2610.08314) |
| byte-distill | byte-distill — marathe et al. 2026 | no | yes (2609.12303) |
| diffusion-curriculum | diffusion-curriculum — drozdova et al. 2026 | no | yes (2609.01449) |
| pde-pfn | pde-pfn — park et al. 2026 | no | yes (2610.13334) |
| clavaddpm | clavaddpm — pang et al. 2024 | no | yes (2405.17724) |
| g2t-fm | g2t-fm — eremeev et al. 2025 | no | yes (2508.20906) |
| grdm | grdm — ketata et al. 2025 | no | yes (2505.16527) |
| parameterfreeencoders | parameterfreeencoders — xu and wipf 2026 | no | yes (2607.05476) |
| path-to-pfrm | path-to-pfrm — abolhasani and ganapathy 2026 | no | yes (2610.23073) |
| relagent | relagent — huang et al. 2026 | no | yes (2605.07840) |
| relbench-v2 | relbench-v2 — gu et al. 2026 | no | yes (2602.12606) |
| reldiff | reldiff — hudovernik et al. 2025 | no | yes (2506.00710) |
| rtgl | rtgl — kolesnichenko et al. 2026 | no | yes (2609.01292) |
| schemapile | schemapile — döhmen et al. 2024 | no | **no** (doi + pdf) |
| syntherela | syntherela — hudovernik et al. 2025 | no | yes (2410.03411) |
| wikidbs | wikidbs — vogel et al. 2024 | no | **no** (neurips pdf) |
| active-feature-acq | active-feature-acq — kobayashi et al. 2026 | no | yes (2610.07406) |
| apt | apt — wu and bergman 2025 | no | yes (2502.04573) |
| contextgap | contextgap — zeldes 2026 | no | yes (2610.06679) |
| crash-kumo | crash-kumo — rafe and das 2026 | no | yes (2610.10321) |
| depth-help | depth-help — gong et al. 2026 | no | yes (2610.19814) |
| ftfm | ftfm — grabocka 2026 | no | yes (2610.25558) |
| geneicl | geneicl — bohl et al. 2026 | no | yes (2610.08694) |
| one-model-rule | one-model-rule — zhang et al. 2025 | no | yes (2505.20003) |
| orionmoe | orionmoe — bouadi et al. 2026 | no | yes (2610.20418) |
| pfn-anomaly | pfn-anomaly — bershtman and cohen 2026 | no | yes (2610.06693) |
| powergrid-tfm | powergrid-tfm — arowolo et al. 2026 | no | yes (2610.20462) |
| privtab | privtab — alrawajfeh et al. 2026 | no | yes (2610.10068) |
| ramanbench | ramanbench — koddenbrock et al. 2026 | no | yes (2605.02003) |
| recurrent-icl | recurrent-icl — vaidhya et al. 2026 | no | yes (2610.14998) |
| retrospective-inference | retrospective-inference — cai et al. 2026 | no | yes (2610.10317) |
| separability-gap | separability-gap — kobialka et al. 2026 | no | yes (2610.14989) |
| shaping-prior | shaping-prior — bouadi et al. 2026 | no | yes (2605.18971) |
| strategic-tabular | strategic-tabular — lv et al. 2026 | no | yes (2605.19662) |
| survicl | survicl — alberge et al. 2026 | no | yes (2610.22242) |
| survival-icl | survival-icl — seletkov et al. 2026 | no | yes (2603.29475) |
| tabgift | tabgift — li et al. 2026 | no | yes (2610.16990) |
| tabiclr | tabiclr — (no citation) | no | **no** (github only) |
| tabmosaic | tabmosaic — kim et al. 2026 | no | yes (2610.15699) |
| tabregobjectives | tabregobjectives — rudenko et al. 2026 | no | yes (2610.13909) |
| tabrelibench | tabrelibench — zhao et al. 2026 | no | yes (2610.13654) |
| tabular-data-scaling | tabular-data-scaling — rubachev et al. 2026 | no | yes (2610.26794) |
| taffy | taffy — li et al. 2026 | no | yes (2610.07559) |
| test-time-compute | test-time-compute — ning et al. 2026 | no | yes (2610.12005) |
| tfm-evo-surrogate | tfm-evo-surrogate — han et al. 2026 | no | yes (2609.18130) |
| tfm-provenance | tfm-provenance — bouadi et al. 2026 | no | yes (2610.02347) |
| tfm-streams | tfm-streams — verma et al. 2026 | no | yes (2610.05352) |
| kit | kit — zhang and li 2026 | no | yes (2609.34507) |
| morpheus-2 | morpheus-2 — aakriti et al. 2026 | no | yes (2610.24321) |
| timer-m1 | timer-m1 — zhang et al. 2026 | no | yes (2610.11734) |
| timestral | timestral — (no citation) | no | **no** (site) |
| tsfm-identification | tsfm-identification — won 2026 | no | yes (2610.08118) |
| turkforecast | turkforecast — (no citation) | no | **no** (github only) |

(80 rows; the `queue`/`papers` split is as listed in the spread table above.)

## (c) What a sync would destroy — less than the ticket assumes

The ticket #17 framing assumes per-entry `subcategory:` and `citation:` patches
this fork added to *shared* entries. **Verified: there are none.** Parsing both
READMEs with the same parser and comparing entry-by-entry across the 275 common
slugs: subcategory differs on **0**, and citation differs on **1** — and the one
difference (`icl-order`) is upstream *adding* a citation after our fork point,
not us patching anything. Our fork's diff against the merge-base `README.md` is
exactly two things: the research-layer preamble (fork banner, stats table,
usage) and the appended 28-entry actuarial category. Not one shared entry line
was touched.

The `subcategory` and `citation` *fields* in `references/manifest.json` are not
README patches — they are produced by the parser (`parse_index`) from structure
that exists in both READMEs (indented category headers, `— [author year]`
citations), and the parser itself lives in `scripts/fm4sd_fetch.py`, which
upstream does not have. They survive any sync that keeps our scripts.

That leaves the precise inventory of what each sync style destroys:

**A plain `git merge upstream/main` (tested in a scratch copy): merges cleanly,
destroys nothing.** Zero conflicts; README auto-merges to 383 parsed entries
(303 + 80); the actuarial block, the research preamble, and all scripts
survive. The only line-level losses are 4 shared entries replaced by upstream's
*improved versions* of themselves (kumorfm gains an archive.org link,
tabshallow gains its arXiv link, icl-order gains its citation, relicl moves to
the relational papers section) — each strictly an upgrade. The merge also
brings in upstream's new `scripts/log.html` and `scripts/talk.html`. Post-merge
housekeeping: re-run `--index` (now safe — 53b82c9 made it carry forward
licence/published/title/fetch metadata keyed by arXiv id) and `--fetch` the new
papers. Expected end state: 383 entries, 61 without arXiv id.

**A hard re-sync (replace our README with upstream's, then `--index`)** would
destroy:

1. The 28 actuarial entries in the index — and, with them, their manifest
   records: 28 entries with `fetch_status: ok`, sha256 digests, arXiv titles,
   published dates, licence records, and 2.83 MB of fetched corpus text whose
   on-disk `papers/<slug>/` payload becomes orphaned (the carry-forward in
   53b82c9 matches on arXiv id *present in the new README*; deleted entries
   have nowhere to carry to).
2. The three actuarial subcategories (`severity` 10, `frequency and count
   models` 11, `tail metrics, quantiles, reserving` 7) — 28 of the 67
   subcategory values in the current manifest.
3. The research-layer preamble in `README.md` (fork banner, corpus stats,
   clone-and-run instructions).

It would **not** destroy: the 39 subcategory values and 288 citations on
shared entries (parser-derived, reproduced from upstream's README), any script,
any digest in `references/summaries/`, or any fetch metadata for entries
present in both indexes. The word "patches" in #17 overstates the exposure:
the local patch layer is one appended README section plus parser logic, not
per-entry edits.

## (d) Upstream's appetite for outside changes

- **Pull requests, all history: 4, all closed, all merged from branches *on the
  upstream repo itself*** (`head.repo.full_name == borawhocodess/fm4sd` for all
  four — i.e. collaborators with push access, or the owner). PRs #2 and #3 from
  `Gurmeher23` (June 2026, presentation slides), #4 from the owner (relational
  work, Oct), #1 closed unmerged. **No fork-based PR has ever been opened
  against this repo, and none merged.** There is no evidence either way on
  whether an outside PR would be welcomed — the behaviour has simply never
  occurred. forks_count: 1 (ours).
- **Issues: none, ever** (0 open, none in `state=all`). Upstream does not use
  the issue tracker, so "PR-back-and-track" cannot lean on upstream issues for
  the tracking half.
- **Activity: high and current.** Last commit 2026-10-28 (`13b8240`, "queue
  tabrelibench" — yesterday relative to this research). 100 commits in the
  current page, spanning 2026-07-17 → 2026-10-28; ~24 commits in October
  alone; sole author `borawhocodess`, recent commits co-authored with Codex.
  Created 2026-06-15; 4 stars.
- **Drift rate: ~3.5 entries/day.** 80 entries added in the 23 days since the
  fork point. This is an actively curated personal reading index, not an
  archive — declared drift compounds visibly: every passing week adds roughly
  25 entries to the "only upstream" column.

## Enough to decide #17?

Yes — the facts that make the choice mechanical:

**Option 1 — re-sync (merge).** A plain `git merge upstream/main` costs one
merge commit, one `--index` + `--fetch` pass (68 new fetchable papers, ~a few
MB), and destroys **nothing**: the 28 actuarial entries and every
parser-derived field survive, as tested. The hard-sync variant (replace README)
destroys the actuarial category and is strictly worse for no benefit — rule it
out. Recurring cost: each future sync is another merge; at upstream's ~3.5
entries/day that is trivial per-sync but unbounded cumulatively. The 61
non-arXiv entries after merge stay unfetchable until #9 resolves — merging does
not make #9 worse, it just adds 12 more of the same kind.

**Option 2 — PR-back-and-track.** Send the 28 actuarial entries upstream as a
PR and keep the local category until it lands (or drop it on landing). Cost:
one PR of ~28 lines in upstream's README format (mechanical — the entries
already exist in exactly that format in our README); risk: upstream has never
merged a fork PR and does not run an issue tracker, so acceptance and latency
are unknown quantities, and upstream's index has no `actuarial` category or
sub-heading concept — the PR changes upstream's structure, not just its
contents, which is a bigger ask than "add these links". If merged, our 28
become ordinary upstream entries and the local-only set shrinks to zero,
making future syncs pure merges. If ignored, drift resumes and we are back
here with a stale PR to manage.

**Option 3 — declared drift.** Write "the index is a snapshot as of
`<date>`/`<sha>`; upstream moves at ~3.5 entries/day and we do not follow" into
`docs/RESEARCH.md` and `PROVENANCE.md`. Cost: zero maintenance, but the corpus
silently stops representing the field — the 80 already-missed entries include
relational staples (graphsage, relbench, relgnn) and the newest TFM queue work,
and the gap doubles in another 3 weeks. This is only defensible if the research
question is considered already answered against the snapshot.

**The hidden fourth fact that reframes the choice:** re-sync and PR-back are not
alternatives. A merge costs nothing and destroys nothing, so the only real
question is whether the 28 actuarial entries should also go upstream (option 2
on top of option 1) or stay fork-local (option 1 alone, drift declared for them
only). "Re-sync discarding the 28" was the framing in #17; it is unnecessary —
nothing needs to be discarded.
