"""Voyah Passion S (岚图追光S) rear end, calibrated to studio rear photo c1_0006.jpg via vps_cam.REAR_CAM.

Key Passion S rear-end features read directly off rear_grid.png (3840 x 2880):
  - Liftback tailgate (`GATE_EDGE` at y +/-0.654 down to z 0.743 above the bumper plate alcove)
  - Raked liftback backlight (`VPS_Glass_Rear`) with dark ceramic backing & subtle painted ducktail lip
  - Twin-pod body-coloured aero roof spoiler (`|y| 0.195..0.545`) linked by a gloss-black centre bridge
    (`|y| < 0.195`) carrying the rear ADAS camera pod
  - Full-width smoked taillight bar housing a continuous horizontal red LED signature, illuminated
    'V O Y A H' centre script, and gloss-black boomerang aero corner vents descending to z 0.87
  - Central vertical gloss-black rear LiDAR/camera pill on the tailgate, '岚图' left, '追光' + red 'S' right
  - Sculpted gloss-black lower diffuser rising into twin outer arches with slim red reflectors,
    bumper licence plate recess, and 7 vertical aero diffuser fins
"""
import math
import os

import bpy

import vps_surface as S
import vps_nose as N
import vps_panels as PN
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
GATE_Y = 0.654
GATE_EDGE = [
    (0.000, 0.743), (0.340, 0.743), (0.480, 0.746), (0.555, 0.758),
    (0.605, 0.785), (0.635, 0.835), (0.648, 0.920), (GATE_Y, 1.030),
    (GATE_Y, 1.135),
]
GATE_TOP = tuple(1.142 + 0.008 * i for i in range(13)) + (1.255, 1.290)

# Full-width smoked taillight bar (rear_grid v 1265..1332, wrapping flanks to y 0.875)
LAMP_UPPER = [
    (0.000, 1.140), (0.340, 1.140), (0.560, 1.135), (0.654, 1.128),
    (0.750, 1.116), (0.815, 1.102), (0.855, 1.086), (0.878, 1.072),
]
LAMP_LOWER = [
    (0.000, 1.086), (0.340, 1.086), (0.480, 1.082), (0.560, 1.072),
    (0.654, 1.068), (0.750, 1.064), (0.815, 1.062), (0.855, 1.063),
    (0.878, 1.068),
]
LAMP_TIP = LAMP_UPPER[-1][0]
LAMP_START = 0.0
LAMP_GAP = 0.006
LAMP_NS = (30, 24)

# Liftback backlight lower edge (rear_grid v 1205: flat at z 1.218 across centre, rounding up at sides)
GLASS_LOW = [
    (0.575, 1.285), (0.565, 1.252), (0.545, 1.232), (0.510, 1.222),
    (0.450, 1.219), (0.320, 1.218), (0.160, 1.218), (0.000, 1.218),
]

# Bumper licence-plate alcove (below GATE_EDGE z 0.743 so plate stays on fixed bumper)
PLATE_RECESS = [
    (-0.02, 0.560), (0.290, 0.560), (0.335, 0.572), (0.355, 0.640),
    (0.345, 0.712), (0.310, 0.726), (-0.02, 0.726),
]
PLATE_DEPTH = 0.012

# Gloss-black lower diffuser top profile: low under plate (0.556), arched over reflectors (0.688)
Z_BLACK_CURVE = Curve([
    (0.000, 0.556), (0.280, 0.556), (0.335, 0.575), (0.385, 0.665),
    (0.450, 0.688), (0.640, 0.686), (0.715, 0.662), (0.775, 0.595),
    (0.840, 0.525), (0.920, 0.500), (1.000, 0.495),
], mode="pchip")

REFLECTOR = (0.435, 0.705, 0.630, 0.648)


# ----------------------------------------------------------------- helpers
def on_tail(y, z, d=0.0):
    zc = max(TAIL.Z_LO + 0.003, min(TAIL.Z_HI - 0.003, z))
    w, v = TAIL.wv_at(abs(y), zc)
    p, n = TAIL.point(w, v), TAIL.normal(w, v)
    p = (p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d)
    if y < 0.0:
        p, n = (p[0], -p[1], p[2]), (n[0], -n[1], n[2])
    return p, n


