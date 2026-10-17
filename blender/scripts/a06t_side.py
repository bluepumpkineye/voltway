"""Avatr 06T side details: electronic-mirror stalks, semi-concealed flush
handles, sculpted rocker with silver blade, the fender camera gill, raised
roof luggage rails, the left-rear charge flap.

    mirrors     slim camera stalks (no mirror glass) at the door's upper
                front corner - the 06T's FHD electronic exterior mirrors
    handles     semi-concealed flush, front door x -0.03..-0.23, rear door
                x -0.96..-1.16
    rocker      gloss black from arch to arch, z 0.185-0.290, silver line on top
    gill        black fender camera blade ahead of the front door
    roof rails  raised black/silver luggage rails along the roof's edges
                (75 kg rated), ends on mounting feet
    charge flap left rear quarter only
"""
import math

import a06t_surface as S
import a06t_nose as N
import a06t_panels as PN
from carkit import geom
from carkit import mesh as M
from carkit.parts import aero, fittings

BODY = N.BODY
proud = BODY.proud


def on_flank(x, z, d=0.0):
    p, n = BODY.side_point(x, z)
    return (p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d), n


# ------------------------------------------------------------------ mirrors
def build_mirrors(collection, lib):
    """Electronic exterior mirrors: a slim, compact camera pod on a short arm
    from the door's upper front corner (design-list_01.jpg, c1_0002.jpg)."""
    return fittings.mirror_cap("A06T_Mirror", collection, lib,
                               rear=(0.330, 0.990, 1.040), size=(0.150, 0.120, 0.050),
                               arm_base=(0.480, 0.930, 1.000), proud=proud,
                               mats=("black_gloss", "shadow", "black_gloss", "black_gloss"))


# ------------------------------------------------------------------ handles
HANDLES = (("F", -0.030, -0.230, 0.925), ("R", -0.960, -1.160, 0.950))


def build_handles(collection, lib):
    return [fittings.flush_handle("A06T_Handle_" + nm, x0, x1, zc, proud, collection,
                                  lib["black_gloss"], h=0.012, d=0.0012)
            for nm, x0, x1, zc in HANDLES]


# ---------------------------------------------------------------- skirts
X_SKIRT_F = S.FRONT_AXLE - S.ARCH_R + 0.005
X_SKIRT_R = S.REAR_AXLE + S.ARCH_R - 0.005


def build_skirts(collection, lib):
    made = [aero.side_skirt("A06T_Skirt", collection, lib, proud,
                            lambda x: S.Y_ROCKER(x) + 0.02, X_SKIRT_R, X_SKIRT_F,
                            0.185, 0.290, nx=60, nz=6, d=0.010, mat="black_gloss")]
    made.append(fittings.surface_band("A06T_Skirt_Line", lambda k: X_SKIRT_R + 0.02,
                                      lambda k: X_SKIRT_F - 0.02,
                                      lambda x: 0.276, lambda x: 0.285,
                                      lambda p, d: proud(p, 0.0205), collection,
                                      lib["stripe"], 60))
    return made


# ------------------------------------------------------------ fender gill
def build_vent(collection, lib):
    """The dark camera gill behind the fender's cut and a gloss black frame."""
    ring = geom.polyline([(x, 0.95, z) for (x, z) in PN.VENT_OUTLINE + PN.VENT_OUTLINE[:1]],
                         40)[:-1]
    a, b, c = [], [], []
    for (x, _y, z) in ring:
        p, n = on_flank(x, z)
        a.append(p)
        b.append(tuple(p[k] - n[k] * 0.012 for k in range(3)))
        c.append(tuple(p[k] - n[k] * 0.035 for k in range(3)))
    a.append(a[0]); b.append(b[0]); c.append(c[0])
    frame = M.strip("A06T_Vent_Frame", a, b, collection, lib["black_gloss"])
    M.mirror_y(frame)
    cx = [sum(p[k] for p in c) / len(c) for k in range(3)]
    back = M.grid("A06T_Vent_Pocket", [[b[i], c[i], tuple(cx)] for i in range(len(b))],
                  collection, lib["shadow"], geom.const((0.0, 1.0, 0.0)))
    M.mirror_y(back)
    return [frame, back]


# ---------------------------------------------------------------- roof rails
def build_roof_rails(collection, lib):
    """Raised aerodynamic luggage rails along each roof edge: a satin silver
    bar on a black base, standing ~28 mm off the roof on feet at both ends."""
    from carkit.interior.sweep import tube, ellipse
    made = []
    x_a, x_b = -1.74, -0.08
    n = 48
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        bar, base = [], []
        for i in range(n + 1):
            x = x_a + (x_b - x_a) * i / float(n)
            y_want = S.Y_ROOF(x) - 0.055
            v = S.v_at_y_upper(x, y_want)
            p, nr = S.surface(x, v), S.surface_normal(x, v)
            foot = min(1.0, 7.0 * (i / float(n)), 7.0 * (1.0 - i / float(n)))
            lift = 0.012 + 0.020 * foot * foot * (3.0 - 2.0 * foot) / 1.0
            bar.append((p[0] + nr[0] * lift, side * abs(p[1] + nr[1] * lift), p[2] + nr[2] * lift))
            base.append((p[0] + nr[0] * 0.004, side * abs(p[1] + nr[1] * 0.004), p[2] + nr[2] * 0.004))
        made.append(tube("A06T_RoofRail_Bar" + tag, bar, ellipse(0.0100, 0.0115, 10), collection,
                         lib["machined"], closed=False, lateral=(0.0, 1.0, 0.0),
                         scale=lambda s: (min(1.0, 14.0 * s, 14.0 * (1.0 - s)) * 0.6 + 0.4,) * 2))
        made.append(tube("A06T_RoofRail_Base" + tag, base, ellipse(0.0150, 0.0060, 10), collection,
                         lib["black_gloss"], closed=False, lateral=(0.0, 1.0, 0.0),
                         scale=lambda s: (min(1.0, 14.0 * s, 14.0 * (1.0 - s)) * 0.6 + 0.4,) * 2))
    return made


# ------------------------------------------------------------ charge flap
def build_charge_door(collection, lib):
    return [fittings.outline_ring("A06T_Charge_Line", -2.100, -1.900, 0.840, 0.965, 0.030,
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
