"""Avatr 06T cockpit: the dash, its display band, the centre screen, the side wings and the steering wheel.

Read from blender/reference/avatr-06t/interior through the solved camera of c10_0001 (a06t_cabinsolve:
camera (-0.565, -0.044, 1.273), 22 mm, 7.5 px), with c10_0008 (the wheel square on), c10_0015 / c10_0047 (the screen
on the console's arch), c10_0055 (the passenger dash) and c3_0001 (the driver's side through the open door):

    display band    a black glossy recess across the dash's top, z 1.124 .. 1.218 at x ~0.58, leaning back ~14 deg;
                    the 35.4 in panoramic display in its upper part (y +-0.43, z 1.151 .. 1.209) and a 6.7 in
                    e-mirror display at each end (y +-0.515 .. +-0.655: 0.145 x 0.08 at x 0.55, which is what a
                    6.7 in 16:9 panel measures - the depth of the whole band comes from it)
    main face       light Misty Purple soft-touch, from the band's lower lip (z 1.124) down to a seam at z ~0.93
                    (the glovebox lid's top on the passenger side), the lid and the knee panel below
    wings           at each end the dash turns into a large triangular sail ahead of the door card (c3_0001), with
                    a black Meridian mesh triangle and a round vent at its foot
    centre screen   15.6 in, outer frame 0.352 x 0.226 (solved with the camera: centre (0.372, 0, 1.058), upright)
    wheel           a squircle rim 0.385 x 0.31 in Misty Purple Nappa, a satin champagne-silver U frame round a
                    rounded-square hub, a roller on each side arm, the silver Avatr pyramid emblem
                    (centre (0.25, 0.39, 1.045) from the camera's rays)

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
BAND_HALF = 0.675               # the black band's ends (just past the e-mirror displays)
FACE_HALF = 0.705               # where the main face hands over to the wings (c10_0001: y -0.715 at x 0.50)

# centreline section (x, z), windscreen to firewall (every z also stays 16 mm under the glass).
# Dash depth significantly reduced (by >50%): top shelf shortened from ~50 cm down to ~23.5 cm so the dash trough is
# completely shielded from exterior view under the cowl/windscreen frit line. Band crest at x 0.865 (z 1.085) with
# panoramic display and e-mirror displays right at the A-pillar base (as in c3_0001 / cockpit_01), face rolling under
# at x 0.790 ahead of the door opening.
DASH_SECTION = [
    (1.100, 0.940), (1.040, 0.935), (0.980, 0.932), (0.930, 0.935),    # 0-3 the dark trough under the windscreen
    (0.905, 0.950), (0.888, 1.020), (0.875, 1.075),                    # 4-6 the strip's back rises from it
    (0.865, 1.085), (0.852, 1.028), (0.846, 1.006),                    # 7-9 the band (display in 7-8)
    (0.838, 1.000), (0.822, 0.990),                                    # 10-11 the lower lip
    (0.808, 0.970), (0.796, 0.940), (0.790, 0.915), (0.790, 0.892),    # 12-15 the main face
    (0.794, 0.872),                                                     # 16 the seam (glovebox top)
    (0.808, 0.846), (0.832, 0.816), (0.880, 0.770), (0.950, 0.710),    # 17-20 lid / knee panel, rolling under
    (1.020, 0.650), (1.090, 0.590), (1.150, 0.540),                    # 21-23 the underside to the firewall
]
DASH_COUNTS = [5, 5, 5, 4, 3, 3, 2, 6, 2, 2, 3, 3, 4, 4, 3, 2, 3, 4, 5, 5, 5, 5, 4]
GLASS_GAP = 0.016
C_TOP_END, C_BAND0, C_BAND1, C_FACE1, C_LOWER = 6, 6, 10, 16, 23

DISPLAY_C = (0.8585, 0.000, 1.0565)
DISPLAY_W, DISPLAY_H = 1.080, 0.062
BAND_TILT = math.radians(13.0)
MIRROR_W, MIRROR_H = 0.145, 0.078
MIRROR_Y, MIRROR_Z = 0.585, 1.050

SCREEN_C = (0.650, 0.000, 0.890)            # floating 15.6" screen top sits below panoramic display band
SCREEN_OUT_W, SCREEN_OUT_H = 0.352, 0.226
SCREEN_W, SCREEN_H = 0.336, 0.210

WHEEL_C = (0.530, 0.390, 1.005)
WHEEL_TILT = math.radians(20.0)


def _face_x(z):
    """x on the band's face at height z (between control points 7 and 8)."""
    (xa, za), (xb, zb) = DASH_SECTION[8], DASH_SECTION[7]
    return xa + (xb - xa) * (z - za) / (zb - za)


