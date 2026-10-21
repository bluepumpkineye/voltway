"""BYD Seal EV panel layout: shut lines, window lines, panels, openings.

Built on carkit (carkit.body.panels, carkit.cut), calibrated to BYD Seal EV
(Autohome Series 6394) studio references and technical dimensions.

Dimensions & Stations:
    Length: 4800 mm, Width: 1875 mm, Height: 1460 mm, Wheelbase: 2920 mm.
    Front axle: +1.5200 m, Rear axle: -1.4000 m.
    Cowl at x = +0.8500 m (extended hood-to-windshield ratio), Backlight base at x = -2.0800 m.
"""
import math
import bpy

import seal_surface as S
import seal_nose as N
from carkit.geom import (
    Curve, clamp01 as _clamp01, smoothstep as _smooth, ramp as _ramp,
)
from carkit import mesh as M
from carkit import cut as C
from carkit.body import panels as BP

GAP = BP.GAP
SKIN = M.SKIN

# ----------------------------------------------------------------- stations
X_COWL = S.COWL_X            # +0.8500 m: windscreen base / A-pillar foot (cab-rearward silhouette)
X_BPILLAR_F = -0.1100        # front door | rear door shut line
X_BACKLIGHT = S.BACKLIGHT_X  # -1.9600 m: fastback backlight base (lengthened rear deck)
X_ROOF_F = 0.2200            # windscreen header
X_ROOF_R = -1.1200           # backlight header
X_QTR_F = -0.9200            # rear door window / quarter glass divider
X_QTR_R = -1.3800            # sleek coupe quarter glass rear apex

# Narrowed coupe-sedan greenhouse glass height
V_BELT = S.V_SHOULDER + 0.030
V_REARGLASS = 0.700          # fastback backlight width

# Curved front & rear door shut lines scaled to 2920 mm wheelbase & cab-rearward cowl
_DOOR_F_EDGE = Curve([
    (0.199, 0.865), (0.274, 0.868), (0.389, 0.882), (0.518, 0.892),
    (0.648, 0.895), (0.777, 0.888), (0.867, 0.868), (0.937, 0.852),
    (1.076, 0.845),
], mode="pchip")

_DOOR_R_EDGE = Curve([
    (0.199, -0.710), (0.289, -0.740), (0.419, -0.860), (0.488, -0.910),
    (0.548, -0.950), (0.613, -0.990), (0.678, -1.040), (0.733, -1.090),
    (0.792, -1.120), (0.872, -1.140), (0.942, -1.130), (1.037, -1.070),
    (1.116, -1.055),
], mode="pchip")


def X_DOOR_F(v):
    return _DOOR_F_EDGE(S.section_v(0.86, v)[1])


def X_DOOR_R(v):
    return _DOOR_R_EDGE(S.section_v(-1.00, v)[1])


def V_SILL(x):
    return S.v_at_z(x, S.Z_FLOOR(x) + 0.030, 0.0, S.V_SHOULDER)


# Hood side shut line along muscular fender crown to headlamp upper edge
Y_HOOD = Curve([
    (S.COWL_X, 0.700), (1.120, 0.745), (1.500, 0.765), (1.760, 0.775),
    (1.900, 0.825), (2.000, 0.765), (2.100, 0.650), (2.190, 0.455),
    (2.260, 0.305), (2.305, 0.230),
])


def V_HOOD(x):
    return S.v_at_y_upper(x, Y_HOOD(x))


def V_GT(x):
    """Top of the side glass: 105 mm below the roof rail outer edge for a sleeker coupe greenhouse."""
    return S.v_along(x, S.v_rail(x), -0.105)


def V_RAIL(x):
    """Inboard edge of the body-colour roof rail."""
    return S.v_along(x, S.v_rail(x), 0.050)


def V_A(x):
    """A-pillar glass edge from cowl to windscreen header."""
    if x <= X_ROOF_F:
        return V_GT(x) + 0.020
    t = (X_COWL - x) / (X_COWL - X_ROOF_F)
    top = V_GT(X_ROOF_F) + 0.020
    return (V_BELT + 0.022) + (top - V_BELT - 0.022) * _smooth(t)


_QTR_TIP = []


def V_QTR_TIP():
    if not _QTR_TIP:
        _QTR_TIP.append(S.v_at_z(X_QTR_R, 1.105, S.V_SHOULDER, 1.0))
    return _QTR_TIP[0]


def V_QTR_LOW(x):
    t = (X_QTR_F - x) / (X_QTR_F - X_QTR_R)
    return (V_BELT + 0.010) + (V_QTR_TIP() - V_BELT - 0.010) * (_clamp01(t) ** 1.55)


