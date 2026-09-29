"""Luxeed RX panel layout: shut lines, window lines, panels, openings.

The machinery is carkit's (carkit.body.panels, carkit.body.fascia,
carkit.cut); this module is the RX's layout, read off the camera-matched
photographs (rx_ref_match.py). Heights and stations below are model metres;
where a line was measured, the photo it came from is named.

    lines       door edges, cowl, A-pillar, belt, glass top, hood edge,
                header, roof spoiler, backlight edges
    PANELS      every flank panel as a region of (x, v)
    openings    wheel arches and the fender vent, cut by exact booleans on
                the half sheets before mirroring
    hidden      shadow shell, wheel liners, underbody tray

Greenhouse: a black-gloss underlay covers the whole greenhouse 3 mm inside
the skin and the glazing sits ON the skin cut to the window outlines, as on
the SU7. On the RX the A-pillars and roof rails are body colour, the roof
between them dark glass ahead of the B-pillar and paint behind it; the rear
glass wraps round each C-pillar as a dark wedge under the roof spoiler.
"""
import math

import rx_surface as S
import rx_nose as N
from carkit import geom
from carkit.geom import Curve, clamp01 as _clamp01, smoothstep as _smooth, ramp as _ramp
from carkit import mesh as M
from carkit import cut as C
from carkit.body import panels as BP

GAP = BP.GAP
SKIN = M.SKIN

# ----------------------------------------------------------------- stations
X_COWL = S.COWL_X            # 0.800, screen base
X_ROOF_F = 0.030             # windscreen header (side photo: A-pillar meets the glass top)
X_KNEE = S.KNEE_X            # -2.200, roof spoiler: backlight below it
X_BPILLAR = -0.345           # front | rear door (side photo, x -0.34 .. -0.35)
X_DLO_TIP = -1.550           # the side glass's rear tip (side photo: -1.546, z 1.28)
X_DOOR_R_TOP = -1.395        # rear door's rear edge at the belt
# The roof glass's rear edge. It first ran back to the C-pillar (x -1.555,
# the rear photo's grazing view of the roof); the owner's review of the high
# rear 3/4 marked that as wrong - the purple show car's roof reads body colour
# over the rear seats (collage_autohome), dark only over the front
# (front34_high_silver). Glass ahead of the B-pillar, paint behind it.
X_ROOF_GLASS_R = -0.345
X_BLADE = -1.968             # the roof spoiler blade's trailing edge (side photo: -2.00, 1.415)
X_FRIT = -2.306              # the black band across the glass's top ends here (v 295)
# The rear glass wraps round each C-pillar as a dark wedge under the roof
# spoiler (side photo u 830-910, forest and street 3/4s, the collage's rear
# 3/4): the painted C-pillar stops at a crisp edge falling from the wedge's
# tip, just behind the side glass, to the ducktail's corner. Cast from the
# side photo onto the loft: the edge at y 0.55-0.565; the wedge's top edge
# (the spoiler's side) rises from the tip to the blade's end.
X_CTIP = -1.827
Z_CEDGE = Curve([(-1.827, 1.387), (-1.886, 1.355), (-1.948, 1.326), (-2.031, 1.294),
                 (-2.107, 1.268), (-2.188, 1.241), (-2.267, 1.214), (-2.350, 1.186)],
                mode="pchip")
Y_WTOP_BLADE = 0.505         # the wedge's top edge meets the blade's end here

# Front door's leading edge: nearly upright at x 0.77 (side photo, z 0.31-1.0)
_DOOR_F_EDGE = Curve([(0.20, 0.766), (0.40, 0.769), (0.70, 0.772), (1.00, 0.770),
                      (1.12, 0.760)], mode="pchip")
