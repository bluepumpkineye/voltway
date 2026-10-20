"""Denza Z9 front end: "Corona" (日冕) split dual-layer headlamps (upper slanted
3-projector cluster + separate lower horizontal LED DRL blade), sculpted painted
front bumper with boomerang side aero curtains & embedded LiDAR pods, trapezoidal
lower grille with central radar sensor, lower chin lip, license plate, and
circular Denza emblem.

Calibrated directly against Autohome studio references c1_0042.jpg (front) and
c1_0040.jpg (side).
"""
import math
import bpy
from mathutils import Vector

import z9_surface as S
import z9_nose as N
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
LAMP_BODY = ("Z9_Fascia", "Z9_Fender_Front", "Z9_Hood")
LAMP_CENTRE = (2.05, 0.45, 0.65)


def _lamp_place(p, d=0.0):
    return PLACER.radial(p, LAMP_CENTRE, LAMP_BODY, d)


# ------------------------------------------------- hardpoints read off the front photograph
# c1_0034.jpg (the black car, straight on) through its solved camera (z9_ref_match "front_black": 8.107 m ahead, 0.516 m
# up, pitched up 3.67 deg, f 5561 px; the shadows lifted so the matt-black grille and pockets read against the gloss
# body). Pixels are turned into (|y|, z) ON the nose's own surface: a ray from the camera, the point on the plane at
# the nose's depth there, again (the nose is a prow, 0.45 m deeper at the centre than at the corners).
FRONT_CAM = dict(loc=(8.107, 0.0, 0.516), rot=(93.67, 0.0, 90.0), f=5561.0)


def _px_yz(u, v):
    from mathutils import Euler
    R = Euler(tuple(math.radians(a) for a in FRONT_CAM["rot"]), 'XYZ').to_matrix()
    loc = Vector(FRONT_CAM["loc"])
    f = FRONT_CAM["f"]
    d = R @ Vector(((u - 1920.0) / f, -(v - 1440.0) / f, -1.0))
    x = 2.5
    y = z = 0.0
    for _ in range(4):
        p = loc + d * ((x - loc.x) / d.x)
        y, z = p.y, p.z
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


# the side pockets (black leaf-shaped air curtains with the sensor modules; the body-colour fin wedges lie under their
# slanting lower edge and the brow above them), the central grille opening, the thin dark bar above the plate
POCKET_PX = [(1115, 1828), (1250, 1812), (1420, 1840), (1525, 1858), (1525, 1900), (1520, 1975), (1535, 2057),
             (1400, 2025), (1250, 2005), (1095, 1985), (1088, 1930), (1095, 1870)]
POCKET = _yz_px(POCKET_PX)
GRILLE = [(-0.02, 0.335), (0.41, 0.335), (0.418, 0.300), (0.405, 0.170), (-0.02, 0.170)]
BROW_UP = [(0.0, 0.500), (0.18, 0.512), (0.39, 0.538)]
BROW_LO = [(0.0, 0.468), (0.18, 0.480), (0.39, 0.508)]


# the front plate's lean (degrees; its face looks down by this much): the nose face's own pitch over the plate's height
# (27 at its middle, 20 to 30 across it), so the plate stands the same few millimetres off the paint top to bottom
PLATE_PITCH = 25.0


# ------------------------------------------------------------------ helpers
def _face(y, z, d=0.0):
    w, v = NOSE.wv_at(abs(y), z)
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
    ob = M.obj(name, v, f, collection, mat)
    return ob


