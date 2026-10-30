"""Avatr 06T rear end: tailgate, star-ring light bar, rear glass, roof spoiler,
wiper, lower bumper / diffuser, plate recess, badges.

Read off the Autohome turnaround photographs (c1_0005..0007.jpg) and the
official rear render (design-list_03.jpg); every position is a rear-elevation
(y, z) on the tail cap (left half), dropped onto the finished surface at build
time.

    tail cap      painted, from under the black bumper's top edge to the
                  ducktail; the tailgate's shut line cut through it: upright
                  at y +/-0.60, rounding into a lower edge at z 0.70 on the
                  centreline (the hatch carries the lamp band and the glass)
    light bar     dual-line "star ring" lamps z 0.90-0.95, y 0.10-0.80 each
                  side, joined by a gloss-black band across the tailgate
    rear glass    one raked pane from under the roof spoiler down over the
                  tail cap to the ducktail lip (foot z ~1.00), black backing
    roof spoiler  deep body-colour blade at the roof's end, camera in the
                  black frit band under it, wiper at the glass's base
    bumper        gloss black from z 0.52 down, a gunmetal diffuser pod each
                  side under a wide red reflector, a silver blade at z 0.28
    plate recess  y +/-0.30, z 0.545-0.665, painted
    badges        Avatr prism on the centreline, '阿维塔' left, '06T' right
"""
import math
import os

import bpy

import a06t_surface as S
import a06t_nose as N
import a06t_panels as PN
from carkit import geom
from carkit.geom import Curve
from carkit import mesh as M
from carkit import cut as C
from carkit import place as P
from carkit.body import fascia as FA
from carkit.body import panels as BP
from carkit.parts import fittings, lamps

BODY = N.BODY
TAIL = N.TAIL
FONT_DIR = os.path.join(os.path.dirname(bpy.app.binary_path), "%d.%d" % bpy.app.version[:2],
                        "datafiles", "fonts")

# --------------------------------------------------------------- hardpoints
GATE_Y = 0.591
# the tailgate's side edge runs straight down at y 0.591 to z 0.83, then rounds into the lower edge
# (z 0.66) with a ~0.15 m radius (c1_0006)
GATE_EDGE = [(0.000, 0.660), (0.250, 0.660), (0.380, 0.662), (0.450, 0.667), (0.507, 0.692),
             (0.550, 0.727), (0.578, 0.771), (GATE_Y, 0.830), (GATE_Y, 0.930), (GATE_Y, 1.020)]
# on up past the cap's top (rear view); points the rays miss are skipped
# (sampled every 8 mm over the cap's top edge: after the 2026-10-28 refit the cap ends lower at y 0.591, the next ray
# lands on the glass slope 16 cm forward, and a 4 cm step left the slot's tube straight through the air above the
# sheet, an uncut bridge: the hatch's skin stayed one piece with the body)
GATE_TOP = tuple(1.028 + 0.008 * i for i in range(13)) + (1.140, 1.180, 1.220)

# The tail lamp is one thin black bar across the whole tailgate (c1_0006: z 0.93..0.987 at the
  # centre), its outer ends wrapping the corners and tapering to a point at y 0.85; lit it is a single
  # thin red line (design-list_03)
#
# 2026-10-28: the horn runs on along the flank to a point ~0.19 m further forward (c1_0004: the lamp's black wedge reaches
# x -1.91 at the quarter; it ended at -2.10). In the rear view that is only 4 cm more of y (the flank at z 0.91 is 0.855
# wide at x -2.10 and 0.89 at x -1.93), so the extra points are close together in y and spread over 17 cm of x.
LAMP_UPPER = [(0.000, 0.982), (0.300, 0.982), (0.560, 0.980), (0.650, 0.976), (0.736, 0.968),
              (0.790, 0.955), (0.830, 0.932), (0.858, 0.925), (0.874, 0.919), (0.884, 0.913),
              (0.890, 0.909)]
LAMP_LOWER = [(0.000, 0.937), (0.300, 0.937), (0.560, 0.938), (0.650, 0.936), (0.736, 0.930),
              (0.790, 0.921), (0.830, 0.912), (0.858, 0.911), (0.874, 0.910), (0.884, 0.9095),
              (0.890, 0.909)]
LAMP_TIP = LAMP_UPPER[-1][0]
LAMP_START = 0.0
LAMP_GAP = 0.006
LAMP_NS = (30, 26)             # stations: gate unit, outer unit
BAND_Z = (0.931, 0.985)        # the gloss-black band behind the lamps