# Rear door's trailing edge, by height: down from the belt, then round the
# wheel opening (kept >= 45 mm clear of the painted arch) to the sill.
_DOOR_R_EDGE = Curve([(0.20, -0.975), (0.40, -0.985), (0.55, -1.025), (0.66, -1.085),
                      (0.76, -1.165), (0.84, -1.260), (0.90, -1.345), (0.96, -1.405),
                      (1.05, -1.420), (1.16, -1.400), (1.30, -1.395)], mode="pchip")


def X_DOOR_F(v):
    return _DOOR_F_EDGE(S.section_v(0.77, v)[1])


def X_DOOR_R(v):
    return _DOOR_R_EDGE(S.section_v(-1.20, v)[1])


def V_SILL(x):
    """Floor edge: where the flank panels start."""
    return S.v_at_z(x, S.Z_FLOOR(x) + 0.030, 0.0, S.V_SHOULDER)


def v_up(x, z):
    """Upper-section parameter whose height is z at station x."""
    return S.v_at_z(x, z, S.V_SHOULDER, 0.995)


# ------------------------------------------------------- the rear bumper
# Behind the rear wheel the paint stops at the gloss black lower bumper's
# top edge, climbing from the arch (z 0.44) to the corner (0.57, where the
# rear face's black starts, rx_rear.Z_BLACK); the black band's own lower
# edge climbs from 0.26 behind the arch to 0.41 at the corner - the body
# is cut up steeply behind the wheel (side photo cast at y 0.88-0.92: top
# u 900/918/930 v 400/384/380, bottom u 884/910/938 v 436/426/408). It hung
# down to the sill there, a painted flap reaching for the ground.
Z_BAND_TOP = Curve([(-2.050, 0.420), (-2.100, 0.440), (-2.135, 0.458), (-2.190, 0.508),
                    (-2.238, 0.548), (-2.308, 0.570), (-2.450, 0.575)], mode="pchip")
Z_BAND_LO = Curve([(-2.050, 0.240), (-2.100, 0.255), (-2.200, 0.310), (-2.300, 0.375),
                   (-2.362, 0.412), (-2.450, 0.435), (-2.600, 0.440), (-2.800, 0.440)],
                  mode="pchip")
X_BAND_F = -2.060            # the band's front, inside the wheel opening
Y_CORNER = 0.785             # outboard of the grey pods (rear photo: y 0.41-0.78)
# the hidden shell, tray and liner go from further in: cut only outboard of
# the pods, the shell's own flank (|y| 0.78-0.80) still hung below the band
Y_CORNER_HIDDEN = 0.550


def V_BAND_TOP(x):
    return S.v_at_z(x, Z_BAND_TOP(x), 0.0, S.V_SHOULDER)


def V_BAND_LO(x):
    return S.v_at_z(x, Z_BAND_LO(x), 0.0, S.V_SHOULDER)


def V_Q_LO(x):
    """Bottom of the rear quarter: the sill ahead of the arch, the black
    lower bumper's top behind it (the switch is inside the opening)."""
    k = _ramp(x, X_BAND_F, 0.04)
    return V_BAND_TOP(x) + (V_SILL(x) - V_BAND_TOP(x)) * k


def rear_corner_cutters(both=False, y0=Y_CORNER):
    """Prisms along y taking away everything under the black band's lower
    edge outboard of y0, behind the rear wheel - on both sides when the
    object's mirror is already applied."""
    xs = [-2.08 - 0.02 * i for i in range(37)]
    outline = [(x, Z_BAND_LO(x)) for x in xs] + [(xs[-1], -0.30), (xs[0], -0.30)]
    made = [C.prism_y("_corner_L", outline, y0, 1.60)]
    if both:
        made.append(C.prism_y("_corner_R", outline, -1.60, -y0))
    return made


# ------------------------------------------------------------ window lines
# Lower edge of the side glass (side photo): rising from 1.12 at the front
# door to the tip.
BELT_Z = Curve([(0.80, 1.114), (0.28, 1.119), (-0.09, 1.121), (-0.41, 1.126),
                (-0.69, 1.142), (-0.97, 1.163), (-1.19, 1.193), (-1.35, 1.231),
                (-1.46, 1.266), (X_DLO_TIP, 1.285)])
