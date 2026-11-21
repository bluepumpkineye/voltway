"""XPeng Mona L05 steering wheel, rebuilt from the photographs (2026-11-21), the way a06t_wheel.py was built for the 06T.

Read from the Cabin 360 FRONT panorama (the camera at the driver's head, square on to the wheel: `pano.cjs view <pano> out.png 0
-22 56 1600 2`, 28.6 px per degree, about 8.7 mm per degree at the wheel) and the Autohome close-ups c10_0009 (the whole wheel),
c10_0002 and c10_0016 (the pods and the buttons), measured from the rim's centre:

    rim        grey fabric, 0.300 wide x 0.254 high outside, a rounded rectangle: the upper half domed (the arch is wide), the lower
               half flatter; 29-31 mm thick at the top and the sides, 37 mm at the bottom; a silver clamp (15 mm) round the
               bottom; a seam across each lower corner and fine tone-on-tone stitching along the inner edge
    hub        a soft pillow, 0.124 wide x 0.104 high, its centre 22 mm below the rim's: the XPENG X (silver) on it and the word
               AIRBAG small under it
    pods       a silver-framed rounded rectangle on each side (53 x 38 mm, centre u +-88 mm, v -5 mm): a grey pad with a knurled
               silver pill roller and a chevron at each end. The pod is the spoke: it joins the hub to the rim
    buttons    under each pod, a black glass rounded square (25 mm) in a silver ring on a grey boss (u +-73 mm, v -49 mm): the
               cruise key on the left, MODE on the right
    stalks     short and dark behind the pods, a pale tip showing above each (c10_0009: u +-104 mm, v +23 mm)

Wheel frame: u to the driver's right, v up the rim plane, w toward the driver (steering.WheelFrame).
"""
import math

import bpy
from mathutils import Vector

from carkit import mesh as M
from carkit.interior import fittings as F
from carkit.interior.sweep import Sweep, grid_mesh, tube, ellipse, resample, stitches, piping

# ------------------------------------------------------------------ the rim
RIM_A, RIM_B = 0.1345, 0.1115                  # the centreline's half width and half height
N_TOP, N_BOT = 2.7, 3.9                        # superellipse exponents of the upper and the lower half
RIM_R_TOP, RIM_R_SIDE, RIM_R_BOT = 0.0145, 0.0155, 0.0185      # the section's radial half size round the rim
RIM_D = 0.0175                                 # and its axial half size
CLAMP_HALF = 0.0095                            # the silver clamp on the bottom (half its length along the rim)
SEAM_U = 0.082                                 # the seam across each lower corner: where the lower rim reaches |u|

# ------------------------------------------------------------------ the hub
HUB_A, HUB_B, HUB_N, HUB_V = 0.062, 0.052, 3.0, -0.022
HUB_RINGS = [(1.000, 0.0100), (0.988, 0.0215), (0.962, 0.0300), (0.915, 0.0345), (0.80, 0.0368), (0.58, 0.0382),
             (0.28, 0.0390), (0.0, 0.0393)]
HUB_TOP = HUB_RINGS[-1][1]

# ------------------------------------------------------------------ the pods and buttons
POD_UV = (0.088, -0.006)                       # centre of each pod
POD_W, POD_H = 0.053, 0.038                    # the silver frame's outside
POD_FRAME = 0.0062                             # its width
POD_Z = 0.0250                                 # the frame's crest
BTN_UV = (0.073, -0.049)                       # the lower buttons


def _squircle(count):
    dense = []
    m = count * 4
    for k in range(m):
        t = 2.0 * math.pi * k / m
        c, s = math.cos(t), math.sin(t)
        n = N_TOP if s >= 0.0 else N_BOT
        dense.append((RIM_A * math.copysign(abs(c) ** (2.0 / n), c), RIM_B * math.copysign(abs(s) ** (2.0 / n), s), 0.0))
    return resample(dense, count, closed=True)


def _fbox(fr, col, name, c, size, mat, r=0.002):
    """A bevelled block in the wheel's frame: centre (u, v, w), size (du, dv, dw)."""
    hu, hv, hw = size[0] / 2, size[1] / 2, size[2] / 2
    pts = [(-hu, -hv, -hw), (hu, -hv, -hw), (hu, hv, -hw), (-hu, hv, -hw),
           (-hu, -hv, hw), (hu, -hv, hw), (hu, hv, hw), (-hu, hv, hw)]
    verts = [fr.p(c[0] + p[0], c[1] + p[1], c[2] + p[2]) for p in pts]
    faces = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    ob = M.obj(name, verts, faces, col, mat, smooth=False)
    M.orient(ob.data, lambda q: tuple(Vector(q) - Vector(fr.p(*c))))
    if r > 0:
        M.bevel(ob, r, 3, 40)
    return ob


