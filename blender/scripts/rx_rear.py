"""Luxeed RX rear end: tailgate, light bar, rear glass, spoiler lip, lower
bumper, plate recess, lettering.

Every position was read off the square rear photograph (rear.jpg) through
its solved camera by casting onto the body (refmatch.on_mesh), then written
here as rear-elevation (y, z) positions on the tail cap (left half) - each
part is dropped onto the finished surface at build time.

    tail cap      painted, from under the black bumper's top edge to the
                  ducktail; the tailgate's shut line cut through it: upright
                  at y +/-0.62 from the lamp down to z 0.81, rounding into a
                  lower edge at z 0.68 on the centreline
    light bar     z 0.96-1.03 across the tailgate, 0.93-1.03 on the outer
                  units beyond its edges (a gap at y +/-0.621), which end in
                  rounded tips just round the corners (y 0.815, z 0.98); lit,
                  as photographed
    rear glass    one pane from under the black band down over the cap to
                  the lip (its foot at z 1.096), on a black backing
    spoiler lip   gloss black blade across the glass's base, z 1.07-1.095
    bumper        gloss black from z 0.575 down, a grey pod each side
                  (y 0.41-0.78, z 0.32-0.49) under a red reflector, a silver
                  strip across the diffuser at z 0.30
    plate recess  y +/-0.317, z 0.508-0.665, painted, 30 mm deep
    lettering     'LUXEED' set wide at z 0.93; '奇瑞汽车' left and '智界 RX'
                  right at z 0.84
"""
import math
import os

import bpy

import rx_surface as S
import rx_nose as N
import rx_panels as PN
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
GATE_Y = 0.621                 # the tailgate's side edges (rear photo, u 678)
GATE_EDGE = [(0.000, 0.682), (0.150, 0.683), (0.276, 0.686), (0.380, 0.698),
             (0.441, 0.712), (0.505, 0.730), (0.551, 0.753), (0.590, 0.780),
             (0.607, 0.807), (0.618, 0.850), (GATE_Y, 0.930), (GATE_Y, 1.010),
             (GATE_Y, 1.100)]

# The light bar's edges in rear elevation (y, z) on the tail cap, to the outer
# unit's tip. Rear photo: level across, 1.03 over 0.93 at the outer units, and
# each outer unit ends in a rounded tip just round the corner - its extreme
# at y 0.815, z 0.98 (x ~-2.29), body colour outboard of it; the forest and
# street 3/4s show the same level, rounded end. (It first ran on up the flank
# to a point at (-2.14, 0.836, 1.108), a red fin climbing the corner.)
LAMP_UPPER = [(0.000, 1.031), (0.300, 1.030), (0.550, 1.028), (0.700, 1.027),
              (0.760, 1.028), (0.790, 1.025), (0.804, 1.016), (0.812, 1.001),
              (0.815, 0.980)]
LAMP_LOWER = [(0.000, 0.959), (0.300, 0.956), (0.450, 0.950), (0.550, 0.940),
              (0.620, 0.930), (0.700, 0.928), (0.760, 0.930), (0.790, 0.935),
              (0.804, 0.946), (0.812, 0.962), (0.815, 0.980)]
LAMP_TIP = LAMP_UPPER[-1][0]
# the tailgate's edge splits the bar into the gate's centre unit and the
# body's outer units (rear photo: a dark gap through the lens at u 677)
LAMP_GAP = 0.006
LAMP_NS = (48, 30)             # stations: centre unit (half), outer unit

SPOILER = (1.070, 1.095)       # z of the lip's lower and upper edge
# The rear glass's foot in rear elevation (y, z), left half, read off the rear
# photo onto the model: round the left end at y 0.568, z 1.20, and down into a
# flat bottom just over the lip (rx_rear._Pane carries it to the side edge).
GLASS_LOW = [(0.568, 1.197), (0.555, 1.177), (0.530, 1.151), (0.483, 1.123),
             (0.437, 1.106), (0.390, 1.099), (0.345, 1.097), (0.181, 1.096),
             (0.000, 1.096)]
