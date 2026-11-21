"""Avatr 06T cockpit: the dash, its display band, the centre screen, the side wings and the steering wheel.

Read from blender/reference/avatr-06t/interior through the solved camera of c10_0001 (a06t_cabinsolve:
camera (-0.565, -0.044, 1.273), 22 mm, 7.5 px), with c10_0008 (the wheel square on), c10_0015 / c10_0047 (the screen
on the console's arch), c10_0055 (the passenger dash) and c3_0001 (the driver's side through the open door):

    hood            2026-11-21 (owner: "overhanging upper dashboard hood ... a shaded recess for the display band"): the
                    dark top pad rises to a flat crown, the trim-coloured lip overhangs a black recess 0.082 tall, and
                    the band bends away from the driver toward each A-pillar (ARCH_FWD), so the recess's end walls
                    face the cabin. A round perforated speaker grille is let into the crown at each end.
    display band    in the recess's back wall (leaning back 13 deg): the 35.4 in panoramic display (0.880 x 0.061, as
                    c10_0001 measures it: 937 x 65 px at 0.94 mm/px) and, at each end, a tapered 6.7 in e-mirror panel
                    set flush on the bent wall (no raised blocks): y +-0.51 .. +-0.66
    main face       light Misty Purple soft-touch, from the recess's lower lip down to a seam at z ~0.87
                    (the glovebox lid's top on the passenger side), the lid and the knee panel below
    wings           at each end the dash turns into a large triangular sail ahead of the door card (c3_0001), with
                    a black Meridian mesh triangle and a round vent at its foot
    centre screen   15.6 in, outer frame 0.352 x 0.226, centre (0.650, 0, 0.945): its top stands 3 mm under the display's
                    lower edge as the driver's eye sees it, at the wheel's height (c10_0008)
    wheel           a06t_wheel: a wide squircle rim 0.385 x 0.270, one satin champagne-silver frame (arch, side
                    spokes with a roller each, trapezoid lower spoke with a cut-out), a rounded hub with the faceted
                    Avatr badge, short dark stalks behind the spokes (centre (0.53, 0.39, 1.005), 20 deg back)

Axes: +X forward, +Y left (the driver's side - China is LHD), +Z up.
"""
import math

import bpy
from mathutils import Matrix, Vector

import a06t_interior as RI
from carkit import mesh as M
from carkit.interior import fittings as F
from carkit.interior.sweep import Sweep, grid_mesh, tube, ellipse, smooth_path, piping, _orient_to

DASH_HALF = 0.755               # the dash's ends, against the door cards
BAND_HALF = 0.705               # the recess's ends (a hand's breadth past the e-mirror displays)
FACE_HALF = 0.705               # where the main face hands over to the wings (c10_0001: y -0.715 at x 0.50)

# centreline section (x, z), windscreen to firewall (the top points also stay 12-16 mm under the glass).
# The dash's upper edge is an overhanging HOOD (c10_0001, c10_0006, c10_0048): the dark top pad rises to a crown, the
# hood's lip overhangs a black recess 8 cm tall, and the panoramic display sits in the recess's back wall (leaning
# back 13 deg) with the two e-mirror displays at its ends. The face below rolls under at x 0.790 ahead of the door
# opening. The recess is 0.082 tall (the 6.7 in e-mirror panel is 0.083 x 0.148).
DASH_SECTION = [
    (1.100, 0.940), (1.040, 0.935), (0.980, 0.932), (0.930, 0.935),    # 0-3 the dark trough under the windscreen
    (0.905, 0.950), (0.893, 1.040), (0.886, 1.080),                    # 4-6 the strip's back rises from it
    (0.870, 1.103), (0.834, 1.103),                                    # 7-8 the hood's crown (a flat top, dark)
    (0.817, 1.095), (0.813, 1.086),                                    # 9-10 the hood's lip, its leading edge
    (0.828, 1.080), (0.862, 1.080),                                    # 11-12 under the hood to the recess's back wall
    (0.843, 0.998),                                                    # 13 the back wall's foot (display in 12-13)
    (0.835, 0.992), (0.826, 0.984), (0.812, 0.968),                    # 14-16 the recess's floor and the lower lip
    (0.800, 0.945), (0.792, 0.918), (0.790, 0.894),                    # 17-19 the main face
    (0.794, 0.872),                                                     # 20 the seam (glovebox top)
    (0.808, 0.846), (0.832, 0.816), (0.880, 0.770), (0.950, 0.710),    # 21-24 lid / knee panel, rolling under
    (1.020, 0.650), (1.090, 0.590), (1.150, 0.540),                    # 25-27 the underside to the firewall
]
DASH_COUNTS = [5, 5, 5, 4, 3, 3, 3, 4, 3, 2, 3, 6, 2, 2, 3, 3, 4, 4, 3, 2, 3, 4, 5, 5, 5, 5, 4]
GLASS_GAP = 0.014
C_TOP_END, C_HOOD1, C_BAND0, C_BAND1, C_FACE1, C_LOWER = 8, 10, 10, 14, 20, 27
K_PLANE_TOP, K_PLANE_BOT = 12, 13           # the display's back wall: control points
# the band wraps toward the A-pillars: at each end it bends away from the driver (the recess's end walls turn to face
# the cabin, where the e-mirror displays sit: c10_0001's trapezoids)
ARCH_Y0, ARCH_FWD = 0.45, 0.080
ARCH_W = [0, 0, 0, 0.35, 0.7] + [1.0] * 9 + [0.85, 0.6, 0.35, 0.15] + [0.0] * 10

