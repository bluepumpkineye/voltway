"""Avatr 06T panel layout: shut lines, window lines, panels, openings.

Read off the Autohome studio set (series 8538: c1_0004 side, c1_0002 front, c1_0006 rear) through the
solved cameras of a06t_cam.py; each shut line and window line is a curve built from its pixel readings:
  - Two-tone floating roof: gloss-black A-pillar, windscreen frame and glass roof (`A06T_Roof_Rail`,
    `A06T_Glass_Roof`) inside a thin painted roof strip (`A06T_Roof_Edge`); the C-pillar sail
    (`A06T_Quarter`) rises in body colour behind the long quarter window (`X_DLO_TIP`) to the roof
    spoiler plate (`A06T_Roof_Blade`, built in a06t_rear).
  - Frameless front and rear doors (`A06T_Door_Front`, `A06T_Door_Rear`) above a black rocker
    (`A06T_Rocker`).
  - A hood (`A06T_Hood`) whose side shut lines run from the cowl corners diagonally forward to the
    nose cap's top corners (`Y_HOOD`) and whose leading edge is the nose cap's top edge.
"""
import math

import a06t_cam as CAM
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
# From the side photograph c1_0004 through the solved camera (a06t_cam.py); the pixel readings
# are listed there. Everything is metres in the model frame (front axle +1.570).
X_COWL = S.COWL_X            # 1.120, windscreen base on the centreline
X_ROOF_F = 0.200             # windscreen header at the A-pillar's top (the centre header is at 0.40)
X_KNEE = S.KNEE_X            # -2.000, shooting-brake roof spoiler root
X_BPILLAR = -0.165           # front | rear door shut line (belt -0.19 .. sill -0.13)
X_DLO_TIP = -1.530           # quarter window's rear tip
X_DOOR_R_TOP = -1.120        # rear door trailing edge at the belt
X_ROOF_GLASS_R = -1.800      # panoramic glass roof ends under the spoiler
X_BLADE = -2.080             # the painted roof spoiler's trailing edge (c1_0004: tip at x -2.05..-2.11)
X_FRIT = -2.125              # ceramic frit band under the roof spoiler

# Rear glass wraps round each C-pillar as a dark wedge under the roof spoiler (c1_0004, c1_0005)
X_CTIP = -1.770
Z_CEDGE = Curve([
    (-1.700, 1.300), (-1.790, 1.262), (-1.900, 1.200), (-2.000, 1.140),
    (-2.120, 1.090), (-2.250, 1.040), (-2.410, 0.990),
], mode="pchip")
Y_WTOP_BLADE = 0.495


def _zx_curve(px, y, lo=None, hi=None):
    """z -> x of a (near-vertical) line read in pixels on the plane y."""
    pts = CAM.zx(px, y)
    if lo:
        pts = [lo] + pts
    if hi:
        pts = pts + [hi]
    return Curve(pts, mode="pchip")


def _xz_curve(px, y, lo=None, hi=None):
    pts = CAM.xz(px, y)
    if lo:
        pts = [lo] + pts
    if hi:
        pts = pts + [hi]
    return Curve(pts, mode="pchip")


# Front door leading edge: nearly upright at x 1.02-1.04, curling forward to the A-pillar's foot
_DOOR_F_EDGE = _zx_curve(CAM.DOOR_F_EDGE_PX, 0.93, lo=(0.150, 1.005), hi=(1.040, 0.930))

# Rear door trailing edge: from the quarter glass's lower tip, bulging back and down into the arch
_DOOR_R_EDGE = _zx_curve(CAM.DOOR_R_EDGE_PX, 0.93, lo=(0.150, -1.130), hi=(1.200, -1.070))

# Top of the black rocker cladding = the doors', fender's and quarter's lower edge
ROCKER_TOP = _xz_curve(CAM.ROCKER_TOP_PX, 0.93, lo=(-1.300, 0.300), hi=(1.300, 0.260))


