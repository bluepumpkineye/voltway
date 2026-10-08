"""Zeekr 7X panel layout: shut lines, window lines, panels, openings.

The machinery is carkit's (carkit.body.panels, carkit.body.fascia,
carkit.cut); this module is the 7X's layout, read off the camera-matched side
photograph (zx_ref_match, zx_camsolve). Lines that run up and down the flank
are written in side-photo PIXELS (side_left_studio.jpg, 3840 x 2880) and turned
into model metres by zx_camsolve.side_xz at the plane they lie on (a door skin
y = 0.9, the roof's centreline y = 0): the reading stays checkable against the
photograph.

    lines       door edges, cowl, A-pillar, belt, glass top, hood edge,
                header, roof spoiler, backlight edges
    PANELS      every flank panel as a region of (x, v)
    openings    wheel arches, cut by exact booleans on the half sheets before
                mirroring
    hidden      shadow shell, wheel liners, underbody tray

Greenhouse: a black-gloss underlay covers the whole greenhouse 3 mm inside the
skin and the glazing sits ON the skin cut to the window outlines, as on the RX.
The A-pillars and roof rails are body colour (silver), the roof between them dark
glass ahead of the B-pillar and paint behind it; the rear glass wraps round each
C-pillar as a dark wedge under the roof spoiler.
"""
import math

import zx_surface as S
import zx_nose as N
import zx_camsolve as CS
from carkit import geom
from carkit.geom import Curve, clamp01 as _clamp01, smoothstep as _smooth, ramp as _ramp
from carkit import mesh as M
from carkit import cut as C
from carkit.body import panels as BP

GAP = BP.GAP
SKIN = M.SKIN


def _zx(px, y):
    """Side-photo pixels -> [(z, x)] sorted by height (for near-vertical lines)."""
    pts = [CS.side_xz(u, v, y) for (u, v) in px]
    return sorted(((z, x) for (x, z) in pts))


def _xz(px, y):
    """Side-photo pixels -> [(x, z)] sorted by x (for lines along the car)."""
    pts = [CS.side_xz(u, v, y) for (u, v) in px]
    return sorted(pts)


# ----------------------------------------------------------------- stations
X_COWL = S.COWL_X            # 1.200, screen base
X_ROOF_F = 0.430             # windscreen header (the glass meets the roof)
X_KNEE = S.KNEE_X            # -1.930, roof spoiler: backlight below it
X_DLO_FRONT = 0.660          # the front door glass's front edge (upright)
X_DLO_TIP = -1.600           # the quarter glass's rear tip (side photo: z 1.265)
X_BLADE = -1.925             # the roof spoiler's trailing edge
X_FRIT = -1.960              # (no frit band on the 7X: the rear glass is uniformly dark)
# the roof: dark glass from the header to just behind the B-pillar, paint behind it
X_ROOF_GLASS_R = -0.100
# B-pillar glass edges: the black pillar between the door glasses (side photo
# u 2002-2114)
GB_F = -0.085
GB_R = -0.250

# Front door's leading edge, by height (sB: (1285,1537) .. (1272,2115) px, on y 0.9).
_DOOR_F_EDGE = Curve(_zx([(1285, 1537), (1260, 1560), (1240, 1585), (1237, 1620),
                          (1237, 1700), (1245, 1800), (1255, 1900), (1265, 2000),
                          (1268, 2050), (1272, 2115)], 0.90), mode="pchip")
# The door split (front door's trailing edge): slightly bowed.
_DOOR_B_EDGE = Curve(_zx([(2035, 1505), (2022, 1550), (2007, 1650), (2002, 1800),
                          (1997, 1950), (1997, 2025), (2005, 2105)], 0.90), mode="pchip")
# Rear door's trailing edge (sC: (2770,1500) .. (2770,1685) px), then round the arch.
_DOOR_R_EDGE = Curve(_zx([(2770, 1500), (2782, 1550), (2780, 1600), (2775, 1650),
                          (2770, 1685), (2768, 1750)], 0.90), mode="pchip")


def X_DOOR_F(v):
    return _DOOR_F_EDGE(S.section_v(1.03, v)[1])


def X_BPILLAR(v):
    return _DOOR_B_EDGE(S.section_v(-0.09, v)[1])


