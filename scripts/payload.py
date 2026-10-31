#!/usr/bin/env python3
"""payload.py — the one answer to "what is in papers/<slug>/?".

Two paths used to answer it differently: the fetch path trusted a `.fetched`
marker alone, while `--index` demanded the marker *and* `text.txt`, so the same
directory could read as fetched on one path and absent on the other (#63). This
module reads the directory once; `ready` is the single rule both paths use.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MARKER = ".fetched"
TEXT = "text.txt"
KINDS = ("tex", "pdf", "html", "xml")
DEFAULT_KIND = "tex"


@dataclass(frozen=True)
class Payload:
    """What `papers/<slug>/` holds, read once."""

    slug: str
    directory: Path
    marker: bool
    kind: str
    sha256: str
    rev: int
    has_text: bool
    text_bytes: int

    @property
    def ready(self) -> bool:
        """Fetched and usable: a non-empty marker plus readable text.

        An empty or truncated marker is not credited: its provenance is unknown,
        so the entry is refetched rather than trusted.
        """
        return self.marker and self.has_text

    @property
    def source(self) -> str:
        """The extraction kind the marker names, normalised to a known one."""
        return self.kind if self.kind in KINDS else DEFAULT_KIND


def read(papers_root: str | Path, slug: str) -> Payload:
    directory = Path(papers_root) / slug
    marker_file = directory / MARKER
    fields = marker_file.read_text(encoding="utf-8").split() if marker_file.is_file() else []
    kind = fields[0] if fields else ""
    sha256 = fields[1] if len(fields) > 1 else ""
    rev = 0
    if len(fields) > 2 and fields[2][:1] == "v" and fields[2][1:].isdigit():
        rev = int(fields[2][1:])
    text = directory / TEXT
    has_text = text.is_file()
    return Payload(
        slug=slug,
        directory=directory,
        marker=bool(fields),
        kind=kind,
        sha256=sha256,
        rev=rev,
        has_text=has_text,
        text_bytes=text.stat().st_size if has_text else 0,
    )


def marker_body(kind: str, sha256: str, rev: int = 0) -> str:
    """The marker's contents: kind, digest, and `vN` when the revision is pinned."""
    return f"{kind}\n{sha256}\n" + (f"v{rev}\n" if rev else "")


def write_marker(directory: str | Path, kind: str, sha256: str, rev: int = 0) -> None:
    (Path(directory) / MARKER).write_text(marker_body(kind, sha256, rev), encoding="utf-8")