def X_DOOR_F(v):
    return _DOOR_F_EDGE(S.section_v(0.78, v)[1])


def X_DOOR_R(v):
    return _DOOR_R_EDGE(S.section_v(-1.15, v)[1])


def V_SILL(x):
    """Floor edge: where the flank panels start."""
    return S.v_at_z(x, S.Z_FLOOR(x) + 0.028, 0.0, S.V_SHOULDER)


def V_ROCK(x):
    """Top of the black rocker cladding: the lower edge of the fender, the doors and the quarter."""
    return S.v_at_z(x, ROCKER_TOP(x), 0.0, S.V_SHOULDER)


def v_up(x, z):
    """Upper-section parameter whose height is z at station x."""
    return S.v_at_z(x, z, S.V_SHOULDER, 0.995)


# ------------------------------------------------------- the rear bumper
# Behind the rear wheel the painted quarter meets the gloss-black lower
# diffuser wrap-around (rising from z 0.38 behind the arch to z 0.52 at the
# rear corner, matching a06t_rear.Z_BLACK = 0.520).
Z_BAND_TOP = Curve([
    (-1.780, 0.420), (-1.900, 0.470), (-2.050, 0.535), (-2.170, 0.600),
    (-2.260, 0.665), (-2.330, 0.640), (-2.410, 0.580), (-2.470, 0.575),
], mode="pchip")
Z_BAND_LO = Curve([
    (-1.780, 0.225), (-1.920, 0.245), (-2.050, 0.280), (-2.180, 0.330),
    (-2.300, 0.375), (-2.420, 0.395), (-2.600, 0.400), (-2.800, 0.400),
], mode="pchip")
X_BAND_F = -1.790
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
# Lower edge of the side glass (c1_0004): nearly flat along the doors, then kicking up steeply
# along the quarter window to its rear tip
BELT_Z = _xz_curve(CAM.BELT_PX, 0.85)
BELT_X_MAX = 0.962

# Upper edge of the side glass along the roof arch (the roof strip's lower edge minus the frame)
DLO_TOP_Z = Curve([
    (X_DLO_TIP, 1.212), (-1.417, 1.260), (-1.285, 1.327), (-1.080, 1.372),
    (-0.930, 1.386), (-0.770, 1.394), (-0.570, 1.395), (-0.330, 1.392),
    (-0.200, 1.398), (-0.070, 1.399), (0.083, 1.394), (X_ROOF_F, 1.380),
], mode="pchip")
A_FOOT = (0.968, 1.013)
A_TOP = (X_ROOF_F, 1.398)
_A_LINE = Curve([(0.186, 1.398), (0.339, 1.339), (0.492, 1.277), (0.636, 1.217),
                 (0.799, 1.130), (0.968, 1.013)], mode="pchip")


def z_a(x):
    return _A_LINE(max(A_TOP[0], min(A_FOOT[0], x)))


def V_BELT(x):
    return v_up(x, BELT_Z(max(X_DLO_TIP, min(BELT_X_MAX, x))))


def V_GT(x):
    if x > X_ROOF_F:
        return v_up(x, z_a(x))
    return v_up(x, DLO_TOP_Z(max(X_DLO_TIP, x)))


def V_A(x):
    """The windscreen's side edge: 34 mm inboard of the A-pillar's outer line (a thin black frame)."""
    return S.v_along(x, v_up(x, z_a(min(A_FOOT[0], x))), 0.034)


def V_FRAME(x):
    """Top of the thin black frame round the side glass (c1_0004: ~30 mm, thinning to nothing at the
    quarter window's tip)."""
    return S.v_along(x, V_GT(x), 0.006 + 0.026 * geom.smoothstep((x - X_DLO_TIP) / 0.30))


