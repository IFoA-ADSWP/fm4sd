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
- defaults: 3 attempts; 408, 429 and every 5xx retryable; every other status final
  (400/401/403/404/410 included — the repo already treats 403 as a challenge, 404/410 as dead);
  `Retry-After` honoured (delay-seconds or HTTP date, a past date falls back to backoff);
  exponential backoff otherwise; no sleep after the last attempt; one log line per retry

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

## The command that proves it

    python3 - <<'PY'
    import sys, urllib.error
    from email.message import Message
    sys.path.insert(0, "scripts"); import net

    def err(code, retry_after=None):
        h = Message()
        if retry_after: h["Retry-After"] = retry_after
        return urllib.error.HTTPError("u", code, "x", h, None)

    def attempts(code, **kw):
        n = [0]
        def t(url, ua, timeout):
            n[0] += 1; raise err(code)
        try: net.get("u", transport=t, sleep=lambda s: None, log=lambda m: None, **kw)
        except net.HttpError as e: return n[0], e.status, e.__cause__ is not None

    for code in (400, 401, 403, 404, 410):
        assert attempts(code)[0] == 1, code
    for code in (408, 429, 500, 502, 503, 504):
        assert attempts(code)[0] == 3, code

    def seq(seq):
        sleeps, waits = [], [0]
        def pace(): waits[0] += 1
        class P: wait = staticmethod(pace)
        def t(url, ua, timeout):
            x = seq.pop(0)
            if isinstance(x, Exception): raise x
            return x
        out = net.get("u", transport=t, pace=P, sleep=sleeps.append, log=lambda m: None)
        return out, waits[0], sleeps

    assert seq([b"ok"]) == (b"ok", 1, [])
    assert seq([err(429, "2"), b"ok"])[2] == [2.0]
    assert seq([err(503), b"ok"])[2] == [1.0]
    assert seq([TimeoutError(), b"ok"])[2] == [1.0]
    assert attempts(403, retry_on=lambda c: c != 404)[0] == 3   # fetch's old policy
    assert net.retry_after("Wed, 21 Oct 2015 07:28:00 GMT") is None
    try: net.get("u", attempts=0)
    except ValueError: pass
    print("all policy cases pass")
    PY