DISPLAY_W, DISPLAY_H = 0.880, 0.061         # c10_0001: 937 x 65 px at 0.94 mm/px
DISPLAY_Z = 1.047                           # centre: 2.5 mm under the hood's underside
BAND_TILT = math.radians(13.0)
MIRROR_W = 0.145                            # the 6.7 in panel; the outline tapers from 0.078 tall (inboard) to 0.058
MIRROR_Y = 0.585
MIRROR_Z_IN, MIRROR_Z_OUT = (1.001, 1.078), (1.010, 1.069)
MIRROR_LIFT = 0.003

SCREEN_C = (0.650, 0.000, 0.945)            # floating 15.6" screen: its top 3 mm under the display's lower edge from the
                                            # driver's eye (c10_0008: top at the cluster, centre at the wheel's)
SCREEN_OUT_W, SCREEN_OUT_H = 0.352, 0.226
SCREEN_W, SCREEN_H = 0.336, 0.210

WHEEL_C = (0.530, 0.390, 1.005)
WHEEL_TILT = math.radians(20.0)


def _face_x(z):
    """x on the display's back wall at height z, on the centre line (between control points 12 and 13)."""
    (xa, za), (xb, zb) = DASH_SECTION[K_PLANE_TOP], DASH_SECTION[K_PLANE_BOT]
    return xb + (xa - xb) * (z - zb) / (za - zb)


def _section_at(y):
    """The dash's centre-line section bent for the station at height y: the band wraps away from the driver toward
    each A-pillar, the ends squeeze under the glass, the lower face swings back into the door card."""
    ay = abs(y)
    # past the main face the dash turns rearward into the wings: its face swings back a little and the lower part
    # lifts so the end meets the door card's top
    e = RI._smooth((ay - FACE_HALF) / (DASH_HALF - FACE_HALF))
    # the body narrows toward the A-pillar's foot: above z 1.05 the dash's last 10 cm squeeze down toward 1.05, or the top
    # pad's corners stood outside the skin (porting/poke_probe_a06t.py: x 0.61-0.74, |y| 0.75, z 1.19-1.24)
    squeeze = 0.35 * RI._smooth((ay - 0.660) / (DASH_HALF - 0.660))
    arch = ARCH_FWD * RI._smooth((ay - ARCH_Y0) / (DASH_HALF - ARCH_Y0))
    pts = []
    for k, (x, z) in enumerate(DASH_SECTION):
        x += arch * ARCH_W[k]
        if k <= 4:
            z = min(z, RI.z_glass(x, y) - GLASS_GAP)
        if z > 1.05:
            z = 1.05 + (z - 1.05) * (1.0 - squeeze)
        if k >= 17:
            x -= 0.030 * e
        pts.append([x, z])
    # the hood and the recess move down together where the glass comes down onto them
    dz = 0.0
    for k in range(5, 13):
        dz = min(dz, RI.z_glass(pts[k][0], y) - GLASS_GAP - pts[k][1])
    for k in range(5, 14):
        pts[k][1] += dz
    return [(x, z) for x, z in pts]


def dash_section(i, s):
    return _section_at(DASH_HALF * (1.0 - 2.0 * s))


def plane_x(y, z):
    """x of the display wall at (y, z) in the bent section (the e-mirror displays sit on it)."""
    sec = _section_at(y)
    (xa, za), (xb, zb) = sec[K_PLANE_TOP], sec[K_PLANE_BOT]
    return xb + (xa - xb) * (z - zb) / (za - zb)


