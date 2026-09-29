"""Find the reusable part for a need: carkit's API, the cars' own builders and
the pipeline manual's sections, ranked by Jev.

    find("wrap a lamp round a curved body corner")
    -> [("carkit.place.Placer.radial", 0.93, "..."), ...]

The index is read from the source with `ast` (no bpy, no imports), so it is
always current. Two calls, the "rank then re-check" pattern:

1. Choice questions over chunks of the index pick a shortlist.
2. One Noul per shortlisted entry, with its full docstring, decides whether
   it really does what the need asks. The Noul is absolute, so a need that
   nothing in the library meets comes back with every score low.
"""
import ast
import os
import re

from . import client as J

SCRIPTS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DOC = os.path.join(J.REPO, "docs", "3d-pipeline.md")
CHUNK = 110          # options per Choice: probabilities stay readable below ~150
SHORT = 3            # shortlisted per chunk
KEEP = 10            # re-checked with a Noul


def _first(doc, n=300):
    """The first two paragraphs (what it is, then usually what it is for)."""
    if not doc:
        return ""
    para = " ".join(doc.strip().split("\n\n")[:2])
    para = re.sub(r"\s+", " ", para)
    return para if len(para) <= n else para[:n].rsplit(" ", 1)[0] + " ..."


def _sig(node):
    a = node.args
    names = [x.arg for x in a.posonlyargs + a.args if x.arg not in ("self", "cls")]
    if a.vararg:
        names.append("*" + a.vararg.arg)
    names += [x.arg for x in a.kwonlyargs]
    if a.kwarg:
        names.append("**" + a.kwarg.arg)
    s = ", ".join(names)
    return "(%s)" % (s if len(s) < 90 else s[:87] + "...")


def _py_entries(path, modname, kind):
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except (OSError, SyntaxError):
        return []
    out = []
    mdoc = ast.get_docstring(tree)
    if kind == "carkit" and mdoc:
        out.append(dict(id=modname, kind="module", short=_first(mdoc, 200),
                        full=mdoc[:900], file=path, line=1))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
            doc = ast.get_docstring(node) or ""
            sig = _sig(node) if isinstance(node, ast.FunctionDef) else ""
            if isinstance(node, ast.ClassDef):
                init = next((n for n in node.body if isinstance(n, ast.FunctionDef)
                             and n.name == "__init__"), None)
                sig = _sig(init) if init else "()"
            out.append(dict(id="%s.%s" % (modname, node.name),
                            kind="class" if isinstance(node, ast.ClassDef) else "function",
                            short=(sig + " " + _first(doc)).strip(), full=(sig + "\n" + doc)[:1200],
                            file=path, line=node.lineno))
            if isinstance(node, ast.ClassDef):
                for m in node.body:
                    if isinstance(m, ast.FunctionDef) and not m.name.startswith("_"):
                        mdoc2 = ast.get_docstring(m) or ""
                        out.append(dict(id="%s.%s.%s" % (modname, node.name, m.name), kind="method",
                                        short=(_sig(m) + " " + _first(mdoc2 or doc, 200)).strip(),
                                        full=(_sig(m) + "\n" + (mdoc2 or ("(class) " + doc)))[:1200],
                                        file=path, line=m.lineno))
    return out


def _doc_entries(path=DOC):
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except OSError:
        return []
    out, head, body, start = [], None, [], 0
    for i, ln in enumerate(lines + ["## END"]):
        if ln.startswith("## ") or ln.startswith("### "):
            if head:
                text = "\n".join(body).strip()
                out.append(dict(id="doc: " + head, kind="doc", short=_first(text, 220),
                                full=text[:1500], file=path, line=start + 1))
            head, body, start = ln.lstrip("#").strip(), [], i
        elif head:
            body.append(ln)
    return out


def index(scopes=("carkit", "cars", "doc")):
    """Every entry: {id, kind, short, full, file, line}."""
    out = []
    if "carkit" in scopes:
        root = os.path.join(SCRIPTS, "carkit")
        for dirpath, _dirs, files in os.walk(root):
            if "jev" in dirpath.split(os.sep) or "__pycache__" in dirpath:
                continue
            for f in sorted(files):
                if f.endswith(".py"):
                    p = os.path.join(dirpath, f)
                    rel = os.path.relpath(p, SCRIPTS)[:-3].replace(os.sep, ".")
                    rel = rel[:-9] if rel.endswith(".__init__") else rel
                    out += _py_entries(p, rel, "carkit")
    if "cars" in scopes:
        for f in sorted(os.listdir(SCRIPTS)):
            if f.endswith(".py") and re.match(r"^(su7|rx)_", f):
                out += _py_entries(os.path.join(SCRIPTS, f), f[:-3], "cars")
    if "doc" in scopes:
        out += _doc_entries()
    seen, uniq = set(), []
    for e in out:
        if e["id"] not in seen:
            seen.add(e["id"])
            uniq.append(e)
    return uniq


def _label(e):
    return e["id"][:120]


def find(need, scopes=("carkit", "cars", "doc"), keep=KEEP, context=None):
    """Rank the index against `need` (plain English). Returns a list of
    dicts {id, p, kind, file, line, short}, best first; `p` is the Noul
    probability that the entry does what the need asks."""
    ents = index(scopes)
    by_label = {_label(e): e for e in ents}
    state = {"need": need}
    if context:
        state["context"] = context
    chunks = [ents[i:i + CHUNK] for i in range(0, len(ents), CHUNK)]
    qs = {}
    for k, ch in enumerate(chunks):
        opts = {_label(e): e["short"] or None for e in ch}
        opts["none_of_these"] = "Nothing in this list does what `need` asks for."
        qs["c%d" % k] = J.choice(
            "Which entry (a carkit function, class or module, a car-specific builder "
            "from a previous car, or a section of the pipeline manual) best provides "
            "or explains what `need` asks for?", opts)
    r1 = J.ask(state, qs, tag="find.rank")
    cand = {}
    for a in r1["answers"].values():
        top = sorted(a["probabilities"].items(), key=lambda kv: -kv[1])
        for lab, p in top[:SHORT]:
            if lab != "none_of_these" and p > 0.02:
                cand[lab] = max(cand.get(lab, 0.0), p)
    short = sorted(cand, key=lambda l: -cand[l])[:keep]
    if not short:
        return []
    qs2 = {}
    for i, lab in enumerate(short):
        e = by_label[lab]
        qs2["n%d" % i] = J.noul({
            "candidate": {"name": e["id"], "kind": e["kind"], "documentation": e["full"]},
            "question": "Does `candidate` do what `need` asks for, either directly or as "
                        "the main building block a script would call (or, for a manual "
                        "section, explain how to do it)?"},
            true="It is the right thing to use or read for this need.",
            false="It does something else, or is only loosely related.")
    r2 = J.ask(state, qs2, tag="find.check")
    res = []
    for i, lab in enumerate(short):
        e = by_label[lab]
        res.append(dict(id=e["id"], p=round(r2["answers"]["n%d" % i]["noul"], 3),
                        rank_p=round(cand[lab], 3), kind=e["kind"],
                        file=os.path.relpath(e["file"], J.REPO), line=e["line"], short=e["short"]))
    res.sort(key=lambda d: (-d["p"], -d["rank_p"]))
    return res
