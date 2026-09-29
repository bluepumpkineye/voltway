"""A new car's spec or press text -> a feature checklist and a module plan.

This is the first step for a new car, before any photo is measured. It does
not replace the photos: every feature it reports is a thing to LOOK FOR in
the reference photos (the build uses only what the photos show). What it
saves is the reading: a spec table, a launch article or a trim list is
turned into "has a roof lidar (0.97), flush handles (0.91), camera mirrors
(0.04) ...", the uncertain ones flagged "verify", and each present feature
paired with the carkit part or earlier-car builder to start from.

Numbers (dimensions, wheelbase, wheel sizes) are pulled out by regex in code:
Jev is not used for arithmetic or number reading.

    m = manifest(open("spec.txt").read(), car="Luxeed RX")
    print(checklist(m))
"""
import re

from . import client as J

YES, NO = 0.75, 0.25          # between the two: "verify in photos"

FEATURES = {
    "roof_lidar": "a lidar sensor on the roof above the windscreen",
    "flush_door_handles": "flush or pop-out door handles that sit level with the door skin",
    "frameless_doors": "frameless door windows",
    "glass_roof": "a panoramic glass roof or glass roof panel",
    "front_light_bar": "a light strip running across the front between the headlamps",
    "rear_light_bar": "a full-width rear light bar across the tail",
    "active_rear_spoiler": "a rear spoiler or wing that deploys or moves",
    "fixed_rear_wing": "a fixed rear wing standing off the body",
    "ducktail_spoiler": "an integrated ducktail or lip spoiler on the boot lid or tailgate",
    "roof_spoiler": "a spoiler at the top of the rear window or tailgate",
    "camera_mirrors": "cameras instead of glass side mirrors",
    "black_arch_cladding": "black or dark plastic cladding around the wheel arches",
    "fender_vents": "air vents or outlets on the front fenders",
    "hood_vents": "vents or air outlets in the bonnet (hood)",
    "front_intake_grille": "a visible lower front air intake or grille",
    "illuminated_logo": "an illuminated badge or logo",
    "two_tone_body": "a two-tone paint scheme (contrasting roof or lower body)",
    "rear_diffuser": "a rear diffuser",
    "frunk": "a front trunk (frunk) under the bonnet",
    "brake_calipers_coloured": "coloured (for example orange, red or yellow) brake calipers",
    "semi_active_air_suspension": "air suspension",
}

CHOICES = {
    "body_style": ("What body style is the car described in `spec`?", {
        "sedan": "Four-door saloon with a separate boot lid.",
        "fastback_liftback": "Sloping roof into a tailgate or lift-back boot.",
        "hatchback": "Small car with a near-vertical tailgate.",
        "suv": "Tall SUV or crossover with an upright tailgate.",
        "coupe_suv": "SUV with a sloping, coupe-like roofline.",
        "mpv": "People carrier / MPV with sliding doors or three rows.",
        "wagon": "Estate / shooting brake.",
        "pickup": "Pickup truck.",
        "unknown": "The text does not say.",
    }),
    "charge_port": ("Where is the charging port on the car in `spec`?", {
        "front_left_fender": None, "front_right_fender": None,
        "rear_left_quarter": None, "rear_right_quarter": None,
        "nose": "In the front of the car.", "unknown": "The text does not say.",
    }),
    "powertrain": ("What powertrain does the car in `spec` have?", {
        "bev": "Battery electric only.", "erev": "Extended-range electric (range extender).",
        "phev": "Plug-in hybrid.", "unknown": "The text does not say.",
    }),
}


