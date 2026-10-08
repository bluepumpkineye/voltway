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


# ------------------------------------------------------------ traced faces
def _polar(a_deg, r, big_r):
    a = math.radians(a_deg)
    return (big_r * r * math.cos(a), big_r * r * math.sin(a))


def _densify(pts, step_deg=1.5, step_r=0.02):
    """The straight edges of a closed polygon in (angle, radius) space cut into
    short pieces, so an outline traced in polar coordinates stays curved - an
    edge between two points of one radius is an arc - once it is x, y."""
    out = []
    n = len(pts)
    for i in range(n):
        a0, r0 = pts[i]
        a1, r1 = pts[(i + 1) % n]
        k = max(1, int(math.ceil(max(abs(a1 - a0) / step_deg, abs(r1 - r0) / step_r))))
        out += [(a0 + (a1 - a0) * j / k, r0 + (r1 - r0) * j / k) for j in range(k)]
    return out


def _prisms(name, loops, z0, z1):
    """One cutter object holding a closed prism per (x, y) loop, from z0 to z1.
    The loops may be concave but must not cross themselves, and the prisms must
    not touch each other (one operand: an overlap empties the cut)."""
    import bmesh
    verts, faces = [], []
    for loop in loops:
        n = len(loop)
        b = len(verts)
        verts += [(x, y, z1) for (x, y) in loop] + [(x, y, z0) for (x, y) in loop]
        faces += [[b + i, b + n + i, b + n + (i + 1) % n, b + (i + 1) % n] for i in range(n)]
        faces.append(list(range(b, b + n)))
        faces.append(list(range(b + 2 * n - 1, b + n - 1, -1)))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _traced_face(name, collection, mat, d_face, big_r, sp, accent=None):
    """A dished closed face with windows cut through it, the outlines traced
    from photographs of the real wheel.

    sp is the spec's "spokes": count; depth (the face's thickness, metres);
    r_in, r_out (metres); windows and notches - closed polygons of ONE repeat
    in (angle in degrees, radius / big_r), turned `count` times round the
    wheel (windows are holes, notches take the edge of the face away between
    its tabs); lug_holes (deg, pcd, radius, count) - the nuts' counterbores;
    rings - extra radii (metres) to put a ring of vertices on; accent_r - the
    radius / big_r from which the top faces take the accent material; inlay -
    {mat, polys, lift}: outlines of one repeat that take another material (see
    _traced_inlay), built as a skin of their own.
    Angles count counter-clockwise, seen from outside, from 3 o'clock.
    """
    count = sp["count"]
    r_in, r_out = sp["r_in"], sp["r_out"]
    nr = sp.get("nr", 24)
    rings = sorted(set([r_in, r_out] + [r_in + (r_out - r_in) * i / float(nr) for i in range(nr + 1)]
                       + [r * big_r for r in sp.get("rings", ())]))
    prof = [(r, d_face(r)) for r in rings]
    v, f = M.revolve(prof, sp.get("seg", 72))
    ob = M.obj(name, v, f, collection, None)
    M.orient(ob.data, lambda c: (0.0, 0.0, 1.0))
    M.solidify(ob, sp["depth"], -1.0)
    step = 360.0 / count
    loops = []
    for k in range(count):
        a = step * k
        for poly in list(sp.get("windows", ())) + list(sp.get("notches", ())):
            pts = _densify([(t + a, r) for (t, r) in poly], sp.get("step_deg", 1.5), sp.get("step_r", 0.02))
            loops.append([_polar(t, r, big_r) for (t, r) in pts])
    lh = sp.get("lug_holes")
    if lh:
        deg, pcd, rad, n = lh["deg"], lh["pcd"], lh["r"], lh["count"]
        for k in range(n):
            a = math.radians(deg + 360.0 * k / n)
            cx, cy = pcd * math.cos(a), pcd * math.sin(a)
            loops.append([(cx + rad * math.cos(2 * math.pi * i / 20.0), cy + rad * math.sin(2 * math.pi * i / 20.0))
                          for i in range(20)])
    zs = [d for (_, d) in prof]
    cutter = _prisms("_cut_" + name, loops, min(zs) - sp["depth"] - 0.03, max(zs) + 0.03)
    C.difference(ob, [cutter], "win_", reset_materials=True)
    if not sp.get("solid"):
        # the back is never seen from outside: keep the face and the walls the cut made
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z < -0.3], context='FACES')
        bm.to_mesh(ob.data)
        bm.free()
        ob.data.update()
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    if accent is not None and sp.get("accent_r"):
        ob.data.materials.append(accent)
        r_acc = sp["accent_r"] * big_r
        for p in ob.data.polygons:
            c = p.center
            if p.normal.z > 0.45 and math.hypot(c.x, c.y) >= r_acc - 1e-6:
                p.material_index = 1
    return ob


