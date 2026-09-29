"""Luxeed RX front end: fascia, hood front edge, headlamps, lower band,
corner intakes, emblem, chin strip, plate, roof lidar.

Hardpoints were read off the blue car's front 3/4 (front34_blue) and the
grey car's side photograph by casting the photo pixels through the solved
cameras onto the body surface (refmatch.on_mesh), then written here as
elevation (y, z) positions: each part is dropped onto the finished surface
at build time, so it follows any later change to the caps.

    fascia        one painted cap from the lip to the hood, cut by
                  - the hood's front shut line: a smile across the nose above
                    the emblem (z 0.82) rising over the lamps' inner tips
                    (0.855 at y 0.50) and back to the fender's hood line
                  - the lower grille's V-frame: level at z 0.57 behind the
                    plate, its sides running down and out to y 0.59 at z 0.34
                    (front_silver), so the painted corners taper to points
                  - the corner intakes: trapezoids y 0.63-0.85, z 0.46-0.67
    V-frame       a recessed gloss black panel behind the opening; slats
                  behind the plate, an inner frame (bar at z 0.48, down the
                  diagonal to a round sensor), the lower opening's dark back
                  with two bars, the radar box; chrome strip and black lip
    headlamps     inner tip (2.37, 0.52, 0.73) on the face, round the corner
                  to a hook on the fender top at (1.82, 0.87, 0.92)
"""
import math

import rx_surface as S
import rx_nose as N
import rx_panels as PN
from carkit import geom
from carkit import mesh as M
from carkit import cut as C
from carkit import place as P
from carkit.body import fascia as FA
from carkit.parts import fittings, lamps, grilles

BODY = N.BODY
NOSE = N.NOSE
PLACER = P.Placer(BODY.proud)

# --------------------------------------------------------------- hardpoints
# The lower grille's black V-frame, front elevation (y, z), left half: the
# straight-on front_silver cast through its solved camera. Its top is level
# at z 0.57, behind the plate's middle; its outer edges run down and OUT on
# a diagonal (y 0.46 at the top to 0.59 at z 0.34), so the painted bumper
# corners under the intakes taper to points - the "V". (The front 3/4 had
# read only the lower opening, a band z 0.26-0.45 with a rounded corner.)
BAND_TOP = 0.568
# square across the centreline (the half-sheet cut must meet its mirror)
BAND = [(-0.020, 0.150), (-0.020, 0.570), (0.430, 0.568), (0.452, 0.566),
        (0.466, 0.558), (0.478, 0.541), (0.492, 0.516), (0.508, 0.489),
        (0.531, 0.443), (0.547, 0.414), (0.564, 0.385), (0.583, 0.356),
        (0.593, 0.337), (0.600, 0.315), (0.604, 0.290), (0.606, 0.150)]
BAND_RECESS = 0.028
# Inside it, a gloss black inner frame (its highlight read off the photo):
# a bar across at z 0.48 turning down parallel to the outer diagonal to a
# round sensor at (0.565, 0.30). Above the bar, horizontal slats behind the
# plate; below it the lower opening with two bars (z 0.40, 0.33) and the
# radar box on the centreline (y +/-0.093, z 0.34-0.43, dark grey).
FRAME = [(0.000, 0.481), (0.200, 0.481), (0.400, 0.479), (0.426, 0.478),
         (0.447, 0.474), (0.462, 0.466), (0.478, 0.448), (0.493, 0.428),
         (0.517, 0.385), (0.540, 0.346), (0.556, 0.318), (0.562, 0.306)]
FRAME_SENSOR = (0.565, 0.300)
LOWER_BARS = (0.399, 0.327)
RADAR = (0.388, 0.093, 0.047)          # z centre, half-width, half-height
# The lowest height face() can place on: the cap's bottom row tucks under at
# z 0.277 on the centreline, and below that wv_at collapses every y onto the
# centre point - the chin strip was built dead straight across, its ends
# 3 cm proud of the bumper, and the lip bunched inside y +/-0.44.
CAP_LOW = 0.280

# Corner intake, front elevation (y, z), left half: the straight-on
# front_silver cast onto the nose cap - a rounded trapezoid, its outer edge
# upright at y 0.85, its top rising outward, pointed inboard at y 0.63. (The
# front 3/4 reading, oblique to the corner, had it 6 cm outboard and 3 cm low.)
INTAKE = [(0.652, 0.621), (0.737, 0.642), (0.838, 0.665), (0.847, 0.639),
          (0.851, 0.570), (0.835, 0.487), (0.800, 0.463), (0.744, 0.462),
          (0.705, 0.482), (0.657, 0.531), (0.634, 0.587)]

