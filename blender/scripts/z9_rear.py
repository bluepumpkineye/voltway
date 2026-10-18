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


def _yz(px, x=X_PLANE):
    out = []
    for (u, v) in px:
        y, z = CAM.rear_yz(u, v, x)
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
Z_LAMP_TOP, Z_LAMP_BOT = 0.971, 0.860
Z_ROUNDEL = CAM.rear_yz(1924, 1495, -2.61)[1]
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
def band(name, zlo, zhi, ny, nz, collection, mat, offset=0.0, thickness=M.SKIN, y_max=None, ymin=0.0,
         off_fn=None, bevel=0.0):
    """A strip of the tail cap between z-limits that depend on |y|: zlo(y), zhi(y)."""
    cols = []
    zm = 0.5 * (zlo(0.4) + zhi(0.4))
    ymax = (TAIL.half_width(max(CAP_LOW, min(CAP_HIGH, zm))) * 0.9995) if y_max is None else y_max
    for i in range(ny + 1):
        s = i / float(ny)
        s = 1.0 - (1.0 - s) ** 1.30
        y = ymin + (ymax - ymin) * s
        col = []
        for k in range(nz + 1):
            z = zlo(y) + (zhi(y) - zlo(y)) * (k / float(nz))
            z = max(CAP_LOW, min(CAP_HIGH, z))
            w, v = TAIL.wv_at(y, z)
            d = off_fn(y, k / float(nz)) if off_fn else offset
            col.append(TAIL.offset(w, v, d) if d else TAIL.point(w, v))
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


# ------------------------------------------------------------------ the tail
def build_tail(collection, lib):
    made = []
    # the upper tail: everything above the lamps' lower edge, under the ducktail lip
    made.append(band("Z9_Tail_Upper", lambda y: lamp_bot(min(y, 0.82)) - 0.0005, lambda y: CAP_HIGH, 56, 8,
                     collection, lib["paint"]))
    # the tailgate: from the bumper's top edge to the lamps (a slim gap above the bumper)
    made.append(band("Z9_Tailgate", lambda y: bumper_top(y) + 0.5 * GAP, lambda y: lamp_bot(min(y, 0.82)) - 0.5 * GAP,
                     56, 14, collection, lib["paint"]))
    # the gloss-black upper bumper ("eyebrow") from the pocket's floor to the tailgate
    made.append(band("Z9_Bumper_Upper", lambda y: 0.432, lambda y: bumper_top(y) + 0.001, 56, 8, collection,
                     lib["black_gloss"], thickness=0.004))
    # the matt-black diffuser under it
    made.append(band("Z9_Bumper_Lower", lambda y: CAP_LOW, lambda y: 0.434, 56, 10, collection,
                     lib["cap_black"], thickness=0.004))
    return made


# ---------------------------------------------------------- tail lamps
def build_lamps(collection, lib):
    made = []

    def lens_band(name, zlo, zhi, mat, off, ny=70, nz=3, y0=0.12, y1=0.83, thickness=0.002):
        return band(name, zlo, zhi, ny, nz, collection, mat, off_fn=off, ymin=y0, y_max=y1, thickness=thickness)

    # the housing: a dark pocket the shape of the leaf, its lens on top
    zlo = lambda y: lamp_bot(y)
    zhi = lambda y: lamp_top(y)
    made.append(lens_band("Z9_Tail_Lamp_Back", zlo, zhi, lib["black_gloss"], lambda y, k: -0.004, thickness=0.003))
    made.append(lens_band("Z9_Tail_Lamp_Lens", zlo, zhi, lib["lamp_red_lens"], lambda y, k: 0.0035 * math.sin(math.pi * k) + 0.0010))
    # the two rows of red light elements, split by a thin grey line
    split = lambda y: lamp_bot(y) + 0.52 * (lamp_top(y) - lamp_bot(y))
    made.append(lens_band("Z9_Tail_Lamp_Row_Up", lambda y: split(y) + 0.004, lambda y: lamp_top(y) - 0.006, lib["led_red"],
                          lambda y, k: 0.0050, y0=0.20, y1=0.70, nz=2))
    made.append(lens_band("Z9_Tail_Lamp_Row_Low", lambda y: lamp_bot(y) + 0.006, lambda y: split(y) - 0.004, lib["led_red"],
                          lambda y, k: 0.0050, y0=0.20, y1=0.70, nz=2))
    return made


# ------------------------------------------------- roundel, plate tray, camera
def build_badges(collection, lib):
    made = []
    # the roundel: a chrome ring, a dark disc and the two-triangle hourglass
    p, n = face(0.0, Z_ROUNDEL, 0.0)
    from mathutils import Vector
    nv = Vector(n).normalized()
    t1 = Vector((0.0, 1.0, 0.0))
    t2 = nv.cross(t1).normalized()
    r = 0.0465
    for tag, rad, lift, mat in (("Ring", r, 0.004, lib["trim_chrome"]), ("Disc", r * 0.80, 0.0055, lib["cap_black"])):
        verts = [tuple(Vector(p) + nv * lift)]
        for i in range(32):
            a = 2 * math.pi * i / 32
            verts.append(tuple(Vector(p) + nv * lift + t1 * (math.cos(a) * rad) + t2 * (math.sin(a) * rad)))
        faces = [[0, 1 + i, 1 + (i + 1) % 32] for i in range(32)]
        ob = M.obj("Z9_Roundel_" + tag, verts, faces, collection, mat)
        M.orient(ob.data, lambda cc, d=tuple(nv): d)
        made.append(ob)
    for k, sgn in enumerate((1.0, -1.0)):
        a = 0.016
        tri = [Vector(p) + nv * 0.0065 + t2 * (sgn * 0.034) + t1 * dy for dy in (-a,)]
        verts = [tuple(Vector(p) + nv * 0.0065 + t2 * (sgn * 0.002) + t1 * (-0.020)),
                 tuple(Vector(p) + nv * 0.0065 + t2 * (sgn * 0.002) + t1 * (0.020)),
                 tuple(Vector(p) + nv * 0.0065 + t2 * (sgn * 0.034) + t1 * 0.0)]
        ob = M.obj("Z9_Roundel_Mark_%d" % k, verts, [[0, 1, 2]], collection, lib["trim_chrome"])
        M.orient(ob.data, lambda cc, d=tuple(nv): d)
        made.append(ob)
    return made