def X_DOOR_R(v):
    return _DOOR_R_EDGE(S.section_v(-1.22, v)[1])


# The flank panels' lower edge: the door's bottom edge rises toward the rear (sB:
# z 0.346 at x 1.02, 0.393 at -0.07, the black rocker below); at the front the
# fender's edge drops toward the bumper.
def Z_FLANK_LOW(x):
    if x >= 1.02:
        return max(0.300, 0.346 - (x - 1.02) * 0.040)
    return min(0.470, 0.346 + (1.02 - x) * 0.043)


def V_SILL(x):
    return S.v_at_z(x, Z_FLANK_LOW(x), 0.0, S.V_SHOULDER)


def v_up(x, z):
    """Upper-section parameter whose height is z at station x."""
    return S.v_at_z(x, z, S.V_SHOULDER, 0.995)


# ------------------------------------------------------------ window lines
# Lower edge of the side glass (side photo, y 0.88): 1.106 at the A-pillar rising
# to 1.265 at the quarter glass's tip.
BELT_Z = Curve([(0.80, 1.100), (0.601, 1.106), (0.186, 1.113), (-0.124, 1.121),
                (-0.690, 1.146), (-0.968, 1.164), (-1.108, 1.194), (-1.265, 1.220),
                (X_DLO_TIP, 1.265)])
# Upper edge along the roof side (side photo, y 0.7).
DLO_TOP_Z = Curve([(X_DLO_FRONT, 1.315), (0.395, 1.434), (0.080, 1.510),
                   (-0.129, 1.535), (-0.443, 1.548), (-0.757, 1.551),
                   (-0.981, 1.523), (-1.261, 1.474), (-1.447, 1.403),
                   (X_DLO_TIP, 1.285)])
A_FOOT = (1.190, 1.100)
A_TOP = (X_ROOF_F, 1.430)


def z_a(x):
    """Height of the A-pillar's glass edge at station x."""
    t = (A_FOOT[0] - x) / (A_FOOT[0] - A_TOP[0])
    return A_FOOT[1] + (A_TOP[1] - A_FOOT[1]) * t


def V_BELT(x):
    return v_up(x, BELT_Z(max(X_DLO_TIP, min(0.80, x))))


def V_GT(x):
    """Top of the side glass: the A-pillar edge ahead of the door glass, the roof
    side behind it."""
    if x > X_DLO_FRONT:
        return v_up(x, z_a(x))
    return v_up(x, DLO_TOP_Z(max(X_DLO_TIP, x)))


def V_A(x):
    """The windscreen's side edge: 80 mm of body-colour A-pillar above the door
    glass's edge."""
    return S.v_along(x, v_up(x, z_a(min(A_FOOT[0], x))), 0.080)


def V_RAIL(x):
    """Inboard edge of the body-colour roof rail: 55 mm above the side glass."""
    return S.v_along(x, V_GT(x), 0.055)


# Backlight edges: an oval in the rear photograph (to be read), widest at mid height.
# rear photo: the glass is +/-0.60 wide under the spoiler and +/-0.66 at its foot
Y_REARGLASS = Curve([(-2.40, 0.665), (-2.34, 0.656), (-2.20, 0.640), (-2.05, 0.620),
                     (X_KNEE, 0.600)])


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


# The painted C-pillar's lower edge over the black wedge (gh_rear: the silver
# pillar's edge falls from the quarter glass's tip to a nearly level line at z 1.19).
X_CTIP = -1.640
Z_CEDGE = Curve([(-1.640, 1.262), (-1.760, 1.215), (-1.880, 1.192), (-2.050, 1.190),
                 (-2.200, 1.192), (-2.350, 1.196)], mode="pchip")
Y_WTOP_BLADE = 0.600


def V_CEDGE(x):
    v = v_up(x, Z_CEDGE(min(X_CTIP, x)))
    # behind the C-pillar the painted edge runs into the backlight: the quarter must
    # stop at the glass's side edge, or it lies over the glass (z-fighting)
    if x < -2.0:
        v = min(v, V_REARGLASS(x) - 0.002)
    return v


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


