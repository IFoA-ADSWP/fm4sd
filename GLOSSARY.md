# Glossary

Vocabulary about the corpus, fixed here so "the corpus" cannot mean three things at once.
Figures and their derivation live in [PROVENANCE.md](PROVENANCE.md); this page defines words,
not numbers.

## entry

One line of the reading index: a single paper, with its title, citation, category and the
links it offers. An entry exists whether or not any content was ever fetched — an entry is a
row in the list, not a file.

## index

The curated reading list: `README.md` (upstream's list preserved, plus the local actuarial
block). It is committed and holds no paper content. Its machine-readable projection is the
manifest, `references/manifest.json` — the same index in another form, not a third thing.

## payload

The fetched paper content itself: `papers/<slug>/text.txt` and the source bundle or PDF it
was extracted from. Payload is gitignored and local, so its size and contents depend on what
a given clone has fetched. Committed manifest data is not payload.

## "the corpus"

Ambiguous, and avoided where a claim depends on it. It has been used for the index (the
list), the manifest (the projection) and the payload (the files). Say which: an entry count
is about the index; a fetch status is about one entry's payload; a byte total is about
payload on one machine. A sentence about "the corpus" that would be true on one clone and
false on another is a payload claim.

## route

The path from an entry's link to payload. The fetcher knows a small set of route families:
arXiv source with arXiv PDF as fallback, direct PDF, publisher PDF with a PMC mirror as
fallback, PMLR proceedings, NeurIPS proceedings, and web-native HTML. A route family is a
kind of path, not a publisher: PMLR and NeurIPS are families because of how their proceedings
serve PDFs. A paper is out of scope when no route serves it to a plain HTTP client, not when
it is unimportant — unreachable is a property of the route, not of the paper.

## shareable

A per-entry permission judgement, recorded as `yes`, `no` or `unknown`. `yes` means the
stated licence plainly allows republishing the extracted text; `no` means it does not (all
rights reserved, a non-derivative licence, or no grant at all); `unknown` means no licence
could be established. Unknown is never permission — only `yes` is published. Shareable is
independent of route: a paper can be fetchable and not shareable, and open access does not
imply it.

## status

What happened when the fetcher last tried an entry. There are three kinds:

- **fetched** — `ok` (retrieved in that run) or `cached` (payload already on disk and not
  re-fetched). The payload exists.
- **skipped** — no payload, and the reason is in the status:
  `skipped:unreachable:<captcha|paywall|dead|unknown>` when no plain-HTTP route served the
  paper, or `skipped:not-paper` when the link is a code repository or blog post.
- **error** — `src-error:<kind>` or `pdf-error:<kind>`: a route was attempted and the
  transfer or extraction failed. The entry is neither fetched nor deliberately out of scope.

`skipped:no-arxiv-id` is retired: it named an identifier an entry lacked rather than why it
was skipped, and so read as a scope decision when it was not one. Status is about an entry's
payload, not about the entry's existence or the index's contents.
