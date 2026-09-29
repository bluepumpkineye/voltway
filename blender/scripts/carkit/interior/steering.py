"""Steering wheels.

A wheel is built in its own frame and placed with one matrix:

    u   to the driver's right (world -Y for a wheel facing the driver)
    v   up the rim plane
    w   along the column axis, toward the driver

    rim       a closed sweep round a D-shaped loop (a circle clamped flat at
              the bottom, optionally at the top), elliptical section, thicker
              at the 9-and-3 grips. Split by ANGLE into trim segments - e.g.
              carbon top, Alcantara grips, carbon bottom - with a marker band
              at 12 o'clock.
    hub       a rounded polygon pad (the airbag cover), domed toward the driver
    spokes    horizontal side spokes carrying button pads; an optional lower
              V spoke
    buttons   round buttons (a drive-mode dial, a red boost button)

    wheel(collection, lib, spec, centre, tilt)  -> objects

spec (all metres/degrees; defaults: SU7 Ultra):
    radius          rim centreline radius
    flat_bottom     v of the flat bottom (None = round)
    flat_top        v of a flat top (None = round)
    section         (radial half-thickness, axial half-depth)
    segments        [(from_deg, to_deg, material role), ...] - angles
                    counter-clockwise from 3 o'clock, as the driver sees it
    marker          (centre_deg, half_width_deg, role) or None
"""
import math

from mathutils import Matrix, Vector

from .. import mesh as M
from .sweep import Sweep, cr_segments, grid_mesh, tube, ellipse, smooth_path

SU7_ULTRA = dict(
    radius=0.172, flat_bottom=-0.150, flat_top=None, section=(0.0145, 0.0175),
    grip_swell=0.12,
    segments=[(35.0, 145.0, "carbon"), (145.0, 222.0, "alcantara"),
              (222.0, 318.0, "carbon"), (318.0, 395.0, "alcantara")],
    marker=(90.0, 2.6, "leather_accent"),
    hub=dict(w=0.128, h=0.112, sides=8, r_corner=0.018, dome=0.006, depth=0.05),
    spokes=dict(v=-0.004, h=0.052, t=0.024, u_in=0.058, pad=(0.070, 0.040)),
    lower_spoke=dict(v_top=-0.052, half_gap=0.020, width=0.016),
    buttons=[(0.087, -0.057, 0.0125, "button_red"), (-0.072, -0.050, 0.0120, "brushed")],
    logo="XIAOMI",
)

# Luxeed RX, read through the solved cabin camera (rx_interior): a 376 mm
# leather rim with a flattened bottom, a ROUND hub pad in a chrome ring
# carrying the hexagon emblem, chrome-framed spoke pads with a roller each, a
# U-shaped brushed lower spoke widening to the rim, and the BOOST button
# (chrome ring) below the right spoke.
LUXEED_RX = dict(
    radius=0.170, flat_bottom=-0.150, flat_top=None, section=(0.0175, 0.0210),
    grip_swell=0.10,
    segments=[(0.0, 180.0, "leather_black"), (180.0, 360.0, "leather_black")],
    marker=None,
    hub=dict(w=0.128, h=0.128, sides=36, r_corner=0.0, dome=0.009, depth=0.05, ring="chrome"),
    spokes=dict(v=0.0, h=0.062, t=0.024, u_in=0.062, pad=(0.098, 0.062), frame="chrome",
                pad_role="gunmetal"),
    lower_spoke=dict(v_top=-0.078, half_gap=0.022, width=0.024, bottom_half=0.036),
    buttons=[(0.083, -0.081, 0.0125, "satin", "chrome")],
    logo=None,
    emblem=dict(w=0.026, h=0.060, role="chrome"),
)


def _loop_ctrl(R, flat_bottom, flat_top, n=48):
    pts = []
    for k in range(n):
        a = 2.0 * math.pi * k / n
        u, v = R * math.cos(a), R * math.sin(a)
        if flat_bottom is not None and v < flat_bottom:
            v = flat_bottom
        if flat_top is not None and v > flat_top:
            v = flat_top
        pts.append((u, v))
    return pts


