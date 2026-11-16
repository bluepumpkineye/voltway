"""Zeekr 7X front end: fascia, light bar and lamps, corner intakes, lower grille,
chrome chin lip, emblem.

Hardpoints are read off the straight-on front photograph (front_studio.jpg, 3840 x
2880, the car's right on the image's left) in PIXELS and turned into (|y|, z) by
zx_camsolve.front_yz on the nose's face (x 2.38); each part is then dropped onto the
finished surface at build time (face(), the radial Placer), so it follows any later
change to the caps. The zoomed, gridded crops they were read from are described in
the comments.

    fascia        one painted cap from the lip to the hood, cut by
                  - the corner intakes (a rounded triangle, wide at the top, to a
                    point at the bottom)
                  - the lower grille, one wide black opening whose top edge drops
                    in a diagonal at each end
    light bar     a chrome strip across the nose at z 0.79-0.84 with the emblem in
                  its middle, over a black housing that wraps the corners; under it
                  a grey lens strip that swells into the headlamp at each end
    chin          a slim chrome blade along the bottom of the bumper
"""
import math

import zx_surface as S
import zx_nose as N
import zx_panels as PN
import zx_camsolve as CS
from carkit import geom
from carkit import mesh as M
from carkit import cut as C
from carkit import place as P
from carkit.body import fascia as FA
from carkit.parts import fittings, lamps

BODY = N.BODY
NOSE = N.NOSE
PLACER = P.Placer(BODY.proud)


def _yz(px, x=2.38):
    """Front-photo pixels -> [(|y|, z)] (the photo's left half is the car's right)."""
    out = []
    for (u, v) in px:
        y, z = CS.front_yz(u, v, x)
        out.append((abs(y), z))
    return out


# --------------------------------------------------------------- hardpoints
# Hood lip (the thin black line along the top of the light bar): v 1497 across the
# nose, rising to 1473 round the corner (fn_L crop).
HOOD_EDGE_PX = [(1921, 1497), (1700, 1498), (1500, 1498), (1300, 1498), (1171, 1497),
                (1128, 1490), (1086, 1473)]
# Light bar (chrome): top v 1498, bottom 1548, its outer end rounded off downward.
# 2026-11-16: a thin continuous LED line (2.2 cm, it was a 5.8 cm bar) across the whole visor, centre to end
BAR_UP_PX = [(1921, 1517), (1700, 1517), (1500, 1517), (1300, 1517), (1230, 1518),
             (1197, 1522), (1178, 1530)]
BAR_LO_PX = [(1921, 1539), (1700, 1539), (1500, 1539), (1300, 1539), (1240, 1540),
             (1207, 1542), (1182, 1541)]
# Black housing: from the lip to the lens strip; it wraps the corner (extended in y).
# the top edge runs 4-5 mm UNDER the hood's front edge (it ran on it: slivers of the cap showed between the two
# along the whole lip, the jagged edge the owner pointed at)
HOUSE_UP_PX = [(1921, 1502), (1500, 1502), (1300, 1502), (1171, 1503), (1128, 1507),
               (1100, 1512), (1086, 1519)]
HOUSE_LO_PX = [(1921, 1597), (1700, 1597), (1450, 1596), (1300, 1594), (1170, 1588),
               (1124, 1580), (1090, 1572)]
# The grey lens strip, and its lower edge: swelling into the headlamp's lobe.
LENS_UP_PX = HOUSE_LO_PX
LENS_LO_PX = [(1921, 1623), (1700, 1625), (1545, 1627), (1432, 1632), (1405, 1641),
              (1374, 1660), (1320, 1664), (1239, 1663), (1198, 1659), (1153, 1645),
              (1131, 1605), (1124, 1580)]
# Corner intake (fn_L crop): a rounded triangle, wide at the top, pointed at the bottom.
INTAKE_PX = [(1135, 1742), (1185, 1735), (1239, 1735), (1266, 1749), (1274, 1765),
             (1248, 1808), (1221, 1853), (1185, 1916), (1158, 1970), (1136, 1979),
             (1122, 1974), (1120, 1875), (1124, 1785)]
