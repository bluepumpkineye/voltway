"""XPeng G9L rear end: the tail lamp cap and its light strips, the tailgate, the painted bumper
top, the black lower bumper with its reflectors, vents, louvred panel and satin blade, the roof
spoiler, lettering, the plate and the camera.

Hardpoints are read off the straight-on rear photograph of the white car (c1_0030.jpg, camera
"rear_white") in PIXELS and turned into (|y|, z) by g9l_cam.rear_yz; parts are built as BANDS of the
tail cap between z-limits that vary across the car (band()), so every panel follows the cap. What
the photographs (c1_0005/0006/0029/0030/0031) show:

    lamp cap      a black shelf across the top of the tailgate, z 1.145-1.27, standing 45 mm proud
                  of the tailgate at its lower edge (it overhangs it), with a thin red light strip
                  at z 1.226 and a fainter one at 1.19, wrapping the corners to the quarter
    tailgate      painted, down to a shallow "smile" shut line (z 0.749 at the centre, 0.87 at the
                  corners), carrying the spaced XPENG wordmark (z 1.086), the camera above the plate
                  (centre z 0.87) and the badges
    bumper        a painted strip under the gate (z 0.652 down to the black), then a black lower
                  bumper holding two reflectors (z 0.58-0.61), a vent slot at each corner, a
                  louvred central panel and a satin blade along the bottom
    spoiler       a black overhang from the roof's trailing edge, swept at its ends
"""
import math

import g9l_surface as S
import g9l_nose as N
import g9l_cam as CAM
from carkit import geom
from carkit import mesh as M

BODY = N.BODY
TAIL = N.TAIL
CAP_LOW = TAIL.Z_LO + 0.004
CAP_HIGH = TAIL.Z_HI - 0.002


def _yz(px, x=-2.54):
    out = []
    for (u, v) in px:
        y, z = CAM.rear_yz(u, v, x)
        out.append((abs(y), z))
    return out


def face(y, z, d=0.0):
    """Point on the tail cap at elevation (y, z) (left half), and normal."""
    z = max(CAP_LOW, min(CAP_HIGH, z))
    w, v = TAIL.wv_at(abs(y), z)
    if abs(TAIL.point(w, v)[2] - z) > 0.001:
        w, v, _ = wv_of(abs(y), z)
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


# --------------------------------------------------------------- hardpoints
Z_CAP_BOT = 1.147                      # the lamp cap's lower edge across the car
Z_LAMP_RED = (1.226, 1.188)            # the two light strips
CAP_END = 0.785                        # |y| where the lamp shelf and its lip end (see build_tail)
GATE_LOW = sorted(_yz(CAM.GATE_LOW_PX))                       # tailgate's lower edge (y, z)
BUMPER_TOP = sorted(_yz(CAM.REAR_BUMPER_TOP_PX))              # black bumper's top edge (y, z)
REFLECTOR = _yz(CAM.REFLECTOR_PX)
VENT = _yz(CAM.REAR_VENT_PX)
GAP = 0.0042


def gate_low(y):
    if y <= GATE_LOW[-1][0]:
        return _lerp(GATE_LOW, y)
    return GATE_LOW[-1][1] + (y - GATE_LOW[-1][0]) * 1.2


def bumper_top(y):
    """z of the black bumper's top edge: 0.652 at the centre, 0.582 at the corner (y 0.81), then
    falling away along the flank toward the diagonal that runs forward to the arch."""
    if y <= BUMPER_TOP[-1][0]:
        return _lerp(BUMPER_TOP, y)
    return BUMPER_TOP[-1][1] - (y - BUMPER_TOP[-1][0]) * 0.9


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