class WheelFrame:
    def __init__(self, centre, tilt, facing=(-1.0, 0.0, 0.0)):
        """centre: rim centre; tilt: rim plane back from vertical (radians).
        facing: the horizontal direction the wheel faces (toward the driver)."""
        f = Vector(facing).normalized()
        self.A = (f * math.cos(tilt) + Vector((0, 0, 1)) * math.sin(tilt)).normalized()
        self.V = (-f * math.sin(tilt) + Vector((0, 0, 1)) * math.cos(tilt)).normalized()
        self.U = self.V.cross(self.A).normalized()
        self.C = Vector(centre)

    def p(self, u, v, w=0.0):
        return tuple(self.C + self.U * u + self.V * v + self.A * w)


def rim(fr, spec, collection, lib, name="int_wheel_rim", ns=192):
    R = spec["radius"]
    ctrl = _loop_ctrl(R, spec.get("flat_bottom"), spec.get("flat_top"))
    loop2d = smooth_path([(u, v, 0.0) for (u, v) in ctrl], ns, closed=True)
    ang = [math.degrees(math.atan2(p[1], p[0])) % 360.0 for p in loop2d]
    rr, dd = spec["section"]
    swell = spec.get("grip_swell", 0.0)

    def section(i, s):
        a = math.radians(ang[i])
        k = 1.0 + swell * (math.cos(a) ** 8)          # fatter at 9 and 3
        return [(dd * k * math.cos(2 * math.pi * j / 16), rr * k * math.sin(2 * math.pi * j / 16))
                for j in range(16)]
    path = [fr.p(u, v) for (u, v, _) in loop2d]
    sw = Sweep(path, section, ns, 1, lateral=tuple(fr.A), closed_spine=True,
               closed_section=True, spine_is_path=True)
    made = []

    def rng(a0, a1):
        idx = [i for i in range(ns) if (a0 <= ang[i] < a1) or (a0 <= ang[i] + 360.0 < a1)]
        return idx

    for k, (a0, a1, role) in enumerate(spec["segments"]):
        idx = rng(a0, a1)
        if not idx:
            continue
        # contiguous run (it may wrap through 0)
        idx.sort()
        if idx[0] == 0 and idx[-1] == ns - 1:
            gap = next(j for j in range(1, len(idx)) if idx[j] != idx[j - 1] + 1)
            idx = idx[gap:] + idx[:gap]
        rows = [sw.pts[i] for i in idx] + [sw.pts[(idx[-1] + 1) % ns]]
        ob = grid_mesh("%s_%d" % (name, k), rows, collection, lib[role], wrap_t=True)
        _outward(ob, path)
        made.append(ob)
    if spec.get("marker"):
        mc, mw, role = spec["marker"]
        idx = [i for i in range(ns) if abs(((ang[i] - mc + 180.0) % 360.0) - 180.0) <= mw]
        idx.sort()
        rows = [[tuple(Vector(p) + (Vector(p) - Vector(path[i])).normalized() * 0.0007)
                 for p in sw.pts[i]] for i in idx]
        ob = grid_mesh(name + "_marker", rows, collection, lib[role], wrap_t=True)
        _outward(ob, path)
        made.append(ob)
    return made


def _outward(ob, path):
    me = ob.data
    c = Vector((0, 0, 0))
    for p in path:
        c += Vector(p)
    score = 0.0
    for poly in me.polygons:
        # nearest spine point
        q = min(path, key=lambda p: (Vector(p) - poly.center).length_squared)
        score += Vector(poly.normal).dot(poly.center - Vector(q))
    if score < 0:
        me.flip_normals()
        me.update()


def _rounded_polygon(w, h, sides, r, n=4):
    """A rounded regular-ish polygon inscribed in a w x h ellipse."""
    pts = []
    for k in range(sides):
        a = 2 * math.pi * (k + 0.5) / sides
        pts.append((0.5 * w * math.cos(a), 0.5 * h * math.sin(a)))
    return [(p[0], p[1]) for p in cr_segments(pts, n, closed=True, alpha=0.5)]


