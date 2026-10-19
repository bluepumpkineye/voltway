"""Nio ES8 front end: Shark-Nose X-Bar fascia, Double-Dash dual-layer crystal DRLs,
recessed vertical HDPL MicroLED projector headlamps, trapezoidal active lower grille,
full-width chrome lower chin blade, NIO Sky-and-Earth emblem, and Watchtower roof
LiDAR + corner camera pods.
"""
import math

import es8_surface as S
import es8_nose as N
import es8_panels as PN
from carkit import geom
from carkit import mesh as M
from carkit import cut as C
from carkit import place as P
from carkit.body import fascia as FA
from carkit.body import panels as BP
from carkit.parts import fittings, lamps

BODY = N.BODY
NOSE = N.NOSE
PLACER = P.Placer(BODY.proud)

# --------------------------------------------------------------- hardpoints
# Double-Dash dual-layer crystal DRLs (spanning from near central emblem to outer bonnet edge)
HOUSE_UP_XY = [(2.542, 0.380), (2.518, 0.480), (2.476, 0.590), (2.418, 0.690), (2.355, 0.765)]
HOUSE_LO_XY = [(2.576, 0.380), (2.552, 0.480), (2.510, 0.590), (2.452, 0.690), (2.390, 0.765)]

UP_IN_UP_XY  = [(2.545, 0.395), (2.530, 0.480), (2.508, 0.575)]
UP_IN_LO_XY  = [(2.560, 0.395), (2.545, 0.480), (2.523, 0.575)]
UP_OUT_UP_XY = [(2.482, 0.595), (2.432, 0.685), (2.370, 0.760)]
UP_OUT_LO_XY = [(2.497, 0.595), (2.447, 0.685), (2.385, 0.760)]

LO_IN_UP_XY  = [(2.561, 0.405), (2.546, 0.480), (2.524, 0.575)]
LO_IN_LO_XY  = [(2.573, 0.405), (2.558, 0.480), (2.536, 0.575)]
LO_OUT_UP_XY = [(2.498, 0.595), (2.448, 0.685), (2.386, 0.755)]
LO_OUT_LO_XY = [(2.510, 0.595), (2.460, 0.685), (2.398, 0.755)]

# Vertical HDPL projector headlamp pocket in outer bumper cheek (y, z loop)
POCKET_YZ = [
    (0.750, 0.805),
    (0.845, 0.812),
    (0.868, 0.785),
    (0.872, 0.675),
    (0.862, 0.560),
    (0.830, 0.542),
    (0.755, 0.548),
    (0.742, 0.675),
]

# Trapezoidal lower active grille opening (half-outline y, z)
BAND_OUTLINE = [
    (-0.020, 0.465),
    ( 0.540, 0.462),
    ( 0.630, 0.435),
    ( 0.685, 0.340),
    ( 0.655, 0.305),
    (-0.020, 0.305),
]
BAND_RECESS = 0.030


# ----------------------------------------------------------------- helpers
def face(y, z, d=0.0):
    zc = max(NOSE.Z_LO + 0.005, min(NOSE.Z_HI - 0.002, z))
    w, v = NOSE.wv_at(abs(y), zc)
    w_safe = min(0.985, w)
    p, n = NOSE.point(w_safe, v), NOSE.normal(w_safe, v)
    if d:
        p = tuple(p[i] + n[i] * d for i in range(3))
    if y < 0.0:
        p, n = (p[0], -p[1], p[2]), (n[0], -n[1], n[2])
    return p, n


def _on_face(yz, n=32):
    path = geom.polyline([(0.0, y, z) for (y, z) in yz], n)
    return [face(y, z)[0] for (_x, y, z) in path]


def _place(p, d):
    return face(p[1], p[2], d)


