"""Avatr 06T front end: fascia, hood front edge, F-type flying-wing headlamps,
lower active grille, chin splitter, prism emblem, roof lidar.

Read off the official renders (design-list_01.jpg, banner.jpg) and the
Autohome turnaround photographs (c1_0001..0003.jpg):

    fascia        one painted cap from the lip to the hood, cut by
                  - the hood's front shut line across the upper nose
                    (z ~0.78) rising over the lamps' inner tips
                  - the lower grille opening: a wide trapezoid, z 0.22..0.47
    lower grille  recessed gloss-black panel with vertical slats, central
                  mmWave radar, full-width chin splitter with silver edge
    headlamps     F-type "flying wing": a slim dark housing with two DRL
                  blades (upper C-wing + lower blade) that sweeps from the
                  inner tip (y 0.48) to the outer corner and a vertical
                  DRL strip dropping down the bumper's outer edge; two
                  matrix projector lenses in the outboard half
    emblem        illuminated Avatr prism badge on the nose face
    lidar         Huawei 896-line pod above the windscreen header
"""
import math

import a06t_surface as S
import a06t_nose as N
import a06t_panels as PN
from carkit import geom
from carkit import mesh as M
from carkit import cut as C
from carkit import place as P
from carkit.body import fascia as FA
from carkit.parts import fittings, lamps

BODY = N.BODY
NOSE = N.NOSE
PLACER = P.Placer(BODY.proud)

# --------------------------------------------------------------- hardpoints
# Lower grille opening, front elevation (y, z), left half, square across the
# centreline: a low, wide dark trapezoid just above the splitter (c1_0001).
BAND_TOP = 0.305
BAND = [(-0.020, 0.040), (-0.020, 0.307), (0.400, 0.303), (0.560, 0.288),
        (0.660, 0.258), (0.725, 0.215), (0.760, 0.170), (0.775, 0.120),
        (0.778, 0.040)]
BAND_RECESS = 0.030
RADAR = (0.222, 0.100, 0.038)           # z centre, half-width, half-height
CAP_LOW = NOSE_LO = N.NOSE_Z_LO + 0.018

# Hood front edge (y, z) on the face: a clean low smile across the nose at
# z ~0.74 (the hood is one broad clamshell), lifting toward the lamps.
HOOD_EDGE = [(-0.020, 0.735), (0.100, 0.736), (0.200, 0.738), (0.300, 0.742),
             (0.400, 0.748), (0.470, 0.754), (0.520, 0.760)]

# F-type flying wing, (y, z) on the face, left half. Two slim DRL blades: the
# upper "C-wing" bar (z 0.67 -> 0.71 sweeping outward) and a lower blade (z
# 0.615 -> 0.628); the dark lens sits between them. A vertical DRL then drops
# down the bumper's outer edge, and a dark triangular housing with the
# matrix projectors hangs under the lower blade.
LAMP_UPPER = [(0.360, 0.668), (0.480, 0.673), (0.600, 0.682), (0.720, 0.695),
              (0.800, 0.706), (0.850, 0.714)]
LAMP_LOWER = [(0.300, 0.612), (0.420, 0.615), (0.540, 0.619), (0.660, 0.624),
              (0.760, 0.629), (0.850, 0.640)]
DRL_DROP_Y = (0.862, 0.874)
DRL_DROP_Z = (0.700, 0.430)
HOUSING = [(0.500, 0.600), (0.700, 0.606), (0.860, 0.612), (0.862, 0.500),
           (0.830, 0.420), (0.760, 0.335), (0.690, 0.405)]
PROJECTORS = ((0.740, 0.545), (0.790, 0.470))
LAMP_CENTRE = (1.95, 0.45, 0.62)
LAMP_BODY = ("A06T_Fascia", "A06T_Fender_Front", "A06T_Hood")
NS, NK = 36, 8

EMBLEM = (0.0, 0.640)                   # (y, z) on the nose face


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


def BP_cap_rows(z_lo, z_hi, w_lo, w_hi, nz, nw, offset):
    from carkit.body import panels as BP
    return BP.cap_rows(NOSE, z_lo, z_hi, w_lo, w_hi, nz, nw, offset=offset)