def band(name, zlo, zhi, ny, nz, collection, mat, offset=0.0, thickness=M.SKIN, y_max=None,
         off_fn=None, ymin=0.0, bevel=0.0, cut=False):
    """A strip of the tail cap between z-limits that depend on |y|: zlo(y), zhi(y), the upper limit
    held under the cap's own top edge (z_reach).

    y_max None: a full-width band, whose side edge follows the cap's join ring (the quarter panel's
    edge) at every height, the columns sliding in where the cap is narrower. Otherwise the band ends
    at the constant y_max.
    off_fn(y, k) overrides `offset` (a shelf that stands proud by a varying amount)."""
    cols = []
    if y_max is None:
        zs = [zlo(0.4) + (zhi(0.4) - zlo(0.4)) * k / 12.0 for k in range(13)]
        ymax = max(edge_y(z) for z in zs)
    else:
        ymax = y_max
    if cut:
        # a band that sits near the cap's top edge (the lamp shelf, the light strips) ends where that
        # edge falls below its lower limit (round the corner, with the join ring), instead of sliding
        # down the corner as a sliver
        y_cut = ymax
        while y_cut > ymin + 0.02 and z_reach(y_cut) - 0.002 < zlo(y_cut) + 0.035:
            y_cut -= 0.005
        ymax = min(ymax, y_cut)

    def row_z(y, fr):
        z1 = min(zhi(y), z_reach(y) - 0.002) if cut else zhi(y)
        z0 = min(zlo(y), z1 - 0.004)
        return max(CAP_LOW, min(CAP_HIGH, z0 + (z1 - z0) * fr))

    for i in range(ny + 1):
        s = i / float(ny)
        s = 1.0 - (1.0 - s) ** 1.30               # columns packed toward the corner
        col = []
        for k in range(nz + 1):
            fr = k / float(nz)
            y = ymin + (ymax - ymin) * s
            z = row_z(y, fr)
            if y_max is None:
                for _ in range(3):                  # the column's y depends on the height it lands at
                    y = ymin + (edge_y(z) - ymin) * s
                    z = row_z(y, fr)
            w, v = wv(y, z) if cut else TAIL.wv_at(y, z)
            d = off_fn(y, fr) if off_fn else offset
            col.append(TAIL.offset(w, v, d) if d else TAIL.point(w, v))
        cols.append(col)
    ob = M.mesh_from_rows(name, cols, collection)
    M.orient(ob.data, geom.axial(-1.0))
    ob.data.materials.append(mat)
    M.mirror_y(ob)
    M.finish(ob, thickness=thickness, bevel=bevel)
    return ob


# ------------------------------------------------------------------ the tail
def build_tail(collection, lib):
    made = []
    zt = CAP_HIGH
    # the lamp cap: a black shelf, proud of the tailgate by 45 mm at its lower edge, 12 mm under the glass
    # (the shelf stops at CAP_END: beyond it the columns that follow the join ring snap to cap points 8 cm below the shelf
    # and the end of the band slid down the corner as a wedge, a black shard standing off the quarter; by then the taper
    # has brought it flush)
    made.append(band("G9L_Tail_Lamp_Cap", lambda y: Z_CAP_BOT, lambda y: zt, 52, 6, collection,
                     lib["black_gloss"], y_max=CAP_END,
                     off_fn=lambda y, k: (0.045 - 0.033 * k) * _taper(y) + 0.002,
                     thickness=0.003, bevel=0.0, cut=True))
    # the shelf's lower lip: a thin black skirt closing the gap between shelf and tailgate
    made.append(band("G9L_Tail_Lamp_Lip", lambda y: Z_CAP_BOT - 0.006, lambda y: Z_CAP_BOT, 52, 2,
                     collection, lib["black_gloss"], y_max=CAP_END,
                     off_fn=lambda y, k: 0.045 * k * _taper(y) + 0.002, thickness=0.003, cut=True))
    # the tailgate, to its smile shut line
    made.append(band("G9L_Tailgate", lambda y: gate_low(y) + 0.5 * GAP, lambda y: Z_CAP_BOT - 0.001,
                     56, 20, collection, lib["paint"], thickness=M.SKIN))
    # the painted bumper strip under it
    made.append(band("G9L_Bumper_Upper", lambda y: bumper_top(y), lambda y: gate_low(y) - 0.5 * GAP,
                     56, 6, collection, lib["paint"], thickness=M.SKIN))
    # the black lower bumper
    made.append(band("G9L_Bumper_Black", lambda y: CAP_LOW, lambda y: bumper_top(y) + 0.001,
                     56, 14, collection, lib["black_trim"], thickness=0.004))
    return made