def build_dash(col, lib):
    made = []
    spine = [(0.0, DASH_HALF - 2 * DASH_HALF * k / 10.0, 0.0) for k in range(11)]
    sw = Sweep(spine, dash_section, 120, DASH_COUNTS, lateral=(1.0, 0.0, 0.0), outward=-1.0)
    ys = [p[1] for p in sw.spine]
    i_b0 = min(range(len(ys)), key=lambda i: abs(ys[i] - BAND_HALF))
    i_b1 = min(range(len(ys)), key=lambda i: abs(ys[i] + BAND_HALF))
    made.append(sw.mesh("int_dash_Top", col, lib["dash_top"], j0=0, j1=sw.col(C_TOP_END)))
    # the hood's lip, in the trim, across the whole width from A-pillar to A-pillar
    made.append(sw.mesh("int_dash_Hood", col, lib["trim_purple"], j0=sw.col(C_TOP_END), j1=sw.col(C_HOOD1)))
    made.append(sw.mesh("int_dash_Band", col, lib["piano"], i0=i_b0, i1=i_b1, j0=sw.col(C_BAND0),
                        j1=sw.col(C_BAND1)))
    for tag, a, b in (("L", 0, i_b0), ("R", i_b1, len(ys) - 1)):
        made.append(sw.mesh("int_dash_BandEnd" + tag, col, lib["trim_purple"], i0=a, i1=b, j0=sw.col(C_BAND0),
                            j1=sw.col(C_BAND1)))
    # ONE pad from the recess's floor down to the firewall: no seam across the face, no groove over the glovebox lid or the
    # knee panel, none under the lip (2026-11-21: "a continuous, rounded horizontal volume")
    made.append(sw.mesh("int_dash_Face", col, lib["trim_purple"], j0=sw.col(C_BAND1), j1=sw.col(C_LOWER)))
    made += build_dash_ends(col, lib, sw)
    return made, sw


def build_dash_ends(col, lib, sw):
    return [F.ngon_cap(col, "int_dash_End" + tag, list(sw.pts[idx]), lib["trim_purple"], (0.0, s, 0.0))
            for idx, tag, s in ((0, "L", 1.0), (len(sw.pts) - 1, "R", -1.0))]


# ---------------------------------------------------------------- screens
def _band_quad(name, cy, cz, w, h, col, lift=0.003):
    """A quad lying on the display's back wall, centred at (y, z) on the straight part of the band."""
    c = (_face_x(cz), cy, cz)
    return F.screen_quad(name, c, w, h, BAND_TILT, col, lift=lift)


