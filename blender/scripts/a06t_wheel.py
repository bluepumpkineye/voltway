"""Avatr 06T steering wheel, rebuilt from the photographs (c10_0008 square on, c10_0009..0012 the hub and the frame,
c10_0013 / c10_0014 the stalks, c10_0001 and c10_0006 for where it sits).

The photograph c10_0008 is 2.56 px/mm at the wheel (rim 985 x 690 px), so every figure below is read off it:

    rim        a wide, low squircle with a flat, slightly crowned top and a flat bottom: 0.385 x 0.270 outside, a fat
               section (36 x 33 mm at the grips, 33 mm on the flats), a thumb contour at 10 and 2 o'clock, and a seam
               across the leather where each flat meets a side grip. The rim's bottom is not leather: the satin frame's
               base is part of the rim there (a sleeve, 76 mm wide).
    frame      ONE satin champagne-silver plate: it arches over the top of the hub, runs out to a horizontal spoke on
               each side (the control pod, with the roller in an oval bezel), and angles down either side of the hub into
               a wide trapezoid that ends in the sleeve, a rounded-triangle cut-out under the hub. Two small windows
               (dark, with a satin button in each) separate the hub from the pods.
    hub        a softly rounded octagonal cushion 0.136 across, a recessed inner ring with tone-on-tone dark stitching,
               and the Avatr badge: a vertical rectangle, four metallic facets sloping to the middle.
    stalks     short, thick, dark, tucked behind the spokes, a satin tip each (c10_0013).

Wheel frame: u to the driver's right (world -Y), v up the rim plane, w toward the driver (steering.WheelFrame).
"""
import math

import bmesh
import bpy
from mathutils import Vector, geometry

from carkit import mesh as M
from carkit.interior import fittings as F
from carkit.interior.sweep import Sweep, grid_mesh, tube, ellipse, resample, stitches, piping, smooth_path

# ------------------------------------------------------------------ the rim
RIM_A, RIM_B, RIM_N = 0.1745, 0.1195, 3.6          # the centreline: a superellipse, half-width, half-height, exponent
RIM_R_SIDE, RIM_R_FLAT, RIM_D = 0.0185, 0.0165, 0.0165      # section half sizes: radial (grips / flats), axial
SLEEVE_HALF = 0.038                                # the frame's base, set into the rim's bottom (half width)
THUMB_DEG = (40.0, 140.0)                          # the thumb contours, as an angle on the squircle (10 and 2 o'clock)
SEAM_DEG = (38.0, 142.0, 218.0, 322.0)             # where the flats meet the grips

# ------------------------------------------------------------------ the hub
HUB_A, HUB_B, HUB_N = 0.068, 0.066, 3.2
HUB_W0 = 0.0125                                    # the cushion's foot, ahead of the wheel's mid plane
HUB_RINGS = [(1.000, 0.0125), (0.992, 0.0185), (0.968, 0.0228), (0.945, 0.0232), (0.925, 0.0205), (0.905, 0.0190),
             (0.890, 0.0200), (0.80, 0.0228), (0.62, 0.0255), (0.38, 0.0272), (0.15, 0.0280), (0.0, 0.0282)]
STITCH_S = (0.936, 0.905)                          # the two stitch lines (a fraction of the outline)

# ------------------------------------------------------------------ the frame (mm, u right, v up; the right half, top
# centre to the bottom centre; the left half is its mirror)
FRAME_W = 0.0085                                   # the plate's front face, at its edge
FRAME_T = 0.0068
FRAME_HALF = [(0, 73.0), (38, 71.5), (68, 65.0), (92, 54.0), (118, 40.5), (140, 29.0), (158, 22.0), (167, 20.0),
              (168, -30.0), (150, -33.5), (122, -34.5), (98, -36.5), (83, -39.5), (77, -46.0), (69, -62.0),
              (61, -80.0), (54, -97.0), (49, -108.0), (44, -113.0), (0, -114.0)]