class _RearView:
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
            verts.extend(S.surface(N.JOIN_R(v) + (-1.68 - N.JOIN_R(v)) * t, v) for v in vs)
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
        return on_tail(y, z, d)
    p, n = h
    return (p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d), n


def _font(fn):
    try:
        return bpy.data.fonts.load(os.path.join(FONT_DIR, fn), check_existing=True)
    except Exception:
        if "CJK" in fn:
            for sys_font in ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/simsun.ttc"):
                if os.path.exists(sys_font):
                    try:
                        return bpy.data.fonts.load(sys_font, check_existing=True)
                    except Exception:
                        pass
        return None


# ---------------------------------------------------------------- tailgate & bumper
def gate_path():
    pts, nrm = [], []
    edge_lo = [(-0.02, 0.743)] + [p for p in GATE_EDGE if p[1] <= 1.035]
    ring = geom.polyline([(0.0, y, z) for (y, z) in edge_lo], 56)
    for (_x, y, z) in ring:
        p, n = on_tail(y, z)
        pts.append(p)
        nrm.append(n)
    _, v0 = TAIL.wv_at(GATE_Y, edge_lo[-1][1])
    va, vb = v0, 0.995
    for _ in range(36):
        vm = 0.5 * (va + vb)
        if S.section_v(TAIL.JOIN(vm), vm)[0] >= GATE_Y:
            va = vm
        else:
            vb = vm
    v_end = 0.5 * (va + vb)
    for k in range(1, 45):
        v = v0 + (v_end - v0) * (k / 44.0)
        yj = S.section_v(TAIL.JOIN(v), v)[0]
        w = min(1.0, GATE_Y / max(1e-4, yj))
        pts.append(TAIL.point(w, v))
        nrm.append(TAIL.normal(w, v))
    return pts, nrm


def _cut_gate(ob):
    pts, nrm = gate_path()
    n_lo = sum(1 for p in pts if p[2] <= 1.060)
    c_lo = C.slot("_gate_lo_" + ob.name, pts[:max(8, n_lo)], nrm[:max(8, n_lo)],
                  PN.GAP, out=0.045, inside=0.045)
    c_hi = C.prism_y("_gate_hi_" + ob.name,
                     [(-2.60, 1.028), (-2.04, 1.028), (-2.04, 1.280), (-2.60, 1.280)],
                     GATE_Y - 0.5 * PN.GAP, GATE_Y + 0.5 * PN.GAP)
    C.difference(ob, [c_lo, c_hi], "gate_", reset_materials=True)


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


def black_stand(w):
    return 0.008 - 0.005 * geom.smoothstep((w - 0.85) / 0.15)


def _z_valance_top(w):
    y_approx = 0.90 * w
    return Z_BLACK_CURVE(min(1.0, max(0.0, y_approx)))


def _pocket(name, outline, depth, collection, mat):
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
    a, b = [], []
    for (y, z) in ring:
        w, v = TAIL.wv_at(max(0.0, y), z)
        a.append(TAIL.point(w, v))
        b.append(TAIL.offset(w, v, -depth))
    wl = M.strip(name + "_Wall", a, b, collection, mat)
    M.mirror_y(wl)
    M.mirror_y(ob)
    return ob