Z_BLACK = 0.575                # top of the gloss black bumper
PLATE_RECESS = geom.round_rect(0.0, 0.317, 0.508, 0.665, 0.020, open_inboard=True)
# shallower than the shadow shell's 7.2 mm inset, or the shell hides it and
# the painted recess renders black
PLATE_DEPTH = 0.0060
POD_BOX = (0.413, 0.776, 0.360, 0.500)     # y0, y1, z0, z1 (rear photo: z 0.36-0.50)
POD = geom.round_rect(*POD_BOX, 0.040)
REFLECTOR = (0.455, 0.745, 0.503, 0.531)


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
    first surface of the tail cap as built (its full grid, before any cut)
    or the flank beside it.

    on_tail inverts the cap's (w, v) chart, and that fails at the corners,
    where the cap turns into the flank: the light bar's tips climbed 9 cm
    and hooked, and the rear glass's foot there was thrown a metre behind the
    car. The ray cannot miss that way."""

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
        # the flank ahead of the cap's join, as far as a corner ray can reach
        base = len(verts)
        vs = [0.25 + 0.55 * k / 60.0 for k in range(61)]
        for i in range(61):
            t = i / 60.0
            verts.extend(S.surface(N.JOIN_R(v) + (-1.85 - N.JOIN_R(v)) * t, v) for v in vs)
        for i in range(60):
            a, b = base + i * 61, base + (i + 1) * 61
            faces += [[a + j, a + j + 1, b + j + 1, b + j] for j in range(60)]
        self.tree = BVHTree.FromPolygons(verts, faces)

    def hit(self, y, z):
        """(point, outward normal) seen at (y, z), or None."""
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
    """A point seen from behind at (y, z), d off the surface. For the corners,
    where on_tail's chart fails."""
    h = rear_view().hit(y, z)
    if h is None:
        raise RuntimeError("rear view: nothing at (y %.3f, z %.3f)" % (y, z))
    p, n = h
    return (p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d), n


def _font(fn):
    try:
        return bpy.data.fonts.load(os.path.join(FONT_DIR, fn), check_existing=True)
    except Exception as e:
        print("font %s not loaded (%s) - using Blender's default" % (fn, e))
        return None


# ---------------------------------------------------------------- tailgate
def gate_path():
    pts, nrm = [], []
    ring = geom.polyline([(0.0, y, z) for (y, z) in [(-0.02, 0.682)] + GATE_EDGE], 70)
    for (_x, y, z) in ring:
        p, n = on_tail(y, z)
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


def _cut_pod(ob):
    L = S.HALF_L
    c = C.prism_x("_pod_" + ob.name, POD, -L - 0.30, -L + 0.40)
    C.difference(ob, [c], "pod_", reset_materials=True)


