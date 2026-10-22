"""BYD Seal rear end (2022-2024 body), read from the blue car's rear photograph c1_0515.jpg through its
solved camera (seal_cam.REAR_CAM) and the side photographs.

What the photographs show:
    * a short boot lid below a large backlight; the lid's rear edge is a DUCK-TAIL lip (dark band,
      its ends sweeping up round the lamps) with a thin silver line on its crest and the lettering
      BUILD YOUR DREAMS spaced across it
    * ONE full-width tail lamp: a thin black bar across the lid with a silver line, ending in two
      wedge lamps that wrap round the corners (their tips reach x -1.81 on the quarter)
    * the lid below the lamp, flat, with 比亚迪 / EV left and 海豹 right
    * a body-colour bumper above a black diffuser shaped like a cup: a thin chrome line climbs from
      the corners to the plate, a red reflector and a clear reverse lamp each side of the plate,
      parking sensors, three fins each side of the plate
    * slim black vertical slits in the bumper's corners

Photo pixels are in the 3840 x 2880 originals; the picture's left half (the car's left) is read.
"""
import math

import seal_surface as S
import seal_nose as N
import seal_cam as CAM
from carkit import geom
from carkit import mesh as M

BODY = N.BODY
TAIL = N.TAIL
CAP_LOW = TAIL.Z_LO + 0.004
CAP_HIGH = TAIL.Z_HI - 0.002
GAP = 0.0042


def _yz(px, x=-2.36):
    """[(|y|, z)] sorted by y, from rear-photo pixels."""
    return sorted((abs(y), z) for (y, z) in (CAM.rear_yz(u, v, x) for (u, v) in px))


def _lerp(pts, y):
    pts = sorted(pts)
    if y <= pts[0][0]:
        return pts[0][1]
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if y0 <= y <= y1:
            t = 0.0 if y1 == y0 else (y - y0) / (y1 - y0)
            return z0 + (z1 - z0) * t
    return pts[-1][1]


# ------------------------------------------------------------------ hardpoints (photo pixels)
# the tail lamp's upper and lower edges, from the centre out to the wedge's tip
LAMP_TOP_PX = [(1920, 1334), (1500, 1334), (1293, 1336), (1182, 1342), (1077, 1356)]
LAMP_BOT_PX = [(1920, 1394), (1800, 1397), (1650, 1408), (1450, 1428), (1293, 1453), (1216, 1456),
               (1127, 1450), (1071, 1422)]
# the lid's lower edge and the bumper's top edge
LID_LOW_PX = [(1927, 1664), (1700, 1655), (1500, 1643), (1349, 1633)]
# the diffuser cup's chrome line: from the corner up the slope to the top, then along it to the plate
CUP_PX = [(1088, 2056), (1138, 2033), (1193, 1978), (1249, 1900), (1293, 1833), (1332, 1794), (1654, 1790)]
LAMP_TOP = _yz(LAMP_TOP_PX)
LAMP_BOT = _yz(LAMP_BOT_PX)
LID_LOW = _yz(LID_LOW_PX)
CUP = _yz(CUP_PX)
Y_CUP = max(y for (y, z) in CUP)                       # the cup's outer corner (y ~0.79)
Z_CUP_FLOOR = min(z for (y, z) in CUP)                 # the corner's height (~0.25)
Z_PLATE = 0.426                                        # plate centre (c1_0515 through the rear camera)

BUMPER_TOP = [(0.000, 0.623), (0.200, 0.625), (0.400, 0.630), (0.550, 0.640), (0.650, 0.655),
              (0.800, 0.665), (0.900, 0.670)]


def lamp_top(y):
    return _lerp(LAMP_TOP, min(y, LAMP_TOP[-1][0]))


def lamp_bot(y):
    return _lerp(LAMP_BOT, min(y, LAMP_BOT[-1][0]))


def bumper_top(y):
    return _lerp(BUMPER_TOP, y)


def cup_top(y):
    """Top of the black diffuser at |y|: flat across the middle, down the corner slope outboard."""
    if y >= Y_CUP:
        return CAP_LOW
    return _lerp(CUP, y)


# ----------------------------------------------------------- band construction
_GRID = {}


