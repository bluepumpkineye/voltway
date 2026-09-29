"""A small client for Jev (TypeSafe's System One model), standard library only.

It runs unchanged in Blender's bundled Python and in the system Python, so the
same decision code serves the Blender build and the agent's shell tools.

    from carkit.jev import client as J
    r = J.ask({"error": tb}, {"kind": J.choice("Which known failure is this?", {...})})
    r["answers"]["kind"]["choice"], r["answers"]["kind"]["confidence"]

The API key comes from, in order: the TYPESAFE_API_KEY environment variable,
the file named by JEV_ENV_FILE, the repo's .env, then the sibling Jev folder's
.env (../Jev/.env next to the repo). The key is never logged or printed.

Every call is appended to blender/jev_log/calls.jsonl (question ids, answers,
latency, tokens; not the state unless asked) so thresholds can be tuned on
real traffic later.
"""
import concurrent.futures
import hashlib
import json
import os
import time
import urllib.error
import urllib.request

BASE_URL = os.environ.get("TYPESAFE_BASE_URL", "https://api.typesafe.ai").rstrip("/")
MODEL = os.environ.get("TYPESAFE_DEFAULT_MODEL", "jev-latest")
TIMEOUT = 20.0
RETRIES = 2
RETRY_STATUS = {408, 429} | set(range(500, 600))

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(_HERE, "..", "..", "..", ".."))
LOG = os.path.join(REPO, "blender", "jev_log", "calls.jsonl")
# Jev 1.13: 64k tokens per request, 32k for the state plus the longest question.
BUDGET_TOTAL = 60000
BUDGET_STATE_PLUS_Q = 30000

_KEY = None


class JevError(RuntimeError):
    pass


# ---------------------------------------------------------------- questions

def noul(instructions, true=None, false=None):
    """A yes/no question; the answer is the probability of yes."""
    q = {"type": "noul", "instructions": instructions}
    if true is not None or false is not None:
        q["criteria"] = {k: v for k, v in (("true", true), ("false", false)) if v is not None}
    return q


def choice(instructions, options):
    """Pick one of `options` (label -> description or None, at most 255)."""
    if not isinstance(options, dict):
        raise JevError("choice options must be a dict of label -> description")
    if not 2 <= len(options) <= 255:
        raise JevError("choice needs 2..255 options, got %d" % len(options))
    return {"type": "choice", "instructions": instructions, "criteria": options}


def score(instructions, levels):
    """Rate against an ordered rubric (2..10 level descriptions, low to high)."""
    if not isinstance(levels, (list, tuple)) or not 2 <= len(levels) <= 10:
        raise JevError("score needs a list of 2..10 levels")
    return {"type": "score", "instructions": instructions, "criteria": list(levels)}


# ---------------------------------------------------------------- key

def _read_env_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("TYPESAFE_API_KEY="):
                    v = line.split("=", 1)[1].strip().strip('"').strip("'")
                    return v or None
    except OSError:
        return None
    return None


def api_key():
    global _KEY
    if _KEY:
        return _KEY
    k = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if not k:
        for p in (os.environ.get("JEV_ENV_FILE"),
                  os.path.join(REPO, ".env"),
                  os.path.join(os.path.dirname(REPO), "Jev", ".env")):
            if p and (k := _read_env_file(p)):
                break
    if not k:
        raise JevError("No Jev API key: set TYPESAFE_API_KEY or put it in ../Jev/.env")
    _KEY = k
    return k


def available():
    """True when a key can be found (the decision layer is optional: callers
    fall back to their default behaviour when Jev is not configured)."""
    try:
        api_key()
        return True
    except JevError:
        return False


# ---------------------------------------------------------------- calls

def est_tokens(obj):
    """Rough token estimate (4 characters a token) for budgeting requests."""
    s = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False)
    return len(s) // 4 + 1


def _post(path, body, timeout):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    last = None
    for attempt in range(RETRIES + 1):
        req = urllib.request.Request(BASE_URL + path, data=data, method="POST", headers={
            "Authorization": "Bearer " + api_key(),
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "carkit-jev/1.0",
        })
        if attempt:
            req.add_header("X-TypeSafe-Retry-Count", str(attempt))
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:400]
            last = JevError("Jev HTTP %d: %s" % (e.code, detail))
            if e.code not in RETRY_STATUS or attempt == RETRIES:
                raise last from None
            wait = e.headers.get("retry-after")
            time.sleep(min(float(wait), 20.0) if wait and wait.replace(".", "").isdigit()
                       else 0.5 * 2 ** attempt)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = JevError("Jev connection error: %s" % e)
            if attempt == RETRIES:
                raise last from None
            time.sleep(0.5 * 2 ** attempt)
    raise last


def _log(tag, state, questions, result, ms, log_state):
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        s = json.dumps(state, ensure_ascii=False, sort_keys=True)
        rec = {
            "t": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "tag": tag,
            "model": result.get("model"),
            "ms": round(ms),
            "usage": result.get("usage"),
            "state_sha": hashlib.sha1(s.encode("utf-8")).hexdigest()[:12],
            "state_chars": len(s),
            "answers": {k: {kk: vv for kk, vv in a.items() if kk != "legend"}
                        for k, a in result.get("answers", {}).items()},
        }
        if log_state:
            rec["state"] = state
            rec["questions"] = questions
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


def ask(state, questions, model=None, tag="", timeout=TIMEOUT, log_state=False):
    """One System One call: every question is answered against `state`.

    Returns the response dict ({"model", "answers", "usage"}) plus "ms".
    Questions over the request budget are split across parallel calls and
    the answers merged, so callers can fan out freely."""
    if not questions:
        raise JevError("at least one question is required")
    s_tok = est_tokens(state)
    groups, cur, cur_tok = [], {}, s_tok
    for qid, q in questions.items():
        q_tok = est_tokens(q)
        if s_tok + q_tok > BUDGET_STATE_PLUS_Q:
            raise JevError("state + question %r is ~%d tokens (limit ~32k)" % (qid, s_tok + q_tok))
        if cur and cur_tok + q_tok > BUDGET_TOTAL:
            groups.append(cur)
            cur, cur_tok = {}, s_tok
        cur[qid] = q
        cur_tok += q_tok
    groups.append(cur)

    def one(qs):
        t0 = time.perf_counter()
        r = _post("/v1/systemone", {"state": state, "questions": qs,
                                    "model": model or MODEL}, timeout)
        ms = (time.perf_counter() - t0) * 1000.0
        _log(tag, state, qs, r, ms, log_state)
        r["ms"] = ms
        return r

    if len(groups) == 1:
        return one(groups[0])
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(groups))) as ex:
        parts = list(ex.map(one, groups))
    out = {"model": parts[0].get("model"), "answers": {}, "ms": max(p["ms"] for p in parts),
           "usage": {"input_tokens": sum(p.get("usage", {}).get("input_tokens", 0) for p in parts),
                     "output_tokens": sum(p.get("usage", {}).get("output_tokens", 0) for p in parts)}}
    for p in parts:
        out["answers"].update(p["answers"])
    return out


def ask_many(jobs, max_workers=8):
    """Run several independent ask() calls in parallel.
    `jobs` is a list of dicts of ask() keyword arguments."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        return list(ex.map(lambda kw: ask(**kw), jobs))


def ping():
    r = ask("The sky is blue.", {"ok": noul("Does the text say the sky is blue?")}, tag="ping")
    return {"model": r["model"], "ms": round(r["ms"]), "noul": r["answers"]["ok"]["noul"]}