def build_plate_tray(collection, lib):
    from carkit.parts import fittings
    made = []
    # the black trapezoid pocket: a recessed gloss panel, dished 12 mm
    half = _yz(TRAY_PX)
    zt, zb = half[0][1], half[-1][1]
    yt, yb = half[0][0], half[-2][0]
    made.append(band("Z9_Plate_Tray", lambda y: zb, lambda y: zt, 24, 10, collection, lib["black_gloss"],
                     off_fn=lambda y, k: -0.012, y_max=yt, thickness=0.003))
    p, n = face(0.0, Z_PLATE, -0.004)
    made += fittings.plate("Z9_Plate_Rear", tuple(p[i] + n[i] * 0.004 for i in range(3)), n, collection, lib,
                           w=0.480, h=0.148, depth=0.008,
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
    tun = _tunnel("Z9_Reflector_Pocket", pocket, (-1.0, 0.0, 0.0), 0.05, collection, lib["shadow"], taper=0.95)
    M.mirror_y(tun)
    made.append(tun)
    refl = _yz(REFLECTOR_PX)
    red = [p for p in refl if p[0] >= 0.63] or refl
    made.append(_flat("Z9_Reflector", _loop3(refl, 0.0045), collection, lib["lamp_red_lens"], 0.002))
    # parking sensors
    for k, (u, v) in enumerate(SENSORS_PX):
        y, z = CAM.rear_yz(u, v, X_PLANE)
        p, n = face(abs(y), z, 0.0)
        made += _disc("Z9_Sensor_%d" % k, p, n, 0.0125, collection, lib["cap_black"], 0.003)
        q, m_ = face(-abs(y), z, 0.0)
        made += _disc("Z9_Sensor_R%d" % k, q, m_, 0.0125, collection, lib["cap_black"], 0.003)
    # the horizontal slot across the diffuser
    z_slot = CAM.rear_yz(1500, 2093, X_PLANE)[1]
    made.append(band("Z9_Diffuser_Slot", lambda y: z_slot - 0.006, lambda y: z_slot + 0.006, 40, 1, collection,
                     lib["black_gloss"], offset=-0.010, y_max=0.50, thickness=0.002))
    # the two vertical fog lamps side by side in the middle
    for k, (u0, v0, u1, v1) in enumerate(FOG_PX):
        ya, za = CAM.rear_yz(u0, v0, X_PLANE)
        yb, zb = CAM.rear_yz(u1, v1, X_PLANE)
        yc = 0.5 * (ya + yb)
        hy = 0.5 * abs(yb - ya)
        # a black housing and the red lens inside it
        made.append(band("Z9_Fog_House_%d" % k, lambda y, zb=zb: zb - 0.012, lambda y, za=za: za + 0.012, 2, 4,
                         collection, lib["black_gloss"], offset=0.006, ymin=max(0.0, abs(yc) - hy - 0.012),
                         y_max=abs(yc) + hy + 0.012, thickness=0.003))
        made.append(band("Z9_Fog_Lens_%d" % k, lambda y, zb=zb: zb, lambda y, za=za: za, 2, 4, collection,
                         lib["led_red"], offset=0.0085, ymin=max(0.0, abs(yc) - hy), y_max=abs(yc) + hy,
                         thickness=0.002))
    # the lip along the bottom of the diffuser: a dark satin band, a few mm proud (c1_0038: it is dark grey,
    # not chrome)
    z_lip = CAM.rear_yz(1500, 2190, X_PLANE)[1]
    made.append(band("Z9_Diffuser_Lip", lambda y: z_lip - 0.010, lambda y: z_lip + 0.030, 40, 3, collection,
                     lib["black_gloss"], offset=0.005, y_max=0.60, thickness=0.003))
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
        y, z = CAM.rear_yz(u, v, -2.57)
        p, n = face(y, z, 0.0012)
        t = M.text_mesh(name, text, size, collection, lib["trim_chrome"], extrude=0.0012, font=fnt, resolution=4)
        _on_surface(t, p, n)
        made.append(t)
    return made


# ------------------------------------------------------------ ducktail lip
def build_ducktail(collection, lib):
    """The slim spoiler lip across the top of the tail (the side photograph's tip at z 1.0)."""
    return [band("Z9_Ducktail_Lip", lambda y: CAP_HIGH - 0.012, lambda y: CAP_HIGH, 40, 2, collection, lib["paint"],
                 off_fn=lambda y, k: 0.008 * k, y_max=0.86, thickness=0.003)]


# ------------------------------------------------------------- build all
def build_all(collection, lib):
    made = []
    made += build_tail(collection, lib)
    made += build_lamps(collection, lib)
    made += build_badges(collection, lib)
    made += build_plate_tray(collection, lib)
    made += build_bumper(collection, lib)
    made += build_lettering(collection, lib)
    made += build_ducktail(collection, lib)
    return made
