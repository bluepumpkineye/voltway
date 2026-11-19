"""Denza Z9 rear end, rebuilt from the black car's straight-on rear photograph (c1_0038.jpg, camera
"rear_black" in z9_ref_match; pixels turned into (|y|, z) by z9_cam.rear_yz) and the side photograph's
tail (c1_0036). What the photographs show:

    tail lamps    two long leaf-shaped lenses (the "Time Hourglass"): from the corner, where they wrap
                  onto the quarter, to a POINT 0.13 m either side of the badge; two rows of red hexagon
                  light elements split by a thin grey line, z 0.86-0.97 across
    badge         the round Denza roundel (0.093 m across) on the centreline at z 0.91
    tailgate      body colour, smooth, a crease running from each lamp's outer end down to the bumper;
                  the "Denza Z9" wordmark low on the left, the e3 badge low on the right
    plate tray    a black trapezoid pocket (0.58 wide at its top, 0.52 at its foot) with the plate in it
                  (centre z 0.515) and the reversing camera in a small pod at its top edge
    bumper        a gloss-black upper "eyebrow" that wraps each corner and holds a long reflector (red
                  outer, clear inner, z 0.45) and a parking sensor; under it a matt-black diffuser with a
                  horizontal slot (z 0.33), two vertical red fog lamps side by side in the middle and
                  a thin lip along the bottom (z 0.22)
"""
import math

import z9_surface as S
import z9_nose as N
import z9_cam as CAM
from carkit import geom
from carkit import mesh as M

BODY = N.BODY
TAIL = N.TAIL
CAP_LOW = TAIL.Z_LO + 0.004
CAP_HIGH = TAIL.Z_HI - 0.002
X_PLANE = -2.58


def _at(u, v):
    """(y, z) of a photo pixel ON the tail's centre profile. The tail face slopes (TAIL_X_OF_Z: -2.41 at the ducktail, -2.55
    at the bumper), so the plane the rear camera looks at is the profile's own x at the pixel's height, not one fixed plane:
    the lamps (z 0.9) are 14 cm nearer the lens than the bumper's belly and read 3 % smaller in y."""
    x = -2.50
    for _ in range(4):
        y, z = CAM.rear_yz(u, v, x)
        x = TAIL.X_OF_Z(max(TAIL.Z_LO, min(TAIL.Z_HI, z)))
    return y, z


def _yz(px, x=None):
    out = []
    for (u, v) in px:
        y, z = CAM.rear_yz(u, v, x) if x is not None else _at(u, v)
        out.append((abs(y), z))
    return out


def face(y, z, d=0.0):
    """Point on the tail cap at elevation (y, z) (left half), and normal."""
    z = max(CAP_LOW, min(CAP_HIGH, z))
    w, v = TAIL.wv_at(abs(y), z)
    p, n = TAIL.point(w, v), TAIL.normal(w, v)
    if d:
        p = tuple(p[i] + n[i] * d for i in range(3))
    if y < 0.0:
        p, n = (p[0], -p[1], p[2]), (n[0], -n[1], n[2])
    return p, n


def _lerp(pts, y):
    pts = sorted(pts)
    if y <= pts[0][0]:
        return pts[0][1]
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if y0 <= y <= y1:
            t = 0.0 if y1 == y0 else (y - y0) / (y1 - y0)
            return z0 + (z1 - z0) * t
    return pts[-1][1]


# ------------------------------------------------------------------ hardpoints
# the tail lamp (left half of the picture = the car's left): upper edge, the pointed inner tip, lower edge,
# and the outer end that wraps round the corner
LAMP_TOP_PX = [(1105, 1505), (1150, 1490), (1190, 1472), (1239, 1458), (1368, 1447), (1579, 1437),
               (1737, 1437), (1763, 1450), (1789, 1474)]
LAMP_BOT_PX = [(1789, 1474), (1779, 1490), (1737, 1521), (1658, 1532), (1421, 1542), (1237, 1547),
               (1180, 1558), (1130, 1565), (1105, 1552)]
LAMP_SPLIT_PX = [(1250, 1498), (1500, 1492), (1700, 1488), (1775, 1482)]
BUMPER_TOP = sorted(_yz([(1100, 1790), (1250, 1812), (1380, 1830), (1500, 1832), (1629, 1818)]))
LAMP_POCKET_PX = [(1160, 1870), (1230, 1878), (1500, 1880), (1560, 1895), (1570, 1935), (1480, 1962),
                  (1230, 1962), (1170, 1935)]
REFLECTOR_PX = [(1231, 1929), (1245, 1900), (1290, 1889), (1411, 1887), (1497, 1889), (1480, 1925),
                (1411, 1929)]
SENSORS_PX = [(1190, 1915), (1535, 1895)]
TRAY_PX = [(1628, 1816), (1646, 1950), (1690, 1990), (1920, 2000)]    # left half of the plate tray
SLOT_PX = [(1130, 2093), (1500, 2093), (1850, 2093)]
FOG_PX = [(1882, 2075, 1905, 2142), (1936, 2075, 1960, 2142)]          # two vertical red lamps (u0,v0,u1,v1)
LIP_PX = [(1140, 2168), (1500, 2190), (1920, 2195)]