def _rrect(w, h, r, n=6):
    return F.round_rect_xy(-w / 2, w / 2, -h / 2, h / 2, r, n)


def _wheel_thread():
    """Tone-on-tone thread for the rim: a step lighter than the grey fabric (c10_0009: a fine grey stitch, not a white one)."""
    m = bpy.data.materials.get("INT_Thread_Wheel")
    if m is None:
        from carkit import materials as MB
        m, nt, b = MB.mat("INT_Thread_Wheel")
        MB.set_inputs(b, base=(0.085, 0.090, 0.100), metallic=0.0, roughness=0.65)
    return m


def _dark_thread():
    m = bpy.data.materials.get("INT_Thread_Dark")
    if m is None:
        from carkit import materials as MB
        m, nt, b = MB.mat("INT_Thread_Dark")
        MB.set_inputs(b, base=(0.011, 0.011, 0.014), metallic=0.0, roughness=0.7)
    return m


def _outward(ob, path):
    me = ob.data
    score = 0.0
    for poly in me.polygons:
        q = min(path, key=lambda p: (Vector(p) - poly.center).length_squared)
        score += Vector(poly.normal).dot(poly.center - Vector(q))
    if score < 0:
        me.flip_normals()
        me.update()


# ------------------------------------------------------------------ rim
def build_rim(fr, col, lib):
    ns = 216
    path2 = _squircle(ns)
    phi = [math.degrees(math.atan2(p[1] / RIM_B, p[0] / RIM_A)) % 360.0 for p in path2]
    path = [fr.p(u, v) for (u, v, _) in path2]

    def sec(i, s):
        sn = math.sin(math.radians(phi[i]))
        rr = RIM_R_SIDE + (RIM_R_TOP - RIM_R_SIDE) * max(0.0, sn) + (RIM_R_BOT - RIM_R_SIDE) * max(0.0, -sn) ** 1.5
        e = 2.0 / 2.6
        out = []
        for j in range(28):
            t = 2.0 * math.pi * j / 28
            c, sh = math.cos(t), math.sin(t)
            out.append((RIM_D * math.copysign(abs(c) ** e, c), rr * math.copysign(abs(sh) ** e, sh)))
        return out

    sw = Sweep(path, sec, ns, 1, lateral=tuple(fr.A), closed_spine=True, closed_section=True, spine_is_path=True)
    rows = sw.rows()
    low = sorted(i for i in range(ns) if path2[i][1] < 0 and abs(path2[i][0]) <= CLAMP_HALF)
    i_a, i_b = low[0], low[-1]
    made = []
    leather = rows[i_b:] + rows[:i_a + 1]
    ob = grid_mesh("int_wheel_rim", leather, col, lib["wheel_fabric"], wrap_t=True)
    _outward(ob, path)
    made.append(ob)
    # the silver clamp: the section's own rows in satin silver, 0.6 mm bigger (a sleeve)
    big = [[tuple(Vector(p) + (Vector(p) - Vector(path[i])).normalized() * 0.0006) for p in rows[i]]
           for i in range(i_a, i_b + 1)]
    cl = grid_mesh("int_wheel_clamp", big, col, lib["silver_satin"], wrap_t=True)
    _outward(cl, path)
    made.append(cl)
    thread = _dark_thread()

    def tangent(k):
        return tuple(Vector(path[(k + 1) % ns]) - Vector(path[k - 1]))

    rings = [i_a - 1, i_b + 1]
    # a seam across each lower corner (where the flat bottom turns up the side)
    for sgn in (1.0, -1.0):
        k = min((i for i in range(ns) if path2[i][1] < 0 and sgn * path2[i][0] > 0), key=lambda i: abs(abs(path2[i][0]) - SEAM_U))
        rings.append(k)
    for k in rings:
        ring = list(rows[k % ns]) + [rows[k % ns][0]]
        made.append(piping("int_wheel_rim_seam%d" % k, ring, col, thread, r=0.0007, lateral=tangent(k % ns)))
    # fine tone-on-tone stitching along the inner edge, on the driver's face
    pts, nrm = [], []
    for i in range(ns + 1):
        u, v, _ = path2[i % ns]
        L = math.hypot(u, v)
        sn = math.sin(math.radians(phi[i % ns]))
        rr = RIM_R_SIDE + (RIM_R_TOP - RIM_R_SIDE) * max(0.0, sn) + (RIM_R_BOT - RIM_R_SIDE) * max(0.0, -sn) ** 1.5
        k_in = (L - rr * 0.58) / L
        pts.append(fr.p(u * k_in, v * k_in, RIM_D * 0.91 + 0.0003))
        nrm.append(tuple(fr.A))
    made.append(stitches("int_wheel_Stitch", pts, nrm, col, _wheel_thread(), stitch=0.0032, gap=0.0018, width=0.0010))
    return made