def V_C(x):
    t = (X_QTR_F - x) / (X_QTR_F - X_QTR_R)
    hi = V_GT(X_QTR_F) + 0.020
    lo = V_QTR_TIP() + 0.020
    return hi - (hi - lo) * (_clamp01(t) ** 1.25)


def V_GLASS_TOP(x):
    if x < X_QTR_F:
        return V_C(x) - 0.020
    return min(V_A(x) - 0.020, V_GT(x))


def V_RAIL_TOP(x):
    a = V_A(x) + 0.016
    r = V_RAIL(x)
    c = V_REARGLASS - 0.004
    k_f = _ramp(x, X_ROOF_F)
    k_r = _ramp(x, X_ROOF_R)
    return c + (r - c) * k_r + (a - r) * k_f


def V_DOOR_R_TOP(x):
    return V_BELT + max(0.0, V_QTR_LOW(x) - V_BELT - 0.010)


def _glass_s(v):
    return _clamp01((v - V_BELT) / max(1e-4, (V_GT(-0.20) - V_BELT)))


def GB_F(v):
    return -0.1000 + (-0.2000 + 0.1000) * _glass_s(v)


def GB_R(v):
    return -0.2300 + (-0.2900 + 0.2300) * _glass_s(v)


V_LID_END = 0.760


def V_LID_EDGE(x):
    if x >= X_BACKLIGHT:
        return V_REARGLASS
    x1 = N.JOIN_R(V_LID_END)
    t = _clamp01((X_BACKLIGHT - x) / max(1e-4, X_BACKLIGHT - x1))
    return V_REARGLASS + (V_LID_END - V_REARGLASS) * _smooth(t)


# ------------------------------------------------------------- flank panels
PANELS = [
    # ---- painted sheet metal
    dict(name="Seal_Fender_Front", x=(X_DOOR_F, N.JOIN_F), v=(V_SILL, V_HOOD),
         nx=50, nv=40, arch=True, gap=dict(v0=False), mat="paint"),
    dict(name="Seal_Door_Front", x=(X_BPILLAR_F, X_DOOR_F), v=(V_SILL, V_BELT),
         nx=40, nv=40, arch=True, gap=dict(v0=False), mat="paint"),
    dict(name="Seal_Door_Rear", x=(X_DOOR_R, X_BPILLAR_F), v=(V_SILL, V_DOOR_R_TOP),
         nx=38, nv=40, arch=True, gap=dict(v0=False), mat="paint"),
    dict(name="Seal_Quarter", x=(N.JOIN_R, X_DOOR_R), v=(V_SILL, V_LID_EDGE),
         nx=50, nv=44, arch=True, gap=dict(v0=False, x0=False), mat="paint",
         quarter_light=True),
    dict(name="Seal_Hood", x=(X_COWL, N.JOIN_F), v=(V_HOOD, 1.0),
         nx=60, nv=34, gap=dict(v1=False), mat="paint"),
    dict(name="Seal_Decklid", x=(lambda v: min(N.JOIN_R(v), X_BACKLIGHT - 0.015), X_BACKLIGHT), v=(V_LID_EDGE, 1.0),
         nx=24, nv=30, gap=dict(v1=False, x0=False), mat="paint"),
    dict(name="Seal_Roof_Rail", x=(X_QTR_R, X_COWL),
         v=(lambda x: V_GLASS_TOP(x) + 0.006, V_RAIL_TOP),
         nx=130, nv=10, gap=dict(x0=False), mat="paint"),

    # ---- greenhouse & cowl blackouts (exported into BYDSeal_Blackout)
    dict(name="Seal_Greenhouse_Black", x=(X_QTR_R - 0.030, X_COWL),
         v=(V_BELT, 1.0), nx=100, nv=44,
         gap=dict(v1=False), mat="black_gloss", offset=-0.003, thickness=0.0),
    dict(name="Seal_Cowl_Black", x=(X_COWL - 0.035, X_COWL + 0.025),
         v=(V_HOOD, 1.0), nx=20, nv=24, gap=dict(v1=False), mat="black_gloss",
         offset=-0.004, thickness=0.0),
    dict(name="Seal_Roof_Rear_Black", x=(X_BACKLIGHT, X_ROOF_R),
         v=(V_REARGLASS, 1.0), nx=24, nv=22, gap=dict(v1=False),
         mat="frit", offset=-0.003, thickness=0.0),

    # ---- flush glazing
    dict(name="Seal_Glass_Windshield", x=(X_ROOF_F, X_COWL - 0.012),
         v=(lambda x: V_A(x) + 0.020, 0.9995), nx=68, nv=52, glass="glass",
         gap=dict(v1=False)),
    dict(name="Seal_Glass_Roof", x=(X_ROOF_R + 0.010, X_ROOF_F - 0.015),
         v=(lambda x: V_RAIL(x) + 0.004, 0.9995), nx=48, nv=28, glass="glass_dark",
         gap=dict(v1=False)),
    dict(name="Seal_Glass_DoorFront", x=(GB_F, X_COWL - 0.030),
         v=(V_BELT + 0.010, lambda x: min(V_A(x) - 0.020, V_GT(x))),
         nx=56, nv=28, glass="glass"),
    dict(name="Seal_BPillar_Black", x=(lambda v: GB_R(v) - 0.004, lambda v: GB_F(v) + 0.004),
         v=(V_BELT + 0.010, V_GT), nx=8, nv=28, mat="black_gloss", offset=-0.001, thickness=0.0,
         gap=dict(x0=False, x1=False, v0=False, v1=False)),
    dict(name="Seal_Glass_DoorRear", x=(X_QTR_F + 0.030, GB_R),
         v=(V_BELT + 0.010, V_GT), nx=48, nv=28, glass="glass_dark"),
    dict(name="Seal_Glass_Quarter", x=(X_QTR_R + 0.004, X_QTR_F),
         v=(V_QTR_LOW, lambda x: V_C(x) - 0.020), nx=24, nv=14,
         glass="glass_dark"),
    dict(name="Seal_Glass_Rear", x=(X_BACKLIGHT + 0.018, X_ROOF_R),
         v=(V_REARGLASS + 0.006, 0.9995), nx=56, nv=44, glass="glass_dark",
         gap=dict(v1=False)),
]