# 2026-11-15, the bumper's zones. Read off the black car's close-up (c1_0038) and checked on the white car (c1_0046), the purple car
# (c1_0014) and the grey one (c1_0070), where the picture is clearer: the lower valance is BODY COLOUR (it reads dark satin on the
# black car), framed by glossy black "wings" that run from the tailgate's lower edge round both outer corners, a plate pocket
# between them, and under the valance a black chin strip separated by a thin slot. The valance's top edge is W-shaped: ~0.43 at the
# sides, falling to 0.37 under the plate (the plate pocket's floor), and ends at the corner at |y| 0.80.
VALANCE_TOP = sorted(_yz([(1921, 2040), (1700, 2040), (1682, 2040), (1655, 2037), (1639, 2027), (1608, 1998), (1582, 1986),
                          (1497, 1981), (1366, 1981), (1224, 1987), (1187, 1993), (1150, 2014), (1129, 2035)]))
Z_VAL_BOT = _at(1500, 2083)[1]          # the slot between the valance and the chin strip (z ~ 0.323)
Y_VAL_END = 0.772                       # the valance and the chin stop here; the wing's fin carries on to the corner
POCKET_Z = (0.400, 0.592)               # the plate pocket's floor and top (the tailgate's lower edge)
POCKET_Y = (0.268, 0.345)               # its half width at the floor and at the top (the sides slope in, c1_0014)


def val_top(y):
    return _lerp(VALANCE_TOP, min(abs(y), VALANCE_TOP[-1][0]))


def wing_lo(y):
    """The wing's lower edge: the valance's top edge, then (past the valance's end) down the corner as the black fin."""
    t = geom.smoothstep((abs(y) - 0.765) / 0.045)
    return val_top(y) * (1.0 - t) + 0.235 * t


def pocket_mask(y, z):
    """1 inside the plate pocket (a trapezoid narrowing downward), 0 outside, eased over 2.5 cm."""
    f = max(0.0, min(1.0, (z - POCKET_Z[0]) / (POCKET_Z[1] - POCKET_Z[0])))
    half = POCKET_Y[0] + (POCKET_Y[1] - POCKET_Y[0]) * f
    if z <= POCKET_Z[0] - 0.004:
        return 0.0
    # (the dish eases in over 3 cm above the floor's lower edge: a hard edge there was a 5 cm cliff, and the floor under the plate
    # showed as a pale bowl in the viewer)
    return geom.smoothstep((half - abs(y)) / 0.025 + 0.5) * geom.smoothstep((z - (POCKET_Z[0] - 0.004)) / 0.030)


# 2026-11-19, the plate. The tail cap bulges backwards at the plate's height (its plan has a radius of about 0.44 m: the centre
# stands 6 cm behind the plate's ends), and the plate was a flat board standing on the cap's centre normal, which is 10 deg off the
# car's axis (n.y 0.17): it was yawed, its ends floated up to 10 cm off the body and a dark tray showed beside it. Now the pocket
# is dished to a FLAT floor, a plane through the cap at |y| 0.22 (the plate's own edge is 0.24), square to the car and pitched like
# the cap, and the plate lies on it.
PLATE_Y_REF = 0.22
_FLOOR = {}


def floor_plane():
    """x = a + b z: the plate pocket's flat floor (a line fitted to the cap's x at |y| PLATE_Y_REF over the pocket's height)."""
    if not _FLOOR:
        zs = (0.40, 0.46, 0.52, 0.58)
        xs = [face(PLATE_Y_REF, z)[0][0] for z in zs]
        mz, mx = sum(zs) / len(zs), sum(xs) / len(xs)
        b = sum((z - mz) * (x - mx) for z, x in zip(zs, xs)) / sum((z - mz) ** 2 for z in zs)
        _FLOOR.update(a=mx - b * mz, b=b)
    return _FLOOR


def floor_x(z):
    f = floor_plane()
    return f["a"] + f["b"] * z


def floor_normal():
    """The floor's outward normal: back (-x) and a little down, no yaw."""
    b = floor_plane()["b"]
    L = math.sqrt(1.0 + b * b)
    return (-1.0 / L, 0.0, b / L)


def pocket_off(y, z):
    """The wing band's offset along the cap normal (negative = into the body) that dishes the pocket to the flat floor: the cap
    moves forward to the floor's x by the pocket mask's weight (1 in the pocket, easing out over 2.5 cm). Where the cap is already
    at or inside the floor (the pocket's outer ends) nothing moves."""
    m = pocket_mask(y, z)
    if m <= 0.0:
        return 0.0
    p, n = face(y, z)
    dx = floor_x(z) - p[0]
    if dx <= 0.0 or n[0] > -0.2:
        return 0.0
    return m * dx / n[0]


