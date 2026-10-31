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


# ---------------------------------------------------------------------------
# Status: one vocabulary for what an entry's fetch state is (#67).
# ---------------------------------------------------------------------------

FETCHED = ("ok", "cached")
ABSENCE_REASONS = frozenset({"not-paper", "captcha", "paywall", "dead", "unknown"})
_PENDING = "pending"


class StatusError(ValueError):
    """The value is not a status this corpus stores."""


@dataclass(frozen=True)
class Status:
    """A stored status value, plus the questions consumers actually ask."""

    value: str

    @property
    def is_fetched(self) -> bool:
        return self.value in FETCHED

    @property
    def reason(self) -> str | None:
        """Why the entry is absent, or None when it is fetched or unclassified."""
        if self.value == "skipped:not-paper":
            return "not-paper"
        if self.value.startswith("skipped:unreachable:"):
            return self.value.split(":", 2)[2]
        if "-error:" in self.value:
            return "error"
        return None

    @property
    def recognised(self) -> bool:
        """False for a value no constructor here could have produced."""
        if self.value in FETCHED or self.value in ("", _PENDING):
            return True
        if self.value == "skipped:not-paper":
            return True
        if self.value.startswith("skipped:unreachable:"):
            return self.value.split(":", 2)[2] in ABSENCE_REASONS
        return "-error:" in self.value


def fetched() -> Status:
    return Status("ok")


def cached() -> Status:
    return Status("cached")


def absent(reason: str) -> Status:
    """An entry recorded as absent. The reason vocabulary is closed."""
    if reason not in ABSENCE_REASONS:
        raise StatusError(f"unknown absence reason: {reason!r}")
    if reason == "not-paper":
        return Status("skipped:not-paper")
    return Status(f"skipped:unreachable:{reason}")


def failed(stage: str, kind: str) -> Status:
    """A transport/extraction failure, recorded the way the fetcher always has."""
    return Status(f"{stage}-error:{kind}")


def pending() -> Status:
    return Status(_PENDING)


def status(value: str | None) -> Status:
    """A stored status, without judging whether it is current.

    Named `status`, not `parse`: `parse()` already means "parse an id", and one
    module with two `parse`s silently shadowed the id parser (#67).
    """
    return Status(value or "")


def is_fresh(value: str | None) -> bool:
    """True for `ok` specifically — fetched in this run, not merely cached."""
    return status(value).value == "ok"


def is_fetched(value: str | None) -> bool:
    return status(value).is_fetched


def reason(value: str | None) -> str | None:
    return status(value).reason


def is_absent(value: str | None) -> bool:
    """True when the entry carries one of the absence reasons (not an error)."""
    return reason(value) in ABSENCE_REASONS


def is_unreachable(value: str | None) -> bool:
    why = reason(value)
    return why is not None and why != "not-paper" and why != "error"