def build_tail(collection, lib):
    made = []
    made.append(FA.cap_panel("VPS_Tail_Upper", TAIL, collection, lib, 0.495,
                             N.TAIL_Z_HI - 0.0008, 0.0, 1.0, 76, 56, mat="paint",
                             top_to_centre=True, cuts=(_cut_gate, _cut_recess, _cut_pane)))
    made += FA.valance("VPS_Tail_Valance", TAIL, collection, lib,
                       _z_valance_top, stand=black_stand, nw=48, nz=28, mat="black_gloss",
                       thickness=0.0030, cuts=(_cut_corner,))
    made.append(_pocket("VPS_Rear_PlateRecess", PLATE_RECESS, PLATE_DEPTH, collection,
                        lib["paint"]))
    p, n = on_rear(0.0, 0.642, -0.006)
    made += fittings.plate("VPS_Plate_Rear", p, n, collection, lib, w=0.440, h=0.140,
                           texts=[("VOYAH 追光S", 0.0, 0.036, False, True)],
                           mat="black_gloss", text_mat="chrome")
    pc, nc = on_rear(0.0, 0.728, 0.002)
    made += lamps.projector("VPS_Rear_Camera", pc, nc, 0.0085, collection, lib,
                            mats=("black_gloss", "lamp_smoked"))
    return made


# ---------------------------------------------------------------- taillight & corner vents
def lamp_place(p, d):
    return on_rear(p[1], p[2], d)


def _lamp_edges(y0, y1, n):
    lo_c = Curve(LAMP_LOWER, mode="pchip")
    up_c = Curve(LAMP_UPPER, mode="pchip")
    ys = [y0 + (y1 - y0) * (1.0 - (1.0 - k / float(n - 1)) ** 1.5
                            if y1 >= LAMP_TIP else k / float(n - 1)) for k in range(n)]
    lo = [on_rear(y, lo_c(y))[0] for y in ys]
    up = [on_rear(y, up_c(y))[0] for y in ys]
    return lo, up


def build_lightbar(collection, lib):
    made = []
    out = geom.away_from((-2.10, 0.30, 1.05))
    crown = (lambda k, n: 0.0032 + 0.0010 * math.sin(math.pi * k / n))
    pipe = (lambda k: 0.0040)
    red = lib["led_red_tail"]
    g = 0.5 * LAMP_GAP
    for tag, (y0, y1), n in (("", (LAMP_START, GATE_Y - g), LAMP_NS[0]),
                             ("Out", (GATE_Y + g, LAMP_TIP), LAMP_NS[1])):
        lo, up = _lamp_edges(y0, y1, n)
        made.append(lamps.lens("VPS_Lightbar_Housing" + tag, lo, up, lamp_place, collection,
                               lib["lamp_housing"], 5, lambda k, nk: 0.0008, out,
                               thickness=0.0025, bevel=0.0))
        made += lamps.seals("VPS_Lightbar_Seal" + tag, lo, up, lamp_place, collection,
                            lib["black_gloss"], out, width=0.0040, d=0.0008)
        made.append(lamps.band_between("VPS_Lightbar_Pipe" + tag, lo, up, range(n),
                                       (0.32, 0.42, 0.52), lamp_place, pipe,
                                       collection, red, out))
        made.append(lamps.lens("VPS_Lightbar_Lens" + tag, lo, up, lamp_place, collection,
                               lib["lamp_red_lens"], 5, crown, out, thickness=0.003,
                               bevel=(0.0010, 2, 30)))

    # Illuminated 'V O Y A H' script inside the centre smoked taillight bar
    inter = _font("Inter.woff2")
    for ch, yy in (("V", 0.180), ("O", 0.090), ("Y", 0.000), ("A", -0.090), ("H", -0.180)):
        p, n = on_rear(yy, 1.114, 0.0024)
        t = M.text_mesh("VPS_Lightbar_Script_" + ch, ch, 0.024, collection, lib["lamp_white_bar"],
                        extrude=0.0012, font=inter, resolution=4, weight=0.0005)
        P.on_surface(t, p, n)
        made.append(t)

    # Gloss-black boomerang aero corner vents descending from outer taillight tips (rear_grid u 1105..1195)
    vent_in = Curve([(1.064, 0.805), (1.005, 0.822), (0.935, 0.848), (0.872, 0.868)], mode="pchip")
    vent_out = Curve([(1.064, 0.858), (1.005, 0.875), (0.935, 0.890), (0.872, 0.885)], mode="pchip")
    v_rows = []
    for j in range(11):
        zz = 1.064 - (1.064 - 0.872) * j / 10.0
        yi, yo = vent_in(zz), vent_out(zz)
        v_rows.append([on_rear(yi + (yo - yi) * k / 6.0, zz, 0.0032)[0] for k in range(7)])
    bv = M.grid("VPS_Rear_CornerVent", v_rows, collection, lib["black_gloss"],
                geom.away_from((-2.15, 0.60, 0.96)))
    M.mirror_y(bv)
    M.finish(bv, thickness=0.0035, bevel=0.0)
    made.append(bv)
    return made