Z_LAMP_TOP, Z_LAMP_BOT = 0.971, 0.860
Z_ROUNDEL = _at(1924, 1495)[1]
Z_PLATE = 0.515


def bumper_top(y):
    if y <= BUMPER_TOP[-1][0]:
        return _lerp(BUMPER_TOP, y)
    return BUMPER_TOP[-1][1] + (y - BUMPER_TOP[-1][0]) * 0.35


LAMP_TOP = sorted(_yz(LAMP_TOP_PX))
LAMP_BOT = sorted(_yz(LAMP_BOT_PX))
GAP = 0.0042


def lamp_top(y):
    return _lerp(LAMP_TOP, y)


def lamp_bot(y):
    return _lerp(LAMP_BOT, y)


# ----------------------------------------------------------- band construction
_GRID = {}


def _grid():
    """The tail cap sampled on a (w, v) grid, as arrays of its (y, z): the robust inverse's first guess."""
    if not _GRID:
        import numpy as np
        ws = np.linspace(0.0, 1.0, 65)
        vs = np.linspace(0.0, 1.0, 129)
        W, V = np.meshgrid(ws, vs)
        P = np.array([[TAIL.point(float(w), float(v)) for w in ws] for v in vs])
        _GRID.update(W=W.ravel(), V=V.ravel(), Y=P[:, :, 1].ravel(), Z=P[:, :, 2].ravel())
    return _GRID


def wv_of(y, z):
    """(w, v, miss) of the tail cap point nearest the elevation position (y, z): a grid search then a
    2-D Newton polish. wv_at bisects on height assuming z rises with v at constant w, which it does not
    round the corner under the backlight, where it lands on the flank 20 cm off; `miss` is the distance
    (m) between the point found and (y, z), > 1 mm where the cap does not reach that position."""
    import numpy as np
    G = _grid()
    k = int(np.argmin((G["Y"] - y) ** 2 + (G["Z"] - z) ** 2))
    w, v = float(G["W"][k]), float(G["V"][k])
    for _ in range(8):
        p = TAIL.point(w, v)
        fy, fz = p[1] - y, p[2] - z
        if abs(fy) < 2e-5 and abs(fz) < 2e-5:
            break
        h = 1e-4
        pw = TAIL.point(min(1.0, w + h), v)
        pv = TAIL.point(w, min(1.0, v + h))
        a11, a21 = (pw[1] - p[1]) / h, (pw[2] - p[2]) / h
        a12, a22 = (pv[1] - p[1]) / h, (pv[2] - p[2]) / h
        det = a11 * a22 - a12 * a21
        if abs(det) < 1e-9:
            break
        dw = (a22 * fy - a12 * fz) / det
        dv = (-a21 * fy + a11 * fz) / det
        w = min(1.0, max(0.0, w - dw))
        v = min(1.0, max(0.0, v - dv))
    p = TAIL.point(w, v)
    return w, v, math.hypot(p[1] - y, p[2] - z)


def wv(y, z):
    """(w, v) of the cap point at (y, z): wv_at where it lands, wv_of where it does not."""
    w, v = TAIL.wv_at(y, z)
    p = TAIL.point(w, v)
    if abs(p[2] - z) > 0.006 or abs(p[1] - y) > 0.006:
        w, v, _ = wv_of(y, z)
    return w, v


_ZTOP = {}


def _reach_at(i):
    """z_reach on the 20 mm grid: the highest z (up to CAP_HIGH) at which the cap exists at y."""
    hit = _ZTOP.get(i)
    if hit is None:
        y = 0.02 * i
        z = CAP_HIGH
        while z > CAP_LOW and wv_of(y, z)[2] > 0.0015:
            z -= 0.004
        hit = z
        _ZTOP[i] = hit
    return hit


def z_reach(y):
    """The highest elevation at which the tail cap exists at |y| (below CAP_HIGH): past the width of the
    backlight's foot the cap's top edge falls away round the corner, along the join ring."""
    f = abs(y) / 0.02
    i = int(f)
    a, b = _reach_at(i), _reach_at(i + 1)
    return a + (b - a) * (f - i)


def edge_y(z):
    """Half-width of the tail cap at height z: where it meets the quarter (the join ring)."""
    return TAIL.half_width(max(CAP_LOW, min(CAP_HIGH, z))) * 0.9995