def _cut_corner(ob):
    """Outboard of the pods the bumper is cut up under the black band's
    lower edge (rx_panels.Z_BAND_LO): behind the rear wheel the body climbs
    away from the ground (side photo)."""
    sheet = C.sheet_bvh(ob)
    C.difference(ob, PN.rear_corner_cutters(), "corner_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


def black_stand(w):
    return 0.008 - 0.005 * geom.smoothstep((w - 0.85) / 0.15)


def build_tail(collection, lib):
    made = []
    # painted tail: from just under the black bumper's top to the ducktail,
    # to the very top (stopped at the spoiler, the cap's corners outboard of
    # the glass were covered by nothing and the car could be seen through) -
    # except under the rear glass, which runs on over the cap to the lip
    made.append(FA.cap_panel("RX_Tail_Upper", TAIL, collection, lib, Z_BLACK - 0.060,
                             N.TAIL_Z_HI - 0.0008, 0.0, 1.0, 44, 44, mat="paint",
                             top_to_centre=True, cuts=(_cut_gate, _cut_recess, _cut_pane)))
    made += FA.valance("RX_Tail_Valance", TAIL, collection, lib, lambda w: Z_BLACK,
                       stand=black_stand, nw=44, nz=26, mat="black_gloss",
                       thickness=0.0030, cuts=(_cut_recess, _cut_pod, _cut_corner))
    # plate recess: a painted pocket with walls
    x_face = FA.recessed_x(TAIL, 0.0)
    made.append(_pocket("RX_Rear_PlateRecess", PLATE_RECESS, PLATE_DEPTH, collection,
                        lib["paint"], x_face))
    # grey pods: proud panels in the pod openings
    y0, y1, z0, z1 = POD_BOX
    pod = fittings.rounded_panel("RX_Rear_Pod", (-S.HALF_L, 0.5 * (y0 + y1), 0.5 * (z0 + z1)),
                                 0.5 * (y1 - y0) - 0.004, 0.5 * (z1 - z0) - 0.004, 0.036,
                                 lambda q, d: on_tail(q[1], q[2], d), -S.HALF_L,
                                 collection, lib["pod"], d=0.013, ny=24,
                                 outward=(-1.0, 0.0, 0.0))
    M.solidify(pod, 0.004)
    M.mirror_y(pod)
    made.append(pod)
    return made


def _pocket(name, outline, depth, collection, mat, x_face, walls=True):
    """A shallow pocket (depth > 0) or a proud panel (depth < 0) inside an
    elevation outline, following the tail's own curvature."""
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
    made = ob
    if walls and depth > 0:
        a, b = [], []
        for (y, z) in ring:
            w, v = TAIL.wv_at(max(0.0, y), z)
            a.append(TAIL.point(w, v))
            b.append(TAIL.offset(w, v, -depth))
        wl = M.strip(name + "_Wall", a, b, collection, mat)
        M.mirror_y(wl)
    M.mirror_y(ob)
    return made


# ---------------------------------------------------------------- the lamps
def lamp_place(p, d):
    """A lamp point onto the tail where the rear photo sees it (y, z)."""
    return on_rear(p[1], p[2], d)


def _lamp_edges(y0, y1, n):
    """The bar's lower and upper edges between y0 and y1, n stations each, on
    the cap; a unit ending at the tip closes to a point there."""
    lo_c = Curve(LAMP_LOWER, mode="pchip")
    up_c = Curve(LAMP_UPPER, mode="pchip")
    # stations packed toward the tip, where the ends round off
    ys = [y0 + (y1 - y0) * (1.0 - (1.0 - k / float(n - 1)) ** 1.6
                            if y1 >= LAMP_TIP else k / float(n - 1)) for k in range(n)]
    lo = [on_rear(y, lo_c(y))[0] for y in ys]
    up = [on_rear(y, up_c(y))[0] for y in ys]
    return lo, up


def build_lightbar(collection, lib):
    made = []
    out = geom.away_from((-2.10, 0.30, 0.98))
    crown = (lambda k, n: 0.0032 + 0.0010 * math.sin(math.pi * k / n))
    pipe = (lambda k: 0.0052)
    red = lib["led_red_tail"]
    g = 0.5 * LAMP_GAP
    for tag, (y0, y1), n in (("", (0.0, GATE_Y - g), LAMP_NS[0]),
                             ("Out", (GATE_Y + g, LAMP_TIP), LAMP_NS[1])):
        lo, up = _lamp_edges(y0, y1, n)
        made.append(lamps.lens("RX_Lightbar_Lens" + tag, lo, up, lamp_place, collection,
                               lib["lamp_red_lens"], 5, crown, out, thickness=0.003,
                               bevel=(0.0010, 2, 30)))
        made += lamps.seals("RX_Lightbar_Seal" + tag, lo, up, lamp_place, collection,
                            lib["grille"], out, width=0.0045, d=0.0008)
        # the bar (rear and rear 3/4 photos): a bright line under the top
        # edge and a second along the lower edge, the smoked wine-red lens
        # between them; on the outer units they close round the tip as a loop
        made.append(lamps.band_between("RX_Lightbar_PipeUp" + tag, lo, up, range(n),
                                       (0.80, 0.86, 0.92), lamp_place, pipe,
                                       collection, red, out))
        made.append(lamps.band_between("RX_Lightbar_Pipe" + tag, lo, up, range(n),
                                       (0.08, 0.14, 0.20), lamp_place, pipe,
                                       collection, red, out))
    return made


# -------------------------------------------------------------- backlight
# The rear glass is ONE pane: a depth map x(y, z) over its outline in rear
# elevation. Above the tail cap's join it lies on the loft's backlight,
# exactly; below it a cubic round-over carries it down to its foot on the
# cap's face, over the lip. Built on the meshes instead (a skin cast along +x
# over the loft's glass, the cap and the quarter), every facet showed through
# it, and so did the loft/cap join - a V across the glass from z 1.18 on the
# centreline to 1.27 at the sides, over a cap top that fans into the ducktail
# and cannot be mapped from behind: the 'arrow' on the glass. The cap's paint
# is cut away under the pane (_cut_pane) and a black backing closes it.
X_PANE_TOP = PN.X_FRIT + 0.025      # the pane runs 25 mm up under the black band
PANE_EDGE = 0.014                   # its side edge inside the backlight's (a black bead)
PANE_LIFT = 0.0008                  # off the loft
PANE_BACK = 0.005                   # the backing behind its lower part
PANE_CUT = 0.006                    # the cap's paint stops this far outside it
Z_FACE = 1.120                      # the round-over's foot on the cap's face (below
                                    # the fan: the cap maps from behind under 1.14)
CORNER_W = 0.14                     # the lower corners: this far in from the widest point
CORNER_BAND = 0.040                 # ... within this of the outline, eased onto the tail


def _v_edge(x):
    return S.v_along(x, PN.V_REARGLASS(x), PANE_EDGE)


def _loft_z(x, y):
    """Height of the loft's upper section at station x and lateral y."""
    return S.section_v(x, S.v_at_y_upper(x, y))[1]


def _join_x(y):
    """Station where the column at lateral y meets the tail cap's join."""
    a, b = -2.47, -2.25
    for _ in range(36):
        m = 0.5 * (a + b)
        if m - N.JOIN_R(S.v_at_y_upper(m, y)) < 0.0:
            a = m
        else:
            b = m
    return 0.5 * (a + b)


def _cap_x(y, z):
    return rear_view().x(y, z)


class _Pane:
    """The pane's outline and depth map."""

    def __init__(self):
        # side edge down the loft, from under the band to its widest point
        xs = [X_PANE_TOP - (X_PANE_TOP + 2.44) * k / 40.0 for k in range(41)]
        edge = [(x,) + tuple(S.section_v(x, _v_edge(x))) for x in xs]
        k_w = max(range(len(edge)), key=lambda k: edge[k][1])
        self.x_w, self.y_w, self.z_w = edge[k_w]
        # top: the section at X_PANE_TOP out to the side edge, then the edge
        y_tc = edge[0][1]
        top = [(y_tc * k / 16.0, _loft_z(X_PANE_TOP, y_tc * k / 16.0)) for k in range(16)]
        top += [(e[1], e[2]) for e in edge[:k_w + 1]]
        self.z_top = Curve(_mono(top), mode="pchip")
        # foot: the photo's lower outline (GLASS_LOW), carried out to meet the
        # side edge at its widest point
        y0, z0 = GLASS_LOW[0]
        low = [(y * self.y_w / y0, z + (self.z_w - z0) * (y / y0) ** 2) for y, z in GLASS_LOW]
        self.z_bot = Curve(_mono(low), mode="pchip")
        self._cols = {}
        n = 120
        ys = [self.y_w * k / float(n) for k in range(n + 1)]
        self._edge = [(y, self.z_bot(y)) for y in ys] + [(y, self.z_top(y)) for y in ys]

    def outline(self, n=48, grow=0.0):
        """Closed (y, z) loop of the left half, grown outward by `grow`."""
        ys = [self.y_w * (1.0 - (1.0 - k / float(n)) ** 1.5) for k in range(n + 1)]
        up = [(y, self.z_top(y) + grow) for y in ys]
        lo = [(y, self.z_bot(y) - grow) for y in ys]
        side = [(self.y_w + grow, 0.5 * (self.z_top(self.y_w) + self.z_bot(self.y_w)))]
        return [(-0.03, lo[0][1])] + lo + side + up[::-1] + [(-0.03, up[0][1])]

    def column(self, y):
        """x(z) for the column at lateral y, as a function."""
        key = round(y, 5)
        f = self._cols.get(key)
        if f is not None:
            return f
        xj = _join_x(y) + 0.012
        # at the pane's sides the join is above its top edge: the column is
        # all round-over, and the loft only gives the upper anchor
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
        """Round the lower corners the round-over ran 1-2.5 cm inside the
        tail, and the paint cut round the pane stood as a torn wall beside
        the glass: within CORNER_BAND of the outline it is eased onto the
        tail as built (seen from behind)."""
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
        """Columns of (x, y, z) from the foot up to the top (or z_hi(y, z_a))."""
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
    """Move every grid point d along the depth map's outward normal."""
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
    """The tail cap's paint stops PANE_CUT outside the pane: under it the cap
    fans into the ducktail, and paint there showed through the glass."""
    c = C.prism_x("_pane_" + ob.name, pane().outline(grow=PANE_CUT), -2.20, -2.70)
    sheet = C.sheet_bvh(ob)
    C.difference(ob, [c], "pane_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


def build_rear_glass(collection, lib):
    P_ = pane()
    glass = M.grid("RX_Glass_Rear", _lift(P_.grid(), PANE_LIFT), collection, lib["glass_dark"],
                   geom.away_from((-2.0, 0.0, 1.0)))
    M.mirror_y(glass)
    # the backing: black, 5 mm behind the pane where it leaves the loft (on
    # the loft the greenhouse underlay RX_Roof_Rear_Black is behind it)
    back = M.grid("RX_Glass_RearBack", _lift(P_.grid(ny=24, nz=16, z_hi=lambda za: za + 0.03),
                                             -PANE_BACK),
                  collection, lib["shadow"], geom.away_from((-2.0, 0.0, 1.0)))
    M.mirror_y(back)
    return [glass, back]


def _mono(pts):
    """(y, z) points sorted by y with duplicates in y dropped."""
    out = []
    for y, z in sorted((p[0], p[1]) for p in pts):
        if not out or y - out[-1][0] > 1e-6:
            out.append((y, z))
    return out


# ------------------------------------------------------------ spoiler lip
def build_spoiler(collection, lib):
    """Gloss black lip across the glass's base, standing ~30 mm off the
    tail and tapering out at the tailgate's edges."""
    n = 36
    rows = []
    for i in range(n + 1):
        y = GATE_Y * i / float(n)
        taper = 1.0 - 0.7 * geom.smoothstep((y - 0.45) / (GATE_Y - 0.45))
        lo, nl = on_tail(y, SPOILER[0], 0.001)
        hi, nh = on_tail(y, SPOILER[1], 0.001)
        tip = tuple(hi[k] + nh[k] * 0.030 * taper - (0, 0, 0.004)[k] for k in range(3))
        rows.append([lo, tip, hi])
    ob = M.grid("RX_Spoiler_Lip", rows, collection, lib["black_gloss"],
                geom.away_from((-2.30, 0.0, 1.00)))
    M.solidify(ob, 0.002)
    M.mirror_y(ob)
    return [ob]


def build_roof_blade(collection, lib):
    """The roof's painted end is a spoiler blade over the backlight (rear
    photo read onto the roof: its top from v 160, the trailing edge at
    v 205 = x -1.968, z 1.42; side photo: the edge at x -2.00, z 1.415 with a
    dark slot under it). Its edge stands ~8 mm proud with a black shadow
    line behind it; the rear camera sits in the black band across the
    glass's top (rx_panels RX_Glass_Frit)."""
    xe = PN.X_BLADE
    n = 30
    y_max = 0.53
    prof = ((-0.004, 0.0006), (0.000, 0.0080), (0.035, 0.0070), (0.090, 0.0035),
            (0.170, 0.0000))
    rows, shade = [], []
    for i in range(n + 1):
        y = y_max * i / float(n)
        taper = 1.0 - geom.smoothstep((y - 0.40) / (y_max - 0.40))
        row = []
        for dx, off in prof:
            x = xe + dx
            v = S.v_at_y_upper(x, y) if y > 0.0 else 1.0
            p, nr = S.surface(x, v), S.surface_normal(x, v)
            d = 0.0006 + (off - 0.0006) * taper if off > 0.0006 else off
            row.append(tuple(p[k] + nr[k] * d for k in range(3)))
        rows.append(row)
        srow = []
        for dx in (-0.022, -0.004):
            x = xe + dx
            v = S.v_at_y_upper(x, y) if y > 0.0 else 1.0
            p, nr = S.surface(x, v), S.surface_normal(x, v)
            srow.append(tuple(p[k] + nr[k] * 0.0008 for k in range(3)))
        shade.append(srow)
    blade = M.grid("RX_Roof_Blade", rows, collection, lib["paint"],
                   geom.away_from((xe + 0.1, 0.0, 1.0)))
    M.mirror_y(blade)
    line = M.grid("RX_Roof_BladeShadow", shade, collection, lib["black_gloss"],
                  geom.away_from((xe, 0.0, 1.0)))
    M.mirror_y(line)
    # rear camera: centred in the black band
    xc = 0.5 * (PN.X_KNEE + PN.X_FRIT)
    zc = S.surface(xc, 1.0)[2]
    cam = fittings.rounded_panel("RX_Spoiler_Camera", (xc, 0.0, zc + 0.004),
                                 0.028, 0.014, 0.010,
                                 lambda q, d: ((q[0] - d, q[1], q[2]), (-1.0, 0.0, 0.0)),
                                 xc, collection, lib["lamp_smoked"], d=0.0,
                                 outward=(-1.0, 0.0, 0.0))
    return [blade, line, cam]


# ---------------------------------------------------------- bumper details
def build_bumper_details(collection, lib):
    made = []
    y0, y1, z0, z1 = REFLECTOR
    rows = []
    for i in range(13):
        y = y0 + (y1 - y0) * i / 12.0
        rows.append([on_tail(y, z, black_stand(0.6) + 0.0015)[0] for z in (z0, z1)])
    ref = M.grid("RX_Reflector", rows, collection, lib["reflector"], geom.axial(-1.0))
    M.mirror_y(ref)
    made.append(ref)
    rows = []
    for i in range(21):
        y = 0.35 * i / 20.0
        rows.append([on_tail(y, z, 0.012)[0] for z in (0.296, 0.306)])
    strip = M.grid("RX_Diffuser_Strip", rows, collection, lib["chrome"], geom.axial(-1.0))
    M.mirror_y(strip)
    made.append(strip)
    return made


# ---------------------------------------------------------------- lettering
def build_badges(collection, lib):
    made = []
    inter, cjk = _font("Inter.woff2"), _font("Noto Sans CJK Regular.woff2")
    mat = lib["text_dark"]

    def badge(name, body, size, y, z, font, mat=mat, **kw):
        p, n = on_tail(y, z, 0.0010)
        t = M.text_mesh(name, body, size, collection, mat, extrude=0.0010,
                        font=font, resolution=4, **kw)
        P.on_surface(t, p, n)
        made.append(t)
        return t

    # 'L U X E E D': caps 20 mm tall, set wide - 0.46 m from the L's left
    # edge to the D's right (rear photo, solved camera; spacing 3.1 had
    # built it 0.24 m, half the photo's)
    badge("RX_Letter_Luxeed", "LUXEED", 0.030, 0.0, 0.928, inter, spacing=6.2,
          weight=0.0004)
    badge("RX_Badge_Chery", "奇瑞汽车", 0.030, 0.528, 0.836, cjk, weight=0.0006)
    badge("RX_Badge_Model", "智界 RX", 0.034, -0.528, 0.836, cjk, weight=0.0006)
    # tailgate release on the centreline
    p, n = on_tail(0.0, 0.860, 0.0008)
    ob = fittings.rounded_panel("RX_Tail_Release", (-S.HALF_L, 0.0, 0.860), 0.008, 0.017,
                                0.008, lambda q, d: on_tail(q[1], q[2], d),
                                -S.HALF_L, collection, lib["black_gloss"], d=0.0012,
                                outward=(-1.0, 0.0, 0.0))
    made.append(ob)
    return made


def build_all(collection, lib):
    made = []
    made += build_tail(collection, lib)
    made += build_lightbar(collection, lib)
    made += build_spoiler(collection, lib)
    made += build_roof_blade(collection, lib)
    made += build_rear_glass(collection, lib)
    made += build_bumper_details(collection, lib)
    made += build_badges(collection, lib)
    return made
