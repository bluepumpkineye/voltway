"""SU7 Ultra panel layout: shut lines, window lines, panels, openings, fascia.

The machinery is carkit's (carkit.body.panels, carkit.body.fascia,
carkit.cut); this module is the SU7's layout, all of it camera-matched against
the side photograph (ref_match.py):

    lines       door edges, cowl, B-pillar, screen and backlight headers,
                quarter light, beltline, hood shut line, fascia splits
    PANELS      every flank panel as a region of (x, v)
    openings    wheel arches, the quarter light and the rear vents - cut by
                exact booleans on the half sheets, before mirroring
    front       painted upper fascia, painted cheeks, the recessed black U
                with its intakes and tunnels, the yellow lower blade
    rear        painted tail cap with the trunk lid's shut line cut through it,
                the gloss black lower bumper, and the plate recess and corner
                pods cut through both, with dark tunnels
    hidden      shadow shell, wheel liners, underbody tray

Greenhouse: a black-gloss underlay covers the whole greenhouse 3 mm inside the
skin, and the glazing sits ON the skin cut to the real window outlines, so
wherever there is no glass you see gloss black - which is how the SU7 Ultra's
black roof and pillars read.
"""
import math

import su7_surface as S
import su7_nose as N
from carkit.geom import (Curve, clamp01 as _clamp01, smoothstep as _smooth,
                         ramp as _ramp, round_rect as _round_rect,
                         smooth_loop as _smooth_loop, vadd as _v3, vnorm as _norm,
                         vcross as _cross, radial, axial)
from carkit import mesh as M
from carkit import cut as C
from carkit.body import panels as BP
from carkit.body import fascia as FA

# ------------------------------------------------------------- shut lines
GAP = BP.GAP                 # 4.2 mm shut line
SKIN = M.SKIN                # panel sheet thickness
SHELL_INSET = BP.SHELL_INSET
SHELL_SHRINK = BP.SHELL_SHRINK

# Longitudinal split lines, camera-matched against the side photograph. The
# door edges are curves: the front door's leading edge bows forward at mid
# height, and the rear door's trailing edge sweeps forward 0.44 m round the
# rear wheel on its way down to the sill.
X_COWL = S.COWL_X            # 0.945, windscreen base / A-pillar foot
X_BPILLAR_F = -0.160         # front door | rear door, below the belt
X_BACKLIGHT = -1.905         # base of the backlight
X_ROOF_F = 0.270             # windscreen header
X_ROOF_R = -1.250            # backlight header
X_QTR_F = -1.065             # rear door frame / quarter light divider
X_QTR_R = -1.430             # quarter light, rear tip

V_BELT = S.V_SHOULDER + 0.028    # beltline / window seal
V_REARGLASS = 0.842              # backlight's side edge, and the decklid's

_DOOR_F_EDGE = Curve([          # x of the front door's leading edge, by height
    (0.200, 0.945), (0.267, 0.948), (0.379, 0.964), (0.507, 0.972),
    (0.635, 0.977), (0.763, 0.972), (0.850, 0.955), (0.917, 0.933),
    (1.050, 0.925),
], mode="pchip")
_DOOR_R_EDGE = Curve([          # x of the rear door's trailing edge, by height
    # Kept >= 45 mm clear of the wheel opening: traced straight off the photo
    # it touched the modelled arch at z 0.54-0.67 and the trim tore a black
    # slot down the shut line.
    (0.200, -0.780), (0.283, -0.813), (0.411, -0.945), (0.480, -0.995),
    (0.539, -1.036), (0.600, -1.075), (0.667, -1.135), (0.720, -1.190),
    (0.779, -1.225), (0.859, -1.251), (0.923, -1.245), (1.020, -1.175),
    (1.100, -1.160),
], mode="pchip")


def X_DOOR_F(v):
    return _DOOR_F_EDGE(S.section_v(0.96, v)[1])


def X_DOOR_R(v):
    return _DOOR_R_EDGE(S.section_v(-1.10, v)[1])


def V_SILL(x):
    """Section parameter of the floor edge - where the flank panels start."""
    return S.v_at_z(x, S.Z_FLOOR(x) + 0.030, 0.0, S.V_SHOULDER)