# Upper edge along the roof side (side photo), and the A-pillar's glass edge
# from (0.62, 1.13) to the header - straight within 20 mm.
DLO_TOP_Z = Curve([(0.030, 1.421), (-0.229, 1.474), (-0.548, 1.492), (-0.717, 1.495),
                   (-1.002, 1.477), (-1.234, 1.436), (-1.392, 1.383), (-1.510, 1.318),
                   (X_DLO_TIP, 1.285)])
A_FOOT = (0.620, 1.130)
A_TOP = (X_ROOF_F, 1.421)


def z_a(x):
    """Height of the A-pillar's glass edge at station x."""
    t = (A_FOOT[0] - x) / (A_FOOT[0] - A_TOP[0])
    return A_FOOT[1] + (A_TOP[1] - A_FOOT[1]) * t


def V_BELT(x):
    return v_up(x, BELT_Z(max(X_DLO_TIP, min(0.80, x))))


def V_GT(x):
    """Top of the side glass: the A-pillar edge ahead of the header, the roof
    side behind it."""
    if x > X_ROOF_F:
        return v_up(x, z_a(x))
    return v_up(x, DLO_TOP_Z(max(X_DLO_TIP, x)))


def V_A(x):
    """The windscreen's side edge: 75 mm of body-colour A-pillar above the
    door glass's edge."""
    return S.v_along(x, v_up(x, z_a(min(A_FOOT[0], x))), 0.075)


def V_RAIL(x):
    """Inboard edge of the body-colour roof rail: 60 mm above the side
    glass (side photo: a ~70 mm silver band over the windows)."""
    return S.v_along(x, V_GT(x), 0.060)


# Backlight edges: an oval in the rear photograph, read onto the model -
# +/-0.52 at the top (z 1.32), widest +/-0.57 at mid height (z 1.21), and
# drawing in again to the base over the ducktail (the glass's foot over the
# tail cap, rx_rear.GLASS_LOW, rounds the lower corners)
Y_REARGLASS = Curve([(-2.46, 0.560), (-2.40, 0.570), (-2.33, 0.570), (-2.27, 0.552),
                     (X_KNEE, 0.528)])


def V_REARGLASS(x):
    return S.v_at_y_upper(x, Y_REARGLASS(x))


def V_FRIT(x):
    """The black band's outboard edge: 12 mm inside the backlight's edge
    below the knee; above it, under the blade, right to the C-pillar's
    painted top (a band that drew in on its own left the shadow shell
    showing between them)."""
    lo = S.v_at_y_upper(x, Y_REARGLASS(min(x, X_KNEE))) + 0.012
    hi = V_RAIL_TOP(x) + 0.004
    k = _ramp(x, X_KNEE)
    return lo + (hi - lo) * k


def V_RAIL_TOP(x):
    """The body-colour band's top: the screen edge down the A-pillar, the
    rail over the roof glass, the backlight's edge behind the spoiler, with
    30 mm ramps between them."""
    a = V_A(x)
    r = V_RAIL(x)
    c = V_REARGLASS(x) - 0.004
    k_f = _ramp(x, X_ROOF_F)
    k_r = _ramp(x, X_KNEE)
    return c + (r - c) * k_r + (a - r) * k_f


def V_CEDGE(x):
    """The painted C-pillar's edge over the glass wedge."""
    return v_up(x, Z_CEDGE(min(X_CTIP, x)))


def V_WTOP(x):
    """The wedge's top edge, under the roof spoiler's side: from the tip up
    to the blade's outer end."""
    t = _clamp01((X_CTIP - x) / (X_CTIP - X_BLADE))
    return V_CEDGE(X_CTIP) + (S.v_at_y_upper(X_BLADE, Y_WTOP_BLADE) - V_CEDGE(X_CTIP)) * t