# Hood front edge, (y, z) on the face: across above the emblem, down to the
# lamp's inner tip and up along its top edge to the fender's hood line.
# (front_silver, solved camera: a smile at z 0.817 on the centreline rising
# to 0.853 at y 0.50 - above the lamps' inner tips, not down to them - then
# turning back up the domes' outer flank to the fender's hood line)
HOOD_EDGE = [(-0.020, 0.817), (0.100, 0.818), (0.200, 0.820), (0.300, 0.824),
             (0.360, 0.828), (0.420, 0.836), (0.470, 0.846), (0.505, 0.855),
             (0.530, 0.866)]

# Headlamp edges, left lamp (x, y, z): placed by radial casts onto the built
# fascia and fender, ~4 mm proud.
LAMP_LOWER = [(2.370, 0.522, 0.730), (2.305, 0.662, 0.749), (2.215, 0.810, 0.765),
              (2.110, 0.905, 0.783), (2.000, 0.925, 0.810), (1.900, 0.905, 0.852),
              (1.830, 0.878, 0.895)]
LAMP_UPPER = [(2.362, 0.526, 0.750), (2.275, 0.590, 0.806), (2.195, 0.680, 0.842),
              (2.120, 0.785, 0.868), (2.010, 0.860, 0.892), (1.905, 0.873, 0.908),
              (1.830, 0.878, 0.912)]
LAMP_CENTRE = (1.95, 0.45, 0.62)
LAMP_BODY = ("RX_Fascia", "RX_Fender_Front", "RX_Hood")
NS, NK = 48, 8

EMBLEM = (0.0, 0.762)            # (y, z): on the face below the hood edge
# plate centre: its edges at z 0.474 / 0.623 in front_silver, over the
# V-frame's top
PLATE = (0.0, 0.549)


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


def _hood_path():
    pts, nrm = [], []
    path = geom.polyline([(0.0, y, z) for (y, z) in HOOD_EDGE], 60)
    for (_x, y, z) in path:
        p, n = face(y, z)
        pts.append(p)
        nrm.append(n)
    # on to the join, where the flank's hood line takes over
    v_j = PN.V_HOOD(N.JOIN_F(0.8))
    for k in range(1, 7):
        t = k / 6.0
        w, v = NOSE.wv_at(HOOD_EDGE[-1][0], HOOD_EDGE[-1][1])
        w = w + (1.0 - w) * t
        v = v + (v_j - v) * t
        pts.append(NOSE.point(w, v))
        nrm.append(NOSE.normal(w, v))
    return pts, nrm


def _cut_hood_edge(ob):
    pts, nrm = _hood_path()
    c = C.slot("_hoodedge_" + ob.name, pts, nrm, PN.GAP, out=0.03, inside=0.03)
    C.difference(ob, [c], "hood_", reset_materials=True)


