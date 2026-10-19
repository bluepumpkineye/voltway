"""Denza Z9 panel layout: shut lines, window lines, panels, openings.

Built on carkit (carkit.body.panels, carkit.cut), adapted from su7_panels.py
and g9l_panels.py and calibrated to Denza Z9 studio references (c1_0040.jpg,
c1_0042.jpg, c1_0046.jpg).

Dimensions & Stations:
    Length: 5220 mm, Width: 1990 mm, Height: 1500 mm, Wheelbase: 3125 mm.
    Front axle: +1.6250 m, Rear axle: -1.5000 m.
    Cowl at x = +0.9870 m, Backlight base at x = -1.9554 m.
"""
import math
import bpy

import z9_surface as S
import z9_nose as N
from carkit.geom import (
    Curve, clamp01 as _clamp01, smoothstep as _smooth, ramp as _ramp,
)
from carkit import mesh as M
from carkit import cut as C
from carkit.body import panels as BP

GAP = BP.GAP
SKIN = M.SKIN

# ----------------------------------------------------------------- stations
X_COWL = S.COWL_X            # +0.9870 m: windscreen base / A-pillar foot
X_BPILLAR_F = -0.145         # front door | rear door shut line
X_BACKLIGHT = S.BACKLIGHT_X  # -2.2600 m: fastback backlight base
X_ROOF_F = 0.280             # windscreen header
X_ROOF_R = -1.280            # backlight header
X_QTR_F = -1.085             # rear door window / quarter glass divider
X_QTR_R = -1.540             # quarter glass rear apex (c1_0040.jpg)

V_BELT = S.V_SHOULDER + 0.026
V_REARGLASS = 0.690          # wide fastback backlight (was 0.795)

# Curved front & rear door shut lines scaled to 3125 mm wheelbase
_DOOR_F_EDGE = Curve([
    (0.200, 0.985), (0.275, 0.988), (0.390, 0.904 + 0.100), (0.520, 1.012),
    (0.650, 1.016), (0.780, 1.010), (0.870, 0.992), (0.940, 0.972),
    (1.080, 0.965),
], mode="pchip")

_DOOR_R_EDGE = Curve([
    (0.200, -0.820), (0.290, -0.855), (0.420, -0.985), (0.490, -1.038),
    (0.550, -1.080), (0.615, -1.120), (0.680, -1.180), (0.735, -1.235),
    (0.795, -1.270), (0.875, -1.295), (0.945, -1.285), (1.040, -1.215),
    (1.120, -1.200),
], mode="pchip")


def X_DOOR_F(v):
    return _DOOR_F_EDGE(S.section_v(1.00, v)[1])


def X_DOOR_R(v):
    return _DOOR_R_EDGE(S.section_v(-1.14, v)[1])


def V_SILL(x):
    return S.v_at_z(x, S.Z_FLOOR(x) + 0.030, 0.0, S.V_SHOULDER)


# Hood side shut line along fender crown to headlamp upper edge (c1_0042.jpg)
Y_HOOD = Curve([
    (S.COWL_X, 0.752), (1.25, 0.802), (1.65, 0.815), (1.92, 0.825),
    (2.05, 0.885), (2.16, 0.820), (2.28, 0.700), (2.38, 0.490),
    (2.46, 0.330), (2.505, 0.250),
])


def V_HOOD(x):
    return S.v_at_y_upper(x, Y_HOOD(x))


def V_GT(x):
    """Top of the side glass: 95 mm below the roof rail outer edge."""
    return S.v_along(x, S.v_rail(x), -0.095)


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
        _QTR_TIP.append(S.v_at_z(X_QTR_R, 1.150, S.V_SHOULDER, 1.0))
    return _QTR_TIP[0]


def V_QTR_LOW(x):
    t = (X_QTR_F - x) / (X_QTR_F - X_QTR_R)
    return (V_BELT + 0.010) + (V_QTR_TIP() - V_BELT - 0.010) * (_clamp01(t) ** 1.6)


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
    return _clamp01((v - V_BELT) / max(1e-4, (V_GT(-0.22) - V_BELT)))


def GB_F(v):
    return -0.135 + (-0.245 + 0.135) * _glass_s(v)


def GB_R(v):
    return -0.278 + (-0.342 + 0.278) * _glass_s(v)


V_LID_END = 0.755


def V_LID_EDGE(x):
    if x >= X_BACKLIGHT:
        return V_REARGLASS
    x1 = N.JOIN_R(V_LID_END)
    t = _clamp01((X_BACKLIGHT - x) / max(1e-4, X_BACKLIGHT - x1))
    return V_REARGLASS + (V_LID_END - V_REARGLASS) * _smooth(t)


