"""Avatr 06T front end, read from the studio front photograph c1_0002.jpg (grey car c1_0010/0011 for
the grille) through its solved camera (a06t_cam.FRONT_CAM).

What the photographs show (nothing here is invented):
    * a broad, taut painted fascia under a bonnet whose leading edge is one soft "smile" across the nose;
      the bonnet's side shut lines run back diagonally from the nose corners to the screen's corners
    * two very thin lamps at the nose corners: a small tapered "eyebrow" wedge on top and, under it, the
      long main blade (the DRL) whose inner tip points at the badge - both dark glass with a bright edge
    * a tall black kite-shaped lamp pocket hugging each corner, widest at its inner apex, holding the
      projector modules behind smoked glass (this is the "large black triangle" at the corners)
    * a black wedge grille opening under the plate: two fields of vertical slats either side of a
      V-shaped centre notch, and under it the black chin with a chrome pin-stripe that curls down at
      each outer end
    * the prism badge above the plate, a camera dot over it, parking sensors, a tow-eye cover
    * the LiDAR pod on the roof's front edge

Photo pixels are in the 3840 x 2880 originals (a06t_cam.py lists them); the left half of the picture
(the car's right) is read and mirrored.
"""
import math

import bpy
from mathutils import Vector

import a06t_surface as S
import a06t_nose as N
import a06t_panels as PN
import a06t_cam as CAM
from carkit import geom
from carkit import mesh as M
from carkit import cut as C
from carkit.body import fascia as FA
from carkit.body import panels as BP
import carkit.place as P
from carkit.parts import fittings, lamps

BODY = N.BODY
NOSE = N.NOSE

PLACER = P.Placer(BODY.proud)
LAMP_BODY = ("A06T_Fascia", "A06T_Fender_Front", "A06T_Hood")
LAMP_CENTRE = (1.95, 0.45, 0.60)


def _lamp_place(p, d=0.0):
    return PLACER.radial(p, LAMP_CENTRE, LAMP_BODY, d)


# ------------------------------------------------------- photo pixels -> the nose's (|y|, z)
def _px_yz(u, v):
    """(|y|, z) of a front-photo pixel ON the nose's own surface: a ray from the camera, the plane at
    the nose's depth there, again (the nose is 0.3 m deeper at the centre than at the corners)."""
    x = 2.38
    y = z = 0.0
    for _ in range(4):
        y, z = CAM.front_yz(u, v, x)
        x = NOSE.x_at(abs(y), max(NOSE.Z_LO + 0.004, min(NOSE.Z_HI - 0.004, z)))
    return (abs(y), z)


def _yz_px(px):
    return [_px_yz(u, v) for (u, v) in px]


def _face(y, z, d=0.0):
    z_clamped = max(NOSE.Z_LO + 0.003, min(NOSE.Z_HI - 0.003, z))
    w, v = NOSE.wv_at(abs(y), z_clamped)
    p, n = NOSE.point(w, v), NOSE.normal(w, v)
    if d:
        p = tuple(p[i] + n[i] * d for i in range(3))
    if y < 0.0:
        p, n = (p[0], -p[1], p[2]), (n[0], -n[1], n[2])
    return p, n


HOOD_EDGE = _yz_px(CAM.HOOD_EDGE_PX)               # (|y|, z), outer corner -> centre
KITE = _yz_px(CAM.KITE_PX)
PAINT_EDGE = _yz_px(CAM.PAINT_EDGE_PX)             # outer corner -> centre
CHIN = _yz_px(CAM.CHIN_PX)
PLATE_Z = _px_yz(0.5 * (CAM.PLATE_PX[0] + CAM.PLATE_PX[2]), 0.5 * (CAM.PLATE_PX[1] + CAM.PLATE_PX[3]))[1]