def hub(fr, spec, collection, lib, name="int_wheel_hub", logo_mat=None):
    h = spec["hub"]
    outline = _rounded_polygon(h["w"], h["h"], h["sides"], h["r_corner"], n=5)
    made = []
    # the pad: rings from the outline in to the centre, domed toward the driver
    rings = []
    for k in range(7):
        s = 1.0 - k / 6.0
        dome = h["dome"] * (1.0 - s ** 2.2)
        rings.append([fr.p(u * s, v * s, 0.020 + dome) for (u, v) in outline])
    rings[-1] = [fr.p(0.0, 0.0, 0.020 + h["dome"])] * len(outline)
    pad = grid_mesh(name + "_pad", rings, collection, lib["leather_black"], wrap_t=True)
    M.orient(pad.data, lambda c: tuple(fr.A))
    made.append(pad)
    # the housing behind the pad, stepping back to the column
    back = []
    for k, (s, w) in enumerate(((1.0, 0.020), (1.04, 0.012), (1.06, -0.004), (0.9, -0.030),
                                (0.55, -h["depth"]))):
        back.append([fr.p(u * s, v * s, w) for (u, v) in outline])
    hs = grid_mesh(name + "_housing", back, collection, lib["piano"], wrap_t=True)
    _outward(hs, [fr.p(0, 0, w) for w in (0.02, 0.0, -0.03, -0.05)])
    made.append(hs)
    if h.get("ring"):
        # a chrome ring round the pad's edge (Luxeed RX)
        path = [fr.p(u * 1.02, v * 1.02, 0.0215) for (u, v) in outline]
        path.append(path[0])
        made.append(tube(name + "_ring", path, ellipse(0.0026, 0.0026, 8), collection,
                         lib[h["ring"]], lateral=tuple(fr.A)))
    return made