# -------------------------------------------------------------- backlight pane
X_PANE_TOP = -1.755
PANE_EDGE = 0.014
PANE_LIFT = 0.0008
PANE_BACK = 0.005
PANE_CUT = 0.006
Z_FACE = 1.142
CORNER_W = 0.14
CORNER_BAND = 0.040


def _v_edge(x):
    return S.v_along(x, PN.V_REARGLASS(x), PANE_EDGE)


def _loft_z(x, y):
    return S.section_v(x, S.v_at_y_upper(x, y))[1]


def _join_x(y):
    a, b = -2.50, -2.10
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
    def __init__(self):
        xs = [X_PANE_TOP - (X_PANE_TOP + 2.44) * k / 40.0 for k in range(41)]
        edge = [(x,) + tuple(S.section_v(x, _v_edge(x))) for x in xs]
        k_w = max(range(len(edge)), key=lambda k: edge[k][1])
        self.x_w, self.y_w, self.z_w = edge[k_w]
        y_tc = edge[0][1]
        top = [(y_tc * k / 16.0, _loft_z(X_PANE_TOP, y_tc * k / 16.0)) for k in range(16)]
        top += [(e[1], e[2]) for e in edge[:k_w + 1]]
        z_top_full = Curve(_mono(top), mode="pchip")
        low_raw = Curve(_mono(GLASS_LOW), mode="pchip")
        y_max = min(self.y_w, GLASS_LOW[0][0])
        a, b = 0.42, y_max
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
        pts = [(_loft_z(xj + (x1 - xj) * k / float(n), y), xj + (x1 - xj) * k / float(n))
               for k in range(n + 1)]
        z_a, x_a = pts[0]
        z_b = _loft_z(xj + 0.010, y)
        s_a = 0.010 / max(1e-4, z_b - z_a)
        loft = Curve(_mono(pts), mode="pchip")
        z_f = min(Z_FACE, self.z_bot(y))
        x_f = _cap_x(y, z_f)
        s_f = (_cap_x(y, z_f + 0.004) - _cap_x(y, z_f - 0.004)) / 0.008
        h = max(0.010, z_a - z_f)

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
        return x if h is None else x + (h[0][0] - x) * w

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
                n = tuple(-cc for cc in n)
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
    glass = M.grid("VPS_Glass_Rear", _lift(P_.grid(), PANE_LIFT), collection, lib["glass_dark"],
                   geom.away_from((-2.0, 0.0, 1.1)))
    M.mirror_y(glass)
    back = M.grid("VPS_Glass_RearBack", _lift(P_.grid(ny=24, nz=16, z_hi=lambda za: za + 0.03),
                                              -PANE_BACK),
                  collection, lib["shadow"], geom.away_from((-2.0, 0.0, 1.1)))
    M.mirror_y(back)
    return [glass, back]


