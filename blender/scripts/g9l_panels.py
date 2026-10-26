"""XPeng G9L panel layout: shut lines, window lines, panels.

The machinery is carkit's (carkit.body.panels, carkit.cut); this module is the G9L's layout,
read off the camera-matched side photographs (g9l_ref_match, g9l_cam). The lines that run
up and down the flank are written in PIXELS of the white car's side photograph and turned into
model metres by g9l_cam at the plane they lie on, so the reading stays checkable.

    lines       door edges, belt, glass lines, hood side, spoiler, backlight edges
    PANELS      every flank panel as a region of (x, v)
    hidden      shadow shell, wheel liners, underbody tray

What the photographs show (c1_0028 white car, c1_0004 purple car):
  - three doors-worth of glass behind a raked black A-pillar frame: front door glass (pale),
    a B-pillar black band (x -0.03 .. -0.17), the rear door glass (x -0.17 .. -0.87), a narrow
    raked vent glass and an arched quarter window that tapers to a point at the belt (x -1.89)
  - the glass is one dark region under a thin black rail along the whole roofline; the sail
    above the quarter window is body colour; the roof's rear half is black glass, the front half
    paint; the spoiler overhangs the backlight
  - front door's leading edge x 1.10-1.14, the split at x 0.0, the rear door's edge x -1.20
"""
import math

import g9l_surface as S
import g9l_nose as N
import g9l_cam as CAM
from carkit import geom
from carkit.geom import Curve, clamp01 as _clamp01, smoothstep as _smooth, ramp as _ramp
from carkit import mesh as M
from carkit import cut as C
from carkit.body import panels as BP

GAP = BP.GAP
SKIN = M.SKIN


def _flank_pts(px, y0=0.93):
    """Photo pixels -> [(x, z)] on the built surface: the plane's y is the section's own at
    the point found (a few passes), not a guess."""
    out = []
    for (u, v) in px:
        y = y0
        for _ in range(4):
            x, z = CAM.side_xz(u, v, y)
            x = max(-S.HALF_L + 0.05, min(S.HALF_L - 0.05, x))
            vv = S.v_at_z(x, z, 0.0, 0.9995)
            y = S.section_v(x, vv)[0]
        out.append((x, z))
    return out


def _by_z(px, y0=0.93):
    return sorted((z, x) for (x, z) in _flank_pts(px, y0))


def _by_x(px, y0=0.93):
    return sorted(_flank_pts(px, y0))


# ----------------------------------------------------------------- stations
X_COWL = S.COWL_X            # 1.200: windscreen base
X_ROOF_F = 0.440             # windscreen header (the glass meets the roof)
X_KNEE = S.KNEE_X            # -1.970: the roof spoiler's trailing edge
X_TIP = -1.885               # the quarter glass's rear tip (side photo)
X_ROOF_GLASS_R = -0.480      # the roof is paint ahead of this, black glass behind it
X_VENT_R = -1.150            # the vent glass's rear edge at the belt


# ----------------------------------------------------------- door and body lines
_DOOR_F_EDGE = Curve(_by_z(CAM.DOOR_F_EDGE_PX, 0.97), mode="pchip")
_DOOR_SPLIT = Curve(_by_z(CAM.DOOR_SPLIT_PX, 0.97), mode="pchip")
_DOOR_R_EDGE = Curve(_by_z(CAM.DOOR_R_EDGE_PX, 0.97), mode="pchip")


def X_DOOR_F(v):
    return _DOOR_F_EDGE(S.section_v(1.12, v)[1])


def X_BPILLAR(v):
    return _DOOR_SPLIT(S.section_v(0.0, v)[1])


def X_DOOR_R(v):
    return _DOOR_R_EDGE(S.section_v(-1.2, v)[1])


# the flank panels' lower edge: the door's foot sits above the side step; ahead of the front arch
# and behind the rear one the bumpers' black lower parts take over
def Z_FLANK_LOW(x):
    """Ahead of the front arch the fender stops on the black bumper band at z 0.40; behind the rear
    arch the quarter's lower edge is the diagonal that runs from the arch's rear foot (z 0.29) up
    to the tail corner (z 0.585) - below it the bumper's black corner (c1_0028)."""
    if x >= 2.0:
        return 0.258 + 0.142 * _smooth((x - 2.0) / 0.12)
    if x <= -1.895:
        return min(0.60, 0.29 + 0.49 * (-1.895 - x))
    return 0.258