def V_Q_TOP(x):
    """Top of the rear quarter: the glass's lower edge to the tip, then the
    whole C-pillar up to the rail, rising to the wedge's tip, then the
    C-pillar's edge down to the tail."""
    if x >= X_DLO_TIP:
        return V_BELT(x)
    if x >= X_CTIP:
        s = _smooth((X_DLO_TIP - x) / (X_DLO_TIP - X_CTIP))
        return V_RAIL_TOP(x) + (V_CEDGE(X_CTIP) - V_RAIL_TOP(x)) * s
    return V_CEDGE(x)


def V_ROOF_LO(x):
    """The painted roof's lower edge: lapping the rail's top, then the
    C-pillar's (a butt - one painted surface), then over the wedge."""
    if x >= X_DLO_TIP:
        return V_RAIL(x) - 0.004
    if x >= X_CTIP:
        return V_Q_TOP(x) - 0.004 * (x - X_CTIP) / (X_DLO_TIP - X_CTIP)
    return V_WTOP(x)


def V_WEDGE_TOP(x):
    """The wedge glass's top: the spoiler's side, then on under the black
    band, then the rear pane's side edge (rx_rear, 14 mm inside the
    backlight's)."""
    if x >= X_BLADE:
        return V_WTOP(x)
    if x >= X_FRIT:
        return V_FRIT(x) + 0.004
    return S.v_along(x, V_REARGLASS(x), 0.014) - 0.001


# The clamshell hood: its side edges run along the fenders just inboard of
# the crowns, from the cowl to the headlamps (front 3/4 photographs).
def _hood_front(v):
    return N.JOIN_F(v) + 0.015 * geom.smoothstep((v - 0.93) / 0.06)


# (front_silver, solved camera: a shield - the full width between the
# windscreen's corners, drawing in along the domes' outer flanks to the
# lamps; y read off the photo, x from casting onto the model - re-cast
# after any change to the hood's height, the view grazes it)
Y_HOOD = Curve([(X_COWL, 0.835), (1.00, 0.815), (1.20, 0.790), (1.40, 0.762),
                (1.60, 0.736), (1.75, 0.712), (1.90, 0.672), (2.05, 0.617),
                (2.17, 0.555), (S.HALF_L, 0.420)])


def V_HOOD(x):
    return S.v_at_y_upper(x, Y_HOOD(x))


# B-pillar glass edges: upright (side photo: the black pillar at u 590-605)
GB_F = -0.300
GB_R = -0.395


