"""BYD Seal front end (the 2022-2024 "Dragon Face 3.0" nose), read from the blue car's front
photograph c1_0511.jpg through its solved camera (seal_cam.FRONT_CAM).

What the photograph shows (nothing here is invented):
    * a low bonnet whose leading edge is one straight line across the nose, above the BYD badge
    * thin crescent headlamps: an arched upper edge sweeping down to a sharp inner tip beside the
      badge, a second small "jewel" module inboard, a DRL line along the lower edge that hooks
      down under the lamp's outer end, and a black vertical slit at the outer end
    * two kite-shaped lower intakes whose inner edge is stepped into 5-6 nested chevron ribs
      (white LED lines when lit) - these stand where fog lamps would be
    * the painted bumper's lower edge sweeping up from the corners to the plate, a black slotted
      grille under the plate in three fields, and a black gloss lip as the chin
    * parking sensors, a camera dot over the plate, a small flap left of the plate

Photo pixels are in the 3840 x 2880 originals; the left half of the picture (the car's right) is
read and mirrored.
"""
import math
import bpy
from mathutils import Vector

import seal_surface as S
import seal_nose as N
import seal_lidar as LD
import seal_cam as CAM
from carkit import geom
from carkit import mesh as M
from carkit import cut as C
from carkit.body import fascia as FA
from carkit.body import panels as BP
import carkit.place as P
from carkit.parts import fittings, lamps

BODY = N.BODY
NOSE = N.NOSE

PLACER = P.Placer(N.BODY.proud)
LAMP_BODY = ("Seal_Fascia", "Seal_Fender_Front", "Seal_Hood")
LAMP_CENTRE = (1.88, 0.45, 0.62)


def _lamp_place(p, d=0.0):
    return PLACER.radial(p, LAMP_CENTRE, LAMP_BODY, d)


# ------------------------------------------------------- photo pixels -> the nose's (|y|, z)
def _px_yz(u, v):
    """(|y|, z) of a front-photo pixel ON the nose's own surface: a ray from the camera, the
    plane at the nose's depth there, again (the nose is 0.35 m deeper at the centre than at the
    corners)."""
    x = 2.38
    y = z = 0.0
    for _ in range(4):
        y, z = CAM.front_yz(u, v, x)
        x = NOSE.x_at(abs(y), max(NOSE.Z_LO + 0.004, min(NOSE.Z_HI - 0.004, z)))
    return (abs(y), z)


def _yz_px(px):
    return [_px_yz(u, v) for (u, v) in px]


def _lerp(pts, y):
    pts = sorted(pts)
    if y <= pts[0][0]:
        return pts[0][1]
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if y0 <= y <= y1:
            t = 0.0 if y1 == y0 else (y - y0) / (y1 - y0)
            return z0 + (z1 - z0) * t
    return pts[-1][1]


# the kite-shaped lower intake, car's right (picture left): outer-top apex, over the stepped inner
# edge to the inner tip, back along the lower edge to the outer-bottom corner
INTAKE_PX = [(1282, 1780), (1327, 1784), (1382, 1800), (1427, 1867), (1440, 1889), (1404, 1913),
             (1327, 1964), (1238, 1980), (1160, 1991), (1104, 1997), (1110, 1967), (1138, 1933),
             (1182, 1878), (1238, 1822)]
INTAKE = _yz_px(INTAKE_PX)

# the painted bumper's lower edge (black grille panel below it), from the outer corner to the centre
PAINT_EDGE_PX = [(1010, 2090), (1100, 2086), (1200, 2090), (1260, 2087), (1320, 2065), (1380, 2030),
                 (1450, 2003), (1520, 1987), (1600, 1978), (1700, 1975), (1927, 1975)]
PAINT_EDGE = _yz_px(PAINT_EDGE_PX)

# louvre rows of the black grille under the plate (photo v) and the chin lip's lower edge
SLAT_V = (2003, 2027, 2046, 2064)
CHIN_PX = [(1030, 2100), (1100, 2108), (1200, 2116), (1330, 2125), (1500, 2132), (1700, 2139),
           (1927, 2142)]