def V_SILL(x):
    return S.v_at_z(x, Z_FLANK_LOW(x), 0.0, S.V_SHOULDER)


def v_up(x, z):
    """Upper-section parameter whose height is z at station x."""
    return S.v_at_z(x, z, S.V_SHOULDER, 0.995)


# ------------------------------------------------------------ window lines
# the belt (lower edge of the side glass, top of the doors): 1.196 at the cowl rising to 1.353
BELT_Z = Curve(_by_x(CAM.BELT_PX, 0.97))


def V_BELT(x):
    return v_up(x, BELT_Z(max(-1.95, min(1.20, x))))


# the greenhouse's dark region: its upper boundary along the A-pillar's inner edge and the roof
DLO_Z = Curve(_by_x(CAM.DLO_TOP_PX, 0.86))


def V_DLO(x):
    """Upper edge of the side glass: the A-pillar's edge, the roof rail, the quarter glass's arch."""
    if x > X_COWL:
        return V_BELT(x)
    return v_up(x, max(BELT_Z(max(-1.95, x)) + 0.004, DLO_Z(max(X_TIP, x))))


def _rail_w(x):
    """Width of the body-colour rail beyond the side glass: 40 mm along the roof, widening into the
    95 mm A-pillar ahead of the header."""
    return 0.040 + 0.055 * _ramp(x, 0.40, 0.25)


def _wtop(x):
    """Width of the body-colour rail on the roof's top, inboard of the loft's rail line: 75 mm along the roof (the
    panoramic glass stands inside white rails), thinning to 20 mm at the spoiler where the glass runs on into the backlight."""
    return 0.020 + 0.055 * _ramp(x, -1.15, 1.6)


def _rail_old(x):
    """The rail's inboard edge as it was drawn from the glass line: DLO + a rail 40 mm wide (the A-pillar's, 95 mm, ahead of the header)."""
    return S.v_along(x, V_DLO(x), _rail_w(x))


def V_RAIL(x):
    """The rail's inboard edge: the A-pillar's, ahead of the header; behind it the line of the roof glass's outer edge, which
    is a distance in plan inboard of the roof's rail line (the photographs: a white rail ~7 cm wide on the roof, the glass
    wraps no further down the shoulder), blended from the A-pillar's edge over 0.3 m."""
    if x >= X_ROOF_F:
        return _rail_old(x)
    t = _smooth((X_ROOF_F - x) / 0.30)
    y_old = S.section_v(x, _rail_old(x))[0]
    y_new = S.Y_ROOF(x) - _wtop(x)
    return S.v_at_y_upper(x, y_old + (y_new - y_old) * t)


V_A = V_RAIL


# Backlight edges, from the rear photograph (c1_0030, read through its solved camera): the glass's side edges run from
# +/-0.535 under the spoiler (x -2.0) to +/-0.68 at the lamp strip's upper edge; the white sail beyond the edge is a thin
# sliver from behind (the greenhouse leans in at ~25 degrees). The edge IS the loft's roof rail there (g9l_surface.Y_ROOF
# follows it), and at the knee it meets the roof glass's edge (Y_ROOF - _wtop) exactly, so the two panes share one line.
Y_REARGLASS = Curve([
    (-2.52, 0.690), (-2.40, 0.655), (-2.20, 0.595), (-2.05, 0.545), (X_KNEE, 0.535),
])


def V_REARGLASS(x):
    if x >= X_KNEE:
        return V_RAIL(x)
    return S.v_at_y_upper(x, Y_REARGLASS(x))


# The backlight's foot. Its lower edge was the body's rear end (x -2.52), but the loft turns down there at the tail corners,
# so the glass ended in a pointed tab 14 cm below the foot line (z 1.185 at |y| 0.64 against 1.33 on the centreline), hanging
# over the lamp shelf as a black shard. The foot is the line z = Z_FOOT instead, and the sail's paint takes the corner below it.
Z_FOOT = 1.245


