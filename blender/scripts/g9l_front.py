"""XPeng G9L front end: the fascia, the Robot Face lamp bar, the corner headlamps and their
slits, the lower intake, the chin, the emblem, the plate and the front charge flap.

Hardpoints are read off the straight-on front photograph of the white car (c1_0026.jpg, camera
"front_white") in PIXELS and turned into (|y|, z) by g9l_cam.front_yz on the nose's face; each part
is dropped onto the finished surface at build time (face(), the cap's own lookup), so it follows
any later change to the caps. What the photographs (c1_0001/0002/0025/0026) show:

    fascia        one big smooth painted slab from the hood's lip to a shallow "smile" edge that
                  dips to z 0.536 at the plate and rises to 0.71 at the corners; below it a
                  black band (the smile edge to a lower line at z 0.36) holding the headlamp
                  modules, the central intake (a three-part black panel with a camera in its
                  middle) and the parking sensors; under that a painted chin lip
    lamp bar      a continuous 58 mm light guide at z 0.945-1.003 across the whole nose, its ends
                  turning up and round the corner; the badge sits above it on the hood's lip
    headlamps     a tall dark lens at each corner (y 0.70-0.80, z 0.47-0.70, its top edge
                  slanting with the black wedge) beside a black vertical slit at the very corner
    right front   a rounded-square charge flap at y -0.419, z 0.62 (the car's right side)
"""
import math

import g9l_surface as S
import g9l_nose as N
import g9l_cam as CAM
from carkit import geom
from carkit import mesh as M
from carkit import cut as C
from carkit.body import fascia as FA
from carkit.parts import lamps, fittings

BODY = N.BODY
NOSE = N.NOSE
CAP_LOW = NOSE.Z_LO + 0.004
CAP_HIGH = NOSE.Z_HI - 0.004


def _yz(px, x=2.50):
    """Front-photo pixels -> [(|y|, z)] (the photo's left half is the car's right)."""
    out = []
    for (u, v) in px:
        y, z = CAM.front_yz(u, v, x)
        out.append((abs(y), z))
    return out


def face(y, z, d=0.0):
    """Point on the nose cap at elevation (y, z) (left half), and normal."""
    z = max(CAP_LOW, min(CAP_HIGH, z))
    w, v = NOSE.wv_at(abs(y), z)
    p, n = NOSE.point(w, v), NOSE.normal(w, v)
    if d:
        p = tuple(p[i] + n[i] * d for i in range(3))
    if y < 0.0:
        p, n = (p[0], -p[1], p[2]), (n[0], -n[1], n[2])
    return p, n


def _place(p, d):
    return BODY.proud(p, d)


def _poly3(yz, n):
    """Elevation polyline [(y, z)] -> n 3D points on the cap's face (resampled by arc length)."""
    pts = [(NOSE.x_at(y, max(CAP_LOW, min(CAP_HIGH, z))) - 0.004, y, z) for (y, z) in yz]
    return geom.polyline(pts, n)


def _lerp(pts, y):
    pts = sorted(pts)
    if y <= pts[0][0]:
        return pts[0][1]
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if y0 <= y <= y1:
            t = 0.0 if y1 == y0 else (y - y0) / (y1 - y0)
            return z0 + (z1 - z0) * t
    return pts[-1][1]


# -------------------------------------------------------------- hardpoints (y >= 0, z)
def _smooth(pts, n=56):
    """A pchip curve through traced points [(|y|, z)] resampled at n points: the cutter's outline is as smooth as the paint's edge
    (the hand-read polyline it replaced showed a kink at each of its nine points in the clearcoat's reflection)."""
    pts = sorted(pts)
    cv = geom.Curve(pts, mode="pchip")
    y0, y1 = pts[0][0], pts[-1][0]
    ys = [y0 + (y1 - y0) * i / (n - 1.0) for i in range(n)]
    return [(y, cv(y)) for y in ys]


FASCIA_LOW = sorted([(0.0, 0.5385)] + _smooth(_yz(CAM.SMILE_PX)))                  # centre -> outer corner
BAND_LOW = sorted([(0.0, 0.3635)] + _smooth(_yz(CAM.BAND_BOT_PX)))
# the headlamp lens: bottom edge, top edge (slanting up toward the corner), y from the car's
# centre outward
LENS_BOT = [(0.700, 0.475), (0.802, 0.471)]
LENS_TOP = [(0.700, 0.629), (0.802, 0.696)]
SLIT_Y, SLIT_Z = (0.826, 0.857), (0.435, 0.790)