def spokes(fr, spec, collection, lib, name="int_wheel_spoke"):
    sp = spec["spokes"]
    R = spec["radius"]
    made = []
    for side, tag in ((1.0, "R"), (-1.0, "L")):
        # a flat member from the hub to the rim, thickening toward the rim
        rows = []
        for k in range(9):
            t = k / 8.0
            u = side * (sp["u_in"] + (R - 0.010 - sp["u_in"]) * t)
            hh = 0.5 * sp["h"] * (1.0 - 0.35 * t)
            prof = [(-hh, -0.004), (-hh * 0.9, 0.010), (0.0, 0.014), (hh * 0.9, 0.010),
                    (hh, -0.004), (hh * 0.8, -sp["t"]), (-hh * 0.8, -sp["t"])]
            rows.append([fr.p(u, sp["v"] + a, 0.004 + b) for (a, b) in prof])
        ob = grid_mesh("%s_%s" % (name, tag), rows, collection, lib["piano"], wrap_t=True)
        M.orient(ob.data, lambda c: tuple(fr.A))
        made.append(ob)
        # the button pad on the spoke face, and its centre toggle
        pw, ph = sp["pad"]
        uc = side * (sp["u_in"] + 0.5 * pw + 0.004)
        pad = [fr.p(uc + a, sp["v"] + b, 0.0195) for (a, b) in
               _rounded_polygon(pw, ph, 4, 0.01, n=5)]
        centre = fr.p(uc, sp["v"], 0.0205)
        verts = [centre] + pad
        faces = [[0, 1 + j, 1 + (j + 1) % len(pad)] for j in range(len(pad))]
        pd = M.obj("%s_%s_pad" % (name, tag), verts, faces, collection,
                   lib[sp.get("pad_role", "satin")])
        M.orient(pd.data, lambda c: tuple(fr.A))
        made.append(pd)
        if sp.get("frame"):
            fp = [fr.p(uc + a, sp["v"] + b, 0.0200) for (a, b) in
                  _rounded_polygon(pw + 0.006, ph + 0.006, 4, 0.01, n=5)]
            fp.append(fp[0])
            made.append(tube("%s_%s_frame" % (name, tag), fp, ellipse(0.0025, 0.0025, 8),
                             collection, lib[sp["frame"]], lateral=tuple(fr.A)))
        tg = [fr.p(uc + a, sp["v"] + b, 0.0232) for (a, b) in
              _rounded_polygon(0.018, 0.007, 4, 0.002, n=3)]
        verts = [fr.p(uc, sp["v"], 0.0235)] + tg
        faces = [[0, 1 + j, 1 + (j + 1) % len(tg)] for j in range(len(tg))]
        tb = M.obj("%s_%s_toggle" % (name, tag), verts, faces, collection, lib["brushed"])
        M.orient(tb.data, lambda c: tuple(fr.A))
        made.append(tb)
    ls = spec.get("lower_spoke")
    if ls:
        # a brushed V from under the hub to the flat bottom of the rim
        vb = spec.get("flat_bottom") or -R
        # legs converge to the rim (a V), or with bottom_half widen to it (a U)
        bh = ls.get("bottom_half", 0.008)
        mid = ls["half_gap"] * 0.7 if "bottom_half" not in ls else 0.5 * (ls["half_gap"] + bh)
        for side in (1.0, -1.0):
            path = smooth_path([fr.p(side * ls["half_gap"], ls["v_top"], 0.010),
                                fr.p(side * mid, 0.5 * (ls["v_top"] + vb), 0.007),
                                fr.p(side * bh, vb + 0.004, 0.003)], 12)
            # a flat brushed leg: wide across the face, thin front to back
            made.append(tube("%s_V%s" % (name, "R" if side > 0 else "L"), path,
                             [(a * 0.0045, b * ls["width"] * 0.55) for (a, b) in ellipse(1, 1, 12)],
                             collection, lib["brushed"], lateral=tuple(fr.A)))
        if "bottom_half" in ls:
            # a U: a bar along the rim's flat bottom joins the legs
            bar = [fr.p(-bh + 2 * bh * t / 10.0, vb + 0.004, 0.003) for t in range(11)]
            made.append(tube("%s_Vbar" % name, bar, [(a * 0.0045, b * 0.0065) for (a, b) in
                                                     ellipse(1, 1, 12)],
                             collection, lib["brushed"], lateral=tuple(fr.A)))
        badge = [fr.p(a, vb + 0.012 + b, 0.009) for (a, b) in
                 _rounded_polygon(0.020, 0.012, 4, 0.002, n=3)]
        verts = [fr.p(0.0, vb + 0.012, 0.0095)] + badge
        faces = [[0, 1 + j, 1 + (j + 1) % len(badge)] for j in range(len(badge))]
        bd = M.obj(name + "_badge", verts, faces, collection, lib["leather_accent"])
        M.orient(bd.data, lambda c: tuple(fr.A))
        made.append(bd)
    return made


def buttons(fr, spec, collection, lib, name="int_wheel_button"):
    made = []
    for k, btn in enumerate(spec.get("buttons", [])):
        u, v, r, role = btn[:4]

        def ring(s, w):
            return [fr.p(u + s * r * math.cos(2 * math.pi * j / 24),
                         v + s * r * math.sin(2 * math.pi * j / 24), w) for j in range(24)]
        # a gloss pod the button sits in, then a flat cap with a small chamfer
        pod = grid_mesh("%s_%d_pod" % (name, k),
                        [ring(1.75, -0.004), ring(1.75, 0.010), ring(1.55, 0.0135),
                         ring(1.25, 0.0140)], collection, lib["piano"], wrap_t=True)
        M.orient(pod.data, lambda c: tuple(fr.A))
        made.append(pod)
        cap = grid_mesh("%s_%d" % (name, k),
                        [ring(1.18, 0.0138), ring(1.18, 0.0168), ring(1.05, 0.0180),
                         ring(0.9, 0.0182), ring(0.0, 0.0183)], collection, lib[role],
                        wrap_t=True)
        M.orient(cap.data, lambda c: tuple(fr.A))
        made.append(cap)
        if len(btn) > 4:
            # a bright ring round the cap (the RX's BOOST button)
            path = ring(1.22, 0.0170)
            path.append(path[0])
            made.append(tube("%s_%d_ring" % (name, k), path, ellipse(0.0016, 0.0016, 8),
                             collection, lib[btn[4]], lateral=tuple(fr.A)))
    return made


