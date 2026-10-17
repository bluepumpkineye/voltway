"""Avatr 06T panel layout: shut lines, window lines, panels, openings.

Calibrated to the Autohome turnaround photos (c1_0001..c1_0007.jpg) and
official Avatr 06T design renders (design-list_01..03.jpg):
  - Two-tone floating roof: gloss-black A-pillar and roof arch (`A06T_Roof_Rail`)
    with full panoramic dark glass roof (`A06T_Glass_Roof`), while the C-pillar
    sail (`A06T_Quarter`) rises in body colour behind the elongated shooting-
    brake quarter window (`X_DLO_TIP = -1.780`) up to the body-colour roof
    spoiler (`A06T_Roof_Paint` / `A06T_Roof_Blade`).
  - Frameless front and rear doors (`A06T_Door_Front`, `A06T_Door_Rear`).
  - Clamshell hood (`A06T_Hood`) with twin power domes inboard of the fenders.
  - Front fender camera gill slot (`VENT_OUTLINE`) spanning the front fender's
    trailing edge ahead of the front door.
"""
import math

import a06t_surface as S
import a06t_nose as N
from carkit import geom
from carkit.geom import Curve, clamp01 as _clamp01, smoothstep as _smooth, ramp as _ramp
from carkit import mesh as M
from carkit import cut as C
from carkit.body import panels as BP

GAP = BP.GAP
SKIN = M.SKIN

# ----------------------------------------------------------------- stations
X_COWL = S.COWL_X            # 0.820, windshield base
X_ROOF_F = 0.040             # windshield header (under 896-line LiDAR)
X_KNEE = S.KNEE_X            # -1.960, shooting-brake roof spoiler trailing edge
X_BPILLAR = -0.310           # front | rear door shut line
X_DLO_TIP = -1.780           # elongated shooting-brake quarter window rear tip
X_DOOR_R_TOP = -1.320        # rear door trailing edge at beltline
X_ROOF_GLASS_R = -1.580      # panoramic glass roof extends over both seat rows
X_BLADE = -1.860             # painted roof spoiler header start
X_FRIT = -2.140              # ceramic frit band under the roof spoiler

# Rear glass wraps around each C-pillar as a dark aerodynamic fin wedge under
# the shooting-brake roof spoiler (c1_0004.jpg, c1_0005.jpg, design-list_03.jpg)
X_CTIP = -1.820
Z_CEDGE = Curve([
    (-1.820, 1.305), (-1.890, 1.275), (-1.970, 1.242), (-2.060, 1.208),
    (-2.150, 1.172), (-2.240, 1.136), (-2.330, 1.100), (-2.410, 1.068),
], mode="pchip")
Y_WTOP_BLADE = 0.495

# Front door leading edge: nearly vertical at x 0.78 (c1_0004.jpg)
_DOOR_F_EDGE = Curve([
    (0.00, 0.776), (0.18, 0.776), (0.38, 0.780), (0.65, 0.782), (0.92, 0.780),
    (1.05, 0.770), (1.30, 0.760), (1.70, 0.750),
], mode="pchip")

# Rear door trailing edge: follows the rear wheel arch opening cleanly down to
# the rocker sill, then stays upright above the belt (the curve is also read
# by the quarter panel, which reaches the roof rail)
_DOOR_R_EDGE = Curve([
    (0.00, -0.900), (0.18, -0.910), (0.36, -0.925), (0.50, -0.965), (0.62, -1.030),
    (0.72, -1.115), (0.80, -1.205), (0.88, -1.280), (0.96, -1.330),
    (1.06, -1.335), (1.20, -1.320), (1.45, -1.310), (1.80, -1.300),
], mode="pchip")



def X_DOOR_F(v):
    return _DOOR_F_EDGE(S.section_v(0.78, v)[1])


def X_DOOR_R(v):
    return _DOOR_R_EDGE(S.section_v(-1.15, v)[1])


def V_SILL(x):
    """Floor edge: where the flank panels start."""
    return S.v_at_z(x, S.Z_FLOOR(x) + 0.028, 0.0, S.V_SHOULDER)