# ------------------------------------------------------------- flank panels
PANELS = [
    # ---- painted sheet metal
    dict(name="Z9_Fender_Front", x=(X_DOOR_F, N.JOIN_F), v=(V_SILL, V_HOOD),
         nx=50, nv=40, arch=True, gap=dict(v0=False), mat="paint"),
    dict(name="Z9_Door_Front", x=(X_BPILLAR_F, X_DOOR_F), v=(V_SILL, V_BELT),
         nx=40, nv=40, arch=True, gap=dict(v0=False), mat="paint"),
    dict(name="Z9_Door_Rear", x=(X_DOOR_R, X_BPILLAR_F), v=(V_SILL, V_DOOR_R_TOP),
         nx=38, nv=40, arch=True, gap=dict(v0=False), mat="paint"),
    dict(name="Z9_Quarter", x=(N.JOIN_R, X_DOOR_R), v=(V_SILL, V_LID_EDGE),
         nx=50, nv=44, arch=True, gap=dict(v0=False, x0=False), mat="paint",
         quarter_light=True),
    dict(name="Z9_Hood", x=(X_COWL, N.JOIN_F), v=(V_HOOD, 1.0),
         nx=60, nv=34, gap=dict(v1=False), mat="paint"),
    # (the join runs ahead of the backlight's foot at the middle heights: JOIN_R -2.13 against -2.26, so a bare x range
    # (JOIN_R, X_BACKLIGHT) is reversed there and the sheet folds over itself, the speckled strip under the rear glass)
    dict(name="Z9_Decklid", x=(lambda v: min(N.JOIN_R(v), X_BACKLIGHT - 0.015), X_BACKLIGHT), v=(V_LID_EDGE, 1.0),
         nx=24, nv=30, gap=dict(v1=False, x0=False), mat="paint"),
    dict(name="Z9_Roof_Rail", x=(X_QTR_R, X_COWL),
         v=(lambda x: V_GLASS_TOP(x) + 0.006, V_RAIL_TOP),
         nx=130, nv=10, gap=dict(x0=False), mat="paint"),

    # ---- greenhouse & cowl blackouts (exported into DenzaZ9_Blackout)
    dict(name="Z9_Greenhouse_Black", x=(X_QTR_R - 0.030, X_COWL),
         v=(V_BELT, 1.0), nx=100, nv=44,
         gap=dict(v1=False), mat="black_gloss", offset=-0.003, thickness=0.0),
    dict(name="Z9_Cowl_Black", x=(X_COWL - 0.035, X_COWL + 0.025),
         v=(V_HOOD, 1.0), nx=20, nv=24, gap=dict(v1=False), mat="black_gloss",
         offset=-0.004, thickness=0.0),
    dict(name="Z9_Roof_Rear_Black", x=(X_BACKLIGHT, X_ROOF_R),
         v=(V_REARGLASS, 1.0), nx=24, nv=22, gap=dict(v1=False),
         mat="frit", offset=-0.003, thickness=0.0),

    # ---- flush glazing
    dict(name="Z9_Glass_Windshield", x=(X_ROOF_F, X_COWL - 0.012),
         v=(lambda x: V_A(x) + 0.020, 0.9995), nx=68, nv=52, glass="glass",
         gap=dict(v1=False)),
    dict(name="Z9_Glass_Roof", x=(X_ROOF_R + 0.010, X_ROOF_F - 0.015),
         v=(lambda x: V_RAIL(x) + 0.004, 0.9995), nx=48, nv=28, glass="glass_dark",
         gap=dict(v1=False)),
    dict(name="Z9_Glass_DoorFront", x=(GB_F, X_COWL - 0.030),
         v=(V_BELT + 0.010, lambda x: min(V_A(x) - 0.020, V_GT(x))),
         nx=56, nv=28, glass="glass"),
    # the B-pillar: a black-glass band between the door panes, as part of the body shell: the viewer's clear glass takes
    # the underlay's triangles out within 5 cm of a clear pane, so the strip of underlay here came out as a sawtooth
    dict(name="Z9_BPillar_Black", x=(lambda v: GB_R(v) - 0.004, lambda v: GB_F(v) + 0.004),
         v=(V_BELT + 0.010, V_GT), nx=8, nv=28, mat="black_gloss", offset=-0.001, thickness=0.0,
         gap=dict(x0=False, x1=False, v0=False, v1=False)),
    dict(name="Z9_Glass_DoorRear", x=(X_QTR_F + 0.030, GB_R),
         v=(V_BELT + 0.010, V_GT), nx=48, nv=28, glass="glass_dark"),
    dict(name="Z9_Glass_Quarter", x=(X_QTR_R + 0.004, X_QTR_F),
         v=(V_QTR_LOW, lambda x: V_C(x) - 0.020), nx=24, nv=14,
         glass="glass_dark"),
    dict(name="Z9_Glass_Rear", x=(X_BACKLIGHT + 0.018, X_ROOF_R),
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
                           core_z=0.68)


# ------------------------------------------------------------------ hidden
def build_shadow_shell(collection, lib, name="Z9_Shell_Shadow"):
    ob = BP.shadow_shell(N.BODY, collection, lib, name, nx=100, inset=0.065, shrink=0.955)
    for sfx in ("_F", "_R"):
        cap_ob = bpy.data.objects.get(name + sfx)
        if cap_ob is not None:
            bpy.data.objects.remove(cap_ob, do_unlink=True)
    for v in ob.data.vertices:
        z_min = S.Z_FLOOR(v.co.x) + 0.045
        if v.co.z < z_min:
            v.co.z = z_min
        if v.co.x > 1.05 and v.co.z > 0.72:
            v.co.z = min(v.co.z, 0.72 - (v.co.x - 1.05) * 0.10)
        if v.co.x < -1.25 and v.co.z > 0.88:
            v.co.z = min(v.co.z, 0.88 + (v.co.x + 1.25) * 0.08)
    ob.data.update()
    return ob


def build_wheel_liners(collection, lib):
    return BP.wheel_liners(S.BODY, collection, lib, "Z9_Liner_")


def build_underbody(collection, lib):
    return BP.underbody(S.BODY, collection, lib, "Z9_Underbody")


def build_all(collection, lib):
    made = []
    made += build_panels(collection, lib)
    made.append(build_shadow_shell(collection, lib))
    made += build_wheel_liners(collection, lib)
    made.append(build_underbody(collection, lib))
    return made