def band(name, zlo, zhi, ny, nz, collection, mat, offset=0.0, thickness=M.SKIN, y_max=None, ymin=0.0,
         off_fn=None, bevel=0.0, cut=False, hold=False):
    """A strip of the tail cap between z-limits that depend on |y|: zlo(y), zhi(y).

    y_max None: a full-width band, whose side edge follows the cap's join ring (the quarter panel's edge) at every
    height, the columns sliding in where the cap is narrower: a band with one constant width stopped short of the ring
    where the cap is wider (a dark slit down the corner) and spilled onto the flank where it is narrower (a flap)."""
    cols = []
    if y_max is None:
        zs = [zlo(0.4) + (zhi(0.4) - zlo(0.4)) * k / 12.0 for k in range(13)]
        ymax = max(edge_y(z) for z in zs)
    else:
        ymax = y_max
    if cut:
        # a band that sits on the cap's top edge (the ducktail's lip) ends where that edge falls below its lower
        # limit (round the corner, with the join ring), and is held under the edge elsewhere
        y_cut = ymax
        while y_cut > ymin + 0.02 and z_reach(y_cut) - 0.002 < zlo(y_cut) + 0.008:
            y_cut -= 0.005
        ymax = min(ymax, y_cut)

    def row_z(y, fr):
        # hold: the band's top is kept under the cap's own top edge (it does not end there, as a cut band does)
        z1 = min(zhi(y), z_reach(y) - 0.002) if (cut or hold) else zhi(y)
        z0 = min(zlo(y), z1 - 0.004) if (cut or hold) else zlo(y)
        return max(CAP_LOW, min(CAP_HIGH, z0 + (z1 - z0) * fr))

    for i in range(ny + 1):
        s = i / float(ny)
        s = 1.0 - (1.0 - s) ** 1.30
        col = []
        for k in range(nz + 1):
            fr = k / float(nz)
            y = ymin + (ymax - ymin) * s
            z = row_z(y, fr)
            if y_max is None:
                for _ in range(3):                  # the column's y depends on the height it lands at
                    y = ymin + (edge_y(z) - ymin) * s
                    z = row_z(y, fr)
            w, v = wv(y, z) if (cut or hold) else TAIL.wv_at(y, z)
            d = off_fn(y, fr) if off_fn else offset
            pt = TAIL.offset(w, v, d) if d else TAIL.point(w, v)
            if i == 0 and ymin == 0.0 and d:
                # the cap's normal on the centre line is one-sided (n.y 0.17): an offset there slid the column off the
                # centre plane and the mirrored halves met in a crease down the dished pocket
                pt = (pt[0], 0.0, pt[2])
            col.append(pt)
        cols.append(col)
    ob = M.mesh_from_rows(name, cols, collection)
    M.orient(ob.data, geom.axial(-1.0))
    ob.data.materials.append(mat)
    M.mirror_y(ob)
    M.finish(ob, thickness=thickness, bevel=bevel)
    return ob


def _loop3(yz, d=0.0):
    return [face(y, z, d)[0] for (y, z) in yz]


def _flat(name, loop, collection, mat, thickness=0.002, outward=(-1.0, 0.0, 0.0), mirror=True):
    n = len(loop)
    ob = M.obj(name, loop, [list(range(n))], collection, mat)
    M.orient(ob.data, lambda cc, o=outward: o)
    if thickness:
        M.solidify(ob, thickness)
    if mirror:
        M.mirror_y(ob)
    return ob


def _tunnel(name, loop, d, depth, collection, mat, taper=0.9):
    c = [sum(p[i] for p in loop) / len(loop) for i in range(3)]
    rows = [[tuple(p[i] + d[i] * 0.003 for i in range(3)) for p in loop]]
    for t in (0.5, 1.0):
        k = 1.0 + (taper - 1.0) * t
        rows.append([tuple(c[i] + (p[i] - c[i]) * k - d[i] * depth * t for i in range(3)) for p in loop])
    back = [sum(p[i] for p in rows[-1]) / len(loop) for i in range(3)]
    rows.append([tuple(back[i] + (p[i] - back[i]) * 0.02 for i in range(3)) for p in rows[-1]])
    cols = [[rows[r][k] for r in range(len(rows))] for k in range(len(loop))]
    cols.append(cols[0])
    ob = M.mesh_from_rows(name, cols, collection)
    ob.data.materials.append(mat)
    return ob


def swell(y, z):
    """The diffuser's convex belly (m): the lower bumper is not a flat slab (c1_0038 / c1_0037: soft highlights roll over it).
    Zero at the band's top (z 0.434, where it meets the black eyebrow) and bottom (0.20), 11 mm at its middle, fading to the sides."""
    t = (z - 0.20) / (0.434 - 0.20)
    if t <= 0.0 or t >= 1.0:
        return 0.0
    return 0.011 * math.sin(math.pi * t) ** 0.8 * max(0.0, 1.0 - (y / 0.92) ** 2)