# The clamshell hood: its side edge runs along the fender crowns from the cowl to
# the lamp (sA: the hood/fender line, z 0.956 at x 1.40, 0.89 at the lamp).
def _hood_front(v):
    return N.JOIN_F(v) + 0.015 * geom.smoothstep((v - 0.93) / 0.06)


Y_HOOD = Curve([(X_COWL, 0.800), (1.40, 0.835), (1.60, 0.850), (1.80, 0.855),
                (2.00, 0.845), (2.15, 0.815), (2.28, 0.760)])


def V_HOOD(x):
    return S.v_at_y_upper(x, Y_HOOD(x))


# the section parameter at the top of the rear wheel opening, where the cap's join
# (zx_nose.JOIN_R) turns back from the arch to the lamp bar
V_ARCHTOP = 0.417
X_ARCHTOP = -1.575


def _v_diag(x):
    """v where the cap's rising shut line (JOIN_R above the arch's top) passes station x."""
    lo, hi = V_ARCHTOP, 1.0
    if x >= N.JOIN_R(lo):
        return lo
    if x <= N.JOIN_R(hi):
        return hi
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if N.JOIN_R(mid) > x:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def V_QLOW(x):
    """Lower limit of the rear quarter: the sill ahead of the arch's top, behind it the
    cap's diagonal. (An x-limit that follows the diagonal folds the quad grid where the
    quarter tapers to its tip; limits that depend on x alone cannot.)"""
    if x >= X_ARCHTOP:
        return V_SILL(x)
    return max(V_SILL(x), _v_diag(x))


def _quarter_tip():
    """Station where the quarter's top edge meets the cap's diagonal."""
    x = -1.62
    while x > -2.34:
        if V_QLOW(x) >= V_Q_TOP(x) - 0.004:
            return x + 0.002
        x -= 0.002
    return -2.34


X_QTIP = _quarter_tip()