# ------------------------------------------------------------------ cuts
def _band_outline():
    """(y, z) loop of the black band: the smile edge on top, the chin line under it, closed round
    the outer corner. Square across the centreline (the half-sheet cut must meet its mirror)."""
    top = [(-0.020, FASCIA_LOW[0][1])] + [p for p in FASCIA_LOW if p[0] > 0.0]
    top.append((0.868, top[-1][1]))
    bot = [(-0.020, BAND_LOW[0][1])] + [p for p in BAND_LOW if p[0] > 0.0]
    bot.append((0.868, bot[-1][1]))
    return top + list(reversed(bot))


def _slit_outline():
    (y0, y1), (z0, z1) = SLIT_Y, SLIT_Z
    r = 0.5 * (y1 - y0)
    return geom.round_rect(y0, y1, z0, z1, r, n=6)


def _cut_fascia(ob):
    cutters = [C.prism_x("_cut_band_" + ob.name, _band_outline(), S.HALF_L + 0.30, S.HALF_L - 0.55)]
    sheet = C.sheet_bvh(ob)
    C.difference(ob, cutters, "front_cuts_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


# ------------------------------------------------------------------ fascia
def build_fascia(collection, lib):
    made = []
    # the painted slab, lip to chin, with the black band and the corner slits cut out
    made.append(FA.cap_panel("G9L_Fascia", NOSE, collection, lib, NOSE.Z_LO + 0.001,
                             NOSE.Z_HI - 0.001, 0.0, 1.0, 84, 96, mat="paint",
                             top_to_centre=True, cuts=(_cut_fascia,)))
    # the black band behind the cut: a recessed gloss apron from the smile edge to the chin line
    zs = [z for (_y, z) in _band_outline()]
    rows, _ = _cap_rows(min(zs) - 0.02, max(zs) + 0.02, 0.0, 1.0, 24, 40, -0.008)
    ap = M.mesh_from_rows("G9L_Apron", rows, collection)
    M.orient(ap.data, geom.axial(1.0))
    ap.data.materials.append(lib["black_trim"])
    M.mirror_y(ap)
    M.finish(ap, thickness=0.0025, bevel=0.0)
    made.append(ap)
    made.append(_slit_inlay(collection, lib))
    return made


def _slit_inlay(collection, lib):
    """The corner's black vertical slit (c1_0026: a tall pill 31 mm wide, z 0.435-0.79): a thin black strip standing 1.5 mm
    proud of the fascia and following its corner. It used to be a hole through the fascia with a 7 cm tunnel behind it in the
    +x direction, which at the corner (where the skin faces diagonally) stood out of the fender as a black fin."""
    (y0, y1), (z0, z1) = SLIT_Y, SLIT_Z
    n = 16
    rows = []
    for yy in (y0, 0.5 * (y0 + y1), y1):
        rows.append([face(yy, z0 + (z1 - z0) * k / n, 0.0015)[0] for k in range(n + 1)])
    ob = M.mesh_from_rows("G9L_Slit", rows, collection)
    M.orient(ob.data, geom.axial(1.0))
    ob.data.materials.append(lib["black_gloss"])
    M.mirror_y(ob)
    M.finish(ob, thickness=0.002, bevel=0.0)
    return ob


def _cap_rows(z_lo, z_hi, w_lo, w_hi, nz, nw, offset):
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


# ------------------------------------------------------------ central intake
# c1_0026 (1.0x crop, 2026-10-26): under the plate a black field holds two wide grille panels of three rows each (rows at v 1964-2036,
# 2045-2115 and 2124-2172, 6-9 px of groove between them), either side of a central module (u 1820-2033) with the camera in its
# top. The panels sit recessed in the apron; their rows and the module are what gives the black field its geometry.
INTAKE_ROWS = [(1964, 2036), (2045, 2115), (2124, 2172)]
MODULE_U = (1820, 2033)


def _zv(v):
    return CAM.front_yz(1920, v)[1]


def _patch(name, za, zb, y0, y1, off, mat, collection, nz=4, nw=18, thickness=0.0025):
    """A strip of the nose cap between z za..zb and |y| y0..y1, `off` metres from its surface (negative = recessed)."""
    zm = 0.5 * (za + zb)
    rows, _ = _cap_rows(za, zb, _w_of(y0, zm), _w_of(y1, zm), nz, nw, off)
    ob = M.mesh_from_rows(name, rows, collection)
    M.orient(ob.data, geom.axial(1.0))
    ob.data.materials.append(mat)
    M.mirror_y(ob)
    M.finish(ob, thickness=thickness, bevel=0.0)
    return ob


def build_intake(collection, lib):
    """The grille: three rows of recessed panels each side of a central module with the camera, framed by glossy bezel bars."""
    made = []
    u0 = CAM.INTAKE_PX["u"][0]
    y_out = abs(CAM.front_yz(u0, 2000)[0])
    y_mod = abs(CAM.front_yz(MODULE_U[0], 2000)[0])              # the module's half-width
    z_top, z_bot = _zv(INTAKE_ROWS[0][0]), _zv(INTAKE_ROWS[-1][1])
    for k, (va, vb) in enumerate(INTAKE_ROWS):
        made.append(_patch("G9L_Intake_%d" % k, _zv(vb), _zv(va), y_mod + 0.007, y_out, -0.0035, lib["black_panel"],
                           collection))
    # the central module: a smooth dark block, a little prouder than the panels, with the camera in its top
    made.append(_patch("G9L_Intake_Bar", z_bot, z_top, 0.0, y_mod - 0.001, -0.0025, lib["cap_black"], collection,
                       nz=6, nw=6))
    # bezel bars: down both sides of the module and along the panels' outer ends, a thin glossy line standing 7 mm off the apron
    # (the apron is a whole sheet 8 mm under the paint: anything built behind it, as the old recessed panels were, is hidden)
    for tag, y0, y1 in (("In", y_mod - 0.001, y_mod + 0.007), ("Out", y_out - 0.008, y_out)):
        made.append(_patch("G9L_Intake_Bezel_" + tag, z_bot - 0.004, z_top + 0.004, y0, y1, -0.0012, lib["black_gloss"],
                           collection, nz=6, nw=2, thickness=0.002))
    # and across the top and bottom of the field
    for tag, za, zb in (("Top", z_top, z_top + 0.007), ("Bot", z_bot - 0.007, z_bot)):
        made.append(_patch("G9L_Intake_Bezel_" + tag, za, zb, y_mod - 0.001, y_out, -0.0012, lib["black_gloss"],
                           collection, nz=2, nw=22, thickness=0.002))
    p, n = face(0.0, _zv(1990), -0.0025)
    made += _disc("G9L_Front_Camera", p, n, 0.0095, collection, lib["lamp_smoked"], 0.0015, mirror=False)
    return made


def _w_of(y, z):
    w, _v = NOSE.wv_at(abs(y), max(CAP_LOW, min(CAP_HIGH, z)))
    return min(1.0, w)


def _disc(name, p, n, r, collection, mat, h, seg=20, mirror=True):
    """A small round pad (a sensor, a camera lens) at p facing n, h tall."""
    nv = geom.Vector(n) if hasattr(geom, "Vector") else None
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
    M.orient(ob.data, lambda cc, c=tuple(c0): (cc[0] - c[0] + nv.x * 0.01, cc[1] - c[1] + nv.y * 0.01,
                                                cc[2] - c[2] + nv.z * 0.01))
    if mirror:
        M.mirror_y(ob)
    return [ob]


# --------------------------------------------------------------- headlamps
def build_headlamps(collection, lib):
    made = []
    nk = 8
    lo = _poly3(LENS_BOT, 14)
    up = _poly3(LENS_TOP, 14)
    out = geom.away_from((1.95, 0.55, 0.55))
    # the lens: a dark clear cover, slightly domed, in a recessed black bucket
    made.append(lamps.lens("G9L_Headlamp_Lens", lo, up, _place, collection, lib["lamp_clear"], nk,
                           lambda k, n: -0.004 + 0.003 * math.sin(math.pi * k / n), out,
                           thickness=0.003, bevel=(0.0010, 2, 30)))
    made += lamps.seals("G9L_Headlamp_Seal", lo, up, _place, collection, lib["black_gloss"], out,
                        width=0.007, d=-0.001, names=("Low", "Up"))
    # the lit parts: a thin DRL line high in the lens and a projector low in it
    st = list(range(1, 13))
    made.append(lamps.band_between("G9L_Headlamp_DRL", lo, up, st, (0.74, 0.77),
                                   _place, lambda k: -0.0005, collection, lib["led_white"], out))
    c, n = face(0.751, 0.52, -0.005)
    made += lamps.projector("G9L_Headlamp_Proj", c, n, 0.030, collection, lib)
    # (the black bucket the lens sat in was a 6 cm tunnel along +x: at the corner it stood out of the fender; the recessed
    # black apron behind the lens is its bucket now)
    return made


# --------------------------------------------------------------- light bar
def _bar_edges():
    top = _yz(CAM.BAR_TOP_PX)[::-1]                 # centre -> corner
    bot = _yz(CAM.BAR_BOT_PX)[::-1]
    # the photograph's bar ends at |y| 0.803-0.807, where the fender's top corner begins (the cap's seam is at y 0.80-0.81 there):
    # it used to curl on to |y| 0.915 across the seam, a bracket standing off the fender; it now closes to a short rounded tip
    top += [(0.815, 1.052)]
    bot += [(0.815, 1.016)]
    return top, bot


def build_lightbar(collection, lib):
    made = []
    top, bot = _bar_edges()
    out = geom.away_from((2.10, 0.0, 0.70))
    n = 60
    up = _poly3(top, n)
    lo = _poly3(bot, n)
    # the black housing: a little wider than the light guide
    up_h = [(p[0], p[1], p[2] + 0.008) for p in up]
    lo_h = [(p[0], p[1], p[2] - 0.008) for p in lo]
    made.append(lamps.lens("G9L_Lamp_House", lo_h, up_h, _place, collection, lib["black_gloss"], 4,
                           lambda k, nk: 0.0030 + 0.0008 * math.sin(math.pi * k / nk), out,
                           thickness=0.003, bevel=(0.0008, 2, 30)))
    made.append(lamps.lens("G9L_Lightbar", lo, up, _place, collection, lib["bar_film"], 4,
                           lambda k, nk: 0.0058 + 0.0016 * math.sin(math.pi * k / nk), out,
                           thickness=0.003, bevel=(0.0010, 2, 30)))
    return made


# ---------------------------------------------------------------- emblem
# the maker's badge on the hood's lip over the bar's middle (c1_0026, 1.5x crop): two dark chevrons
# pointing at each other, each 0.055 wide and 0.042 tall, notched on the outer side. Local
# coordinates (a outward from the centreline, b up).
_CHEV = [(0.006, 0.0), (0.061, 0.021), (0.043, 0.0), (0.061, -0.021)]


def build_emblem(collection, lib):
    from mathutils import Vector
    made = []
    p, n = face(0.0, 1.050, 0.0)
    nv = Vector(n).normalized()
    t1 = Vector((0.0, 1.0, 0.0))
    t2 = nv.cross(t1).normalized()
    for k, sgn in enumerate((1.0, -1.0)):
        verts = [tuple(Vector(p) + nv * 0.003 + t1 * (sgn * a) + t2 * b) for (a, b) in _CHEV]
        if sgn < 0:
            verts = verts[::-1]
        ob = M.obj("G9L_Emblem_%d" % k, verts, [list(range(len(verts)))], collection, lib["cap_black"])
        M.orient(ob.data, lambda cc, d=tuple(nv): d)
        M.solidify(ob, 0.002)
        made.append(ob)
    return made


# --------------------------------------------------------- plate and sensors
def build_plate(collection, lib):
    made = []
    p, n = face(0.0, 0.614, 0.0)
    made += fittings.plate("G9L_Plate_Front", tuple(p[i] + n[i] * 0.004 for i in range(3)), n,
                           collection, lib, w=0.480, h=0.148, depth=0.008,
                           texts=[("XPENG G9", 0.0, 0.038, False, True)],
                           mat="black_gloss", text_mat="machined")
    for k, (y, z) in enumerate(((0.341, 0.591), (0.644, 0.410))):
        pp, nn = face(y, z, 0.0)
        made += _disc("G9L_Sensor_F%d" % k, pp, nn, 0.0125, collection, lib["cap_black"], 0.003)
    return made


def build_charge_flap(collection, lib):
    """The rounded-square charge flap on the car's RIGHT front (y -0.419, z 0.62): a thin groove
    ring on the paint, like the photograph."""
    y0, y1 = -0.455, -0.383
    z0, z1 = 0.582, 0.660
    loop = geom.rounded_loop(y0, y1, z0, z1, 0.018, per_corner=7, closed=False)
    outer, inner = [], []
    cy, cz = 0.5 * (y0 + y1), 0.5 * (z0 + z1)
    for (y, z) in loop:
        outer.append(face(y, z, 0.0012)[0])
        k = 0.965
        inner.append(face(cy + (y - cy) * k, cz + (z - cz) * k, 0.0012)[0])
    cols = [[outer[i], inner[i]] for i in range(len(outer))]
    cols.append(cols[0])
    ob = M.mesh_from_rows("G9L_Charge_Flap_Ring", cols, collection)
    ob.data.materials.append(lib["black_gloss"])
    return [ob]


# ------------------------------------------------------------- build all
def build_all(collection, lib):
    made = []
    made += build_fascia(collection, lib)
    made += build_intake(collection, lib)
    made += build_headlamps(collection, lib)
    made += build_lightbar(collection, lib)
    made += build_emblem(collection, lib)
    made += build_plate(collection, lib)
    made += build_charge_flap(collection, lib)
    return made