# ------------------------------------------------------------- flank panels
PANELS = [
    dict(name="RX_Fender_Front", x=(X_DOOR_F, N.JOIN_F), v=(V_SILL, V_HOOD),
         nx=46, nv=40, arch=True, fender_vent=True, gap=dict(v0=False, x1=False),
         mat="paint"),
    dict(name="RX_Door_Front", x=(X_BPILLAR, X_DOOR_F), v=(V_SILL, V_BELT),
         nx=40, nv=40, arch=True, gap=dict(v0=False), mat="paint"),
    dict(name="RX_Door_Rear", x=(X_DOOR_R, X_BPILLAR), v=(V_SILL, V_BELT),
         nx=38, nv=40, arch=True, gap=dict(v0=False), mat="paint"),
    # One rear quarter from the tail to the rear door, including the whole
    # C-pillar up to the rail: one pressing, butted to the tail cap.
    dict(name="RX_Quarter", x=(N.JOIN_R, X_DOOR_R), v=(V_Q_LO, V_Q_TOP),
         nx=56, nv=48, arch=True, gap=dict(v0=False, x0=False), mat="paint",
         fixed_x=(X_DLO_TIP, X_CTIP)),
    # the gloss black lower bumper's side, behind the rear wheel
    dict(name="RX_Quarter_Low", x=(N.JOIN_R, X_BAND_F + 0.030), v=(V_BAND_LO, V_BAND_TOP),
         nx=16, nv=10, arch=True, gap=dict(x0=False, x1=False, v1=False),
         mat="black_gloss"),
    # 0.5 mm proud: it laps the nose cap's top edge instead of crossing it
    # (two triangulations of one surface z-fought along the seam), and near
    # the centreline runs 15 mm on over the cap, whose top rows converge on
    # its tip in slivers that speckled in reflections
    dict(name="RX_Hood", x=(X_COWL, _hood_front), v=(V_HOOD, 1.0),
         nx=60, nv=34, gap=dict(v1=False, x1=False), mat="paint", offset=0.0005),
    # Body-colour A-pillar and roof rail, butted to the quarter's C-pillar
    dict(name="RX_Roof_Rail", x=(X_DLO_TIP, X_COWL),
         v=(lambda x: V_GT(x) + 0.006, V_RAIL_TOP),
         nx=140, nv=10, gap=dict(x0=False), mat="paint"),

    # ---- greenhouse underlay: glass surround, B-pillar, under the roof glass
    dict(name="RX_Greenhouse_Black", x=(X_DLO_TIP - 0.030, X_COWL),
         v=(V_BELT, 1.0), nx=120, nv=50, gap=dict(v1=False), mat="black_gloss",
         offset=-0.003, thickness=0.0),
    # behind the C-pillar's edge down to the tail (under the wedge glass and
    # the edge's gap) and the whole top behind the side glass
    dict(name="RX_Roof_Rear_Black", x=(N.JOIN_R, X_DLO_TIP - 0.020),
         v=(lambda x: min(V_REARGLASS(x), V_CEDGE(x) - 0.006), 1.0), nx=48, nv=24,
         gap=dict(v1=False, x0=False), mat="black_gloss", offset=-0.003, thickness=0.0),

    # ---- glazing, on the skin, cut to the window outlines
    dict(name="RX_Glass_Windshield", x=(X_ROOF_F, X_COWL - 0.012),
         v=(lambda x: V_A(x) + 0.004, 0.9995), nx=72, nv=56, glass="glass",
         gap=dict(v1=False)),
    # the roof: body colour from the spoiler blade forward to the B-pillar,
    # one dark glass panel between the rails ahead of it
    dict(name="RX_Roof_Paint", x=(X_BLADE + 0.004, X_ROOF_GLASS_R),
         v=(V_ROOF_LO, 1.0), nx=64, nv=24, fixed_x=(X_CTIP,),
         gap=dict(v1=False, x0=False, v0=False), mat="paint"),
    dict(name="RX_Glass_Roof", x=(X_ROOF_GLASS_R + 0.006, X_ROOF_F - 0.020),
         v=(lambda x: V_RAIL(x) + 0.004, 0.9995), nx=48, nv=30, glass="glass_dark",
         gap=dict(v1=False)),
    # the glass wedge round the C-pillar, from the tail cap's join up to its
    # tip under the spoiler; the gap along its lower edge is the C-pillar's
    # crisp edge line
    dict(name="RX_Glass_Wedge", x=(lambda v: N.JOIN_R(v) + 0.002, X_CTIP),
         v=(V_CEDGE, V_WEDGE_TOP), nx=36, nv=10, glass="glass_dark", fixed_x=(X_BLADE,),
         gap=dict(x0=False, v1=False)),
    dict(name="RX_Glass_DoorFront", x=(GB_F, 0.660),
         v=(lambda x: V_BELT(x) + 0.010, lambda x: V_GT(x) - 0.004),
         nx=60, nv=28, glass="glass"),
    dict(name="RX_Glass_DoorRear", x=(X_DOOR_R_TOP + 0.020, GB_R),
         v=(lambda x: V_BELT(x) + 0.010, lambda x: V_GT(x) - 0.004),
         nx=46, nv=28, glass="glass_dark"),
    dict(name="RX_Glass_Quarter", x=(X_DLO_TIP + 0.012, X_DOOR_R_TOP - 0.012),
         v=(lambda x: V_BELT(x) + 0.008, lambda x: V_GT(x) - 0.004),
         nx=14, nv=10, glass="glass_dark"),
    # (the rear glass itself is one pane over the loft and the tail cap:
    # rx_rear.build_rear_glass)
    # the black band across the glass's top, from right under the blade's
    # edge (the side photograph's dark slot under the blade, u 829-870; the
    # low rear photo cannot see behind the lip) to v 295 of the rear photo;
    # the rear camera sits in it. Matte: in gloss black it mirrored the web
    # studio's ceiling and read as a grey band. 2.2 mm up, clear of the pane.
    dict(name="RX_Glass_Frit", x=(X_FRIT, X_BLADE - 0.004),
         v=(V_FRIT, 0.9995), nx=16, nv=40,
         mat="frit", offset=0.0022, thickness=0.0, gap=dict(v1=False)),
]