# ------------------------------------------------------------- flank panels
PANELS = [
    dict(name="ZX_Fender_Front", x=(X_DOOR_F, N.JOIN_F), v=(V_SILL, V_HOOD),
         nx=46, nv=40, arch=True, gap=dict(v0=False, x1=False), mat="paint"),
    dict(name="ZX_Door_Front", x=(X_BPILLAR, X_DOOR_F), v=(V_SILL, V_BELT),
         nx=40, nv=40, arch=True, gap=dict(v0=False), mat="paint"),
    dict(name="ZX_Door_Rear", x=(X_DOOR_R, X_BPILLAR), v=(V_SILL, V_BELT),
         nx=38, nv=40, arch=True, gap=dict(v0=False), mat="paint"),
    # One rear quarter from the tail to the rear door, including the whole
    # C-pillar up to the rail: one pressing, butted to the tail cap.
    # (behind the arch's top the cap's diagonal shut line is the quarter's LOWER edge,
    # and the quarter ends where that meets its top edge: V_QLOW, X_QTIP)
    dict(name="ZX_Quarter", x=(X_QTIP, X_DOOR_R), v=(V_QLOW, V_Q_TOP),
         nx=56, nv=48, arch=True, gap=dict(v0=False, x0=False), mat="paint",
         fixed_x=(X_DLO_TIP, X_CTIP)),
    dict(name="ZX_Hood", x=(X_COWL, _hood_front), v=(V_HOOD, 1.0),
         nx=60, nv=34, gap=dict(v1=False, x1=False), mat="paint", offset=0.0005),
    # Body-colour A-pillar and roof rail, butted to the quarter's C-pillar
    dict(name="ZX_Roof_Rail", x=(X_DLO_TIP, X_COWL),
         v=(lambda x: V_GT(x) + 0.006, V_RAIL_TOP),
         nx=140, nv=10, gap=dict(x0=False), mat="paint"),

    # ---- greenhouse underlay: glass surround, B-pillar, under the roof glass
    dict(name="ZX_Greenhouse_Black", x=(X_DLO_TIP - 0.030, X_COWL),
         v=(V_BELT, 1.0), nx=120, nv=50, gap=dict(v1=False), mat="black_gloss",
         offset=-0.003, thickness=0.0),
    dict(name="ZX_Roof_Rear_Black", x=(N.JOIN_R, X_DLO_TIP - 0.020),
         v=(lambda x: min(V_REARGLASS(x), V_CEDGE(x) - 0.006), 1.0), nx=48, nv=24,
         gap=dict(v1=False, x0=False), mat="black_gloss", offset=-0.010, thickness=0.0),

    # ---- glazing, on the skin, cut to the window outlines
    dict(name="ZX_Glass_Windshield", x=(X_ROOF_F, X_COWL - 0.012),
         v=(lambda x: V_A(x) + 0.004, 0.9995), nx=72, nv=56, glass="glass",
         gap=dict(v1=False)),
    # the paint starts at the blade's foot, so the roof spoiler's trailing face is body colour
    dict(name="ZX_Roof_Paint", x=(X_KNEE - 0.003, X_ROOF_GLASS_R),
         v=(V_ROOF_LO, 1.0), nx=64, nv=24, fixed_x=(X_CTIP,),
         gap=dict(v1=False, x0=False, v0=False), mat="paint"),
    dict(name="ZX_Glass_Roof", x=(X_ROOF_GLASS_R + 0.006, X_ROOF_F - 0.020),
         v=(lambda x: V_RAIL(x) + 0.004, 0.9995), nx=48, nv=30, glass="glass_dark",
         gap=dict(v1=False)),
    dict(name="ZX_Glass_Wedge", x=(lambda v: N.JOIN_R(v) + 0.002, X_CTIP),
         v=(V_CEDGE, V_WEDGE_TOP), nx=36, nv=10, glass="glass_dark", fixed_x=(X_BLADE,),
         gap=dict(x0=False, v1=False)),
    dict(name="ZX_Glass_DoorFront", x=(GB_F, X_DLO_FRONT),
         v=(lambda x: V_BELT(x) + 0.010, lambda x: V_GT(x) - 0.004),
         nx=60, nv=28, glass="glass"),
    dict(name="ZX_Glass_DoorRear", x=(-1.10, GB_R),
         v=(lambda x: V_BELT(x) + 0.010, lambda x: V_GT(x) - 0.004),
         nx=46, nv=28, glass="glass_dark"),
    dict(name="ZX_Glass_Quarter", x=(X_DLO_TIP + 0.012, -1.14),
         v=(lambda x: V_BELT(x) + 0.008, lambda x: V_GT(x) - 0.004),
         nx=14, nv=10, glass="glass_dark"),
    # the rear glass: one pane on the loft's backlight, from the lamp bar's lip to the spoiler
    dict(name="ZX_Glass_Rear", x=(lambda v: N.JOIN_R(v) + 0.004, X_BLADE - 0.006),
         v=(V_REARGLASS, 0.9995), nx=44, nv=40, glass="glass_dark",
         gap=dict(v1=False, x0=False)),
]


# ----------------------------------------------------------------- openings
def _cut_arches(ob):
    return C.cut_arches(ob, S.BODY, 0.35, 1.40)


CUTTERS = {"arch": _cut_arches}


def build_panels(collection, lib):
    return BP.build_panels(PANELS, S.BODY, collection, lib, cutters=CUTTERS,
                           core_z=0.72, butt_bevel=False)


# ------------------------------------------------------------------ hidden
def build_shadow_shell(collection, lib, name="ZX_Shell_Shadow", skins=()):
    ob = BP.shadow_shell(N.BODY, collection, lib, name, nx=140, nv=80, inset=0.030)
    if skins:
        clear_shell(ob, skins)
    return ob


def clear_shell(shell, skins, gap=0.015, core_z=0.70):
    """Pull the shell in to `gap` under the built skin, along rays from its core
    line (see rx_panels.clear_shell)."""
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
    # inside the painted arch lip: the black cladding stands round the tyre
    return BP.wheel_liners(S.BODY, collection, lib, "ZX_Liner_", y_outer=0.925,
                           mat="shadow", inner_wall=True, wall_z=0.25)


def build_underbody(collection, lib):
    return BP.underbody(S.BODY, collection, lib, "ZX_Underbody", x0=-2.15, length=4.30)


def build_all(collection, lib):
    made = []
    made += build_panels(collection, lib)
    made.append(build_shadow_shell(collection, lib, skins=list(made)))
    made += build_wheel_liners(collection, lib)
    made.append(build_underbody(collection, lib))
    return made