# Lower grille, car's right half in the image; the cut spans the whole width (centre
# bar included): top edge v 1885 between the diagonals, down to the chin lip.
GRILLE_PX = [(1275, 2033), (1302, 2003), (1342, 1972), (1388, 1937), (1432, 1907),
             (1478, 1891), (1523, 1887), (1700, 1885), (1921, 1885)]
GRILLE_BOTTOM_PX = [(1921, 2038), (1700, 2038), (1500, 2038), (1275, 2038)]
# The chin: a chrome blade v 2044-2058 along the whole bottom edge of the bumper
# (its end wedge at the corner reaches v 2069).
CHIN_UP_PX = [(1921, 2044), (1700, 2044), (1450, 2044), (1250, 2042), (1150, 2036),
              (1088, 2024)]
CHIN_LO_PX = [(1921, 2058), (1700, 2058), (1450, 2058), (1250, 2060), (1150, 2064),
              (1100, 2069)]

# a point inside the nose, behind the corner, for the radial casts
LAMP_CENTRE = (1.95, 0.40, 0.58)
LAMP_BODY = ("ZX_Fascia", "ZX_Fender_Front", "ZX_Hood")
NS, NK = 56, 6
CAP_LOW = 0.268                   # lowest height face() can place on

EMBLEM = (0.0, 0.814)             # (y, z): on the bar's middle


# ----------------------------------------------------------------- helpers
def face(y, z, d=0.0):
    """Point on the nose cap at elevation (y, z) (left half), and normal."""
    w, v = NOSE.wv_at(abs(y), z)
    p, n = NOSE.point(w, v), NOSE.normal(w, v)
    if d:
        p = tuple(p[i] + n[i] * d for i in range(3))
    if y < 0.0:
        p, n = (p[0], -p[1], p[2]), (n[0], -n[1], n[2])
    return p, n


def _poly3(yz, extend=None, n=NS):
    """Elevation polyline [(y, z)] -> n 3D points lying on the cap's face (x from
    the cap at that elevation; the radial Placer then snaps them to the built
    skin). `extend` appends points (y, z) round the corner."""
    pts = list(yz) + list(extend or [])
    return geom.polyline([(NOSE.x_at(y, max(NOSE.Z_LO + 0.002, min(NOSE.Z_HI - 0.002, z))) - 0.01,
                           y, z) for (y, z) in pts], n)


def _place(p, d):
    # the analytic surface (nose cap or flank, whichever is nearer): the points of every
    # strip are made ON the cap, so this is smooth. The radial ray cast onto the built
    # meshes jumped between the hood's lip and the fascia and left the light bar's
    # edges ragged.
    return BODY.proud(p, d)


def BP_cap_rows(z_lo, z_hi, w_lo, w_hi, nz, nw, offset):
    from carkit.body import panels as BP
    return BP.cap_rows(NOSE, z_lo, z_hi, w_lo, w_hi, nz, nw, offset=offset)


def _tunnel(name, loop, d, depth, collection, mat, taper=0.9):
    c = [sum(p[i] for p in loop) / len(loop) for i in range(3)]
    rows = [[tuple(p[i] + d[i] * 0.003 for i in range(3)) for p in loop]]
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


# ------------------------------------------------------------------- cuts
def _intake_loop():
    pts, ns = [], []
    ring = _yz(INTAKE_PX)
    for (_x, y, z) in geom.polyline([(0.0, y, z) for (y, z) in ring + ring[:1]], 48)[:-1]:
        p, n = face(y, z)
        pts.append(p)
        ns.append(n)
    d = [sum(n[i] for n in ns) for i in range(3)]
    L = math.sqrt(sum(c * c for c in d))
    return pts, tuple(c / L for c in d)


