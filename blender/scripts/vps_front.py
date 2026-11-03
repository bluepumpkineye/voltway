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

2026-11-03, the owner: "the same unpolished and unfinished design" on the front bumper and headlamps, "the upper headlights
should form a continuous line with the middle stripe". The upper lamp, the nose channel and the cheek pockets are now read
off the studio front photograph c1_0002.jpg (vps_lampdata: traced contours and hand readings of 3x crops) and laid on the
panels along the photo's own rays (carkit.photolay), as for the 06T and the ES8: the lamp is ONE eyelid (a black hood over a
dark lens with the white DRL line across it) whose inner end IS the nose channel's start (same height, no gap), the channel
runs on to the emblem with its lit strip, and the cheek is cut along the traced outline of the black recess.
"""
import math

import bpy
from mathutils import Vector

import vps_surface as S
import vps_nose as N
import vps_panels as PN
import vps_cam as CAM
import vps_lampdata as LD
import vps_ref_match as RM
from carkit import geom
from carkit import photolay as PL
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


CHIN_PX = [
    (1072, 1996), (1140, 2012), (1260, 2020), (1450, 2022),
    (1680, 2022), (1920, 2022),
]

PLATE_PX = (1700, 1742, 2140, 1898)
CAMERA_PX = (1920, 1720)
TOWCAP_PX = (1425, 1796)
SENSORS_PX = [(1078, 1792), (1362, 1812), (1625, 1872)]

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


# ---------------------------------------------------- the photo's rays onto the model's panels
# The outlines of vps_lampdata are pixels of c1_0002.jpg; each point goes along the photo's own ray (vps_ref_match "front",
# mirrored onto the half sheet y >= 0) to the first of the panels that meets it (the uncut fascia, the front fender, the hood),
# the point being the hit and the normal the panels' own smooth vertex normals (carkit.photolay.Surf).
SURF_PANELS = ("VPS_Fascia", "VPS_Fender_Front", "VPS_Hood")
_SURF = []


def _surf():
    if not _SURF:
        _SURF.append(PL.Surf(SURF_PANELS, inside=(1.2, 0.0, 0.6), x_range=(2.60, 1.70)))
    return _SURF[0]


def _on_surface(u, v, cam="front", inset=0.0):
    o, d = RM.ray(cam, u, v)
    o, d = Vector((o.x, -o.y, o.z)), Vector((d.x, -d.y, d.z))
    h = _surf().hit(o, d, inset)
    if h is None:
        raise RuntimeError("vps_front: the photo ray through (%g, %g) misses the nose" % (u, v))
    return h


LAY = PL.Lay(_on_surface, geom.away_from((1.90, 0.45, 0.65)))


def _surf_cut(ob):
    """First cut of the fascia, run on the uncut sheet: take the panels as they stand for the photo's rays."""
    del _SURF[:]
    _surf()


LIP_PX = 16.0                      # the paint left at the cheek's outer edge (1.8 cm): the corner's own lip


def _lip(u, v):
    """The cut's outer edge moved in by LIP_PX (a smooth ramp over 26 px in u, fading out between v 1880 and 1920 where the
    cavity's rounded foot meets the fang): the traced edge is the fascia sheet's own, and a cut along a sheet's very edge
    tore into sawteeth (the owner: "as if someone cuts roughly with a cutter")."""
    def ss(t):
        t = min(1.0, max(0.0, t))
        return t * t * (3.0 - 2.0 * t)
    if u >= 1130.0:
        return u
    return u + LIP_PX * (1.0 - ss((u - 1104.0) / 26.0)) * (1.0 - ss((v - 1880.0) / 40.0))


def _mask_cut():
    """The cheek-and-grille recess the paint is cut along (c1_0002, traced and simplified: LD.CHEEK_PTS, corners sharp, the
    rest spline-smoothed), as (y, z) of the nose; its edge on the centre line crosses it (y = -0.025) so the two halves meet."""
    pts = PL.resample_loop(PL.smooth_loop(LD.CHEEK_PTS, LD.CHEEK_CORNERS, 6), 5.0)
    out = []
    for (u, v) in pts:
        if u > LD.CENTRE_U - 3.0:
            y, z = _px_yz(u, v)
            out.append((-0.025, z))
            continue
        p, _n = _on_surface(_lip(u, v), v, inset=0.004)
        out.append((p.y, p.z))
    return out