# the glass's lower edge: flat at z 1.093 across, rounding up into the sides (c1_0006)
GLASS_LOW = [(0.552, 1.160), (0.545, 1.128), (0.530, 1.108), (0.500, 1.098),
             (0.450, 1.094), (0.350, 1.093), (0.180, 1.093), (0.000, 1.093)]
Z_BLACK = 0.620                # top of the gloss black bumper (0.58 at the corners)
# the plate's black surround: a hexagon, pointed at the sides (c1_0006: y +-0.325, z 0.706..0.887)
PLATE_RECESS = [(-0.02, 0.706), (0.150, 0.706), (0.245, 0.712), (0.300, 0.745), (0.325, 0.796),
                (0.300, 0.848), (0.245, 0.882), (0.150, 0.887), (-0.02, 0.887)]
PLATE_DEPTH = 0.0070
REFLECTOR = (0.270, 0.620, 0.507, 0.521)     # the red reflective strips each side (c1_0006)


# ----------------------------------------------------------------- helpers
def on_tail(y, z, d=0.0):
    w, v = TAIL.wv_at(abs(y), z)
    p, n = TAIL.point(w, v), TAIL.normal(w, v)
    p = (p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d)
    if y < 0.0:
        p, n = (p[0], -p[1], p[2]), (n[0], -n[1], n[2])
    return p, n


class _RearView:
    """What the rear photo sees at (y, z): a ray along +x from behind to the
    first surface of the tail cap as built (before any cut) or the flank
    beside it. on_tail's (w, v) chart fails at the corners; a ray cannot."""

    def __init__(self):
        from mathutils.bvhtree import BVHTree
        rows, _ = BP.cap_rows(TAIL, TAIL.Z_LO + 0.02, TAIL.Z_HI - 0.0008, 0.0, 1.0,
                              120, 90, top_to_centre=True)
        verts, faces = [], []
        nv = len(rows[0])
        for r in rows:
            verts.extend(r)
        for i in range(len(rows) - 1):
            a, b = i * nv, (i + 1) * nv
            faces += [[a + j, a + j + 1, b + j + 1, b + j] for j in range(nv - 1)]
        base = len(verts)
        vs = [0.25 + 0.55 * k / 60.0 for k in range(61)]
        for i in range(61):
            t = i / 60.0
            verts.extend(S.surface(N.JOIN_R(v) + (-1.75 - N.JOIN_R(v)) * t, v) for v in vs)
        for i in range(60):
            a, b = base + i * 61, base + (i + 1) * 61
            faces += [[a + j, a + j + 1, b + j + 1, b + j] for j in range(60)]
        self.tree = BVHTree.FromPolygons(verts, faces)

    def hit(self, y, z):
        from mathutils import Vector
        loc, nrm, _i, _d = self.tree.ray_cast(Vector((-3.6, abs(y), z)), Vector((1.0, 0.0, 0.0)), 3.0)
        if loc is None:
            return None
        n = nrm.normalized()
        if n.x > 0.0:
            n = -n
        p, n = tuple(loc), tuple(n)
        if y < 0.0:
            p, n = (p[0], -p[1], p[2]), (n[0], -n[1], n[2])
        return p, n

    def x(self, y, z):
        h = self.hit(y, z)
        if h is None:
            raise RuntimeError("rear view: nothing at (y %.3f, z %.3f)" % (y, z))
        return h[0][0]


_REAR = None


def rear_view():
    global _REAR
    if _REAR is None:
        _REAR = _RearView()
    return _REAR


def on_rear(y, z, d=0.0):
    h = rear_view().hit(y, z)
    if h is None:
        raise RuntimeError("rear view: nothing at (y %.3f, z %.3f)" % (y, z))
    p, n = h
    return (p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d), n


def _font(fn):
    try:
        return bpy.data.fonts.load(os.path.join(FONT_DIR, fn), check_existing=True)
    except Exception as e:
        if "CJK" in fn:
            for sys_font in ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/simsun.ttc"):
                if os.path.exists(sys_font):
                    try:
                        return bpy.data.fonts.load(sys_font, check_existing=True)
                    except Exception:
                        pass
        print("font %s not loaded (%s) - using Blender's default" % (fn, e))
        return None


# ---------------------------------------------------------------- tailgate
def gate_path():
    pts, nrm = [], []
    ring = geom.polyline([(0.0, y, z) for (y, z) in [(-0.02, 0.700)] + GATE_EDGE], 70)
    for (_x, y, z) in ring:
        p, n = on_tail(y, z)
        pts.append(p)
        nrm.append(n)
    for z in GATE_TOP:
        try:
            p, n = on_rear(GATE_Y, z)
        except RuntimeError:
            break
        pts.append(p)
        nrm.append(n)
    return pts, nrm


