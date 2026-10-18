"""Zeekr 7X rear end: the hatch's shut line, tail lamp bar, rear glass, chrome and
black lower bumper, reflectors, diffuser, sensors, lettering.

Positions are read off the straight-on rear photograph (rear_studio.jpg, 3840 x
2880: the car's left on the image's left) in PIXELS and turned into (y, z) by
zx_camsolve.rear_yz on the tail's face (x -2.40); each part is then dropped onto the
finished surface at build time through a ray cast from behind (on_rear), so it
follows any later change to the caps. The zoomed, gridded crops they were read from
(rtL_up / rtL_low, 25 px grid) are in the scratch notes; coordinates there are in
photo px.

    tail cap      painted, from the black bumper's top edge to the lamp bar and the lip
                  above it; the hatch's shut line cut through it: a rounded rectangle,
                  upright at y +/-0.795 from z 1.0 down to 0.76, rounding into a lower
                  edge at z 0.68 - 0.70
    lamp bar      a slim smoked strip z 1.026-1.058 across the whole tail, its ends
                  sweeping round the corners to a tip at y 0.863, z 0.996; the rear
                  camera sits in a black pod in its middle (y +/-0.09)
    rear glass    one pane on the loft's backlight (zx_panels)
    reflectors    a long slim hexagon each side, y 0.456-0.758, z 0.586-0.645
    bumper        gloss black from z 0.553 down (the edge dipping to 0.483 at the
                  corners), four parking sensors at z 0.516, a chrome band z 0.447-0.480
                  that hooks down at the corners, a five-fin diffuser z 0.345-0.447
    lettering     the maker's name (two glyphs) at y +0.59 and '7X' at y -0.63, z 0.94
"""
import math
import os

import bpy
from mathutils import Vector

import zx_surface as S
import zx_nose as N
import zx_panels as PN
import zx_camsolve as CS
from carkit import geom
from carkit.geom import Curve
from carkit import mesh as M
from carkit import cut as C
from carkit import place as P
from carkit.body import fascia as FA
from carkit.body import panels as BP
from carkit.parts import fittings, lamps

BODY = N.BODY
TAIL = N.TAIL
FONT_DIR = os.path.join(os.path.dirname(bpy.app.binary_path), "%d.%d" % bpy.app.version[:2],
                        "datafiles", "fonts")


def _yz(px, x=-2.40):
    """Rear-photo pixels -> [(y, z)] (the photo's left is the car's left, y > 0)."""
    return [CS.rear_yz(u, v, x) for (u, v) in px]


# --------------------------------------------------------------- hardpoints
# The hatch's outline (rtL_up/rtL_low): up the side edge from the bottom corner to the
# top at the lamp bar, then along the bottom edge to the centreline. Pixel readings.
GATE_PX = [(1921, 1655), (1768, 1657), (1576, 1661), (1384, 1666), (1269, 1670),
           (1245, 1660), (1221, 1631), (1202, 1593), (1185, 1545), (1173, 1492),
           (1168, 1444), (1169, 1396), (1180, 1372),
           # on up past the lamp bar to the cap's top edge, so the shut line cuts the hatch's skin
           # clear of the body's (the opening photographs: the lamp bar's swept ends stay on the
           # body)
           (1188, 1345), (1196, 1315), (1204, 1285), (1212, 1255)]
# lamp bar: top edge, lens bottom edge, and the swept end (pixels)
BAR_UP_PX = [(1921, 1314), (1700, 1314), (1500, 1315), (1300, 1316), (1240, 1317),
             (1185, 1320), (1163, 1326), (1135, 1342), (1115, 1362)]
BAR_LO_PX = [(1921, 1346), (1700, 1347), (1500, 1346), (1300, 1345), (1240, 1345),
             (1190, 1348), (1155, 1360), (1130, 1372), (1115, 1370)]
POD_BOX = (1838, 1275, 2005, 1348)           # u0, v0, u1, v1 of the camera pod
REFLECTOR_PX = [(1211, 1733), (1230, 1714), (1260, 1706), (1400, 1703), (1480, 1703),
                (1494, 1714), (1475, 1744), (1400, 1752), (1250, 1759), (1215, 1745)]
# gloss black band: its top edge across, then dipping down the corner (px)
BLACK_PX = [(1921, 1790), (1700, 1790), (1500, 1790), (1300, 1791), (1202, 1793),
            (1144, 1812), (1115, 1836), (1091, 1855)]
# chrome band: across, then hooking down the corner
CHROME_UP_PX = [(1921, 1852), (1700, 1856), (1480, 1860), (1230, 1872), (1180, 1890),
                (1150, 1930), (1140, 1980)]