def _cut_openings(ob):
    """Cut the connected cheek/projector/lower-grille mask and trim below the chin line."""
    chin_cut = [(-0.02, CHIN[-1][1])] + [(y, z) for (y, z) in reversed(CHIN)] + [
        (CHIN[0][0] + 0.03, 0.05), (-0.02, 0.05)
    ]
    cutters = [
        C.prism_x("_cut_mask_" + ob.name, _mask_cut(), S.HALF_L + 0.30, S.HALF_L - 0.65),
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
        cuts=(_surf_cut, _cut_openings))
    made.append(fascia)

    # Recessed gloss-black mask behind the cheek pockets & active-shutter lower grille
    # (up to z 0.84, the cut's top at the panel: carried on over the nose's crown to the centre line, as it was, the apron
    # stood through the paint above the emblem as two black shards)
    rows, _ = BP.cap_rows(NOSE, N.NOSE_Z_LO + 0.002, 0.840, 0.0, 1.0, 24, 36, offset=-0.020)
    ap = M.mesh_from_rows("VPS_Apron", rows, collection)
    M.orient(ap.data, geom.axial(1.0))
    ap.data.materials.append(lib["grille"])
    M.mirror_y(ap)
    M.finish(ap, thickness=0.0025, bevel=0.0)
    made.append(ap)

    return made


# --------------------------------------------------------- grille, radar & chin
def build_grille(collection, lib):
    made = []
    _, z_top = _px_yz(1700, 1892)
    _, z_lo = _px_yz(1700, 1996)

    # The active-shutter grille as c1_0002 shows it: two rows of dark openings, a thin vertical blade (pale, pointed at both
    # ends) every 6.2 cm in each (u 1593, 1648, 1705, 1761 and the frame's at 1537; rows v 1862-1912 and 1933-1978), a bar
    # between the rows (v 1927) running in to the radar
    verts, faces = [], []
    wid, dep = 0.0030, 0.007
    rows_v = ((1862, 1912), (1933, 1978))
    for side in (1.0, -1.0):
        for (va, vb) in rows_v:
            zt, zb = _px_yz(1700, va)[1], _px_yz(1700, vb)[1]
            for u in (1537, 1593, 1648, 1705, 1761):
                y = (CAM.W / 2.0 - u) * 1.106e-3
                x_f = min(_face(y, zt)[0][0], _face(y, zb)[0][0]) - 0.016
                k = len(verts)
                for (xx, zz) in ((x_f - dep, zb), (x_f, zb), (x_f, zt), (x_f - dep, zt)):
                    verts.append((xx, side * (y - wid * 0.5), zz))
                    verts.append((xx, side * (y + wid * 0.5), zz))
                faces += [[k + 0, k + 1, k + 3, k + 2], [k + 2, k + 3, k + 5, k + 4],
                          [k + 4, k + 5, k + 7, k + 6], [k + 6, k + 7, k + 1, k + 0],
                          [k + 0, k + 2, k + 4, k + 6], [k + 1, k + 7, k + 5, k + 3]]
    z_mid = _px_yz(1700, 1927)[1]
    for side in (1.0, -1.0):
        k = len(verts)
        for (yy, zz) in ((0.115, z_mid - 0.0030), (0.510, z_mid - 0.0030), (0.510, z_mid + 0.0030), (0.115, z_mid + 0.0030)):
            xf = _face(yy, zz)[0][0] - 0.0150
            verts.append((xf - 0.006, side * yy, zz))
            verts.append((xf, side * yy, zz))
        faces += [[k + 0, k + 1, k + 3, k + 2], [k + 2, k + 3, k + 5, k + 4],
                  [k + 4, k + 5, k + 7, k + 6], [k + 6, k + 7, k + 1, k + 0]]
    made.append(M.obj("VPS_Grille_Slats", verts, faces, collection, lib["lamp_hair"], smooth=False))

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


# --------------------------------------------------------- the upper lamp, the nose channel, the cheek pockets
# Depths are metres along the paint's normal (c1_0002: 1 px is about 1.1 mm). The lamp and the channel stand proud of the
# paint as one applied piece (the hood and the fascia they cross are not cut for them); inside the cheek everything stands
# in the recess, in front of the apron (-20 mm).
LAMP_UP, LAMP_T = 0.0016, 0.0020
LENS_UP, LINE_UP, STRIP_UP = 0.0024, 0.0032, 0.0030
PANEL_DEPTH, BEZEL_DEPTH, SLAT_DEPTH, FIN_DEPTH, BODY_DEPTH = -0.0120, -0.0085, -0.0080, -0.0150, -0.0100


