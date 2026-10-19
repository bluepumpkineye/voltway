"""Nio ES8 panel layout: shut lines, window lines, panels, openings.

Follows carkit.body.panels (dict-based PANELS table, matching zx_panels.py).
"""
import es8_surface as S
import es8_nose as N
from carkit import geom
from carkit.geom import Curve, clamp01 as _clamp01, smoothstep as _smooth, ramp as _ramp
from carkit import mesh as M
from carkit import cut as C
from carkit.body import panels as BP

GAP = BP.GAP
SKIN = M.SKIN

# ----------------------------------------------------------------- stations
X_COWL = S.COWL_X            # 1.320, windscreen base
X_ROOF_F = 0.520             # windscreen header
X_KNEE = S.KNEE_X            # -2.180, roof spoiler trailing edge
X_DLO_FRONT = 0.740          # where roof-side glass line meets A-pillar
X_DOOR_TOP_F = 1.035         # front door leading edge at belt
X_GLASS_F = 1.030            # front door glass front edge
X_FOOT_END = 1.210           # A-pillar foot end
X_DLO_TIP = -1.880           # 3rd-row quarter glass rear tip
X_BLADE = -2.175             # roof spoiler trailing edge
X_ROOF_GLASS_R = -1.650      # panoramic glass roof rear edge
GB_F = -0.045                # B-pillar front door glass edge
GB_R = -0.185                # B-pillar rear door glass edge
X_BPILLAR_C = -0.065         # B-pillar nominal center station
X_DOOR_R_TOP = -1.200        # rear door trailing edge at beltline

_DOOR_F_EDGE = Curve([
    (0.25, 1.015), (0.50, 1.025), (0.80, 1.030), (1.14, 1.035),
], mode="pchip")

_DOOR_B_EDGE = Curve([
    (0.25, -0.075), (0.55, -0.070), (0.85, -0.062), (1.14, -0.055),
], mode="pchip")

_DOOR_R_EDGE = Curve([
    (0.32, -1.080), (0.55, -1.150), (0.85, -1.215), (1.14, -1.245),
], mode="pchip")


def X_DOOR_F(v):
    return _DOOR_F_EDGE(S.section_v(1.03, v)[1])


def X_BPILLAR(v):
    return _DOOR_B_EDGE(S.section_v(-0.07, v)[1])


def X_DOOR_R(v):
    return _DOOR_R_EDGE(S.section_v(-1.16, v)[1])


def Z_FLANK_LOW(x):
    if x >= 1.02:
        return max(0.295, 0.340 - (x - 1.02) * 0.035)
    return min(0.380, 0.340 + (1.02 - x) * 0.015)


def V_SILL(x):
    return S.v_at_z(x, Z_FLANK_LOW(x), 0.0, S.V_SHOULDER)


def v_up(x, z):
    return S.v_at_z(x, z, S.V_SHOULDER, 0.995)


# ------------------------------------------------------------ window lines
# Horizontal 16 mm beltline ("宽舷肩线")
BELT_Z = Curve([
    (1.05, 1.120), (0.60, 1.125), (0.00, 1.132), (-0.75, 1.142),
    (-1.35, 1.155), (X_DLO_TIP, 1.175),
])

DLO_TOP_Z = Curve([
    (X_DLO_FRONT, 1.445), (0.42, 1.595), (0.00, 1.655), (-0.55, 1.662),
    (-1.15, 1.650), (-1.60, 1.615), (X_DLO_TIP, 1.540),
])

A_FOOT = (1.300, 1.115)
A_TOP = (X_ROOF_F, 1.565)


def z_a(x):
    t = (A_FOOT[0] - x) / (A_FOOT[0] - A_TOP[0])
    return A_FOOT[1] + (A_TOP[1] - A_FOOT[1]) * t


def V_BELT(x):
    return v_up(x, BELT_Z(max(X_DLO_TIP, min(1.05, x))))


def V_GT(x):
    if x > X_DLO_FRONT:
        miss = z_a(X_DLO_FRONT) - DLO_TOP_Z(X_DLO_FRONT)
        t = _clamp01((x - X_DLO_FRONT) / 0.30)
        return v_up(x, z_a(x) - miss * (1.0 - _smooth(t)))
    return v_up(x, DLO_TOP_Z(max(X_DLO_TIP, x)))


def V_A(x):
    return S.v_along(x, v_up(x, z_a(min(A_FOOT[0], x))), 0.080)