CHROME_LO_PX = [(1921, 1885), (1700, 1888), (1480, 1892), (1250, 1905), (1205, 1925),
                (1175, 1960), (1156, 2000)]
SENSORS_PX = [(1259, 1824), (1658, 1807)]     # parking sensors, one side (the other mirrored)
DIFFUSER_PX = (1380, 1892, 2463, 1985)        # u0, v0, u1, v1: the fin panel (both sides)

Z_BLACK = CS.rear_yz(1921, 1790)[1]           # 0.553
Z_CHROME = (CS.rear_yz(1921, 1885)[1], CS.rear_yz(1921, 1852)[1])
GATE_Y = 0.795                                # the hatch's side edges (mean of the side line)


# ----------------------------------------------------------------- helpers
def on_tail(y, z, d=0.0):
    w, v = TAIL.wv_at(abs(y), z)
    p, n = TAIL.point(w, v), TAIL.normal(w, v)
    p = (p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d)
    if y < 0.0:
        p, n = (p[0], -p[1], p[2]), (n[0], -n[1], n[2])
    return p, n


class _RearView:
    """What the rear photo sees at (y, z): a ray along +x from behind to the first
    surface of the tail cap as built (its full grid, before any cut) or the flank
    beside it (see rx_rear._RearView: the cap's chart fails at the corners)."""

    def __init__(self):
        from mathutils.bvhtree import BVHTree
        rows, _ = BP.cap_rows(TAIL, TAIL.Z_LO + 0.02, TAIL.Z_HI - 0.0008, 0.0, 1.0,
                              120, 90, top_to_centre=True)
        verts, faces = [], []
        nv = len(rows[0])
        for r in rows:
            verts.extend(r)
        for i in range(len(rows) - 1):
            a, b = i * nv, (i + 1) * nv
            faces += [[a + j, a + j + 1, b + j + 1, b + j] for j in range(nv - 1)]
        base = len(verts)
        vs = [0.20 + 0.65 * k / 60.0 for k in range(61)]
        for i in range(61):
            t = i / 60.0
            verts.extend(S.surface(N.JOIN_R(v) + (-1.30 - N.JOIN_R(v)) * t, v) for v in vs)
        for i in range(60):
            a, b = base + i * 61, base + (i + 1) * 61
            faces += [[a + j, a + j + 1, b + j + 1, b + j] for j in range(60)]
        self.tree = BVHTree.FromPolygons(verts, faces)

    def hit(self, y, z):
        loc, nrm, _i, _d = self.tree.ray_cast(Vector((-3.6, abs(y), z)), Vector((1.0, 0.0, 0.0)), 3.0)
        if loc is None:
            return None
        n = nrm.normalized()
        if n.x > 0.0:
            n = -n
        p, n = tuple(loc), tuple(n)
        if y < 0.0:
            p, n = (p[0], -p[1], p[2]), (n[0], -n[1], n[2])
        return p, n

    def x(self, y, z):
        h = self.hit(y, z)
        if h is None:
            raise RuntimeError("rear view: nothing at (y %.3f, z %.3f)" % (y, z))
        return h[0][0]


_REAR = None


def rear_view():
    global _REAR
    if _REAR is None:
        _REAR = _RearView()
    return _REAR


def on_rear(y, z, d=0.0):
    h = rear_view().hit(y, z)
    if h is None:
        raise RuntimeError("rear view: nothing at (y %.3f, z %.3f)" % (y, z))
    p, n = h
    return (p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d), n


def _font(fn):
    try:
        return bpy.data.fonts.load(os.path.join(FONT_DIR, fn), check_existing=True)
    except Exception as e:
        print("font %s not loaded (%s) - using Blender's default" % (fn, e))
        return None


# ---------------------------------------------------------------- tailgate
def gate_path():
    ring = _yz(GATE_PX)
    pts, nrm = [], []
    for (_x, y, z) in geom.polyline([(0.0, y, z) for (y, z) in [(-0.02, ring[0][1])] + ring], 90):
        p, n = on_rear(y, z)
        pts.append(p)
        nrm.append(n)
    return pts, nrm


def _cut_gate(ob):
    pts, nrm = gate_path()
    c = C.slot("_gate_" + ob.name, pts, nrm, PN.GAP, out=0.03, inside=0.03)
    C.difference(ob, [c], "gate_", reset_materials=True)