# Hood shut line, as a lateral position: just outboard of the fender crowns,
# as on the car's clamshell hood. As a fixed section parameter it put the
# shut line 0.41 m from the centreline once the hood came down - halfway
# across the hood.
Y_HOOD = Curve([
    (S.COWL_X, 0.745), (1.20, 0.798), (1.60, 0.808), (1.85, 0.810),
    (2.10, 0.775), (2.40, 0.700), (S.HALF_L, 0.650),
])


def V_HOOD(x):
    return S.v_at_y_upper(x, Y_HOOD(x))


def V_GT(x):
    """Top of the side glass: 100 mm below the roof rail's outer edge."""
    return S.v_along(x, S.v_rail(x), -0.100)


def V_RAIL(x):
    """Inboard edge of the body-colour rail, 50 mm onto the roof."""
    return S.v_along(x, S.v_rail(x), 0.050)


def V_A(x):
    """The A-pillar: from just above the belt at the cowl to the header."""
    t = (X_COWL - x) / (X_COWL - X_ROOF_F)
    top = V_GT(X_ROOF_F) + 0.020
    return (V_BELT + 0.022) + (top - V_BELT - 0.022) * _smooth(t)


# The quarter light is a wedge: its lower edge sweeps up ~100 mm off the belt
# to a rounded tip at (-1.43, 1.13), with body colour all round it.
_QTR_TIP = []


def V_QTR_TIP():
    if not _QTR_TIP:
        _QTR_TIP.append(S.v_at_z(X_QTR_R, 1.130, S.V_SHOULDER, 1.0))
    return _QTR_TIP[0]


def V_QTR_LOW(x):
    t = (X_QTR_F - x) / (X_QTR_F - X_QTR_R)
    return (V_BELT + 0.010) + (V_QTR_TIP() - V_BELT - 0.010) * (_clamp01(t) ** 1.6)


def V_C(x):
    """Top edge of the quarter light (+0.020), falling to the tip."""
    t = (X_QTR_F - x) / (X_QTR_F - X_QTR_R)
    hi = V_GT(X_QTR_F) + 0.020
    lo = V_QTR_TIP() + 0.020
    return hi - (hi - lo) * (_clamp01(t) ** 1.25)


def V_GLASS_TOP(x):
    """Top of whichever glass sits at station x."""
    if x < X_QTR_F:
        return V_C(x) - 0.020
    return min(V_A(x) - 0.020, V_GT(x))


def V_RAIL_TOP(x):
    """Inboard edge of the rail: the screen's edge down the A-pillar, 50 mm onto
    the roof over the glass roof, the backlight's edge down the C-pillar - with
    30 mm smoothstep ramps between them (a step shears the quads)."""
    a = V_A(x) + 0.016
    r = V_RAIL(x)
    c = V_REARGLASS - 0.004
    k_f = _ramp(x, X_ROOF_F)
    k_r = _ramp(x, X_ROOF_R)
    return c + (r - c) * k_r + (a - r) * k_f


def V_Q_TOP(x):
    """Top of the rear quarter: under the quarter light, then the whole sail."""
    if x >= X_QTR_R:
        return V_QTR_LOW(x) - 0.010
    return V_REARGLASS


def V_DOOR_R_TOP(x):
    """The rear door's top follows the quarter light's rising lower edge.

    Held at the belt it left a black wedge of underlay between the door and
    the window over the last 110 mm of the door.
    """
    return V_BELT + max(0.0, V_QTR_LOW(x) - V_BELT - 0.010)


# The B-pillar leans back: its glass edges are ~0.1 m further aft at the
# header than at the belt, and the pillar narrows from 147 to 98 mm.
def _glass_s(v):
    return _clamp01((v - V_BELT) / max(1e-4, (V_GT(-0.25) - V_BELT)))


def GB_F(v):
    return -0.150 + (-0.264 + 0.150) * _glass_s(v)


def GB_R(v):
    return -0.297 + (-0.362 + 0.297) * _glass_s(v)


# The black U starts right under the plate. Both sit ~65 mm lower than the
# first cut: in the front 3/4 photographs the headlamp's inboard tip is level
# with the top of the plate, and the lamp tip is at z ~0.60.
Z_FASCIA_SPLIT_F = 0.488
W_FENCE = 0.872              # cap w at the body-colour air-curtain fences
U_DEPTH = 0.030              # how far the black U sits behind the painted lip