# ------------------------------------------------------------------ the tail
def build_tail(collection, lib):
    made = []
    # the upper tail: everything above the lamps' lower edge, under the ducktail lip
    made.append(band("Z9_Tail_Upper", lambda y: lamp_bot(min(y, 0.82)) - 0.0005, lambda y: CAP_HIGH, 56, 8,
                     collection, lib["paint"], hold=True))
    # the tailgate: from the bumper's top edge to the lamps (a slim gap above the bumper)
    made.append(band("Z9_Tailgate", lambda y: bumper_top(y) + 0.5 * GAP, lambda y: lamp_bot(min(y, 0.82)) - 0.5 * GAP,
                     56, 14, collection, lib["paint"]))
    # the gloss-black WINGS: from the tailgate's lower edge down to the valance's W-shaped top edge, and past the valance's end
    # down the corner as a fin; the plate pocket is dished into them (12 mm, a trapezoid narrowing downward)
    made.append(band("Z9_Bumper_Upper", wing_lo, lambda y: bumper_top(y) + 0.001, 64, 8, collection,
                     lib["wing"], thickness=0.004,
                     off_fn=lambda y, fr: pocket_off(y, wing_lo(y) + fr * (bumper_top(y) + 0.001 - wing_lo(y)))))
    # the BODY-COLOUR valance under the plate and across the tail, with its convex belly
    made.append(band("Z9_Bumper_Valance", lambda y: Z_VAL_BOT + 0.003, val_top, 44, 7, collection, lib["paint"],
                     thickness=0.004, y_max=Y_VAL_END,
                     off_fn=lambda y, fr: swell(y, (Z_VAL_BOT + 0.003) + fr * (val_top(y) - Z_VAL_BOT - 0.003))))
    # the black chin strip under it (satin), its top edge the slot
    made.append(band("Z9_Bumper_Lower", lambda y: CAP_LOW, lambda y: Z_VAL_BOT - 0.006, 56, 8, collection,
                     lib["diffuser"], thickness=0.004, y_max=Y_VAL_END,
                     off_fn=lambda y, fr: swell(y, CAP_LOW + fr * (Z_VAL_BOT - 0.006 - CAP_LOW))))
    return made


# ---------------------------------------------------------- tail lamps
def block(name, corners, ny, nz, collection, mat, off, thickness=0.002):
    """A quadrilateral patch on the tail cap. corners = [(y, z) bottom-left, bottom-right, top-right, top-left] in the
    elevation plane (the left half, y >= 0); the grid between them is bilinear and every point is put on the cap (wv) and
    lifted along its normal by off (a number, or a function of (s, t) across and up the block)."""
    (yb0, zb0), (yb1, zb1), (yt1, zt1), (yt0, zt0) = corners
    cols = []
    for i in range(ny + 1):
        s = i / float(ny)
        col = []
        for k in range(nz + 1):
            t = k / float(nz)
            yl, yr = yb0 + (yt0 - yb0) * t, yb1 + (yt1 - yb1) * t
            zb, zt = zb0 + (zb1 - zb0) * s, zt0 + (zt1 - zt0) * s
            y, z = yl + (yr - yl) * s, zb + (zt - zb) * t
            w, v = wv(y, z)
            d = off(s, t) if callable(off) else off
            col.append(TAIL.offset(w, v, d) if d else TAIL.point(w, v))
        cols.append(col)
    ob = M.mesh_from_rows(name, cols, collection)
    M.orient(ob.data, geom.axial(-1.0))
    ob.data.materials.append(mat)
    M.mirror_y(ob)
    M.finish(ob, thickness=thickness, bevel=0.0)
    return ob


# The photographed lamp (c1_0038 / c1_0037 close-ups): ONE smoked-red leaf from the pointed tip beside the roundel (y 0.137) to
# the tailgate's side shut line (y 0.704), split along its length by a thin grey bar; in each half a row of pale red cells,
# wide-topped (V) in the upper row and wide-bottomed (A) in the lower, so a pair makes an hourglass; past the shut line a
# separate wrap-round piece (two strips, the lower with a bright red line along its foot) turns the corner onto the quarter.
Y_TIP, Y_RIB, Y_END = 0.125, 0.704, 0.842
CELLS_Y = [(0.575, 0.668), (0.410, 0.515), (0.225, 0.350), (0.146, 0.204)]      # cells along the leaf, outer to inner
BAR = 0.0036


def _split(y):
    return lamp_bot(y) + 0.52 * (lamp_top(y) - lamp_bot(y))


