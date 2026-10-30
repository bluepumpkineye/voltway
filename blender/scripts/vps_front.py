"""Voyah Passion S (岚图追光S) front end, calibrated to studio front photo c1_0002.jpg via vps_cam.FRONT_CAM.

Key Passion S front-end features read directly off front_grid.png (3840 x 2880):
  - Winged upper DRL assemblies at the bonnet corners with dual-row angled white LED blades,
    linked across the nose by a slim gloss-black channel and continuous illuminated light bar
  - Illuminated Voyah Kunpeng winged V-emblem centred in the nose channel
  - Smoked horizontal lower main-beam pods housing twin rectangular LED projectors [o] [o]
  - Connected gloss-black cheek pockets (with horizontal aero strake) and trapezoidal active-shutter
    lower grille (with square central mmWave radar) wrapping around continuous body-coloured lower aero fangs
  - Full-width gloss-black chin splitter, front surround camera, circular tow-eye cover, parking sensors,
    and Huawei Qiankun ADS 4.1 896-line roof LiDAR pod
"""
import math

import bpy

import vps_surface as S
import vps_nose as N
import vps_panels as PN
import vps_cam as CAM
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
LAMP_BODY = ("VPS_Fascia", "VPS_Fender_Front", "VPS_Hood")
LAMP_CENTRE = (1.95, 0.45, 0.65)


def _lamp_place(p, d=0.0):
    return PLACER.radial(p, LAMP_CENTRE, LAMP_BODY, d)


# ------------------------------------------------------- front photo pixels -> nose (|y|, z)
def _px_yz(u, v):
    x = 2.42
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


# Pixel outlines read off front_grid.png (right half u <= 1920, mirrored to both sides)
DRL_UP_PX = [(1088, 1396), (1150, 1412), (1230, 1438), (1320, 1472), (1402, 1502)]
DRL_LO_PX = [(1086, 1468), (1120, 1502), (1185, 1515), (1270, 1516), (1350, 1514), (1402, 1514)]

CHANNEL_UP_PX = [(1402, 1502), (1540, 1512), (1700, 1516), (1858, 1516), (1920, 1516)]
CHANNEL_LO_PX = [(1402, 1516), (1540, 1530), (1700, 1536), (1858, 1538), (1920, 1538)]

POD_UP_PX = [(1102, 1620), (1210, 1620), (1338, 1626)]
POD_LO_PX = [(1096, 1698), (1210, 1698), (1380, 1700)]

# Connected dark mask cutout preserving the continuous painted lower aero fang (u 1112..1524, v 1836..1998)
MASK_CUT_SIDE_PX = [
    (1102, 1620), (1215, 1620), (1338, 1626), (1382, 1700),
    (1445, 1744), (1525, 1790), (1605, 1808),
]
MASK_CUT_LOW_PX = [
    (1335, 2000), (1425, 1938), (1524, 1846),
    (1410, 1836), (1305, 1846), (1205, 1886), (1128, 1928),
    (1108, 1916), (1098, 1855), (1092, 1760), (1094, 1680),
]

CHIN_PX = [
    (1072, 1996), (1140, 2012), (1260, 2020), (1450, 2022),
    (1680, 2022), (1920, 2022),
]

PLATE_PX = (1700, 1742, 2140, 1898)
CAMERA_PX = (1920, 1720)
TOWCAP_PX = (1425, 1796)
SENSORS_PX = [(1078, 1792), (1362, 1812), (1625, 1872)]

_z_mask_hi = _px_yz(1920, 1810)[1]
_z_mask_lo = _px_yz(1920, 2002)[1]
MASK_CUT = _yz_px(MASK_CUT_SIDE_PX) + [(-0.025, _z_mask_hi), (-0.025, _z_mask_lo)] + _yz_px(MASK_CUT_LOW_PX)
CHIN = _yz_px(CHIN_PX)
CHIN[-1] = (0.0, CHIN[-1][1])
PLATE_Z = _px_yz(1920, 0.5 * (PLATE_PX[1] + PLATE_PX[3]))[1]


