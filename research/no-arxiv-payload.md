# The 50 entries with no arXiv payload: what the index offers, what is reachable, what licence it carries

Research for decision ticket #9 (wayfinding map: issue #18). Branch: `research/no-arxiv-payload`.
All probing done 2026-10-29.

## Scope and method

**Source of truth.** `references/manifest.json` (303 entries; 225 `cached`, 28 `ok`,
50 `skipped:no-arxiv-id`). `references/README.md` is corpus documentation and carries no
per-entry identifiers, so identifiers below come from the manifest's `links` block, which is
parsed from the repo-root `README.md` (the index itself). Checked: exactly **1 of the 50 has an
arXiv link at all** (`gnr`, a legacy `cond-mat/…` id); the other 49 have none.

**What I did not run.** `scripts/fm4sd_fetch.py --index` and `--fetch` were never executed —
the tracked manifest was only read. The repository working tree is untouched apart from this
file. Probe scripts and raw results live outside the repo in a scratch directory
(`probe.py` … `probe5.py`, `probe*_results.json`, `openalex_spotcheck.json`).

**How requests were made.** Python `requests`, one shared session, User-Agent
`fm4sd-corpus-research/1.0 (licence+reachability audit; https://github.com/IFoA-ADSWP/fm4sd)`,
global throttle of 1.1 s between requests (≈1 req/s), redirects followed, per-entry links tried
in payload-first order (`pdf` → `openreview` → publisher landing → DOI → blog/site). HTML reads
capped at 0.6–1.5 MB, PDFs at 3–30 MB; a few PDF reads were deliberately truncated once `%PDF-`
was confirmed (those rows say so). Licence text was scanned in page HTML (tags stripped) and in
full extracted PDF text (PyMuPDF). Publisher routes were corroborated with two free, credential-less
APIs: Crossref (`api.crossref.org/works/<doi>`, licence field) and OpenAlex (`is_oa`, `oa_status`,
`best_oa_location.license`). Each DOI was queried once.

**Vantage and honesty limits.** One machine, one network, no JavaScript execution, no cookies, no
login, no CAPTCHA solving, no institutional access. "Not reachable" below means *not reachable by a
plain HTTP client from here*, which is exactly the capability `scripts/fm4sd_fetch.py` has — it does
**not** prove a human with a browser would be asked to pay. Where I could not test something, the
row says `not checked`.

### Classification used

| Class | Meaning here |
|---|---|
| **FETCHABLE** | the index's URL (or a second link the same index provides) delivered full text — PDF, LaTeX, or complete web-native paper — with no credentials |
| **PAYWALLED** | full text withheld behind a login/subscription **or** a browser-verification challenge/CAPTCHA (the brief groups CAPTCHA with paywalls); the notes column says which flavour |
| **DEAD** | 404/DNS failure/stub redirect that lands on something that is not the paper |
| **UNKNOWN** | could not decide: bot-defence blocked us and no paywall was observable, or the URL offers a landing page with no payload to test |

## Headline counts

**18 FETCHABLE / 27 PAYWALLED (20 challenge-CAPTCHA + 7 subscription) / 4 UNKNOWN / 1 DEAD = 50.**

Reachability by the identifier the index actually offers (primary identifier per entry):