def build_lamps(collection, lib):
    made = []

    def lb(name, zlo, zhi, mat, off, y0, y1, ny, nz=2, thickness=0.002):
        return band(name, zlo, zhi, ny, nz, collection, mat, off_fn=off, ymin=y0, y_max=y1, thickness=thickness)

    bulge = lambda y, k: 0.0030 * math.sin(math.pi * k) + 0.0010
    zu_lo = lambda y: _split(y) + BAR
    zu_hi = lambda y: lamp_top(y) - 0.003
    zl_lo = lambda y: lamp_bot(y) + 0.003
    zl_hi = lambda y: _split(y) - BAR

    # the housing: a gloss-black pocket the shape of the leaf (its rim shows round the lens)
    made.append(lb("Z9_Tail_Lamp_Back", lambda y: lamp_bot(y), lambda y: lamp_top(y), lib["black_gloss"],
                   lambda y, k: -0.004, 0.12, Y_END, 80, thickness=0.003))
    # the main leaf: two lens strips and the bar between them
    for tag, lo, hi in (("U", zu_lo, zu_hi), ("L", zl_lo, zl_hi)):
        made.append(lb("Z9_Tail_Lamp_Lens_" + tag, lo, hi, lib["lamp_smoke"], bulge, Y_TIP - 0.004, Y_RIB - 0.004, 60))
        made.append(lb("Z9_Tail_Lamp_Wrap_" + tag, lo, hi, lib["lamp_smoke"], bulge, Y_RIB + 0.008, Y_END, 14))
    made.append(lb("Z9_Tail_Lamp_Bar", lambda y: _split(y) - BAR, lambda y: _split(y) + BAR, lib["paint"],
                   lambda y, k: 0.0036, Y_TIP, Y_END, 80, nz=1))
    # the cells: four a row, the upper row V-shaped (wide at the top), the lower A-shaped
    slant = 0.020
    for k, (ya, yb) in enumerate(CELLS_Y):
        for row in ("U", "L"):
            lo, hi = (zu_lo, zu_hi) if row == "U" else (zl_lo, zl_hi)
            zlo = lambda y, lo=lo: lo(y) + 0.0065
            zhi = lambda y, hi=hi: hi(y) - 0.0065
            d = min(slant, 0.4 * (yb - ya))
            if row == "U":
                c = [(ya + d, zlo(ya + d)), (yb - d, zlo(yb - d)), (yb, zhi(yb)), (ya, zhi(ya))]
            else:
                c = [(ya, zlo(ya)), (yb, zlo(yb)), (yb - d, zhi(yb - d)), (ya + d, zhi(ya + d))]
            made.append(block("Z9_Tail_Cell_%s%d" % (row, k), c, 7, 2, collection, lib["led_red"], 0.0060,
                              thickness=0.0015))
    # the wrap piece: a pale cell in the upper strip and the bright red line along the lower strip's foot
    yw0, yw1 = Y_RIB + 0.020, Y_END - 0.060
    made.append(block("Z9_Tail_Cell_WU", [(yw0, zu_lo(yw0) + 0.007), (yw1, zu_lo(yw1) + 0.007), (yw1, zu_hi(yw1) - 0.007),
                                          (yw0, zu_hi(yw0) - 0.007)], 5, 2, collection, lib["led_red"], 0.0060,
                      thickness=0.0015))
    made.append(block("Z9_Tail_Cell_WL", [(yw0, zl_lo(yw0) + 0.004), (yw1, zl_lo(yw1) + 0.004), (yw1, zl_lo(yw1) + 0.011),
                                          (yw0, zl_lo(yw0) + 0.011)], 5, 1, collection, lib["led_red"], 0.0060,
                      thickness=0.0015))
    return made


# ------------------------------------------------- roundel, plate tray, camera
def build_badges(collection, lib):
    """The Denza emblem on the tailgate (z9_logo: black ring, silver disc with the hourglass opening, blue enamel), 93 mm across
    (c1_0046: 0.19 of the 480 mm plate sign's width), centred on the car's axis at the lamps' height."""
    import z9_logo as LG
    p, n = face(0.0, Z_ROUNDEL, 0.0)
    centre = tuple(p[i] - n[i] * 0.0015 for i in range(3))
    return LG.build("Z9_Roundel_", collection, lib, centre, n, 0.0465)


def build_plate_tray(collection, lib):
    from carkit.parts import fittings
    made = []
    # (the black trapezoid pocket is dished into the bumper's wing band now, to a flat floor: pocket_off)
    half = _yz(TRAY_PX)
    zt, zb = half[0][1], half[-1][1]
    # the plate: a flat board square to the car, lying on the floor (7 mm proud of it, its 8 mm body sunk 1 mm into the skin), on a
    # black mount block that fills the 1 cm between its back and the cap where the cap is inside the floor (the plate's ends)
    n = floor_normal()
    p_floor = (floor_x(Z_PLATE), 0.0, Z_PLATE)
    p_front = tuple(p_floor[i] + n[i] * 0.007 for i in range(3))
    p_mount = tuple(p_floor[i] + n[i] * 0.001 for i in range(3))
    made += fittings.plate("Z9_Plate_Mount_Rear", p_mount, n, collection, lib, w=0.490, h=0.156, depth=0.022,
                           mat="black_gloss", bevel=(0.003, 2, 30))
    made += fittings.plate("Z9_Plate_Rear", p_front, n, collection, lib, w=0.480, h=0.148, depth=0.008,
                           texts=[("DENZA Z9", 0.0, 0.038, False, True)],
                           mat="black_gloss", text_mat="machined")
    # the reversing camera: a small black pod at the tray's top edge with two lenses
    zc = zt + 0.004
    made.append(band("Z9_Camera_Pod", lambda y: zc - 0.012, lambda y: zc + 0.016, 14, 3, collection, lib["black_gloss"],
                      offset=0.012, y_max=0.060, thickness=0.004))
    for dy in (0.012, -0.026):
        pp, nn = face(dy, zc, 0.0145)
        made += _disc("Z9_Camera_Lens", pp, nn, 0.0085, collection, lib["lamp_smoked"], 0.002)
    return made