# ------------------------------------------------------------------- rear
# Read off the three rear photographs (blender/reference/su7-ultra/rear) with
# the plate - 440 x 140 mm, spanning z 0.39-0.53 - as the ruler at the tail
# face, and the side photograph for anything on the flank. The three agree
# to ~10 mm on every height below.
#
# Trunk lid: 1.08 m wide at the tail, its edges crossing the corner lamps at
# y = +/-0.54, ending in a U-shaped shut line at z 0.68 with ~100 mm
# corners. It carries the light bar, the lamps' inner hooks, the wordmark
# above and both badges below. Above the lamps its edges run up over the tail
# to the decklid - the flank panel between the backlight's edges.
Y_LID = 0.540
Z_LID = 0.680
R_LID = 0.100
# Where the lid's edge reaches the cap/flank join, 0.45 m out: from there the
# decklid's side edge runs forward and in to the backlight's corner.
V_LID_END = 0.765


def V_LID_EDGE(x):
    """The decklid's side edge (and the quarter's top edge) along the deck:
    the backlight's edge line, widening over the last ~0.2 m to meet the
    lid's edge on the tail. Held at the backlight line, it met the tail at
    y 0.29 and the lid's edge had to cut 0.25 m across the corner of the
    deck to reach it."""
    x0, x1 = X_BACKLIGHT - 0.030, N.JOIN_R(V_LID_END)
    t = _clamp01((x0 - x) / (x0 - x1))
    return V_REARGLASS + (V_LID_END - V_REARGLASS) * _smooth(t)

# The gloss black lower bumper: level at z ~0.58 right across the tail - in
# the rear photographs its top edge reaches the corners at the same height as
# over the plate - then dropping round the corner onto the flank, where the
# side photograph has it at 0.54 (x -2.23), 0.44 (-2.19) and 0.34 (-2.125),
# carrying on to the wheel arch (su7_rear.build_rear_sill). It stands proud
# of the painted cap: a separate bumper, not a paint split.
Z_BLACK = Curve([(0.00, 0.580), (0.60, 0.578), (0.75, 0.572), (0.84, 0.560),
                 (0.88, 0.540), (0.92, 0.460), (0.96, 0.380), (1.00, 0.345)],
                mode="pchip")
BLACK_STAND = 0.010


def black_stand(w):
    """The black bumper's stand: 10 mm across the tail, easing to the 3 mm
    of the sill trim it runs into on the flank (su7_rear.build_rear_sill) -
    a full-height step there read as a black slab at the corner."""
    return BLACK_STAND - (BLACK_STAND - 0.003) * _smooth((w - 0.86) / 0.14)

# Openings in the black bumper, rear elevation (y, z), left half. The plate
# sits in a recess between the corner pods: big rounded ducts, square at the
# plate and rounding off toward the corner, each with a body-colour blade in
# it (su7_rear.build_pods).
PLATE_RECESS = _round_rect(0.0, 0.245, 0.355, 0.568, 0.020, open_inboard=True)
POD = _smooth_loop([
    (0.262, 0.300), (0.262, 0.495), (0.300, 0.512), (0.450, 0.514),
    (0.600, 0.508), (0.700, 0.492), (0.765, 0.458), (0.797, 0.405),
    (0.793, 0.345), (0.765, 0.305), (0.700, 0.288), (0.450, 0.285),
    (0.300, 0.286),
], samples=4)
POD_DEPTH = 0.075
PLATE_DEPTH = 0.055


# ---------------------------------------------------------------- outlines
INTAKE_MAIN = _round_rect(0.0, 0.375, 0.250, 0.462, 0.050, open_inboard=True)
INTAKE_CORNER = _smooth_loop([
    (0.440, 0.205), (0.560, 0.212), (0.680, 0.232), (0.770, 0.262),
    (0.770, 0.378), (0.680, 0.400), (0.560, 0.425), (0.440, 0.448),
], samples=5)


# ------------------------------------------------ helpers, old names kept
_mesh_from_rows = M.mesh_from_rows
_orient = M.orient
_finish = M.finish
_apply_modifiers = M.apply_modifiers
_strip = M.strip
_radial = radial(0.70)
_axial = axial


def _mirror(ob, clip=True):
    return M.mirror_y(ob, clip)