def _cut_band(ob):
    L = S.HALF_L
    c = C.prism_x("_band_" + ob.name, BAND, L + 0.40, L - 0.70)
    sheet = C.sheet_bvh(ob)
    C.difference(ob, [c], "band_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


def _intake_loop():
    pts, ns = [], []
    for (_x, y, z) in geom.polyline([(0.0, y, z) for (y, z) in INTAKE + INTAKE[:1]], 48)[:-1]:
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


# ------------------------------------------------------------------ fascia
def build_fascia(collection, lib):
    made = [FA.cap_panel("RX_Fascia", NOSE, collection, lib, N.NOSE_Z_LO + 0.0008,
                         N.NOSE_Z_HI - 0.0008, 0.0, 1.0, 46, 48, mat="paint",
                         top_to_centre=True,
                         cuts=(_cut_hood_edge, _cut_band, _cut_intake))]

    # the recessed band: gloss black, standing BAND_RECESS behind the face
    rows, _ = BP_cap_rows(N.NOSE_Z_LO + 0.001, BAND_TOP + 0.030, 0.0, 0.70, 14, 30,
                          -BAND_RECESS)
    band = M.mesh_from_rows("RX_Band", rows, collection)
    M.orient(band.data, geom.axial(1.0))
    band.data.materials.append(lib["black_gloss"])
    M.mirror_y(band)
    M.finish(band, thickness=0.0025, bevel=0.0)
    made.append(band)

    # return wall from the painted edge back to the band
    ring = [(0.0, y, z) for (y, z) in BAND[1:-1]]
    a = [face(y, z)[0] for (_x, y, z) in ring]
    b = [face(y, z, -BAND_RECESS - 0.002)[0] for (_x, y, z) in ring]
    wall = M.strip("RX_Band_Wall", a, b, collection, lib["black_gloss"])
    M.mirror_y(wall)
    made.append(wall)

    # corner intakes: dark tunnels
    loop, d = _intake_loop()
    tun = _tunnel("RX_Intake_Tunnel", loop, d, 0.11, collection, lib["shadow"])
    M.mirror_y(tun)
    made.append(tun)
    return made


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


# ------------------------------------------------------------ band details
def _y_on(pts, z):
    """y of a descending elevation polyline [(y, z), ...] at height z."""
    if z >= pts[0][1]:
        return pts[0][0]
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if z1 <= z <= z0:
            return y0 + (y1 - y0) * (z0 - z) / (z0 - z1)
    return pts[-1][0]


def _frame_y(z):
    """The inner frame's outer y at height z (the lower opening's edge)."""
    return _y_on(FRAME[3:], z)


def _band_y(z):
    """The V-frame's outer edge at height z."""
    return _y_on(BAND[2:], z)


def _frame_bar(name, path, collection, mat, width=0.016, back=0.026, crown=0.003):
    """A rounded gloss bar along an elevation path (y, z) on the face: flat
    sides from `back` behind the face, a crowned front that catches the
    highlight the photo shows along the frame."""
    pts = geom.polyline([(0.0, y, z) for (y, z) in path], 4 * len(path))
    rows = []
    for i, (_x, y, z) in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        ty, tz = b[1] - a[1], b[2] - a[2]
        L = math.hypot(ty, tz) or 1.0
        ny, nz = -tz / L * width * 0.5, ty / L * width * 0.5
        x = face(y, z)[0][0]
        rows.append([(x - back, y - ny, z - nz), (x - 0.008, y - ny, z - nz),
                     (x - crown, y, z),
                     (x - 0.008, y + ny, z + nz), (x - back, y + ny, z + nz)])
    ob = M.grid(name, rows, collection, mat, geom.axial(1.0))
    return ob


def build_band_details(collection, lib):
    """The V-frame's inside (front_silver): slats behind the plate, the inner
    frame, the lower opening's dark back, two bars, the radar box and the
    frame's corner sensors; the chrome strip and the black lip under it."""
    made = []
    fx = lambda y, z: face(y, z)[0][0]

    # radar box: a dark grey rounded window on the centreline
    xs = lambda y, z: NOSE.offset(*NOSE.wv_at(abs(y), z), -BAND_RECESS)[0]
    zc, hw, hh = RADAR
    made.append(fittings.rounded_panel(
        "RX_Radar", (S.HALF_L, 0.0, zc), hw, hh, 0.012,
        lambda p, dd: ((xs(p[1], p[2]) + dd, p[1], p[2]), (1.0, 0.0, 0.0)),
        S.HALF_L, collection, lib["radar"], d=0.012, outward=(1.0, 0.0, 0.0)))

    # the inner frame: across at z 0.48 and down the diagonal
    frame = _frame_bar("RX_Band_Frame", FRAME, collection, lib["black_gloss"])
    M.mirror_y(frame)
    made.append(frame)
    # the round sensors at the frame's lower ends, body coloured
    sy, sz = FRAME_SENSOR
    for side in (1.0, -1.0):
        made.append(fittings.rounded_panel(
            "RX_Band_Sensor%s" % ("L" if side > 0 else "R"), (S.HALF_L, side * sy, sz),
            0.011, 0.011, 0.0105,
            lambda q, dd: ((fx(q[1], q[2]) - 0.004 + dd, q[1], q[2]), (1.0, 0.0, 0.0)),
            S.HALF_L, collection, lib["paint"], d=0.0, ny=10, outward=(1.0, 0.0, 0.0)))

    # the lower opening reads deep: a dark back inside the frame, in front
    # of the gloss recess
    rows = []
    for j in range(9):
        z = CAP_LOW + (FRAME[3][1] - 0.004 - CAP_LOW) * j / 8.0
        y1 = _frame_y(z) - 0.004
        rows.append([face(y1 * i / 12.0, z, -BAND_RECESS + 0.004)[0] for i in range(13)])
    back = M.grid("RX_Band_Opening", rows, collection, lib["shadow"], geom.axial(1.0))
    M.mirror_y(back)
    made.append(back)

    # two gloss bars across the opening, behind the radar box
    for k, zb in enumerate(LOWER_BARS):
        bar = grilles.slats("RX_Band_Bar%d" % k, 0.0, _frame_y(zb) - 0.006, zb - 0.006,
                            zb + 0.006, fx, 0.010, collection, lib["black_gloss"], count=1,
                            blade=0.010, depth=0.016, angle_deg=-8.0, n=20)
        M.mirror_y(bar)
        made.append(bar)

    # horizontal slats behind the plate, between the frame bar and the top
    top_y = lambda z: _band_y(z) - 0.006
    sl = grilles.slats("RX_Band_Slats", 0.0, top_y(0.525), 0.490, 0.560, fx, 0.012,
                       collection, lib["black_gloss"], count=5, blade=0.005,
                       depth=0.014, angle_deg=-10.0, n=20)
    M.mirror_y(sl)
    made.append(sl)

    # the chin (front_silver): a slim chrome strip z 0.266-0.286 ending at
    # y 0.53, standing forward of the V-frame, and the black lip under it
    # running the whole nose under the painted bumper corners
    n = 44
    strip = []
    for i in range(n + 1):
        y = -0.532 + 1.064 * i / float(n)
        p0, _n0 = face(y, CAP_LOW, 0.0)
        p1, _n1 = face(y, 0.290, 0.0)
        k = 1.0 - 0.6 * geom.smoothstep((abs(y) - 0.40) / 0.13)
        x0 = max(p0[0], p1[0]) + 0.012 * k
        strip.append([(x0, y, 0.266), (x0, y, 0.286), (p1[0], y, 0.290)])
    s_ob = M.grid("RX_Chin_Strip", strip, collection, lib["chrome"], geom.axial(1.0))
    M.solidify(s_ob, 0.003)
    made.append(s_ob)
    # Round the corner it follows the cap's lower edge along the surface
    # normal, standing off less and less (a lip that rose up the corner cut
    # through the paint in steps)
    lip = []
    n = 64
    for i in range(n + 1):
        y = -0.88 + 1.76 * i / float(n)
        p0, n0 = face(y, CAP_LOW, 0.0)
        h = math.hypot(n0[0], n0[1]) or 1.0
        fx_, fy_ = n0[0] / h, n0[1] / h
        k = 1.0 - 0.4 * geom.smoothstep((abs(y) - 0.40) / 0.13)
        # dying into the corner at the wheel (photo: out to y 0.9)
        k *= 1.0 - 0.8 * geom.smoothstep((abs(y) - 0.78) / 0.10)
        # from the most forward point of the bumper's lower 9 cm: at the
        # corners the paint bulges out above a tucked-under edge, and a lip
        # set off the edge itself hid under it
        base = max((face(y, z, 0.0)[0] for z in (CAP_LOW, 0.29, 0.32, 0.35)),
                   key=lambda p: p[0] * fx_ + p[1] * fy_)
        at = lambda d, z: (base[0] + fx_ * d, base[1] + fy_ * d, z)
        # outboard of the chrome the painted corners end level at z 0.285
        # (front_silver cast: 0.279-0.291 out to y 0.92 - the rise the photo
        # seems to show is the corner wrapping back), so there the lip covers
        # the cap's bottom 2.5 cm
        s = 0.022 * geom.smoothstep((abs(y) - 0.50) / 0.10)
        lip.append([at(-0.030, 0.238 + s), at(0.004 + 0.012 * k, 0.239 + s),
                    at(0.012 * k, 0.266 + s)])
    l_ob = M.grid("RX_Chin_Lip", lip, collection, lib["black_gloss"], geom.axial(1.0))
    M.solidify(l_ob, 0.003)
    made.append(l_ob)
    # three slats in each corner intake
    slats = grilles.slats("RX_Intake_Slats", 0.665, 0.842, 0.480, 0.650, fx, 0.012,
                          collection, lib["black_gloss"], count=3, blade=0.009,
                          depth=0.030, angle_deg=-12.0, n=12)
    M.mirror_y(slats)
    made.append(slats)
    return made


# --------------------------------------------------------------- headlamps
def _lamp_place(p, d):
    return PLACER.radial(p, LAMP_CENTRE, LAMP_BODY, d)


def build_headlamps(collection, lib):
    made = []
    lo = geom.polyline(LAMP_LOWER, NS)
    up = geom.polyline(LAMP_UPPER, NS)
    out = geom.away_from((2.10, 0.55, 0.70))
    crown = lambda k, nk: 0.0035 + 0.0015 * math.sin(math.pi * k / float(nk))
    made.append(lamps.lens("RX_Lamp_Lens", lo, up, _lamp_place, collection,
                           lib["lamp_clear"], NK, crown, out, thickness=0.003))
    made += lamps.seals("RX_Lamp_Seal", lo, up, _lamp_place, collection,
                        lib["lamp_housing"], out, width=0.005, d=0.0008)
    # DRL: a thin guide along the lower edge, the full length of the lamp
    made.append(lamps.band_between("RX_Lamp_DRL", lo, up, range(1, NS - 2),
                                   (0.08, 0.16, 0.24), _lamp_place,
                                   lambda k: 0.0035 + 0.0015 * math.sin(math.pi * k) + 0.0006,
                                   collection, lib["led_white"], out))
    # two projector modules in the outboard half
    for i, yy in enumerate((0.74, 0.84)):
        k = lamps.station_nearest_y(lo, up, yy)
        c, n = _lamp_place(geom.lerp(lo[k], up[k], 0.62), 0.0058)
        made += lamps.projector("RX_Lamp_Proj%d" % i, c, n, 0.018, collection, lib)
    return made


# ---------------------------------------------------------- emblem + plate
def build_emblem(collection, lib):
    """The Luxeed emblem: an upright hexagon with an X, ~65 x 80 mm."""
    p, n = face(EMBLEM[0], EMBLEM[1], 0.002)
    hw, hh, t = 0.032, 0.040, 0.006
    ring = [(0.0, hh), (hw, hh * 0.45), (hw, -hh * 0.45), (0.0, -hh),
            (-hw, -hh * 0.45), (-hw, hh * 0.45)]
    return [fittings_emblem("RX_Emblem", ring, t, p, n, collection, lib["chrome"])]


def fittings_emblem(name, ring, t, p, n, collection, mat):
    """Hexagon outline plus an X, as flat bars in the badge plane."""
    verts, faces = [], []

    def bar(a, b, w):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        ox, oy = -dy / L * w * 0.5, dx / L * w * 0.5
        k = len(verts)
        for q in ((a[0] + ox, a[1] + oy), (b[0] + ox, b[1] + oy),
                  (b[0] - ox, b[1] - oy), (a[0] - ox, a[1] - oy)):
            verts.append((q[0], q[1], 0.0))
        faces.append([k, k + 1, k + 2, k + 3])
    for i in range(len(ring)):
        bar(ring[i], ring[(i + 1) % len(ring)], t)
    bar(ring[1], ring[4], t * 0.8)
    bar(ring[5], ring[2], t * 0.8)
    ob = M.obj(name, verts, faces, collection, mat)
    M.solidify(ob, 0.0025)
    P.on_surface(ob, p, n)
    # on_surface puts local +Y up and +X to the car's left: a front badge
    # faces +X, so its local X must point to -Y (the viewer's right)
    return ob


def build_plate(collection, lib):
    """The 'RX' show plate on the face above the band (grey car: black plate,
    '智界 RX')."""
    p, n = face(PLATE[0], PLATE[1], 0.012)
    return fittings.plate("RX_Plate", p, n, collection, lib, w=0.480, h=0.140,
                          mat="black_gloss", text_mat="chrome",
                          texts=(("RX", 0.0, 0.070, False, True),))


# ------------------------------------------------------------------- lidar
def build_lidar(collection, lib):
    """The roof lidar at the screen header - the black pod on the roof's
    leading edge in every photograph."""
    # wide and flat: ~0.34 m across and ~50 mm tall in front34_blue, ~0.14 m
    # long in the side photograph
    cx = 0.080
    return [fittings.lidar_pod("RX_Lidar", collection, lib["black_gloss"], cx,
                               S.Z_ROOF(cx) - 0.012, a=0.075, b=0.170, c=0.052)]


def build_all(collection, lib):
    PLACER.reset()
    made = []
    made += build_fascia(collection, lib)
    made += build_band_details(collection, lib)
    PLACER.reset()
    made += build_headlamps(collection, lib)
    made += build_emblem(collection, lib)
    made += build_plate(collection, lib)
    made += build_lidar(collection, lib)
    return made