# ------------------------------------------------------------------ helpers
def _box(name, c, size, collection, mat):
    x, y, z = c
    hx, hy, hz = (0.5 * t for t in size)
    v = [(x + sx * hx, y + sy * hy, z + sz * hz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    f = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
    return M.obj(name, v, f, collection, mat)


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


def _strip(name, pts_yz, half, depth, collection, mat, n=None, thickness=0.0022):
    pts = _resample(pts_yz, n) if n else pts_yz
    cols = [[_face(y, z - half, depth)[0], _face(y, z + half, depth)[0]] for (y, z) in pts]
    ob = M.mesh_from_rows(name, cols, collection)
    ob.data.materials.append(mat)
    M.mirror_y(ob)
    M.finish(ob, thickness=thickness, bevel=0.0)
    return ob


def _cut_openings(ob):
    """Cut the connected cheek/projector/lower-grille mask and trim below the chin line."""
    chin_cut = [(-0.02, CHIN[-1][1])] + [(y, z) for (y, z) in reversed(CHIN)] + [
        (CHIN[0][0] + 0.03, 0.05), (-0.02, 0.05)
    ]
    cutters = [
        C.prism_x("_cut_mask_" + ob.name, MASK_CUT, S.HALF_L + 0.30, S.HALF_L - 0.65),
        C.prism_x("_cut_chin_" + ob.name, chin_cut, S.HALF_L + 0.30, S.HALF_L - 0.65),
    ]
    sheet = C.sheet_bvh(ob)
    C.difference(ob, cutters, "front_cuts_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


# ------------------------------------------------------------------ fascia
def build_fascia(collection, lib):
    made = []
    fascia = FA.cap_panel(
        "VPS_Fascia", NOSE, collection, lib,
        N.NOSE_Z_LO + 0.0008, N.NOSE_Z_HI - 0.0008,
        0.0, 1.0, 48, 52, mat="paint", top_to_centre=True,
        cuts=(_cut_openings,))
    made.append(fascia)

    # Recessed gloss-black mask behind the cheek pockets & active-shutter lower grille
    rows, _ = BP.cap_rows(NOSE, N.NOSE_Z_LO + 0.002, 0.800, 0.0, 1.0, 24, 36,
                          offset=-0.020, top_to_centre=True)
    ap = M.mesh_from_rows("VPS_Apron", rows, collection)
    M.orient(ap.data, geom.axial(1.0))
    ap.data.materials.append(lib["black_gloss"])
    M.mirror_y(ap)
    M.finish(ap, thickness=0.0025, bevel=0.0)
    made.append(ap)

    # Cheek horizontal aero strake inside the outer intake pocket (front_grid u 1125..1285, v 1812)
    strake_yz = _yz_px([(1118, 1812), (1200, 1812), (1285, 1814)])
    made.append(_strip("VPS_Cheek_Strake", strake_yz, 0.0055, -0.006, collection,
                       lib["black_gloss"], n=12, thickness=0.003))
    return made


# --------------------------------------------------------- grille, radar & chin
def build_grille(collection, lib):
    made = []
    _, z_top = _px_yz(1700, 1892)
    _, z_lo = _px_yz(1700, 1996)

    # Vertical active-shutter grille dividers either side of the central square mmWave radar
    verts, faces = [], []
    wid, dep = 0.0040, 0.008
    for side in (1.0, -1.0):
        for y in (0.145, 0.235, 0.325, 0.415, 0.505):
            zt = z_top - 0.006 if y < 0.44 else z_top - 0.028
            x_f = min(_face(y, zt)[0][0], _face(y, z_lo)[0][0]) - 0.015
            x_b = x_f - dep
            k = len(verts)
            for (xx, zz) in ((x_b, z_lo), (x_f, z_lo), (x_f, zt), (x_b, zt)):
                verts.append((xx, side * (y - wid * 0.5), zz))
                verts.append((xx, side * (y + wid * 0.5), zz))
            faces += [[k + 0, k + 1, k + 3, k + 2], [k + 2, k + 3, k + 5, k + 4],
                      [k + 4, k + 5, k + 7, k + 6], [k + 6, k + 7, k + 1, k + 0],
                      [k + 0, k + 2, k + 4, k + 6], [k + 1, k + 7, k + 5, k + 3]]
    # Horizontal mid bar across the active grille
    z_mid = 0.5 * (z_top + z_lo)
    for side in (1.0, -1.0):
        k = len(verts)
        for (yy, zz) in ((0.115, z_mid - 0.003), (0.545, z_mid - 0.003),
                         (0.545, z_mid + 0.003), (0.115, z_mid + 0.003)):
            xf = _face(yy, zz)[0][0] - 0.014
            verts.append((xf - 0.006, side * yy, zz))
            verts.append((xf, side * yy, zz))
        faces += [[k + 0, k + 1, k + 3, k + 2], [k + 2, k + 3, k + 5, k + 4],
                  [k + 4, k + 5, k + 7, k + 6], [k + 6, k + 7, k + 1, k + 0]]
    made.append(M.obj("VPS_Grille_Slats", verts, faces, collection, lib["black_trim"], smooth=False))

    # Central square mmWave radar module (front_grid u 1820..2020, v 1898..1988)
    yr, zr_t = _px_yz(1822, 1898)
    _, zr_b = _px_yz(1822, 1988)
    radar_rows = []
    for y in (0.0, yr * 0.5, yr):
        radar_rows.append([_face(y, zr_b, -0.008)[0], _face(y, zr_t, -0.008)[0]])
    rd = M.mesh_from_rows("VPS_Radar_Cover", radar_rows, collection)
    rd.data.materials.append(lib["radar"])
    M.mirror_y(rd)
    M.finish(rd, thickness=0.003, bevel=0.0)
    made.append(rd)

    # Full-width gloss-black chin splitter along the lower bumper edge
    made.append(_strip("VPS_Chin_Lip", [(y, z - 0.016) for (y, z) in _resample(CHIN, 44)],
                       0.024, 0.012, collection, lib["black_gloss"], thickness=0.0035))
    return made


# --------------------------------------------------------- split headlamps & channel
def _hit(bodies, u, v, fallback):
    try:
        import vps_ref_match as RM
        h = RM.on_mesh("front", u, v, bodies)
    except Exception:
        h = None
    if h is None:
        return fallback
    return (h[0], abs(h[1]), h[2])


def build_headlamps(collection, lib):
    made = []
    PLACER.reset()
    bodies = [bpy.data.objects[n] for n in LAMP_BODY if n in bpy.data.objects]
    try:
        import vps_ref_match as RM
        RM.clear_bvh()
    except Exception:
        pass

    def pts3(px):
        out = []
        for (u, v) in px:
            y, z = _px_yz(u, v)
            out.append(_hit(bodies, u, v, (NOSE.x_at(y, max(NOSE.Z_LO + 0.004, min(NOSE.Z_HI - 0.004, z))), y, z)))
        return out

    NS, NK = 44, 5
    out = geom.away_from((1.90, 0.45, 0.65))

    def _crown(k, extra=0.0):
        return 0.0026 + 0.0010 * math.sin(math.pi * max(0.0, min(1.0, k))) + extra

    # 1. Winged upper DRL housing, dual-row white LED blades, and smoked crystal lens
    up = geom.polyline(pts3(DRL_UP_PX), NS)
    lo = geom.polyline(pts3(DRL_LO_PX), NS)
    made.append(lamps.lens("VPS_DRL_Housing", lo, up, _lamp_place, collection, lib["lamp_housing"],
                           NK, lambda k, nk: 0.0012, out, thickness=0.0025, bevel=0.0))
    made += lamps.seals("VPS_DRL_Seal", lo, up, _lamp_place, collection, lib["black_gloss"], out,
                        width=0.0032, d=0.0012)
    made.append(lamps.lens("VPS_DRL_Lens", lo, up, _lamp_place, collection, lib["lamp_clear"],
                           NK, lambda k, nk: _crown(k / float(nk), 0.0005), out,
                           thickness=0.0018, bevel=(0.0008, 2, 30)))
    made.append(lamps.band_between("VPS_DRL_Bar", lo, up, range(2, int(NS * 0.98)), [0.16, 0.25, 0.34],
                                   _lamp_place, lambda k: _crown(k, 0.0024), collection, lib["lamp_white_bar"], out))
    for b_idx in range(5):
        s0 = 4 + b_idx * 7
        made.append(lamps.band_between("VPS_DRL_Blade_%d" % b_idx, lo, up, range(s0, min(NS - 2, s0 + 5)),
                                       [0.52, 0.65, 0.78], _lamp_place, lambda k: _crown(k, 0.0022),
                                       collection, lib["led_white"], out))

    # 2. Full-width gloss-black nose channel & continuous illuminated white light strip
    ch_yz = [0.5 * (u_pt[1] + l_pt[1]) for u_pt, l_pt in zip(_yz_px(CHANNEL_UP_PX), _yz_px(CHANNEL_LO_PX))]
    ch_line = [(u_pt[0], zc) for u_pt, zc in zip(_yz_px(CHANNEL_UP_PX), ch_yz)]
    ch_line[-1] = (0.0, ch_line[-1][1])
    made.append(_strip("VPS_Nose_Channel", ch_line, 0.0095, 0.0014, collection,
                       lib["black_gloss"], n=28, thickness=0.0024))
    made.append(_strip("VPS_Nose_LightBar", [(y, z - 0.001) for (y, z) in ch_line], 0.0028, 0.0028,
                       collection, lib["lamp_white_bar"], n=28, thickness=0.0018))

    # 3. Lower horizontal smoked main-beam pod with visible twin LED projectors [o] [o]
    pu = geom.polyline([(_face(y, z, -0.012)[0]) for (y, z) in _yz_px(POD_UP_PX)], 28)
    pl = geom.polyline([(_face(y, z, -0.012)[0]) for (y, z) in _yz_px(POD_LO_PX)], 28)
    made.append(lamps.lens("VPS_MainPod_Housing", pl, pu, lambda p, d=0.0: (p, (1.0, 0.0, 0.0)),
                           collection, lib["lamp_housing"], 4, lambda k, nk: 0.0, out,
                           thickness=0.0025, bevel=0.0))
    made += lamps.seals("VPS_MainPod_Seal", pl, pu,
                        lambda p, d=0.0: ((p[0] + 0.005, p[1], p[2]), (1.0, 0.0, 0.0)),
                        collection, lib["black_gloss"], out, width=0.0038, d=0.0008)
    for i, (u, v) in enumerate(((1166, 1658), (1268, 1660))):
        y, z = _px_yz(u, v)
        p, n = _face(y, z, -0.004)
        # Rectangular satin-chrome bezel framing each crystal projector lens
        bz = fittings.rounded_panel("VPS_MainProj_Bezel_%d" % i, (p[0] - 0.002, p[1], p[2]),
                                    0.028, 0.019, 0.007,
                                    lambda q, d: ((q[0] + d, q[1], q[2]), n),
                                    p[0] - 0.002, collection, lib["machined"], d=0.0015,
                                    outward=(1.0, 0.0, 0.0))
        M.mirror_y(bz)
        made.append(bz)
        made += lamps.projector("VPS_MainProj_%d" % i, p, n, 0.0175, collection, lib,
                                mats=("lamp_bowl", "lamp_smoked"))
    return made


# --------------------------------------------------------- Kunpeng V-emblem, plate & lidar
def build_emblem(collection, lib):
    """Illuminated Voyah Kunpeng winged V-emblem centred on the nose channel (u 1858..1982, v 1512..1652)."""
    _, z_top = _px_yz(1920, 1514)
    _, z_bot = _px_yz(1920, 1650)
    y_top, _ = _px_yz(1860, 1518)
    zc = 0.5 * (z_top + z_bot)
    hh = 0.5 * (z_top - z_bot)
    hw = y_top
    p, n = _face(0.0, zc, 0.0032)

    # Outer gloss-black winged V-shield backing
    shield = [
        (0.0, hh * 0.62), (hw, hh), (hw * 0.86, hh * 0.35),
        (hw * 0.24, -hh * 0.72), (0.0, -hh), (-hw * 0.24, -hh * 0.72),
        (-hw * 0.86, hh * 0.35), (-hw, hh),
    ]
    sv = [(q[0], q[1], 0.0) for q in shield]
    sf = [[0, 1, 2, 3], [0, 3, 4, 5], [0, 5, 6, 7]]
    sh = M.obj("VPS_Emblem_Shield", sv, sf, collection, lib["black_gloss"], smooth=False)
    M.solidify(sh, 0.0030)
    P.on_surface(sh, p, n)

    # Inner illuminated white Kunpeng wings + centre spine
    p_lit = tuple(p[i] + n[i] * 0.0022 for i in range(3))
    wv, wf = [], []
    for s in (1.0, -1.0):
        k = len(wv)
        pts = [
            (s * 0.006, hh * 0.42), (s * hw * 0.82, hh * 0.86),
            (s * hw * 0.68, hh * 0.36), (s * 0.006, -hh * 0.82),
        ]
        for q in pts:
            wv.append((q[0], q[1], 0.0))
        wf.append([k, k + 1, k + 2, k + 3] if s > 0 else [k, k + 3, k + 2, k + 1])
    lit = M.obj("VPS_Emblem_Lit", wv, wf, collection, lib["lamp_white_bar"], smooth=False)
    M.solidify(lit, 0.0022)
    P.on_surface(lit, p_lit, n)
    return [sh, lit]


def build_plate(collection, lib):
    made = []
    p, n = _face(0.0, PLATE_Z, 0.004)
    p_mount = tuple(p[i] - n[i] * 0.003 for i in range(3))
    made += fittings.plate("VPS_Plate_Mount_Front", p_mount, n, collection, lib, w=0.500, h=0.160, depth=0.028,
                           mat="black_gloss", bevel=(0.003, 2, 30))
    made += fittings.plate("VPS_Plate_Front", p, n, collection, lib, w=0.480, h=0.140, depth=0.004,
                           texts=[("VOYAH 追光S", 0.0, 0.036, False, True)],
                           mat="black_gloss", text_mat="chrome")
    _, zc = _px_yz(*CAMERA_PX)
    pc, nc = _face(0.0, zc, 0.0025)
    made += lamps.projector("VPS_Front_Camera", pc, nc, 0.0085, collection, lib,
                            mats=("black_gloss", "lamp_smoked"))
    for i, (u, v) in enumerate(SENSORS_PX):
        y, z = _px_yz(u, v)
        ps, ns = _face(y, z, 0.0018)
        made += lamps.projector("VPS_Sensor_F_%d" % i, ps, ns, 0.0095, collection, lib,
                                mats=("black_gloss", "lamp_smoked"))
    yt, zt = _px_yz(*TOWCAP_PX)
    ring = [(yt + 0.024 * math.cos(2.0 * math.pi * i / 24.0),
             zt + 0.024 * math.sin(2.0 * math.pi * i / 24.0)) for i in range(25)]
    tc = M.strip("VPS_Tow_Cap_F", [_face(py, pz, 0.0007)[0] for (py, pz) in ring],
                 [_face(py, pz, -0.0007)[0] for (py, pz) in ring], collection, lib["shadow"])
    M.mirror_y(tc)
    made.append(tc)
    return made


def build_lidar(collection, lib):
    """Huawei Qiankun ADS 4.1 896-line roof LiDAR pod (side_grid_mid x 0.16..0.37, top z 1.658)."""
    cx, a, b, c = 0.268, 0.112, 0.148, 0.056
    zc = S.Z_ROOF(cx) + 0.038
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
    pod = M.obj("VPS_Lidar", verts, faces, collection, lib["black_gloss"])
    M.orient(pod.data, geom.away_from((cx, 0.0, zc - 0.02)))
    win = fittings.rounded_panel("VPS_Lidar_Window", (cx + a * 0.93, 0.0, zc + 0.024), 0.096, 0.015, 0.008,
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
    made += build_emblem(collection, lib)
    made += build_plate(collection, lib)
    made += build_lidar(collection, lib)
    return made
