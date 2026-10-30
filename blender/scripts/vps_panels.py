"""Voyah Passion S (岚图追光S) panel layout: shut lines, window lines, panels, openings.

Read off the Autohome studio set (series 8534: c1_0004 side, c1_0002 front, c1_0006 rear) through
the solved cameras of vps_cam.py:
  - Body-coloured A-pillar and coupe roof arch (`VPS_Roof_Edge`) over a slim gloss-black window
    surround (`VPS_Roof_Rail`), framing a full-length dark panoramic glass roof (`VPS_Glass_Roof`).
  - Frameless front and rear doors (`VPS_Door_Front`, `VPS_Door_Rear`) with sculpted gloss-black
    lower door cladding (`VPS_Door_Low_F`, `VPS_Door_Low_R`) above a continuous black sill (`VPS_Rocker`).
  - Sculpted clamshell-side bonnet (`VPS_Hood`) whose leading edge is the full-width black nose
    channel (`N.JOIN_F`) and whose side shut lines run along the upper fenders (`Y_HOOD`) to the cowl.
  - Vertical front-fender ADAS camera/LiDAR gill cut cleanly ahead of the front door shut line.
"""
import math

import vps_cam as CAM
import vps_surface as S
import vps_nose as N
from carkit import geom
from carkit.geom import Curve, clamp01 as _clamp01, smoothstep as _smooth, ramp as _ramp
from carkit import mesh as M
from carkit import cut as C
from carkit.body import panels as BP

GAP = BP.GAP
SKIN = M.SKIN

# ----------------------------------------------------------------- stations
X_COWL = S.COWL_X            # 1.040, windscreen base on the centreline
X_ROOF_F = 0.240             # windscreen header at A-pillar top (curves to 0.380 at centre)
X_KNEE = S.KNEE_X            # -1.720, roof rear header under twin-pod spoiler
X_BPILLAR = -0.155           # nominal B-pillar station (sloped curve _DOOR_SPLIT_EDGE used below)
X_DLO_TIP = -1.502           # quarter window rear tip (side_grid_mid u 2875, v 1394)
X_DOOR_R_TOP = -1.202        # rear door trailing edge at belt
X_ROOF_GLASS_R = -1.660      # panoramic glass roof rear edge ahead of twin-pod spoiler root
X_BLADE = -1.865             # twin-pod spoiler trailing edge
X_FRIT = -1.960              # ceramic frit band under the spoiler

# Dark glass wedge wrapping the C-pillar under the twin-pod spoiler (side_grid_tail u 3020..3425)
X_CTIP = -1.680
Z_CEDGE = Curve([
    (-1.680, 1.445), (-1.760, 1.402), (-1.860, 1.352), (-1.960, 1.305),
    (-2.060, 1.262), (-2.160, 1.232), (-2.280, 1.218), (-2.420, 1.216),
], mode="pchip")

# Front door leading edge (side_grid_mid u 1314..1362: upright at x 0.91..0.955, curving to A-pillar foot)
_DOOR_F_EDGE = Curve([
    (0.200, 0.905), (0.335, 0.910), (0.450, 0.922), (0.600, 0.938),
    (0.750, 0.950), (0.905, 0.955), (1.055, 0.944), (1.195, 0.880),
], mode="pchip")

# Front | rear door split (side_grid_mid u 2018..2065: -0.145 at sill rising to -0.213 at belt)
_DOOR_SPLIT_EDGE = Curve([
    (0.200, -0.150), (0.335, -0.148), (0.485, -0.145), (0.650, -0.142),
    (0.800, -0.144), (0.950, -0.156), (1.080, -0.176), (1.220, -0.213),
], mode="pchip")

# Rear door trailing edge: curves smoothly outside VPS_Clad_R (r_out = 0.532 m around (-1.475, 0.375))
_DOOR_R_EDGE = Curve([
    (0.200, -0.922), (0.335, -0.928), (0.415, -0.935), (0.540, -0.958),
    (0.660, -1.012), (0.780, -1.112), (0.875, -1.245), (0.990, -1.275),
    (1.116, -1.288), (1.210, -1.266), (1.280, -1.202),
], mode="pchip")