def v_up(x, z):
    """Upper-section parameter whose height is z at station x."""
    return S.v_at_z(x, z, S.V_SHOULDER, 0.995)


# ------------------------------------------------------- the rear bumper
# Behind the rear wheel the painted quarter meets the gloss-black lower
# diffuser wrap-around (rising from z 0.38 behind the arch to z 0.52 at the
# rear corner, matching a06t_rear.Z_BLACK = 0.520).
Z_BAND_TOP = Curve([
    (-1.850, 0.365), (-1.920, 0.385), (-2.000, 0.418), (-2.100, 0.462),
    (-2.200, 0.498), (-2.300, 0.516), (-2.470, 0.520),
], mode="pchip")
Z_BAND_LO = Curve([
    (-1.850, 0.205), (-1.920, 0.220), (-2.050, 0.268), (-2.180, 0.322),
    (-2.300, 0.368), (-2.420, 0.392), (-2.600, 0.398), (-2.800, 0.398),
], mode="pchip")
X_BAND_F = -1.860
Y_CORNER = 0.765
Y_CORNER_HIDDEN = 0.540


def V_BAND_TOP(x):
    return S.v_at_z(x, Z_BAND_TOP(x), 0.0, S.V_SHOULDER)


def V_BAND_LO(x):
    return S.v_at_z(x, Z_BAND_LO(x), 0.0, S.V_SHOULDER)


def V_Q_LO(x):
    k = _ramp(x, X_BAND_F, 0.04)
    return V_BAND_TOP(x) + (V_SILL(x) - V_BAND_TOP(x)) * k


def rear_corner_cutters(both=False, y0=Y_CORNER):
    xs = [-1.88 - 0.02 * i for i in range(42)]
    outline = [(x, Z_BAND_LO(x)) for x in xs] + [(xs[-1], -0.30), (xs[0], -0.30)]
    made = [C.prism_y("_corner_L", outline, y0, 1.60)]
    if both:
        made.append(C.prism_y("_corner_R", outline, -1.60, -y0))
    return made


# ------------------------------------------------------------ window lines
# Lower edge of the side glass (c1_0004.jpg, design-list_02.jpg): rises sleekly
# along the doors and kicks up along the elongated shooting-brake quarter glass
BELT_Z = Curve([
    (0.82, 0.996), (0.30, 1.002), (-0.10, 1.008), (-0.42, 1.016),
    (-0.75, 1.030), (-1.08, 1.050), (-1.35, 1.078), (-1.56, 1.112),
    (-1.70, 1.142), (X_DLO_TIP, 1.165),
])

# Upper edge of the side glass along the shooting-brake roof arch
DLO_TOP_Z = Curve([
    (0.040, 1.318), (-0.220, 1.362), (-0.550, 1.378), (-0.850, 1.375),
    (-1.150, 1.358), (-1.400, 1.325), (-1.580, 1.275), (-1.700, 1.218),
    (X_DLO_TIP, 1.165),
])
A_FOOT = (0.650, 1.010)
A_TOP = (X_ROOF_F, 1.318)


def z_a(x):
    t = (A_FOOT[0] - x) / (A_FOOT[0] - A_TOP[0])
    return A_FOOT[1] + (A_TOP[1] - A_FOOT[1]) * t


def V_BELT(x):
    return v_up(x, BELT_Z(max(X_DLO_TIP, min(0.82, x))))


def V_GT(x):
    if x > X_ROOF_F:
        return v_up(x, z_a(x))
    return v_up(x, DLO_TOP_Z(max(X_DLO_TIP, x)))


def V_A(x):
    return S.v_along(x, v_up(x, z_a(min(A_FOOT[0], x))), 0.072)


def V_RAIL(x):
    return S.v_along(x, V_GT(x), 0.058)


# Backlight lateral half-width on the shooting-brake tail
Y_REARGLASS = Curve([
    (-2.44, 0.545), (-2.34, 0.558), (-2.22, 0.555), (-2.08, 0.538),
    (X_KNEE, 0.515),
])


def V_REARGLASS(x):
    return S.v_at_y_upper(x, Y_REARGLASS(x))