def V_RAIL(x):
    """The panoramic glass roof's side edge: the painted roof strip is ~85 mm wide above the frame."""
    return S.v_along(x, V_GT(x), 0.085)


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
    """The wedge's lower edge: where the body-colour C-pillar/quarter meets the rear glass's dark side
    (the photographed line, c1_0004: (-1.77, 1.26) down to (-2.41, 0.99))."""
    return v_up(x, Z_CEDGE(min(X_CTIP, x)))


# the wedge's upper edge: the underside of the roof spoiler (c1_0004: z 1.26 .. 1.29)
Z_WTOP = Curve([(X_CTIP, 1.262), (-1.850, 1.272), (-1.950, 1.284), (-2.080, 1.290), (-2.300, 1.290)],
               mode="pchip")


def V_WTOP(x):
    """Upper edge of the wedge. The spoiler overhangs the glass, so past the point where the loft no
    longer reaches the spoiler's underside the edge is held at a lateral limit instead (0.50 at the
    spoiler's end, widening to the C-edge's 0.60)."""
    xx = min(X_CTIP, x)
    v_z = v_up(x, max(Z_WTOP(xx), Z_CEDGE(xx) + 0.030))
    y_lim = 0.50 + 0.10 * _smooth(_clamp01((xx - X_BLADE) / (X_CTIP - X_BLADE)))
    return max(min(v_z, S.v_at_y_upper(x, y_lim)), V_CEDGE(x) + 0.012)


def V_Q_TOP(x):
    """The quarter / C-pillar paint runs right up to the roof edge behind the quarter window's tip: it is
    one continuous skin, and the dark wedge of the rear glass lies on it as a separate, slightly proud
    piece (so no paint boundary has to follow the wedge's curved outline)."""
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
    """The windscreen's top edge: at the A-pillar's top x 0.20, curving ahead to x 0.42 across the
    centre (c1_0004: the LiDAR housing stands just behind it, its top at x 0.15..0.40)."""
    return X_ROOF_F + 0.22 * _smooth(_clamp01((v - 0.70) / 0.28))


def _hood_front(v):
    """The bonnet's leading edge is the nose cap's top edge: one shut line across the front."""
    return N.JOIN_F(v)


# The hood's side shut lines run from the cowl corners diagonally forward to the nose's top corners
# (c1_0002: photo rays onto the surface, y 0.76 at x 1.25 -> 0.67 at 1.97 -> 0.49 at 2.25)
Y_HOOD = Curve([
    (X_COWL, 0.775), (1.255, 0.760), (1.60, 0.713), (1.97, 0.666),
    (2.05, 0.630), (2.15, 0.585), (2.22, 0.535), (2.27, 0.465), (2.30, 0.385),
    (2.318, 0.250), (2.326, 0.120), (2.330, 0.0),
])


def V_HOOD(x):
    return S.v_at_y_upper(x, Y_HOOD(x))


# B-pillar glass edges
GB_F = -0.140
GB_R = -0.300