def _disc(name, p, n, r, collection, mat, h, seg=20):
    from mathutils import Vector
    nv = Vector(n).normalized()
    up = Vector((0, 0, 1)) if abs(nv.z) < 0.9 else Vector((1, 0, 0))
    t1 = nv.cross(up).normalized()
    t2 = nv.cross(t1).normalized()
    c0, c1 = Vector(p), Vector(p) + nv * h
    verts = [tuple(c1)]
    for i in range(seg):
        a = 2 * math.pi * i / seg
        verts.append(tuple(c1 + (t1 * math.cos(a) + t2 * math.sin(a)) * r))
    for i in range(seg):
        a = 2 * math.pi * i / seg
        verts.append(tuple(c0 + (t1 * math.cos(a) + t2 * math.sin(a)) * r))
    faces = [[0, 1 + i, 1 + (i + 1) % seg] for i in range(seg)]
    for i in range(seg):
        a, b = 1 + i, 1 + (i + 1) % seg
        faces.append([a, a + seg, b + seg, b])
    ob = M.obj(name, verts, faces, collection, mat)
    M.orient(ob.data, lambda cc, c=tuple(c0), d=tuple(nv): (cc[0] - c[0] + d[0] * 0.01, cc[1] - c[1] + d[1] * 0.01,
                                                                    cc[2] - c[2] + d[2] * 0.01))
    return [ob]


# ------------------------------------------------------- bumper details
def build_bumper(collection, lib):
    made = []
    # the long reflector in its pocket: red outer, clear inner
    pocket = _loop3(sorted(_yz(LAMP_POCKET_PX), key=lambda p: math.atan2(p[1] - 0.45, p[0] - 0.5)), 0.001)
    tun = _tunnel("Z9_Reflector_Pocket", pocket, (-1.0, 0.0, 0.0), 0.05, collection, lib["cap_black"], taper=0.95)
    M.mirror_y(tun)
    made.append(tun)
    # the long lamp in its slot: a red outer part and, inboard of it, the reversing lamp's clear lens (c1_0038: red
    # u 1231-1413, clear 1413-1497 px)
    red = _yz([(1231, 1929), (1245, 1900), (1290, 1889), (1411, 1887), (1414, 1929)])
    clear = _yz([(1414, 1887), (1497, 1889), (1480, 1925), (1414, 1929)])
    made.append(_flat("Z9_Reflector", _loop3(red, 0.0045), collection, lib["led_red"], 0.002))
    made.append(_flat("Z9_Reflector_Clear", _loop3(clear, 0.0045), collection, lib["lamp_white"], 0.002))
    # parking sensors
    for k, (u, v) in enumerate(SENSORS_PX):
        y, z = _at(u, v)
        p, n = face(abs(y), z, 0.0)
        made += _disc("Z9_Sensor_%d" % k, p, n, 0.0125, collection, lib["cap_black"], 0.003)
        q, m_ = face(-abs(y), z, 0.0)
        made += _disc("Z9_Sensor_R%d" % k, q, m_, 0.0125, collection, lib["cap_black"], 0.003)
    # the horizontal slot across the diffuser
    # (c1_0038: a thin dark slot runs from the fog lamps' housings to the corner, between the valance and the chin strip)
    made.append(band("Z9_Diffuser_Slot", lambda y: Z_VAL_BOT - 0.006, lambda y: Z_VAL_BOT + 0.003, 70, 1, collection,
                     lib["shadow"], off_fn=lambda y, fr: -0.005 + swell(y, Z_VAL_BOT), ymin=0.07, y_max=Y_VAL_END + 0.004,
                     thickness=0.002))
    # the two vertical fog lamps side by side in the middle
    for k, (u0, v0, u1, v1) in enumerate(FOG_PX):
        ya, za = _at(u0, v0)
        yb, zb = _at(u1, v1)
        yc = 0.5 * (ya + yb)
        hy = 0.5 * abs(yb - ya)
        # a black housing and the red lens inside it
        zm = 0.5 * (za + zb)
        made.append(band("Z9_Fog_House_%d" % k, lambda y, zb=zb: zb - 0.012, lambda y, za=za: za + 0.012, 2, 4,
                         collection, lib["black_gloss"], offset=0.006 + swell(0.0, zm),
                         ymin=max(0.0, abs(yc) - hy - 0.012), y_max=abs(yc) + hy + 0.012, thickness=0.003))
        made.append(band("Z9_Fog_Lens_%d" % k, lambda y, zb=zb: zb, lambda y, za=za: za, 2, 4, collection,
                         lib["led_red"], offset=0.0085 + swell(0.0, zm), ymin=max(0.0, abs(yc) - hy),
                         y_max=abs(yc) + hy, thickness=0.002))
    # (the separate dark lip band under the chin is gone: it hung like a tray with square ends; the chin strip's own lower edge
    # is the lip, as in c1_0038)
    # the silver tips at the chin strip's lower outer corners (c1_0038: a pointed sliver where the strip ends at the tyre)
    made.append(band("Z9_Chin_Tip", lambda y: 0.222, lambda y: 0.234, 10, 1, collection, lib["trim_chrome"],
                     off_fn=lambda y, fr: 0.011 * (1.0 - geom.smoothstep((y - 0.70) / 0.14)) + 0.002, ymin=0.70, y_max=0.84,
                     thickness=0.002))
    # the small pictogram label (an open boot with an arrow) at the tailgate's lower edge, 0.20 m to the car's right (c1_0046,
    # c1_0014): a dark plaque with two silver strokes
    zb, yb = 0.620, -0.200
    plaque = [(yb + 0.016, zb - 0.0075), (yb - 0.016, zb - 0.0075), (yb - 0.016, zb + 0.0075), (yb + 0.016, zb + 0.0075)]
    made.append(_flat("Z9_Label_Boot", _loop3(plaque, 0.0030), collection, lib["black_gloss"], 0.002, mirror=False))
    for k, (dy, w_) in enumerate(((0.007, 0.0090), (-0.006, 0.0050))):
        stroke = [(yb + dy + w_, zb - 0.0020), (yb + dy - w_, zb - 0.0020), (yb + dy - w_, zb + 0.0028),
                  (yb + dy + w_, zb + 0.0028)]
        made.append(_flat("Z9_Label_Boot_Mark_%d" % k, _loop3(stroke, 0.0044), collection, lib["trim_chrome"], 0.0008,
                          mirror=False))
    return made