def V_FRIT(x):
    lo = S.v_at_y_upper(x, Y_REARGLASS(min(x, X_KNEE))) + 0.012
    hi = V_RAIL_TOP(x) + 0.004
    k = _ramp(x, X_KNEE)
    return lo + (hi - lo) * k


def V_RAIL_TOP(x):
    a = V_A(x)
    r = V_RAIL(x)
    c = V_REARGLASS(x) - 0.004
    k_f = _ramp(x, X_ROOF_F)
    k_r = _ramp(x, X_KNEE)
    return c + (r - c) * k_r + (a - r) * k_f


def V_CEDGE(x):
    xx = min(X_CTIP, x)
    # never above what the loft reaches at the pillar's lateral position: the
    # tail falls away faster than the tabulated edge near the ducktail
    z_reach = S.section_v(xx, S.v_at_y_upper(xx, 0.60))[1] - 0.008
    return v_up(x, min(Z_CEDGE(xx), z_reach))


def V_WTOP(x):
    t = _clamp01((X_CTIP - x) / (X_CTIP - X_BLADE))
    return V_CEDGE(X_CTIP) + (S.v_at_y_upper(X_BLADE, Y_WTOP_BLADE) - V_CEDGE(X_CTIP)) * t


def V_Q_TOP(x):
    if x >= X_DLO_TIP:
        return V_BELT(x)
    if x >= X_CTIP:
        s = _smooth((X_DLO_TIP - x) / (X_DLO_TIP - X_CTIP))
        return V_RAIL_TOP(x) + (V_CEDGE(X_CTIP) - V_RAIL_TOP(x)) * s
    return V_CEDGE(x)


def V_ROOF_LO(x):
    if x >= X_DLO_TIP:
        return V_RAIL(x) - 0.004
    if x >= X_CTIP:
        return V_Q_TOP(x) - 0.004 * (x - X_CTIP) / (X_DLO_TIP - X_CTIP)
    return V_WTOP(x)


def V_WEDGE_TOP(x):
    if x >= X_BLADE:
        return V_WTOP(x)
    if x >= X_FRIT:
        return V_FRIT(x) + 0.004
    return S.v_along(x, V_REARGLASS(x), 0.014) - 0.001


def _hood_front(v):
    return N.JOIN_F(v) + 0.015 * geom.smoothstep((v - 0.93) / 0.06)


Y_HOOD = Curve([
    (X_COWL, 0.815), (1.05, 0.795), (1.25, 0.770), (1.45, 0.742),
    (1.65, 0.715), (1.80, 0.690), (1.95, 0.648), (2.08, 0.590),
    (2.18, 0.530), (S.HALF_L, 0.400),
])


def V_HOOD(x):
    return S.v_at_y_upper(x, Y_HOOD(x))


# B-pillar glass edges
GB_F = -0.265
GB_R = -0.355


