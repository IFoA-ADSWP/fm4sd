#!/usr/bin/env python3
"""net.py — one HTTP client for this repo (#73).

Policy lives here; the *pace* and the *transport* are adapters the caller
supplies. Production passes the default urllib transport and a rate limiter;
a scratch run passes a fake transport and a recording pace, so retries and
spacing are assertable without a socket.

Defaults: three attempts; **408, 429 and every 5xx are retryable**; every other
status is final, including 400/401/403/404/410 — the repo already classifies
403 as a challenge and 404/410 as dead, so retrying them is wasted politeness.
`Retry-After` is honoured as delay-seconds or as an HTTP date; otherwise the
delay is exponential (1s, 2s, …); the last attempt does not sleep; success is
silent and each retry logs one line.

    data = net.get(url, pace=limiter)
    data = net.get(url, retry_on=lambda code: code != 404)   # fetch's old policy
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
ATTEMPTS = 3
MAX_DELAY = 60.0
RETRYABLE = frozenset({408, 429}) | frozenset(range(500, 600))


class HttpError(RuntimeError):
    """A request that did not produce bytes, after the policy's attempts."""

    def __init__(self, url: str, message: str, status: int | None = None) -> None:
        self.url = url
        self.status = status
        super().__init__(f"{url}: {message}")


class Pace(Protocol):
    """Anything that can space requests: the module calls `wait()` per attempt."""

    def wait(self) -> None: ...


def transport(url: str, user_agent: str, timeout: float) -> bytes:
    """The production transport: one urllib GET with the caller's user agent."""
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def retryable(status: int) -> bool:
    """The default policy: transient statuses retry, the rest are answers."""
    return status in RETRYABLE


def retry_after(value: str | None) -> float | None:
    """Seconds from a Retry-After header, or None when there is no usable delay.

    A date already in the past yields None rather than 0: an instant retry is
    worse than falling back to the exponential delay.
    """
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        seconds = float(value)
        return seconds if seconds > 0 else None
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    seconds = (when - datetime.now(timezone.utc)).total_seconds()
    return seconds if seconds > 0 else None


def _log(message: str) -> None:
    print(f"net: {message}", file=sys.stderr)


def get(
    url: str,
    *,
    transport: Callable[[str, str, float], bytes] = transport,
    pace: Pace | None = None,
    attempts: int = ATTEMPTS,
    retry_on: Callable[[int], bool] = retryable,
    user_agent: str = USER_AGENT,
    timeout: float = TIMEOUT,
    sleep: Callable[[float], None] = time.sleep,
    log: Callable[[str], None] | None = None,
) -> bytes:
    """GET `url` under the policy above. Raises HttpError when it gives up."""
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    log = log or _log
    last: Exception | None = None
    last_status: int | None = None
    for attempt in range(attempts):
        status: int | None = None
        if pace is not None:
            pace.wait()
        try:
            return transport(url, user_agent, timeout)
        except urllib.error.HTTPError as error:
            status = last_status = error.code
            last = error
            if not retry_on(error.code):
                raise HttpError(url, f"status {error.code}", error.code) from error
            wait = retry_after(error.headers.get("Retry-After") if error.headers else None)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            last = error
            last_status = None
            wait = None
        if attempt == attempts - 1:
            break
        delay = wait if wait is not None else min(MAX_DELAY, 2.0 ** attempt)
        log(f"retrying {url} in {delay:.0f}s (attempt {attempt + 1}/{attempts}): {last}")
        sleep(delay)
    raise HttpError(url, f"gave up after {attempts} attempts: {last}",
                    last_status) from last