# ------------------------------------------------------------------ hub
def _hub_outline(n=80):
    out = []
    pts = []
    m = n * 4
    for k in range(m):
        t = 2.0 * math.pi * k / m
        c, s = math.cos(t), math.sin(t)
        pts.append((HUB_A * math.copysign(abs(c) ** (2.0 / HUB_N), c), HUB_B * math.copysign(abs(s) ** (2.0 / HUB_N), s), 0.0))
    return [(p[0], p[1]) for p in resample(pts, n, closed=True)]


def build_hub(fr, col, lib):
    outline = _hub_outline()
    rings = [[fr.p(u * s, HUB_V + v * s, w) for (u, v) in outline] for (s, w) in HUB_RINGS]
    rings[-1] = [rings[-1][0]] * len(outline)
    pad = grid_mesh("int_wheel_hub_pad", rings, col, lib["wheel_fabric"], wrap_t=True)
    M.orient(pad.data, lambda c: tuple(fr.A))
    made = [pad]
    back = []
    for s, w in ((1.0, 0.0100), (1.03, 0.0040), (1.04, -0.0080), (0.90, -0.0280), (0.55, -0.0500)):
        back.append([fr.p(u * s, HUB_V + v * s, w) for (u, v) in outline])
    hb = grid_mesh("int_wheel_hub_housing", back, col, lib["dash_lav"], wrap_t=True)
    M.orient(hb.data, lambda c: tuple(fr.A))
    made.append(hb)
    # the XPENG X and the AIRBAG mark under it
    import mona_interior as MI
    made += MI.build_wheel_emblem(fr, col, lib, v_off=-0.003, w_off=HUB_TOP + 0.0006)
    t = M.text_mesh("int_wheel_airbag", "AIRBAG", 0.0042, col, lib["silver_satin"], extrude=0.0002, resolution=3)
    U, V, N = Vector(fr.U), Vector(fr.V), Vector(fr.A)
    from mathutils import Matrix
    Mx = Matrix((tuple(U), tuple(V), tuple(N))).transposed().to_4x4()
    Mx.translation = Vector(fr.p(-0.0105, -0.0325, HUB_TOP - 0.0004))
    t.matrix_world = Mx
    made.append(t)
    return made


# ------------------------------------------------------------------ pods and buttons
def build_pods(fr, col, lib):
    made = []
    for side, tag in ((-1.0, "L"), (1.0, "R")):
        uc, vc = side * POD_UV[0], POD_UV[1]
        # the spoke: a grey block from the hub's side into the rim
        made.append(_fbox(fr, col, "int_wheel_spoke" + tag, (side * 0.092, vc, 0.0060), (0.066, 0.042, 0.026),
                          lib["wheel_fabric"], r=0.006))
        # the silver frame: a flat annulus with soft edges (outer edge, crest, inner edge), 6 mm wide
        outer = _rrect(POD_W, POD_H, 0.011)
        crest = _rrect(POD_W - 0.0034, POD_H - 0.0034, 0.0098)
        inner = _rrect(POD_W - 2 * POD_FRAME, POD_H - 2 * POD_FRAME, 0.0070)
        loops = [(outer, POD_Z - 0.0040), (outer, POD_Z - 0.0012), (crest, POD_Z), (inner, POD_Z - 0.0012),
                 (inner, POD_Z - 0.0042)]
        rows = [[fr.p(uc + a, vc + b, w) for (a, b) in lp] for (lp, w) in loops]
        fm = grid_mesh("int_wheel_podframe" + tag, rows, col, lib["silver_satin"], wrap_t=True)
        M.orient(fm.data, lambda c: tuple(fr.A))
        made.append(fm)
        # the pad inside it: the wheel's grey, a touch recessed
        pad = [fr.p(uc + a, vc + b, POD_Z - 0.0050) for (a, b) in _rrect(POD_W - 2 * POD_FRAME + 0.001, POD_H - 2 * POD_FRAME + 0.001, 0.0066)]
        made.append(F.ngon_cap(col, "int_wheel_podpad" + tag, pad, lib["wheel_fabric"], tuple(fr.A)))
        # the knurled silver pill roller, and its grooves
        made.append(_fbox(fr, col, "int_wheel_roller" + tag, (uc, vc, POD_Z - 0.0042), (0.0205, 0.0098, 0.0064),
                          lib["silver_satin"], r=0.0030))
        for k in range(5):
            xk = uc + (k - 2) * 0.0034
            ln = [fr.p(xk, vc + 0.0036, POD_Z + 0.0001), fr.p(xk, vc - 0.0036, POD_Z + 0.0001)]
            made.append(tube("int_wheel_knurl%s%d" % (tag, k), ln, ellipse(0.0003, 0.0003, 4), col, _dark_thread(),
                             lateral=tuple(fr.A)))
    return made