def _cut_band(ob):
    c = C.prism_x("_band_" + ob.name, BAND_OUTLINE, S.HALF_L + 0.35, S.HALF_L - 0.65)
    sheet = C.sheet_bvh(ob)
    C.difference(ob, [c], "band_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


def _pocket_loop():
    pts, ns = [], []
    for (_x, y, z) in geom.polyline([(0.0, y, z) for (y, z) in POCKET_YZ + POCKET_YZ[:1]], 44)[:-1]:
        p, n = face(y, z)
        pts.append(p)
        ns.append(n)
    d = [sum(n[i] for n in ns) for i in range(3)]
    L = math.sqrt(sum(c * c for c in d))
    return pts, tuple(c / L for c in d)


def _cut_pocket(ob):
    loop, d = _pocket_loop()
    c = C.prism_dir("_pocket_" + ob.name, loop, d, back=0.16, front=0.10)
    sheet = C.sheet_bvh(ob)
    C.difference(ob, [c], "pocket_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


def _tunnel(name, loop, d, depth, collection, mat, taper=0.88):
    c = [sum(p[i] for p in loop) / len(loop) for i in range(3)]
    rows = [[tuple(p[i] + d[i] * 0.002 for i in range(3)) for p in loop]]
    for t in (0.5, 1.0):
        k = 1.0 + (taper - 1.0) * t
        rows.append([tuple(c[i] + (p[i] - c[i]) * k - d[i] * depth * t for i in range(3))
                     for p in loop])
    back = [sum(p[i] for p in rows[-1]) / len(loop) for i in range(3)]
    rows.append([tuple(back[i] + (p[i] - back[i]) * 0.02 for i in range(3)) for p in rows[-1]])
    cols = [[rows[r][k] for r in range(len(rows))] for k in range(len(loop))]
    cols.append(cols[0])
    ob = M.mesh_from_rows(name, cols, collection)
    ob.data.materials.append(mat)
    return ob


# ------------------------------------------------------------------ fascia
def build_fascia(collection, lib):
    made = [FA.cap_panel(
        "ES8_Fascia", NOSE, collection, lib,
        N.NOSE_Z_LO + 0.001, N.NOSE_Z_HI - 0.0008, 0.0, 1.0, 48, 48,
        mat="paint", top_to_centre=True,
        cuts=(_cut_band, _cut_pocket),
    )]

    # Recessed black grille panel behind the trapezoidal opening
    rows, _ = BP.cap_rows(NOSE, 0.295, 0.480, 0.0, 0.70, 16, 32, offset=-BAND_RECESS)
    band = M.mesh_from_rows("ES8_Band", rows, collection)
    M.orient(band.data, geom.axial(1.0))
    band.data.materials.append(lib["grille"])
    M.mirror_y(band)
    M.finish(band, thickness=0.0025, bevel=0.0)
    made.append(band)

    # Active horizontal louvers inside the lower grille
    for idx, z_slat in enumerate((0.340, 0.382, 0.424)):
        pts = [face(y, z_slat, -0.010)[0] for y in (0.0, 0.18, 0.36, 0.52, 0.62)]
        slat_rows = [
            [(p[0] + 0.008, p[1], p[2] - 0.004) for p in pts],
            [(p[0] - 0.012, p[1], p[2] + 0.004) for p in pts],
        ]
        slat = M.grid(f"ES8_Grille_Slat_{idx}", slat_rows, collection, lib["black_gloss"],
                      geom.const((1.0, 0.0, 0.0)))
        M.mirror_y(slat)
        M.finish(slat, thickness=0.003, bevel=0.0)
        made.append(slat)

    # Central 4D mmWave radar module in lower grille
    made.append(fittings.rounded_panel(
        "ES8_Radar", (S.HALF_L, 0.0, 0.385), 0.082, 0.050, 0.010,
        lambda p, d: face(p[1], p[2], d), S.HALF_L, collection, lib["black_gloss"],
        d=-0.008, ny=16,
    ))
    return made


# --------------------------------------------------------------- chin lip
def build_chin(collection, lib):
    made = []
    # Full-width satin silver lower bumper blade
    ch_rows, _ = BP.cap_rows(NOSE, 0.296, 0.312, 0.0, 0.78, 4, 36, offset=0.0045)
    ch = M.grid("ES8_Chin_Strip", ch_rows, collection, lib["trim_silver"],
                geom.const((1.0, 0.0, 0.0)))
    M.mirror_y(ch)
    M.finish(ch, thickness=0.003, bevel=0.0008)
    made.append(ch)

    # Gloss-black aero chin splitter underneath
    lip_rows, _ = BP.cap_rows(NOSE, 0.280, 0.296, 0.0, 0.80, 4, 36, offset=0.0035)
    lip = M.grid("ES8_Chin_Lip", lip_rows, collection, lib["black_gloss"],
                 geom.const((1.0, 0.0, 0.0)))
    M.mirror_y(lip)
    M.finish(lip, thickness=0.003, bevel=0.001)
    made.append(lip)
    return made


# ----------------------------------------------------------- Double-Dash + HDPL lamps
def _top_place(p, d):
    return BODY.top_point(p[0], p[1], d)


def _pts_3d(xy_list):
    return [BODY.top_point(x, y)[0] for (x, y) in xy_list]


def _strip_top(name, lo_xy, up_xy, dist, collection, mat, n=32, nk=4,
               thickness=0.0022, bevel=(0.0006, 2, 40)):
    lo_3d = _pts_3d(lo_xy)
    up_3d = _pts_3d(up_xy)
    lo_p = geom.polyline(lo_3d, n)
    up_p = geom.polyline(up_3d, n)
    out = geom.away_from((2.05, 0.55, 0.65))
    return lamps.lens(
        name, lo_p, up_p, _top_place,
        collection, mat, nk, dist, out,
        thickness=thickness, bevel=bevel,
    )


def build_headlamps(collection, lib):
    made = []
    # 1. Double-Dash upper crystal DRL dark housing
    made.append(_strip_top(
        "ES8_Lamp_Housing", HOUSE_LO_XY, HOUSE_UP_XY,
        lambda k, nk: 0.0022 + 0.0006 * math.sin(math.pi * k / nk),
        collection, lib["black_gloss"], n=36, nk=5, bevel=(0.0006, 2, 40),
    ))
    # Four crystal LED blades per side (Double-Dash 2x2 segments)
    for nm, lo, up in (
        ("ES8_Lamp_DRL_In",   UP_IN_LO_XY,  UP_IN_UP_XY),
        ("ES8_Lamp_DRL_Out",  UP_OUT_LO_XY, UP_OUT_UP_XY),
        ("ES8_Lamp_DRL2_In",  LO_IN_LO_XY,  LO_IN_UP_XY),
        ("ES8_Lamp_DRL2_Out", LO_OUT_LO_XY, LO_OUT_UP_XY),
    ):
        made.append(_strip_top(
            nm, lo, up,
            lambda k, nk: 0.0042 + 0.0008 * math.sin(math.pi * k / nk),
            collection, lib["led_white"], n=20, nk=3, thickness=0.0020, bevel=None,
        ))

    # 2. Vertical HDPL smart projector pocket in outer bumper cheek
    loop, d = _pocket_loop()
    tun = _tunnel("ES8_Pocket_Tunnel", loop, d, 0.075, collection, lib["black_gloss"])
    M.mirror_y(tun)
    made.append(tun)

    # Stacked dual HDPL MicroLED projector modules inside the vertical pocket
    for idx, (yp, zp) in enumerate(((0.805, 0.725), (0.808, 0.625))):
        p, n = face(yp, zp, -0.008)
        aim = (n[0] + 0.35, n[1] * 0.35, 0.0)
        made += lamps.projector(f"ES8_Lamp_Proj{idx}", p, aim, 0.030, collection, lib)
    return made


# ----------------------------------------------------------- emblem & plate
def build_emblem_and_plate(collection, lib):
    made = []
    # Nio Sky & Earth emblem on sloped upper Shark-Nose panel between DRLs
    emb = fittings.rounded_panel(
        "ES8_Emblem", (S.HALF_L, 0.0, 0.902), 0.026, 0.019, 0.005,
        lambda p, d: face(p[1], p[2], d),
        S.HALF_L, collection, lib["chrome"], d=0.0025, ny=14,
        outward=(0.82, 0.0, 0.57),
    )
    made.append(emb)

    # Front show plate aligned with the top of the trapezoidal lower grille
    p_pl, n_pl = face(0.0, 0.485, 0.002)
    made += fittings.plate(
        "ES8_Plate_Front", p_pl, n_pl, collection, lib, w=0.440, h=0.140,
        texts=[("NIO ES8", 0.0, 0.038, False, True)],
        mat="black_gloss", text_mat="machined",
    )
    return made


# ----------------------------------------------------------- Watchtower roof sensors
def build_watchtower(collection, lib):
    made = []
    # Central Aquila ultra-long-range LiDAR pod above windshield header
    cx = 0.460
    zc = S.Z_ROOF(cx) - 0.012
    made.append(fittings.lidar_pod(
        "ES8_Lidar", collection, lib["black_gloss"], cx, zc,
        a=0.075, b=0.112, c=0.042,
    ))
    # Two front corner 8MP Watchtower camera pods ("犄角" at y = +/- 0.49 m)
    cx_cam, cy_cam = 0.420, 0.490
    p_cam, _ = BODY.top_point(cx_cam, cy_cam, 0.0)
    z_cam = p_cam[2] - 0.006
    rows = []
    for dx, r_scale in ((-0.060, 0.35), (-0.020, 0.95), (0.028, 1.0), (0.050, 0.45)):
        x = cx_cam + dx
        row = []
        for ang in (-0.95, -0.45, 0.0, 0.45, 0.95):
            dy = 0.028 * r_scale * math.sin(ang)
            dz = 0.022 * r_scale * math.cos(ang)
            row.append((x, cy_cam + dy, z_cam + dz))
        rows.append(row)
    pod = M.grid("ES8_Watchtower_Cam", rows, collection, lib["black_gloss"],
                 geom.away_from((cx_cam, cy_cam, z_cam - 0.05)))
    M.solidify(pod, 0.004)
    M.mirror_y(pod)
    made.append(pod)
    made += lamps.projector(
        "ES8_Watchtower_Lens", (cx_cam + 0.044, cy_cam, z_cam + 0.007),
        (1.0, 0.0, 0.0), 0.010, collection, lib,
    )
    return made


def build_all(collection, lib):
    made = []
    made += build_fascia(collection, lib)
    made += build_chin(collection, lib)
    made += build_headlamps(collection, lib)
    made += build_emblem_and_plate(collection, lib)
    made += build_watchtower(collection, lib)
    return made
