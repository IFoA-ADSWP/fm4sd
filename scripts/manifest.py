#!/usr/bin/env python3
"""manifest.py — the one definition of the manifest file format.

`references/manifest.json` is a header object, a delimiter line, then the entries
array. Every reader and writer goes through this module so the format, the
delimiter and the malformed-input rule live in one place (#63).

Callers keep their own user-facing wording: catch `ManifestError` and translate.
"""

from __future__ import annotations

import json
from pathlib import Path

DELIM = "\n--- entries ---\n"
NOTE = "Parsed from the fm4sd README. Payload lives in gitignored papers/."


class ManifestError(Exception):
    """The file is missing, malformed, or not shaped like a manifest."""


def read(path: str | Path) -> tuple[dict, list[dict], str]:
    """Return (header, entries, raw_text). Raises ManifestError."""
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ManifestError(f"{path}: cannot read ({error})") from error
    if DELIM not in raw:
        raise ManifestError(f"{path}: no {DELIM.strip()!r} line")
    head, body = raw.split(DELIM, 1)
    try:
        header = json.loads(head)
        entries = json.loads(body)
    except json.JSONDecodeError as error:
        raise ManifestError(f"{path}: not valid JSON ({error})") from error
    if not isinstance(header, dict):
        raise ManifestError(f"{path}: header is not an object")
    if not isinstance(entries, list):
        raise ManifestError(f"{path}: entries section is not a list")
    return header, entries, raw


def by_slug(entries: list[dict]) -> dict[str, dict]:
    """Index entries by slug, ignoring rows without one."""
    return {
        entry["slug"]: entry
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("slug"), str)
    }


def build_header(source: str, count: int) -> dict:
    return {"source": source, "note": NOTE, "count": count}


def render(header: dict, entries: list[dict]) -> str:
    return f"{json.dumps(header, indent=2)}{DELIM}{json.dumps(entries, indent=2)}\n"


def write(path: str | Path, entries: list[dict]) -> None:
    """Rewrite the entries, keeping the file's existing header byte for byte."""
    path = Path(path)
    _, _, raw = read(path)
    head = raw.split(DELIM, 1)[0]
    path.write_text(f"{head}{DELIM}{json.dumps(entries, indent=2)}\n", encoding="utf-8")