PLATE_PITCH = 6.0                 # the nose face here is nearly upright (x 2.40 at z 0.34, 2.41 at 0.45)


# ------------------------------------------------------------------ helpers
def _face(y, z, d=0.0):
    z_clamped = max(NOSE.Z_LO + 0.003, min(NOSE.Z_HI - 0.003, z))
    w, v = NOSE.wv_at(abs(y), z_clamped)
    p, n = NOSE.point(w, v), NOSE.normal(w, v)
    if d:
        p = tuple(p[i] + n[i] * d for i in range(3))
    if y < 0.0:
        p, n = (p[0], -p[1], p[2]), (n[0], -n[1], n[2])
    return p, n


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
    """A thin strip along a polyline (|y|, z) on the nose, `half` metres each side in z, `depth`
    proud (negative: recessed). Mirrored."""
    pts = _resample(pts_yz, n) if n else pts_yz
    cols = [[_face(y, z - half, depth)[0], _face(y, z + half, depth)[0]] for (y, z) in pts]
    ob = M.mesh_from_rows(name, cols, collection)
    ob.data.materials.append(mat)
    M.mirror_y(ob)
    M.finish(ob, thickness=thickness, bevel=0.0)
    return ob


def _ray_poly(p, d, poly):
    """Smallest t > 0 where the ray p + t d meets the closed polygon `poly` (None if it does not)."""
    best = None
    for a, b in zip(poly, poly[1:] + poly[:1]):
        ex, ez = b[0] - a[0], b[1] - a[1]
        den = d[0] * ez - d[1] * ex
        if abs(den) < 1e-12:
            continue
        t = ((a[0] - p[0]) * ez - (a[1] - p[1]) * ex) / den
        s = ((a[0] - p[0]) * d[1] - (a[1] - p[1]) * d[0]) / den
        if t > 1e-6 and 0.0 <= s <= 1.0 and (best is None or t < best):
            best = t
    return best