# Top of the sculpted gloss-black rocker panel (side_grid_mid v 1942..2005: arches to z 0.490 near B-pillar)
ROCKER_TOP = Curve([
    (-1.450, 0.385), (-1.100, 0.405), (-0.950, 0.418), (-0.690, 0.460),
    (-0.375, 0.489), (-0.145, 0.485), (0.250, 0.458), (0.640, 0.425),
    (0.920, 0.392), (1.150, 0.372),
], mode="pchip")


def X_DOOR_F(v):
    return _DOOR_F_EDGE(S.section_v(0.85, v)[1])


def X_DOOR_SPLIT(v):
    return _DOOR_SPLIT_EDGE(S.section_v(-0.16, v)[1])


def X_DOOR_R(v):
    return _DOOR_R_EDGE(S.section_v(-1.15, v)[1])


def V_SILL(x):
    """Bottom floor edge where the lower sill panel begins."""
    return S.v_at_z(x, S.Z_FLOOR(x) + 0.022, 0.0, S.V_SHOULDER)


def V_SILL_HI(x):
    """Horizontal split at z ~0.332 between fixed lower sill skirt and door-mounted black cladding."""
    return S.v_at_z(x, 0.332, 0.0, S.V_SHOULDER)


def V_ROCK(x):
    """Arched top of the gloss-black lower door/fender cladding."""
    return S.v_at_z(x, ROCKER_TOP(x), 0.0, S.V_SHOULDER)


def v_up(x, z):
    """Upper-section parameter whose height is z at station x."""
    return S.v_at_z(x, z, S.V_SHOULDER, 0.995)


# ------------------------------------------------------- rear lower bumper split
Z_BAND_TOP = Curve([
    (-1.980, 0.410), (-2.060, 0.425), (-2.160, 0.455), (-2.260, 0.525),
    (-2.350, 0.615), (-2.430, 0.655), (-2.525, 0.660),
], mode="pchip")
Z_BAND_LO = Curve([
    (-1.980, 0.270), (-2.100, 0.292), (-2.240, 0.320), (-2.380, 0.352),
    (-2.480, 0.375), (-2.650, 0.385), (-2.800, 0.385),
], mode="pchip")
X_BAND_F = -1.990
Y_CORNER = 0.770
Y_CORNER_HIDDEN = 0.540


def V_BAND_TOP(x):
    return S.v_at_z(x, Z_BAND_TOP(x), 0.0, S.V_SHOULDER)


def V_BAND_LO(x):
    return S.v_at_z(x, Z_BAND_LO(x), 0.0, S.V_SHOULDER)


def V_Q_LO(x):
    k = _ramp(x, X_BAND_F + 0.14, 0.24)
    return V_BAND_TOP(x) + (V_SILL(x) - V_BAND_TOP(x)) * k


def rear_corner_cutters(both=False, y0=Y_CORNER):
    xs = [-2.00 - 0.02 * i for i in range(40)]
    outline = [(x, Z_BAND_LO(x)) for x in xs] + [(xs[-1], -0.30), (xs[0], -0.30)]
    made = [C.prism_y("_corner_L", outline, y0, 1.60)]
    if both:
        made.append(C.prism_y("_corner_R", outline, -1.60, -y0))
    return made


# ------------------------------------------------------------ window lines
BELT_Z = Curve([
    (X_DLO_TIP, 1.346), (-1.357, 1.301), (-1.208, 1.268), (-1.011, 1.242),
    (-0.617, 1.220), (-0.214, 1.211), (0.169, 1.201), (0.563, 1.194),
    (0.865, 1.187), (0.960, 1.185),
], mode="pchip")
BELT_X_MAX = 0.940

DLO_TOP_Z = Curve([
    (X_DLO_TIP, 1.346), (-1.363, 1.422), (-1.174, 1.485), (-0.937, 1.535),
    (-0.700, 1.562), (-0.463, 1.579), (-0.230, 1.584), (-0.060, 1.574),
    (0.140, 1.542), (X_ROOF_F, 1.512),
], mode="pchip")