# ------------------------------------------------------------- flank panels
PANELS = [
    dict(name="A06T_Fender_Front", x=(X_DOOR_F, N.JOIN_F), v=(V_ROCK, V_HOOD),
         nx=46, nv=40, arch=True, gap=dict(v0=False, x1=False),
         mat="paint"),
    dict(name="A06T_Door_Front", x=(X_BPILLAR, X_DOOR_F), v=(V_ROCK, V_BELT),
         nx=40, nv=40, arch=True, gap=dict(v0=False), mat="paint"),
    dict(name="A06T_Door_Rear", x=(X_DOOR_R, X_BPILLAR), v=(V_ROCK, V_BELT),
         nx=38, nv=40, arch=True, gap=dict(v0=False), mat="paint"),
    dict(name="A06T_Rocker", x=(-1.12, 1.22), v=(V_SILL, V_ROCK),
         nx=60, nv=14, arch=True, gap=dict(v0=False, x0=False, x1=False), mat="black_trim"),
    dict(name="A06T_Quarter", x=(N.JOIN_R, X_DOOR_R), v=(V_Q_LO, V_Q_TOP),
         nx=56, nv=48, arch=True, gap=dict(v0=False, x0=False), mat="paint",
         fixed_x=(X_DLO_TIP, X_CTIP)),
    dict(name="A06T_Quarter_Low", x=(N.JOIN_R, X_BAND_F + 0.030), v=(V_BAND_LO, V_BAND_TOP),
         nx=16, nv=10, arch=True, gap=dict(x0=False, x1=False, v1=False),
         mat="black_gloss"),
    dict(name="A06T_Hood", x=(X_COWL, _hood_front), v=(V_HOOD, 1.0),
         nx=60, nv=34, gap=dict(v1=False), mat="paint", offset=0.0005),
    # On the Avatr 06T (c1_0001..c1_0007.jpg), the A-pillar and upper roof arch
    # are gloss black, creating the floating-roof silhouette, while the C-pillar
    # on A06T_Quarter rises in body colour behind X_DLO_TIP.
    dict(name="A06T_Roof_Rail", x=(X_DLO_TIP, X_COWL),
         v=(lambda x: V_GT(x) + 0.006, V_FRAME),
         nx=100, nv=6, gap=dict(x0=False), mat="black_gloss"),
    # the painted roof strip between the frame and the glass roof (c1_0004, design-ratio): body colour
    dict(name="A06T_Roof_Edge", x=(X_DLO_TIP, X_ROOF_F),
         v=(lambda x: V_FRAME(x) + 0.002, V_RAIL),
         nx=72, nv=8, gap=dict(x0=False, x1=False), mat="paint"),

    # ---- greenhouse underlay
    dict(name="A06T_Greenhouse_Black", x=(X_DLO_TIP - 0.030, X_COWL),
         v=(V_BELT, 1.0), nx=84, nv=36, gap=dict(v1=False), mat="black_gloss",
         offset=-0.003, thickness=0.0),
    dict(name="A06T_Roof_Rear_Black", x=(N.JOIN_R, X_DLO_TIP - 0.020),
         v=(lambda x: min(V_REARGLASS(x), V_CEDGE(x) - 0.006), 1.0), nx=48, nv=24,
         gap=dict(v1=False, x0=False), mat="black_gloss", offset=-0.003, thickness=0.0),

    # ---- glazing & roof panels
    dict(name="A06T_Glass_Windshield", x=(_x_header, X_COWL - 0.012),
         v=(lambda x: V_A(x) + 0.004, 0.9995), nx=52, nv=40, glass="glass",
         gap=dict(v1=False)),
    # Body-colour rear roof crown leading into the shooting-brake roof spoiler
    dict(name="A06T_Roof_Paint", x=(X_KNEE, X_ROOF_GLASS_R),
         v=(V_ROOF_LO, 1.0), nx=36, nv=24, fixed_x=(X_CTIP,),
         gap=dict(v1=False, x0=False, v0=False), mat="paint"),
    # Panoramic dark glass roof spanning both rows
    dict(name="A06T_Glass_Roof", x=(X_ROOF_GLASS_R + 0.006, lambda v: _x_header(v) - 0.020),
         v=(lambda x: V_RAIL(x) + 0.004, 0.9995), nx=56, nv=22, glass="glass_dark",
         gap=dict(v1=False)),
    dict(name="A06T_Glass_Wedge", x=(lambda v: N.JOIN_R(v) + 0.002, X_CTIP),
         v=(V_CEDGE, V_WEDGE_TOP), nx=48, nv=10, glass="glass_dark", fixed_x=(X_BLADE,),
         gap=dict(x0=False, v1=False), offset=0.0016),
    dict(name="A06T_Glass_DoorFront", x=(GB_F, 0.940),
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
    ob = BP.shadow_shell(N.BODY, collection, lib, name, nx=104, nv=64, inset=0.028)
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