def _cut_gate(ob):
    pts, nrm = gate_path()
    c = C.slot("_gate_" + ob.name, pts, nrm, PN.GAP, out=0.03, inside=0.03)
    C.difference(ob, [c], "gate_", reset_materials=True)


def _cut_recess(ob):
    L = S.HALF_L
    c = C.prism_x("_recess_" + ob.name, PLATE_RECESS, -L - 0.30, -L + 0.40)
    sheet = C.sheet_bvh(ob)
    C.difference(ob, [c], "recess_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


def _cut_corner(ob):
    sheet = C.sheet_bvh(ob)
    C.difference(ob, PN.rear_corner_cutters(), "corner_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


# The diffuser (c1_0006 / c1_0007 / design-list_03): under the dull red reflector strips the black bumper carries a
# dark satin insert whose top edge is a shallow W (low at the centre, up under the reflectors, down to the corner);
# below it a gunmetal lip with a thin chrome blade along its upper edge that sweeps up round the corner; vertical
# fins in the insert's lower half. It used to be a pocket cut through the valance with a dish behind it: a
# faceted hole, a bright slanted wall and chrome shards poking out of the corner (2026-10-28 rebuild: nothing is
# cut, the insert and the fins stand a few mm proud of the unbroken gloss bumper).
DIFF_TOP = [(0.000, 0.447), (0.060, 0.452), (0.124, 0.463), (0.206, 0.494), (0.266, 0.512),
            (0.340, 0.516), (0.434, 0.516), (0.537, 0.509), (0.608, 0.487), (0.650, 0.430),
            (0.690, 0.372), (0.715, 0.335)]
DIFF_Z_LO = 0.300
DIFF_Y_END = 0.715
FIN_Y = [0.075 + 0.0905 * k for k in range(7)]       # 7 fins a side, y 0.075 .. 0.618
FIN_W, FIN_Z = 0.0065, (0.312, 0.370)
LIP_Y_END = 0.745


def _smooth01(t):
    return geom.smoothstep(min(1.0, max(0.0, t)))


def black_stand(w):
    return 0.008 - 0.005 * geom.smoothstep((w - 0.85) / 0.15)


def build_tail(collection, lib):
    made = []
    # 76 x 56 grid (was 44 x 44): the corner roll is tighter than it was, and a06t_gate._gate_faces keeps only the skin
    # within 2 mm of the dense rear_view surface; the 44-column chords sagged more than that round the corner,
    # the corner faces were dropped and the shut line "did not separate the hatch's skin"
    made.append(FA.cap_panel("A06T_Tail_Upper", TAIL, collection, lib, Z_BLACK - 0.060,
                             N.TAIL_Z_HI - 0.0008, 0.0, 1.0, 76, 56, mat="paint",
                             top_to_centre=True, cuts=(_cut_gate, _cut_recess, _cut_pane)))
    made += FA.valance("A06T_Tail_Valance", TAIL, collection, lib,
                       lambda w: Z_BLACK - 0.045 * geom.smoothstep(w),
                       stand=black_stand, nw=44, nz=26, mat="black_trim",
                       thickness=0.0030, cuts=(_cut_corner,))
    x_face = FA.recessed_x(TAIL, 0.0)
    made.append(_pocket("A06T_Rear_PlateRecess", PLATE_RECESS, PLATE_DEPTH, collection,
                        lib["black_gloss"], x_face))
    p, n = on_rear(0.0, 0.796, 0.002)
    made += fittings.plate("A06T_Plate_Rear", p, n, collection, lib, w=0.440, h=0.140,
                           texts=[("AVATR 06T", 0.0, 0.038, False, True)],
                           mat="black_gloss", text_mat="machined")
    return made


def _pocket(name, outline, depth, collection, mat, x_face, walls=True):
    rows = []
    ring = [(y, z) for (y, z) in outline if y >= 0.0]
    cy = sum(p[0] for p in ring) / len(ring)
    cz = sum(p[1] for p in ring) / len(ring)
    for k in (1.0, 0.66, 0.33, 0.0):
        row = []
        for (y, z) in ring:
            yy, zz = cy + (y - cy) * k, cz + (z - cz) * k
            w, v = TAIL.wv_at(max(0.0, yy), zz)
            row.append(TAIL.offset(w, v, -depth))
        rows.append(row)
    cols = [[rows[r][i] for r in range(len(rows))] for i in range(len(ring))]
    ob = M.mesh_from_rows(name, cols, collection)
    M.orient(ob.data, geom.axial(-1.0))
    ob.data.materials.append(mat)
    if walls and depth > 0:
        a, b = [], []
        for (y, z) in ring:
            w, v = TAIL.wv_at(max(0.0, y), z)
            a.append(TAIL.point(w, v))
            b.append(TAIL.offset(w, v, -depth))
        wl = M.strip(name + "_Wall", a, b, collection, mat)
        M.mirror_y(wl)
    M.mirror_y(ob)
    return ob


# ---------------------------------------------------------------- the lamps
def lamp_place(p, d):
    return on_rear(p[1], p[2], d)


def _lamp_edges(y0, y1, n):
    lo_c = Curve(LAMP_LOWER, mode="pchip")
    up_c = Curve(LAMP_UPPER, mode="pchip")
    ys = [y0 + (y1 - y0) * (1.0 - (1.0 - k / float(n - 1)) ** 1.6
                            if y1 >= LAMP_TIP else k / float(n - 1)) for k in range(n)]
    lo = [on_rear(y, lo_c(y))[0] for y in ys]
    up = [on_rear(y, up_c(y))[0] for y in ys]
    return lo, up


def build_lightbar(collection, lib):
    """One thin black lamp bar across the tailgate with a single red line lit along it."""
    made = []
    out = geom.away_from((-2.10, 0.30, 0.93))
    crown = (lambda k, n: 0.0032 + 0.0010 * math.sin(math.pi * k / n))
    pipe = (lambda k: 0.0042)
    red = lib["led_red_tail"]
    g = 0.5 * LAMP_GAP
    for tag, (y0, y1), n in (("", (LAMP_START, GATE_Y - g), LAMP_NS[0]),
                             ("Out", (GATE_Y + g, LAMP_TIP), LAMP_NS[1])):
        lo, up = _lamp_edges(y0, y1, n)
        made.append(lamps.lens("A06T_Lightbar_Lens" + tag, lo, up, lamp_place, collection,
                               lib["lamp_red_lens"], 5, crown, out, thickness=0.003,
                               bevel=(0.0010, 2, 30)))
        made += lamps.seals("A06T_Lightbar_Seal" + tag, lo, up, lamp_place, collection,
                            lib["grille"], out, width=0.0040, d=0.0008)
        made.append(lamps.band_between("A06T_Lightbar_Pipe" + tag, lo, up, range(n),
                                       (0.26, 0.31, 0.36), lamp_place, pipe,
                                       collection, red, out))
    return made


# -------------------------------------------------------------- backlight
X_PANE_TOP = -1.985            # the glass's top edge (z ~1.29 on the centreline, c1_0006), 0.1 m ahead of the spoiler's tip (x -2.09)
PANE_EDGE = 0.014
PANE_LIFT = 0.0008
PANE_BACK = 0.005
PANE_CUT = 0.006
Z_FACE = 0.985
CORNER_W = 0.14
CORNER_BAND = 0.040


def _v_edge(x):
    return S.v_along(x, PN.V_REARGLASS(x), PANE_EDGE)


def _loft_z(x, y):
    return S.section_v(x, S.v_at_y_upper(x, y))[1]


def _join_x(y):
    a, b = -2.50, -2.15
    for _ in range(36):
        m = 0.5 * (a + b)
        if m - N.JOIN_R(S.v_at_y_upper(m, y)) < 0.0:
            a = m
        else:
            b = m
    return 0.5 * (a + b)


def _cap_x(y, z):
    return rear_view().x(y, z)


def _mono(pts):
    out = []
    for y, z in sorted((p[0], p[1]) for p in pts):
        if not out or y - out[-1][0] > 1e-6:
            out.append((y, z))
    return out


class _Pane:
    """The pane's outline and depth map (see the Luxeed RX's _Pane)."""

    def __init__(self):
        xs = [X_PANE_TOP - (X_PANE_TOP + 2.44) * k / 40.0 for k in range(41)]
        edge = [(x,) + tuple(S.section_v(x, _v_edge(x))) for x in xs]
        k_w = max(range(len(edge)), key=lambda k: edge[k][1])
        self.x_w, self.y_w, self.z_w = edge[k_w]
        y_tc = edge[0][1]
        top = [(y_tc * k / 16.0, _loft_z(X_PANE_TOP, y_tc * k / 16.0)) for k in range(16)]
        top += [(e[1], e[2]) for e in edge[:k_w + 1]]
        z_top_full = Curve(_mono(top), mode="pchip")
        # The pane closes where the backlight's lateral edge comes down onto the lower edge's rounded corner (c1_0006: the
        # glass's side is upright and rounds into the bottom edge at z ~1.10..1.14, y ~0.53). It used to close at the
        # lateral edge's WIDEST point and drag the lower edge down to it: with the shorter tail that point is the loft's
        # tail end at z ~1.0, so the lower edge sagged 13 cm at the corners and dark glass hung below the real glass line
        # as two wings (found with porting/glass_diff.py, 2026-10-28).
        low_raw = Curve(_mono(GLASS_LOW), mode="pchip")
        y_max = min(self.y_w, GLASS_LOW[0][0])
        a, b = 0.40, y_max
        for _ in range(40):
            m = 0.5 * (a + b)
            if z_top_full(m) - low_raw(m) > 0.0:
                a = m
            else:
                b = m
        self.y_w = 0.5 * (a + b)
        self.z_w = float(low_raw(self.y_w))
        top = [(y, z) for (y, z) in _mono(top) if y < self.y_w - 0.004] + [(self.y_w, self.z_w)]
        self.z_top = Curve(_mono(top), mode="pchip")
        self.z_bot = Curve(_mono([(y, z) for (y, z) in GLASS_LOW if y <= self.y_w + 1e-9] +
                                 [(self.y_w, self.z_w)]), mode="pchip")
        self._cols = {}
        n = 120
        ys = [self.y_w * k / float(n) for k in range(n + 1)]
        self._edge = [(y, self.z_bot(y)) for y in ys] + [(y, self.z_top(y)) for y in ys]

    def outline(self, n=48, grow=0.0):
        ys = [self.y_w * (1.0 - (1.0 - k / float(n)) ** 1.5) for k in range(n + 1)]
        up = [(y, self.z_top(y) + grow) for y in ys]
        lo = [(y, self.z_bot(y) - grow) for y in ys]
        side = [(self.y_w + grow, 0.5 * (self.z_top(self.y_w) + self.z_bot(self.y_w)))]
        return [(-0.03, lo[0][1])] + lo + side + up[::-1] + [(-0.03, up[0][1])]

    def column(self, y):
        key = round(y, 5)
        f = self._cols.get(key)
        if f is not None:
            return f
        xj = _join_x(y) + 0.012
        x1 = max(X_PANE_TOP + 0.01, xj + 0.05)
        n = 24
        pts = []
        for k in range(n + 1):
            x = xj + (x1 - xj) * k / float(n)
            pts.append((_loft_z(x, y), x))
        z_a, x_a = pts[0]
        z_b = _loft_z(xj + 0.010, y)
        s_a = 0.010 / max(1e-4, z_b - z_a)
        loft = Curve(_mono(pts), mode="pchip")
        z_f = min(Z_FACE, self.z_bot(y))
        x_f = _cap_x(y, z_f)
        s_f = (_cap_x(y, z_f + 0.004) - _cap_x(y, z_f - 0.004)) / 0.008
        h = z_a - z_f

        def x_of(z):
            if z >= z_a:
                return loft(z)
            if z <= z_f:
                return _cap_x(y, z)
            t = (z - z_f) / h
            t2, t3 = t * t, t * t * t
            return ((2 * t3 - 3 * t2 + 1) * x_f + (t3 - 2 * t2 + t) * h * s_f
                    + (-2 * t3 + 3 * t2) * x_a + (t3 - t2) * h * s_a)
        f = (x_of, z_a)
        self._cols[key] = f
        return f

    def corner(self, x, y, z, z_a):
        if z >= z_a:
            return x
        ws = geom.smoothstep((y - (self.y_w - CORNER_W)) / (0.6 * CORNER_W))
        if ws <= 0.0:
            return x
        d = min(math.hypot(y - ey, z - ez) for ey, ez in self._edge)
        w = ws * geom.smoothstep(1.0 - d / CORNER_BAND)
        if w <= 0.0:
            return x
        h = rear_view().hit(y, z)
        if h is None:
            return x
        return x + (h[0][0] - x) * w

    def grid(self, ny=36, nz=40, z_hi=None):
        cols = []
        for j in range(ny + 1):
            y = (self.y_w - 0.0005) * (1.0 - (1.0 - j / float(ny)) ** 1.4)
            x_of, z_a = self.column(y)
            z0, z1 = self.z_bot(y), self.z_top(y)
            if z_hi is not None:
                z1 = max(z0 + 0.002, min(z1, z_hi(z_a)))
            cols.append([(self.corner(x_of(z), y, z, z_a), y, z) for z in
                         [z0 + (z1 - z0) * i / float(nz) for i in range(nz + 1)]])
        return cols


_PANE = None


def pane():
    global _PANE
    if _PANE is None:
        _PANE = _Pane()
    return _PANE


def _lift(cols, d):
    out = []
    J, I = len(cols), len(cols[0])
    for j in range(J):
        col = []
        for i in range(I):
            a, b = cols[max(0, j - 1)][i], cols[min(J - 1, j + 1)][i]
            c, e = cols[j][max(0, i - 1)], cols[j][min(I - 1, i + 1)]
            ty = [b[k] - a[k] for k in range(3)]
            tz = [e[k] - c[k] for k in range(3)]
            n = geom.vnorm(geom.vcross(tz, ty))
            if n[0] > 0.0:
                n = tuple(-c for c in n)
            p = cols[j][i]
            q = (p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d)
            col.append((q[0], 0.0 if j == 0 else q[1], q[2]))
        out.append(col)
    return out


def _cut_pane(ob):
    c = C.prism_x("_pane_" + ob.name, pane().outline(grow=PANE_CUT), -2.20, -2.70)
    sheet = C.sheet_bvh(ob)
    C.difference(ob, [c], "pane_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


def build_rear_glass(collection, lib):
    P_ = pane()
    glass = M.grid("A06T_Glass_Rear", _lift(P_.grid(), PANE_LIFT), collection, lib["glass_dark"],
                   geom.away_from((-2.0, 0.0, 1.0)))
    M.mirror_y(glass)
    back = M.grid("A06T_Glass_RearBack", _lift(P_.grid(ny=24, nz=16, z_hi=lambda za: za + 0.03),
                                               -PANE_BACK),
                  collection, lib["shadow"], geom.away_from((-2.0, 0.0, 1.0)))
    M.mirror_y(back)
    return [glass, back]


def build_wiper(collection, lib):
    """Rear wiper blade lying on the glass's base, parked to the left."""
    x_of, _za = pane().column(0.0)
    rows = []
    for i in range(13):
        y = 0.050 + 0.400 * i / 12.0
        x_of, _za = pane().column(min(y, pane().y_w - 0.01))
        rows.append([(x_of(z) - 0.003, y, z) for z in (1.046, 1.058)])
    blade = M.grid("A06T_Wiper", rows, collection, lib["black_gloss"],
                   geom.away_from((-2.0, 0.0, 1.0)))
    M.solidify(blade, 0.003)
    return [blade]


def build_roof_blade(collection, lib):
    """The roof's rear end: the painted roof continues past the glass's top as a thin spoiler plate
    (c1_0004/0005: its tip stands ~7 cm over the glass, x -2.08..-2.11, with a black underside); the
    rear camera sits in the black band under it."""
    # The plate starts at the knee, where the painted roof panel (A06T_Roof_Paint, x -1.95..-1.80) ends. It used to
    # start at -1.80 and lie 0.8 mm over that whole panel: the chord sag of its coarse grid was bigger than 0.8 mm, so
    # the two surfaces cut through each other along the plate's sides in a ragged stair (and black under-plate teeth).
    x_s, x_k = S.KNEE_X, S.KNEE_X
    y_max, n_y, n_x = 0.520, 26, 14
    t_tip = 0.014

    def z_roof(x, y):
        return S.section_v(x, S.v_at_y_upper(x, y))[1]

    top_rows, bot_rows = [], []
    for j in range(n_y + 1):
        y = y_max * j / float(n_y)
        yk = min(y, y_max)
        x_te = PN.X_BLADE + 0.050 * (y / y_max) ** 2
        z_k = z_roof(x_k + 0.02, yk)
        m = (z_roof(x_k + 0.02, yk) - z_roof(x_s, yk)) / (x_k + 0.02 - x_s)       # the roof's slope
        top, bot = [], []
        for i in range(n_x + 1):
            t = i / float(n_x)
            x = x_s + (x_te - x_s) * t
            z = z_roof(x, yk) if x >= x_k + 0.02 else z_k + m * (x - (x_k + 0.02))
            lift = 0.0008 * geom.smoothstep((x - x_s) / 0.04)
            th = t_tip * geom.smoothstep((t - 0.25) / 0.6)
            taper = 1.0 - 0.85 * geom.smoothstep((y / y_max - 0.55) / 0.45)
            top.append((x, y, z + lift))
            # never closer than 3 mm under the top: for the first quarter of the plate the thickness was 0, so the black
            # underside lay exactly on the paint and the two z-fought in the viewer as a band of black speckles across the
            # spoiler (2026-10-28, seen from above in the browser; Cycles hid it)
            bot.append((x, y, z + lift - max(0.003, th * taper)))
        top_rows.append(top)
        bot_rows.append(bot)
    blade = M.grid("A06T_Roof_Blade", top_rows, collection, lib["paint"], geom.away_from((-1.9, 0.0, 0.9)))
    M.mirror_y(blade)
    under = M.grid("A06T_Roof_BladeShadow", bot_rows, collection, lib["black_gloss"],
                   geom.away_from((-1.9, 0.0, 2.0)))
    M.mirror_y(under)
    # the camera in the band under the spoiler
    xc = 0.5 * (PN.X_KNEE + PN.X_FRIT)
    zc = S.surface(xc, 1.0)[2]
    cam = fittings.rounded_panel("A06T_Spoiler_Camera", (xc, 0.0, zc + 0.004),
                                 0.028, 0.014, 0.010,
                                 lambda q, d: ((q[0] - d, q[1], q[2]), (-1.0, 0.0, 0.0)),
                                 xc, collection, lib["lamp_smoked"], d=0.0,
                                 outward=(-1.0, 0.0, 0.0))
    return [blade, under, cam]


# ------------------------------------------------------- the ducktail lip
def build_lip(collection, lib):
    """A thin painted ridge along the backlight's foot (c1_0005 / c1_0007: a fine highlight along the glass's
    lower edge, the tailgate's top lip standing a few mm over the deck). It fades out toward the pane's
    corners so it reads as part of the tailgate, not a bolted-on strip."""
    P_ = pane()
    n = 44
    y_end = P_.y_w - 0.045
    rows = []
    for i in range(n + 1):
        y = y_end * (1.0 - (1.0 - i / float(n)) ** 1.15)
        zb = P_.z_bot(min(y, P_.y_w - 0.001)) - PANE_CUT
        k = 1.0 - geom.smoothstep((y - 0.28) / (y_end - 0.28))
        h = 0.0070 * (0.30 + 0.70 * k)
        try:
            p0 = on_rear(y, zb - 0.018, 0.0004)[0]
            p1 = on_rear(y, zb - 0.0045, h)[0]
            p2 = on_rear(y, zb - 0.0005, 0.0004)[0]
        except RuntimeError:
            continue
        rows.append([p0, p1, p2])
    if len(rows) < 6:
        return []
    ob = M.grid("A06T_Spoiler_Lip", rows, collection, lib["paint"], geom.away_from((-2.30, 0.0, 1.00)))
    M.mirror_y(ob)
    M.finish(ob, thickness=0.0020, bevel=0.0)
    return [ob]


# ---------------------------------------------------------- bumper details
def build_bumper_details(collection, lib):
    made = []
    y0, y1, z0, z1 = REFLECTOR
    rows = []
    for i in range(13):
        y = y0 + (y1 - y0) * i / 12.0
        rows.append([on_tail(y, z, black_stand(0.6) + 0.0015)[0] for z in (z0, z1)])
    ref = M.grid("A06T_Reflector", rows, collection, lib["reflector"], geom.axial(-1.0))
    M.mirror_y(ref)
    made.append(ref)
    return made


# -------------------------------------------------------------- the diffuser
def build_diffuser(collection, lib):
    top = Curve(DIFF_TOP, mode="pchip")
    d0 = black_stand(0.7) + 0.0035            # the insert, standing on the bumper's skin
    ys = [DIFF_Y_END * (1.0 - (1.0 - i / 40.0) ** 1.25) for i in range(41)]
    rows = []
    for y in ys:
        z_hi = top(y)
        rows.append([on_tail(y, DIFF_Z_LO + (z_hi - DIFF_Z_LO) * k / 6.0, d0)[0] for k in range(7)])
    ins = M.grid("A06T_Rear_Diffuser", rows, collection, lib["black_trim"], geom.axial(-1.0))
    M.mirror_y(ins)
    M.finish(ins, thickness=0.0030, bevel=0.0010)
    made = [ins]
    # the fins
    verts, faces = [], []
    for y in FIN_Y:
        k = len(verts)
        for yy in (y - 0.5 * FIN_W, y + 0.5 * FIN_W):
            for z in FIN_Z:
                verts.append(on_tail(yy, z, d0 + 0.0030)[0])
        faces.append([k, k + 1, k + 3, k + 2])
    fins = M.obj("A06T_Rear_Fins", verts, faces, collection, lib["black_gloss"])
    M.orient(fins.data, geom.axial(-1.0))
    M.solidify(fins, 0.0026)
    M.mirror_y(fins)
    made.append(fins)
    # the lip below the insert and the chrome blade on its upper edge (c1_0007: level across, then up round the
    # corner toward the wheel arch)
    def z_blade(y):
        return 0.316 + 0.082 * _smooth01((y - 0.44) / 0.31)

    def z_lip_lo(y):
        return 0.266 + 0.060 * _smooth01((y - 0.52) / 0.23)
    ys = [LIP_Y_END * (1.0 - (1.0 - i / 44.0) ** 1.2) for i in range(45)]
    rows = [[on_tail(y, z_lip_lo(y) + (z_blade(y) - z_lip_lo(y)) * k / 4.0, 0.0105)[0] for k in range(5)]
            for y in ys]
    lip = M.grid("A06T_Rear_Lip", rows, collection, lib["pod"], geom.axial(-1.0))
    M.mirror_y(lip)
    # no Bevel modifier here: on a 3 mm strip whose first row sits on the mirror plane it threw vertices out to 1e17
    # (found by the NaN/huge-vertex check, which also broke the shadow bake's footprint)
    M.finish(lip, thickness=0.0030, bevel=0.0)
    made.append(lip)
    y0, y1 = 0.135, 0.745
    rows = []
    for i in range(41):
        y = y0 + (y1 - y0) * (1.0 - (1.0 - i / 40.0) ** 1.15)
        taper = _smooth01((y - y0) / 0.05) * (1.0 - 0.6 * _smooth01((y - 0.66) / 0.085))
        zc = z_blade(y)
        h = 0.0062 * taper
        rows.append([on_tail(y, zc - 0.0005, 0.0128)[0], on_tail(y, zc - 0.0005 + h, 0.0128)[0]])
    blade = M.grid("A06T_Diffuser_Strip", rows, collection, lib["chrome"], geom.axial(-1.0))
    M.mirror_y(blade)
    made.append(blade)
    return made


# ---------------------------------------------------------------- badges
def _emblem(collection, lib, y, z, name="A06T_Tail_Emblem"):
    p, n = on_tail(y, z, 0.0012)
    hw, hh, t = 0.0175, 0.021, 0.0035
    ring = [(0.0, hh), (hw, hh * 0.15), (0.0, -hh), (-hw, hh * 0.15)]
    verts, faces = [], []

    def bar(a, b, w):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        ox, oy = -dy / L * w * 0.5, dx / L * w * 0.5
        k = len(verts)
        for q in ((a[0] + ox, a[1] + oy), (b[0] + ox, b[1] + oy),
                  (b[0] - ox, b[1] - oy), (a[0] - ox, a[1] - oy)):
            verts.append((q[0], q[1], 0.0))
        faces.append([k, k + 1, k + 2, k + 3])
    for i in range(len(ring)):
        bar(ring[i], ring[(i + 1) % len(ring)], t)
    bar(ring[0], ring[2], t * 0.8)
    ob = M.obj(name, verts, faces, collection, lib["chrome"])
    M.solidify(ob, 0.0022)
    P.on_surface(ob, p, n)
    return ob


def build_badges(collection, lib):
    made = []
    cjk, inter = _font("Noto Sans CJK Regular.woff2"), _font("Inter.woff2")
    mat = lib["chrome"]

    def badge(name, body, size, y, z, font, **kw):
        p, n = on_tail(y, z, 0.0012)
        t = M.text_mesh(name, body, size, collection, mat, extrude=0.0012,
                        font=font, resolution=4, **kw)
        P.on_surface(t, p, n)
        made.append(t)
        return t

    made.append(_emblem(collection, lib, 0.0, 1.055))
    badge("A06T_Badge_Brand", "阿维塔", 0.062, 0.463, 0.871, cjk, weight=0.0004)
    badge("A06T_Badge_Model", "06T", 0.034, -0.463, 0.871, inter, weight=0.0004,
          spacing=1.6)
    return made


def build_all(collection, lib):
    made = []
    made += build_tail(collection, lib)
    made += build_diffuser(collection, lib)
    made += build_lightbar(collection, lib)
    made += build_roof_blade(collection, lib)
    made += build_rear_glass(collection, lib)
    made += build_wiper(collection, lib)
    made += build_lip(collection, lib)
    made += build_bumper_details(collection, lib)
    made += build_badges(collection, lib)
    return made