# --------------------------------------------------------- twin-pod aero roof spoiler
def build_roof_blade(collection, lib):
    """Twin-pod body-coloured outer aero wings (|y| 0.195..0.540) linked by a gloss-black centre bridge."""
    x_s = S.KNEE_X + 0.060
    x_k = S.KNEE_X

    def z_roof(x, y):
        return S.section_v(x, S.v_at_y_upper(x, y))[1]

    made = []
    # 1. Gloss-black centre bridge (|y| 0.000..0.200)
    b_top, b_bot = [], []
    for j in range(11):
        y = 0.200 * j / 10.0
        z_k = z_roof(x_k + 0.02, y)
        m = (z_roof(x_k + 0.02, y) - z_roof(x_s, y)) / (x_k + 0.02 - x_s)
        x_te = PN.X_BLADE + 0.018
        top, bot = [], []
        for i in range(13):
            t = i / 12.0
            x = x_s + (x_te - x_s) * t
            z = z_roof(x, y) if x >= x_k + 0.02 else z_k + m * (x - (x_k + 0.02))
            top.append((x, y, z + 0.002))
            bot.append((x, y, z - 0.008 - 0.006 * t))
        b_top.append(top)
        b_bot.append(bot)
    br = M.grid("VPS_Spoiler_Bridge", b_top, collection, lib["black_gloss"], geom.away_from((-1.8, 0.0, 1.0)))
    M.mirror_y(br)
    br_u = M.grid("VPS_Spoiler_BridgeUnder", b_bot, collection, lib["black_gloss"], geom.away_from((-1.8, 0.0, 2.0)))
    M.mirror_y(br_u)
    made += [br, br_u]

    # 2. Twin painted outer aero wing pods (|y| 0.195..0.540)
    p_top, p_bot = [], []
    for j in range(19):
        u = j / 18.0
        y = 0.195 + (0.540 - 0.195) * u
        z_k = z_roof(x_k + 0.02, y)
        m = (z_roof(x_k + 0.02, y) - z_roof(x_s, y)) / (x_k + 0.02 - x_s)
        x_te = PN.X_BLADE + 0.025 * (u ** 2)
        pod_crown = 0.018 * math.sin(math.pi * min(1.0, max(0.0, u))) ** 0.7
        top, bot = [], []
        for i in range(15):
            t = i / 14.0
            x = (x_s + 0.08) + (x_te - (x_s + 0.08)) * t
            z_base = z_roof(x, y) if x >= x_k + 0.02 else z_k + m * (x - (x_k + 0.02))
            lift = pod_crown * geom.smoothstep(t / 0.55)
            top.append((x, y, z_base + 0.002 + lift))
            bot.append((x, y, z_base - 0.004 - 0.008 * t))
        p_top.append(top)
        p_bot.append(bot)
    pod = M.grid("VPS_Roof_Blade", p_top, collection, lib["paint"], geom.away_from((-1.8, 0.35, 1.0)))
    M.mirror_y(pod)
    M.finish(pod, thickness=0.003, bevel=0.0)
    pod_u = M.grid("VPS_Roof_BladeShadow", p_bot, collection, lib["black_gloss"], geom.away_from((-1.8, 0.35, 2.0)))
    M.mirror_y(pod_u)
    made += [pod, pod_u]

    # Central rear-view ADAS camera bump on the gloss-black bridge (rear_grid u 1920, v 920)
    xc = PN.X_BLADE + 0.022
    zc = z_roof(x_k + 0.02, 0.0) - 0.002
    cam = fittings.rounded_panel("VPS_Spoiler_Camera", (xc, 0.0, zc), 0.022, 0.016, 0.010,
                                 lambda q, d: ((q[0] - d, q[1], q[2]), (-1.0, 0.0, 0.0)),
                                 xc, collection, lib["black_gloss"], d=0.002,
                                 outward=(-1.0, 0.0, 0.0))
    made.append(cam)
    return made


def build_lip(collection, lib):
    P_ = pane()
    n = 40
    y_end = P_.y_w - 0.045
    rows = []
    for i in range(n + 1):
        y = y_end * (1.0 - (1.0 - i / float(n)) ** 1.15)
        zb = P_.z_bot(min(y, P_.y_w - 0.001)) - PANE_CUT
        k = 1.0 - geom.smoothstep((y - 0.28) / (y_end - 0.28))
        h = 0.0075 * (0.30 + 0.70 * k)
        p0 = on_rear(y, zb - 0.018, 0.0004)[0]
        p1 = on_rear(y, zb - 0.0045, h)[0]
        p2 = on_rear(y, zb - 0.0005, 0.0004)[0]
        rows.append([p0, p1, p2])
    ob = M.grid("VPS_Spoiler_Lip", rows, collection, lib["paint"], geom.away_from((-2.30, 0.0, 1.10)))
    M.mirror_y(ob)
    M.finish(ob, thickness=0.0020, bevel=0.0)
    return [ob]