A_FOOT = (0.865, 1.187)
A_TOP = (X_ROOF_F, 1.512)
_A_LINE = Curve([
    (X_ROOF_F, 1.512), (0.406, 1.450), (0.643, 1.328), (0.865, 1.187),
], mode="pchip")


def z_a(x):
    return _A_LINE(max(A_TOP[0], min(A_FOOT[0], x)))


def V_BELT(x):
    return v_up(x, BELT_Z(max(X_DLO_TIP, min(BELT_X_MAX, x))))


def V_GT(x):
    if x > X_ROOF_F:
        return v_up(x, z_a(x))
    return v_up(x, DLO_TOP_Z(max(X_DLO_TIP, x)))


def V_A(x):
    return S.v_along(x, v_up(x, z_a(min(A_FOOT[0], x))), 0.068)


def V_FRAME(x):
    return S.v_along(x, V_GT(x), 0.005 + 0.015 * geom.smoothstep((x - X_DLO_TIP) / 0.28))


def V_RAIL(x):
    v = S.v_along(x, V_GT(x), 0.072)
    k = _smooth(_clamp01((-1.15 - x) / 0.35))
    if k <= 0.0:
        return v
    y_old = abs(S.surface(x, v)[1])
    y_new = y_old + (S.Y_ROOF(x) - 0.038 - 0.012 * k - y_old) * k
    return S.v_at_y_upper(x, y_new)