def _hood_path():
    pts, nrm = [], []
    path = geom.polyline([(0.0, y, z) for (y, z) in HOOD_EDGE], 60)
    for (_x, y, z) in path:
        p, n = face(y, z)
        pts.append(p)
        nrm.append(n)
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


# ------------------------------------------------------------------ fascia
def build_fascia(collection, lib):
    made = [FA.cap_panel("A06T_Fascia", NOSE, collection, lib, N.NOSE_Z_LO + 0.0008,
                         N.NOSE_Z_HI - 0.0008, 0.0, 1.0, 46, 48, mat="paint",
                         top_to_centre=True, cuts=(_cut_hood_edge, _cut_band))]

    # the recessed grille back: gloss black, standing BAND_RECESS behind the face
    rows, _ = BP_cap_rows(N.NOSE_Z_LO + 0.001, BAND_TOP + 0.030, 0.0, 0.88, 14, 34,
                          -BAND_RECESS)
    band = M.mesh_from_rows("A06T_Band", rows, collection)
    M.orient(band.data, geom.axial(1.0))
    band.data.materials.append(lib["black_gloss"])
    M.mirror_y(band)
    M.finish(band, thickness=0.0025, bevel=0.0)
    made.append(band)

    # return wall from the painted edge back to the recess
    ring = [(0.0, y, z) for (y, z) in BAND[1:-1]]
    a = [face(y, z)[0] for (_x, y, z) in ring]
    b = [face(y, z, -BAND_RECESS - 0.002)[0] for (_x, y, z) in ring]
    wall = M.strip("A06T_Band_Wall", a, b, collection, lib["black_gloss"])
    M.mirror_y(wall)
    made.append(wall)
    return made


# ------------------------------------------------------------ band details
def _band_y(z):
    """The opening's outer edge at height z (descending polyline)."""
    pts = BAND[2:]
    if z >= pts[0][1]:
        return pts[0][0]
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if z1 <= z <= z0:
            return y0 + (y1 - y0) * (z0 - z) / (z0 - z1)
    return pts[-1][0]


