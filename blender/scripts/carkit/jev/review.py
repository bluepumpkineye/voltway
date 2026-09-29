"""Turn review notes into a fix plan: which module, what kind of fix, how bad.

The notes are text: the agent's photo-vs-render comparisons (written while
looking at the matched pairs), or the owner's feedback. Jev routes each note;
code orders the plan. Jev never sees the images, so a note must say what is
wrong in words ("the light bar sits 3 cm too low in the rear view").

    plan = route("rx", ["front: the headlamp is too thin ...", ...])
    for item in plan: item["module"], item["action"], item["severity"]

One call per note (in parallel), so each note is judged on its own words.
"""
import ast
import os
import re

from . import client as J
from .finder import SCRIPTS

ACTIONS = {
    "shape": "The model has the part, but its surface or outline is the wrong shape or size: "
             "profile, section, crown, bulge, height, width, overhang, where a line peaks.",
    "position": "The model has the part with the right shape, but it sits in the wrong place "
                "or at the wrong angle.",
    "missing": "The real car (the photos) has a feature or detail that the model lacks.",
    "invented": "The model has something (a bar, trim, vent, line, part) that the real car "
                "does not have; the fix is to remove it.",
    "material": "Colour, gloss, metallic flake, texture, transparency or lamp look of a surface "
                "is wrong.",
    "render": "The difference comes from lighting, reflections, exposure, camera or background, "
              "not from the model.",
    "ok": "The note says the area matches; nothing to change.",
}

SEVERITY = [
    "No visible difference.",
    "Cosmetic: only visible up close or when looking for it.",
    "Noticeable at first glance in a matched view.",
    "Obvious: the car reads wrong in that area.",
    "Breaks the likeness: someone who knows the car would not recognise it.",
]

EXTRA_MODULES = {
    "scene_setup": "Studio lights, world, render cameras and render settings.",
    "carkit": "A bug or missing feature in the shared carkit library itself.",
}


def car_modules(car):
    """{module: description} from the car's build_<car>.py docstring (the
    module table every car's entry point carries)."""
    path = os.path.join(SCRIPTS, "build_%s.py" % car)
    doc = ast.get_docstring(ast.parse(open(path, encoding="utf-8").read())) or ""
    mods = {}
    for line in doc.splitlines():
        m = re.match(r"^\s{2,}(%s_\w+)\s{2,}(.+)$" % re.escape(car), line)
        if m:
            mods[m.group(1)] = m.group(2).strip()
    mods.update(EXTRA_MODULES)
    return mods


def route(car, notes, car_name=None):
    """Route each note; returns items sorted most severe first:
    {note, module, module_conf, action, action_conf, severity, severity_conf}."""
    mods = car_modules(car)
    jobs = []
    for n in notes:
        state = {"car": car_name or car, "review_note": n}
        jobs.append(dict(state=state, tag="review.route", questions={
            "module": J.choice("Which build module has to change to fix what `review_note` "
                               "describes?", mods),
            "action": J.choice("What kind of change does `review_note` call for?", ACTIONS),
            "severity": J.score("How serious is the difference `review_note` describes, for a "
                                "photoreal model of the real car?", SEVERITY),
        }))
    out = []
    for n, r in zip(notes, J.ask_many(jobs)):
        a = r["answers"]
        out.append(dict(note=n, module=a["module"]["choice"],
                        module_conf=round(a["module"]["confidence"], 2),
                        action=a["action"]["choice"], action_conf=round(a["action"]["confidence"], 2),
                        severity=round(a["severity"]["score"], 2),
                        severity_conf=round(a["severity"]["confidence"], 2)))
    out.sort(key=lambda d: -d["severity"])
    return out


def plan_text(items, min_severity=1.0):
    """The plan as lines, grouped by module, most severe module first."""
    todo = [i for i in items if i["action"] != "ok" and i["severity"] >= min_severity]
    by = {}
    for i in todo:
        by.setdefault(i["module"], []).append(i)
    lines = []
    for mod, its in sorted(by.items(), key=lambda kv: -max(i["severity"] for i in kv[1])):
        lines.append("%s" % mod)
        for i in its:
            flag = "" if i["module_conf"] >= 0.5 and i["action_conf"] >= 0.5 else "  (check routing)"
            lines.append("  [%.1f %-8s] %s%s" % (i["severity"], i["action"], i["note"], flag))
    return "\n".join(lines)