# ----------------------------------------------------------------- openings
ARCH_OPEN = C.ARCH_OPEN


def _cut_arches(ob):
    return C.cut_arches(ob, S.BODY, 0.35, 1.40, ARCH_OPEN)


def _quarter_light_outline():
    pts = []
    n = 40
    x_front = X_QTR_F + 0.080
    for i in range(n + 1):
        x = X_QTR_R + (x_front - X_QTR_R) * i / float(n)
        v = max(V_BELT, V_QTR_LOW(min(x, X_QTR_F)) - 0.010)
        pts.append((x, S.section_v(x, v)[1]))
    pts += [(x_front, 1.65), (X_QTR_R, 1.65)]
    return pts


def _cut_quarter_light(ob):
    c = C.prism_y("_qlight_" + ob.name, _quarter_light_outline(), 0.30, 1.40)
    sheet = C.sheet_bvh(ob)
    C.difference(ob, [c], "qlight_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


CUTTERS = {"arch": _cut_arches, "quarter_light": _cut_quarter_light}


def build_panels(collection, lib):
    return BP.build_panels(PANELS, S.BODY, collection, lib, cutters=CUTTERS,
                           core_z=0.625)


# ------------------------------------------------------------------ hidden
def build_shadow_shell(collection, lib, name="Seal_Shell_Shadow"):
    ob = BP.shadow_shell(N.BODY, collection, lib, name, nx=100, inset=0.068, shrink=0.950)
    for sfx in ("_F", "_R"):
        cap_ob = bpy.data.objects.get(name + sfx)
        if cap_ob is not None:
            bpy.data.objects.remove(cap_ob, do_unlink=True)
    for v in ob.data.vertices:
        z_min = S.Z_FLOOR(v.co.x) + 0.045
        if v.co.z < z_min:
            v.co.z = z_min
        if v.co.x > 0.90 and v.co.z > 0.67:
            v.co.z = min(v.co.z, 0.67 - (v.co.x - 0.90) * 0.11)
        if v.co.x < -1.15 and v.co.z > 0.84:
            v.co.z = min(v.co.z, 0.84 + (v.co.x + 1.15) * 0.08)
    ob.data.update()
    return ob


def build_wheel_liners(collection, lib):
    # Clamped y_outer=0.835 so the liners sit cleanly inside BYD Seal's 1875 mm body width
    return BP.wheel_liners(
        S.BODY, collection, lib, "Seal_Liner_",
        y_outer=0.835, depth=0.220, lip_in=0.008, flare=0.015, z_min=0.165, inner_wall=True
    )


def build_underbody(collection, lib):
    # Clamped x0=-1.86, length=3.70, edge_in=0.065 so no black corners ever poke past the nose/tail caps
    return BP.underbody(
        S.BODY, collection, lib, "Seal_Underbody",
        x0=-1.86, length=3.70, edge_in=0.065, lift=0.006
    )


def build_all(collection, lib):
    made = []
    made += build_panels(collection, lib)
    made.append(build_shadow_shell(collection, lib))
    made += build_wheel_liners(collection, lib)
    made.append(build_underbody(collection, lib))
    return made
