"""Wheels, tyres and brakes.

A wheel is built in its own frame - axle along local Z, outboard positive, the
face in local XY - and placed with ONE proper rotation, so left and right can
never drift apart and no reflection (determinant -1, which silently inverts
winding in glTF) is ever used.

    build_wheel(collection, prefix, tag, centre, sign, lib, spec, ...)
    build_set(collection, prefix, lib, corners)   four corners from a table

A spec is a dict; PRESETS holds named ones and `preset(name, **overrides)`
copies one with changes. The pieces:

    tyre      revolved profile: bead, sidewall bulge, shoulder, tread
    rim       barrel, flange, optional pinstripe on the flange
    face      the SPOKE STYLE (below), following a dish depth curve
    hub       hub plate, centre cap, lug bolts in counterbores
    brake     disc (drilled / slotted / plain), bell, caliper

Spoke styles (spec["spokes"]["style"]):

    hairpin_u   closed U round the hub, two slender legs to the rim - the SU7
                Ultra's forged "double-five-spoke U"
    straight    N tapered radial spokes; `twist` bends them into a turbine
    split_y     a stem from the hub forking into two legs (Y spokes)
    twin        pairs of parallel spokes
    aero        a closed dished aero face with N windows cut through it

A wheel's identity is DEPTH, not detail: the face dish (spec["dish"], depth
below the flange by radius) separates spokes, disc and caliper into layers
with dark voids between them. Flat spokes on one plane read as a black dish.
"""
import copy
import math

import bpy
from mathutils import Matrix

from ..geom import Curve, smoothstep
from .. import mesh as M
from .. import cut as C

# ---------------------------------------------------------------- dishes
# Depth of the face below the flange by radius (metres). DEEP is the SU7
# Ultra: the crest 14 mm below the flange at the rim, plunging 74 mm to the hub.
DISH_DEEP = Curve([
    (0.000, 0.0735), (0.090, 0.0735), (0.105, 0.0660), (0.130, 0.0450),
    (0.160, 0.0275), (0.200, 0.0190), (0.232, 0.0145), (0.245, 0.0120),
], mode="pchip")
DISH_MEDIUM = Curve([
    (0.000, 0.0500), (0.090, 0.0500), (0.110, 0.0430), (0.150, 0.0270),
    (0.200, 0.0160), (0.245, 0.0100),
], mode="pchip")
DISH_FLAT = Curve([
    (0.000, 0.0300), (0.090, 0.0300), (0.120, 0.0220), (0.180, 0.0120),
    (0.245, 0.0080),
], mode="pchip")


# ---------------------------------------------------------------- spokes
def sweep(path, width, a0, d_face, depth, tilt=None):
    """A rectangle swept along a centreline in the wheel face.

    path: [(u, s)] in a frame rotated by a0 (u radial, s tangential);
    width: per-point widths. The top face follows the dish (d_face(r)), and
    the member is `depth` deep behind it. One continuous solid - ten separate
    beveled boxes per leg left a seam at every joint and read as chain links.

    tilt: per-point depth (metres) of the +side edge below the -side edge -
    a top face canted across its width, as on a twisted blade spoke.
    """
    ca, sa = math.cos(a0), math.sin(a0)

    def to_face(u, s):
        return (u * ca - s * sa, u * sa + s * ca)

    verts = []
    n = len(path)
    for i in range(n):
        u0, s0 = path[max(0, i - 1)]
        u1, s1 = path[min(n - 1, i + 1)]
        tu, ts = u1 - u0, s1 - s0
        L = math.hypot(tu, ts) or 1.0
        nu, ns = -ts / L, tu / L                 # lateral, in the face plane
        u, s = path[i]
        hw = 0.5 * width[i]
        for side in (-1.0, 1.0):
            x, y = to_face(u + nu * hw * side, s + ns * hw * side)
            r = math.hypot(x, y)
            df = d_face(r)
            if tilt is not None and side > 0:
                df -= tilt[i]
            verts.append((x, y, df))
            verts.append((x, y, df - depth))
    faces = []
    for i in range(n - 1):
        b, c = i * 4, (i + 1) * 4
        faces += [[b + 0, c + 0, c + 2, b + 2],      # face
                  [b + 1, b + 3, c + 3, c + 1],      # back
                  [b + 0, b + 1, c + 1, c + 0],      # wall
                  [b + 2, c + 2, c + 3, b + 3]]      # wall
    faces.append([0, 2, 3, 1])
    last = (n - 1) * 4
    faces.append([last + 0, last + 1, last + 3, last + 2])
    return verts, faces


