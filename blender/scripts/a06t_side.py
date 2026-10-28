"""Avatr 06T side details, read off the left-side photograph c1_0004.jpg (a06t_cam.py) and the detail
close-ups c12_0005..0016:

    mirrors     the electronic exterior mirrors: a long, slim black blade from the A-pillar's foot, a
                camera pod at its tip facing aft, a thin light strip along its top edge and a surround
                camera under it (no mirror glass)
    handles     flush handles in a dark pocket: front door x -0.04..0.18, rear door x -1.06..-0.85
    pinstripe   the thin chrome line along the lower edge of the black rocker cladding
    blade       the black "AVATR" blade with a camera lens at its front tip, on the fender and door
    roof rails  slim black rails along the roof edges, x -1.60 .. 0.02, on short posts
    charge flap the left-rear quarter's flap outline
"""
import math

import a06t_surface as S
import a06t_nose as N
import a06t_panels as PN
import a06t_cam as CAM
from carkit import geom
from carkit import mesh as M
from carkit.parts import aero, fittings, lamps

BODY = N.BODY
proud = BODY.proud


def on_flank(x, z, d=0.0):
    p, n = BODY.side_point(x, z)
    return (p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d), n


def _superellipse(cx, cz, hx, hz, n, e=0.55):
    out = []
    for j in range(n):
        a = 2.0 * math.pi * j / n
        c, s = math.cos(a), math.sin(a)
        out.append((cx + hx * math.copysign(abs(c) ** e, c), cz + hz * math.copysign(abs(s) ** e, s)))
    return out


# ------------------------------------------------------------------ mirrors
Y_TIP = 1.035                       # c1_0002: the mirrors' outer tips are at 1.03
MIRROR_Z = (0.985, 1.078)


def build_mirrors(collection, lib):
    """A slim black camera blade: lofted along y from the A-pillar's foot (x 0.585 .. 0.905 deep, 93 mm
    tall) to the tip (0.10 m deep, 56 mm tall), with the camera pod's lens on its aft face."""
    made = []
    p0, _n0 = on_flank(0.78, 1.00)
    y0 = p0[1] - 0.012
    ns, nr = 22, 22
    verts, faces = [], []
    for i in range(ns + 1):
        s = i / float(ns)
        y = y0 + (Y_TIP - y0) * s
        x_rear = 0.585 + 0.030 * s
        x_front = 0.905 - 0.225 * s ** 1.15
        z_hi = MIRROR_Z[1] - 0.020 * s
        z_lo = MIRROR_Z[0] + 0.010 * s + 0.012 * s * s
        for (x, z) in _superellipse(0.5 * (x_rear + x_front), 0.5 * (z_lo + z_hi),
                                    0.5 * (x_front - x_rear), 0.5 * (z_hi - z_lo), nr):
            verts.append((x, y, z))
    for i in range(ns):
        for j in range(nr):
            a0, a1 = i * nr + j, i * nr + (j + 1) % nr
            b0, b1 = (i + 1) * nr + j, (i + 1) * nr + (j + 1) % nr
            faces.append([a0, a1, b1, b0])
    tip = len(verts)
    ys = y0 + (Y_TIP - y0)
    verts.append((0.5 * (0.615 + 0.680), Y_TIP + 0.006, 0.5 * (MIRROR_Z[0] + 0.022 + MIRROR_Z[1] - 0.020)))
    for j in range(nr):
        faces.append([ns * nr + j, ns * nr + (j + 1) % nr, tip])
    arm = M.obj("A06T_Mirror_Head", verts, faces, collection, lib["black_gloss"])
    M.orient(arm.data, geom.away_from((0.75, 0.0, 1.03)))
    M.mirror_y(arm)
    made.append(arm)

    # the camera pod's lens, facing aft on the tip, and the surround camera on the underside
    z_mid = 0.5 * (MIRROR_Z[0] + 0.022 + MIRROR_Z[1] - 0.020)
    made += lamps.projector("A06T_Mirror_Cam1", (0.598, Y_TIP - 0.020, z_mid), (-1.0, 0.0, 0.0), 0.021,
                            collection, lib, mats=("lamp_bowl", "lamp_smoked"))
    made += lamps.projector("A06T_Mirror_Cam2", (0.77, y0 + 0.62 * (Y_TIP - y0), MIRROR_Z[0] + 0.004),
                            (0.0, 0.0, -1.0), 0.016, collection, lib, mats=("lamp_bowl", "lamp_smoked"))

    # the light strip along the top edge (a pale grey line, just proud)
    rows = []
    for i in range(0, 15):
        s = 0.10 + 0.82 * i / 14.0
        y = y0 + (Y_TIP - y0) * s
        x_rear = 0.585 + 0.030 * s
        z_hi = MIRROR_Z[1] - 0.020 * s
        rows.append([(x_rear + 0.030, y, z_hi - 0.0005), (x_rear + 0.038, y, z_hi + 0.0008)])
    strip = M.grid("A06T_Mirror_Strip", rows, collection, lib["stripe"], geom.away_from((0.7, 0.0, 0.9)))
    M.solidify(strip, 0.0015)
    M.mirror_y(strip)
    made.append(strip)
    return made