# ------------------------------------------------------------- flank panels
PANELS = [
    # ---- sheet metal
    dict(name="SU7Ultra_Fender_Front", x=(X_DOOR_F, N.JOIN_F), v=(V_SILL, V_HOOD),
         nx=50, nv=40, arch=True, gap=dict(v0=False), mat="paint"),
    dict(name="SU7Ultra_Door_Front", x=(X_BPILLAR_F, X_DOOR_F), v=(V_SILL, V_BELT),
         nx=40, nv=40, arch=True, gap=dict(v0=False), mat="paint"),
    dict(name="SU7Ultra_Door_Rear", x=(X_DOOR_R, X_BPILLAR_F), v=(V_SILL, V_DOOR_R_TOP),
         nx=38, nv=40, arch=True, gap=dict(v0=False), mat="paint"),
    # One rear quarter from the tail to the rear door, INCLUDING the C-pillar
    # sail and the body colour under the quarter light: on the car that is
    # one pressing with no line along the belt behind the window. It butts
    # the tail cap with no gap: the real rear corner has no shut line there,
    # only the lid's edge (su7_panels.lid_edge_path) and the lamps.
    dict(name="SU7Ultra_Quarter", x=(N.JOIN_R, X_DOOR_R), v=(V_SILL, V_LID_EDGE),
         nx=50, nv=44, arch=True, gap=dict(v0=False, x0=False), mat="paint",
         quarter_light=True, rear_vent=True),
    dict(name="SU7Ultra_Hood", x=(X_COWL, N.JOIN_F), v=(V_HOOD, 1.0),
         nx=60, nv=34, gap=dict(v1=False), mat="paint"),
    # the lid's deck: one pressing with the lid on the tail, no line across
    dict(name="SU7Ultra_Decklid", x=(N.JOIN_R, X_BACKLIGHT), v=(V_LID_EDGE, 1.0),
         nx=16, nv=30, gap=dict(v1=False, x0=False), mat="paint"),
    # Body-colour A-pillar and roof rail: on the SU7 Ultra only the glass and
    # the B-pillar are black. Butted (no gap) against the quarter's sail.
    dict(name="SU7Ultra_Roof_Rail", x=(X_QTR_R, X_COWL),
         v=(lambda x: V_GLASS_TOP(x) + 0.006, V_RAIL_TOP),
         nx=130, nv=10, gap=dict(x0=False), mat="paint"),

    # ---- greenhouse underlay: glass surround, B-pillar and glass roof
    dict(name="SU7Ultra_Greenhouse_Black", x=(X_QTR_R - 0.030, X_COWL),
         v=(V_BELT, 1.0), nx=110, nv=48, gap=dict(v1=False), mat="black_gloss",
         offset=-0.003, thickness=0.0),
    dict(name="SU7Ultra_Roof_Rear_Black", x=(X_BACKLIGHT, X_QTR_R),
         v=(V_REARGLASS, 1.0), nx=10, nv=12, gap=dict(v1=False),
         mat="black_gloss", offset=-0.003, thickness=0.0),

    # ---- glazing, on the skin, cut to the real window outlines
    dict(name="SU7Ultra_Glass_Windshield", x=(X_ROOF_F, X_COWL - 0.012),
         v=(lambda x: V_A(x) + 0.020, 0.9995), nx=72, nv=56, glass="glass",
         gap=dict(v1=False)),
    # front door glass is clear, like the windscreen: China requires >= 70 %
    # light transmission ahead of the B-pillar (GB 7258); privacy glass starts
    # at the rear doors
    dict(name="SU7Ultra_Glass_DoorFront", x=(GB_F, X_COWL - 0.030),
         v=(V_BELT + 0.010, lambda x: min(V_A(x) - 0.020, V_GT(x))),
         nx=60, nv=28, glass="glass"),
    dict(name="SU7Ultra_Glass_DoorRear", x=(X_QTR_F + 0.030, GB_R),
         v=(V_BELT + 0.010, V_GT), nx=50, nv=28, glass="glass_dark"),
    dict(name="SU7Ultra_Glass_Quarter", x=(X_QTR_R + 0.004, X_QTR_F),
         v=(V_QTR_LOW, lambda x: V_C(x) - 0.020), nx=24, nv=14,
         glass="glass_dark"),
    # The backlight runs from the deck up to a header at x = -1.25: a long
    # raked fastback glass, as on the car, instead of a short steep window.
    dict(name="SU7Ultra_Glass_Rear", x=(X_BACKLIGHT + 0.018, X_ROOF_R),
         v=(V_REARGLASS + 0.012, 0.9995), nx=56, nv=44, glass="glass_dark",
         gap=dict(v1=False)),
]