| Identifier offered | n | Fetchable | Paywalled (CAPTCHA) | Paywalled (subscription) | Unknown | Dead |
|---|---|---|---|---|---|---|
| OpenReview forum/pdf | 15 | 2 (via the index's PMLR link) | 13 | – | – | – |
| Direct PDF URL | 7 | 6 | – | – | – | 1 |
| DOI only | 11 | 1 | 3 | 5 | 2 | – |
| Publisher landing page | 10 | 2 | 4 | 2 | 2 | – |
| Web page / blog / repo only | 6 | 6 | – | – | – | – |
| Legacy arXiv id | 1 | 1 | – | – | – | – |
| **Total** | **50** | **18** | **20** | **7** | **4** | **1** |

Section split: 7 of the 50 sit in `## papers`, 43 in `## queue`.

Licence recorded for these 50 in the manifest: **absent** — the `licence` key exists only on the
253 arXiv entries (`api-omitted`); skipped entries carry no licence field at all.

Licence declared by the page/PDF itself:

| Licence status | n | Entries |
|---|---|---|
| CC BY 4.0 | 5 | tabpfnv2, tabssldataselect, cwfm, stablepfn, bitcoinllmforecast |
| CC BY-NC-ND 4.0 | 3 | pfnsyn (in the PDF), zerorel, ggpl |
| arXiv "assumed 1991–2003" licence | 1 | gnr |
| © / all-rights-reserved, no grant (page or PDF read) | 11 | agata, ratab, bsplinenorm, orchecause (LG), mmda, exo-zeroshot-tsfm (IEEE), ptnas, baguan-ts, pf-ges (PMLR), mit-ai-report, augtab |
| No licence statement at all in fetched content | 9 | tfm-agents-humans, era-of-experience, cdc-prompt, good-bad-controls, circuits-framework, monosemanticity, nonergodic-geometry, kumo-tabular, timesfm-3 |
| Code-repo MIT (not a paper licence) | 1 | aplr |
| Closed publisher, no reuse licence published (Crossref/OpenAlex checked) | 4 | sdi, kamel, qdhgan, tabllama |
| **Could not check** (page never served, or link dead) | 16 | 13 OpenReview-only entries, twostagefinance (SSRN), icl-order (ResearchGate), kumorfm (dead) |

## Full table

Entry id | Short title | Identifier offered | Reachable? | Licence noted | Notes
--- | --- | --- |---|---|---
gnr | Organization of Growing Random Networks (krapivsky & redner 2001) | legacy arXiv id `cond-mat/0011094` (+ DOI 10.1103/PhysRevE.63.066123) | **FETCHABLE** | arXiv "assumed 1991–2003" licence (abs page "view license" → `arxiv.org/licenses/assumed-1991-2003/`); Crossref: APS default | `/abs` 200, `/pdf` 200 (`%PDF-`, 320 KB), `/src` **200 `application/gzip`, 69.6 KB** — LaTeX source is there. This is a regex miss: `ARXIV_RE` only matches `\d{4}\.\d{4,5}`, never `cond-mat/0011094`.
tabpfnv2 | Accurate predictions on small data with a tabular foundation model (hollmann et al. 2025) | publisher landing (Nature, DOI in path) + PMC mirror | **FETCHABLE** | **CC BY 4.0** (landing page, Crossref) | article 200; `…/s41586-024-08328-6.pdf` 200 `application/pdf` (read truncated at ~600 KB after `%PDF-` confirmed); PMC mirror 200
aplr | APLR — interpretable gradient-boosting regression | **GitHub repo only — no paper identifier** | FETCHABLE (repo; no paper payload) | repo `LICENSE` = MIT (code, not paper) | index offers no paper link for this row; nothing literature-shaped to fetch
tfm-agents-humans | "…Data Science Requires Tabular Foundation Models, Agents, and Humans" (cong et al. 2025) | direct PDF (CWI repository) | **FETCHABLE** | none stated (full 20-page text scanned) | 200 `application/pdf`, 327 KB
kumo-tabular | NVIDIA Kumo Tabular sets a new accuracy–efficiency frontier | blog (+ GitHub) only | FETCHABLE (blog; no paper payload) | none stated | HuggingFace blog 200; GitHub link not separately probed (loop stopped at the blog)
kumorfm | Kumo Relational Foundation Model (fey et al. 2025) | direct PDF (kumo.ai) | **DEAD** | not reachable | given PDF URL **redirects to `docs.nvidia.com` product-overview HTML** (stub); `kumo.ai/research` does the same. Index offers no second identifier. OpenAlex title search did not surface this exact paper (a related *KumoRFM-2* arXiv entry exists — unverified, not claimed as the same work)
timesfm-3 | TimesFM-3: a zero-shot foundation model for multivariate forecasting | blog only | FETCHABLE (blog) | none stated | Google Research blog 200
era-of-experience | The Era of Experience (silver & sutton) | direct PDF (DeepMind storage) | **FETCHABLE** | none stated (11-page scan) | 200 `application/pdf`, 226 KB
sdi | Semantic-guided data augmentation… (zhou et al. 2027) | DOI (Elsevier, Pattern Recognition) | PAYWALLED (subscription) | no reuse licence (Crossref: Elsevier TDM terms only; OpenAlex: `closed`) | doi.org → `linkinghub` JS "Redirecting" interstitial (no meta refresh to follow); `sciencedirect.com` article URL → **403** for this client
zeroshot-coordination-llm-agents | zero-shot coordination with LLM agents (hayler et al. 2026) | OpenReview forum | PAYWALLED (CAPTCHA) | **not checked** | web `/forum` and `/pdf`, and `api2.openreview.net/notes`, all return "Verifying your browser" / `ChallengeRequiredError` 403
strong-posttraining-pretraining | (no citation in index) | OpenReview forum | PAYWALLED (CAPTCHA) | not checked | same challenge page
ensemble-inference | (no citation in index) | OpenReview forum | PAYWALLED (CAPTCHA) | not checked | same
shapinggeometry | (merchant et al. 2026) | OpenReview forum (+ poster PNG) | PAYWALLED (CAPTCHA) | not checked | poster PNG is not a payload; not probed
tabshallow | (cannistraci & vogt 2026) | OpenReview forum | PAYWALLED (CAPTCHA) | not checked | same
ptnas | pTNAS: progressive neural architecture search for tabular data (xing et al. 2026) | OpenReview pdf + PMLR proceedings | **FETCHABLE (via the PMLR link)** | no CC statement; PMLR landing copyright, "Copyright 2026" in PDF | OpenReview route challenged; PMLR landing 200 → PDF (`raw.githubusercontent.com/mlresearch/v306/…xing26a.pdf`) 200, 32 pp (read truncated at 3 MB)
kamel | KAMEL… (wang et al. 2026) | DOI (Elsevier, Information Sciences) | PAYWALLED (subscription) | none published (Crossref TDM only; OpenAlex `closed`) | same linkinghub/ScienceDirect 403 path as `sdi`
pfnsyn | PFN-Syn: generating synthetic tabular data with PFNs (zuo et al. 2026) | direct PDF (TaDA 2026 workshop site) | **FETCHABLE** | **CC BY-NC-ND 4.0**, stated in the PDF itself | 200 `application/pdf`
qdhgan | (zhou et al. 2026) | DOI (Elsevier, Knowledge-Based Systems) | PAYWALLED (subscription) | none published (OpenAlex `closed`) | as `sdi`
ggpl | efficient piecewise-linear embeddings for deep tabular regression (suh et al. 2026) | DOI (ACM DL, KDD '26) + LG landing | PAYWALLED (CAPTCHA) | Crossref: **CC BY-NC-ND 4.0** (ACM page could not be opened to confirm free full text); LG landing footer: all rights reserved | `dl.acm.org` **403 "Just a moment"** (Cloudflare) with both research and browser UA; LG landing 200 but abstract only, **no PDF link on the page**
agata | AGATa: attention-guided augmentation… (eo et al. 2024) | LG landing + OpenReview | PAYWALLED (CAPTCHA) | LG footer: all rights reserved; OpenReview not checked | LG page 200, abstract only, no PDF link anywhere in the HTML
ratab | representation-space augmentation… (eo et al. 2025) | LG landing only | **UNKNOWN** | all rights reserved (LG footer) | landing 200 but offers no payload; no other identifier in the index to try
bsplinenorm | learnable numerical input normalization… (suh et al. 2024) | LG landing + OpenReview | PAYWALLED (CAPTCHA) | LG: all rights reserved; OpenReview not checked | as `agata`
icl-order | investigating the role of order for in-context learning in tabular FMs | ResearchGate landing only | PAYWALLED (CAPTCHA/login) | not verified; OpenAlex `closed` (DOI 10.13140/rg.2.2.10553.33123) | RG **403** "Temporarily Unavailable" + cookie/JS challenge
tabssldataselect | "Less is more": unlabeled data selection… (stevanoska et al. 2026) | DOI (Springer, Machine Learning) | **FETCHABLE** | **CC BY 4.0** (landing + Crossref) | landing 200; `content/pdf/…07133-8.pdf` 200 `application/pdf`
augtab | AugTab: learnable feature augmentation… | DOI (Springer chapter) | PAYWALLED (subscription) | none published (Crossref TDM terms only; © Springer Nature) | landing 200 with "check access"; `content/pdf` **redirects back to the chapter HTML** — no PDF without access
tabllama | TabLlama… (yeom et al. 2026) | DOI (Elsevier, Neurocomputing) | PAYWALLED (subscription) | none published (OpenAlex `closed`) | as `sdi`
goggle | GOGGLE… (liu et al. 2023) | OpenReview forum (+ iclr.cc virtual page) | PAYWALLED (CAPTCHA) | not checked | the iclr.cc page is an event page, not a payload; not probed
zerorel | (tian et al. 2026) | DOI (ACM DL, KDD '26) | PAYWALLED (CAPTCHA) | Crossref: **CC BY-NC-ND 4.0** (page unopenable from here) | 403 Cloudflare with both UAs
baguan-ts | Baguan-TS… (yang et al. 2026) | OpenReview + PMLR proceedings | **FETCHABLE (via the PMLR link)** | no CC statement; "Copyright 2026" in PDF | PMLR landing 200 → PDF (`mlresearch/v306/…yang26ac.pdf`) 200, 26 pp (read truncated at 3 MB)
mmda | MMDA: masked multi-teacher distillation… | IEEE Xplore landing | PAYWALLED (subscription) | © IEEE, no reuse grant; OpenAlex `closed` (DOI 10.1109/tase.2026.3726963) | abstract page 200; `stamp/stamp.jsp` **redirects to the document page — no PDF** without subscription
twostagefinance | (isufaj et al. 2026) | SSRN landing | PAYWALLED (CAPTCHA) | not checked | 403 Cloudflare "Just a moment" with both UAs; SSRN downloads normally need an account anyway
bitcoinllmforecast | enhancing LLMs for bitcoin time-series forecasting (chaffard et al. 2025) | DOI (Elsevier, Knowledge-Based Systems) | **UNKNOWN** | **CC BY** (OpenAlex: hybrid OA, published version) | doi.org → linkinghub interstitial; `sciencedirect.com` article URL → **403** — bot defence rather than a paywall (OpenAlex says OA), could not confirm from here
exo-zeroshot-tsfm | a universal foundation model for zero-shot TSF with exogenous variables | IEEE Xplore landing | PAYWALLED (subscription) | © IEEE; OpenAlex `closed` (DOI 10.1109/tii.2026.3732176) | as `mmda`
tscausalfm | (thumm et al. 2026) | OpenReview forum | PAYWALLED (CAPTCHA) | not checked | challenge page
causalfewshot | (ossen et al. 2026) | OpenReview forum | PAYWALLED (CAPTCHA) | not checked | challenge page
causalorder | (xu et al. 2026) | OpenReview forum | PAYWALLED (CAPTCHA) | not checked | challenge page
causaltab | (li et al. 2026) | OpenReview forum | PAYWALLED (CAPTCHA) | not checked | challenge page
posttreatmentcfm | (ham et al. 2026) | OpenReview forum | PAYWALLED (CAPTCHA) | not checked | challenge page
stablepfn | (guan et al. 2026) | DOI (ACM DL) | PAYWALLED (CAPTCHA) | Crossref: **CC BY 4.0** (page unopenable from here) | 403 Cloudflare both UAs
orchecause | OrcheCause… (lyu et al. 2026) | LG landing only | **UNKNOWN** | all rights reserved (LG footer) | as `ratab`
cwfm | estimating causal effects from tabular data with assumption gates… (berti 2026) | DOI (MDPI, Electronics) | **UNKNOWN** | **CC BY 4.0** (Crossref version-of-record + OpenAlex `gold`) | `mdpi.com` **403 "Access Denied" with both UAs** — bot defence, not a paywall; OA status known but the PDF never arrived
pf-ges | nonparametric greedy equivalence search with prior-fitted networks (gajewski & olko 2026) | PMLR proceedings landing | **FETCHABLE** | no CC statement; PMLR copyright line | landing 200 → PDF (`mlresearch/v323/…gajewski26a.pdf`) 200, 694 KB
good-bad-controls | a crash course in good and bad controls (cinelli et al. 2022) | direct PDF (UCLA) + DOI (Sage) | **FETCHABLE** | no licence grant in the 30-page PDF; Crossref: SAGE CHORUS notice (not a reuse licence) | 200 `application/pdf`, 1.3 MB
cdc-prompt | prompt used for "a proof of the cycle double cover conjecture" | direct PDF (OpenAI CDN) | **FETCHABLE** | none stated (2 pages) | 200 `application/pdf`
rna-topology-encoding | (franke et al. 2026) | OpenReview pdf | PAYWALLED (CAPTCHA) | not checked | challenge page (challenge also on `/pdf?id=`)
mit-ai-report | report of MIT's ad hoc committee on AI use in teaching, learning, and research | direct PDF (MIT) | **FETCHABLE** | © line only, **no grant** (40-page scan) | 200 `application/pdf`, 2.3 MB
rules-or-exemplars | (balef et al. 2026) | OpenReview forum | PAYWALLED (CAPTCHA) | not checked | challenge page
circuits-framework | a mathematical framework for transformer circuits | web page only | **FETCHABLE (web-native)** | none stated | 200, full HTML paper
monosemanticity | towards monosemanticity… | web page only | **FETCHABLE (web-native)** | none stated | 200. Caveat: the strings "CC BY", "All rights reserved" and "captcha" on this page are **training-data examples inside the embedded model-activity JSON**, not licence or bot-check text — do not read them as licence evidence.
nonergodic-geometry | the geometry of nonergodic composition | web page only | **FETCHABLE (web-native)** | none stated | 200, full HTML paper

## What I could not check, and why

- **OpenReview licences (13 entries).** Every route — web forum, web PDF, and the public
  `api2.openreview.net` API — returns `ChallengeRequiredError`. No licence text was ever served, so
  those rows say `not checked`, not "unknown-but-probably-open".
- **Whether the CAPTCHA-gated routes are free in a browser.** I have no JS execution here, so for
  OpenReview, ACM DL, SSRN and ResearchGate I can say only "blocked to an HTTP client", not
  "money required". Crossref does show declared CC licences for three of the ACM rows
  (zerorel, stablepfn, ggpl), which suggests those are open content behind a bot wall — but I could
  not open the pages to confirm free full text.
- **Elsevier and IEEE full text.** ScienceDirect 403'd on direct article URLs; IEEE's `stamp.jsp`
  hands back the abstract page. Crossref/OpenAlex say `closed` for sdi, kamel, qdhgan, tabllama,
  mmda, exo-zeroshot-tsfm, so the paywall classification rests on the metadata plus the observed
  block, not on a rendered "buy this article" page.
- **LG AI Research payloads.** The five LG landing pages load, carry an "All Rights Reserved"
  footer, and contain no `.pdf` href in the HTML. I did not reverse-engineer their JavaScript to
  look for a download endpoint — so those are UNKNOWN (no payload offered) rather than dead.
- **Alternate arXiv copies of the other 49.** Not systematically searched (~50 more API calls, out
  of scope). Six OpenAlex title spot-checks did not surface the indexed work for the
  OpenReview-only rows; results were unrelated, so the question stays open.
- **Institutional access, cookies, referrers that some publishers expect.** Untested by design —
  no credentials were used anywhere in this audit.
- **Secondary links I deliberately skipped:** videos, `iclr.cc`/`icml.cc` event pages, the
  `shapinggeometry` poster PNG, and the `kumo-tabular` GitHub repo (the blog already answered the
  reachability question for that row).

## Enough to decide #9?

**Yes for the committed-payload question; the local-fetch question is now a cost judgement, not a
knowledge gap.**

- **"arXiv-only is a deliberate line" is supported for what gets committed.** Of the 50, only
  **2 entries are both fetchable here and plainly licensed for redistribution**
  (`tabpfnv2`, `tabssldataselect`, both CC BY 4.0). One more is fetchable but CC BY-NC-ND
  (`pfnsyn` — non-commercial, no derivatives, so extracted text is a derivative: not shareable as
  corpus payload). One more (`gnr`) sits under arXiv's assumed 1991–2003 licence, which is
  arXiv's *distribution* permission, not a public-reuse grant — the repo already treats that class
  as non-redistributable. Everything else that was readable either says nothing (9 entries) or
  says © / all rights reserved (11 entries). **~48 of the 50 could never be shared**, which is the
  licensing argument in `references/README.md` and `PROVENANCE.md` holding up under measurement.
- **"arXiv-only" is *not* supported as a claim about the world.** 18 of 50 are fetchable without
  credentials, 15 of them actual paper content, and one of those (`gnr`) is blocked purely by a
  one-line bug: `ARXIV_RE`/`ARXIV_PDF_RE` only match modern ids, so a legacy `cond-mat/0011094`
  — whose `/src/` answers `application/gzip` — is mislabelled `skipped:no-arxiv-id`. That is a
  defect, not a policy.
- **"fetch-and-gitignore-more" has a hard ceiling of ~15 entries (5% of the 303).** The other 32
  (27 paywalled/challenge-gated + 4 unknown + 1 dead) are unreachable by *any* plain HTTP fetcher
  from here — OpenReview alone is 13 of them, and no amount of fetcher work changes that without
  credentials or a browser-verification bypass, which are out of scope for this repo. So the
  decision is not "how much more can we get" but "is a multi-source fetcher (Nature, Springer,
  PMLR, OpenAI/DeepMind/CWI/UCLA mirrors, plus publisher politeness and dead-link maintenance)
  worth +15 locally-readable entries whose payloads we still may not commit".
- **On sharing specifically:** even a successful fetch-and-gitignore extension would put **2
  entries** into the "safe to commit" column, not 15. Payload sharing and payload *fetching*
  separate cleanly in this data: fetch what you can read locally, keep committing only what a
  licence line supports.

Honest caveat: this audit proves reachability from one non-JS client on 2026-10-29. A row marked
PAYWALLED(CAPTCHA) could be free in a real browser; a row marked UNKNOWN could resolve either way
tomorrow as a publisher changes its bot rules. Nothing here was invented — every row above was
probed, or says `not checked`.