def _traced_inlay(name, collection, mat, d_face, big_r, sp, inl):
    """A skin of the traced face's top surface inside some outlines, in another
    material: the machined wedges of a two-tone face. The outlines are polygons of
    one repeat like the windows (turned `count` times); they may run past the
    face's edge, where the skin stops, but must not touch a window. The skin is
    `lift` above the face so the two never fight over a pixel; nothing else of
    the solid is kept."""
    import bmesh
    count = sp["count"]
    r_in, r_out = sp["r_in"], sp["r_out"]
    nr = sp.get("nr", 24)
    rings = sorted(set([r_in, r_out] + [r_in + (r_out - r_in) * i / float(nr) for i in range(nr + 1)]
                       + [r * big_r for r in sp.get("rings", ())]))
    prof = [(r, d_face(r)) for r in rings]
    v, f = M.revolve(prof, sp.get("seg", 72))
    ob = M.obj(name, v, f, collection, None)
    M.orient(ob.data, lambda c: (0.0, 0.0, 1.0))
    M.solidify(ob, sp["depth"], -1.0)
    step = 360.0 / count
    loops = []
    for k in range(count):
        for poly in inl["polys"]:
            pts = _densify([(t + step * k, r) for (t, r) in poly], sp.get("step_deg", 1.5), sp.get("step_r", 0.02))
            loops.append([_polar(t, r, big_r) for (t, r) in pts])
    zs = [d for (_, d) in prof]
    cutter = _prisms("_inl_" + name, loops, min(zs) - sp["depth"] - 0.03, max(zs) + 0.03)
    b = ob.modifiers.new("inlay", 'BOOLEAN')
    b.operation = 'INTERSECT'
    b.solver = 'EXACT'
    try:
        b.use_hole_tolerant = True
    except Exception:
        pass
    b.object = cutter
    M.apply_modifiers(ob)
    C.weld(ob)
    cd = cutter.data
    bpy.data.objects.remove(cutter, do_unlink=True)
    if cd.users == 0:
        bpy.data.meshes.remove(cd)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z < 0.3], context='FACES')
    lift = inl.get("lift", 0.0004)
    for vt in bm.verts:
        vt.co.z += lift
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.material_index = 0
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
    # the face a left wheel shows from outside is the right wheel's turned half a revolution
    # (the local frame is): a design whose clocking is photographed sets roll_left
    roll = spec.get("roll_left", 0.0) if sign > 0 else 0.0
    ff = spec.get("flange_face", 0.011)         # radial width of the flange's visible face

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
        (rim_r - ff, d_flange),                     # flange face, inner edge
    ]
    v, f = M.revolve(barrel, seg)
    parts.append(M.obj(prefix + "RimBarrel_" + tag, v, f, collection, lib[mats.get("barrel", mats["rim"])]))

    flange = [
        (rim_r - ff, d_flange), (rim_r - 0.0005, d_flange),
        (rim_r + 0.0015, d_flange - 0.004), (rim_r + 0.0005, d_flange - 0.012),
    ]
    v, f = M.revolve(flange, seg)
    parts.append(M.obj(prefix + "RimFlange_" + tag, v, f, collection, lib[mats.get("lip", mats["rim"])]))

    if spec.get("pinstripe"):
        sr = spec.get("stripe_r", (0.0070, 0.0030))     # radial extent, metres inside the lip
        stripe = [(rim_r - sr[0], d_flange + 0.0004), (rim_r - sr[1], d_flange + 0.0004)]
        v, f = M.revolve(stripe, seg)
        parts.append(M.obj(prefix + "RimStripe_" + tag, v, f, collection,
                           lib[mats["stripe"]]))

    # --------------------------------------------------------------- face
    sp = spec["spokes"]
    style = sp["style"]
    mat_sp = lib[sp.get("mat", mats["rim"])]
    if style == "traced":
        # the same face for all four corners: built once, copied, turned by roll
        cache = spec.setdefault("_faces", {})
        src = cache.get("spokes")
        if src is None or bpy.data.objects.get(src.name) is not src:
            acc = lib[mats["accent"]] if "accent" in mats else None
            face = _traced_face(prefix + "Spokes_" + tag, collection, mat_sp, d_face, rim_r, sp, acc)
            M.bevel(face, sp.get("bevel", 0.0020), sp.get("bevel_segs", 1), 30, harden=True)
            cache["spokes"] = face
        else:
            face = src.copy()
            face.data = src.data.copy()
            face.name = prefix + "Spokes_" + tag
            face.parent = None
            collection.objects.link(face)
        face.rotation_euler = (0.0, 0.0, roll)
        parts.append(face)
        inl = sp.get("inlay")
        if inl:
            src = cache.get("inlay")
            if src is None or bpy.data.objects.get(src.name) is not src:
                skin = _traced_inlay(prefix + "Inlay_" + tag, collection, lib[inl["mat"]], d_face, rim_r, sp, inl)
                cache["inlay"] = skin
            else:
                skin = src.copy()
                skin.data = src.data.copy()
                skin.name = prefix + "Inlay_" + tag
                skin.parent = None
                collection.objects.link(skin)
            skin.rotation_euler = (0.0, 0.0, roll)
            parts.append(skin)
        rg = sp.get("ring")
        if rg:
            r0, r1 = rg["r_in"], rim_r - ff
            nrg = rg.get("rings", 6)
            prof = [(r0 + (r1 - r0) * i / float(nrg), d_flange - rg["dish"](r0 + (r1 - r0) * i / float(nrg)))
                    for i in range(nrg + 1)]
            v, f = M.revolve(prof, seg)
            ring = M.obj(prefix + "Ring_" + tag, v, f, collection, lib[rg.get("mat", "machined")])
            M.orient(ring.data, lambda c: (0.0, 0.0, 1.0))
            if rg.get("depth", 0.006) > 0.0:
                M.solidify(ring, rg.get("depth", 0.006), -1.0)
            parts.append(ring)
    elif style == "aero":
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

    cr = hub_spec.get("cap_rise", 0.0)
    kc = hub_spec.get("cap_r", 0.029) / 0.029
    cap = [(0.0, d_hub + 0.0055 + cr), (0.026 * kc, d_hub + 0.0055 + cr), (0.029 * kc, d_hub + 0.003 + cr),
           (0.029 * kc, d_hub)]
    v, f = M.revolve(cap, 32)
    parts.append(M.obj(prefix + "HubCap_" + tag, v, f, collection, lib[mats["cap"]]))

    # lug bolts in counterbores, between the spokes
    lg = spec["lugs"]
    nl = lg["count"]
    lugs = []
    for k in range(nl):
        a = 2.0 * math.pi * k / nl + sp["phase"] + math.pi / nl
        if "deg" in lg:
            a = math.radians(lg["deg"]) + 2.0 * math.pi * k / nl + roll
        cx, cy = lg["pcd_r"] * math.cos(a), lg["pcd_r"] * math.sin(a)
        ring = []
        for i in range(6):
            b = 2 * math.pi * i / 6
            ring.append((cx + lg["r"] * math.cos(b), cy + lg["r"] * math.sin(b)))
        z0 = d_hub - 0.001 + lg.get("rise", 0.0)
        if lg.get("dome"):
            # a round cap, domed: the SU7's black locking nuts
            h = lg["dome"] if isinstance(lg["dome"], float) else 0.0085
            rr = lg["r"]
            prof = [(0.0, h), (0.40 * rr, 0.97 * h), (0.70 * rr, 0.84 * h), (0.88 * rr, 0.58 * h),
                    (0.97 * rr, 0.22 * h), (rr, 0.0), (rr, -0.011)]
            vv, ff = M.revolve([(r_, z_) for (r_, z_) in prof], 20)
            vv = [(x + cx, y + cy, z + z0) for (x, y, z) in vv]
            lugs.append((vv, ff))
            continue
        vv = [(p[0], p[1], z0) for p in ring] + \
             [(p[0], p[1], z0 - 0.011) for p in ring] + [(cx, cy, z0)]
        ff = [[i, (i + 1) % 6, 6 + (i + 1) % 6, 6 + i] for i in range(6)]
        ff += [[12, i, (i + 1) % 6] for i in range(6)]
        lugs.append((vv, ff))
    v, f = M.merge_parts(lugs)
    parts.append(M.obj(prefix + "Lugs_" + tag, v, f, collection, lib[mats["lugs"]],
                       smooth=bool(lg.get("dome"))))

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
    # the rear calipers are smaller (4 pistons against 6): span_rear. r_inner is an
    # absolute inner radius - where the caliper's top, bulge and all, stays clear of
    # the face's top surface - instead of one hung from the disc's edge
    span = math.radians(cs.get("span_rear", cs.get("span_deg", 30.0)) if tag.startswith("R")
                        else cs.get("span_deg", 30.0))
    r0 = cs["r_inner"] if "r_inner" in cs else disc_r - cs.get("r_in", 0.058)
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
    # wound outwards: the first version came out inside-out, which a double-sided
    # material hides and an ambient-occlusion bake (carkit.bake) does not
    cfaces = [f[::-1] for f in cfaces]
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
    spec.pop("_faces", None)
    for tag, axle, sign, w, r, dr, cal, outer in corners:
        cy = sign * (outer - w / 2.0)
        made.append(build_wheel(collection, prefix, tag, (axle, cy, r), sign, lib,
                                spec, w, r, dr, cal))
    return made