def black_top(w):
    """The black band's top edge across the tail (w 0 centre .. 1 the corner join)."""
    return Z_BLACK - 0.070 * geom.smoothstep((w - 0.84) / 0.16)


def black_stand(w):
    return 0.006 - 0.003 * geom.smoothstep((w - 0.85) / 0.15)


def build_tail(collection, lib):
    made = []
    made.append(FA.cap_panel("ZX_Tail_Upper", TAIL, collection, lib, Z_BLACK - 0.070,
                             N.TAIL_Z_HI - 0.0008, 0.0, 1.0, 44, 44, mat="paint",
                             top_to_centre=True, cuts=(_cut_gate,)))
    made += FA.valance("ZX_Tail_Valance", TAIL, collection, lib, black_top,
                       stand=black_stand, nw=44, nz=26, mat="black_gloss",
                       thickness=0.0030)
    return made


# ---------------------------------------------------------------- the lamps
def lamp_place(p, d):
    return on_rear(p[1], p[2], d)


def _edge3(px, n=60):
    ring = _yz(px)
    pts = geom.polyline([(0.0, y, z) for (y, z) in ring], n)
    return [on_rear(y, z)[0] for (_x, y, z) in pts]


def build_lightbar(collection, lib):
    made = []
    out = geom.away_from((-2.10, 0.30, 1.00))
    lo = _edge3(BAR_LO_PX)
    up = _edge3(BAR_UP_PX)
    crown = (lambda k, n: 0.0030 + 0.0010 * math.sin(math.pi * k / n))
    made.append(lamps.lens("ZX_Lightbar_Lens", lo, up, lamp_place, collection,
                           lib["lamp_red_lens"], 5, crown, out, thickness=0.003,
                           bevel=(0.0010, 2, 30)))
    made += lamps.seals("ZX_Lightbar_Seal", lo, up, lamp_place, collection,
                        lib["black_gloss"], out, width=0.0045, d=0.0008)
    # the bright line along the lens' top edge (the chrome highlight in the photographs)
    made.append(lamps.band_between("ZX_Lightbar_Edge", lo, up, range(len(lo)),
                                   (0.90, 0.95, 1.00), lamp_place, lambda k: 0.0050,
                                   collection, lib["chrome"], out))
    # the rear camera's pod in the middle of the bar
    u0, v0, u1, v1 = POD_BOX
    (y0, z1), (y1, z0) = _yz([(u0, v0)])[0], _yz([(u1, v1)])[0]
    yc = 0.0
    hw = abs(y0) if y0 > 0 else abs(y1)
    zc, hh = 0.5 * (z0 + z1), 0.5 * (z1 - z0)
    pod = fittings.rounded_panel("ZX_Lightbar_Pod", (-S.HALF_L, yc, zc), hw, hh, 0.012,
                                 lambda q, d: on_rear(q[1], q[2], d), -S.HALF_L, collection,
                                 lib["black_gloss"], d=0.0045, ny=18, outward=(-1.0, 0.0, 0.0))
    made.append(pod)
    p, n = on_rear(0.0, zc - 0.004, 0.0075)
    cam = fittings.rounded_panel("ZX_Rear_Camera", (-S.HALF_L, 0.0, zc - 0.004), 0.011, 0.011,
                                 0.011, lambda q, d: on_rear(q[1], q[2], d), -S.HALF_L,
                                 collection, lib["lamp_smoked"], d=0.0072, ny=12,
                                 outward=(-1.0, 0.0, 0.0))
    made.append(cam)
    return made