def dash_section(i, s):
    y = DASH_HALF * (1.0 - 2.0 * s)
    ay = abs(y)
    # past the main face the dash turns rearward into the wings: its face swings back a little and the lower part
    # lifts so the end meets the door card's top
    e = RI._smooth((ay - FACE_HALF) / (DASH_HALF - FACE_HALF))
    # the body narrows toward the A-pillar's foot: above z 1.10 the dash's last 10 cm squeeze down toward 1.10, or the top
    # pad's corners stood outside the skin (porting/poke_probe_a06t.py: x 0.61-0.74, |y| 0.75, z 1.19-1.24)
    squeeze = 0.6 * RI._smooth((ay - 0.660) / (DASH_HALF - 0.660))
    out = []
    for k, (x, z) in enumerate(DASH_SECTION):
        if k <= 6:
            z = min(z, RI.z_glass(x, y) - GLASS_GAP)
        if z > 1.05:
            z = 1.05 + (z - 1.05) * (1.0 - squeeze)
        if k >= 10:
            x -= 0.030 * e
        out.append((x, z))
    return out


def build_dash(col, lib):
    made = []
    spine = [(0.0, DASH_HALF - 2 * DASH_HALF * k / 10.0, 0.0) for k in range(11)]
    sw = Sweep(spine, dash_section, 120, DASH_COUNTS, lateral=(1.0, 0.0, 0.0), outward=-1.0)
    ys = [p[1] for p in sw.spine]
    i_b0 = min(range(len(ys)), key=lambda i: abs(ys[i] - BAND_HALF))
    i_b1 = min(range(len(ys)), key=lambda i: abs(ys[i] + BAND_HALF))
    made.append(sw.mesh("int_dash_Top", col, lib["dash_top"], j0=0, j1=sw.col(C_TOP_END)))
    made.append(sw.mesh("int_dash_Band", col, lib["piano"], i0=i_b0, i1=i_b1, j0=sw.col(C_BAND0),
                        j1=sw.col(C_BAND1)))
    for tag, a, b in (("L", 0, i_b0), ("R", i_b1, len(ys) - 1)):
        made.append(sw.mesh("int_dash_BandEnd" + tag, col, lib["trim_purple"], i0=a, i1=b, j0=sw.col(C_BAND0),
                            j1=sw.col(C_BAND1)))
    made.append(sw.mesh("int_dash_Face", col, lib["trim_purple"], j0=sw.col(C_BAND1), j1=sw.col(C_FACE1)))
    made.append(sw.mesh("int_dash_Lower", col, lib["trim_purple"], j0=sw.col(C_FACE1), j1=sw.col(C_LOWER)))
    # the seam over the glovebox lid (passenger) and the knee panel (driver): a dark groove, broken at the console
    for tag, y0, y1 in (("R", -0.080, -0.660), ("L", 0.660, 0.080)):
        i0 = min(range(len(ys)), key=lambda i: abs(ys[i] - y0))
        i1 = min(range(len(ys)), key=lambda i: abs(ys[i] - y1))
        a, b = min(i0, i1), max(i0, i1)
        p, n = sw.iso_col(sw.col(C_FACE1), a, b, lift=-0.0008)
        made.append(piping("int_dash_Seam" + tag, p, col, lib["satin"], r=0.0016, lateral=(1.0, 0.0, 0.0)))
    # a soft groove under the band's lip, full width (c10_0001: the shadow line under the display band)
    p, n = sw.iso_col(sw.col(11), 2, len(ys) - 3, lift=-0.0006)
    made.append(piping("int_dash_LipGroove", p, col, lib["satin"], r=0.0012, lateral=(1.0, 0.0, 0.0)))
    made += build_dash_ends(col, lib, sw)
    return made, sw