# ------------------------------------------------------------- lettering
def _font(fn):
    import os
    import bpy
    d = os.path.join(os.path.dirname(bpy.app.binary_path), bpy.app.version_string.rsplit(".", 1)[0],
                     "datafiles", "fonts")
    try:
        return bpy.data.fonts.load(os.path.join(d, fn), check_existing=True)
    except Exception as e:
        print("font %s not loaded (%s)" % (fn, e))
        return None


def _on_surface(ob, p, n):
    from carkit import place as P
    P.on_surface(ob, p, n)


def build_lettering(collection, lib):
    made = []
    inter, cjk = _font("Inter.woff2"), _font("Noto Sans CJK Regular.woff2")
    for name, text, u, v, size, fnt in (("Z9_Badge_Model", "腾势Z9", 1432, 1732, 0.030, cjk),
                                        ("Z9_Badge_E3", "e³", 2410, 1732, 0.026, inter)):
        y, z = _at(u, v)
        p, n = face(y, z, 0.0012)
        t = M.text_mesh(name, text, size, collection, lib["trim_chrome"], extrude=0.0012, font=fnt, resolution=4)
        _on_surface(t, p, n)
        made.append(t)
    return made


# ------------------------------------------------------------ ducktail lip
def build_ducktail(collection, lib):
    """The slim spoiler lip across the top of the tail (the side photograph's tip at z 1.0)."""
    # (2026-11-15: it ends at the lid's side shut line (y 0.70) and fades to nothing there, as the photographed lip does:
    # the old one ran on to y 0.86 round the corner, where the cap's top edge falls away, and crumpled into a flap)
    return [band("Z9_Ducktail_Lip", lambda y: CAP_HIGH - 0.012, lambda y: CAP_HIGH, 40, 2, collection, lib["paint"], hold=True,
                 off_fn=lambda y, k: 0.008 * k * (1.0 - geom.smoothstep((y - 0.30) / 0.40)) + 0.001, y_max=0.70, thickness=0.003)]


def build_deck(collection, lib):
    """The rear deck: the cap's top sheet, from the tail's upper edge (z_hi on the centreline) up and forward to the
    join ring under the rear glass. No panel covered it (the tail bands stop at z_hi, the decklid starts at the
    ring), so the dark hull showed there as a black band across the car; in the photographs (c1_0014..) it is
    body colour. The sheet is the cap's own surface over v from where the ring reaches z_hi up to v = 1."""
    S_ = S.BODY
    v_a = 0.0
    for k in range(401):
        v = k / 400.0
        if S_.section_v(TAIL.JOIN(v), v)[1] >= CAP_HIGH - 0.012:
            v_a = v
            break
    nw, nv = 36, 24
    cols = []
    for i in range(nw + 1):
        w = i / float(nw)
        w = 1.0 - (1.0 - w) ** 1.25                   # packed toward the corner
        cols.append([TAIL.offset(w, v_a + (1.0 - v_a) * j / float(nv), 0.0006) for j in range(nv + 1)])
    ob = M.mesh_from_rows("Z9_Rear_Deck", cols, collection)
    M.orient(ob.data, geom.axial(-1.0))
    ob.data.materials.append(lib["paint"])
    M.mirror_y(ob)
    M.finish(ob, thickness=M.SKIN, bevel=0.0)
    return [ob]


# ------------------------------------------------------------- build all
def build_all(collection, lib):
    made = []
    made += build_tail(collection, lib)
    made += build_lamps(collection, lib)
    made += build_badges(collection, lib)
    made += build_plate_tray(collection, lib)
    made += build_bumper(collection, lib)
    made += build_lettering(collection, lib)
    # (2026-11-15: the separate ducktail lip is gone: its crumpled ends read as a flap; the deck's own trailing edge is the lip)
    made += build_deck(collection, lib)
    return made