# ------------------------------------------------------------- flank panels
PANELS = [
    dict(name="A06T_Fender_Front", x=(X_DOOR_F, N.JOIN_F), v=(V_SILL, V_HOOD),
         nx=46, nv=40, arch=True, fender_vent=True, gap=dict(v0=False, x1=False),
         mat="paint"),
    dict(name="A06T_Door_Front", x=(X_BPILLAR, X_DOOR_F), v=(V_SILL, V_BELT),
         nx=40, nv=40, arch=True, gap=dict(v0=False), mat="paint"),
    dict(name="A06T_Door_Rear", x=(X_DOOR_R, X_BPILLAR), v=(V_SILL, V_BELT),
         nx=38, nv=40, arch=True, gap=dict(v0=False), mat="paint"),
    dict(name="A06T_Quarter", x=(N.JOIN_R, X_DOOR_R), v=(V_Q_LO, V_Q_TOP),
         nx=56, nv=48, arch=True, gap=dict(v0=False, x0=False), mat="paint",
         fixed_x=(X_DLO_TIP, X_CTIP)),
    dict(name="A06T_Quarter_Low", x=(N.JOIN_R, X_BAND_F + 0.030), v=(V_BAND_LO, V_BAND_TOP),
         nx=16, nv=10, arch=True, gap=dict(x0=False, x1=False, v1=False),
         mat="black_gloss"),
    dict(name="A06T_Hood", x=(X_COWL, _hood_front), v=(V_HOOD, 1.0),
         nx=60, nv=34, gap=dict(v1=False, x1=False), mat="paint", offset=0.0005),
    # On the Avatr 06T (c1_0001..c1_0007.jpg), the A-pillar and upper roof arch
    # are gloss black, creating the floating-roof silhouette, while the C-pillar
    # on A06T_Quarter rises in body colour behind X_DLO_TIP.
    dict(name="A06T_Roof_Rail", x=(X_DLO_TIP, X_COWL),
         v=(lambda x: V_GT(x) + 0.006, V_RAIL_TOP),
         nx=140, nv=10, gap=dict(x0=False), mat="black_gloss"),

    # ---- greenhouse underlay
    dict(name="A06T_Greenhouse_Black", x=(X_DLO_TIP - 0.030, X_COWL),
         v=(V_BELT, 1.0), nx=120, nv=50, gap=dict(v1=False), mat="black_gloss",
         offset=-0.003, thickness=0.0),
    dict(name="A06T_Roof_Rear_Black", x=(N.JOIN_R, X_DLO_TIP - 0.020),
         v=(lambda x: min(V_REARGLASS(x), V_CEDGE(x) - 0.006), 1.0), nx=48, nv=24,
         gap=dict(v1=False, x0=False), mat="black_gloss", offset=-0.003, thickness=0.0),

    # ---- glazing & roof panels
    dict(name="A06T_Glass_Windshield", x=(X_ROOF_F, X_COWL - 0.012),
         v=(lambda x: V_A(x) + 0.004, 0.9995), nx=72, nv=56, glass="glass",
         gap=dict(v1=False)),
    # Body-colour rear roof crown leading into the shooting-brake roof spoiler
    dict(name="A06T_Roof_Paint", x=(X_BLADE + 0.004, X_ROOF_GLASS_R),
         v=(V_ROOF_LO, 1.0), nx=36, nv=24, fixed_x=(X_CTIP,),
         gap=dict(v1=False, x0=False, v0=False), mat="paint"),
    # Panoramic dark glass roof spanning both rows
    dict(name="A06T_Glass_Roof", x=(X_ROOF_GLASS_R + 0.006, X_ROOF_F - 0.020),
         v=(lambda x: V_RAIL(x) + 0.004, 0.9995), nx=72, nv=30, glass="glass_dark",
         gap=dict(v1=False)),
    dict(name="A06T_Glass_Wedge", x=(lambda v: N.JOIN_R(v) + 0.002, X_CTIP),
         v=(V_CEDGE, V_WEDGE_TOP), nx=36, nv=10, glass="glass_dark", fixed_x=(X_BLADE,),
         gap=dict(x0=False, v1=False)),
    dict(name="A06T_Glass_DoorFront", x=(GB_F, 0.680),
         v=(lambda x: V_BELT(x) + 0.010, lambda x: V_GT(x) - 0.004),
         nx=60, nv=28, glass="glass"),
    dict(name="A06T_Glass_DoorRear", x=(X_DOOR_R_TOP + 0.020, GB_R),
         v=(lambda x: V_BELT(x) + 0.010, lambda x: V_GT(x) - 0.004),
         nx=46, nv=28, glass="glass_dark"),
    dict(name="A06T_Glass_Quarter", x=(X_DLO_TIP + 0.012, X_DOOR_R_TOP - 0.012),
         v=(lambda x: V_BELT(x) + 0.008, lambda x: V_GT(x) - 0.004),
         nx=24, nv=14, glass="glass_dark"),
    dict(name="A06T_Glass_Frit", x=(X_FRIT, X_BLADE - 0.004),
         v=(V_FRIT, 0.9995), nx=16, nv=40,
         mat="frit", offset=0.0022, thickness=0.0, gap=dict(v1=False)),
]


# ----------------------------------------------------------------- openings
def _cut_arches(ob):
    return C.cut_arches(ob, S.BODY, 0.32, 1.35)