# ----------------------------------------------------------------- openings
ARCH_OPEN = C.ARCH_OPEN      # half a shut line outside the modelled arch


def _cut_arches(ob):
    """Boolean the wheel openings through a flank half-sheet (before mirror)."""
    return C.cut_arches(ob, S.BODY, 0.35, 1.40, ARCH_OPEN)


def _quarter_light_outline():
    """Side-elevation region the quarter panel must NOT cover: everything
    above the quarter light's lower edge (less its seal), forward of the tip.
    Cut, not trimmed: the panel's top edge jumps 0.2 in v at the tip."""
    pts = []
    n = 40
    x_front = X_QTR_F + 0.080
    for i in range(n + 1):
        x = X_QTR_R + (x_front - X_QTR_R) * i / float(n)
        v = max(V_BELT, V_QTR_LOW(min(x, X_QTR_F)) - 0.010)
        pts.append((x, S.section_v(x, v)[1]))
    pts += [(x_front, 1.80), (X_QTR_R, 1.80)]
    return pts


def _cut_quarter_light(ob):
    c = C.prism_y("_qlight_" + ob.name, _quarter_light_outline(), 0.30, 1.40)
    sheet = C.sheet_bvh(ob)
    C.difference(ob, [c], "qlight_", reset_materials=True)
    # The panel is an open sheet, so the exact solver also keeps the prism's
    # lower wall: a painted shelf from the skin in to y 0.30, invisible from
    # outside but a big paint sheet from the rear seats.
    C.prune_off_sheet(ob, sheet)


# A vent through each rear corner: a teardrop triangle, its long outer edge
# the slanted line the side photograph shows from (-2.080, 0.436) up to
# (-2.146, 0.664), its broad rounded top turning 90 mm round the corner toward
# the tail face (the side photograph sees it nearly edge-on; from behind it
# is a bold black triangle), pointing down at the wheel. The first cut was a parallel slot
# 45 mm wide. CUT through every panel it crosses (quarter, tail cap), so the
# dark shell shows through; patches laid on the surface read as black flaps.
def rear_vent_frame():
    """(E0, E1, d, w, hw): outer edge ends (bottom tip, top), outward normal,
    width direction (toward the tail face) and a nominal half-width."""
    def flank(x, z):
        v = S.v_at_z(x, z, 0.0, S.V_SHOULDER)
        y, zz = S.section_v(x, v)
        return (x, y, zz), S.surface_normal(x, v)
    E0, n0 = flank(-2.080, 0.436)
    E1, n1 = flank(-2.146, 0.664)
    d = _norm(_v3(n0, n1))
    a = _v3(E1, E0, -1.0)
    w = _norm(_cross(d, a))
    if w[0] > 0.0:
        w = tuple(-c for c in w)
    return E0, E1, d, w, (lambda t: 0.031 * t)


def _fillet(poly, radii, n=6):
    """A closed 2D polygon with each corner rounded (quadratic Bezier)."""
    import math
    out = []
    m = len(poly)
    for i in range(m):
        p0, p1, p2 = poly[i - 1], poly[i], poly[(i + 1) % m]
        l0 = math.hypot(p0[0] - p1[0], p0[1] - p1[1])
        l2 = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        t = min(radii[i], 0.45 * l0, 0.45 * l2)
        a = (p1[0] + (p0[0] - p1[0]) * t / l0, p1[1] + (p0[1] - p1[1]) * t / l0)
        b = (p1[0] + (p2[0] - p1[0]) * t / l2, p1[1] + (p2[1] - p1[1]) * t / l2)
        for k in range(n + 1):
            s = k / float(n)
            out.append(((1 - s) ** 2 * a[0] + 2 * s * (1 - s) * p1[0] + s * s * b[0],
                        (1 - s) ** 2 * a[1] + 2 * s * (1 - s) * p1[1] + s * s * b[1]))
    return out


def rear_vent_outline(n=6):
    """Closed teardrop outline, in the plane of the vent's outer edge."""
    E0, E1, d, w, hw = rear_vent_frame()
    a = _v3(E1, E0, -1.0)
    L = sum(c * c for c in a) ** 0.5
    au = tuple(c / L for c in a)
    # (along the outer edge from the bottom tip, toward the tail face)
    tri = [(0.0, 0.0), (L, 0.0), (L - 0.052, 0.090)]
    loop2 = _fillet(tri, (0.006, 0.022, 0.020), n)
    return [_v3(_v3(E0, au, s), w, q) for (s, q) in loop2], d