def _mirror_panel(name, side, col, mat, nu=12, nv=4):
    """An e-mirror display (6.7 in): a tapered (trapezoid) panel set flush in the recess's end wall, on the bent wall,
    so it turns to face the cabin (c10_0001, c10_0006). UV: u runs from the larger y to the smaller, v up the panel."""
    y_lo, y_hi = MIRROR_Y - MIRROR_W / 2, MIRROR_Y + MIRROR_W / 2
    verts, uvs = [], []
    for i in range(nu + 1):
        t = i / float(nu)
        ay = y_lo + (y_hi - y_lo) * t                      # |y|, inboard to outboard
        z0 = MIRROR_Z_IN[0] + (MIRROR_Z_OUT[0] - MIRROR_Z_IN[0]) * t
        z1 = MIRROR_Z_IN[1] + (MIRROR_Z_OUT[1] - MIRROR_Z_IN[1]) * t
        y = side * ay
        for j in range(nv + 1):
            tv = j / float(nv)
            z = z0 + (z1 - z0) * tv
            verts.append((plane_x(y, z) - MIRROR_LIFT, y, z))
            uvs.append(((y_hi - ay) / (y_hi - y_lo) if side > 0 else (ay - y_lo) / (y_hi - y_lo), tv))
    faces = [[i * (nv + 1) + j, (i + 1) * (nv + 1) + j, (i + 1) * (nv + 1) + j + 1, i * (nv + 1) + j + 1]
             for i in range(nu) for j in range(nv)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            uv.data[li].uv = uvs[me.loops[li].vertex_index]
    me.update()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    ob.data.materials.append(mat)
    for poly in me.polygons:
        poly.use_smooth = True
    M.orient(me, lambda c: (-1.0, 0.0, 0.0))
    return ob


def build_screens(col, lib):
    """screen_main (the 15.6 in, the HMI's anchor), screen_cluster (the 35.4 in panoramic display, the generated
    cluster picture) and screen_mirror_L / R (the 6.7 in e-mirror displays)."""
    made = []
    # the 15.6 in floating screen: a thin piano-black slab with a satin edge, the active area proud of it
    made.append(F.slab("int_screen_body", SCREEN_C, SCREEN_OUT_W, SCREEN_OUT_H, 0.014, 0.012, 0.0, col,
                       lib["piano"]))
    q = F.screen_quad("screen_main", SCREEN_C, SCREEN_W, SCREEN_H, 0.0, col)
    q.data.materials.append(F.screen_material())
    made.append(q)
    rim = [(SCREEN_C[0] + 0.0005, SCREEN_C[1] + a, SCREEN_C[2] + b) for (a, b) in
           F.round_rect_xy(-SCREEN_OUT_W / 2, SCREEN_OUT_W / 2, -SCREEN_OUT_H / 2, SCREEN_OUT_H / 2, 0.012, 6)]
    made.append(tube("int_screen_rim", rim + [rim[0]], ellipse(0.0016, 0.0022, 8), col, lib["satin_metal"],
                     lateral=(1.0, 0.0, 0.0)))
    # the panoramic display in the band
    made.append(_band_quad("screen_cluster", 0.0, DISPLAY_Z, DISPLAY_W, DISPLAY_H, col))
    made[-1].data.materials.append(F.screen_material())
    # the e-mirror displays at the band's ends, flush in the recess (no raised blocks)
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        made.append(_mirror_panel("screen_mirror_" + tag, side, col, lib["display_mirror"]))
    return made


def build_grilles(col, lib):
    """A flush round perforated speaker grille at each top corner of the dash (c10_0001, c10_0006): on the hood's
    crown, in the dark pad, a satin ring round each."""
    made = []
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        y = side * 0.625
        sec = _section_at(y)
        x = 0.5 * (sec[7][0] + sec[8][0]) + 0.004
        z = max(sec[7][1], sec[8][1]) + 0.0004
        made += F.disc(col, "int_dash_Grille" + tag, (x, y, z), (0.0, 0.0, 1.0), 0.032, lib["speaker_silver"],
                       dome=0.0004, rim=0.0016, rim_mat=lib["satin_metal"])
    return made


def cluster_image(path=None, w=3072, h=180):
    """The panoramic display's resting picture for the 35.4-inch 4K Star Ring Display.
    Matches c10_0001 / c10_0048: ADAS 3D road visualization behind steering wheel, media ribbon in centre,
    weather and clock on passenger side."""
    import os
    import numpy as np
    from carkit.textures import TEX_DIR
    out = path or os.path.join(TEX_DIR, "cluster_a06t.png")
    if os.path.exists(out):
        im = bpy.data.images.get("T_Cluster_A06T")
        if not im:
            im = bpy.data.images.load(out)
            im.name = "T_Cluster_A06T"
        return out
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    img = np.zeros((h, w, 3), np.float32)
    top, bot = np.array([0.08, 0.10, 0.16]), np.array([0.05, 0.06, 0.10])
    img[...] = top + (bot - top) * (yy / h)[..., None]
    im = bpy.data.images.get("T_Cluster_A06T") or bpy.data.images.new("T_Cluster_A06T", w, h)
    if tuple(im.size) != (w, h):
        im.scale(w, h)
    rgba = np.ones((h, w, 4), np.float32)
    srgb = np.where(img <= 0.0031308, img * 12.92, 1.055 * np.power(np.clip(img, 0, 1), 1 / 2.4) - 0.055)
    rgba[..., :3] = srgb[::-1]
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw = out
    im.file_format = 'PNG'
    im.save()
    return out


# ------------------------------------------------------------------ wings
def build_wings(col, lib):
    """The dash's ends: clean end face meeting the door shut line smoothly, without nested clashing parts."""
    made = []
    under = lambda x: DASH_SECTION[21][1] + (DASH_SECTION[27][1] - DASH_SECTION[21][1]) * max(0.0, min(1.0, (
        x - DASH_SECTION[21][0]) / (DASH_SECTION[27][0] - DASH_SECTION[21][0])))
    x_w0, x_w1 = 0.790, 1.150
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        # the panel under the dash, floor to the dash's underside, closing the footwell
        rows = [[(x_w0 + (x_w1 - x_w0) * i / 14.0, side * (DASH_HALF - 0.002), RI.FLOOR_Z + (under(x_w0 + (x_w1 - x_w0) * i / 14.0)
                 + 0.004 - RI.FLOOR_Z) * j / 8.0) for j in range(9)] for i in range(15)]
        bk = grid_mesh("int_wing_Panel" + tag, rows, col, lib["trim_purple"])
        _orient_to(bk, Vector(rows[7][4]), Vector((0.0, side, 0.0)))
        made.append(bk)
        # Round vent at foot
        made += F.disc(col, "int_wing_Vent" + tag, (0.930, side * (DASH_HALF + 0.002), 0.525), (0.0, side, 0.0),
                       0.026, lib["piano"], rim=0.0035, rim_mat=lib["trim_purple"])
    return made


# ------------------------------------------------------------ steering wheel
def build_wheel(col, lib):
    """The squircle wheel with its single satin frame, hub, rollers and stalks (a06t_wheel)."""
    import a06t_wheel as WH
    made, _fr = WH.build(col, lib, WHEEL_C, WHEEL_TILT)
    return made