# ------------------------------------------------------- bumper details
def build_bumper_details(collection, lib):
    made = []
    # the reflector: a slim hexagon each side
    ring = _yz(REFLECTOR_PX)
    rows = []
    pts = geom.polyline([(0.0, y, z) for (y, z) in ring + ring[:1]], 40)
    cy = sum(y for (_x, y, _z) in pts) / len(pts)
    cz = sum(z for (_x, _y, z) in pts) / len(pts)
    for k in (1.0, 0.7, 0.4, 0.0):
        rows.append([on_rear(cy + (y - cy) * k, cz + (z - cz) * k, 0.0020)[0] for (_x, y, z) in pts])
    cols = [[rows[r][i] for r in range(len(rows))] for i in range(len(pts))]
    ref = M.mesh_from_rows("ZX_Reflector", cols, collection)
    M.orient(ref.data, geom.axial(-1.0))
    ref.data.materials.append(lib["reflector"])
    M.mirror_y(ref)
    made.append(ref)
    # the chrome band, hooking down the corner
    lo = _edge3(CHROME_LO_PX, 50)
    up = _edge3(CHROME_UP_PX, 50)
    made.append(lamps.lens("ZX_Chrome_Band", lo, up, lamp_place, collection, lib["chrome"], 3,
                           (lambda k, n: 0.0045 + 0.0008 * math.sin(math.pi * k / n)),
                           geom.away_from((-2.10, 0.30, 0.45)), thickness=0.003,
                           bevel=(0.0008, 2, 30)))
    # parking sensors: dark discs on the black band
    for i, (u, v) in enumerate(SENSORS_PX):
        (y, z) = _yz([(u, v)])[0]
        p, n = on_rear(y, z, 0.0045)
        for k, (nm, r, mat) in enumerate((("Ring", 0.0125, "black_gloss"), ("Eye", 0.0085, "lamp_smoked"))):
            ob = fittings.rounded_panel("ZX_Sensor%d%s" % (i, nm), (-S.HALF_L, y, z), r, r, r,
                                        lambda q, d: on_rear(q[1], q[2], d), -S.HALF_L, collection,
                                        lib[mat], d=0.0045 + 0.0008 * k, ny=14,
                                        outward=(-1.0, 0.0, 0.0))
            made.append(ob)
    return made


def _box(name, c, size, collection, mat):
    """An axis-aligned box centred on c = (x, y, z), size = (dx, dy, dz)."""
    x, y, z = c
    hx, hy, hz = (0.5 * t for t in size)
    v = [(x + sx * hx, y + sy * hy, z + sz * hz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    f = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
    ob = M.obj(name, v, f, collection, mat)
    M.orient(ob.data, lambda cc, c0=c: (cc[0] - c0[0], cc[1] - c0[1], cc[2] - c0[2]))
    return ob


def build_diffuser(collection, lib):
    """Black fins in a dark opening under the chrome band (rear photo: u 1380-2463,
    v 1892-1985: five fins, a rail across the top and bottom)."""
    made = []
    u0, v0, u1, v1 = DIFFUSER_PX
    y_half = abs(CS.rear_yz(u0, v0)[0])
    z_top, z_bot = CS.rear_yz(1921, v0)[1], CS.rear_yz(1921, v1)[1]
    n = 6
    for i in range(n):
        y = -y_half + 2.0 * y_half * i / float(n - 1)
        p, nrm = on_rear(y, 0.5 * (z_top + z_bot), 0.0)
        made.append(_box("ZX_Diffuser_Fin%d" % i, (p[0] + 0.012, y, 0.5 * (z_top + z_bot)),
                         (0.030, 0.007, z_top - z_bot), collection, lib["black_gloss"]))
    # the opening's dark back, between the fins
    p, nrm = on_rear(0.0, 0.5 * (z_top + z_bot), 0.0)
    made.append(_box("ZX_Diffuser_Back", (p[0] + 0.004, 0.0, 0.5 * (z_top + z_bot)),
                     (0.008, 2.0 * y_half, z_top - z_bot), collection, lib["shadow"]))
    return made


# ---------------------------------------------------------------- lettering
def build_badges(collection, lib):
    made = []
    inter, cjk = _font("Inter.woff2"), _font("Noto Sans CJK Regular.woff2")
    mat = lib["text_dark"]

    def badge(name, body, size, y, z, font, mat=mat, **kw):
        p, n = on_rear(y, z, 0.0010)
        t = M.text_mesh(name, body, size, collection, mat, extrude=0.0010,
                        font=font, resolution=4, **kw)
        P.on_surface(t, p, n)
        made.append(t)
        return t

    # the maker's name (two glyphs, ~0.105 m wide) on the left, '7X' on the right
    badge("ZX_Badge_Maker", "极氪", 0.040, 0.588, 0.936, cjk, weight=0.0008)
    badge("ZX_Badge_Model", "7X", 0.045, -0.626, 0.947, inter, weight=0.0010)
    return made


def build_plate(collection, lib):
    """Rear show plate on the tailgate with ZEEKR 7X model name."""
    p, n = on_rear(0.0, 0.740, 0.005)
    return fittings.plate("ZX_Plate_Rear", p, n, collection, lib, w=0.440, h=0.140, depth=0.008,
                          texts=[("ZEEKR 7X", 0.0, 0.038, False, True)],
                          mat="black_gloss", text_mat="machined")


def build_all(collection, lib):
    made = []
    made += build_tail(collection, lib)
    made += build_lightbar(collection, lib)
    made += build_bumper_details(collection, lib)
    made += build_diffuser(collection, lib)
    made += build_badges(collection, lib)
    made += build_plate(collection, lib)
    return made