def _zfoot(y):
    """The foot's height at |y|: Z_FOOT across the middle, rising 10 cm toward the rail, so the glass's lower corner is a chamfer that
    ends above the lamp shelf's end instead of a pointed tab running down the corner (the close-up of the tail's upper corner:
    the viewer's reflections crumpled in it)."""
    return Z_FOOT + 0.100 * _smooth((abs(y) - 0.50) / 0.15)


def X_REARGLASS_FOOT(v):
    """x of the backlight's lower edge at v: where the body reaches the foot, no further back than -2.52."""
    lo, hi = -2.52, -2.10                   # (the chamfer moves the foot at the rail forward of x -2.30: the old limit clamped it into a zigzag)
    y, z = S.section_v(lo, v)
    if z >= _zfoot(y):
        return lo
    for _ in range(28):
        mid = 0.5 * (lo + hi)
        y, z = S.section_v(mid, v)
        if z < _zfoot(y):
            lo = mid
        else:
            hi = mid
    return hi


def V_SAIL_TOP(x):
    """The sail's upper edge: the backlight's side edge, or - behind the point where that edge falls below the foot - the foot line."""
    v0 = V_REARGLASS(x)
    y, z = S.section_v(x, v0)
    if x > -2.10 or z >= _zfoot(y):
        return v0
    lo, hi = v0, 1.0
    for _ in range(28):
        mid = 0.5 * (lo + hi)
        y, z = S.section_v(x, mid)
        if z < _zfoot(y):
            lo = mid
        else:
            hi = mid
    return hi


def V_QTOP(x):
    """Top of the quarter panel: the belt along the quarter glass, then up the C-pillar's sail to
    the backlight's edge."""
    if x >= X_TIP:
        return V_BELT(x)
    t = _smooth((X_TIP - x) / (X_TIP - (-2.20)))
    return V_BELT(x) + (V_REARGLASS(x) - V_BELT(x)) * t


def V_SAIL_LOW(x):
    """The sail's lower edge: the quarter panel's top (it butts, no shut line, so the sail is not drawn twice over the quarter),
    or - behind the quarter panel's end - the belt."""
    if x >= N.JOIN_R(0.8):
        return V_QTOP(x)
    # behind the quarter panel the sail's foot is the tail cap's top edge (z 1.268; 13 mm under it): the paint that fills the
    # wedge between the cap, the lamp shelf's end and the backlight's edge, running to a point at the corner
    return S.v_at_z(x, 1.255, S.V_SHOULDER, 1.0)


# glass divisions as x of the line at the height of v (raked lines)
_GF_REAR = Curve(_by_z(CAM.GLASS_F_REAR_PX, 0.88), mode="pchip")
_GR_FRONT = Curve(_by_z(CAM.GLASS_R_FRONT_PX, 0.88), mode="pchip")
_GR_REAR = Curve(_by_z(CAM.GLASS_R_REAR_PX, 0.88), mode="pchip")
_VENT_REAR = Curve(_by_z(CAM.VENT_REAR_PX, 0.88), mode="pchip")


def _x_of(curve, x_nom):
    return lambda v: curve(S.section_v(x_nom, v)[1])


X_GF_REAR = _x_of(_GF_REAR, 0.0)       # front door glass's rear edge
X_GR_FRONT = _x_of(_GR_FRONT, -0.15)   # rear door glass's front edge (the B-pillar's band between)
X_GR_REAR = _x_of(_GR_REAR, -0.87)     # rear door glass's rear edge
X_VENT_REAR = _x_of(_VENT_REAR, -1.1)  # the vent glass's rear edge (a raked line)


def _hood_front(v):
    return N.JOIN_F(v) + 0.012 * geom.smoothstep((v - 0.93) / 0.06)


# The hood's side edge runs along the fender crown from the cowl to the lamp bar's end
Z_HOODSIDE = Curve(_by_x(CAM.HOOD_SIDE_PX, 0.85))


def V_HOOD(x):
    if x >= 2.25:
        return v_up(x, Z_HOODSIDE(2.25))
    return v_up(x, Z_HOODSIDE(x))