def hairpin_u(a0, d_face, depth=0.030, r_bight=0.128, rb=0.041, r_rim=0.250,
              h_rim=0.058, w_bight=0.024, w_rim=0.021, n_leg=18, n_arc=16):
    """One U spoke: closed round the hub, two slender legs out to the rim."""
    path, width = [], []
    for i in range(n_leg + 1):                   # leg 1, rim -> bight
        t = i / float(n_leg)
        path.append((r_rim + (r_bight - r_rim) * t, -(h_rim + (rb - h_rim) * t)))
        width.append(w_rim + (w_bight - w_rim) * t)
    for i in range(1, n_arc):                    # bight, round the hub side
        th = -0.5 * math.pi - math.pi * i / float(n_arc)
        path.append((r_bight + rb * math.cos(th), rb * math.sin(th)))
        width.append(w_bight)
    for i in range(n_leg + 1):                   # leg 2, bight -> rim
        t = i / float(n_leg)
        path.append((r_bight + (r_rim - r_bight) * t, rb + (h_rim - rb) * t))
        width.append(w_bight + (w_rim - w_bight) * t)
    return sweep(path, width, a0, d_face, depth)


def straight(a0, d_face, depth=0.030, r_hub=0.100, r_rim=0.250, w_hub=0.034,
             w_rim=0.024, twist=0.0, twist_power=1.6, offset=0.0, n=16):
    """A tapered radial spoke. twist (radians at the rim) curves it into a
    turbine blade; offset (metres) shifts it sideways (for twins)."""
    path, width = [], []
    for i in range(n + 1):
        t = i / float(n)
        r = r_hub + (r_rim - r_hub) * t
        ang = twist * t ** twist_power
        path.append((r * math.cos(ang) - offset * math.sin(ang),
                     r * math.sin(ang) + offset * math.cos(ang)))
        width.append(w_hub + (w_rim - w_hub) * t)
    return sweep(path, width, a0, d_face, depth)