# --------------------------------------------------------- diffuser, reflectors & badges
def build_diffuser(collection, lib):
    made = []
    # Slim red retro-reflector strips inside the outer diffuser arches
    y0, y1, z0, z1 = REFLECTOR
    rows = [[on_tail(y0 + (y1 - y0) * i / 14.0, z, black_stand(0.6) + 0.0020)[0] for z in (z0, z1)]
            for i in range(15)]
    ref = M.grid("VPS_Reflector", rows, collection, lib["reflector"], geom.axial(-1.0))
    M.mirror_y(ref)
    made.append(ref)

    # 7 vertical aero diffuser fins across z 0.365..0.468 (y = 0.000, +/-0.193, +/-0.387, +/-0.580)
    verts, faces = [], []
    d0 = black_stand(0.5) + 0.006
    for y in (0.000, 0.193, -0.193, 0.387, -0.387, 0.580, -0.580):
        k = len(verts)
        for yy in (y - 0.0045, y + 0.0045):
            for z in (0.365, 0.468):
                verts.append(on_tail(yy, z, d0)[0])
        faces.append([k, k + 1, k + 3, k + 2])
    fins = M.obj("VPS_Rear_Fins", verts, faces, collection, lib["black_gloss"])
    M.orient(fins.data, geom.axial(-1.0))
    M.solidify(fins, 0.0040)
    made.append(fins)

    # Rear ultrasonic parking sensors + circular tow-eye cap
    for i, (yy, zz) in enumerate(((0.295, 0.520), (0.655, 0.520), (0.865, 0.595))):
        for s in (1.0, -1.0):
            ps, ns = on_tail(s * yy, zz, black_stand(0.6) + 0.002)
            made += lamps.projector("VPS_Sensor_R_%d_%s" % (i, "L" if s > 0 else "R"), ps, ns, 0.009,
                                    collection, lib, mats=("black_gloss", "lamp_smoked"))
    return made


def build_badges(collection, lib):
    made = []
    cjk, inter = _font("Noto Sans CJK Regular.woff2"), _font("Inter.woff2")

    # Vertical gloss-black rear solid-state LiDAR / camera pill on the tailgate centreline (z 0.992)
    pl, nl = on_tail(0.0, 0.992, 0.0020)
    pill = fittings.rounded_panel("VPS_Rear_LidarPill", pl, 0.011, 0.024, 0.009,
                                  lambda q, d: on_tail(q[1], q[2], 0.0020 + d),
                                  pl[0], collection, lib["black_gloss"], d=0.001,
                                  outward=(-1.0, 0.0, 0.0))
    made.append(pill)

    def badge(name, body, size, y, z, font, mat_key="chrome", **kw):
        p, n = on_tail(y, z, 0.0014)
        t = M.text_mesh(name, body, size, collection, lib[mat_key], extrude=0.0014,
                        font=font, resolution=4, **kw)
        P.on_surface(t, p, n)
        made.append(t)
        return t

    badge("VPS_Badge_Brand", "岚图", 0.044, 0.525, 0.825, cjk, weight=0.0004)
    badge("VPS_Badge_Model", "追光", 0.044, -0.492, 0.825, cjk, weight=0.0004)
    badge("VPS_Badge_SportS", "S", 0.036, -0.556, 0.825, inter, mat_key="badge_red", weight=0.0008)
    return made


def build_all(collection, lib):
    made = []
    made += build_tail(collection, lib)
    made += build_diffuser(collection, lib)
    made += build_lightbar(collection, lib)
    made += build_roof_blade(collection, lib)
    made += build_rear_glass(collection, lib)
    made += build_lip(collection, lib)
    made += build_badges(collection, lib)
    return made