WINDOW = [(-90.6, 31.6), (-67.0, 38.3), (-69.0, -25.0), (-84.8, -17.2)]      # the left window; the right is its mirror
CUTOUT = [(-52, -71), (52, -71), (47, -84), (38, -96), (24, -104), (0, -107), (-24, -104), (-38, -96), (-47, -84)]
POD_UV = (0.131, -0.004)                           # the roller's centre on each pod


def _wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def _squircle(a, b, n, count):
    dense = []
    m = count * 4
    for k in range(m):
        t = 2.0 * math.pi * k / m
        c, s = math.cos(t), math.sin(t)
        dense.append((a * math.copysign(abs(c) ** (2.0 / n), c), b * math.copysign(abs(s) ** (2.0 / n), s), 0.0))
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


# ------------------------------------------------------------------ materials
def _champagne():
    """The frame's satin champagne metal. The shared INT_Satin_Silver (0.50) read cream-white under the hall light; the
    photographs (c10_0008, c10_0010) show a duller warm grey, mid-tone even where it faces the light."""
    m = bpy.data.materials.get("INT_Wheel_Satin")
    if m is None:
        from carkit import materials as MB
        m, nt, b = MB.mat("INT_Wheel_Satin")
        MB.set_inputs(b, base=(0.330, 0.315, 0.282), metallic=1.0, roughness=0.40)
    return m


def _dark_thread():
    m = bpy.data.materials.get("INT_Thread_Dark")
    if m is None:
        from carkit import materials as MB
        m, nt, b = MB.mat("INT_Thread_Dark")
        MB.set_inputs(b, base=(0.011, 0.011, 0.014), metallic=0.0, roughness=0.7)
    return m


# ------------------------------------------------------------------ rim
def build_rim(fr, col, lib):
    ns = 216
    path2 = _squircle(RIM_A, RIM_B, RIM_N, ns)
    phi = [math.degrees(math.atan2(p[1] / RIM_B, p[0] / RIM_A)) % 360.0 for p in path2]
    path = [fr.p(u, v) for (u, v, _) in path2]

    def sec(i, s):
        ph = math.radians(phi[i])
        side = math.cos(ph) ** 2
        rr = RIM_R_FLAT + (RIM_R_SIDE - RIM_R_FLAT) * side
        bump = sum(math.exp(-(_wrap(phi[i] - t) / 14.0) ** 2) for t in THUMB_DEG)
        ka, kr = 1.0 + 0.11 * bump, 1.0 + 0.05 * bump
        e = 2.0 / 2.7
        out = []
        for j in range(16):
            t = 2.0 * math.pi * j / 16
            c, sn = math.cos(t), math.sin(t)
            out.append((RIM_D * ka * math.copysign(abs(c) ** e, c), rr * kr * math.copysign(abs(sn) ** e, sn)))
        return out

    sw = Sweep(path, sec, ns, 1, lateral=tuple(fr.A), closed_spine=True, closed_section=True, spine_is_path=True)
    rows = sw.rows()
    # the rim's bottom is the frame's sleeve: rows with |u| under SLEEVE_HALF on the lower flat
    low = [i for i in range(ns) if path2[i][1] < 0 and abs(path2[i][0]) <= SLEEVE_HALF]
    low.sort()
    i_a, i_b = low[0], low[-1]
    leather = rows[i_b:] + rows[:i_a + 1]
    made = []
    ob = grid_mesh("int_wheel_rim", leather, col, lib["leather_purple"], wrap_t=True)
    _outward(ob, path)
    made.append(ob)
    sl = grid_mesh("int_wheel_rim_sleeve", rows[i_a:i_b + 1], col, _champagne(), wrap_t=True)
    _outward(sl, path)
    made.append(sl)
    # the sleeve's two joints, and the four seams where a flat meets a grip
    thread = _dark_thread()

    def tangent(k):
        return tuple(Vector(path[(k + 1) % ns]) - Vector(path[k - 1]))

    for k in (i_a, i_b):
        ring = list(rows[k]) + [rows[k][0]]
        made.append(piping("int_wheel_rim_joint%d" % k, ring, col, thread, r=0.0007, lateral=tangent(k)))
    for deg in SEAM_DEG:
        k = min(range(ns), key=lambda i: abs(_wrap(phi[i] - deg)))
        ring = list(rows[k]) + [rows[k][0]]
        made.append(piping("int_wheel_rim_seam%d" % int(deg), ring, col, thread, r=0.0008, lateral=tangent(k)))
    # tone-on-tone stitching along the rim's inner edge, on the driver's face
    pts, nrm = [], []
    for i in range(ns + 1):
        u, v, _ = path2[i % ns]
        L = math.hypot(u, v)
        rr = RIM_R_FLAT + (RIM_R_SIDE - RIM_R_FLAT) * math.cos(math.radians(phi[i % ns])) ** 2
        k_in = (L - rr * 0.55) / L
        pts.append(fr.p(u * k_in, v * k_in, RIM_D * 0.92 + 0.0003))
        nrm.append(tuple(fr.A))
    made.append(stitches("int_wheel_Stitch", pts, nrm, col, thread, stitch=0.0035, gap=0.0018))
    return made