def _grid():
    if not _GRID:
        import numpy as np
        ws = np.linspace(0.0, 1.0, 65)
        vs = np.linspace(0.0, 1.0, 129)
        W, V = np.meshgrid(ws, vs)
        P = np.array([[TAIL.point(float(w), float(v)) for w in ws] for v in vs])
        _GRID.update(W=W.ravel(), V=V.ravel(), Y=P[:, :, 1].ravel(), Z=P[:, :, 2].ravel())
    return _GRID


def wv_of(y, z):
    """(w, v, miss) of the tail cap point nearest elevation (y, z)."""
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
    w, v = TAIL.wv_at(y, z)
    p = TAIL.point(w, v)
    if abs(p[2] - z) > 0.006 or abs(p[1] - y) > 0.006:
        w, v, _ = wv_of(y, z)
    return w, v


def face(y, z, d=0.0):
    """Point on the tail cap at elevation (y, z) (either side), and normal."""
    z = max(CAP_LOW, min(CAP_HIGH, z))
    w, v = wv(abs(y), z)
    p, n = TAIL.point(w, v), TAIL.normal(w, v)
    if d:
        p = tuple(p[i] + n[i] * d for i in range(3))
    if y < 0.0:
        p, n = (p[0], -p[1], p[2]), (n[0], -n[1], n[2])
    return p, n


_ZTOP = {}


def _reach_at(i):
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
    f = abs(y) / 0.02
    i = int(f)
    a, b = _reach_at(i), _reach_at(i + 1)
    return a + (b - a) * (f - i)


def edge_y(z):
    """Half-width of the tail cap at height z: meeting the quarter join ring."""
    return TAIL.half_width(max(CAP_LOW, min(CAP_HIGH, z))) * 0.9995


def band(name, zlo, zhi, ny, nz, collection, mat, offset=0.0, thickness=M.SKIN, y_max=None, ymin=0.0,
         off_fn=None, bevel=0.0, cut=False, hold=False):
    """A strip of the tail cap wrapping all the way around to JOIN_R."""
    cols = []
    if y_max is None:
        zs = [zlo(0.4) + (zhi(0.4) - zlo(0.4)) * k / 12.0 for k in range(13)]
        ymax = max(edge_y(z) for z in zs)
    else:
        ymax = y_max
    if cut:
        y_cut = ymax
        while y_cut > ymin + 0.02 and z_reach(y_cut) - 0.002 < zlo(y_cut) + 0.008:
            y_cut -= 0.005
        ymax = min(ymax, y_cut)

    def row_z(y, fr):
        z1 = min(zhi(y), z_reach(y) - 0.002) if (cut or hold) else zhi(y)
        z0 = min(zlo(y), z1 - 0.004) if (cut or hold) else zlo(y)
        return max(CAP_LOW, min(CAP_HIGH, z0 + (z1 - z0) * fr))

    for i in range(ny + 1):
        s = i / float(ny)
        s = 1.0 - (1.0 - s) ** 1.30
        col = []
        for k in range(nz + 1):
            fr = k / float(nz)
            if y_max is None and ymin == 0.0:
                w = s
                z_lo_w = TAIL.point(w, 0.0)[2] + 0.002
                z_hi_w = TAIL.point(w, 1.0)[2] - 0.001
                y = TAIL.point(w, 0.55)[1]
                for _ in range(2):
                    z1 = min(zhi(y), z_hi_w)
                    z0 = min(zlo(y), z1 - 0.003)
                    z = max(z_lo_w, min(z_hi_w, z0 + (z1 - z0) * fr))
                    v = TAIL.v_at_z(z, w=w)
                    y = TAIL.point(w, v)[1]
            else:
                y = ymin + (ymax - ymin) * s
                z = row_z(y, fr)
                w, v = wv(y, z) if (cut or hold) else TAIL.wv_at(y, z)
            d = off_fn(y, fr) if off_fn else offset
            col.append(TAIL.offset(w, v, d) if d else TAIL.point(w, v))
        cols.append(col)
    ob = M.mesh_from_rows(name, cols, collection)
    M.orient(ob.data, geom.axial(-1.0))
    ob.data.materials.append(mat)
    M.mirror_y(ob)
    M.finish(ob, thickness=thickness, bevel=bevel)
    return ob