def build_band_details(collection, lib):
    """Vertical active-grille slats, the radar window, and the chin splitter
    with its silver edge trim."""
    made = []
    fx = lambda y, z: face(y, z)[0][0]

    # mmWave radar: dark grey rounded window on the centreline
    xs = lambda y, z: NOSE.offset(*NOSE.wv_at(abs(y), z), -BAND_RECESS)[0]
    zc, hw, hh = RADAR
    made.append(fittings.rounded_panel(
        "A06T_Radar", (S.HALF_L, 0.0, zc), hw, hh, 0.012,
        lambda p, dd: ((xs(p[1], p[2]) + dd, p[1], p[2]), (1.0, 0.0, 0.0)),
        S.HALF_L, collection, lib["radar"], d=0.012, outward=(1.0, 0.0, 0.0)))

    # vertical slats across the grille opening (both sides, one mesh)
    verts, faces = [], []
    pitch, wid, dep = 0.052, 0.010, 0.022
    n_slat = 14
    z_lo, z_hi = CAP_LOW + 0.030, BAND_TOP - 0.012
    for side in (1.0, -1.0):
        for i in range(n_slat):
            y = 0.150 + pitch * i
            if y < RADAR[1] + 0.020 and False:
                continue
            # skip slats that would pass in front of the radar window
            top_z = z_hi
            lo_z = z_lo
            if abs(y) < RADAR[1] + 0.012:
                lo_z = RADAR[0] + RADAR[2] + 0.010
            edge = _band_y(lo_z) - 0.020
            if y > edge:
                break
            x_f = min(fx(y, lo_z), fx(y, top_z)) - BAND_RECESS + dep
            x_b = x_f - dep
            k = len(verts)
            for (xx, zz) in ((x_b, lo_z), (x_f, lo_z), (x_f, top_z), (x_b, top_z)):
                verts.append((xx, side * (y - wid * 0.5), zz))
                verts.append((xx, side * (y + wid * 0.5), zz))
            # 8 verts: index = 2*corner + (0 inner y, 1 outer y)
            faces += [[k + 0, k + 1, k + 3, k + 2], [k + 2, k + 3, k + 5, k + 4],
                      [k + 4, k + 5, k + 7, k + 6], [k + 6, k + 7, k + 1, k + 0],
                      [k + 0, k + 2, k + 4, k + 6], [k + 1, k + 7, k + 5, k + 3]]
    slats = M.obj("A06T_Grille_Slats", verts, faces, collection, lib["black_gloss"],
                  smooth=False)
    made.append(slats)

    # chin splitter: a slim chrome strip standing forward of the grille and a
    # gloss-black lip under it running the full width round the corners
    n = 44
    strip = []
    zc = CAP_LOW
    for i in range(n + 1):
        y = -0.790 + 1.580 * i / float(n)
        p0, _n0 = face(y, zc, 0.0)
        p1, _n1 = face(y, zc + 0.010, 0.0)
        k = 1.0 - 0.6 * geom.smoothstep((abs(y) - 0.45) / 0.30)
        x0 = max(p0[0], p1[0]) + 0.012 * k
        strip.append([(x0, y, zc - 0.014), (x0, y, zc + 0.006), (p1[0], y, zc + 0.010)])
    s_ob = M.grid("A06T_Chin_Strip", strip, collection, lib["chrome"], geom.axial(1.0))
    M.solidify(s_ob, 0.003)
    made.append(s_ob)

    lip = []
    n = 64
    for i in range(n + 1):
        y = -0.90 + 1.80 * i / float(n)
        p0, n0 = face(y, zc, 0.0)
        h = math.hypot(n0[0], n0[1]) or 1.0
        fx_, fy_ = n0[0] / h, n0[1] / h
        k = 1.0 - 0.4 * geom.smoothstep((abs(y) - 0.45) / 0.30)
        k *= 1.0 - 0.8 * geom.smoothstep((abs(y) - 0.80) / 0.10)
        base = max((face(y, z, 0.0)[0] for z in (zc, zc + 0.010, zc + 0.040, zc + 0.070)),
                   key=lambda p: p[0] * fx_ + p[1] * fy_)
        at = lambda d, z: (base[0] + fx_ * d, base[1] + fy_ * d, z)
        s = 0.020 * geom.smoothstep((abs(y) - 0.55) / 0.15)
        lip.append([at(-0.030, zc - 0.042 + s), at(0.004 + 0.012 * k, zc - 0.041 + s),
                    at(0.012 * k, zc - 0.014 + s)])
    l_ob = M.grid("A06T_Chin_Lip", lip, collection, lib["black_gloss"], geom.axial(1.0))
    M.solidify(l_ob, 0.003)
    made.append(l_ob)
    return made


# --------------------------------------------------------------- headlamps
def _lamp_place(p, d):
    return PLACER.radial(p, LAMP_CENTRE, LAMP_BODY, d)


def _on_face(pairs, n):
    """Elevation (y, z) pairs -> n points on the nose face (smooth polyline)."""
    path = geom.polyline([(0.0, y, z) for (y, z) in pairs], n)
    return [face(y, z)[0] for (_x, y, z) in path]