# ------------------------------------------------------------------ handles
HANDLES = (("F", 0.178, -0.040, 0.862), ("R", -0.850, -1.062, 0.887))


def build_handles(collection, lib):
    return [fittings.flush_handle("A06T_Handle_" + nm, x0, x1, zc, proud, collection,
                                  lib["black_gloss"], h=0.030, d=0.0012)
            for nm, x0, x1, zc in HANDLES]


# ---------------------------------------------------------- rocker pinstripe
X_SKIRT_F = S.FRONT_AXLE - S.ARCH_R + 0.005
X_SKIRT_R = S.REAR_AXLE + S.ARCH_R - 0.005


def build_skirts(collection, lib):
    z0 = lambda x: S.Z_FLOOR(x) + 0.010
    z1 = lambda x: S.Z_FLOOR(x) + 0.017
    return [fittings.surface_band("A06T_Skirt_Line", lambda k: X_SKIRT_R + 0.01,
                                  lambda k: X_SKIRT_F - 0.01, z0, z1,
                                  lambda p, d: proud(p, 0.0035), collection,
                                  lib["chrome"], 64)]


# ------------------------------------------------------------- the AVATR blade
def _blade_outline():
    return [(x, z) for (x, z) in CAM.xz(CAM.BLADE_PX, 0.93)]


def build_vent(collection, lib):
    """The black blade on the fender and the door's front corner (c1_0004: x 0.86..1.21, z 0.70..0.75,
    pointed at both ends), in two pieces so the door's half goes with the door; a camera lens near
    its front tip."""
    made = []
    pts = _blade_outline()
    # upper edge (left to right in the picture = front to back) and lower edge, as z(x)
    top = sorted((x, z) for (x, z) in pts if z >= 0.715)
    bot = sorted((x, z) for (x, z) in pts if z < 0.715)
    x_door = PN._DOOR_F_EDGE(0.725)

    def piece(name, xa, xb, n=14):
        rows = []
        for i in range(n + 1):
            x = xa + (xb - xa) * i / float(n)
            zt = _lerp(top, x)
            zb = _lerp(bot, x)
            rows.append([on_flank(x, zb, 0.0032)[0], on_flank(x, 0.5 * (zt + zb), 0.0040)[0],
                         on_flank(x, zt, 0.0032)[0]])
        ob = M.grid(name, rows, collection, lib["black_gloss"], geom.away_from((x_door, 0.0, 0.72)))
        M.solidify(ob, 0.0020)
        M.mirror_y(ob)
        return ob
    x_a, x_b = min(p[0] for p in pts), max(p[0] for p in pts)
    made.append(piece("A06T_Blade_Fender", x_door + 0.012, x_b))
    made.append(piece("A06T_Blade_Door", x_a, x_door - 0.012))
    # the camera lens near the front tip
    p, n = on_flank(x_b - 0.045, 0.726, 0.0045)
    made += lamps.projector("A06T_Blade_Lens", p, n, 0.011, collection, lib, mats=("lamp_bowl", "lamp_smoked"))
    return made