def _line_v(u):
    import numpy as np
    return float(np.interp(u, [p[0] for p in LD.LAMP_LINE], [p[1] for p in LD.LAMP_LINE]))


def _lens_poly():
    """The lens: the lamp's outline below the white line, closed along the line."""
    out = [(float(p[0]), float(p[1])) for p in LD.LAMP_OUT]
    below = [p[1] > _line_v(p[0]) + 2.0 for p in out]
    n = len(out)
    start = next(i for i in range(n) if not below[i] and below[(i + 1) % n])
    arc = []
    i = (start + 1) % n
    while below[i % n] and len(arc) < n:
        arc.append(out[i % n])
        i += 1
    return arc + [tuple(p) for p in reversed(LD.LAMP_LINE)]


def _rrect(box, k=5):
    u0, v0, u1, v1, r = box
    pts = []
    for (cx, cy, a0) in ((u1 - r, v0 + r, -90.0), (u1 - r, v1 - r, 0.0), (u0 + r, v1 - r, 90.0), (u0 + r, v0 + r, 180.0)):
        for i in range(k + 1):
            a = math.radians(a0 + 90.0 * i / k)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _disc(c, r, n=28):
    return [(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def build_lamp(collection, lib):
    """The upper lamp: a black eyelid over a dark lens, the white DRL line across it. Its inner end is the channel's start."""
    made = []
    made.append(LAY.region("VPS_Lamp_Body", PL.grow(LD.LAMP_OUT, 0.8), LAMP_UP, lib["lamp_frame"], collection, step=6.0,
                           thick=LAMP_T, bevel=0.0006))
    made.append(LAY.region("VPS_Lamp_Lens", PL.grow(_lens_poly(), -1.6), LENS_UP, lib["lamp_clear"], collection, step=5.0,
                           thick=0.0004))
    made.append(LAY.ribbon("VPS_Lamp_Hair", LD.LAMP_LINE, 0.0017, LINE_UP - 0.0004, lib["lamp_hair"], collection, step=6.0,
                           thick=0.0004))
    made.append(LAY.ribbon("VPS_Lamp_Line", LD.LAMP_LINE, 0.0009, LINE_UP, lib["led_white"], collection, step=6.0, thick=0.0005))
    return made


def build_channel(collection, lib):
    """The nose channel from the lamp's inner end to the emblem: a black frame and its lit strip (the DRL, continuing)."""
    made = []
    up, lo = LD.CH_BOT, LD.CH_TOP                      # (frac 1 = up of the band)
    made.append(LAY.band("VPS_Nose_Channel", up, lo, 0, 2, LAMP_UP - 0.0002, lib["lamp_frame"], collection, thick=LAMP_T, paired=True))
    made.append(LAY.band("VPS_Nose_Strip", up, lo, 0, 2, STRIP_UP, lib["led_white"], collection, thick=0.0005, paired=True,
                         frac=lambda t: (0.5, 0.30)))
    return made


def build_cheek(collection, lib):
    """The cheek recess (cut along LD.CHEEK_OUT): the smoked lamp panel with its two projector units, the intake's fin,
    slat and round cover. The black apron behind is VPS_Apron."""
    made = []
    made.append(LAY.region("VPS_Cheek_Panel", PL.grow(PL.smooth_loop(LD.PANEL, (), 3), 5.0), PANEL_DEPTH, lib["lamp_smoked"],
                           collection, step=9.0))
    for i, bez in enumerate((LD.BEZEL_1, LD.BEZEL_2)):
        ring = _rrect(bez)
        made.append(LAY.ribbon("VPS_Proj_Bezel_%d" % i, ring, 0.0017, BEZEL_DEPTH, lib["lamp_hair"], collection, step=5.0,
                               thick=0.0008, closed=True))
        made.append(LAY.region("VPS_Proj_Lens_%d" % i, PL.grow(PL.smooth_loop(ring, (), 2), -3.2), BEZEL_DEPTH - 0.0003,
                               lib["lamp_lens"], collection, step=5.0, thick=0.0006))
    made.append(LAY.region("VPS_Intake_Body", PL.smooth_loop(LD.BULK, (), 2), BODY_DEPTH, lib["intake_grey"], collection,
                           step=12.0))
    made.append(LAY.region("VPS_Intake_Fin", PL.smooth_loop(LD.FIN, (), 3), FIN_DEPTH, lib["intake_grey"], collection,
                           step=8.0))
    made.append(LAY.region("VPS_Intake_Slat", PL.smooth_loop(LD.SLAT, (), 2), SLAT_DEPTH, lib["lamp_frame"], collection,
                           step=6.0, thick=0.0014))
    made.append(LAY.ribbon("VPS_Intake_Slat_Edge", LD.SLAT[:4], 0.0007, SLAT_DEPTH + 0.0014, lib["lamp_hair"], collection,
                           step=6.0, thick=0.0004, smooth=False))
    cu, cv, r = LD.CIRCLE
    made.append(LAY.ribbon("VPS_Intake_Cover", _disc((cu, cv), r), 0.0008, -0.0160, lib["lamp_frame"], collection, step=8.0,
                           thick=0.0006, closed=True))
    return made


def build_headlamps(collection, lib):
    return build_lamp(collection, lib) + build_channel(collection, lib) + build_cheek(collection, lib)


def relax_lamp_ao(ob, radius=0.040, ring=0.035):
    """Undo the baked occlusion's grey halo round the cheek recess's cut (see a06t_front.relax_lamp_ao): every FRONT-SKIN
    vertex of `ob` (the nose, modifiers applied, both halves) within `radius` of the recess outline takes the average of the
    front-skin ring `ring` beyond it."""
    import numpy as np
    from mathutils.kdtree import KDTree
    pts = []
    for (u, v) in PL.resample_loop(LD.CHEEK_OUT, 14.0):
        if u > LD.CENTRE_U - 3.0:
            continue
        p, _n = _on_surface(u, v)
        pts += [p, Vector((p.x, -p.y, p.z))]
    tree = KDTree(len(pts))
    for i, p in enumerate(pts):
        tree.insert(p, i)
    tree.balance()
    me = ob.data
    at = me.attributes.get("_BAKEDAO")
    if at is None:
        return 0
    ao = np.empty(len(at.data), np.float32)
    at.data.foreach_get("value", ao)
    skin_tree = _surf().tree
    mw = ob.matrix_world
    d = np.empty(len(me.vertices))
    skin = np.zeros(len(me.vertices), bool)
    for i, v in enumerate(me.vertices):
        w = mw @ v.co
        d[i] = tree.find(w)[2]
        if d[i] < radius + ring:
            hit = skin_tree.find_nearest(Vector((w.x, abs(w.y), w.z)))
            skin[i] = hit[0] is not None and hit[3] < 0.0014
    inner = (d < radius) & skin
    outer = (d >= radius) & (d < radius + ring) & skin
    if not inner.any() or not outer.any():
        return 0
    ref = float(ao[outer].mean())
    ao[inner] = np.maximum(ao[inner], ref)
    at.data.foreach_set("value", ao)
    me.update()
    print("lamp AO ring %.2f, %d skin vertices lifted" % (ref, int(inner.sum())))
    return int(inner.sum())


# --------------------------------------------------------- Kunpeng V-emblem, plate & lidar
def _arc_order(poly):
    """A traced loop that had its top removed starts mid-arc: rotate it to start after its biggest jump."""
    n = len(poly)
    jump = max(range(n), key=lambda i: math.hypot(poly[(i + 1) % n][0] - poly[i][0], poly[(i + 1) % n][1] - poly[i][1]))
    return [poly[(jump + 1 + k) % n] for k in range(n)]


def build_emblem(collection, lib):
    """The Kunpeng emblem under the channel (c1_0002, traced: LD.EMB_*): a black shield (flush with the channel's frame, its
    point down) and the white lit blades in it (the upper arm with the stem's outer bar, the centre pill and bar), lit with the
    DRL line and the channel's strip."""
    made = [LAY.region("VPS_Emblem_Shield", _arc_order(LD.EMB_SHIELD), 0.0032, lib["lamp_frame"], collection, step=5.0,
                       thick=0.0030, bevel=0.0008)]
    made.append(LAY.region("VPS_Emblem_Blade", PL.grow(LD.EMB_BLADE, -0.4), 0.0046, lib["lamp_white_bar"], collection, step=3.6,
                           thick=0.0006))
    made.append(LAY.region("VPS_Emblem_Pill", LD.EMB_PILL, 0.0046, lib["lamp_white_bar"], collection, step=2.4, thick=0.0006))
    made.append(LAY.region("VPS_Emblem_Bar", LD.EMB_BAR, 0.0046, lib["lamp_white_bar"], collection, step=3.0, thick=0.0006))
    return made


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