# ------------------------------------------------------------------ fascia
def _cut_fascia(ob):
    cutters = [C.prism_x("_cut_pocket_" + ob.name, POCKET, S.HALF_L + 0.30, S.HALF_L - 0.60),
               C.prism_x("_cut_grille_" + ob.name, GRILLE, S.HALF_L + 0.30, S.HALF_L - 0.60)]
    sheet = C.sheet_bvh(ob)
    C.difference(ob, cutters, "front_cuts_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


def build_fascia(collection, lib):
    made = []
    # 1. Painted front nose & bumper skin (top_to_centre=True closes seam to Z9_Hood), the black pockets and the grille
    # opening cut out of it
    fascia = FA.cap_panel(
        "Z9_Fascia", NOSE, collection, lib,
        N.NOSE_Z_LO + 0.002, N.NOSE_Z_HI - 0.0008,
        0.0, 1.0, 40, 44, mat="paint", top_to_centre=True, cuts=(_cut_fascia,),
    )
    made.append(fascia)

    # the dark apron behind the cuts: a recessed satin-black sheet from the chin to above the pockets (it shows only
    # through the openings)
    from carkit.body import panels as BP
    rows, _ = BP.cap_rows(NOSE, 0.150, 0.585, 0.0, 1.0, 24, 40, offset=-0.012)
    ap = M.mesh_from_rows("Z9_Apron", rows, collection)
    M.orient(ap.data, geom.axial(1.0))
    ap.data.materials.append(lib["black_trim"])
    M.mirror_y(ap)
    M.finish(ap, thickness=0.0025, bevel=0.0)
    made.append(ap)

    # 2. The grille behind its opening: a black mesh with the radiator's horizontal bars (c1_0034: four) and a
    # square radar cover in the middle
    ny, nz = 24, 10
    g_cols = []
    for i in range(ny + 1):
        y = 0.43 * i / float(ny)
        col = []
        for j in range(nz + 1):
            z = 0.168 + (0.338 - 0.168) * j / float(nz)
            col.append(_face(y, z, d=-0.020)[0])
        g_cols.append(col)
    grille = M.mesh_from_rows("Z9_Grille_Mesh", g_cols, collection)
    grille.data.materials.append(lib["black_trim"])
    M.mirror_y(grille)
    M.finish(grille, thickness=0.0025, bevel=0.0)
    made.append(grille)
    for idx, z_slat in enumerate((0.200, 0.238, 0.276, 0.314)):
        s_lo, s_up = [], []
        for i in range(17):
            y = 0.39 * (i / 16.0)
            s_lo.append(_face(y, z_slat - 0.008, d=-0.012)[0])
            s_up.append(_face(y, z_slat + 0.008, d=-0.012)[0])
        s_cols = [[s_lo[c], s_up[c]] for c in range(17)]
        slat = M.mesh_from_rows(f"Z9_Grille_Slat_{idx}", s_cols, collection)
        slat.data.materials.append(lib["trim_chrome"])
        M.mirror_y(slat)
        M.finish(slat, thickness=0.002, bevel=0.0)
        made.append(slat)
    # the radar cover (c1_0034: 140 x 76 px = 0.16 x 0.09 m, centre z 0.24)
    p_rad, _ = _face(0.0, 0.245, d=-0.004)
    made.append(_box("Z9_Front_Radar", p_rad, (0.010, 0.160, 0.090), collection, lib["black_gloss"]))

    # 3. The thin dark bar across the nose above the plate (the hood's lip / sensor bar)
    ns = 20
    cols = []
    for i in range(ns + 1):
        y = 0.39 * i / float(ns)
        zl = _lerp(BROW_LO, y)
        zu = _lerp(BROW_UP, y)
        cols.append([_face(y, zl, d=0.003)[0], _face(y, zu, d=0.003)[0]])
    brow = M.mesh_from_rows("Z9_Brow_Bar", cols, collection)
    brow.data.materials.append(lib["black_trim"])
    M.mirror_y(brow)
    M.finish(brow, thickness=0.003, bevel=0.0)
    made.append(brow)

    # the sensor module inside each pocket (c1_0034: a small vertical pod at the pocket's outer third)
    p_lid, _ = _face(0.68, 0.350, d=-0.004)
    lidar_pod = _box("Z9_Front_Side_Lidar", p_lid, (0.012, 0.085, 0.036), collection, lib["lamp_clear"])
    M.mirror_y(lidar_pod)
    made.append(lidar_pod)

    # 4. Full-width gloss-black lower front chin splitter lip (z 0.145..0.165)
    ns = 32
    ch_lo, ch_up = [], []
    for i in range(ns + 1):
        t = i / float(ns)
        y = 0.86 * t
        ch_lo.append(_face(y, 0.148, d=0.006)[0])
        ch_up.append(_face(y, 0.166, d=0.006)[0])
    ch_cols = [[ch_lo[c], ch_up[c]] for c in range(ns + 1)]
    chin = M.mesh_from_rows("Z9_Chin_Lip", ch_cols, collection)
    chin.data.materials.append(lib["black_trim"])
    M.mirror_y(chin)
    M.finish(chin, thickness=0.003, bevel=0.0)
    made.append(chin)

    # 5. Front license plate mount & plate: the 480 x 140 mm sign (c1_0034 through its solved camera: 493 px wide,
    # centre z 0.40; the first build put it at 0.445 and 440 mm wide, read from the wide-lens showroom shot)
    # The plate is a flat board: it takes the nose's pitch there (27 deg, an undercut face: PLATE_PITCH) and none of its yaw
    # (the nose normal at the centre has a y component of 0.1), and a mount block as deep as the nose's recession across the
    # plate's width (4 cm at the edges) fills the gap behind it. Before, the plate followed the nose's normal and the mount
    # was an upright box, so the two crossed as a twisted wedge in front of the bumper.
    pitch = math.radians(PLATE_PITCH)
    n_plate = (math.cos(pitch), 0.0, -math.sin(pitch))
    p_c, _ = _face(0.0, 0.400, d=0.006)
    p_plate_f = (p_c[0], 0.0, p_c[2])
    p_mount = tuple(p_plate_f[i] - n_plate[i] * 0.003 for i in range(3))
    made += fittings.plate("Z9_Plate_Mount_Front", p_mount, n_plate, collection, lib, w=0.500, h=0.150, depth=0.080,
                           mat="black_gloss", bevel=(0.003, 2, 30))
    made += fittings.plate("Z9_Plate_Front", p_plate_f, n_plate, collection, lib, w=0.480, h=0.140, depth=0.004,
                           texts=[("DENZA Z9", 0.0, 0.038, False, True)],
                           mat="black_gloss", text_mat="machined")

    return made


# ------------------------------------------------------------- headlamps
LAMP_UPPER = [
    (2.510, 0.345, 0.685),
    (2.440, 0.460, 0.718),
    (2.350, 0.600, 0.750),
    (2.240, 0.730, 0.782),
    (2.140, 0.830, 0.810),
    (2.040, 0.895, 0.832),
]

LAMP_LOWER = [
    (2.510, 0.345, 0.685),
    (2.455, 0.435, 0.655),
    (2.375, 0.575, 0.660),
    (2.260, 0.715, 0.680),
    (2.150, 0.825, 0.725),
    (2.080, 0.875, 0.775),
    (2.040, 0.895, 0.832),
]

DRL_BLADE_UPPER = [
    (2.550, 0.360, 0.605),
    (2.470, 0.500, 0.618),
    (2.370, 0.660, 0.630),
    (2.260, 0.790, 0.640),
    (2.180, 0.865, 0.645),
]

DRL_BLADE_LOWER = [
    (2.550, 0.360, 0.588),
    (2.470, 0.500, 0.602),
    (2.370, 0.660, 0.614),
    (2.260, 0.790, 0.624),
    (2.180, 0.865, 0.630),
]


def _projector_bezel(name, c, n, r_in, r_out, collection, mat, seg=16):
    nvec = Vector(n).normalized()
    upv = Vector((0, 0, 1)) if abs(nvec.z) < 0.9 else Vector((1, 0, 0))
    t1 = nvec.cross(upv).normalized()
    t2 = nvec.cross(t1).normalized()
    cols = []
    for i in range(seg + 1):
        ang = 2.0 * math.pi * (i / float(seg))
        ca, sa = math.cos(ang), math.sin(ang)
        d_vec = t1 * ca + t2 * sa
        p_in = tuple(Vector(c) + d_vec * r_in)
        p_out = tuple(Vector(c) + d_vec * r_out)
        cols.append([p_in, p_out])
    ob = M.mesh_from_rows(name, cols, collection)
    ob.data.materials.append(mat)
    M.mirror_y(ob)
    M.finish(ob, thickness=0.002, bevel=0.0)
    return ob


def build_headlamps(collection, lib):
    """Denza Z9 'Corona' (日冕) split dual-layer headlamp system:
    1. Upper main angular headlamp cluster spanning from nose prow (x=2.480, y=0.345)
       all the way back across the front corner and onto the front fender crown (x=2.040, y=0.895, z=0.832),
       peaking 62 mm above the wheel arch peak.
       Features:
       - Dark housing backing set into the contour
       - Gasket seal band setting the lamp into the sheet metal
       - Continuous L-shaped LED DRL light guide along lower contour and outer sweep
       - Three faceted crystalline LED projector units with chrome bezels
       - Smoked clear polycarbonate outer lens with realistic clearcoat
    2. Lower Corona DRL blade (x=2.510..2.180, y=0.360..0.865, z=0.588..0.645)
       nestled in the bumper crease below the 40 mm painted bridge:
       - Gloss black channel bezel
       - Luminous white LED strip
    """
    made = []
    PLACER.reset()
    NS, NK = 64, 8
    lo = geom.polyline(LAMP_LOWER, NS)
    up = geom.polyline(LAMP_UPPER, NS)
    out = geom.away_from((2.10, 0.50, 0.68))

    def _crown(k, extra=0.0):
        return 0.0035 + 0.0016 * math.sin(math.pi * max(0.0, min(1.0, k))) + extra

    # 1. Dark housing backing
    made.append(lamps.lens(
        "Z9_Headlamp_Housing", lo, up, _lamp_place, collection, lib["lamp_housing"],
        NK, lambda k, nk: 0.0020, out, thickness=0.0025, bevel=0.0
    ))

    # 2. Outer seal gasket band
    made += lamps.seals(
        "Z9_Headlamp_Seal", lo, up, _lamp_place, collection, lib["grille"], out,
        width=0.0045, d=0.0012
    )

    # 3. Continuous L-shaped DRL light guide along lower contour
    k0, k1 = 0.08, 0.24
    made.append(lamps.band_between(
        "Z9_Headlamp_DRL", lo, up, range(1, int(NS * 0.94)),
        [k0 + (k1 - k0) * c / 2.0 for c in range(3)],
        _lamp_place, lambda k: _crown(k, 0.0012), collection, lib["led_white"], out
    ))

    # 4. Three stepped crystalline LED projector units with chrome bezels
    modules = [(0.54, 0.702), (0.67, 0.725), (0.79, 0.762)]
    for idx, (yy, zz) in enumerate(modules):
        best = lamps.station_nearest_y(lo, up, yy)
        zl, zu = lo[best][2], up[best][2]
        k = max(0.35, min(0.75, (zz - zl) / max(1e-4, zu - zl)))
        c, n = _lamp_place(geom.lerp(lo[best], up[best], k), 0.0045)
        made.append(_projector_bezel(
            f"Z9_Headlamp_ProjBezel_{idx}", c, n, 0.016, 0.021, collection, lib["logo_chrome"]
        ))
        made += lamps.projector(
            f"Z9_Headlamp_Proj_{idx}", c, n, 0.016, collection, lib,
            mats=("lamp_bowl", "led_white")
        )

    # 5. Smoked clear outer polycarbonate lens
    made.append(lamps.lens(
        "Z9_Headlamp_Lens", lo, up, _lamp_place, collection, lib["lamp_clear"],
        NK, lambda k, nk: _crown(k / float(nk)), out,
        thickness=0.0025, bevel=(0.0010, 2, 30)
    ))

    # 6. Lower Corona DRL Blade
    lo_drl = geom.polyline(DRL_BLADE_LOWER, 40)
    up_drl = geom.polyline(DRL_BLADE_UPPER, 40)
    out_drl = geom.away_from((2.10, 0.50, 0.60))

    made.append(lamps.lens(
        "Z9_Lower_DRL_Housing", lo_drl, up_drl, _lamp_place, collection,
        lib["black_gloss"], 4, lambda k, nk: 0.0025, out_drl,
        thickness=0.0025, bevel=0.0
    ))

    made.append(lamps.band_between(
        "Z9_Lower_DRL_Blade", lo_drl, up_drl, range(len(lo_drl)),
        [0.2, 0.5, 0.8], _lamp_place, lambda k: 0.0055, collection,
        lib["led_white"], out_drl
    ))

    return made


# --------------------------------------------------------------- emblem
def build_emblem(collection, lib):
    """Denza circular/oval emblem centered on the upper nose at z=0.690 (c1_0042.jpg):
    - Outer polished chrome ring
    - Gloss black backing disc
    - Central chrome water-drop / wing motif
    """
    made = []
    z_c = 0.690
    n_seg = 24
    ry, rz = 0.036, 0.028

    # Black backing disc
    disc_cols = []
    for i in range(n_seg + 1):
        ang = math.pi * i / float(n_seg) - 0.5 * math.pi
        y = ry * math.cos(ang)
        z0 = z_c - rz * math.sin(ang)
        z1 = z_c + rz * math.sin(ang)
        disc_cols.append([_face(y, z0, d=0.0025)[0], _face(y, z1, d=0.0025)[0]])
    disc = M.mesh_from_rows("Z9_Emblem_Front_Disc", disc_cols, collection)
    disc.data.materials.append(lib["black_gloss"])
    M.mirror_y(disc)
    M.finish(disc, thickness=0.002, bevel=0.0)
    made.append(disc)

    # Outer chrome ring + central vertical drop
    ring_cols = []
    for i in range(n_seg + 1):
        ang = math.pi * i / float(n_seg)
        y_in, z_in = 0.78 * ry * math.sin(ang), z_c + 0.78 * rz * math.cos(ang)
        y_out, z_out = ry * math.sin(ang), z_c + rz * math.cos(ang)
        ring_cols.append([_face(y_in, z_in, d=0.004)[0], _face(y_out, z_out, d=0.004)[0]])
    ring = M.mesh_from_rows("Z9_Emblem_Front_Ring", ring_cols, collection)
    ring.data.materials.append(lib["logo_chrome"])
    M.mirror_y(ring)
    M.finish(ring, thickness=0.002, bevel=0.0)
    made.append(ring)

    p_drop, n_drop = _face(0.0, z_c, d=0.004)
    d_cols = [
        [(p_drop[0] + n_drop[0]*0.0015, 0.0, z_c + 0.014), (p_drop[0] + n_drop[0]*0.0015, 0.0, z_c + 0.014)],
        [(p_drop[0] + n_drop[0]*0.0015, -0.007, z_c), (p_drop[0] + n_drop[0]*0.0015, 0.007, z_c)],
        [(p_drop[0] + n_drop[0]*0.0015, 0.0, z_c - 0.014), (p_drop[0] + n_drop[0]*0.0015, 0.0, z_c - 0.014)],
    ]
    drop = M.mesh_from_rows("Z9_Emblem_Front_Drop", d_cols, collection)
    drop.data.materials.append(lib["logo_chrome"])
    M.finish(drop, thickness=0.0015, bevel=0.0)
    made.append(drop)

    return made


# -------------------------------------------------------- hood ridges
def build_hood_features(collection, lib):
    """Twin sculpted power bulges / crease ridges on the front hood (c1_0002.jpg)
    sweeping forward from cowl (y=0.44, z=0.96) to front prow (y=0.24, z=0.74).
    """
    made = []
    nc = 28
    for side in (-1, 1):
        cols = []
        for i in range(nc + 1):
            t = i / float(nc)
            x = 1.02 + (2.56 - 1.02) * t
            y_c = (0.44 - 0.22 * (t ** 1.2)) * side
            z_c = S.Z_ROOF(x) - 0.002 + 0.007 * math.sin(math.pi * t)
            p0 = (x, y_c - 0.014 * side, z_c)
            p1 = (x, y_c, z_c + 0.0055)
            p2 = (x, y_c + 0.014 * side, z_c)
            cols.append([p0, p1, p2])
        c_ob = M.mesh_from_rows(f"Z9_Hood_Ridge_{'R' if side > 0 else 'L'}", cols, collection)
        c_ob.data.materials.append(lib["paint"])
        M.finish(c_ob, thickness=0.002, bevel=0.0)
        made.append(c_ob)
    return made


# ------------------------------------------------------------- build all
def build_all(collection, lib):
    made = []
    made += build_fascia(collection, lib)
    made += build_headlamps(collection, lib)
    made += build_emblem(collection, lib)
    made += build_hood_features(collection, lib)
    return made