def _line(name, pts_yz, half, d, collection, mat, n=None, thickness=0.0018):
    """A thin strip along a polyline (|y|, z) on the tail, `half` metres each way in z, d proud."""
    pts = pts_yz if not n else _resample(pts_yz, n)
    cols = [[face(y, z - half, d)[0], face(y, z + half, d)[0]] for (y, z) in pts]
    ob = M.mesh_from_rows(name, cols, collection)
    M.orient(ob.data, geom.axial(-1.0))
    ob.data.materials.append(mat)
    M.mirror_y(ob)
    M.finish(ob, thickness=thickness, bevel=0.0)
    return ob


def _resample(pts, n):
    d = [0.0]
    for a, b in zip(pts, pts[1:]):
        d.append(d[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    out = []
    for i in range(n):
        s = d[-1] * i / float(n - 1)
        j = max(0, min(len(pts) - 2, next((k for k in range(len(d) - 1) if d[k + 1] >= s), len(pts) - 2)))
        t = 0.0 if d[j + 1] == d[j] else (s - d[j]) / (d[j + 1] - d[j])
        out.append((pts[j][0] + (pts[j + 1][0] - pts[j][0]) * t, pts[j][1] + (pts[j + 1][1] - pts[j][1]) * t))
    return out


# ------------------------------------------------------------------ the tail
def build_tail(collection, lib):
    made = []
    # 1. the duck-tail band above the lamp, wrapping to the quarter
    made.append(band("Seal_Tail_Upper", lambda y: lamp_bot(min(y, 0.825)) - 0.002, lambda y: CAP_HIGH, 56, 12,
                     collection, lib["paint"], hold=True))
    # 2. the boot lid and the wings beside it: from the bumper's top edge up to the lamp
    made.append(band("Seal_Tailgate_Skin", lambda y: bumper_top(y) + 0.5 * GAP, lambda y: lamp_bot(min(y, 0.825)) + 0.001,
                     56, 16, collection, lib["paint"]))
    # 3. the body-colour bumper, down to the top of the diffuser's cup
    made.append(band("Seal_Bumper_Upper", lambda y: cup_top(y), lambda y: bumper_top(y) + 0.001, 56, 10, collection,
                     lib["paint"], thickness=0.003))
    # 4. the black diffuser inside the cup, and the skirt under it
    made.append(band("Seal_Bumper_Lower", lambda y: CAP_LOW, lambda y: cup_top(y) + 0.001, 56, 12, collection,
                     lib["black_trim"], thickness=0.003))
    # the lid's shut lines: the lower arc and the two sides up to the lamp (dark, 1.4 mm)
    sides = _yz([(1293, 1453), (1300, 1500), (1320, 1570), (1349, 1633)])
    arc = _yz([(1349, 1633), (1500, 1643), (1700, 1655), (1927, 1664)])
    made.append(_line("Seal_Lid_ShutLine_Arc", arc, 0.0007, 0.0006, collection, lib["shadow"], n=24))
    made.append(_line("Seal_Lid_ShutLine_Side", sorted(sides, key=lambda p: p[1]), 0.0007, 0.0006, collection, lib["shadow"], n=12))
    return made


# ---------------------------------------------------------- tail lamps
def build_tail_lamps(collection, lib):
    """One full-width tail lamp: a thin black bar across the lid, ending in wedge lamps that wrap round the
    corners; a silver line and a red LED line along its middle; a red dot matrix in the wedges."""
    from mathutils import Vector
    made = []

    def lens_band(name, zlo, zhi, mat, off, ny=64, nz=3, y0=0.0, y1=None, y_max=None, thickness=0.002):
        y_hi = y1 if y_max is None else y_max
        return band(name, zlo, zhi, ny, nz, collection, mat, off_fn=off, ymin=y0, y_max=y_hi, thickness=thickness)

    made.append(lens_band("Seal_Tail_Housing", lambda y: lamp_bot(y) - 0.0025, lambda y: lamp_top(y) + 0.0025,
                          lib["black_gloss"], lambda y, k: 0.0012, thickness=0.0025, y_max=None))
    made.append(lens_band("Seal_Tail_Lens", lamp_bot, lamp_top, lib["lamp_red_lens"],
                          lambda y, k: 0.0018 * math.sin(math.pi * k) + 0.0020, y_max=None, thickness=0.0020))

    bar_c = lambda y: lamp_bot(y) + 0.62 * (lamp_top(y) - lamp_bot(y))
    # the silver line along the bar (the photograph's, z ~0.90 at the middle) and a red LED line just under it
    made.append(lens_band("Seal_Tail_Chrome_Bar", lambda y: bar_c(y) + 0.0020, lambda y: bar_c(y) + 0.0044,
                          lib["logo_chrome"], lambda y, k: 0.0048, y0=0.0, y1=0.66, nz=2))
    made.append(lens_band("Seal_Tail_Through_Bar", lambda y: bar_c(y) - 0.0042, lambda y: bar_c(y) + 0.0002,
                          lib["led_red"], lambda y, k: 0.0046, y0=0.0, y1=0.66, nz=2))

    # the dot matrix in the wedges' lower half
    dot_verts, dot_faces = [], []
    n_cols, n_sides = 18, 8
    for col_i in range(n_cols):
        u = col_i / float(n_cols - 1)
        y_d = 0.56 + u * 0.24
        zb, zt = lamp_bot(y_d), lamp_top(y_d)
        for row_k, frac in enumerate((0.16, 0.34)):
            r_dot = 0.0023 + 0.0012 * u
            y_j = y_d + (0.004 if row_k == 1 else 0.0)
            z_d = zb + frac * (zt - zb)
            p_c, n_c = face(y_j, z_d, 0.0048)
            nvec = Vector(n_c).normalized()
            upv = Vector((0, 0, 1)) if abs(nvec.z) < 0.9 else Vector((1, 0, 0))
            t1 = nvec.cross(upv).normalized()
            t2 = nvec.cross(t1).normalized()
            c_vec = Vector(p_c)
            base = len(dot_verts)
            for s_i in range(n_sides):
                ang = 2.0 * math.pi * (s_i / float(n_sides))
                pt = c_vec + t1 * (math.cos(ang) * r_dot) + t2 * (math.sin(ang) * r_dot)
                dot_verts.append((pt.x, pt.y, pt.z))
            dot_faces.append([base + s_i for s_i in range(n_sides)])
    dots_ob = M.obj("Seal_Tail_Dot_Matrix", dot_verts, dot_faces, collection, lib["led_red"])
    M.orient(dots_ob.data, geom.axial(-1.0))
    M.mirror_y(dots_ob)
    M.finish(dots_ob, thickness=0.0014, bevel=0.0)
    made.append(dots_ob)
    made += build_lamp_wrap(collection, lib)
    return made


def build_lamp_wrap(collection, lib):
    """The wedge lamp's part on the quarter panel: the photograph's teardrop (x -1.81 at its tip to
    -2.2, z 0.86-0.97), laid on the flank where the tail cap does not reach, built as a lens between its
    upper and lower edges (c1_0513 side view) with a red LED line along the upper edge."""
    import seal_cam as C
    from carkit.parts import fittings
    up = [C.BLUE.side_xz(u, v, 0.85) for (u, v) in ((3225, 1635), (3280, 1626), (3330, 1618), (3410, 1612), (3492, 1610))]
    lo = [C.BLUE.side_xz(u, v, 0.85) for (u, v) in ((3225, 1635), (3280, 1654), (3330, 1668), (3430, 1688), (3495, 1690))]
    made = [fittings.side_patch("Seal_Tail_Lamp_Side", lo, up, BODY.side_point, collection, lib["lamp_red_lens"],
                                d=0.0022, n=28, nk=3, y_ref=0.85, outward=(0.0, 1.0, 0.0))]
    up2 = [(x, z - 0.004) for (x, z) in up]
    up3 = [(x, z - 0.0015) for (x, z) in up]
    made.append(fittings.side_patch("Seal_Tail_Lamp_Side_LED", up2, up3, BODY.side_point, collection, lib["led_red"],
                                    d=0.0034, n=28, nk=1, y_ref=0.85, outward=(0.0, 1.0, 0.0)))
    return made


# ------------------------------------------------------------- rear deck & ducktail
def build_deck(collection, lib):
    """The rear deck sheet, joining the tail cap seamlessly to the backlight base."""
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
        w = 1.0 - (1.0 - w) ** 1.25
        cols.append([TAIL.offset(w, v_a + (1.0 - v_a) * j / float(nv), 0.0006) for j in range(nv + 1)])
    ob = M.mesh_from_rows("Seal_Rear_Deck", cols, collection)
    M.orient(ob.data, geom.axial(-1.0))
    ob.data.materials.append(lib["paint"])
    M.mirror_y(ob)
    M.finish(ob, thickness=M.SKIN, bevel=0.0)
    return [ob]


def build_ducktail(collection, lib):
    """The duck-tail lip along the boot lid's rear edge, its ends sweeping up round the lamps, and a thin
    silver line on its crest."""
    made = [band("Seal_Ducktail_Lip", lambda y: CAP_HIGH - 0.018, lambda y: CAP_HIGH, 48, 3, collection, lib["paint"],
                 cut=True,
                 off_fn=lambda y, k: 0.0120 * (k ** 1.10) * (1.0 - geom.smoothstep((y - 0.62) / 0.20)) + 0.0008,
                 y_max=0.80, thickness=0.0025)]
    crest = [(0.62 * i / 20.0, CAP_HIGH - 0.001) for i in range(21)]
    made.append(_line("Seal_Ducktail_Trim", crest, 0.0011, 0.0128, collection, lib["trim_chrome"], thickness=0.0014))
    return made


# ------------------------------------------------------------- bumper details
def build_bumper(collection, lib):
    """The cup-shaped diffuser: a chrome line from the corners up to the plate, three slim vertical fins
    each side of the plate, a red reflector and a clear reverse lamp, the plate in its recess, sensors."""
    made = []
    # the cup's chrome line, from the outer corner up the slope and along the top to the plate recess
    cup = [(y, z) for (y, z) in CUP if y > 0.30]
    made.append(_line("Seal_Cup_Chrome", sorted(cup, key=lambda p: -p[0]), 0.0017, 0.0042, collection, lib["trim_chrome"],
                      n=40, thickness=0.0016))

    # the fins: slim, black gloss, standing 9 mm out of the diffuser; y read at 0.558 / 0.422 / 0.281
    for idx, y_f in enumerate((0.558, 0.422, 0.281)):
        z_top = cup_top(y_f) - 0.020
        z_bot = 0.285
        cols = []
        for dy in (-0.0045, 0.0045):
            col = []
            for k in range(8):
                fr = k / 7.0
                z = z_bot + (z_top - z_bot) * fr
                col.append(face(y_f + dy, z, 0.0025 + 0.0070 * math.sin(math.pi * min(1.0, fr * 1.05)) ** 0.5)[0])
            cols.append(col)
        fin = M.mesh_from_rows("Seal_Diffuser_Fin_%d" % idx, cols, collection)
        M.orient(fin.data, geom.axial(-1.0))
        fin.data.materials.append(lib["black_gloss"])
        M.mirror_y(fin)
        M.finish(fin, thickness=0.0022, bevel=0.0)
        made.append(fin)

    # red reflector and clear reverse lamp under the cup's top edge, either side of the plate
    for nm, (y0, y1), (z0, z1), mat in (("Seal_Rear_Reflector", (0.395, 0.557), (0.466, 0.490), lib["reflector_red"]),
                                       ("Seal_Rear_Reverse", (0.296, 0.385), (0.468, 0.492), lib["plate_white"])):
        verts = [face(y, z, 0.0030)[0] for (y, z) in ((y0, z0), (y1, z0), (y1, z1), (y0, z1))]
        ob = M.obj(nm, verts, [[0, 1, 2, 3]], collection, mat, smooth=False)
        M.orient(ob.data, geom.axial(-1.0))
        M.solidify(ob, 0.0018)
        M.mirror_y(ob)
        made.append(ob)

    # parking sensors and the camera dot, the boot release
    from carkit.parts import lamps, fittings
    for nm, (y, z) in (("Seal_Rear_Sensor", (0.340, 0.452)), ("Seal_Rear_Sensor_Out", (0.74, 0.60))):
        p, n = face(y, z, 0.0026)
        made += lamps.projector(nm, p, n, 0.0105, collection, lib, mats=("lamp_bowl", "lamp_smoked"))
    p, n = face(0.0, 0.545, 0.0026)
    made += lamps.projector("Seal_Rear_Camera", p, n, 0.0085, collection, lib, mats=("lamp_bowl", "lamp_smoked"), mirror=False)
    verts = [face(y, z, 0.0030)[0] for (y, z) in ((-0.0155, 0.5945), (0.0155, 0.5945), (0.0155, 0.6145), (-0.0155, 0.6145))]
    rel = M.obj("Seal_Boot_Release", verts, [[0, 1, 2, 3]], collection, lib["black_gloss"], smooth=False)
    M.orient(rel.data, geom.axial(-1.0))
    M.solidify(rel, 0.0020)
    made.append(rel)

    # the corners' slim vertical slits
    made.append(band("Seal_Corner_Vent", lambda y: 0.360, lambda y: 0.600, 2, 10, collection, lib["black_gloss"],
                     ymin=0.806, y_max=0.824, off_fn=lambda y, k: -0.0010, thickness=0.0025))

    # the plate: its recess, then the BYD SEAL plate
    p_plat, n_plat = face(0.0, Z_PLATE, 0.0035)
    made += fittings.plate("Seal_Plate_Mount_Rear", p_plat, n_plat, collection, lib,
                           w=0.520, h=0.190, depth=0.030, mat="black_gloss", bevel=(0.003, 2, 30))
    made += fittings.plate("Seal_Plate_Rear", p_plat, n_plat, collection, lib,
                           w=0.440, h=0.140, depth=0.004,
                           texts=[("BYD SEAL", 0.0, 0.036, False, True)],
                           mat="black_gloss", text_mat="machined")
    return made


# ------------------------------------------------------------------ badges
def _font(fn):
    import os, bpy
    d = os.path.join(os.path.dirname(bpy.app.binary_path), bpy.app.version_string.rsplit(".", 1)[0],
                     "datafiles", "fonts")
    try:
        return bpy.data.fonts.load(os.path.join(d, fn), check_existing=True)
    except Exception:
        return None


def build_badges(collection, lib):
    """BUILD YOUR DREAMS spaced across the duck-tail's band; 比亚迪 / EV left and 海豹 right of the lid."""
    made = []
    inter = _font("Inter.woff2")
    import carkit.place as P

    # the slogan: 17 letters on a 0.031 m pitch (0.55 m wide in the photograph, 17 mm tall)
    z_s = CAM.rear_yz(1920, 1291, -2.2)[1]
    text = "BUILD YOUR DREAMS"
    letters = [c for c in text]
    pitch = 0.0307
    total = pitch * (len(letters) - 1)
    for i, ch in enumerate(letters):
        if ch == " ":
            continue
        y = 0.5 * total - pitch * i
        p, n = face(y, z_s, 0.0030)
        t = M.text_mesh("Seal_Slogan_%02d" % i, ch, 0.0165, collection, lib["trim_chrome"], extrude=0.0012,
                        font=inter, resolution=3)
        P.on_surface(t, p, n)
        made.append(t)

    # 比亚迪 + EV (the car's left = +y) and 海豹 (right = -y), read at u 1385 / 2430, v 1560 / 1565
    yb, zb = CAM.rear_yz(1432, 1561, -2.37)
    p, n = face(yb, zb, 0.0025)
    bl = M.text_mesh("Seal_Badge_BYD_Zh", "比亚迪", 0.026, collection, lib["trim_chrome"], extrude=0.0014, resolution=4)
    P.on_surface(bl, p, n)
    made.append(bl)
    p, n = face(yb + 0.002, zb - 0.036, 0.0025)
    ev = M.text_mesh("Seal_Badge_EV", "EV", 0.0135, collection, lib["trim_chrome"], extrude=0.0012, font=inter, resolution=3)
    P.on_surface(ev, p, n)
    made.append(ev)
    ys, zs_ = CAM.rear_yz(2432, 1564, -2.37)
    p, n = face(ys, zs_, 0.0025)
    br = M.text_mesh("Seal_Badge_Seal", "海豹", 0.024, collection, lib["trim_chrome"], extrude=0.0014, resolution=4)
    P.on_surface(br, p, n)
    made.append(br)
    return made


def build_all(collection, lib):
    made = []
    made += build_tail(collection, lib)
    made += build_tail_lamps(collection, lib)
    made += build_deck(collection, lib)
    made += build_ducktail(collection, lib)
    made += build_bumper(collection, lib)
    made += build_badges(collection, lib)
    return made