def _lerp(pts, x):
    if x <= pts[0][0]:
        return pts[0][1]
    for (a, za), (b, zb) in zip(pts, pts[1:]):
        if a <= x <= b:
            return za + (zb - za) * (x - a) / max(1e-9, b - a)
    return pts[-1][1]


# ---------------------------------------------------------------- roof rails
def build_roof_rails(collection, lib):
    """Slim black roof rails along each roof edge on short posts (x -1.60 .. 0.02), with a thin
    machined line along the inner side (c1_0004: black rail, silver inset)."""
    from carkit.interior.sweep import tube, ellipse
    made = []
    x_a, x_b = -1.60, 0.02
    n = 56
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        bar, base, inset = [], [], []
        for i in range(n + 1):
            x = x_a + (x_b - x_a) * i / float(n)
            # the rails draw in toward the rear (c1_0006: their ends stand ~2.5 cm closer than the old line) and
            # stand 3 cm, not 4.7 cm, over the roof's edge (c1_0004: the rail's top is 1.508, the roof edge ~1.48)
            y_want = S.Y_ROOF(x) - 0.030 - 0.022 * geom.smoothstep((-0.90 - x) / 0.70)
            v = S.v_at_y_upper(x, y_want)
            p, nr = S.surface(x, v), S.surface_normal(x, v)
            foot = min(1.0, 8.0 * (i / float(n)), 8.0 * (1.0 - i / float(n)))
            lift = 0.010 + 0.008 * foot * foot * (3.0 - 2.0 * foot)
            bar.append((p[0] + nr[0] * lift, side * abs(p[1] + nr[1] * lift), p[2] + nr[2] * lift))
            base.append((p[0] + nr[0] * 0.003, side * abs(p[1] + nr[1] * 0.003), p[2] + nr[2] * 0.003))
            inset.append((p[0] + nr[0] * (lift - 0.002), side * (abs(p[1]) - 0.0085), p[2] + nr[2] * (lift - 0.002)))
        sc = lambda s: (min(1.0, 16.0 * s, 16.0 * (1.0 - s)) * 0.6 + 0.4,) * 2
        made.append(tube("A06T_RoofRail_Bar" + tag, bar, ellipse(0.0100, 0.0125, 10), collection,
                         lib["black_gloss"], closed=False, lateral=(0.0, 1.0, 0.0), scale=sc))
        made.append(tube("A06T_RoofRail_Base" + tag, base, ellipse(0.0150, 0.0050, 10), collection,
                         lib["black_gloss"], closed=False, lateral=(0.0, 1.0, 0.0), scale=sc))
        made.append(tube("A06T_RoofRail_Inset" + tag, inset[3:-3], ellipse(0.0022, 0.0022, 6), collection,
                         lib["machined"], closed=False, lateral=(0.0, 1.0, 0.0)))
    return made


# ------------------------------------------------------------ charge flap
def build_charge_door(collection, lib):
    """The left-rear quarter's charge flap: a flat rounded oval x -1.88..-1.54, z 0.92..1.04."""
    return [fittings.outline_ring("A06T_Charge_Line", -1.880, -1.540, 0.920, 1.040, 0.050,
                                  proud, collection, lib["shadow"], y_ref=0.90)]


def build_all(collection, lib):
    made = []
    made += build_mirrors(collection, lib)
    made += build_handles(collection, lib)
    made += build_skirts(collection, lib)
    made += build_vent(collection, lib)
    made += build_roof_rails(collection, lib)
    made += build_charge_door(collection, lib)
    return made