def build_headlamps(collection, lib):
    made = []
    lo = _on_face(LAMP_LOWER, NS)
    up = _on_face(LAMP_UPPER, NS)
    out = geom.away_from((2.10, 0.55, 0.70))
    crown = lambda k, nk: 0.0030 + 0.0012 * math.sin(math.pi * k / float(nk))
    made.append(lamps.lens("A06T_Lamp_Lens", lo, up, _lamp_place, collection,
                           lib["lamp_clear"], NK, crown, out, thickness=0.003))
    made += lamps.seals("A06T_Lamp_Seal", lo, up, _lamp_place, collection,
                        lib["lamp_housing"], out, width=0.004, d=0.0008)
    width = lambda k: 0.0040 + 0.0012 * math.sin(math.pi * k)
    # lower DRL blade along the lower edge, the upper C-wing bar along the top
    made.append(lamps.band_between("A06T_Lamp_DRL_Low", lo, up, range(1, NS - 1),
                                   (0.06, 0.10, 0.14), _lamp_place, width,
                                   collection, lib["led_white"], out))
    made.append(lamps.band_between("A06T_Lamp_DRL_Up", lo, up, range(1, NS - 1),
                                   (0.86, 0.90, 0.94), _lamp_place, width,
                                   collection, lib["led_white"], out))
    # the vertical DRL dropping down the bumper's outer edge
    n = 20
    dlo = [face(DRL_DROP_Y[0], DRL_DROP_Z[0] + (DRL_DROP_Z[1] - DRL_DROP_Z[0]) * k / (n - 1.0))[0]
           for k in range(n)]
    dup = [face(DRL_DROP_Y[1], DRL_DROP_Z[0] + (DRL_DROP_Z[1] - DRL_DROP_Z[0]) * k / (n - 1.0))[0]
           for k in range(n)]
    made.append(lamps.band_between("A06T_Lamp_DRL_Drop", dlo, dup, range(n),
                                   (0.30, 0.50, 0.70), _lamp_place,
                                   lambda k: 0.0042, collection, lib["led_white"], out))
    # the dark triangular housing under the lower blade: concentric rings on the
    # nose surface so it stays completely proud of the curved bumper
    ring = geom.polyline([(0.0, y, z) for (y, z) in HOUSING + HOUSING[:1]], 36)[:-1]
    cy = sum(y for _x, y, z in ring) / len(ring)
    cz = sum(z for _x, y, z in ring) / len(ring)
    verts = [face(cy, cz, 0.0035)[0]]
    faces = []
    # ring 1 at 0.55 scale, ring 2 at 1.0 scale
    n_ring = len(ring)
    for scale in (0.55, 1.0):
        for _x, y, z in ring:
            verts.append(face(cy + (y - cy) * scale, cz + (z - cz) * scale, 0.0035)[0])
    # fan to ring 1
    for i in range(n_ring):
        faces.append([0, 1 + (i + 1) % n_ring, 1 + i])
    # quad strip between ring 1 and ring 2
    b1 = 1
    b2 = 1 + n_ring
    for i in range(n_ring):
        i_next = (i + 1) % n_ring
        faces.append([b1 + i, b1 + i_next, b2 + i_next, b2 + i])
    hs = M.obj("A06T_Lamp_Housing", verts, faces, collection, lib["lamp_housing"], smooth=True)
    M.orient(hs.data, geom.axial(1.0))
    M.mirror_y(hs)
    made.append(hs)
    for i, (yy, zz) in enumerate(PROJECTORS):
        p, nrm = face(yy, zz, 0.006)
        made += lamps.projector("A06T_Lamp_Proj%d" % i, p, nrm, 0.020, collection, lib)
    return made



# ---------------------------------------------------------------- emblem
def build_emblem(collection, lib):
    """The Avatr prism badge: a tall kite with a vertical centre bar, ~50x95 mm."""
    p, n = face(EMBLEM[0], EMBLEM[1], 0.002)
    hw, hh, t = 0.025, 0.048, 0.006
    ring = [(0.0, hh), (hw, hh * 0.15), (0.0, -hh), (-hw, hh * 0.15)]
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
    bar(ring[0], ring[2], t * 0.8)
    ob = M.obj("A06T_Emblem", verts, faces, collection, lib["chrome"])
    M.solidify(ob, 0.0025)
    P.on_surface(ob, p, n)
    return [ob]


# ---------------------------------------------------------------- front plate
def build_plate(collection, lib):
    """Front show plate with dark holder, and front camera above it."""
    made = []
    p, n = face(0.0, 0.440, 0.002)
    made += fittings.plate("A06T_Plate_Front", p, n, collection, lib, w=0.440, h=0.140,
                           texts=[("AVATR 06T", 0.0, 0.038, False, True)],
                           mat="black_gloss", text_mat="machined")
    p_cam, n_cam = face(0.0, 0.522, 0.002)
    cam = fittings.rounded_panel("A06T_Camera_Front", (p_cam[0], 0.0, 0.522), 0.018, 0.012, 0.006,
                                 lambda q, d: face(q[1], q[2], d), p_cam[0], collection,
                                 lib["lamp_smoked"], d=0.001)
    made.append(cam)
    return made


# ------------------------------------------------------------------- lidar
def build_lidar(collection, lib):
    """Huawei 896-line lidar pod above the windscreen header."""
    cx = 0.060
    return [fittings.lidar_pod("A06T_Lidar", collection, lib["black_gloss"], cx,
                               S.Z_ROOF(cx) - 0.010, a=0.062, b=0.150, c=0.050)]


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