Y_REARGLASS = Curve([
    (-2.460, 0.565), (-2.380, 0.585), (-2.220, 0.588), (-2.020, 0.568),
    (-1.850, 0.545), (X_KNEE, 0.525),
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
    k_r = _ramp(x, X_KNEE, 0.14)
    return c + (r - c) * k_r + (a - r) * k_f


def V_CEDGE(x):
    return v_up(x, Z_CEDGE(min(X_CTIP, x)))


Z_WTOP = Curve([
    (X_CTIP, 1.450), (-1.780, 1.462), (-1.880, 1.470), (-2.050, 1.475), (-2.300, 1.475),
], mode="pchip")


def V_WTOP(x):
    xx = min(X_CTIP, x)
    v_z = v_up(x, max(Z_WTOP(xx), Z_CEDGE(xx) + 0.028))
    y_lim = 0.51 + 0.09 * _smooth(_clamp01((xx - X_BLADE) / (X_CTIP - X_BLADE)))
    return max(min(v_z, S.v_at_y_upper(x, y_lim)), V_CEDGE(x) + 0.012)


def V_Q_TOP(x):
    if x >= X_DLO_TIP:
        return V_BELT(x)
    return V_RAIL_TOP(x)


def V_ROOF_LO(x):
    if x >= X_DLO_TIP:
        return V_RAIL(x) - 0.004
    return V_RAIL_TOP(x) - 0.004


def V_WEDGE_TOP(x):
    if x >= X_BLADE:
        return V_WTOP(x)
    if x >= X_FRIT:
        return V_FRIT(x) + 0.004
    return S.v_along(x, V_REARGLASS(x), 0.014) - 0.001


def _x_header(v):
    return X_ROOF_F + 0.135 * _smooth(_clamp01((v - 0.72) / 0.26))


def _hood_front(v):
    return N.JOIN_F(v)


Y_HOOD = Curve([
    (X_COWL, 0.835), (1.180, 0.818), (1.420, 0.790), (1.680, 0.758),
    (1.900, 0.718), (2.060, 0.665), (2.200, 0.585), (2.300, 0.460),
    (2.350, 0.260), (2.360, 0.000),
])


def V_HOOD(x):
    return S.v_at_y_upper(x, Y_HOOD(x))


GB_F = -0.115
GB_R = -0.255


# ------------------------------------------------------------- flank panels
PANELS = [
    dict(name="VPS_Fender_Front", x=(X_DOOR_F, N.JOIN_F), v=(V_SILL_HI, V_HOOD),
         nx=48, nv=42, arch=True, fender_vent=True, gap=dict(v0=False, x1=False),
         mat="paint"),
    dict(name="VPS_Door_Front", x=(X_DOOR_SPLIT, X_DOOR_F), v=(V_ROCK, V_BELT),
         nx=42, nv=38, arch=True, gap=dict(v0=False), mat="paint"),
    dict(name="VPS_Door_Rear", x=(X_DOOR_R, X_DOOR_SPLIT), v=(V_ROCK, V_BELT),
         nx=40, nv=38, arch=True, gap=dict(v0=False), mat="paint"),
    dict(name="VPS_Door_Low_F", x=(X_DOOR_SPLIT, X_DOOR_F), v=(V_SILL_HI, V_ROCK),
         nx=42, nv=10, arch=True, gap=dict(v0=False, v1=False), mat="black_gloss"),
    dict(name="VPS_Door_Low_R", x=(X_DOOR_R, X_DOOR_SPLIT), v=(V_SILL_HI, V_ROCK),
         nx=40, nv=10, arch=True, gap=dict(v0=False, v1=False), mat="black_gloss"),
    dict(name="VPS_Rocker", x=(-1.020, 1.060), v=(V_SILL, V_SILL_HI),
         nx=64, nv=8, arch=True, gap=dict(v0=False, x0=False, x1=False), mat="black_gloss"),
    dict(name="VPS_Quarter", x=(N.JOIN_R, X_DOOR_R), v=(V_Q_LO, V_Q_TOP),
         nx=58, nv=48, arch=True, gap=dict(v0=False, x0=False), mat="paint",
         fixed_x=(X_DLO_TIP,)),
    dict(name="VPS_Quarter_Low", x=(N.JOIN_R, X_BAND_F + 0.030), v=(V_BAND_LO, V_BAND_TOP),
         nx=18, nv=10, arch=True, gap=dict(x0=False, x1=False, v1=False),
         mat="black_gloss"),
    dict(name="VPS_Hood", x=(X_COWL, _hood_front), v=(V_HOOD, 1.0),
         nx=62, nv=36, gap=dict(v1=False), mat="paint", offset=0.0005),
    dict(name="VPS_Roof_Rail", x=(X_DLO_TIP, A_FOOT[0] + 0.015),
         v=(lambda x: V_GT(x) + 0.005, V_FRAME),
         nx=92, nv=5, gap=dict(x0=False), mat="black_gloss"),
    dict(name="VPS_Roof_Edge", x=(X_DLO_TIP, A_FOOT[0] + 0.015),
         v=(lambda x: V_FRAME(x) + 0.002, V_RAIL_TOP),
         nx=96, nv=9, gap=dict(x0=False), mat="paint"),

    # ---- greenhouse underlay & cowl plenum
    dict(name="VPS_Cowl_Black", x=(X_COWL - 0.040, X_COWL + 0.028),
         v=(V_HOOD, 1.0), nx=8, nv=24, gap=dict(v1=False, x0=False, x1=False),
         mat="black_trim", offset=-0.006, thickness=0.0),
    dict(name="VPS_Greenhouse_Black", x=(X_DLO_TIP - 0.030, X_COWL + 0.008),
         v=(V_BELT, 1.0), nx=90, nv=38, gap=dict(v1=False), mat="black_gloss",
         offset=-0.003, thickness=0.0),
    dict(name="VPS_Roof_Rear_Black", x=(N.JOIN_R, X_DLO_TIP - 0.020),
         v=(lambda x: min(V_REARGLASS(x), V_CEDGE(x) - 0.006), 1.0), nx=48, nv=24,
         gap=dict(v1=False, x0=False), mat="black_gloss", offset=-0.008, thickness=0.0),

    # ---- glazing & roof panels
    dict(name="VPS_Glass_Windshield", x=(_x_header, X_COWL - 0.010),
         v=(lambda x: V_A(x) + 0.004, 1.0), nx=56, nv=42, glass="glass",
         gap=dict(v1=False)),
    dict(name="VPS_Roof_Paint", x=(X_KNEE, X_ROOF_GLASS_R),
         v=(V_ROOF_LO, 1.0), nx=18, nv=20,
         gap=dict(v1=False, x0=False, v0=False), mat="paint"),
    dict(name="VPS_Glass_Roof", x=(X_ROOF_GLASS_R + 0.006, _x_header),
         v=(lambda x: V_RAIL(x) + 0.004, 1.0), nx=76, nv=32, glass="glass_dark",
         gap=dict(v1=False)),
    dict(name="VPS_Glass_Wedge", x=(lambda v: N.JOIN_R(v) + 0.002, X_CTIP),
         v=(V_CEDGE, V_WEDGE_TOP), nx=36, nv=10, glass="glass_dark", fixed_x=(X_BLADE,),
         gap=dict(x0=False, v1=False), offset=0.0022),
    dict(name="VPS_Glass_DoorFront", x=(GB_F, 0.805),
         v=(lambda x: V_BELT(x) + 0.010, lambda x: V_GT(x) - 0.004),
         nx=60, nv=28, glass="glass"),
    dict(name="VPS_Glass_DoorRear", x=(X_DOOR_R_TOP + 0.020, GB_R),
         v=(lambda x: V_BELT(x) + 0.010, lambda x: V_GT(x) - 0.004),
         nx=46, nv=28, glass="glass_dark"),
    dict(name="VPS_Glass_Quarter", x=(X_DLO_TIP + 0.012, X_DOOR_R_TOP - 0.012),
         v=(lambda x: V_BELT(x) + 0.008, lambda x: V_GT(x) - 0.004),
         nx=18, nv=12, glass="glass_dark"),
    dict(name="VPS_Glass_Frit", x=(X_FRIT, X_BLADE - 0.004),
         v=(V_FRIT, 1.0), nx=16, nv=36,
         mat="frit", offset=0.0024, thickness=0.0, gap=dict(v1=False)),
]


# ----------------------------------------------------------------- openings
def _cut_arches(ob):
    return C.cut_arches(ob, S.BODY, 0.35, 1.40)


VENT_OUTLINE = [
    (1.048, 1.042), (0.966, 1.040), (0.972, 0.905), (0.964, 0.742),
    (1.005, 0.778), (1.044, 0.855), (1.055, 0.955),
]


def _cut_fender_vent(ob):
    c = C.prism_y("_fvent_" + ob.name, VENT_OUTLINE, 0.55, 1.40)
    sheet = C.sheet_bvh(ob)
    C.difference(ob, [c], "fvent_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


CUTTERS = {"arch": _cut_arches, "fender_vent": _cut_fender_vent}


def build_panels(collection, lib):
    return BP.build_panels(PANELS, S.BODY, collection, lib, cutters=CUTTERS,
                           core_z=0.72, butt_bevel=False)


# ------------------------------------------------------------------ hidden
def build_shadow_shell(collection, lib, name="VPS_Shell_Shadow", skins=()):
    ob = BP.shadow_shell(N.BODY, collection, lib, name, nx=140, nv=80, inset=0.030)
    if skins:
        clear_shell(ob, skins)
    return ob


def clear_shell(shell, skins, gap=0.015, core_z=0.70):
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
    return BP.wheel_liners(S.BODY, collection, lib, "VPS_Liner_", y_outer=0.935,
                           mat="shadow", inner_wall=True, wall_z=0.25)


def build_underbody(collection, lib):
    return BP.underbody(S.BODY, collection, lib, "VPS_Underbody", x0=-2.26, length=4.34)


def build_all(collection, lib):
    made = []
    made += build_panels(collection, lib)
    made.append(build_shadow_shell(collection, lib, skins=list(made)))
    made += build_wheel_liners(collection, lib)
    made.append(build_underbody(collection, lib))
    import bpy
    for nm in ("VPS_Shell_Shadow", "VPS_Shell_Shadow_R", "VPS_Underbody", "VPS_Liner_R"):
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            M.apply_modifiers(ob)
            sheet = C.sheet_bvh(ob)
            C.difference(ob, rear_corner_cutters(both=True, y0=Y_CORNER_HIDDEN), "corner_")
            C.prune_off_sheet(ob, sheet)
    for nm in ("VPS_Shell_Shadow", "VPS_Underbody"):
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            sheet = C.sheet_bvh(ob)
            fc = C.prism_y("_fchin_" + nm, [(2.06, 0.05), (2.60, 0.05), (2.60, 0.305), (2.06, 0.285)], -1.10, 1.10)
            C.difference(ob, [fc], "fchin_")
            C.prune_off_sheet(ob, sheet)
    return made