def emblem(fr, spec, collection, lib, name="int_wheel_emblem"):
    """The Luxeed emblem: an elongated hexagon, pointed top and bottom, with
    a bar across its waist and an X inside, as a raised chrome outline on the
    hub pad."""
    e = spec["emblem"]
    w, h = e["w"], e["h"]
    lift = 0.0215 + spec["hub"]["dome"] * 0.97
    hexa = [(0.0, h / 2), (w / 2, h / 4), (w / 2, -h / 4), (0.0, -h / 2), (-w / 2, -h / 4),
            (-w / 2, h / 4)]
    prof = ellipse(0.0011, 0.0011, 6)
    made = []
    path = [fr.p(a, b, lift) for (a, b) in hexa] + [fr.p(hexa[0][0], hexa[0][1], lift)]
    dense = []
    for i in range(len(path) - 1):
        A, B = Vector(path[i]), Vector(path[i + 1])
        dense += [tuple(A.lerp(B, t / 6.0)) for t in range(6)]
    dense.append(path[-1])
    made.append(tube(name, dense, prof, collection, lib[e["role"]], lateral=tuple(fr.A)))
    for k, (a, b) in enumerate((((-w / 2, h / 4), (w / 2, -h / 4)), ((w / 2, h / 4), (-w / 2, -h / 4)),
                                ((-w / 2, 0.0), (w / 2, 0.0)))):
        A, B = Vector(fr.p(a[0], a[1], lift)), Vector(fr.p(b[0], b[1], lift))
        made.append(tube("%s_bar%d" % (name, k), [tuple(A.lerp(B, t / 8.0)) for t in range(9)],
                         prof, collection, lib[e["role"]], lateral=tuple(fr.A)))
    return made


def column(fr, collection, lib, length=0.20, name="int_wheel_column"):
    """The column shroud from behind the hub toward the dash."""
    path = [fr.p(0.0, -0.01, -0.03 - length * k / 8.0) for k in range(9)]
    prof = [(a * 0.055, b * 0.045) for (a, b) in ellipse(1, 1, 16)]
    return [tube(name, path, prof, collection, lib["satin"], lateral=tuple(fr.V),
                 scale=lambda s: (1.0 + 0.25 * s, 1.0 + 0.3 * s))]


def logo(fr, text, collection, mat, size=0.013, name="int_wheel_logo"):
    t = M.text_mesh(name, text, size, collection, mat, extrude=0.0003)
    # lay it on the pad, facing the driver, reading left to right (U, V, A is
    # right-handed: U x V = A)
    Mx = Matrix((tuple(fr.U), tuple(fr.V), tuple(fr.A))).transposed().to_4x4()
    Mx.translation = Vector(fr.p(0.0, 0.004, 0.0325))
    t.matrix_world = Mx
    return [t]


def wheel(collection, lib, spec, centre, tilt, facing=(-1.0, 0.0, 0.0)):
    fr = WheelFrame(centre, tilt, facing)
    made = []
    made += rim(fr, spec, collection, lib)
    made += hub(fr, spec, collection, lib)
    made += spokes(fr, spec, collection, lib)
    made += buttons(fr, spec, collection, lib)
    made += column(fr, collection, lib)
    if spec.get("logo"):
        made += logo(fr, spec["logo"], collection, lib["gunmetal"])
    if spec.get("emblem"):
        made += emblem(fr, spec, collection, lib)
    return made, fr
