#!/usr/bin/env python3
"""entry.py — the vocabulary of a corpus entry (#66).

One place decides what an arXiv id is, which revision it names and which year it
belongs to. The corpus builder, the metadata helper, the licence pass and the
year query all ask here, so "this consumer knows the id" stops being a separate
question from "the corpus knows the id".

Stored ids keep their case (`id`) so the manifest's bytes stay put; `key` is the
lowercase form for cache and lookup keys.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Modern `YYMM.NNNNN` and legacy `archive[/subclass]/YYMMNNN`. Case is tolerated
# inside the fragment itself, so a regex that interpolates it needs no `re.I` and
# accepts exactly what `parse()` accepts. Grouped, so interpolation is safe.
ARXIV_ID = r"(?:\d{4}\.\d{4,5}|[A-Za-z][A-Za-z-]*(?:\.[A-Za-z][A-Za-z-]*)?/\d{7})"

_ID_RE = re.compile(rf"^(?P<id>{ARXIV_ID})(?:v(?P<rev>\d+))?$", re.I)


class IdError(ValueError):
    """The string is not an arXiv id this corpus accepts."""


@dataclass(frozen=True)
class ArxivId:
    """A parsed identifier: the stored id, a lookup key, its revision and year."""

    id: str          # versionless, case as published
    key: str         # lowercase, for cache and lookup keys
    revision: int
    year: int | None


def _year(identifier: str) -> int | None:
    """YYMM from either form: `2102.10154` and `cond-mat/0011094` both carry it."""
    tail = identifier.rsplit("/", 1)[-1]
    prefix = tail[:2]
    if not prefix.isdigit():
        return None
    yy = int(prefix)
    return 2000 + yy if yy < 91 else 1900 + yy


def parse(raw: str) -> ArxivId:
    """Parse a modern or legacy id, with or without a version suffix."""
    value = (raw or "").strip()
    match = _ID_RE.match(value)
    if not match:
        raise IdError(f"not an arXiv id: {raw!r}")
    identifier = match.group("id")
    return ArxivId(
        id=identifier,
        key=identifier.lower(),
        revision=int(match.group("rev") or 0),
        year=_year(identifier),
    )


def key(raw: str) -> str:
    """The lowercase lookup key for an id, parsed once."""
    return parse(raw).key