def _cut_rear_vent(ob):
    loop, d = rear_vent_outline()
    c = C.prism_dir("_rvent_" + ob.name, loop, d)
    C.difference(ob, [c], "rvent_", reset_materials=True)


CUTTERS = {"arch": _cut_arches, "quarter_light": _cut_quarter_light,
           "rear_vent": _cut_rear_vent}


def build_panels(collection, lib):
    return BP.build_panels(PANELS, S.BODY, collection, lib, cutters=CUTTERS,
                           core_z=0.70)


# ----------------------------------------------------------------- end caps
def cap_rows(front, z_lo, z_hi, w_lo, w_hi, nz, nw, offset=0.0,
             top_to_centre=False):
    """Grid over part of a cap. v chosen so heights are even across the face."""
    return BP.cap_rows(N.NOSE if front else N.TAIL, z_lo, z_hi, w_lo, w_hi, nz, nw,
                       offset=offset, top_to_centre=top_to_centre)


def build_front(collection, lib):
    """Painted upper fascia, painted cheeks, recessed black U, walls, intakes."""
    made = []
    zl = N.NOSE_Z_LO
    up, ch, u, vs_lo = FA.split_nose(
        "SU7Ultra_Fascia", N.NOSE, collection, lib, Z_FASCIA_SPLIT_F, W_FENCE,
        U_DEPTH, intakes=(INTAKE_MAIN, INTAKE_CORNER), x_cut=(2.95, 1.70))
    made += [up, ch, u]

    # Yellow lower blade: a painted lip standing proud of the black U under
    # each corner intake, from a point below the intake's inner end, rising
    # to meet the cheek - the "smile" the front 3/4 photographs show.
    w0, w1 = 0.46, W_FENCE

    def blade_top(w):
        t = _smooth((w - w0) / (w1 - w0))
        return zl + 0.016 + 0.110 * t
    made += FA.blade("SU7Ultra_Fascia_Blade", N.NOSE, collection, lib, w0, w1,
                     blade_top, nw=24, nz=6, recess=U_DEPTH)

    # return walls: under the painted lip, and the inner face of each fence
    made += FA.mouth_walls("SU7Ultra_Fascia", N.NOSE, collection, lib,
                           Z_FASCIA_SPLIT_F, W_FENCE, U_DEPTH, vs_lo)

    # tunnels behind the intakes, in unlit black: a satin wall catches the key
    # light and the mouth reads as a flat panel instead of an opening
    x_u = FA.recessed_x(N.NOSE, U_DEPTH)
    for nm, outline, depth in (("Main", INTAKE_MAIN, 0.115),
                               ("Corner", INTAKE_CORNER, 0.125)):
        r = FA.intake_tunnel("SU7Ultra_Intake_%s_Tunnel" % nm, outline, collection,
                             lib["shadow"], cap=N.NOSE, x_surface=x_u, depth=depth,
                             taper=0.95)
        _mirror(r)
        made.append(r)
    return made


def lid_edge_path():
    """The trunk lid's shut line on the tail cap, left half, as (points,
    normals): across under the badges at Z_LID from just past the centreline,
    round a R_LID corner, up the lid's side at Y_LID behind the corner lamp,
    then over the tail's top edge and forward to the join, where the decklid's
    side edge (V_LID_EDGE) carries it on to the backlight."""
    T = N.TAIL
    pts, nrm = [], []

    def face(y, z):
        w, v = T.wv_at(abs(y), z)
        p, n = T.point(w, v), T.normal(w, v)
        if y < 0.0:
            p, n = (p[0], -p[1], p[2]), (n[0], -n[1], n[2])
        pts.append(p)
        nrm.append(n)

    y_c, z_c = Y_LID - R_LID, Z_LID + R_LID
    for i in range(15):
        face(-0.02 + (y_c + 0.02) * i / 15.0, Z_LID)
    for i in range(11):
        a = math.radians(-90.0 + 90.0 * i / 10.0)
        face(y_c + R_LID * math.cos(a), z_c + R_LID * math.sin(a))
    z_top = 0.930
    for i in range(1, 8):
        face(Y_LID, z_c + (z_top - z_c) * i / 7.0)
    w_a, v_a = T.wv_at(Y_LID, z_top)
    v_j = V_LID_END
    y_j = S.section_v(N.JOIN_R(v_j), v_j)[0]
    for i in range(1, 25):
        s = i / 24.0
        v = v_a + (v_j - v_a) * s
        yj = S.section_v(N.JOIN_R(v), v)[0]
        y = Y_LID + (y_j - Y_LID) * s * s
        w = 1.0 if i == 24 else min(1.0, y / yj)
        pts.append(T.point(w, v))
        nrm.append(T.normal(w, v))
    return pts, nrm