# ----------------------------------------------------------------- openings
def _cut_arches(ob):
    return C.cut_arches(ob, S.BODY, 0.35, 1.40)


# The fender vent ahead of the front door (side photo): a black blade from
# (0.99, 0.882) forward to (0.813, 0.883) along the top, its front edge
# raked down to a point at (0.872, 0.692).
VENT_OUTLINE = [(0.993, 0.884), (0.955, 0.790), (0.905, 0.715), (0.872, 0.692),
                (0.848, 0.720), (0.822, 0.800), (0.812, 0.884)]


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
def build_shadow_shell(collection, lib, name="RX_Shell_Shadow", skins=()):
    # sunk under the skin (the default 2.5 mm poked through the hood beside
    # its shut line, where the groove between dome and crown runs; 20 mm
    # still poked through the C-pillar's foot over the shoulder deck, x -2.1)
    ob = BP.shadow_shell(N.BODY, collection, lib, name, nx=140, nv=80, inset=0.030)
    if skins:
        clear_shell(ob, skins)
    return ob


def clear_shell(shell, skins, gap=0.015, core_z=0.70):
    """Pull the shell in to `gap` under the built skin, along rays from its
    core line. The shell is the loft shrunk about that line, and over the
    concave C-pillar foot its chords still cut through the skin at 30 mm: a
    black sliver 9 mm proud on the C-pillar (x -2.1, z 1.21-1.27). Vertices
    first, then any face whose centre still sits too close drags its corners
    in (a quad across the fold crossed the skin between clear corners)."""
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
    # inside the painted arch lip (0.93-0.97): the rear tyres stand out past
    # the paint, under the cladding
    return BP.wheel_liners(S.BODY, collection, lib, "RX_Liner_", y_outer=0.925,
                           mat="shadow", inner_wall=True, wall_z=0.25)   # above the floor


def build_underbody(collection, lib):
    return BP.underbody(S.BODY, collection, lib, "RX_Underbody", x0=-2.30, length=4.62)


def build_all(collection, lib):
    made = []
    made += build_panels(collection, lib)
    made.append(build_shadow_shell(collection, lib, skins=list(made)))
    made += build_wheel_liners(collection, lib)
    made.append(build_underbody(collection, lib))
    # the rear corners cut up under the black band: the mirror baked first so
    # both halves are cut, and the cutters' walls that the open-sheet EXACT
    # boolean keeps pruned (they hung below the band as a black flap)
    import bpy
    for nm in ("RX_Shell_Shadow", "RX_Shell_Shadow_R", "RX_Underbody", "RX_Liner_R"):
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            M.apply_modifiers(ob)
            sheet = C.sheet_bvh(ob)
            C.difference(ob, rear_corner_cutters(both=True, y0=Y_CORNER_HIDDEN), "corner_")
            C.prune_off_sheet(ob, sheet)
    return made