def build_dash_ends(col, lib, sw):
    return [F.ngon_cap(col, "int_dash_End" + tag, list(sw.pts[idx]), lib["trim_purple"], (0.0, s, 0.0))
            for idx, tag, s in ((0, "L", 1.0), (len(sw.pts) - 1, "R", -1.0))]


# ---------------------------------------------------------------- screens
def _band_quad(name, cy, cz, w, h, col, lift=0.005):
    """A quad lying on the band's face, centred at (y, z)."""
    c = (_face_x(cz), cy, cz)
    return F.screen_quad(name, c, w, h, BAND_TILT, col, lift=lift)


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
    made.append(_band_quad("screen_cluster", DISPLAY_C[1], DISPLAY_C[2], DISPLAY_W, DISPLAY_H, col))
    made[-1].data.materials.append(F.screen_material())
    # the e-mirror displays at the band's ends
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        m = _band_quad("screen_mirror_" + tag, side * MIRROR_Y, MIRROR_Z, MIRROR_W, MIRROR_H, col)
        m.data.materials.append(lib["display_mirror"])
        made.append(m)
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
    under = lambda x: DASH_SECTION[17][1] + (DASH_SECTION[23][1] - DASH_SECTION[17][1]) * max(0.0, min(1.0, (
        x - DASH_SECTION[17][0]) / (DASH_SECTION[23][0] - DASH_SECTION[17][0])))
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
A06T_WHEEL = dict(
    radius=0.165, loop=dict(a=0.165, b=0.130, n=3.2, ctrl=72), section=(0.0122, 0.0142), grip_swell=0.05,
    segments=[(0.0, 180.0, "leather_purple"), (180.0, 360.0, "leather_purple")],
    marker=None,
    hub=dict(w=0.114, h=0.104, sides=4, r_corner=0.026, dome=0.008, depth=0.045, pad_role="leather_purple",
             housing_role="trim_purple"),
    spokes=None, lower_spoke=None, buttons=[], logo=None,
)


def _emblem(fr, col, lib, w=0.0135, h=0.024):
    """The refined, elegantly integrated Avatr emblem on the hub: an upright faceted satin-silver lozenge
    recessed flush into a debossed pocket in the leather pad (only 1.2 mm rise, eliminates bulky pyramid)."""
    lift = 0.016 + A06T_WHEEL["hub"]["dome"] + 0.0003
    apex_h = lift + 0.0012
    v_bot = fr.p(0.0, -h / 2, lift)
    v_right = fr.p(w / 2, 0.0, lift)
    v_top = fr.p(0.0, h / 2, lift)
    v_left = fr.p(-w / 2, 0.0, lift)
    v_apex = fr.p(0.0, 0.0, apex_h)
    v_rb = fr.p(0.0, -h * 0.25, apex_h * 0.98 + lift * 0.02)
    v_rt = fr.p(0.0, h * 0.25, apex_h * 0.98 + lift * 0.02)
    verts = [v_bot, v_right, v_top, v_left, v_apex, v_rb, v_rt]
    faces = [
        [0, 1, 5], [1, 4, 5], [1, 6, 4], [1, 2, 6],
        [2, 3, 6], [3, 4, 6], [3, 5, 4], [3, 0, 5]
    ]
    made = [M.obj("int_wheel_emblem", verts, faces, col, lib["satin_metal"], smooth=False)]
    # Debossed leather pocket perimeter
    p_rim = [fr.p(u, v, lift - 0.0004) for (u, v) in F.round_rect_xy(-0.0085, 0.0085, -0.014, 0.014, 0.003, 4)]
    made.append(tube("int_wheel_emblem_pocket", p_rim + [p_rim[0]], ellipse(0.0008, 0.0006, 6), col, lib["trim_purple"],
                     lateral=tuple(fr.A)))
    return made