def _outward(ob, path):
    me = ob.data
    score = 0.0
    for poly in me.polygons:
        q = min(path, key=lambda p: (Vector(p) - poly.center).length_squared)
        score += Vector(poly.normal).dot(poly.center - Vector(q))
    if score < 0:
        me.flip_normals()
        me.update()


# ------------------------------------------------------------------ hub
def _emblem(fr, col, lib, w=0.0245, h=0.043, c=(0.0, -0.008)):
    """The Avatr badge: a vertical rectangle, four metallic facets sloping to a point in the middle."""
    base = HUB_RINGS[-1][1] - 0.0006
    apex = base + 0.0028
    cu, cv = c
    v = [fr.p(cu - w / 2, cv - h / 2, base), fr.p(cu + w / 2, cv - h / 2, base),
         fr.p(cu + w / 2, cv + h / 2, base), fr.p(cu - w / 2, cv + h / 2, base), fr.p(cu + 0.0007, cv + 0.002, apex)]
    faces = [[0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]]
    made = [M.obj("int_wheel_emblem", v, faces, col, lib["satin_metal"], smooth=False)]
    M.orient(made[0].data, lambda q: tuple(fr.A))
    ring = [fr.p(cu + a, cv + b, base - 0.0002) for (a, b) in F.round_rect_xy(-w / 2 - 0.0012, w / 2 + 0.0012,
                                                                              -h / 2 - 0.0012, h / 2 + 0.0012, 0.003, 4)]
    made.append(tube("int_wheel_emblem_pocket", ring + [ring[0]], ellipse(0.0007, 0.0007, 6), col, _dark_thread(),
                     lateral=tuple(fr.A)))
    return made


def build_hub(fr, col, lib):
    outline = [(p[0], p[1]) for p in _squircle(HUB_A, HUB_B, HUB_N, 80)]
    rings = []
    for s, w in HUB_RINGS:
        rings.append([fr.p(u * s, v * s, w) for (u, v) in outline])
    rings[-1] = [rings[-1][0]] * len(outline)
    pad = grid_mesh("int_wheel_hub_pad", rings, col, lib["leather_purple"], wrap_t=True)
    M.orient(pad.data, lambda c: tuple(fr.A))
    made = [pad]
    # the housing behind the cushion
    back = []
    for s, w in ((1.0, HUB_W0), (1.03, 0.006), (1.04, -0.006), (0.88, -0.026), (0.55, -0.045)):
        back.append([fr.p(u * s, v * s, w) for (u, v) in outline])
    hb = grid_mesh("int_wheel_hub_housing", back, col, lib["satin"], wrap_t=True)
    M.orient(hb.data, lambda c: tuple(fr.A))
    made.append(hb)
    # two tone-on-tone dark stitch lines, one on the shoulder and one in the recessed ring
    thread = _dark_thread()
    for s in STITCH_S:
        pts = [fr.p(u * s, v * s, _w_at(s) + 0.0004) for (u, v) in outline]
        pts.append(pts[0])
        made.append(stitches("int_wheel_HubStitch%d" % int(s * 1000), pts, [tuple(fr.A)] * len(pts), col, thread,
                             stitch=0.0030, gap=0.0016))
    made += _emblem(fr, col, lib)
    return made