def V_RAIL(x):
    return S.v_along(x, V_GT(x), 0.055)


Y_REARGLASS = Curve([
    (-2.60, 0.655), (-2.48, 0.645), (-2.34, 0.625), (X_KNEE, 0.595),
])


def V_REARGLASS(x):
    return S.v_at_y_upper(x, Y_REARGLASS(x))


def V_RAIL_TOP(x):
    a = V_A(x)
    r = V_RAIL(x)
    c = V_REARGLASS(x) - 0.004
    k_f = _ramp(x, X_ROOF_F)
    k_r = _ramp(x, X_KNEE)
    return c + (r - c) * k_r + (a - r) * k_f


X_CTIP = -1.920
Z_CEDGE = Curve([
    (-1.920, 1.185), (-2.080, 1.160), (-2.280, 1.150), (-2.520, 1.145),
], mode="pchip")
Y_WTOP_BLADE = 0.595


def V_CEDGE(x):
    v = v_up(x, Z_CEDGE(min(X_CTIP, x)))
    if x < -2.22:
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


def V_QBASE(x):
    if x >= X_DLO_TIP:
        return V_BELT(x)
    if x >= X_CTIP:
        s = _smooth((X_DLO_TIP - x) / (X_DLO_TIP - X_CTIP))
        return V_BELT(X_DLO_TIP) + (V_CEDGE(X_CTIP) - V_BELT(X_DLO_TIP)) * s
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
    return S.v_along(x, V_REARGLASS(x), 0.003) - 0.001


def _hood_front(v):
    return N.JOIN_F(v)


Y_HOOD = Curve([
    (X_COWL, 0.795), (1.55, 0.785), (1.85, 0.775),
    (2.15, 0.750), (2.35, 0.700), (2.46, 0.640),
])


def V_HOOD(x):
    return S.v_at_y_upper(x, Y_HOOD(x))


V_ARCHTOP = 0.415
X_ARCHTOP = -1.820


def _v_diag(x):
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
    if x >= X_ARCHTOP:
        return V_SILL(x)
    return max(V_SILL(x), _v_diag(x))


def _quarter_tip():
    x = -1.85
    while x > -2.52:
        if V_QLOW(x) >= V_Q_TOP(x) - 0.004:
            return x + 0.002
        x -= 0.002
    return -2.52


X_QTIP = _quarter_tip()


def _wedge_end():
    x = -2.20
    while x > -2.54:
        if V_WEDGE_TOP(x) - V_CEDGE(x) < 0.012:
            return x
        x -= 0.002
    return -2.54


X_WEDGE_END = _wedge_end()