def split_y(a0, d_face, depth=0.030, r_hub=0.100, r_split=0.165, r_rim=0.250,
            spread=0.16, w_stem=0.036, w_leg=0.019, n=12):
    """A Y spoke: a stem that forks into two legs at r_split. spread is each
    leg's half-angle at the rim, radians."""
    parts = [straight(a0, d_face, depth, r_hub, r_split + 0.012, w_stem, w_stem * 0.9,
                      n=max(4, n // 2))]
    for side in (-1.0, 1.0):
        path, width = [], []
        for i in range(n + 1):
            t = i / float(n)
            r = (r_split - 0.004) + (r_rim - r_split + 0.004) * t
            ang = side * spread * smoothstep(t * 1.15)
            path.append((r * math.cos(ang), r * math.sin(ang)))
            width.append(w_stem * 0.62 + (w_leg - w_stem * 0.62) * t)
        parts.append(sweep(path, width, a0, d_face, depth))
    return M.merge_parts(parts)


def twin(a0, d_face, depth=0.030, gap=0.024, **kw):
    """Two parallel spokes `gap` apart (centre to centre)."""
    kw.setdefault("w_hub", 0.020)
    kw.setdefault("w_rim", 0.016)
    return M.merge_parts([straight(a0, d_face, depth, offset=-0.5 * gap, **kw),
                          straight(a0, d_face, depth, offset=0.5 * gap, **kw)])


def blade(a0, d_face, depth=0.032, r_hub=0.096, r_rim=0.258, w_hub=0.060,
          w_rim=0.112, twist=0.13, twist_power=1.5, split=0.55, drop=0.026, n=20,
          split_hub=None):
    """A broad blade spoke, widening to the rim and gently swept (twist), in
    two facets along its length: a flat machined face on the leading side
    (`split` of the width) and a flank on the trailing side that drops
    `drop` below it - the Luxeed RX's 21 in wheel, bright face, dark flank.
    split_hub: the face's share of the width at the hub end, if it narrows
    to the hub (the RX: a machined triangle, nothing at the hub).

    Returns (verts, faces, face_mat): face_mat 1 marks the machined face.
    """
    path, w_face, w_flank, off_face, off_flank, drops = [], [], [], [], [], []
    for i in range(n + 1):
        t = i / float(n)
        r = r_hub + (r_rim - r_hub) * t
        ang = twist * t ** twist_power
        path.append((r * math.cos(ang), r * math.sin(ang)))
        w = w_hub + (w_rim - w_hub) * smoothstep(t)
        k = split if split_hub is None else split_hub + (split - split_hub) * t
        w_face.append(w * k)
        w_flank.append(w * (1.0 - k))
        drops.append([0.0, drop * (0.5 + 0.5 * t)])
    faces_out, verts_out, mats = [], [], []
    for part, widths, sgn in (("face", w_face, -1.0), ("flank", w_flank, 1.0)):
        # shift the centreline sideways so the two facets share an edge
        shifted = []
        for i, (u, s) in enumerate(path):
            u0, s0 = path[max(0, i - 1)]
            u1, s1 = path[min(n, i + 1)]
            tu, ts = u1 - u0, s1 - s0
            L = math.hypot(tu, ts) or 1.0
            nu, ns = -ts / L, tu / L
            h = 0.5 * widths[i] * sgn
            shifted.append((u + nu * h, s + ns * h))
        if part == "face":
            v, f = sweep(shifted, widths, a0, d_face, depth)
        else:
            # the flank's inner edge (shared with the face) stays level with
            # it, its outer edge drops: tilt acts on the +side
            v, f = sweep(shifted, widths, a0, d_face, depth - 0.004,
                         tilt=[d[1] for d in drops])
        base = len(verts_out)
        verts_out += v
        for k, face in enumerate(f):
            faces_out.append([base + j for j in face])
            # the first of each 4 per segment is the top face
            mats.append(1 if (part == "face" and k < 4 * n and k % 4 == 0) else 0)
    return verts_out, faces_out, mats


SPOKE_STYLES = {"hairpin_u": hairpin_u, "straight": straight, "split_y": split_y,
                "twin": twin, "blade": blade}


# ------------------------------------------------------------------ presets
PRESETS = {
    # Xiaomi SU7 Ultra: 21 in forged double-five-spoke U, gloss black with a
    # gold pinstripe, carbon-ceramic drilled discs, gold Akebono calipers.
    "su7_ultra_hairpin": dict(
        rim_d=0.5334, flange=(0.126, 0.1325, 0.55), dish=DISH_DEEP,
        spokes=dict(style="hairpin_u", count=5, phase=math.pi / 2.0, depth=0.030,
                    params={}, bevel=0.0030, mat="rim"),
        pinstripe=True, hub=dict(depth=0.0735, setback=0.010),
        lugs=dict(count=5, pcd_r=0.05715, r=0.0118),
        disc=dict(style="drilled", inner_r=0.128, thickness=0.036, setback=0.104,
                  rings=3, per_ring=18, hole_r=0.0042),
        caliper=dict(span_deg=30.0, r_in=0.058, r_out=0.020, rim_clear=0.034,
                     d_out=0.046, d_in=0.080, bulge=0.012, bevel=0.008, steps=12),
        tyre=dict(bulge=1.055, shoulder=0.016),
        mats=dict(tyre="rubber", rim="rim", stripe="rim_lip", cap="black_gloss",
                  lugs="disc", disc="disc", bell="lamp_housing", holes="shadow",
                  caliper="caliper"),
        seg=72,
    ),
}


def _derive(base, **changes):
    d = copy.deepcopy(PRESETS[base])
    for k, v in changes.items():
        if isinstance(v, dict) and isinstance(d.get(k), dict):
            d[k].update(v)
        else:
            d[k] = v
    return d


# Catalogue presets for other cars. Styles, not copies of any one car: pick the
# nearest, then set sizes and counts from the reference photographs.
PRESETS["aero_5window"] = _derive(
    "su7_ultra_hairpin", dish=DISH_FLAT, pinstripe=False,
    spokes=dict(style="aero", count=5, phase=math.pi / 2.0, depth=0.008, bevel=0.0015,
                params=dict(r_in=0.070, r_win0=0.140, r_win1=0.228, half_angle=0.30,
                            corner=0.3)),
    disc=dict(style="plain"), caliper=dict(span_deg=26.0))
PRESETS["turbine_10"] = _derive(
    "su7_ultra_hairpin", dish=DISH_MEDIUM, pinstripe=False,
    spokes=dict(style="straight", count=10, phase=math.pi / 2.0, depth=0.024,
                bevel=0.0022, params=dict(w_hub=0.022, w_rim=0.018, twist=0.34)),
    disc=dict(style="slotted"))
PRESETS["y_spoke_5"] = _derive(
    "su7_ultra_hairpin", dish=DISH_MEDIUM, pinstripe=False,
    spokes=dict(style="split_y", count=5, phase=math.pi / 2.0, depth=0.028,
                bevel=0.0025, params=dict(spread=0.20)))
PRESETS["twin_5"] = _derive(
    "su7_ultra_hairpin", dish=DISH_MEDIUM, pinstripe=False,
    spokes=dict(style="twin", count=5, phase=math.pi / 2.0, depth=0.026,
                bevel=0.0022, params=dict(gap=0.030)))
PRESETS["blade_5"] = _derive(
    "su7_ultra_hairpin", dish=DISH_MEDIUM, pinstripe=True,
    mats=dict(stripe="chrome"),
    spokes=dict(style="blade", count=5, phase=math.pi / 2.0, depth=0.032,
                bevel=0.0020, params={}, face_mat="chrome"),
    disc=dict(style="plain", inner_r=0.120, thickness=0.032), caliper=dict(span_deg=28.0))
PRESETS["multi_10"] = _derive(
    "su7_ultra_hairpin", dish=DISH_DEEP, pinstripe=False,
    spokes=dict(style="straight", count=10, phase=math.pi / 2.0, depth=0.028,
                bevel=0.0025, params=dict(w_hub=0.024, w_rim=0.016)),
    disc=dict(style="plain"))


def preset(name, **changes):
    """A copy of PRESETS[name]; dict-valued changes are merged one level deep."""
    return _derive(name, **changes)


# ------------------------------------------------------------------- tyre
def tyre_profile(rim_r, radius, hw, bulge=1.055, shoulder=0.016):
    """(r, d) profile of a tyre from bead to bead across the tread."""
    sh = radius - shoulder
    mid = (rim_r + radius) * 0.5
    return [
        (rim_r + 0.004, -hw * 0.92), (rim_r + 0.024, -hw * 1.02),
        (mid, -hw * bulge), (sh - 0.010, -hw * 1.00), (sh, -hw * 0.93),
        (radius - 0.002, -hw * 0.82), (radius, -hw * 0.40), (radius, hw * 0.40),
        (radius - 0.002, hw * 0.82), (sh, hw * 0.93), (sh - 0.010, hw * 1.00),
        (mid, hw * bulge), (rim_r + 0.024, hw * 1.02), (rim_r + 0.004, hw * 0.92),
    ], mid


# --------------------------------------------------------------- aero face
def _aero_face(name, collection, mat, d_face, rim_r, count, phase, depth, params,
               seg=72, nr=14):
    """A closed dished face with `count` windows cut through it."""
    r_in = params.get("r_in", 0.070)
    r_out = rim_r - 0.012
    prof = [(r_in + (r_out - r_in) * i / float(nr), 0.0) for i in range(nr + 1)]
    prof = [(r, d_face(r)) for (r, _) in prof]
    v, f = M.revolve(prof, seg)
    ob = M.obj(name, v, f, collection, mat)
    M.orient(ob.data, lambda c: (0.0, 0.0, 1.0))
    M.solidify(ob, depth, -1.0)
    r0, r1 = params.get("r_win0", 0.14), params.get("r_win1", 0.228)
    ha = params.get("half_angle", 0.30)
    corner = params.get("corner", 0.3)
    cutters = []
    for k in range(count):
        a0 = 2.0 * math.pi * k / count + phase + math.pi / count
        loop = []
        m = 10
        for i in range(m + 1):                               # outer arc
            t = -1.0 + 2.0 * i / m
            a = a0 + ha * t * (1.0 - corner * 0.25 * t * t)
            loop.append((r1 * math.cos(a), r1 * math.sin(a), 0.0))
        for i in range(m + 1):                               # inner arc
            t = 1.0 - 2.0 * i / m
            a = a0 + ha * 0.62 * t * (1.0 - corner * 0.25 * t * t)
            loop.append((r0 * math.cos(a), r0 * math.sin(a), 0.0))
        cutters.append(C.prism_dir("_win_%s_%d" % (name, k), loop, (0.0, 0.0, 1.0),
                                   back=0.3, front=0.3))
    C.difference(ob, cutters, "win_", reset_materials=True)
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


# ------------------------------------------------------------------ wheel
def build_wheel(collection, prefix, tag, centre, sign, lib, spec, tyre_w, radius,
                disc_r, caliper_deg):
    """One corner. `sign` +1 for the left side, -1 for the right.

    Returns (empty, parts); the parts are parented to the empty, which carries
    the placement.
    """
    parts = []
    mats = spec["mats"]
    seg = spec.get("seg", 72)
    rim_r = spec["rim_d"] / 2.0
    hw = tyre_w / 2.0
    fa, fb, fc = spec["flange"]
    d_flange = fa + (hw - fb) * fc            # wider rims sit further out
    dish = spec["dish"]

    def d_face(r):
        return d_flange - dish(r)

    # ---------------------------------------------------------------- tyre
    prof, mid = tyre_profile(rim_r, radius, hw, spec["tyre"]["bulge"],
                             spec["tyre"]["shoulder"])
    v, f = M.revolve(prof, seg)
    tyre = M.obj(prefix + "Tyre_" + tag, v, f, collection, lib[mats["tyre"]])
    M.orient_revolved(tyre, mid, 0.0)
    parts.append(tyre)

    # ----------------------------------------------------- rim barrel + flange
    barrel = [
        (rim_r - 0.006, -hw * 0.90), (rim_r - 0.030, -hw * 0.70),
        (rim_r - 0.030, hw * 0.35), (rim_r - 0.022, d_flange - 0.040),
        (rim_r - 0.014, d_flange - 0.018),          # rim landing, spokes meet it
        (rim_r - 0.010, d_flange - 0.004),
        (rim_r - 0.011, d_flange),                  # flange face, inner edge
    ]
    v, f = M.revolve(barrel, seg)
    parts.append(M.obj(prefix + "RimBarrel_" + tag, v, f, collection, lib[mats["rim"]]))

    flange = [
        (rim_r - 0.011, d_flange), (rim_r - 0.0005, d_flange),
        (rim_r + 0.0015, d_flange - 0.004), (rim_r + 0.0005, d_flange - 0.012),
    ]
    v, f = M.revolve(flange, seg)
    parts.append(M.obj(prefix + "RimFlange_" + tag, v, f, collection, lib[mats["rim"]]))

    if spec.get("pinstripe"):
        stripe = [(rim_r - 0.0070, d_flange + 0.0004), (rim_r - 0.0030, d_flange + 0.0004)]
        v, f = M.revolve(stripe, seg)
        parts.append(M.obj(prefix + "RimStripe_" + tag, v, f, collection,
                           lib[mats["stripe"]]))

    # --------------------------------------------------------------- face
    sp = spec["spokes"]
    style = sp["style"]
    mat_sp = lib[sp.get("mat", mats["rim"])]
    if style == "aero":
        face = _aero_face(prefix + "Spokes_" + tag, collection, mat_sp, d_face, rim_r,
                          sp["count"], sp["phase"], sp["depth"], sp.get("params", {}),
                          seg=seg)
        M.bevel(face, sp.get("bevel", 0.0015), 2, 30, harden=True)
        parts.append(face)
    else:
        fn = SPOKE_STYLES[style]
        members = []
        for k in range(sp["count"]):
            a0 = 2.0 * math.pi * k / sp["count"] + sp["phase"]
            members.append(fn(a0, d_face, depth=sp["depth"], **sp.get("params", {})))
        # a style may return (verts, faces, face_mat) - a per-face material
        # index for two-tone faces (blade: machined face, painted flank)
        fmat = None
        if any(len(m) == 3 for m in members):
            fmat = []
            for m in members:
                fmat += list(m[2]) if len(m) == 3 else [0] * len(m[1])
            members = [(m[0], m[1]) for m in members]
        v, f = M.merge_parts(members)
        spokes = M.obj(prefix + "Spokes_" + tag, v, f, collection, mat_sp, smooth=False)
        if sp.get("face_mat"):
            spokes.data.materials.append(lib[sp["face_mat"]])
            for i, p in enumerate(spokes.data.polygons):
                if fmat is not None:
                    p.material_index = fmat[i]
                elif p.normal.z > 0.55:
                    p.material_index = 1
        M.bevel(spokes, sp.get("bevel", 0.0030), 2, 30, harden=True)
        parts.append(spokes)

    # ------------------------------------------------------------ hub plate
    hub_spec = spec["hub"]
    d_hub = d_flange - hub_spec["depth"] - hub_spec["setback"]
    hub = [(0.004, d_hub + 0.002), (0.030, d_hub + 0.002), (0.034, d_hub),
           (0.098, d_hub), (0.104, d_hub - 0.008), (0.104, d_hub - 0.022),
           (0.010, d_hub - 0.024)]
    v, f = M.revolve(hub, 40)
    parts.append(M.obj(prefix + "Hub_" + tag, v, f, collection, lib[mats["rim"]]))

    cap = [(0.0, d_hub + 0.0055), (0.026, d_hub + 0.0055), (0.029, d_hub + 0.003),
           (0.029, d_hub)]
    v, f = M.revolve(cap, 32)
    parts.append(M.obj(prefix + "HubCap_" + tag, v, f, collection, lib[mats["cap"]]))

    # lug bolts in counterbores, between the spokes
    lg = spec["lugs"]
    nl = lg["count"]
    lugs = []
    for k in range(nl):
        a = 2.0 * math.pi * k / nl + sp["phase"] + math.pi / nl
        cx, cy = lg["pcd_r"] * math.cos(a), lg["pcd_r"] * math.sin(a)
        ring = []
        for i in range(6):
            b = 2 * math.pi * i / 6
            ring.append((cx + lg["r"] * math.cos(b), cy + lg["r"] * math.sin(b)))
        vv = [(p[0], p[1], d_hub - 0.001) for p in ring] + \
             [(p[0], p[1], d_hub - 0.012) for p in ring] + [(cx, cy, d_hub - 0.001)]
        ff = [[i, (i + 1) % 6, 6 + (i + 1) % 6, 6 + i] for i in range(6)]
        ff += [[12, i, (i + 1) % 6] for i in range(6)]
        lugs.append((vv, ff))
    v, f = M.merge_parts(lugs)
    parts.append(M.obj(prefix + "Lugs_" + tag, v, f, collection, lib[mats["lugs"]],
                       smooth=False))

    # ------------------------------------------------------ disc and caliper
    dk = spec["disc"]
    d_disc = d_flange - dk.get("setback", 0.104)
    r_in = dk.get("inner_r", 0.128)
    th = dk.get("thickness", 0.036)
    disc = [(r_in, d_disc), (disc_r, d_disc), (disc_r, d_disc - th), (r_in, d_disc - th)]
    v, f = M.revolve(disc, 72)
    parts.append(M.obj(prefix + "Disc_" + tag, v, f, collection, lib[mats["disc"]],
                       smooth=False))
    bell = [(0.100, d_hub - 0.024), (r_in, d_hub - 0.030), (r_in, d_disc)]
    v, f = M.revolve(bell, 40)
    parts.append(M.obj(prefix + "DiscBell_" + tag, v, f, collection, lib[mats["bell"]]))

    style_d = dk.get("style", "drilled")
    if style_d == "drilled":
        holes = []
        rings = dk.get("rings", 3)
        per = dk.get("per_ring", 18)
        hr = dk.get("hole_r", 0.0042)
        for ring_i, rr in enumerate([disc_r - 0.022, disc_r - 0.040, disc_r - 0.058][:rings]):
            for k in range(per):
                a = 2 * math.pi * (k + ring_i / 3.0) / per
                cx, cy = rr * math.cos(a), rr * math.sin(a)
                vv = [(cx, cy, d_disc + 0.0004)]
                vv += [(cx + hr * math.cos(2 * math.pi * i / 8),
                        cy + hr * math.sin(2 * math.pi * i / 8), d_disc + 0.0004)
                       for i in range(8)]
                holes.append((vv, [[0, 1 + i, 1 + (i + 1) % 8] for i in range(8)]))
        v, f = M.merge_parts(holes)
        parts.append(M.obj(prefix + "DiscHoles_" + tag, v, f, collection,
                           lib[mats["holes"]], smooth=False))
    elif style_d == "slotted":
        slots = []
        n_s = dk.get("slots", 12)
        for k in range(n_s):
            a0 = 2 * math.pi * k / n_s
            quad = []
            for (rr, da) in ((disc_r - 0.050, 0.0), (disc_r - 0.012, 0.22)):
                for w in (-0.0022, 0.0022):
                    a = a0 + da + w / rr
                    quad.append((rr * math.cos(a), rr * math.sin(a), d_disc + 0.0004))
            slots.append((quad, [[0, 1, 3, 2]]))
        v, f = M.merge_parts(slots)
        parts.append(M.obj(prefix + "DiscHoles_" + tag, v, f, collection,
                           lib[mats["holes"]], smooth=False))

    cs = spec["caliper"]
    ca = math.radians(caliper_deg)
    span = math.radians(cs.get("span_deg", 30.0))
    r0 = disc_r - cs.get("r_in", 0.058)
    r1 = min(disc_r + cs.get("r_out", 0.020), rim_r - cs.get("rim_clear", 0.034))
    d_out = d_disc + cs.get("d_out", 0.046)
    d_in = d_disc - cs.get("d_in", 0.080)
    bulge_c = cs.get("bulge", 0.012)
    steps = cs.get("steps", 12)
    cverts, cfaces = [], []
    for i in range(steps + 1):
        a = ca - span + 2 * span * i / steps
        bulge = bulge_c * math.sin(math.pi * i / steps)   # swell in the middle
        for r in (r0, r1):
            for dd in (d_out + bulge, d_in):
                cverts.append((r * math.cos(a), r * math.sin(a), dd))
    for i in range(steps):
        b = i * 4
        n = b + 4
        cfaces += [[b + 0, n + 0, n + 2, b + 2], [b + 1, b + 3, n + 3, n + 1],
                   [b + 0, b + 1, n + 1, n + 0], [b + 2, n + 2, n + 3, b + 3]]
    cfaces.append([0, 2, 3, 1])
    last = steps * 4
    cfaces.append([last + 0, last + 1, last + 3, last + 2])
    cal = M.obj(prefix + "Caliper_" + tag, cverts, cfaces, collection,
                lib[mats["caliper"]], smooth=True)
    M.bevel(cal, cs.get("bevel", 0.008), 3, 30, harden=True)
    parts.append(cal)

    # ---------------------------------------------------------- placement
    # Proper rotations about X, never reflections: local Z (the axle, outboard
    # positive) goes to world +Y on the left and -Y on the right.
    cx, cy, cz = centre
    if sign > 0:
        R = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))     # Rx(-90)
    else:
        R = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))     # Rx(+90)
    Mx = R.to_4x4()
    Mx.translation = (cx, cy, cz)
    empty = bpy.data.objects.new(prefix + "Wheel_" + tag, None)
    empty.empty_display_size = 0.12
    collection.objects.link(empty)
    empty.matrix_world = Mx
    for p in parts:
        p.parent = empty
    return empty, parts


def build_set(collection, prefix, lib, spec, corners):
    """Four (or more) corners.

    corners: [(tag, x_axle, sign, tyre width, rolling radius, disc radius,
               caliper degrees, outer sidewall y), ...]. The wheel is centred
    so its outer sidewall sits at that y - about 20 mm inside the arch lip.
    """
    made = []
    for tag, axle, sign, w, r, dr, cal, outer in corners:
        cy = sign * (outer - w / 2.0)
        made.append(build_wheel(collection, prefix, tag, (axle, cy, r), sign, lib,
                                spec, w, r, dr, cal))
    return made