def _w_at(s):
    """Height of the cushion's face at a fraction s of its outline (linear between the rings)."""
    for (s0, w0), (s1, w1) in zip(HUB_RINGS[:-1], HUB_RINGS[1:]):
        if s1 <= s <= s0:
            t = (s - s0) / (s1 - s0) if s1 != s0 else 0.0
            return w0 + (w1 - w0) * t
    return HUB_RINGS[-1][1]


# ------------------------------------------------------------------ frame
def _loop(half):
    pts = [(u * 0.001, v * 0.001) for (u, v) in half]
    left = [(-u, v) for (u, v) in pts[::-1] if u != 0.0]
    return pts + left


def _plate(fr, col, lib):
    outer = _loop(FRAME_HALF)
    win_l = [(u * 0.001, v * 0.001) for (u, v) in WINDOW]
    win_r = [(-u, v) for (u, v) in win_l[::-1]]
    cut = [(u * 0.001, v * 0.001) for (u, v) in CUTOUT]
    loops = [outer, win_l, win_r, cut]
    polys = [[Vector((u, v, 0.0)) for (u, v) in lp] for lp in loops]
    tris = geometry.tessellate_polygon(polys)
    allv = [p for pl in polys for p in pl]
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in allv]
    for t in tris:
        try:
            bm.faces.new([vs[i] for i in t])
        except ValueError:
            pass
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=5, use_grid_fill=True)
    me = bpy.data.meshes.new("int_wheel_frame")
    for v in bm.verts:
        u, vv = v.co.x, v.co.y
        bulge = max(0.0, 1.0 - ((u / 0.175) ** 2 + (vv / 0.140) ** 2))
        p = fr.p(u, vv, FRAME_W + 0.0045 * bulge)
        v.co = Vector(p)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("int_wheel_frame", me)
    col.objects.link(ob)
    ob.data.materials.append(_champagne())
    for poly in me.polygons:
        poly.use_smooth = True
    M.orient(me, lambda c: tuple(fr.A))
    M.solidify(ob, FRAME_T, -1.0)
    M.bevel(ob, 0.0012, 2, 35)
    made = [ob]
    # what shows through the windows: a dark recess
    for k, win in enumerate((win_l, win_r)):
        cx = sum(p[0] for p in win) / 4
        cv = sum(p[1] for p in win) / 4
        grown = [(cx + (u - cx) * 1.12, cv + (v - cv) * 1.12) for (u, v) in win]
        made.append(F.ngon_cap(col, "int_wheel_window%d" % k, [fr.p(u, v, -0.004) for (u, v) in grown], lib["dash_top"],
                               tuple(fr.A)))
        # a satin button, outboard in each window (c10_0010)
        bu = cx - 0.003 if cx < 0 else cx + 0.003
        made.append(_fbox(fr, col, "int_wheel_winbtn%d" % k, (bu, cv + 0.004, 0.0025), (0.011, 0.038, 0.004),
                          _champagne(), r=0.0015))
    return made


def _gear(r, teeth=26, depth=0.045):
    out = []
    n = teeth * 4
    for k in range(n):
        t = 2.0 * math.pi * k / n
        wave = 1.0 if (k % 4) in (0, 1) else 1.0 - depth
        out.append((r * wave * math.cos(t), r * wave * math.sin(t)))
    return out