def build_wheel(col, lib):
    """Refined Avatr 06T steering wheel: sleek squircle rim with thumb rests, tailored airbag hub,
    flush faceted emblem, continuous satin bezel, sculpted hollow bottom spoke, and knurled roller pods."""
    from carkit.interior import steering as ST
    fr = ST.WheelFrame(WHEEL_C, WHEEL_TILT)
    made = []

    # 1. Sculpted Rim with reduced cross-section (24.4x28.4 mm) and ergonomic thumb rests
    a, b = A06T_WHEEL["loop"]["a"], A06T_WHEEL["loop"]["b"]
    ns = 192
    loop2d = []
    for i in range(ns):
        t = 2.0 * math.pi * i / ns
        c, s_ = math.cos(t), math.sin(t)
        u = a * math.copysign(abs(c) ** (2.0 / A06T_WHEEL["loop"]["n"]), c)
        v = b * math.copysign(abs(s_) ** (2.0 / A06T_WHEEL["loop"]["n"]), s_)
        loop2d.append((u, v, 0.0))
    ang = [math.degrees(math.atan2(p[1], p[0])) % 360.0 for p in loop2d]
    rr, dd = A06T_WHEEL["section"]

    def rim_sec(i, s):
        swell_10 = math.exp(-((ang[i] - 140.0) / 18.0) ** 2)
        swell_2 = math.exp(-((ang[i] - 40.0) / 18.0) ** 2)
        swell_thumb = 1.0 + 0.15 * (swell_10 + swell_2)
        return [(dd * swell_thumb * math.cos(2 * math.pi * j / 16),
                 rr * swell_thumb * math.sin(2 * math.pi * j / 16))
                for j in range(16)]

    path_rim = [fr.p(u, v) for (u, v, _) in loop2d]
    sw_rim = Sweep(path_rim, rim_sec, ns, 1, lateral=tuple(fr.A), closed_spine=True,
                   closed_section=True, spine_is_path=True)
    made.append(sw_rim.mesh("int_wheel_rim", col, lib["leather_purple"]))
    made += _rim_stitch(fr, col, lib)

    # 2. Airbag Hub: Soft squircle pillow with tailored perimeter seam
    hw, hh = A06T_WHEEL["hub"]["w"], A06T_WHEEL["hub"]["h"]
    hr = A06T_WHEEL["hub"]["r_corner"]
    hdome = A06T_WHEEL["hub"]["dome"]
    hub_ctrl = F.round_rect_xy(-hw / 2, hw / 2, -hh / 2, hh / 2, hr, 6)
    hub_loop = smooth_path([(u, v, 0.0) for (u, v) in hub_ctrl], 64, closed=True)
    hub_outline = [(p[0], p[1]) for p in hub_loop]

    hub_rings = []
    for k in range(7):
        s = 1.0 - k / 6.0
        dome = hdome * (1.0 - s ** 2.2)
        hub_rings.append([fr.p(u * s, v * s, 0.016 + dome) for (u, v) in hub_outline])
    hub_rings[-1] = [fr.p(0.0, 0.0, 0.016 + hdome)] * len(hub_outline)
    hub_pad = grid_mesh("int_wheel_hub_pad", hub_rings, col, lib["leather_purple"], wrap_t=True)
    M.orient(hub_pad.data, lambda c: tuple(fr.A))
    made.append(hub_pad)

    # Hub housing stepping back to steering column
    back_rings = []
    for k, (s, w) in enumerate(((1.0, 0.016), (1.03, 0.008), (1.04, -0.006), (0.88, -0.026), (0.55, -A06T_WHEEL["hub"]["depth"]))):
        back_rings.append([fr.p(u * s, v * s, w) for (u, v) in hub_outline])
    hub_back = grid_mesh("int_wheel_hub_housing", back_rings, col, lib["trim_purple"], wrap_t=True)
    M.orient(hub_back.data, lambda c: tuple(fr.A))
    made.append(hub_back)

    # Tailored decorative stitch line inset 6.5 mm on horn pad face
    stitch_pad_pts, stitch_pad_nrm = [], []
    for u, v in hub_outline:
        stitch_pad_pts.append(fr.p(u * 0.88, v * 0.88, 0.016 + hdome * (1.0 - 0.88 ** 2.2) + 0.0006))
        stitch_pad_nrm.append(tuple(fr.A))
    from carkit.interior.sweep import stitches
    made.append(stitches("int_wheel_HubStitch", stitch_pad_pts + [stitch_pad_pts[0]], stitch_pad_nrm + [stitch_pad_nrm[0]],
                         col, lib["thread_purple"], stitch=0.0032, gap=0.0016))

    # 3. Discrete Faceted Avatr Logo Badge
    made += _emblem(fr, col, lib)

    # 4. Steering Column Shroud
    col_path = [fr.p(0.0, -0.012, -0.030 - 0.200 * k / 8.0) for k in range(9)]
    made.append(tube("int_wheel_column", col_path, [(ca * 0.038, cb * 0.032) for (ca, cb) in ellipse(1, 1, 16)], col,
                     lib["trim_purple"], lateral=tuple(fr.V), scale=lambda s: (1.0 + 0.15 * s, 1.0 + 0.2 * s)))

    # 5. Continuous Satin-Metal Accent Ribbon & Bezel
    flat_metal = [(math.copysign(abs(math.cos(t)) ** 0.35, math.cos(t)), math.copysign(abs(math.sin(t)) ** 0.35, math.sin(t)))
                  for t in [2 * math.pi * k / 16 for k in range(16)]]

    def ribbon(name, pts_uv, width=0.0075, thick=0.0055, w_lift=0.0135, taper=0.0):
        path = smooth_path([fr.p(u, v, w_lift) for (u, v) in pts_uv], 36)
        return tube(name, path, [(0.5 * thick * p0, 0.5 * width * p1) for (p0, p1) in flat_metal], col,
                    lib["satin_metal"], lateral=tuple(fr.A), scale=lambda s: (1.0, 1.0 - taper * s))

    # Lower hub cradle ribbon
    cradle_pts = [
        (-0.062, 0.018), (-0.060, -0.016), (-0.048, -0.044), (-0.026, -0.052),
        (0.000, -0.054), (0.026, -0.052), (0.048, -0.044), (0.060, -0.016), (0.062, 0.018)
    ]
    made.append(ribbon("int_wheel_Frame_Cradle", cradle_pts, width=0.007, thick=0.005, w_lift=0.013))

    # 6. Bottom Vertical Spoke: Sculpted twin-blade architectural design with hollow slot
    v_top_spoke = -0.050
    v_bot_spoke = -(b - 0.004)
    blade_L = [(-0.013, v_top_spoke), (-0.015, (v_top_spoke + v_bot_spoke) * 0.5), (-0.016, v_bot_spoke)]
    blade_R = [(0.013, v_top_spoke), (0.015, (v_top_spoke + v_bot_spoke) * 0.5), (0.016, v_bot_spoke)]
    made.append(ribbon("int_wheel_Spoke_BladeL", blade_L, width=0.007, thick=0.006, w_lift=0.011))
    made.append(ribbon("int_wheel_Spoke_BladeR", blade_R, width=0.007, thick=0.006, w_lift=0.011))
    # Bottom clasp cuff onto flat rim
    made.append(F.box(col, "int_wheel_Spoke_Clasp", fr.p(0.0, v_bot_spoke + 0.004, 0.007), (0.034, 0.010, 0.012),
                      lib["satin_metal"], r=0.003))

    # 7. Horizontal Spokes: Layered Leather Bridge + Satin Lower Cradle + Control Pods
    for side, tag in ((1.0, "R"), (-1.0, "L")):
        # Leather upper bridge
        bridge_pts = [(side * 0.056, 0.018), (side * 0.100, 0.020), (side * (a - 0.008), 0.018)]
        bridge_mesh = tube("int_wheel_Bridge_" + tag, [fr.p(u, v, 0.009) for (u, v) in bridge_pts],
                           [(ca * 0.010, cb * 0.014) for (ca, cb) in ellipse(1, 1, 12)], col,
                           lib["leather_purple"], lateral=tuple(fr.A))
        made.append(bridge_mesh)

        # Satin lower frame ribbon
        pod_ribbon = [
            (side * 0.056, 0.000), (side * 0.080, -0.006), (side * 0.115, -0.006),
            (side * 0.142, 0.004), (side * (a - 0.008), 0.016)
        ]
        made.append(ribbon("int_wheel_Pod_Frame_" + tag, pod_ribbon, width=0.0065, thick=0.005, w_lift=0.012))

        # Recessed dark control pod face
        pod_cu, pod_cv = side * 0.098, 0.008
        made.append(F.box(col, "int_wheel_Pod_Face_" + tag, fr.p(pod_cu, pod_cv, 0.012), (0.038, 0.019, 0.006),
                          lib["piano"], r=0.003))

        # Precision tactile knurled roller
        roller_pos = fr.p(side * 0.098, 0.008, 0.015)
        made += F.disc(col, "int_wheel_Roller_" + tag, roller_pos, tuple(fr.A), 0.0075,
                       lib["piano"], dome=0.002, rim=0.0015, rim_mat=lib["satin_metal"])

        # Flanking micro-switches
        btn_in_pos = fr.p(side * 0.082, 0.008, 0.0135)
        made += F.disc(col, "int_wheel_BtnIn_" + tag, btn_in_pos, tuple(fr.A), 0.0042,
                       lib["satin_metal"], dome=0.0010, rim=0.0008, rim_mat=lib["piano"])
        btn_out_pos = fr.p(side * 0.114, 0.008, 0.0135)
        made += F.disc(col, "int_wheel_BtnOut_" + tag, btn_out_pos, tuple(fr.A), 0.0042,
                       lib["satin_metal"], dome=0.0010, rim=0.0008, rim_mat=lib["piano"])

    made += build_stalks(col, lib, fr)
    return made


