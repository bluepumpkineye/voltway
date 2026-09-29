"""Is this error, or this render symptom, a failure we have already solved?

    triage(traceback_text)            -> {"id", "p", "confidence", "fix", ...}
    with guard("building rx_rear"):   # inside Blender: annotate and re-raise
        build_rx.parts(["rx_rear"])

One call: a Choice over the known failures (plus "unknown") ranks them, and
Nouls re-check them against their descriptions. The fix is reported
only when both agree (gate below), otherwise the result says "unknown" and the
error is handled the usual way. Only the last lines of a traceback are sent.
"""
import contextlib
import traceback

from . import client as J
from .known_failures import FAILURES, UNKNOWN

GATE_P = 0.60        # Noul re-check
GATE_CONF = 0.35     # Choice confidence
TENTATIVE_P, TENTATIVE_CONF = 0.40, 0.75
TAIL_LINES = 40


def _tail(text, n=TAIL_LINES):
    lines = [l for l in str(text).splitlines() if l.strip()]
    return "\n".join(lines[-n:])


def triage(text, doing=None):
    state = {"error_or_symptom": _tail(text)}
    if doing:
        state["what_was_being_done"] = doing
    opts = {k: v["looks_like"] for k, v in FAILURES.items()}
    opts[UNKNOWN] = "None of the known failures matches."
    qs = {"which": J.choice(
        "Which known failure is `error_or_symptom` an instance of? Match on the error "
        "message and the situation, not on shared words.", opts)}
    # Speculative fan-out: an absolute Noul for every failure in the same call
    # (a few thousand tokens), so the winner's re-check costs no second trip.
    for k, v in FAILURES.items():
        qs["is_" + k] = J.noul({
            "known_failure": {"looks_like": v["looks_like"], "cause": v["cause"]},
            "question": "Is `error_or_symptom` an instance of `known_failure`?"})
    r = J.ask(state, qs, tag="triage")
    a = r["answers"]["which"]
    top = a["choice"]
    ranked = sorted(((k, a["probabilities"].get(k, 0.0), r["answers"]["is_" + k]["noul"])
                     for k in FAILURES), key=lambda t: -(t[1] + t[2]))
    out = {"id": UNKNOWN, "choice": top, "confidence": round(a["confidence"], 3),
           "ranked": [(k, round(pc, 3), round(pn, 3)) for k, pc, pn in ranked[:3]],
           "ms": round(r["ms"])}
    if top != UNKNOWN:
        pn = r["answers"]["is_" + top]["noul"]
        out["p"] = round(pn, 3)
        if pn >= GATE_P and a["confidence"] >= GATE_CONF:
            out.update(id=top, cause=FAILURES[top]["cause"], fix=FAILURES[top]["fix"])
        elif pn >= TENTATIVE_P and a["confidence"] >= TENTATIVE_CONF:
            # e.g. a bare KeyError: the choice is sure, the re-check is not
            out.update(id=top, tentative=True, cause=FAILURES[top]["cause"],
                       fix=FAILURES[top]["fix"])
    return out


def hint(text, doing=None):
    """A one-paragraph hint for a log, or '' when nothing known matches (or
    Jev is not configured / unreachable: triage must never break a build)."""
    if not J.available():
        return ""
    try:
        t = triage(text, doing)
    except J.JevError:
        return ""
    if t["id"] == UNKNOWN:
        return ""
    return "[jev triage] %s known failure '%s' (p=%.2f): %s Fix: %s" % (
        "possibly the" if t.get("tentative") else "the", t["id"], t.get("p", 0.0),
        t["cause"], t["fix"])


class Hinted(RuntimeError):
    """An exception re-raised with the known fix in its message (the Blender
    MCP reports only the message, so a printed hint would be lost)."""


@contextlib.contextmanager
def guard(doing=None):
    """On an exception matching a known failure, re-raise it as Hinted with
    the cause and fix appended (the original is chained as __cause__); any
    other exception passes through unchanged."""
    try:
        yield
    except Exception as e:
        h = hint(traceback.format_exc(), doing)
        if not h:
            raise
        print(h)
        raise Hinted("%s: %s\n%s" % (type(e).__name__, e, h)) from e