def _cut_lid(ob):
    path, nrm = lid_edge_path()
    c = C.slot("_lid_" + ob.name, path, nrm, GAP, out=0.03, inside=0.03)
    C.difference(ob, [c], "lid_", reset_materials=True)


def _cut_openings(ob):
    """Plate recess and corner pods through a half sheet of the tail."""
    cs = [C.prism_x("_open_%s_%d" % (ob.name, k), o, -2.62, -2.05)
          for k, o in enumerate((PLATE_RECESS, POD))]
    C.difference(ob, cs, "open_", reset_materials=True)


def build_rear(collection, lib):
    """Tail cap: the painted lid and quarters above a gloss black lower bumper.

    The lid's shut line is a real 4.2 mm gap cut through the painted sheet
    (lid_edge_path), over the dark shell, like every other panel gap. The
    black bumper stands BLACK_STAND proud with a return wall along its top
    edge (Z_BLACK), so it reads as the separate bumper it is; the painted cap
    runs down behind it. Both are cut through by the plate recess and the
    corner pods, which get dark tunnels, and the painted cap by the vents.
    """
    zh = N.TAIL_Z_HI
    # cap_panel spaces its rows by height at the CENTRELINE and keeps those
    # v rows across the car. The tail's v rises toward the corners, so a
    # bottom row at z 0.35 in the middle sat at 0.43 at the join. That was
    # above the bumper's dropping top edge (0.345 there), and a black hole
    # opened under each vent. At 0.25 the row is at 0.33 in the corners,
    # tucked behind the bumper everywhere.
    made = [FA.cap_panel("SU7Ultra_Tail_Upper", N.TAIL, collection, lib, 0.250,
                         zh - 0.0008, 0.0, 1.0, 40, 44, mat="paint",
                         top_to_centre=True,
                         cuts=(_cut_rear_vent, _cut_lid, _cut_openings))]
    made += FA.valance("SU7Ultra_Tail_Valance", N.TAIL, collection, lib, Z_BLACK,
                       stand=black_stand, nw=44, nz=26, mat="black_gloss",
                       thickness=0.0030, cuts=(_cut_openings,))
    on_bumper = FA.recessed_x(N.TAIL, lambda w: -black_stand(w))
    for nm, outline, depth in (("Plate", PLATE_RECESS, PLATE_DEPTH),
                               ("Pod", POD, POD_DEPTH)):
        t = FA.intake_tunnel("SU7Ultra_Rear%s_Tunnel" % nm, outline, collection,
                             lib["shadow"], cap=N.TAIL, x_surface=on_bumper,
                             depth=depth, taper=0.97)
        _mirror(t)
        made.append(t)
    return made


# ------------------------------------------------------------------ hidden
def build_shadow_shell(collection, lib, name="SU7Ultra_Shell_Shadow"):
    # 100 stations, not 140: it is only ever seen, dark, through gaps, and the
    # 10k triangles pay for the rear's lettering and lamps
    return BP.shadow_shell(N.BODY, collection, lib, name, nx=100)


def build_wheel_liners(collection, lib):
    return BP.wheel_liners(S.BODY, collection, lib, "SU7Ultra_Liner_")


def build_underbody(collection, lib):
    return BP.underbody(S.BODY, collection, lib, "SU7Ultra_Underbody")


tri_count = M.tri_count


def build_all(collection, lib):
    made = []
    made += build_panels(collection, lib)
    made += build_front(collection, lib)
    made += build_rear(collection, lib)
    made.append(build_shadow_shell(collection, lib))
    made += build_wheel_liners(collection, lib)
    made.append(build_underbody(collection, lib))
    return made