# ------------------------------------------------------------------ fascia
def _cut_fascia(ob):
    lower = [(-0.02, PAINT_EDGE[-1][1])] + [(y, z) for (y, z) in reversed(PAINT_EDGE)]
    lower += [(PAINT_EDGE[0][0] - 0.01, 0.02), (-0.02, 0.02)]
    cutters = [C.prism_x("_cut_intake_" + ob.name, INTAKE, S.HALF_L + 0.30, S.HALF_L - 0.60),
               C.prism_x("_cut_lower_" + ob.name, lower, S.HALF_L + 0.30, S.HALF_L - 0.60)]
    sheet = C.sheet_bvh(ob)
    C.difference(ob, cutters, "front_cuts_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


def build_fascia(collection, lib):
    made = []
    # 1. the painted nose and bumper, with the intakes and the lower grille panel cut out
    fascia = FA.cap_panel(
        "Seal_Fascia", NOSE, collection, lib,
        N.NOSE_Z_LO + 0.002, N.NOSE_Z_HI - 0.0008,
        0.0, 1.0, 44, 48, mat="paint", top_to_centre=True, cuts=(_cut_fascia,),
    )
    made.append(fascia)

    # 2. the dark apron behind every opening, recessed 2.4 cm (it shows only through the cuts)
    rows, _ = BP.cap_rows(NOSE, N.NOSE_Z_LO + 0.002, 0.640, 0.0, 1.0, 28, 42, offset=-0.024)
    ap = M.mesh_from_rows("Seal_Apron", rows, collection)
    M.orient(ap.data, geom.axial(1.0))
    ap.data.materials.append(lib["black_trim"])
    M.mirror_y(ap)
    M.finish(ap, thickness=0.0025, bevel=0.0)
    made.append(ap)

    # 3. the intake's nested chevron ribs: the innermost follows the stepped inner edge, the others
    # are copies whose apex steps outboard, the legs running out to the opening's edges
    poly = [(y, z) for (y, z) in INTAKE]
    apex0 = min(poly, key=lambda p: p[0])                                  # the inner tip
    ia = poly.index(apex0)
    top_mid = poly[(ia - 3) % len(poly)]                                   # the stepped upper edge
    bot_mid = poly[(ia + 2) % len(poly)]                                   # the lower edge
    def _unit(a):
        L = math.hypot(*a)
        return (a[0] / L, a[1] / L)

    d_up = _unit((top_mid[0] - apex0[0], top_mid[1] - apex0[1]))
    d_lo = _unit((bot_mid[0] - apex0[0], bot_mid[1] - apex0[1]))
    for i in range(6):
        ap_i = (apex0[0] + 0.014 + 0.030 * i, apex0[1] - 0.006 * i)
        if not (0.0 < ap_i[0] < 2.0):
            continue
        tu = _ray_poly(ap_i, d_up, poly)
        tl = _ray_poly(ap_i, d_lo, poly)
        if not tu or not tl:
            continue
        pts = [(ap_i[0] + d_up[0] * (tu - 0.004), ap_i[1] + d_up[1] * (tu - 0.004)), ap_i,
               (ap_i[0] + d_lo[0] * (tl - 0.004), ap_i[1] + d_lo[1] * (tl - 0.004))]
        line = _resample(pts, 18)
        made.append(_strip("Seal_Intake_Rib_%d" % i, line, 0.0045, -0.014, collection, lib["logo_chrome"], thickness=0.0035))

    # 4. the lower grille under the plate: louvre rows and two short fins dividing it into fields
    for idx, vrow in enumerate(SLAT_V):
        z_k = CAM.front_yz(1927, vrow, 2.40)[1]
        ymax = 0.52 if idx < 2 else 0.47
        pts = [(ymax * j / 14.0, z_k) for j in range(15)]
        made.append(_strip("Seal_Grille_Slat_%d" % idx, pts, 0.0045, -0.012, collection, lib["black_gloss"], thickness=0.002))
    for idx, u_f in enumerate((1760,)):
        yf, zf = CAM.front_yz(u_f, 2020, 2.40)
        p_f, _ = _face(abs(yf), zf, d=-0.004)
        fin = _box("Seal_Grille_Fin_%d" % idx, p_f, (0.006, 0.010, 0.060), collection, lib["trim_chrome"])
        M.mirror_y(fin)
        made.append(fin)

    # 5. the chin: a black gloss lip along the bumper's lower edge, with a thin silver line over it
    chin = _yz_px([(u, v) for (u, v) in CHIN_PX])
    made.append(_strip("Seal_Chin_Lip", chin, 0.0095, 0.006, collection, lib["black_gloss"], n=40, thickness=0.003))
    chin_hi = [(y, z + 0.0125) for (y, z) in _resample(chin, 40)]
    made.append(_strip("Seal_Chin_Silver", chin_hi, 0.0016, 0.0075, collection, lib["trim_chrome"], thickness=0.0016))

    # 6. parking sensors, the camera dot over the plate
    for nm, (u, v) in (("Seal_Sensor_Bumper", (1193, 1753)), ("Seal_Sensor_Outer", (1138, 1812))):
        y, z = _px_yz(u, v)
        p, n = _face(y, z, d=0.0022)
        made += lamps.projector(nm, p, n, 0.0105, collection, lib, mats=("lamp_bowl", "lamp_smoked"))
    y, z = _px_yz(1927, 1808)
    p, n = _face(0.0, z, d=0.002)
    made.append(_box("Seal_Front_Camera", p, (0.006, 0.020, 0.020), collection, lib["black_gloss"]))

    # 7. the front plate: the BYD SEAL showroom plate (the owner's photograph shows it)
    pitch = math.radians(PLATE_PITCH)
    n_plate = (math.cos(pitch), 0.0, -math.sin(pitch))
    y_p, z_p = _px_yz(1927, 1911)
    p_c, _ = _face(0.0, z_p, d=0.004)
    p_plate_f = (p_c[0], 0.0, p_c[2])
    p_mount = tuple(p_plate_f[i] - n_plate[i] * 0.002 for i in range(3))
    made += fittings.plate("Seal_Plate_Mount_Front", p_mount, n_plate, collection, lib, w=0.464, h=0.158, depth=0.030,
                           mat="black_gloss", bevel=(0.003, 2, 30))
    made += fittings.plate("Seal_Plate_Front", p_plate_f, n_plate, collection, lib, w=0.440, h=0.140, depth=0.004,
                           texts=[("BYD SEAL", 0.0, 0.036, False, True)],
                           mat="black_gloss", text_mat="machined")
    return made


# ------------------------------------------------------------- headlamps
# car's right (picture left), from the inner tip beside the badge out to the lamp's outer end
LAMP_UP_PX = [(1536, 1658), (1504, 1639), (1427, 1594), (1338, 1553), (1249, 1522), (1160, 1511), (1104, 1528)]
LAMP_LO_PX = [(1536, 1658), (1438, 1642), (1327, 1631), (1238, 1620), (1160, 1611), (1110, 1609)]
# the DRL's hook under the lamp's outer end (a thin curved blade) and the black slit at the outer end
HOOK_UP_PX = [(1288, 1700), (1216, 1694), (1138, 1678), (1099, 1644)]
HOOK_LO_PX = [(1288, 1710), (1216, 1705), (1140, 1690), (1096, 1656)]
SLIT_UP_PX = [(1112, 1531), (1112, 1644)]
SLIT_LO_PX = [(1084, 1531), (1084, 1644)]
# the stepped inner "jewel" module and the big outer projector, picture coordinates of their centres
JEWEL_PX = [(1368, 1594), (1405, 1610)]
PROJ_PX = [(1218, 1578, 0.0195), (1290, 1591, 0.0195)]
FRONT_CAMERA = "front_blue"


def _hit(bodies, u, v, fallback):
    """The photo ray's first hit on the body meshes, mirrored to y >= 0 (None -> fallback)."""
    try:
        import seal_ref_match as RM
        h = RM.on_mesh(FRONT_CAMERA, u, v, bodies)
    except Exception as e:                              # no camera / no mesh: use the plane fit
        print("seal_front: ray cast failed:", e)
        h = None
    if h is None:
        return fallback
    return (h[0], abs(h[1]), h[2])


def build_headlamps(collection, lib):
    made = []
    PLACER.reset()
    bodies = [bpy.data.objects[n] for n in LAMP_BODY if n in bpy.data.objects]
    try:
        import seal_ref_match as RM
        RM.clear_bvh()
    except Exception:
        pass

    def pts3(px):
        out = []
        for (u, v) in px:
            y, z = _px_yz(u, v)
            out.append(_hit(bodies, u, v, (NOSE.x_at(y, max(NOSE.Z_LO + 0.004, min(NOSE.Z_HI - 0.004, z))), y, z)))
        return out

    NS, NK = 64, 8
    up = geom.polyline(pts3(LAMP_UP_PX), NS)
    lo = geom.polyline(pts3(LAMP_LO_PX), NS)
    out = geom.away_from((1.86, 0.45, 0.60))

    def _crown(k, extra=0.0):
        return 0.0030 + 0.0013 * math.sin(math.pi * max(0.0, min(1.0, k))) + extra

    # dark housing behind the lens, and a satin gasket round both edges
    made.append(lamps.lens("Seal_Headlamp_Housing", lo, up, _lamp_place, collection, lib["lamp_housing"],
                           NK, lambda k, nk: 0.0016, out, thickness=0.0025, bevel=0.0))
    made += lamps.seals("Seal_Headlamp_Seal", lo, up, _lamp_place, collection, lib["grille"], out,
                        width=0.0040, d=0.0011)

    # the DRL: a thin white line along the lower edge, from the inner tip out to the outer end
    made.append(lamps.band_between(
        "Seal_Headlamp_DRL", lo, up, range(2, int(NS * 0.97)), [0.035, 0.075, 0.115],
        _lamp_place, lambda k: _crown(k, 0.0022), collection, lib["led_white"], out))

    # the stepped inner "jewel" module: two small dark LED squares with chrome edges
    ju = pts3(JEWEL_PX)
    for idx, p in enumerate(ju):
        c, n = _lamp_place(p, 0.0068)
        made += _square("Seal_Headlamp_Jewel_%d" % idx, c, n, 0.0150, 0.0105, collection, lib)
    # two round projectors in the big outer lens
    for idx, (u, v, r) in enumerate(PROJ_PX):
        p = pts3([(u, v)])[0]
        c, n = _lamp_place(p, 0.0068)
        made += lamps.projector("Seal_Headlamp_Proj_%d" % idx, c, n, r, collection, lib,
                                mats=("lamp_bowl", "lamp_smoked"))
        made.append(_ring("Seal_Headlamp_ProjRing_%d" % idx, c, n, r * 0.98, r * 1.22, collection, lib["logo_chrome"]))

    # the smoked lens over everything
    made.append(lamps.lens("Seal_Headlamp_Lens", lo, up, _lamp_place, collection, lib["lamp_clear"],
                           NK, lambda k, nk: _crown(k / float(nk), 0.0006), out,
                           thickness=0.0022, bevel=(0.0010, 2, 30)))

    # the upper edge: a slim black brow that sharpens the crease
    made.append(lamps.band_between(
        "Seal_Headlamp_Brow", lo, up, range(1, int(NS * 0.985)), [0.93, 0.975, 1.0],
        _lamp_place, lambda k: _crown(k, 0.0050), collection, lib["black_gloss"], out))

    # the DRL's hook under the outer end
    hu = geom.polyline(pts3(HOOK_UP_PX), 36)
    hl = geom.polyline(pts3(HOOK_LO_PX), 36)
    out_h = geom.away_from((1.86, 0.45, 0.55))
    made.append(lamps.lens("Seal_Hook_Housing", hl, hu, _lamp_place, collection, lib["black_gloss"], 3,
                           lambda k, nk: 0.0020, out_h, thickness=0.0022, bevel=0.0))
    made.append(lamps.band_between("Seal_Hook_DRL", hl, hu, range(36), [0.30, 0.50, 0.70],
                                   _lamp_place, lambda k: 0.0040, collection, lib["led_white"], out_h))

    # the black slit at the outer end
    su = geom.polyline(pts3(SLIT_UP_PX), 12)
    sl = geom.polyline(pts3(SLIT_LO_PX), 12)
    out_s = geom.away_from((1.86, 0.45, 0.60))
    made.append(lamps.lens("Seal_Lamp_Slit", sl, su, _lamp_place, collection, lib["black_gloss"], 2,
                           lambda k, nk: 0.0008, out_s, thickness=0.0020, bevel=0.0))
    made.append(lamps.band_between("Seal_Lamp_Slit_Edge", sl, su, range(12), [0.0, 0.14],
                                   _lamp_place, lambda k: 0.0014, collection, lib["trim_chrome"], out_s))
    return made


def _square(name, c, n, hw, hh, collection, lib):
    """A small rectangular LED module: chrome frame, dark bowl, white LED bar."""
    nvec = Vector(n).normalized()
    upv = Vector((0, 0, 1)) if abs(nvec.z) < 0.9 else Vector((1, 0, 0))
    t1 = nvec.cross(upv).normalized()
    t2 = nvec.cross(t1).normalized()
    made = []
    for tag, kx, ky, lift, mat in (("Frame", 1.0, 1.0, 0.0, lib["logo_chrome"]),
                                   ("Bowl", 0.80, 0.78, 0.0006, lib["lamp_bowl"]),
                                   ("Led", 0.62, 0.20, 0.0012, lib["led_white"])):
        cv = Vector(c) + nvec * lift
        v = [tuple(cv + t1 * (sx * hw * kx) + t2 * (sy * hh * ky)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        ob = M.obj(name + tag, v, [[0, 1, 2, 3]], collection, mat)
        M.orient(ob.data, lambda cc, nv=nvec: tuple(nv))
        M.mirror_y(ob)
        made.append(ob)
    return made


def _ring(name, c, n, r_in, r_out, collection, mat, seg=18):
    nvec = Vector(n).normalized()
    upv = Vector((0, 0, 1)) if abs(nvec.z) < 0.9 else Vector((1, 0, 0))
    t1 = nvec.cross(upv).normalized()
    t2 = nvec.cross(t1).normalized()
    cols = []
    for i in range(seg + 1):
        a = 2.0 * math.pi * (i / float(seg))
        d_vec = t1 * math.cos(a) + t2 * math.sin(a)
        cols.append([tuple(Vector(c) + d_vec * r_in), tuple(Vector(c) + d_vec * r_out)])
    ob = M.mesh_from_rows(name, cols, collection)
    ob.data.materials.append(mat)
    M.mirror_y(ob)
    M.finish(ob, thickness=0.0018, bevel=0.0)
    return ob


# --------------------------------------------------------------- the badge
def _font(fn):
    import os
    d = os.path.join(os.path.dirname(bpy.app.binary_path), bpy.app.version_string.rsplit(".", 1)[0],
                     "datafiles", "fonts")
    try:
        return bpy.data.fonts.load(os.path.join(d, fn), check_existing=True)
    except Exception:
        return None


def build_emblem(collection, lib):
    """The wide-spaced chrome BYD wordmark on the nose, under the bonnet's leading edge: 267 px wide
    (0.26 m) and 24 px high (0.023 m) at z 0.632 in the photograph."""
    made = []
    inter = _font("Inter.woff2")
    y0, z_c = _px_yz(1927, 1669)
    for i, (ch, dy) in enumerate((("B", -0.093), ("Y", 0.0), ("D", 0.093))):
        p, n = _face(abs(dy), z_c, d=0.0016)
        if dy < 0.0:
            p, n = (p[0], -p[1], p[2]), (n[0], -n[1], n[2])
        emb = M.text_mesh("Seal_Emblem_Front_%s" % ch, ch, 0.026, collection, lib["logo_chrome"],
                          extrude=0.0016, font=inter, resolution=4)
        P.on_surface(emb, p, n)
        made.append(emb)
    return made


def build_hood_features(collection, lib):
    """The two soft ridges that run back along the bonnet from the lamps' inner tips to the screen's corners
    (c1_0511: straight lines at y +-0.37..0.40, faint highlights that bound a central panel)."""
    cols = []
    nc = 40
    for i in range(nc + 1):
        t = i / float(nc)
        x = 1.10 + (2.22 - 1.10) * t
        y_c = 0.395 - 0.020 * t
        row = []
        for dy in (-0.034, -0.018, -0.006, 0.0, 0.006, 0.018, 0.034):
            v = S.v_at_y_upper(x, y_c + dy)
            y_s, z_s = S.section_v(x, v)
            lift = 0.0024 * math.cos(0.5 * math.pi * dy / 0.034) ** 2.0 * math.sin(math.pi * min(1.0, t * 1.02)) ** 0.9
            row.append((x, y_s, z_s + lift - 0.0006))
        cols.append(row)
    ob = M.mesh_from_rows("Seal_Hood_Ridge", cols, collection)
    M.orient(ob.data, lambda c: (0.0, 0.0, 1.0))
    ob.data.materials.append(lib["paint"])
    M.mirror_y(ob)
    M.finish(ob, thickness=0.0016, bevel=0.0)
    return [ob]


def build_all(collection, lib):
    made = []
    made += build_fascia(collection, lib)
    made += build_headlamps(collection, lib)
    made += build_emblem(collection, lib)
    made += build_hood_features(collection, lib)
    made += LD.build_all(collection, lib)
    return made