def build_buttons(fr, col, lib):
    """The lower button on each side: a black glass rounded square in a silver ring, on a grey boss."""
    made = []
    for side, tag in ((-1.0, "L"), (1.0, "R")):
        uc, vc = side * BTN_UV[0], BTN_UV[1]
        made.append(_fbox(fr, col, "int_wheel_boss" + tag, (uc, vc + 0.004, 0.0010), (0.038, 0.034, 0.028),
                          lib["wheel_fabric"], r=0.010))
        ring = [fr.p(uc + a, vc + b, 0.0158) for (a, b) in _rrect(0.0250, 0.0230, 0.0085)]
        made.append(tube("int_wheel_btnring" + tag, ring + [ring[0]], ellipse(0.0016, 0.0013, 8), col, lib["silver_satin"],
                         lateral=tuple(fr.A)))
        face = [fr.p(uc + a, vc + b, 0.0166) for (a, b) in _rrect(0.0222, 0.0202, 0.0075)]
        made.append(F.ngon_cap(col, "int_wheel_btnface" + tag, face, lib["piano"], tuple(fr.A)))
    return made


# ------------------------------------------------------------------ column and stalks
def build_column(fr, col, lib):
    path = [fr.p(0.0, -0.030, -0.034 - 0.200 * k / 8.0) for k in range(9)]
    return [tube("int_wheel_column", path, [(a * 0.034, b * 0.028) for (a, b) in ellipse(1, 1, 16)], col, lib["dash_lav"],
                 lateral=tuple(fr.V), scale=lambda s: (1.0 + 0.15 * s, 1.0 + 0.2 * s))]


def build_stalks(fr, col, lib):
    """Two short dark stalks behind the pods, a pale tip showing above each (c10_0009)."""
    made = []
    for side, tag in ((-1.0, "L"), (1.0, "R")):
        a = Vector(fr.p(side * 0.036, 0.012, -0.046))
        b = Vector(fr.p(side * 0.102, 0.026, -0.030))
        d = (b - a).normalized()
        path = [tuple(a.lerp(b, t / 10.0)) for t in range(11)]
        made.append(tube("int_wheel_stalk" + tag, path, ellipse(0.0090, 0.0100, 14), col, lib["dash_lav"],
                         lateral=tuple(fr.A), scale=lambda s: (1.0 - 0.14 * s, 1.0 - 0.18 * s)))
        tip = [tuple(b + d * (-0.002 + 0.015 * t / 4.0)) for t in range(5)]
        made.append(tube("int_wheel_stalkTip" + tag, tip, ellipse(0.0064, 0.0078, 12), col, lib["silver_satin"],
                         lateral=tuple(fr.A)))
    return made


# ------------------------------------------------------------------ the wheel
def build(col, lib, centre, tilt):
    from carkit.interior import steering as ST
    fr = ST.WheelFrame(centre, tilt)
    made = []
    made += build_rim(fr, col, lib)
    made += build_hub(fr, col, lib)
    made += build_pods(fr, col, lib)
    made += build_buttons(fr, col, lib)
    made += build_column(fr, col, lib)
    made += build_stalks(fr, col, lib)
    return made, fr