def _cut_intake(ob):
    loop, d = _intake_loop()
    c = C.prism_dir("_intake_" + ob.name, loop, d, back=0.20, front=0.10)
    sheet = C.sheet_bvh(ob)
    C.difference(ob, [c], "intake_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


def _grille_outline():
    """(y, z) outline of the grille opening, square across the centreline (the
    half-sheet cut must meet its mirror)."""
    top = _yz(GRILLE_PX)             # outer foot of the diagonal -> centre
    bot = _yz(GRILLE_BOTTOM_PX)      # centre -> outer
    pts = [(-0.020, top[-1][1])] + list(reversed(top[:-1]))
    pts += [(bot[-1][0], bot[-1][1]), (-0.020, bot[0][1])]
    return pts


def _cut_grille(ob):
    c = C.prism_x("_grille_" + ob.name, _grille_outline(), S.HALF_L + 0.40, S.HALF_L - 0.70)
    sheet = C.sheet_bvh(ob)
    C.difference(ob, [c], "grille_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


# ------------------------------------------------------------------ fascia
GRILLE_RECESS = 0.030


def build_fascia(collection, lib):
    made = [FA.cap_panel("ZX_Fascia", NOSE, collection, lib, N.NOSE_Z_LO + 0.0008,
                         N.NOSE_Z_HI - 0.0008, 0.0, 1.0, 46, 48, mat="paint",
                         top_to_centre=True, cuts=(_cut_intake, _cut_grille))]
    # the recessed black grille panel behind the opening
    gz = [z for (_y, z) in _grille_outline()]
    rows, _ = BP_cap_rows(N.NOSE_Z_LO + 0.001, max(gz) + 0.030, 0.0, 0.72, 14, 30,
                          -GRILLE_RECESS)
    band = M.mesh_from_rows("ZX_Band", rows, collection)
    M.orient(band.data, geom.axial(1.0))
    band.data.materials.append(lib["grille"])
    M.mirror_y(band)
    M.finish(band, thickness=0.0025, bevel=0.0)
    made.append(band)
    # corner intakes: dark tunnels
    loop, d = _intake_loop()
    tun = _tunnel("ZX_Intake_Tunnel", loop, d, 0.11, collection, lib["shadow"])
    M.mirror_y(tun)
    made.append(tun)
    return made


# --------------------------------------------------------------- light bar
def _strip(name, lo_px, up_px, dist, collection, mat, extend_lo=(), extend_up=(),
           bevel=(0.0008, 2, 30), thickness=0.0030):
    lo = _poly3(_yz(lo_px), extend_lo)
    up = _poly3(_yz(up_px), extend_up)
    out = geom.away_from((2.10, 0.55, 0.62))
    return lamps.lens(name, lo, up, _place, collection, mat, NK, dist, out,
                      thickness=thickness, bevel=bevel)


def build_lightbar(collection, lib):
    made = []
    # 2026-11-16: the visor. One continuous dark smoked-glass housing from end to end under the hood's lip
    # (the old one ran on round the corner as two thin wedges: the spike on the hood's corner)
    made.append(_strip("ZX_Lamp_House", HOUSE_LO_PX, HOUSE_UP_PX,
                       lambda k, nk: 0.0030 + 0.0010 * math.sin(math.pi * k / nk),
                       collection, lib["visor"]))
    # the smoked lens strip under the LED line, swelling into the headlamp lobe (the lower matrix lamp)
    made.append(_strip("ZX_Lamp_Lens", LENS_LO_PX, LENS_UP_PX,
                       lambda k, nk: 0.0040 + 0.0012 * math.sin(math.pi * k / nk),
                       collection, lib["visor_glass"]))
    # the light bar over the housing: a pale satin light guide (a flat silver-white band in
    # the photographs, lit white with the headlamps on - the viewer lights "led_white")
    made.append(_strip("ZX_Lightbar", BAR_LO_PX, BAR_UP_PX,
                       lambda k, nk: 0.0062 + 0.0018 * math.sin(math.pi * k / nk),
                       collection, lib["led_white"], bevel=(0.0010, 2, 30)))
    return made


# ------------------------------------------------------------ grille detail
GRILLE_SLATS = 4
RADAR_HW, RADAR_HH = 0.092, 0.080          # the central radar module, ~18 x 16 cm (front photo)
MATRIX_PX = [(1186, 1631), (1213, 1631), (1240, 1631), (1267, 1631), (1294, 1631), (1321, 1631),
             (1348, 1631)]


def _grille_edges():
    ol = _grille_outline()
    return ol[:-2], ol[-1][1]        # the top edge [(y, z)] centre -> outer foot, the bottom height


def _edge_y(top, z):
    """|y| where the opening's top edge has fallen to height z."""
    y = 0.0
    while y < top[-1][0] and _lerp_y(top, y) > z:
        y += 0.004
    return y


def build_grille_detail(collection, lib):
    """The lower grille's furniture (the photographs): horizontal slats on both sides of a square radar
    module in the middle, and a thin bright edge along the opening's top (it runs down the diagonals)."""
    made = []
    top, z_bot = _grille_edges()
    z_top_c = _lerp_y(top, 0.0)
    y_out = top[-1][0]
    # the radar module fills the opening's middle (it was 16 cm tall in an opening ~14 cm high at the centre and
    # stood out below the grille's lower edge)
    rh = 0.5 * (z_top_c - z_bot) - 0.014
    rw = 1.10 * rh
    zc = 0.5 * (z_top_c + z_bot)
    inside = -GRILLE_RECESS
    for k in range(GRILLE_SLATS):
        z = z_bot + 0.030 + (z_top_c - z_bot - 0.058) * k / float(GRILLE_SLATS - 1)
        y_hi = _edge_y(top, z + 0.004) - 0.040
        y_lo = rw + 0.006
        if y_hi <= y_lo + 0.05:
            continue
        rows = []
        for i in range(15):
            y = y_lo + (y_hi - y_lo) * i / 14.0
            rows.append([face(y, z - 0.0035, inside + 0.012)[0], face(y, z + 0.0035, inside + 0.012)[0]])
        ob = M.grid("ZX_Grille_Slat%d" % k, rows, collection, lib["radar"], geom.axial(1.0))
        M.solidify(ob, 0.010)
        M.mirror_y(ob, clip=False)
        made.append(ob)

    def place(q, d):
        return face(q[1], q[2], inside + d)

    made.append(fittings.rounded_panel("ZX_Grille_Radar", (S.HALF_L, 0.0, zc), rw, rh, 0.018,
                                       place, S.HALF_L, collection, lib["radar"], d=0.014, ny=24,
                                       outward=(1.0, 0.0, 0.0)))
    made.append(fittings.rounded_panel("ZX_Grille_RadarLens", (S.HALF_L, 0.0, zc), rw - 0.017,
                                       rh - 0.017, 0.012, place, S.HALF_L, collection,
                                       lib["lamp_smoked"], d=0.0158, ny=24, outward=(1.0, 0.0, 0.0)))
    rows = []
    for i in range(61):
        y = y_out * i / 60.0
        z = _lerp_y(top, y)
        rows.append([face(y, z + 0.0004, 0.0025)[0], face(y, z + 0.0074, 0.0025)[0]])
    edge = M.grid("ZX_Grille_Edge", rows, collection, lib["trim_silver"], geom.axial(1.0))
    M.solidify(edge, 0.002)
    M.mirror_y(edge)
    made.append(edge)
    return made


def build_matrix(collection, lib):
    """The matrix headlamp's LED elements: a row of small light cells in each lens lobe."""
    made = []
    for i, (u, v) in enumerate(MATRIX_PX):
        (y, z) = _yz([(u, v)])[0]
        ob = fittings.rounded_panel("ZX_Lamp_Cell%d" % i, (S.HALF_L, y, z), 0.0095, 0.0036, 0.0026,
                                    lambda q, d: face(q[1], q[2], d), S.HALF_L, collection,
                                    lib["led_white"], d=0.0062, ny=8, outward=(1.0, 0.0, 0.0))
        M.mirror_y(ob, clip=False)
        made.append(ob)
    return made


# --------------------------------------------------------------- chin lip
def build_chin(collection, lib):
    made = []
    up = _yz(CHIN_UP_PX)
    lo = _yz(CHIN_LO_PX)
    n = 44
    strip = []
    for i in range(n + 1):
        t = i / float(n)
        # elevation positions along the lip, from the centre (y 0) out to the corner
        y = up[-1][0] * t
        zu = _lerp_y(up, y)
        zl = _lerp_y(lo, y)
        p0, _n0 = face(y, max(CAP_LOW, zl), 0.0)
        p1, _n1 = face(y, max(CAP_LOW + 0.01, zu + 0.012), 0.0)
        k = 1.0 - 0.6 * geom.smoothstep((abs(y) - 0.40) / 0.30)
        x0 = max(p0[0], p1[0]) + 0.010 * k
        strip.append([(x0, y, zl), (x0, y, zu), (p1[0], y, zu + 0.004)])
    s_ob = M.grid("ZX_Chin_Strip", strip, collection, lib["chrome"], geom.axial(1.0))
    M.solidify(s_ob, 0.003)
    M.mirror_y(s_ob)
    made.append(s_ob)
    return made


def _lerp_y(pts, y):
    """z of the polyline [(y, z), ...] (y ascending or descending) at y."""
    pts = sorted(pts)
    if y <= pts[0][0]:
        return pts[0][1]
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if y0 <= y <= y1:
            t = 0.0 if y1 == y0 else (y - y0) / (y1 - y0)
            return z0 + (z1 - z0) * t
    return pts[-1][1]


# ---------------------------------------------------------------- emblem
# The maker's badge on the bar's middle (emblem crop, 5.6x): a white plate 0.060 x 0.0395
# m holding two dark blocks split by a stepped diagonal (a stylised S); crop px below.
_EMB_PLATE = (270.0, 225.0, 590.0, 447.0)          # x0, y0, x1, y1 of the white plate
_EMB_LEFT = [(308, 256), (372, 256), (372, 305), (450, 372), (450, 430), (308, 430)]
_EMB_RIGHT = [(418, 256), (555, 256), (555, 430), (492, 430), (492, 368), (418, 300)]
_EMB_K = 0.0600 / 320.0                               # metres per crop px


def _emb_local(pt):
    x0, y0, x1, y1 = _EMB_PLATE
    return ((pt[0] - 0.5 * (x0 + x1)) * _EMB_K, -(pt[1] - 0.5 * (y0 + y1)) * _EMB_K)


def _flat(name, poly, collection, mat):
    n = len(poly)
    verts = [(x, y, 0.0) for (x, y) in poly]
    ob = M.obj(name, verts, [list(range(n))], collection, mat)
    return ob


def build_emblem(collection, lib):
    """Zeekr badge centered on the nose light bar: gloss-black housing + crisp chrome Zeekr mark."""
    p, n = face(EMBLEM[0], EMBLEM[1], 0.0)
    hw, hh = 0.028, 0.022
    back_loop = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    back = fittings.emblem_poly("ZX_Emblem_Back", [back_loop], 0.0032, collection, lib["black_gloss"],
                                bevel=0.0010)
    P.on_surface(back, tuple(p[i] + n[i] * 0.0126 for i in range(3)), n)
    mark = fittings.emblem_zeekr("ZX_Emblem_Mark", collection, lib["chrome"],
                                  w=0.042, h=0.034, bar=0.0036, step=0.0046, thick=0.0020, bevel=0.0004)
    P.on_surface(mark, tuple(p[i] + n[i] * 0.0156 for i in range(3)), n)
    return [back, mark]


def build_plate(collection, lib):
    """Front show plate on the lower bumper fascia with ZEEKR 7X model name."""
    p, n = face(0.0, 0.495, 0.004)
    return fittings.plate("ZX_Plate_Front", p, n, collection, lib, w=0.440, h=0.140, depth=0.008,
                          texts=[("ZEEKR 7X", 0.0, 0.038, False, True)],
                          mat="black_gloss", text_mat="machined")


def build_all(collection, lib):
    PLACER.reset()
    made = []
    made += build_fascia(collection, lib)
    PLACER.reset()
    made += build_lightbar(collection, lib)
    made += build_matrix(collection, lib)
    made += build_grille_detail(collection, lib)
    made += build_chin(collection, lib)
    made += build_emblem(collection, lib)
    made += build_plate(collection, lib)
    return made