def build_pods(fr, col, lib):
    """A roller in an oval bezel on each pod: a black knurled wheel set flush (c10_0008 / c10_0010)."""
    made = []
    thread = _dark_thread()
    for side, tag in ((-1.0, "L"), (1.0, "R")):
        cu, cv = side * POD_UV[0], POD_UV[1]
        w0 = FRAME_W + 0.0045 * max(0.0, 1.0 - ((cu / 0.175) ** 2 + (cv / 0.14) ** 2))
        bez = [fr.p(cu + 0.0150 * math.cos(2 * math.pi * k / 40), cv + 0.0172 * math.sin(2 * math.pi * k / 40), w0 + 0.0005)
               for k in range(40)]
        made.append(tube("int_wheel_bezel" + tag, bez + [bez[0]], ellipse(0.0016, 0.0009, 8), col, _champagne(),
                         lateral=tuple(fr.A)))
        # the recess floor, dark
        made += F.disc(col, "int_wheel_recess" + tag, fr.p(cu, cv, w0 - 0.0004), tuple(fr.A), 0.0140, thread)
        a = fr.p(cu, cv, w0 - 0.0005)
        b = fr.p(cu, cv, w0 + 0.0062)
        made.append(tube("int_wheel_roller" + tag, [a, b], _gear(0.0102), col, lib["rubber"], lateral=tuple(fr.U)))
    return made


# ------------------------------------------------------------------ column and stalks
def build_column(fr, col, lib):
    path = [fr.p(0.0, -0.012, -0.030 - 0.200 * k / 8.0) for k in range(9)]
    return [tube("int_wheel_column", path, [(a * 0.038, b * 0.032) for (a, b) in ellipse(1, 1, 16)], col,
                 lib["satin"], lateral=tuple(fr.V), scale=lambda s: (1.0 + 0.15 * s, 1.0 + 0.2 * s))]


def build_stalks(fr, col, lib):
    """The indicator / wiper stalk (left) and the gear selector (right): short, thick, dark, with a satin tip, sprung
    from a round boss on the column and tucked behind the spokes (c10_0013, c10_0006). Neither reaches past the rim."""
    made = []
    for side, tag in ((-1.0, "L"), (1.0, "R")):
        a = Vector(fr.p(side * 0.036, 0.040, -0.046))
        b = Vector(fr.p(side * 0.128, 0.044, -0.034))
        d = (b - a).normalized()
        path = [tuple(a.lerp(b, t / 10.0)) for t in range(11)]
        made.append(tube("int_wheel_stalk" + tag, path, ellipse(0.0100, 0.0125, 14), col, lib["satin"],
                         lateral=tuple(fr.A), scale=lambda s: (1.0 - 0.12 * s, 1.0 - 0.18 * s)))
        # the boss it comes out of
        boss = [fr.p(side * 0.034, 0.040, -0.040 - 0.020 * k / 4.0) for k in range(5)]
        made.append(tube("int_wheel_stalkBoss" + tag, boss, ellipse(0.0150, 0.0150, 16), col, lib["satin"],
                         lateral=tuple(fr.U)))
        # the satin tip
        tip = [tuple(b + d * (-0.002 + 0.016 * t / 4.0)) for t in range(5)]
        made.append(tube("int_wheel_stalkTip" + tag, tip, ellipse(0.0078, 0.0100, 12), col, _champagne(),
                         lateral=tuple(fr.A)))
    return made


# ------------------------------------------------------------------ the wheel
def build(col, lib, centre, tilt):
    from carkit.interior import steering as ST
    fr = ST.WheelFrame(centre, tilt)
    made = []
    made += build_rim(fr, col, lib)
    made += _plate(fr, col, lib)
    made += build_hub(fr, col, lib)
    made += build_pods(fr, col, lib)
    made += build_column(fr, col, lib)
    made += build_stalks(fr, col, lib)
    return made, fr