# ---------------------------------------------------------- tail lamp strips
def _taper(y):
    """1 across the tail, 0 at the corner: the shelf is proud along the cap's normal, which turns sideways
    round the corner, so an untapered shelf ends as a shard standing out past the body's side."""
    return 1.0 - geom.smoothstep((y - 0.60) / 0.20)


def _shelf(y, z):
    """How far the lamp cap's face stands off the cap surface at (y, z): 45 mm at its lower edge,
    12 mm under the glass, fading to the surface round the corners."""
    k = (z - Z_CAP_BOT) / (CAP_HIGH - Z_CAP_BOT)
    return (0.045 - 0.033 * k) * _taper(y) + 0.002


def build_lamps(collection, lib):
    made = []

    def strip(name, z0, z1, mat, lift, ny=60, y_end=0.80, thickness=0.0020):
        zm = 0.5 * (z0 + z1)
        return band(name, lambda y: z0, lambda y: z1, ny, 2, collection, mat,
                    off_fn=lambda y, k: _shelf(y, zm) + lift, y_max=y_end, thickness=thickness, cut=True)

    # a dark smoked lens over the cap's face: the housing of the light
    made.append(band("G9L_Tail_Lens", lambda y: Z_CAP_BOT + 0.010, lambda y: CAP_HIGH - 0.012, 56, 4,
                     collection, lib["lamp_clear"],
                     off_fn=lambda y, k: _shelf(y, Z_CAP_BOT + 0.010 + 0.110 * k) + 0.0012,
                     y_max=0.86, thickness=0.002, cut=True))
    made.append(strip("G9L_Tail_Strip_Main", Z_LAMP_RED[0] - 0.005, Z_LAMP_RED[0] + 0.004, lib["led_red"], 0.0030))
    made.append(strip("G9L_Tail_Strip_Low", Z_LAMP_RED[1] - 0.003, Z_LAMP_RED[1] + 0.003, lib["lamp_red_lens"],
                      0.0030))
    return made


# ------------------------------------------------ reflectors, vents, louvres
def _loop3(yz, d=0.0):
    return [face(y, z, d)[0] for (y, z) in yz]


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


def _flat(name, loop, collection, mat, thickness=0.002, outward=(-1.0, 0.0, 0.0)):
    n = len(loop)
    ob = M.obj(name, loop, [list(range(n))], collection, mat)
    M.orient(ob.data, lambda cc, o=outward: o)
    if thickness:
        M.solidify(ob, thickness)
    return ob


def build_details(collection, lib):
    made = []
    # reflectors: a red lens strip standing 3.5 mm proud of the black bumper
    ob = _flat("G9L_Reflector_R", _loop3(REFLECTOR, 0.0035), collection, lib["lamp_red_lens"], 0.002)
    M.mirror_y(ob)
    made.append(ob)
    # corner vents: a dark pocket with slats
    tun = _tunnel("G9L_Rear_Vent", _loop3(VENT, 0.002), (-1.0, 0.0, 0.0), 0.06, collection, lib["shadow"],
                  taper=0.9)
    M.mirror_y(tun)
    made.append(tun)
    for k in range(6):
        z = 0.505 + 0.012 * k
        p0, _n = face(0.725, z, -0.012)
        p1, _n = face(0.775, z, -0.012)
        slat = _flat("G9L_Vent_Slat_%d" % k, [p0, p1, (p1[0], p1[1], p1[2] + 0.004), (p0[0], p0[1], p0[2] + 0.004)],
                     collection, lib["black_gloss"], 0.0015)
        M.mirror_y(slat)
        made.append(slat)
    # the louvred central panel: recessed black with fine horizontal louvres
    for k in range(9):
        z0 = 0.375 + 0.0145 * k
        made.append(band("G9L_Louvre_%d" % k, lambda y, z0=z0: z0, lambda y, z0=z0: z0 + 0.0085, 40, 1,
                         collection, lib["cap_black"], offset=-0.012, y_max=0.50, thickness=0.0015))
    made.append(band("G9L_Louvre_Back", lambda y: 0.370, lambda y: 0.508, 40, 3, collection, lib["shadow"],
                     offset=-0.020, y_max=0.51, thickness=0.0015))
    # the satin blade along the bottom of the black bumper
    made.append(band("G9L_Diffuser_Blade", lambda y: 0.300, lambda y: 0.366, 40, 3, collection,
                     lib["trim_chrome"], offset=0.006, y_max=0.62, thickness=0.003, bevel=0.0008))
    return made