# ------------------------------------------------------------- flank panels
PANELS = [
    # fender and doors
    dict(name="G9L_Fender_Front", x=(X_DOOR_F, N.JOIN_F), v=(V_SILL, V_HOOD),
         nx=44, nv=38, arch=True, gap=dict(v0=False, x1=False, v1=False), mat="paint"),
    dict(name="G9L_Door_Front", x=(X_BPILLAR, X_DOOR_F), v=(V_SILL, V_BELT),
         nx=40, nv=38, arch=True, gap=dict(v0=False), mat="paint"),
    dict(name="G9L_Door_Rear", x=(X_DOOR_R, X_BPILLAR), v=(V_SILL, V_BELT),
         nx=38, nv=38, arch=True, gap=dict(v0=False), mat="paint"),
    dict(name="G9L_Quarter", x=(N.JOIN_R, X_DOOR_R), v=(V_SILL, V_QTOP),
         nx=56, nv=40, arch=True, gap=dict(v0=False, x0=False, v1=False), mat="paint"),
    # the black corner of the rear bumper under the diagonal, from the arch's foot round to the tail
    dict(name="G9L_Bumper_Side", x=(N.JOIN_R, -1.870), v=(0.030, V_SILL),
         nx=24, nv=14, gap=dict(v0=False, x0=False, v1=False), mat="black_trim"),
    # hood flush to the cowl and the fender crown
    dict(name="G9L_Hood", x=(X_COWL, _hood_front), v=(V_HOOD, 1.0),
         nx=54, nv=32, gap=dict(v1=False, x1=False, x0=False, v0=False), mat="paint"),

    # A-pillar and roof rail: the body-colour strip between the glass and the roof
    dict(name="G9L_Roof_Rail", x=(X_TIP, X_COWL), v=(V_DLO, V_RAIL),
         nx=120, nv=12, gap=dict(x0=False, x1=False, v0=False, v1=False), mat="paint"),
    # painted roof between the rails: from the header back over the front seats
    dict(name="G9L_Roof_Paint", x=(X_ROOF_GLASS_R, X_ROOF_F), v=(V_RAIL, 1.0),
         nx=44, nv=22, gap=dict(v1=False, x0=False, x1=False, v0=False), mat="paint"),
    # painted sail behind the glass tip, round the C-pillar to the backlight's edge
    dict(name="G9L_Sail", x=(-2.52, X_TIP), v=(V_SAIL_LOW, V_SAIL_TOP),
         nx=48, nv=28, gap=dict(v0=False, x0=False, x1=False), mat="paint"),

    # ---- the dark region under the side glass (the black frames show where glass stops). Satin, not gloss: the viewer's clear glass takes
    # most of this sheet out and the slivers it leaves between the panes (the pillars, the belt) mirrored the white studio as thin chrome
    # lines across the greenhouse
    dict(name="G9L_Greenhouse_Black", x=(X_TIP, X_COWL), v=(V_BELT, V_DLO),
         nx=120, nv=28, gap=dict(v1=False, x0=False, v0=False), mat="black_trim",
         offset=-0.008, thickness=0.0),
    dict(name="G9L_Cowl_Black", x=(X_COWL - 0.035, X_COWL + 0.025),
         v=(V_HOOD, 1.0), nx=24, nv=28, gap=dict(v1=False), mat="black_trim",
         offset=-0.004, thickness=0.0),
    dict(name="G9L_Roof_Rear_Black", x=(-2.52, X_KNEE - 0.010),
         v=(V_REARGLASS, 1.0), nx=40, nv=24,
         gap=dict(v1=False, x0=False), mat="black_trim", offset=-0.018, thickness=0.0),

    # ---- glazing
    dict(name="G9L_Glass_Windshield", x=(X_ROOF_F - 0.012, X_COWL - 0.010),
         v=(lambda x: V_A(x) + 0.001, 0.9995), nx=64, nv=48, glass="glass", gap=dict(v1=False)),
    # the black roof glass behind the painted front half, to the spoiler
    dict(name="G9L_Glass_Roof", x=(X_KNEE + 0.012, X_ROOF_GLASS_R - 0.004),
         v=(lambda x: V_RAIL(x) + 0.004, 0.9995), nx=64, nv=28, glass="glass_dark",
         gap=dict(v1=False)),
    # side glass: front door (pale, raked to the A-pillar), the B-pillar band between, rear door,
    # the vent glass, the arched quarter window
    dict(name="G9L_Glass_DoorFront", x=(X_GF_REAR, 1.18),
         v=(lambda x: V_BELT(x) + 0.004, lambda x: V_DLO(x) - 0.004),
         nx=64, nv=26, glass="glass"),
    # the B-pillar: a black-glass band between the two door panes. The greenhouse underlay already runs behind it, but
    # the viewer's clear glass (src/components/viewer/clearGlass.ts) takes the underlay's TRIANGLES out within 5 cm of
    # a clear pane's vertices, so a pillar strip narrower than 10 cm was eaten into a sawtooth; this band is a part of
    # the body shell, which that pass leaves alone
    dict(name="G9L_BPillar_Black", x=(lambda v: X_GR_FRONT(v) - 0.004, lambda v: X_GF_REAR(v) + 0.004),
         v=(lambda x: V_BELT(x) + 0.004, lambda x: V_DLO(x) - 0.004),
         nx=8, nv=26, mat="black_gloss", offset=-0.001, thickness=0.0,
         gap=dict(x0=False, x1=False, v0=False, v1=False)),
    dict(name="G9L_Glass_DoorRear", x=(X_GR_REAR, X_GR_FRONT),
         v=(lambda x: V_BELT(x) + 0.004, lambda x: V_DLO(x) - 0.004),
         nx=44, nv=26, glass="glass_dark"),
    dict(name="G9L_Glass_Vent", x=(X_VENT_REAR, lambda v: X_GR_REAR(v) - 0.012),
         v=(lambda x: V_BELT(x) + 0.004, lambda x: V_DLO(x) - 0.004),
         nx=14, nv=26, glass="glass_dark"),
    dict(name="G9L_Glass_Quarter", x=(X_TIP + 0.002, lambda v: X_VENT_REAR(v) - 0.012),
         v=(lambda x: V_BELT(x) + 0.004, lambda x: V_DLO(x) - 0.004),
         nx=40, nv=24, glass="glass_dark"),
    # the wide backlight under the spoiler
    dict(name="G9L_Glass_Rear", x=(X_REARGLASS_FOOT, X_KNEE - 0.006),
         v=(V_REARGLASS, 0.9995), nx=44, nv=40, glass="glass_dark",
         gap=dict(v1=False, x0=False), offset=0.001),
]