# ------------------------------------------------------------------ helpers
def _box(name, c, size, collection, mat):
    x, y, z = c
    hx, hy, hz = (0.5 * t for t in size)
    v = [(x + sx * hx, y + sy * hy, z + sz * hz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    f = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
    return M.obj(name, v, f, collection, mat)


def _resample(pts, n):
    """n points along a 2D polyline, equally spaced by arc length."""
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


def _strip(name, pts_yz, half, depth, collection, mat, n=None, thickness=0.0022):
    """A thin strip along a polyline (|y|, z) on the nose, `half` metres each side in z, `depth` proud
    (negative: recessed). Mirrored."""
    pts = _resample(pts_yz, n) if n else pts_yz
    cols = [[_face(y, z - half, depth)[0], _face(y, z + half, depth)[0]] for (y, z) in pts]
    ob = M.mesh_from_rows(name, cols, collection)
    ob.data.materials.append(mat)
    M.mirror_y(ob)
    M.finish(ob, thickness=thickness, bevel=0.0)
    return ob


# ---------------------------------------------------------- bonnet edge slot
def _hood_path():
    pts, nrm = [], []
    half = [(y, z) for (y, z) in reversed(HOOD_EDGE)]                    # centre -> outer corner
    full = [(-y, z) for (y, z) in reversed(half[1:])] + half            # symmetric: flat at the centre
    path = geom.polyline([(0.0, y, z) for (y, z) in full], 140)
    path = [q for q in path if q[1] >= -1e-6]
    for (_x, y, z) in path:
        p, n = _face(y, z)
        pts.append(p)
        nrm.append(n)
    # on up the flank to the bonnet's side line (the diagonal that runs back to the screen's corner)
    y0, z0 = HOOD_EDGE[0]
    w, v = NOSE.wv_at(y0, z0)
    for k in range(1, 7):
        t = k / 6.0
        pts.append(NOSE.point(w + (1.0 - w) * t, v + (min(1.0, v + 0.02) - v) * t))
        nrm.append(NOSE.normal(w + (1.0 - w) * t, v + (min(1.0, v + 0.02) - v) * t))
    return pts, nrm


def _cut_hood_edge(ob):
    pts, nrm = _hood_path()
    c = C.slot("_hoodedge_" + ob.name, pts, nrm, PN.GAP, out=0.03, inside=0.03)
    C.difference(ob, [c], "hood_", reset_materials=True)


def _cut_openings(ob):
    """The lamp pocket (kite) and everything under the painted bumper edge."""
    lower = [(PAINT_EDGE[-1][0] - 0.02, PAINT_EDGE[-1][1])] + [(y, z) for (y, z) in reversed(PAINT_EDGE)]
    lower += [(PAINT_EDGE[0][0] - 0.01, 0.02), (-0.02, 0.02)]
    cutters = [C.prism_x("_cut_kite_" + ob.name, KITE, S.HALF_L + 0.30, S.HALF_L - 0.60),
               C.prism_x("_cut_lower_" + ob.name, lower, S.HALF_L + 0.30, S.HALF_L - 0.60)]
    sheet = C.sheet_bvh(ob)
    C.difference(ob, cutters, "front_cuts_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


# ------------------------------------------------------------------ fascia
def build_fascia(collection, lib):
    made = []
    fascia = FA.cap_panel(
        "A06T_Fascia", NOSE, collection, lib,
        N.NOSE_Z_LO + 0.0008, N.NOSE_Z_HI - 0.0008,
        0.0, 1.0, 46, 50, mat="paint", top_to_centre=True,
        cuts=(_cut_openings,))
    made.append(fascia)

    # the dark apron behind every opening, recessed 2.4 cm (it shows only through the cuts)
    rows, _ = BP.cap_rows(NOSE, N.NOSE_Z_LO + 0.002, 0.755, 0.0, 1.0, 20, 32, offset=-0.024)
    ap = M.mesh_from_rows("A06T_Apron", rows, collection)
    M.orient(ap.data, geom.axial(1.0))
    ap.data.materials.append(lib["black_trim"])
    M.mirror_y(ap)
    M.finish(ap, thickness=0.0025, bevel=0.0)
    made.append(ap)

    # smoked glass over the projector modules, 9 mm behind the painted face
    rows, _ = BP.cap_rows(NOSE, 0.34, 0.80, 0.50, 1.0, 14, 24, offset=-0.009)
    gl = M.mesh_from_rows("A06T_Pocket_Glass", rows, collection)
    M.orient(gl.data, geom.axial(1.0))
    gl.data.materials.append(lib["black_gloss"])
    M.mirror_y(gl)
    M.finish(gl, thickness=0.0018, bevel=0.0)
    made.append(gl)
    return made


# --------------------------------------------------------- grille and chin
GRILLE_TOP_Z = None


def build_grille(collection, lib):
    """Two fields of vertical slats either side of a V notch, in the black opening under the plate,
    then the chin blade with its chrome pin-stripe curling down at each outer end."""
    made = []
    y_top = PAINT_EDGE[-1][1]                                       # the opening's top edge (z)
    z_lo = N.NOSE_Z_LO + 0.050
    # dividers: thin vertical bars, a field per side (c1_0010: ~7 panels, ~75 mm pitch)
    verts, faces = [], []
    pitch, wid, dep = 0.078, 0.0035, 0.007
    for side in (1.0, -1.0):
        for i in range(8):
            y = 0.185 + pitch * i
            z_t = y_top - 0.020
            edge_y = None
            # stop where the opening's diagonal edge comes in
            for (ya, za), (yb, zb) in zip(PAINT_EDGE, PAINT_EDGE[1:]):
                if za <= z_t <= zb or zb <= z_t <= za:
                    edge_y = ya
                    break
            if edge_y is not None and y > edge_y - 0.03:
                break
            x_f = min(_face(y, z_t)[0][0], _face(y, z_lo)[0][0]) - 0.020 + dep
            x_b = x_f - dep
            k = len(verts)
            for (xx, zz) in ((x_b, z_lo), (x_f, z_lo), (x_f, z_t), (x_b, z_t)):
                verts.append((xx, side * (y - wid * 0.5), zz))
                verts.append((xx, side * (y + wid * 0.5), zz))
            faces += [[k + 0, k + 1, k + 3, k + 2], [k + 2, k + 3, k + 5, k + 4],
                      [k + 4, k + 5, k + 7, k + 6], [k + 6, k + 7, k + 1, k + 0],
                      [k + 0, k + 2, k + 4, k + 6], [k + 1, k + 7, k + 5, k + 3]]
    made.append(M.obj("A06T_Grille_Slats", verts, faces, collection, lib["black_gloss"], smooth=False))

    # the V-shaped centre notch: a smooth recessed trapezoid pointing down (the radar's cover)
    zt = y_top - 0.004
    notch = [(0.150, zt), (0.115, zt - 0.060), (0.060, zt - 0.112), (0.0, zt - 0.118)]
    rows = []
    for (y, z) in _resample(notch, 14):
        rows.append([_face(y, z, -0.012)[0], _face(y, zt, -0.012)[0]])
    nb = M.mesh_from_rows("A06T_Grille_Notch", rows, collection)
    nb.data.materials.append(lib["radar"])
    M.mirror_y(nb)
    M.finish(nb, thickness=0.0022, bevel=0.0)
    made.append(nb)

    # the chin: a satin black blade along the bumper's lower edge, a thin chrome line along it that
    # curls down at the outer end (c1_0002: the pin-stripe starts at the corner and runs to y 0.55)
    chin = [(y, z) for (y, z) in CHIN]
    made.append(_strip("A06T_Chin_Lip", [(y, z + 0.010) for (y, z) in _resample(chin, 40)], 0.0140, 0.010,
                       collection, lib["black_gloss"], thickness=0.003))
    made.append(_strip("A06T_Chin_Silver", _resample(chin, 44), 0.0021, 0.0135, collection,
                       lib["chrome"], thickness=0.0016))
    return made


# ---------------------------------------------------------------- headlamps
def _hit(bodies, u, v, fallback):
    """The photo ray's first hit on the body meshes, mirrored to y >= 0 (None -> the plane fit)."""
    try:
        import a06t_ref_match as RM
        h = RM.on_mesh("front", u, v, bodies)
    except Exception as e:
        print("a06t_front: ray cast failed:", e)
        h = None
    if h is None:
        return fallback
    return (h[0], abs(h[1]), h[2])


def build_headlamps(collection, lib):
    made = []
    PLACER.reset()
    bodies = [bpy.data.objects[n] for n in LAMP_BODY if n in bpy.data.objects]
    try:
        import a06t_ref_match as RM
        RM.clear_bvh()
    except Exception:
        pass

    def pts3(px):
        out = []
        for (u, v) in px:
            y, z = _px_yz(u, v)
            out.append(_hit(bodies, u, v, (NOSE.x_at(y, max(NOSE.Z_LO + 0.004, min(NOSE.Z_HI - 0.004, z))), y, z)))
        return out

    NS, NK = 48, 5
    out = geom.away_from((1.90, 0.45, 0.60))

    def _crown(k, extra=0.0):
        return 0.0028 + 0.0010 * math.sin(math.pi * max(0.0, min(1.0, k))) + extra

    # ---- the main blade (DRL): a dark glass lens with a bright line along its lower part
    up = geom.polyline(pts3(CAM.DRL_UP_PX), NS)
    lo = geom.polyline(pts3(CAM.DRL_LO_PX), NS)
    made.append(lamps.lens("A06T_Lamp_Housing", lo, up, _lamp_place, collection, lib["lamp_housing"],
                           NK, lambda k, nk: 0.0016, out, thickness=0.0025, bevel=0.0))
    made += lamps.seals("A06T_Lamp_Seal", lo, up, _lamp_place, collection, lib["grille"], out,
                        width=0.0030, d=0.0010)
    made.append(lamps.band_between("A06T_Lamp_DRL", lo, up, range(2, int(NS * 0.97)), [0.18, 0.26, 0.34],
                                   _lamp_place, lambda k: _crown(k, 0.0022), collection, lib["led_white"], out))
    made.append(lamps.lens("A06T_Lamp_Lens", lo, up, _lamp_place, collection, lib["lamp_clear"],
                           NK, lambda k, nk: _crown(k / float(nk), 0.0006), out,
                           thickness=0.0020, bevel=(0.0008, 2, 30)))
    # the silver edge along the blade's lower rim
    made.append(lamps.band_between("A06T_Lamp_Rim", lo, up, range(1, int(NS * 0.985)), [-0.07, -0.02],
                                   _lamp_place, lambda k: _crown(0.5, 0.0030), collection, lib["chrome"], out))

    # ---- the eyebrow: a tapered wedge with a clear lens and a black frame
    eu = geom.polyline(pts3(CAM.EYEBROW_UP_PX), NS)
    el = geom.polyline(pts3(CAM.EYEBROW_LO_PX), NS)
    made.append(lamps.lens("A06T_Eyebrow_Housing", el, eu, _lamp_place, collection, lib["lamp_housing"],
                           NK, lambda k, nk: 0.0018, out, thickness=0.0025, bevel=0.0))
    made.append(lamps.lens("A06T_Eyebrow_Lens", el, eu, _lamp_place, collection, lib["lamp_clear"],
                           NK, lambda k, nk: _crown(k / float(nk), 0.0006), out,
                           thickness=0.0020, bevel=(0.0008, 2, 30)))
    return made


# ------------------------------------------------------- the lamp pocket's insides
def build_pocket(collection, lib):
    """Projector modules behind the smoked glass, and the pocket's thin silver edge."""
    made = []
    # two modules down the pocket (c1_0002: a small oval and a square, in the dark)
    for i, (u, v, r) in enumerate(((1196, 1788, 0.0160), (1204, 1842, 0.0150), (1176, 1906, 0.0130))):
        y, z = _px_yz(u, v)
        p, n = _face(y, z, -0.0040)
        made += lamps.projector("A06T_Pocket_Proj%d" % i, p, n, r, collection, lib,
                                mats=("lamp_bowl", "lamp_smoked"))
    # the pocket's inner edge: a thin silver line along the diagonal and the lower leg (the apex at 1258)
    edge_px = [(1160, 1692), (1190, 1720), (1220, 1765), (1248, 1810), (1258, 1838), (1248, 1880),
               (1222, 1925), (1190, 1962), (1165, 1985)]
    made.append(_strip("A06T_Pocket_Edge", _resample(_yz_px(edge_px), 40), 0.0016, 0.0007, collection,
                       lib["chrome"], thickness=0.0014))
    return made


# ------------------------------------------------------------ badge, plate, bits
def _font(fn):
    import os
    d = os.path.join(os.path.dirname(bpy.app.binary_path), bpy.app.version_string.rsplit(".", 1)[0],
                     "datafiles", "fonts")
    try:
        return bpy.data.fonts.load(os.path.join(d, fn), check_existing=True)
    except Exception:
        return None


def build_emblem(collection, lib):
    """The Avatr prism badge: a tall kite with a vertical centre bar, ~35 x 42 mm."""
    y, z = _px_yz(*CAM.EMBLEM_PX)
    p, n = _face(0.0, z, 0.002)
    hw, hh, t = 0.0175, 0.021, 0.0035
    ring = [(0.0, hh), (hw, hh * 0.15), (0.0, -hh), (-hw, hh * 0.15)]
    verts, faces = [], []

    def bar(a, b, w):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        ox, oy = -dy / L * w * 0.5, dx / L * w * 0.5
        k = len(verts)
        for q in ((a[0] + ox, a[1] + oy), (b[0] + ox, b[1] + oy), (b[0] - ox, b[1] - oy), (a[0] - ox, a[1] - oy)):
            verts.append((q[0], q[1], 0.0))
        faces.append([k, k + 1, k + 2, k + 3])
    for i in range(len(ring)):
        bar(ring[i], ring[(i + 1) % len(ring)], t)
    bar(ring[0], ring[2], t * 0.8)
    ob = M.obj("A06T_Emblem", verts, faces, collection, lib["chrome"])
    M.solidify(ob, 0.0020)
    P.on_surface(ob, p, n)
    return [ob]


def build_plate(collection, lib):
    """Front show plate (480 x 140 mm) with its dark holder, the camera dot over it, the parking
    sensors and the tow-eye cover."""
    made = []
    p, n = _face(0.0, PLATE_Z, 0.004)
    p_mount = tuple(p[i] - n[i] * 0.002 for i in range(3))
    made += fittings.plate("A06T_Plate_Mount_Front", p_mount, n, collection, lib, w=0.500, h=0.158, depth=0.030,
                           mat="black_gloss", bevel=(0.003, 2, 30))
    made += fittings.plate("A06T_Plate_Front", p, n, collection, lib, w=0.480, h=0.140, depth=0.004,
                           texts=[("AVATR 06T", 0.0, 0.038, False, True)],
                           mat="black_gloss", text_mat="machined")
    y, z = _px_yz(*CAM.CAMERA_PX)
    pc, _nc = _face(0.0, z, 0.002)
    made.append(_box("A06T_Front_Camera", pc, (0.006, 0.018, 0.018), collection, lib["black_gloss"]))
    for i, (u, v) in enumerate(CAM.SENSORS_PX):
        y, z = _px_yz(u, v)
        ps, ns = _face(y, z, 0.0020)
        made += lamps.projector("A06T_Sensor_%d" % i, ps, ns, 0.0100, collection, lib,
                                mats=("lamp_bowl", "lamp_smoked"))
    u0, v0, u1, v1 = CAM.TOWCAP_PX
    y, z = _px_yz(0.5 * (u0 + u1), 0.5 * (v0 + v1))
    made.append(_tow_cap(y, z, collection, lib))
    return made


def _tow_cap(y, z, collection, lib):
    hw, hh = 0.031, 0.027
    ring = [(y + hw * math.copysign(abs(math.cos(a)) ** 0.35, math.cos(a)),
             z + hh * math.copysign(abs(math.sin(a)) ** 0.35, math.sin(a)))
            for a in [2.0 * math.pi * i / 28.0 for i in range(28)]]
    ring.append(ring[0])
    a = [_face(py, pz, 0.0006)[0] for (py, pz) in ring]
    b = [_face(py, pz, -0.0006)[0] for (py, pz) in ring]
    ob = M.strip("A06T_Tow_Cap", a, b, collection, lib["shadow"])
    M.mirror_y(ob)
    return ob


# ------------------------------------------------------------------- lidar
def build_lidar(collection, lib):
    """Huawei 896-line lidar pod on the roof's front edge: x 0.15..0.40, top 1.447 (c1_0004)."""
    cx, a, b, c = 0.275, 0.125, 0.150, 0.047
    zc = S.Z_ROOF(cx) - 0.012
    n_az, n_el, e = 40, 9, 2.8
    verts, faces = [], []
    for j in range(n_el + 1):
        el = math.radians(78.0) * j / n_el
        sc = math.cos(el) ** 0.45
        for i in range(n_az):
            t = 2.0 * math.pi * i / n_az
            cx_, sy_ = math.cos(t), math.sin(t)
            verts.append((cx + a * sc * math.copysign(abs(cx_) ** (2.0 / e), cx_),
                          b * sc * math.copysign(abs(sy_) ** (2.0 / e), sy_),
                          zc + c * math.sin(el) ** 0.8))
    for j in range(n_el):
        for i in range(n_az):
            i2 = (i + 1) % n_az
            faces.append([j * n_az + i, j * n_az + i2, (j + 1) * n_az + i2, (j + 1) * n_az + i])
    top = len(verts)
    verts.append((cx, 0.0, zc + c))
    for i in range(n_az):
        faces.append([n_el * n_az + i, n_el * n_az + (i + 1) % n_az, top])
    pod = M.obj("A06T_Lidar", verts, faces, collection, lib["black_gloss"])
    M.orient(pod.data, geom.away_from((cx, 0.0, zc - 0.02)))
    # the smoked window across its front face
    win = fittings.rounded_panel("A06T_Lidar_Window", (cx + a * 0.93, 0.0, zc + 0.020), 0.098, 0.013, 0.008,
                                 lambda q, d: ((cx + a * 0.93 + d, q[1], q[2]), (1.0, 0.0, 0.0)),
                                 cx + a * 0.93, collection, lib["lamp_smoked"], d=0.0006,
                                 outward=(1.0, 0.0, 0.0))
    return [pod, win]


def build_all(collection, lib):
    PLACER.reset()
    made = []
    made += build_fascia(collection, lib)
    made += build_grille(collection, lib)
    PLACER.reset()
    made += build_headlamps(collection, lib)
    made += build_pocket(collection, lib)
    made += build_emblem(collection, lib)
    made += build_plate(collection, lib)
    made += build_lidar(collection, lib)
    return made