def _rim_stitch(fr, col, lib):
    """Tone-on-tone stitching round the rim's inner edge."""
    from carkit.interior.sweep import stitches
    a, b = A06T_WHEEL["loop"]["a"], A06T_WHEEL["loop"]["b"]
    e = A06T_WHEEL["loop"]["n"]
    rr = A06T_WHEEL["section"][0]
    pts, nrm = [], []
    for k in range(181):
        t = 2.0 * math.pi * k / 180
        c, s_ = math.cos(t), math.sin(t)
        u = a * math.copysign(abs(c) ** (2.0 / e), c)
        v = b * math.copysign(abs(s_) ** (2.0 / e), s_)
        L = math.hypot(u, v)
        k_in = (L - rr * 0.72) / L
        pts.append(fr.p(u * k_in, v * k_in, 0.007))
        nrm.append(tuple(fr.A))
    return [stitches("int_wheel_Stitch", pts, nrm, col, lib["thread_purple"], stitch=0.0035, gap=0.0018)]


def build_stalks(col, lib, fr):
    """The wiper stalk (left) and the column drive selector (right), satin-tipped (c10_0013 / c10_0014)."""
    made = []
    for side, tag, ln in ((-1.0, "L", 0.115), (1.0, "R", 0.120)):
        a = Vector(fr.p(side * 0.050, 0.040, -0.075))
        b = Vector(fr.p(side * (0.050 + ln), 0.052, -0.050))
        path = [tuple(a.lerp(b, t / 10.0)) for t in range(11)]
        made.append(tube("int_wheel_stalk" + tag, path, ellipse(0.0070, 0.0062, 12), col, lib["trim_purple"],
                         lateral=tuple(fr.A), scale=lambda s: (1.0 - 0.15 * s, 1.0 - 0.15 * s)))
        tip = [tuple(b.lerp(b + (b - a).normalized() * 0.028, t / 6.0)) for t in range(7)]
        made.append(tube("int_wheel_stalkTip" + tag, tip, ellipse(0.0072, 0.0068, 12), col, lib["satin_metal"],
                         lateral=tuple(fr.A), scale=lambda s: (1.0 - 0.3 * s ** 3, 1.0 - 0.3 * s ** 3)))
    return made
