"""Detail parts for the SU7 Ultra: glass, lights, aero, mirrors, wheels."""
import bpy
import math
from mathutils import Matrix

import lib_build as L


def box(col, name, cx, cy, cz, sx, sy, sz, rot_y=0.0, rot_z=0.0):
    """Box centred at (cx, cy, cz), optionally pitched about Y then yawed about Z."""
    hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
    pts = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
           (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    cyy, syy = math.cos(rot_y), math.sin(rot_y)
    czz, szz = math.cos(rot_z), math.sin(rot_z)
    verts = []
    for (x, y, z) in pts:
        x, z = x * cyy + z * syy, -x * syy + z * cyy
        x, y = x * czz - y * szz, x * szz + y * czz
        verts.append((cx + x, cy + y, cz + z))
    faces = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4],
             [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    return L.new_mesh_object(name, verts, faces, col)


def bevel(ob, width=0.012, segments=2):
    m = ob.modifiers.new("Bevel", 'BEVEL')
    m.width = width
    m.segments = segments
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(40)
    return m


# --------------------------------------------------------------------- glass
def build_glass(col, half_section, x_front, x_rear, stations=60,
                lo_frac=0.605, offset=0.008):
    """Dark canopy over the greenhouse, sampled from the body's own sections.

    The band is taken as a fixed fraction of each section's arc rather than by
    a z threshold. A z threshold picks a different number of points per station
    and tears the surface around the A-pillar; an arc fraction always yields the
    same count, so the loft stays quad-clean the whole way down the car.
    """
    n_band = 18
    rings = []
    for i in range(stations):
        u = i / (stations - 1.0)
        x = x_front + (x_rear - x_front) * u
        sec = half_section(x)
        n = len(sec)
        lo = int(round(lo_frac * (n - 1)))
        band = sec[lo:]
        idx = [int(round(k * (len(band) - 1) / (n_band - 1.0))) for k in range(n_band)]
        band = [band[k] for k in idx]

        right = [(x, y + offset, z + offset * 0.35) for (y, z) in band]
        left = [(x, -y - offset, z + offset * 0.35) for (y, z) in reversed(band)]
        rings.append(left + right)

    ob = L.loft(rings, col, "SU7_Glass", cap_front=False, cap_rear=False)
    L.merge_doubles(ob, 0.0006)
    L.shade_smooth(ob)
    return ob


# -------------------------------------------------------------------- lights
def build_lights(col, half_l, curves):
    y_at = curves["y_at"]
    made = []

    x_h, z_h = half_l - 0.325, 0.735
    y_h = y_at(x_h, z_h)
    for sgn in (1, -1):
        tag = 'L' if sgn > 0 else 'R'
        h = box(col, "SU7_Headlight_" + tag,
                x_h, sgn * (y_h - 0.185), z_h,
                0.245, 0.345, 0.062,
                rot_y=math.radians(-6), rot_z=math.radians(sgn * 11))
        bevel(h, 0.012, 2)
        made.append(h)

    x_t, z_t = -half_l + 0.135, 0.895
    y_t = y_at(x_t, z_t)
    tl = box(col, "SU7_Taillight", x_t, 0.0, z_t, 0.062, y_t * 2.0 * 0.90, 0.072)
    bevel(tl, 0.014, 2)
    made.append(tl)

    x_r, z_r = -half_l + 0.125, 0.545
    y_r = y_at(x_r, z_r)
    for sgn in (1, -1):
        tag = 'L' if sgn > 0 else 'R'
        r = box(col, "SU7_RearRefl_" + tag,
                x_r, sgn * (y_r - 0.155), z_r, 0.040, 0.255, 0.036)
        bevel(r, 0.009, 2)
        made.append(r)
    return made


# ---------------------------------------------------------------------- aero
def build_aero(col, half_l, rear_axle, curves):
    """Aero parts positioned from the body's own profile curves.

    Hand-picked coordinates leave splitters and skirts floating in space, so
    every part here is anchored to w_max / z_bot / z_top at its own station.
    """
    w_max = curves["w_max"]
    z_bot = curves["z_bot"]
    z_top = curves["z_top"]
    y_at = curves["y_at"]
    made = []

    # front splitter: sits under the fascia, no wider than the nose above it
    x_sp = half_l - 0.235
    z_sp = z_bot(x_sp) - 0.006
    sp = box(col, "SU7_Splitter", x_sp, 0.0, z_sp,
             0.34, y_at(x_sp, z_sp + 0.030) * 2.0 * 1.03, 0.024)
    bevel(sp, 0.008, 2)
    made.append(sp)

    # side skirts: hug the rocker at their own height, not at the beltline
    x_sk = 0.05
    z_sk = z_bot(x_sk) + 0.058
    y_sk = y_at(x_sk, z_sk)
    for sgn in (1, -1):
        tag = 'L' if sgn > 0 else 'R'
        sk = box(col, "SU7_Skirt_" + tag, x_sk,
                 sgn * (y_sk + 0.014), z_sk, 2.52, 0.055, 0.070)
        bevel(sk, 0.011, 2)
        made.append(sk)

    # rear diffuser
    x_df = -half_l + 0.26
    z_df = z_bot(x_df) + 0.030
    df = box(col, "SU7_Diffuser", x_df, 0.0, z_df,
             0.42, y_at(x_df, z_df + 0.045) * 2.0 * 0.94, 0.135,
             rot_y=math.radians(11))
    bevel(df, 0.010, 2)
    made.append(df)

    # fixed rear wing, standing off the decklid
    x_wg = rear_axle - 0.78
    z_deck = z_top(x_wg)
    z_blade = z_deck + 0.175
    half_span = w_max(x_wg) * 0.80
    blade = box(col, "SU7_Wing_Blade", x_wg, 0.0, z_blade,
                0.285, half_span * 2.0, 0.026, rot_y=math.radians(7))
    bevel(blade, 0.007, 2)
    made.append(blade)
    for sgn in (1, -1):
        tag = 'L' if sgn > 0 else 'R'
        ep = box(col, "SU7_Wing_End_" + tag, x_wg, sgn * half_span,
                 z_blade - 0.045, 0.320, 0.018, 0.170)
        bevel(ep, 0.006, 2)
        made.append(ep)
        st = box(col, "SU7_Wing_Stay_" + tag, x_wg + 0.010, sgn * half_span * 0.62,
                 (z_blade + z_deck) / 2.0 - 0.010, 0.062, 0.026,
                 z_blade - z_deck + 0.030)
        made.append(st)
    return made


def build_mirrors(col, curves):
    w_max = curves["w_max"]
    x_m = 0.855
    y_body = w_max(x_m)
    made = []
    for sgn in (1, -1):
        tag = 'L' if sgn > 0 else 'R'
        arm = box(col, "SU7_MirrorArm_" + tag, x_m, sgn * (y_body + 0.020),
                  1.012, 0.048, 0.090, 0.032)
        made.append(arm)
        pod = box(col, "SU7_MirrorPod_" + tag, x_m - 0.015,
                  sgn * (y_body + 0.105), 1.034,
                  0.128, 0.108, 0.068, rot_z=math.radians(sgn * -6))
        bevel(pod, 0.020, 3)
        made.append(pod)
    return made


# -------------------------------------------------------------------- wheels
def _ring(verts, cx, y, radius, wheel_r, seg):
    base = len(verts)
    for i in range(seg):
        a = 2.0 * math.pi * i / seg
        verts.append((cx + radius * math.cos(a), y, wheel_r + radius * math.sin(a)))
    return base


def build_wheel_assembly(col, name, cx, cy, sgn, wheel_r, tyre_w):
    """Tyre, dished rim, twin spokes, brake disc and caliper."""
    parts = []
    seg = 44
    hw = tyre_w / 2.0
    r_bead = wheel_r * 0.742
    y_out = cy + sgn * hw
    y_in = cy - sgn * hw

    # ---- tyre
    verts, faces = [], []
    t_o = _ring(verts, cx, cy + sgn * hw * 0.80, wheel_r, wheel_r, seg)
    t_i = _ring(verts, cx, cy - sgn * hw * 0.80, wheel_r, wheel_r, seg)
    b_o = _ring(verts, cx, y_out, r_bead, wheel_r, seg)
    b_i = _ring(verts, cx, y_in, r_bead, wheel_r, seg)
    for a, b in ((t_o, t_i), (b_o, t_o), (t_i, b_i)):
        for i in range(seg):
            j = (i + 1) % seg
            faces.append([a + i, a + j, b + j, b + i])
    c_in = len(verts)
    verts.append((cx, y_in, wheel_r))
    for i in range(seg):
        j = (i + 1) % seg
        faces.append([b_i + j, b_i + i, c_in])
    tyre = L.new_mesh_object(name + "_Tyre", verts, faces, col)
    L.merge_doubles(tyre, 0.0006)
    L.shade_smooth(tyre)
    parts.append(tyre)

    # ---- rim barrel and hub face
    verts, faces = [], []
    ba_o = _ring(verts, cx, y_out - sgn * 0.014, r_bead * 0.99, wheel_r, seg)
    ba_i = _ring(verts, cx, cy - sgn * hw * 0.55, r_bead * 0.99, wheel_r, seg)
    for i in range(seg):
        j = (i + 1) % seg
        faces.append([ba_o + i, ba_o + j, ba_i + j, ba_i + i])
    hub_r = _ring(verts, cx, cy - sgn * hw * 0.05, wheel_r * 0.200, wheel_r, seg)
    hub_c = len(verts)
    verts.append((cx, cy - sgn * hw * 0.12, wheel_r))
    for i in range(seg):
        j = (i + 1) % seg
        faces.append([hub_r + j, hub_r + i, hub_c])
    rim = L.new_mesh_object(name + "_Rim", verts, faces, col)
    L.merge_doubles(rim, 0.0006)
    L.shade_smooth(rim)
    parts.append(rim)

    # ---- ten spokes, rotated into the wheel plane about the axle
    spoke_y = cy - sgn * hw * 0.30
    for k in range(10):
        a = 2.0 * math.pi * k / 10.0 + math.radians(9)
        rmid = wheel_r * 0.455
        px = cx + rmid * math.cos(a)
        pz = wheel_r + rmid * math.sin(a)
        sp = box(col, name + "_Spoke%d" % k, px, spoke_y, pz,
                 wheel_r * 0.585, 0.028, 0.050)
        piv = (px, spoke_y, pz)
        M = (Matrix.Translation(piv) @ Matrix.Rotation(-a, 4, 'Y') @
             Matrix.Translation((-piv[0], -piv[1], -piv[2])))
        sp.data.transform(M)
        sp.data.update()
        parts.append(sp)

    # ---- brake disc
    verts, faces = [], []
    d_o = _ring(verts, cx, cy - sgn * hw * 0.36, wheel_r * 0.675, wheel_r, seg)
    d_i = _ring(verts, cx, cy - sgn * hw * 0.24, wheel_r * 0.675, wheel_r, seg)
    for i in range(seg):
        j = (i + 1) % seg
        faces.append([d_o + i, d_o + j, d_i + j, d_i + i])
    co = len(verts)
    verts.append((cx, cy - sgn * hw * 0.36, wheel_r))
    for i in range(seg):
        j = (i + 1) % seg
        faces.append([d_o + j, d_o + i, co])
    ci = len(verts)
    verts.append((cx, cy - sgn * hw * 0.24, wheel_r))
    for i in range(seg):
        j = (i + 1) % seg
        faces.append([d_i + i, d_i + j, ci])
    disc = L.new_mesh_object(name + "_Disc", verts, faces, col)
    L.merge_doubles(disc, 0.0006)
    L.shade_smooth(disc)
    parts.append(disc)

    cal = box(col, name + "_Caliper", cx - wheel_r * 0.505, cy - sgn * hw * 0.30,
              wheel_r + wheel_r * 0.435, 0.095, 0.058, 0.230)
    bevel(cal, 0.009, 2)
    parts.append(cal)

    return parts