def numbers(text):
    """Dimensions, wheelbase and wheel sizes read by regex (mm, inches)."""
    t = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", text)      # 5,020 -> 5020 only
    out = {}
    m = re.search(r"(\d{4})\s*[x×*/]\s*(\d{4})\s*[x×*/]\s*(\d{4})", t)
    if m:
        out["length_mm"], out["width_mm"], out["height_mm"] = (int(g) for g in m.groups())
    for key, word in (("length_mm", r"(?:length|long|长度?)"), ("width_mm", r"(?:width|wide|宽度?)"),
                      ("height_mm", r"(?:height|tall|high|高度?)"),
                      ("wheelbase_mm", r"(?:wheelbase|wheel base|轴距)")):
        if key in out and key != "wheelbase_mm":
            continue
        # "5020 mm in length" (number first) or "length: 5020" / "轴距3000" (word first)
        m = (re.search(r"(\d{4})\s*mm\s+(?:in\s+|of\s+)?" + word, t, re.I)
             or re.search(word + r"(?:\s+of)?\s*(?:is\s*)?[:：=为]?\s*(\d{4})", t, re.I))
        if m:
            out[key] = int(m.group(1))
    sizes = sorted({int(s) for s in re.findall(r"(?<!\d)(1[6-9]|2[0-3])\s*(?:-?\s*inch|in\b|\"|”|英寸|寸)", t, re.I)}
                   | {int(s) for s in re.findall(r"\d{3}/\d{2}\s*Z?R\s*(1[6-9]|2[0-3])", t, re.I)})
    if sizes:
        out["wheel_inches"] = sizes
    tyres = sorted(set(re.findall(r"\d{3}/\d{2}\s*Z?R\s*\d{2}", t, re.I)))
    if tyres:
        out["tyres"] = tyres
    return out


def manifest(text, car=None, with_parts=False):
    """{numbers, features: {name: {p, verdict}}, choices: {name: {choice, confidence}},
    parts: {feature: finder hits}}."""
    state = {"spec": text[:60000]}
    if car:
        state["car"] = car
    qs = {}
    for k, desc in FEATURES.items():
        qs["f_" + k] = J.noul("According to `spec`, does the car have %s?" % desc,
                              true="`spec` says or clearly implies the car has it.",
                              false="`spec` says it does not, or does not mention it.")
    for k, (ins, opts) in CHOICES.items():
        qs["c_" + k] = J.choice(ins, opts)
    r = J.ask(state, qs, tag="onboard")
    a = r["answers"]
    feats = {}
    for k in FEATURES:
        p = a["f_" + k]["noul"]
        feats[k] = dict(p=round(p, 3), verdict="yes" if p >= YES else "no" if p <= NO else "verify")
    chs = {k: dict(choice=a["c_" + k]["choice"], confidence=round(a["c_" + k]["confidence"], 2))
           for k in CHOICES}
    out = dict(car=car, numbers=numbers(text), features=feats, choices=chs, ms=round(r["ms"]))
    if with_parts:
        from . import finder
        want = [k for k, f in feats.items() if f["verdict"] != "no"]
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
            hits = list(ex.map(lambda k: finder.find("build " + FEATURES[k], keep=5), want))
        out["parts"] = {k: [(h["id"], h["p"]) for h in hs[:3] if h["p"] >= 0.5]
                        for k, hs in zip(want, hits)}
    return out


def checklist(m):
    """Markdown: what to look for in the photos, and where to start."""
    L = ["# %s: onboarding checklist" % (m.get("car") or "new car"), "",
         "Every item is a thing to confirm in the reference photos; nothing is built from this list.", ""]
    if m["numbers"]:
        L += ["## Numbers (regex; check against the type-approval filing)", ""]
        L += ["- %s: %s" % (k, v) for k, v in m["numbers"].items()] + [""]
    L += ["## Body", ""]
    L += ["- %s: **%s** (confidence %.2f)" % (k, c["choice"], c["confidence"])
          for k, c in m["choices"].items()] + [""]
    for verdict, title in (("yes", "Features the text says it has (find them in the photos)"),
                           ("verify", "Unclear from the text (decide from the photos)"),
                           ("no", "Not mentioned or absent (check the photos before leaving out)")):
        ks = [k for k, f in m["features"].items() if f["verdict"] == verdict]
        if not ks:
            continue
        L += ["## " + title, ""]
        for k in sorted(ks, key=lambda k: -m["features"][k]["p"]):
            line = "- [ ] %s (p=%.2f)" % (FEATURES[k], m["features"][k]["p"])
            parts = m.get("parts", {}).get(k)
            if parts:
                line += " -> start from " + ", ".join("`%s`" % p for p, _ in parts)
            L.append(line)
        L.append("")
    return "\n".join(L)
