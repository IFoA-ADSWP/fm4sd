#!/usr/bin/env python3
"""net.py — one HTTP client for this repo (#73).

Policy lives here; the *pace* and the *transport* are adapters the caller
supplies. Production passes the default urllib transport and a rate limiter;
a scratch run passes a fake transport and a recording pace, so retries and
spacing are assertable without a socket.

Defaults: three attempts; 404 is final; every other HTTP status is retryable;
`Retry-After` is honoured as delay-seconds or as an HTTP date; otherwise the
delay is exponential (1s, 2s, …); the last attempt does not sleep; success is
silent and each retry logs one line.

    data = http.get(url, pace=limiter)
    data = http.get(url, retry_statuses=(429, 503), pace=limiter)
"""

from __future__ import annotations

import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Callable, Protocol

USER_AGENT = "fm4sd-corpus/1.0 (research; https://github.com/IFoA-ADSWP/fm4sd)"
TIMEOUT = 60.0
RETRIES = 3
FINAL_STATUSES = (404,)
RETRY_STATUSES: tuple[int, ...] | None = None  # None = every non-final status
MAX_DELAY = 60.0


class HttpError(RuntimeError):
    """A request that did not produce bytes, after the policy's attempts."""

    def __init__(self, url: str, message: str, status: int | None = None) -> None:
        self.url = url
        self.status = status
        super().__init__(f"{url}: {message}")


class Pace(Protocol):
    """Anything that can space requests: the module calls `wait()` per attempt."""

    def wait(self) -> None: ...


class NoPace:
    """The null pace: useful for a single-shot client or a test."""

    def wait(self) -> None:
        return None


def transport(url: str, user_agent: str, timeout: float) -> bytes:
    """The production transport: one urllib GET with the caller's user agent."""
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def retry_after(value: str | None) -> float | None:
    """Seconds from a Retry-After header: delay-seconds or an HTTP date."""
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return max(0.0, (when - datetime.now(timezone.utc)).total_seconds())


def _log(message: str) -> None:
    print(f"http: {message}", file=sys.stderr)


def get(
    url: str,
    *,
    transport: Callable[[str, str, float], bytes] = transport,
    pace: Pace | None = None,
    retries: int = RETRIES,
    final_statuses: tuple[int, ...] = FINAL_STATUSES,
    retry_statuses: tuple[int, ...] | None = RETRY_STATUSES,
    user_agent: str = USER_AGENT,
    timeout: float = TIMEOUT,
    sleep: Callable[[float], None] = time.sleep,
    log: Callable[[str], None] | None = None,
) -> bytes:
    """GET `url`, retrying by the policy above. Raises HttpError when it gives up."""
    log = log or _log
    last: Exception | None = None
    status: int | None = None
    for attempt in range(retries):
        if pace is not None:
            pace.wait()
        try:
            return transport(url, user_agent, timeout)
        except urllib.error.HTTPError as error:
            status = error.code
            last = error
            if error.code in final_statuses:
                raise HttpError(url, f"final status {error.code}", error.code) from error
            if retry_statuses is not None and error.code not in retry_statuses:
                raise HttpError(url, f"status {error.code}", error.code) from error
            wait = retry_after(error.headers.get("Retry-After") if error.headers else None)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            last = error
            wait = None
        if attempt == retries - 1:
            break
        delay = wait if wait is not None else min(MAX_DELAY, 2.0 ** attempt)
        log(f"retrying {url} in {delay:.0f}s (attempt {attempt + 1}/{retries}): {last}")
        sleep(delay)
    raise HttpError(url, f"gave up after {retries} attempts: {last}", status)