# ---------------------------------------------------- lettering, camera, plate
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
    for ch, u in zip("XPENG", CAM.LETTERS_U):
        y, z = CAM.rear_yz(u, CAM.LETTERS_V, -2.52)
        p, n = face(y, z, 0.0012)
        t = M.text_mesh("G9L_Letter_" + ch, ch, 0.0235, collection, lib["cap_black"], extrude=0.0012,
                        bold=True, font=inter, resolution=4)
        _on_surface(t, p, n)
        made.append(t)
    # the brand's name in Chinese on the left, the model name on the right (c1_0030)
    for name, text, u, v, size, fnt in (("G9L_Badge_Brand", "小鹏", 1030, 1546, 0.024, cjk),
                                        ("G9L_Badge_Model", "G9L", 2810, 1546, 0.026, inter)):
        y, z = CAM.rear_yz(u, v, -2.52)
        p, n = face(y, z, 0.0012)
        t = M.text_mesh(name, text, size, collection, lib["cap_black"], extrude=0.0010, font=fnt, resolution=4)
        _on_surface(t, p, n)
        made.append(t)
    return made


def build_plate(collection, lib):
    from carkit.parts import fittings
    made = []
    y, z = CAM.rear_yz(1934, 1606, -2.52)
    p, n = face(0.0, z, 0.0)
    made += fittings.plate("G9L_Plate_Rear", tuple(p[i] + n[i] * 0.004 for i in range(3)), n, collection, lib,
                           w=0.480, h=0.148, depth=0.008,
                           texts=[("XPENG G9", 0.0, 0.038, False, True)],
                           mat="black_gloss", text_mat="machined")
    # the reversing camera in its black housing above the plate
    pz = z + 0.075 + 0.045
    made.append(band("G9L_Rear_Camera_House", lambda yy: pz - 0.014, lambda yy: pz + 0.014, 14, 2, collection,
                     lib["black_gloss"], offset=0.010, y_max=0.058, thickness=0.004))
    made.append(band("G9L_Rear_Camera_Lens", lambda yy: pz - 0.006, lambda yy: pz + 0.006, 6, 2, collection,
                     lib["lamp_smoked"], offset=0.013, y_max=0.022, thickness=0.002))
    return made


# ------------------------------------------------------------------ spoiler
def build_spoiler(collection, lib):
    """A black roof spoiler: the roof's end, overhanging the backlight by 0.07 m, swept and
    pointed at its ends (c1_0028 crop d: the tip at x -2.03, z 1.64)."""
    made = []
    ns = 36
    k = S.KNEE_X
    zr = S.Z_ROOF(k)
    cols = []
    for i in range(ns + 1):
        t = i / float(ns)
        y = 0.640 * t
        x_te = k - 0.070 + 0.050 * t ** 2.2                    # trailing edge sweeps forward at the ends
        z_te = zr - 0.045 - 0.050 * t ** 3
        cols.append([(k + 0.030, y, zr - 0.012), (x_te, y, z_te), (x_te + 0.012, y, z_te - 0.020),
                     (k + 0.030, y, zr - 0.040)])
    ob = M.mesh_from_rows("G9L_Spoiler", cols, collection)
    M.orient(ob.data, geom.away_from((k + 0.03, 0.0, zr - 0.06)))
    ob.data.materials.append(lib["black_gloss"])
    M.mirror_y(ob)
    M.finish(ob, thickness=0.004, bevel=0.0008)
    made.append(ob)
    return made


# ------------------------------------------------------------- build all
def build_all(collection, lib):
    made = []
    made += build_tail(collection, lib)
    made += build_lamps(collection, lib)
    made += build_details(collection, lib)
    made += build_lettering(collection, lib)
    made += build_plate(collection, lib)
    made += build_spoiler(collection, lib)
    return made