# ------------------------------------------------------------- flank panels
PANELS = [
    dict(name="ES8_Fender_Front", x=(X_DOOR_F, N.JOIN_F), v=(V_SILL, V_HOOD),
         nx=46, nv=40, arch=True, gap=dict(v0=False, x1=False), mat="paint"),
    dict(name="ES8_Door_Front", x=(X_BPILLAR, X_DOOR_F), v=(V_SILL, V_BELT),
         nx=42, nv=40, arch=True, gap=dict(v0=False), mat="paint"),
    dict(name="ES8_Door_Rear", x=(X_DOOR_R, X_BPILLAR), v=(V_SILL, V_BELT),
         nx=40, nv=40, arch=True, gap=dict(v0=False), mat="paint"),
    dict(name="ES8_Quarter", x=(X_QTIP, X_DOOR_R), v=(V_QLOW, V_QBASE),
         nx=56, nv=48, arch=True, gap=dict(v0=False, x0=False), mat="paint"),
    dict(name="ES8_Quarter_Pillar", x=(X_CTIP + 0.002, X_DLO_TIP), v=(V_QBASE, V_Q_TOP),
         nx=12, nv=24, gap=dict(v0=False, x1=False), mat="black_gloss"),
    dict(name="ES8_Hood", x=(X_COWL, _hood_front), v=(V_HOOD, 1.0),
         nx=60, nv=34, gap=dict(v1=False, x1=False), mat="paint", offset=0.0005),
    # Floating black roof rail & A-pillar
    dict(name="ES8_Roof_Rail", x=(X_DLO_TIP, X_COWL),
         v=(lambda x: V_GT(x) + 0.006, V_RAIL_TOP),
         nx=140, nv=10, gap=dict(x0=False), mat="black_gloss"),
    dict(name="ES8_Pillar_Foot", x=(X_DOOR_TOP_F + 0.004, X_FOOT_END),
         v=(lambda x: V_HOOD(x) + 0.0005, lambda x: V_GT(x) + 0.006),
         nx=14, nv=12, gap=dict(v0=False, v1=False), mat="black_gloss"),

    # ---- greenhouse underlay
    dict(name="ES8_Greenhouse_Black", x=(X_DLO_TIP - 0.030, X_COWL),
         v=(V_BELT, 1.0), nx=120, nv=50, gap=dict(v1=False), mat="black_gloss",
         offset=-0.003, thickness=0.0),
    dict(name="ES8_Roof_Rear_Black", x=(N.JOIN_R, X_DLO_TIP - 0.020),
         v=(lambda x: min(V_REARGLASS(x), V_CEDGE(x) - 0.006), 1.0), nx=48, nv=24,
         gap=dict(v1=False, x0=False), mat="black_gloss", offset=-0.010, thickness=0.0),

    # ---- glazing
    dict(name="ES8_Glass_Windshield", x=(X_ROOF_F, X_COWL - 0.012),
         v=(lambda x: V_A(x) + 0.004, 0.9995), nx=72, nv=56, glass="glass",
         gap=dict(v1=False)),
    dict(name="ES8_Roof_Paint", x=(X_KNEE - 0.003, X_ROOF_GLASS_R),
         v=(V_ROOF_LO, 1.0), nx=36, nv=24, fixed_x=(X_CTIP,),
         gap=dict(v1=False, x0=False, v0=False), mat="black_gloss"),
    dict(name="ES8_Glass_Roof", x=(X_ROOF_GLASS_R + 0.006, X_ROOF_F - 0.020),
         v=(lambda x: V_RAIL(x) + 0.004, 0.9995), nx=64, nv=30, glass="glass_dark",
         gap=dict(v1=False)),
    dict(name="ES8_Glass_Wedge", x=(X_WEDGE_END, X_CTIP),
         v=(V_CEDGE, V_WEDGE_TOP), nx=36, nv=10, glass="glass_dark",
         gap=dict(x0=False, v1=False)),
    dict(name="ES8_Glass_DoorFront", x=(GB_F, X_GLASS_F),
         v=(lambda x: V_BELT(x) + 0.010, lambda x: V_GT(x) - 0.004),
         nx=72, nv=28, glass="glass"),
    dict(name="ES8_Glass_DoorRear", x=(-1.20, GB_R),
         v=(lambda x: V_BELT(x) + 0.010, lambda x: V_GT(x) - 0.004),
         nx=52, nv=28, glass="glass_dark"),
    dict(name="ES8_Glass_Quarter", x=(X_DLO_TIP + 0.012, -1.24),
         v=(lambda x: V_BELT(x) + 0.008, lambda x: V_GT(x) - 0.004),
         nx=28, nv=16, glass="glass_dark"),
    dict(name="ES8_Glass_Rear", x=(lambda v: N.JOIN_R(v) + 0.004, X_BLADE - 0.006),
         v=(V_REARGLASS, 0.9995), nx=44, nv=40, glass="glass_dark",
         gap=dict(v1=False, x0=False)),
]


def _cut_arches(ob):
    return C.cut_arches(ob, S.BODY, 0.35, 1.40)


CUTTERS = {"arch": _cut_arches}


def build_panels(collection, lib):
    return BP.build_panels(PANELS, S.BODY, collection, lib, cutters=CUTTERS,
                           core_z=0.75, butt_bevel=False)


def build_shadow_shell(collection, lib, name="ES8_Shell_Shadow", skins=()):
    ob = BP.shadow_shell(N.BODY, collection, lib, name, nx=140, nv=80, inset=0.030)
    if skins:
        clear_shell(ob, skins)
    return ob


def clear_shell(shell, skins, gap=0.015, core_z=0.74):
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
    return len(moved)


def build_wheel_liners(collection, lib):
    return BP.wheel_liners(S.BODY, collection, lib, "ES8_Liner_", y_outer=0.950,
                           mat="shadow", inner_wall=True, wall_z=0.25)


def build_underbody(collection, lib):
    return BP.underbody(S.BODY, collection, lib, "ES8_Underbody", x0=-2.35, length=4.70)


def build_all(collection, lib):
    made = []
    made += build_panels(collection, lib)
    made.append(build_shadow_shell(collection, lib, skins=list(made)))
    made += build_wheel_liners(collection, lib)
    made.append(build_underbody(collection, lib))
    return made