# Front fender ADAS camera gill blade ahead of the front door (design-list_03.jpg, c1_0004.jpg):
# a sleek horizontal black camera blade at x 0.60..0.83, z 0.630..0.662
VENT_OUTLINE = [
    (0.835, 0.646), (0.810, 0.660), (0.610, 0.662), (0.598, 0.648),
    (0.610, 0.632), (0.805, 0.632),
]


def _cut_fender_vent(ob):
    c = C.prism_y("_fvent_" + ob.name, VENT_OUTLINE, 0.55, 1.40)
    sheet = C.sheet_bvh(ob)
    C.difference(ob, [c], "fvent_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


CUTTERS = {"arch": _cut_arches, "fender_vent": _cut_fender_vent}


def build_panels(collection, lib):
    return BP.build_panels(PANELS, S.BODY, collection, lib, cutters=CUTTERS,
                           core_z=0.66, butt_bevel=False)


# ------------------------------------------------------------------ hidden
def build_shadow_shell(collection, lib, name="A06T_Shell_Shadow", skins=()):
    ob = BP.shadow_shell(N.BODY, collection, lib, name, nx=140, nv=80, inset=0.028)
    if skins:
        clear_shell(ob, skins)
    return ob


def clear_shell(shell, skins, gap=0.015, core_z=0.65):
    """Pull the shadow shell in to `gap` under the built skin along rays from
    its core line so no dark sliver pokes through concave regions."""
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    verts, faces = [], []
    for ob in skins:
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        base = len(verts)
        verts += [ob.matrix_world @ v.co for v in me.vertices]
        faces += [[base + i for i in p.vertices] for p in me.polygons]
        ev.to_mesh_clear()
    tree = BVHTree.FromPolygons(verts, faces)
    mw = shell.matrix_world
    inv = mw.inverted()
    me = shell.data

    def ray(p):
        c = Vector((p.x, 0.0, core_z))
        d = p - c
        n = d.length
        if n < 1e-6:
            return None
        d /= n
        hit = tree.ray_cast(c, d, n + 0.25)[0]
        if hit is None:
            return None
        return c, d, n, (hit - c).length

    moved = set()
    for v in me.vertices:
        r = ray(mw @ v.co)
        if r and r[2] > r[3] - gap:
            c, d, n, reach = r
            v.co = inv @ (c + d * max(0.0, reach - gap))
            moved.add(v.index)
    for _ in range(3):
        again = False
        for f in me.polygons:
            r = ray(mw @ f.center)
            if not r or r[2] <= r[3] - 0.5 * gap:
                continue
            deficit = r[2] - (r[3] - 0.5 * gap)
            for i in f.vertices:
                q = ray(mw @ me.vertices[i].co)
                if q:
                    c, d, n, _reach = q
                    me.vertices[i].co = inv @ (c + d * max(0.0, n - deficit))
                    moved.add(i)
            again = True
        me.update()
        if not again:
            break
    print("shadow shell: %d vertices pulled under the skin" % len(moved))
    return len(moved)


def build_wheel_liners(collection, lib):
    return BP.wheel_liners(S.BODY, collection, lib, "A06T_Liner_", y_outer=0.920,
                           mat="shadow", inner_wall=True, wall_z=0.22)


def build_underbody(collection, lib):
    return BP.underbody(S.BODY, collection, lib, "A06T_Underbody", x0=-2.25, length=4.52)


def build_all(collection, lib):
    made = []
    made += build_panels(collection, lib)
    made.append(build_shadow_shell(collection, lib, skins=list(made)))
    made += build_wheel_liners(collection, lib)
    made.append(build_underbody(collection, lib))
    import bpy
    for nm in ("A06T_Shell_Shadow", "A06T_Shell_Shadow_R", "A06T_Underbody", "A06T_Liner_R"):
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            M.apply_modifiers(ob)
            sheet = C.sheet_bvh(ob)
            C.difference(ob, rear_corner_cutters(both=True, y0=Y_CORNER_HIDDEN), "corner_")
            C.prune_off_sheet(ob, sheet)
    return made
