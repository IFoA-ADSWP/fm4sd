# Plan — one HTTP client (2026-10-31)

Ticket #73 (T1 of spec #72). Three clients to the same host with three retry loops and three
paces; none accepts a transport, so retry and pacing can only be exercised with a socket.

## What

`scripts/net.py`, no caller changed:

The file is not called `http.py`: that name shadows the stdlib `http` package that `urllib`
imports, and every script here puts `scripts/` first on `sys.path`. A name that breaks the
standard library is not a style question.

- `get(url, *, transport, pace, retries, final_statuses, retry_statuses, user_agent, timeout,
  sleep, log)` — the policy in one place
- default transport: urllib with the repo User-Agent; anything callable substitutes
- pace: anything with `wait()`, called once per attempt; the module owns no rate
- `HttpError` carrying the URL and status
- defaults: 3 attempts, 404 final, every other status retryable, `Retry-After` honoured
  (delay-seconds or HTTP date), exponential backoff otherwise, no sleep after the last attempt,
  one log line per retry

## Why

One implementation is the only way "be a polite client" becomes checkable. The adapters are what
make a retry decision testable without a socket; the repo has two such adapters (urllib, fake),
so the seam is real rather than hypothetical.

## Verification

A scratch command injects a fake transport and a recording pace:
- 200 first try → one attempt, one `wait()`, no sleep
- 429 with `Retry-After: 2`, then 200 → sleeps exactly 2 s, two attempts
- 503 then 200 → exponential delay (1 s)
- 404 → one attempt, `HttpError(status=404)`
- timeout → retried, then 200
- exhausted retries → one `HttpError` naming the URL; no sleep after the final attempt

Plus: gate 3/3, no caller changed, `--index` byte-identical.

## Out of scope

Migrating the three clients (T2, T3); the gate's subprocess seam (#6); new dependencies.
