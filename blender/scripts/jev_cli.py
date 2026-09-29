"""The pipeline's decision layer from the shell (system Python, no Blender).

    python blender/scripts/jev_cli.py ping
    python blender/scripts/jev_cli.py find "wrap a lamp round a curved body corner"
    python blender/scripts/jev_cli.py triage error.txt          (or pipe a traceback in)
    python blender/scripts/jev_cli.py review rx notes.txt       (one note per line)
    python blender/scripts/jev_cli.py onboard spec.txt --car "Luxeed RX" --parts
    python blender/scripts/jev_cli.py log                       (calls, latency, cost)

Add --json for the raw result. See carkit/jev/__init__.py and
docs/3d-pipeline.md, "Decision layer (Jev)".
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

from carkit.jev import client as J  # noqa: E402

PRICE_PER_MTOK = 0.042


def _read(path):
    if not path or path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as f:
        return f.read()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ping")
    f = sub.add_parser("find")
    f.add_argument("need")
    f.add_argument("--scope", default="carkit,cars,doc")
    f.add_argument("-k", type=int, default=6)
    t = sub.add_parser("triage")
    t.add_argument("file", nargs="?", default="-")
    t.add_argument("--doing")
    r = sub.add_parser("review")
    r.add_argument("car")
    r.add_argument("file", nargs="?", default="-")
    r.add_argument("--name")
    o = sub.add_parser("onboard")
    o.add_argument("file")
    o.add_argument("--car")
    o.add_argument("--parts", action="store_true")
    o.add_argument("--out")
    lg = sub.add_parser("log")
    lg.add_argument("n", nargs="?", type=int, default=0)
    a = ap.parse_args(argv)

    if a.cmd == "ping":
        res = J.ping()
        print(json.dumps(res) if a.json else "%(model)s  %(ms)d ms  noul=%(noul).2f" % res)
    elif a.cmd == "find":
        from carkit.jev import finder
        res = finder.find(a.need, scopes=tuple(a.scope.split(",")), keep=max(a.k, 6))[:a.k]
        if a.json:
            print(json.dumps(res, indent=1, ensure_ascii=False))
        else:
            for h in res:
                print("%.2f  %-48s %s:%d" % (h["p"], h["id"], h["file"].replace(os.sep, "/"), h["line"]))
                print("      %s" % h["short"][:150])
    elif a.cmd == "triage":
        from carkit.jev import triage
        res = triage.triage(_read(a.file), a.doing)
        if a.json:
            print(json.dumps(res, indent=1))
        elif res["id"] == "unknown":
            print("unknown (closest: %s)" % ", ".join("%s %.2f/%.2f" % x for x in res["ranked"]))
        else:
            print("%s%s  p=%.2f conf=%.2f\ncause: %s\nfix:   %s" % (
                res["id"], " (tentative)" if res.get("tentative") else "", res["p"],
                res["confidence"], res["cause"], res["fix"]))
    elif a.cmd == "review":
        from carkit.jev import review
        notes = [l.strip(" -*\t") for l in _read(a.file).splitlines() if l.strip()]
        items = review.route(a.car, notes, a.name)
        print(json.dumps(items, indent=1, ensure_ascii=False) if a.json else review.plan_text(items))
    elif a.cmd == "onboard":
        from carkit.jev import onboard
        m = onboard.manifest(_read(a.file), car=a.car, with_parts=a.parts)
        text = json.dumps(m, indent=1, ensure_ascii=False) if a.json else onboard.checklist(m)
        if a.out:
            with open(a.out, "w", encoding="utf-8") as fh:
                fh.write(text)
        print(text)
    elif a.cmd == "log":
        recs = []
        if os.path.exists(J.LOG):
            with open(J.LOG, encoding="utf-8") as fh:
                recs = [json.loads(l) for l in fh if l.strip()]
        recs = recs[-a.n:] if a.n else recs
        by = {}
        for rec in recs:
            by.setdefault(rec["tag"].split(".")[0] or "-", []).append(rec)
        tok_all = 0
        for tag, rs in sorted(by.items()):
            tok = sum((x.get("usage") or {}).get("input_tokens", 0) for x in rs)
            tok_all += tok
            ms = sorted(x["ms"] for x in rs)
            print("%-9s %4d calls  median %4d ms  %8d in-tokens  $%.4f" % (
                tag, len(rs), ms[len(ms) // 2], tok, tok * PRICE_PER_MTOK / 1e6))
        print("total     %4d calls  %8d in-tokens  $%.4f" % (len(recs), tok_all,
                                                            tok_all * PRICE_PER_MTOK / 1e6))


if __name__ == "__main__":
    main()