# ----------------------------------------------------------------- openings
def _cut_arches(ob):
    return C.cut_arches(ob, S.BODY, 0.35, 1.40)


CUTTERS = {"arch": _cut_arches}


def build_panels(collection, lib):
    return BP.build_panels(PANELS, S.BODY, collection, lib, cutters=CUTTERS,
                           core_z=0.78, butt_bevel=False)


# ------------------------------------------------------------------ hidden
def build_shadow_shell(collection, lib, name="G9L_Shell_Shadow"):
    ob = BP.shadow_shell(N.BODY, collection, lib, name, nx=100, nv=48, inset=0.080, shrink=0.950)
    sf = bpy_obj(name + "_F")
    if sf is not None:
        import bpy
        bpy.data.objects.remove(sf, do_unlink=True)
    for v in ob.data.vertices:
        if v.co.x > 1.20 and v.co.z > 0.80:
            v.co.z = min(v.co.z, 0.80 - (v.co.x - 1.20) * 0.15)
    ob.data.update()
    return ob


def bpy_obj(name):
    import bpy
    return bpy.data.objects.get(name)


def build_wheel_liners(collection, lib):
    return BP.wheel_liners(S.BODY, collection, lib, "G9L_Liner_", y_outer=0.880,
                           mat="shadow", inner_wall=True, wall_z=0.25)


def build_underbody(collection, lib):
    return BP.underbody(S.BODY, collection, lib, "G9L_Underbody", x0=-2.30, length=4.60)


def build_all(collection, lib):
    made = []
    made += build_panels(collection, lib)
    made.append(build_shadow_shell(collection, lib))
    made += build_wheel_liners(collection, lib)
    made.append(build_underbody(collection, lib))
    return made


# names the cabin (g9l_interior*.py) reads
V_GT = V_DLO                 # top of the side glass
X_DLO_TIP = X_TIP            # the quarter glass's rear tip
GB_F = -0.030                # B-pillar's front glass edge (the front door glass's rear edge at the top)
GB_R = -0.150                # B-pillar's rear glass edge (the rear door glass's front edge)
