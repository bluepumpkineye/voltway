"""Avatr 06T front end, read from the studio front photograph c1_0002.jpg (grey car c1_0010/0011 for
the grille) through its solved camera (a06t_cam.FRONT_CAM).

What the photographs show (nothing here is invented):
    * a broad, taut painted fascia under a bonnet whose leading edge is one soft "smile" across the nose;
      the bonnet's side shut lines run back diagonally from the nose corners to the screen's corners
    * each headlamp is ONE dark glass "7" let into the nose's corner (c12_0011/0012 close-ups; rebuilt as such
      2026-11-03, the owner: "the headlight is continuous: from the edge it goes down and draws a 7"): an upper
      arm (a translucent lens in a black frame, thick at the corner, tapering to a point aimed at the badge)
      turns the corner into a stem that runs down the nose's edge and widens into a triangular pocket with two
      projector modules between ribbed fins, a light-guide down the stem's inner edge; paint fills the angle of
      the 7. Under the arm a separate long slit lamp (the DRL) with a silver rim at its outer end and lower edge
    * a black wedge grille opening under the plate: two fields of vertical slats either side of a
      V-shaped centre notch, and under it the black chin with a chrome pin-stripe that curls down at
      each outer end
    * the prism badge above the plate, a camera dot over it, parking sensors, a tow-eye cover
    * the LiDAR pod on the roof's front edge

Photo pixels are in the 3840 x 2880 originals (a06t_cam.py lists them); the left half of the picture
(the car's right) is read and mirrored.
"""
import math

import bpy
import mathutils.geometry as G
from mathutils import Vector
from mathutils.bvhtree import BVHTree

import a06t_surface as S
import a06t_nose as N
import a06t_panels as PN
import a06t_cam as CAM
import a06t_lampdata as LD
from carkit import geom
from carkit import mesh as M
from carkit import cut as C
from carkit.body import fascia as FA
from carkit.body import panels as BP
import carkit.place as P
from carkit.parts import fittings, lamps

BODY = N.BODY
NOSE = N.NOSE
C_HAIR, C_MODULES, C_LED_DOTS = CAM.POCKET_HAIR, CAM.POCKET_MODULES, CAM.POCKET_LED_DOTS
C_SLAT_DIR, C_SLAT_START, C_SLAT_PITCH, C_SLAT_N = CAM.POCKET_SLAT_DIR, CAM.POCKET_SLAT_START, CAM.POCKET_SLAT_PITCH, CAM.POCKET_SLAT_N

PLACER = P.Placer(BODY.proud)
OUT = geom.away_from((1.90, 0.45, 0.60))


# ------------------------------------------------------- photo pixels -> the nose's (|y|, z)
def _px_yz(u, v):
    """(|y|, z) of a front-photo pixel ON the nose's own surface: a ray from the camera, the plane at
    the nose's depth there, again (the nose is 0.3 m deeper at the centre than at the corners)."""
    x = 2.38
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


HOOD_EDGE = _yz_px(CAM.HOOD_EDGE_PX)               # (|y|, z), outer corner -> centre
PAINT_EDGE = _yz_px(CAM.PAINT_EDGE_PX)             # outer corner -> centre
CHIN = _yz_px(CAM.CHIN_PX)
PLATE_Z = _px_yz(0.5 * (CAM.PLATE_PX[0] + CAM.PLATE_PX[2]), 0.5 * (CAM.PLATE_PX[1] + CAM.PLATE_PX[3]))[1]


# ------------------------------------------------------------------ helpers
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
    """A thin strip along a polyline (|y|, z) on the nose, `half` metres each side in z, `depth` proud
    (negative: recessed). Mirrored."""
    pts = _resample(pts_yz, n) if n else pts_yz
    cols = [[_face(y, z - half, depth)[0], _face(y, z + half, depth)[0]] for (y, z) in pts]
    ob = M.mesh_from_rows(name, cols, collection)
    ob.data.materials.append(mat)
    M.mirror_y(ob)
    M.finish(ob, thickness=thickness, bevel=0.0)
    return ob


# ---------------------------------------------------------- bonnet edge slot
def _hood_path():
    pts, nrm = [], []
    half = [(y, z) for (y, z) in reversed(HOOD_EDGE)]                    # centre -> outer corner
    full = [(-y, z) for (y, z) in reversed(half[1:])] + half            # symmetric: flat at the centre
    path = geom.polyline([(0.0, y, z) for (y, z) in full], 140)
    path = [q for q in path if q[1] >= -1e-6]
    for (_x, y, z) in path:
        p, n = _face(y, z)
        pts.append(p)
        nrm.append(n)
    # on up the flank to the bonnet's side line (the diagonal that runs back to the screen's corner)
    y0, z0 = HOOD_EDGE[0]
    w, v = NOSE.wv_at(y0, z0)
    for k in range(1, 7):
        t = k / 6.0
        pts.append(NOSE.point(w + (1.0 - w) * t, v + (min(1.0, v + 0.02) - v) * t))
        nrm.append(NOSE.normal(w + (1.0 - w) * t, v + (min(1.0, v + 0.02) - v) * t))
    return pts, nrm


def _cut_hood_edge(ob):
    pts, nrm = _hood_path()
    c = C.slot("_hoodedge_" + ob.name, pts, nrm, PN.GAP, out=0.03, inside=0.03)
    C.difference(ob, [c], "hood_", reset_materials=True)


# ------------------------------------------------ the paint, seen through a photograph's camera
# The headlamp parts are laid on the UNCUT painted nose by casting a photograph's own rays onto it (the corner is a
# steep, wrapping surface at which a plane or a clamped height reads the stem's edge and the arm's top wrongly). The
# lamp is read on the car's RIGHT, in the close-up c12_0011 (camera "lamp11", a06t_lampdata): the ray is mirrored onto
# the left half, which is the half sheet's side (y >= 0).
FASCIA_ROWS = (N.NOSE_Z_LO + 0.0008, N.NOSE_Z_HI - 0.0008, 0.0, 1.0, 46, 50)
_PAINT = []
CAM_L = "lamp11"


def _paint_bvh():
    """BVH of the uncut painted nose (the same grid build_fascia cuts), with the grid's rows and the cap's own
    parameters, so a hit can be given the cap's smooth point and normal instead of its facet's."""
    if not _PAINT:
        rows, vs = BP.cap_rows(NOSE, *FASCIA_ROWS, top_to_centre=True)
        nw, nv = len(rows) - 1, len(rows[0])
        ws = [1.0 - (1.0 - i / float(nw)) ** 1.35 for i in range(nw + 1)]       # cap_rows' packing toward w = 1
        verts = [Vector(p) for r in rows for p in r]
        faces = [(i * nv + j, i * nv + j + 1, (i + 1) * nv + j + 1, (i + 1) * nv + j)
                 for i in range(nw) for j in range(nv - 1)]
        _PAINT.append((BVHTree.FromPolygons(verts, faces), rows, nv - 1, None, ws, vs))
    return _PAINT[0]


def _on_paint(u, v, cam=CAM_L):
    """(point, outward normal) where `cam`'s pixel (u, v), read on the car's right, meets the paint; the point is
    on the half sheet (y >= 0).

    The ray finds the grid cell; the point and normal are then the cap's own ANALYTIC surface at that cell's
    (w, v): the paint mesh is chords of it, and a glossy lens laid on the chords (or offset along a facet's
    normal) shows every cell edge as a stair-step in its reflections."""
    import a06t_ref_match as RM
    o, d = RM.ray(cam, u, v)
    o, d = Vector((o.x, -o.y, o.z)), Vector((d.x, -d.y, d.z))
    tree, rows, nvq, _c, ws, vs = _paint_bvh()
    h = tree.ray_cast(o, d)
    if h[0] is None:
        raise RuntimeError("a06t_front: the photo ray through (%g, %g) misses the nose" % (u, v))
    p = Vector(h[0])
    i, j = h[2] // nvq, h[2] % nvq
    q00, q10, q01, q11 = (Vector(rows[i][j]), Vector(rows[i + 1][j]), Vector(rows[i][j + 1]),
                          Vector(rows[i + 1][j + 1]))
    a = b = 0.5
    for _ in range(6):                               # (a, b) of the point in the cell's bilinear patch
        pa = (q10 - q00) * (1.0 - b) + (q11 - q01) * b
        pb = (q01 - q00) * (1.0 - a) + (q11 - q10) * a
        r = p - (q00 * (1 - a) * (1 - b) + q10 * a * (1 - b) + q01 * (1 - a) * b + q11 * a * b)
        m00, m01, m11 = pa.dot(pa), pa.dot(pb), pb.dot(pb)
        det = m00 * m11 - m01 * m01
        if abs(det) < 1e-18:
            break
        da, db = (m11 * pa.dot(r) - m01 * pb.dot(r)) / det, (m00 * pb.dot(r) - m01 * pa.dot(r)) / det
        a, b = min(1.0, max(0.0, a + da)), min(1.0, max(0.0, b + db))
    w = ws[i] + (ws[i + 1] - ws[i]) * a
    vv = vs[j] + (vs[j + 1] - vs[j]) * b
    # the bilinear patch is only the cell's chords: finish on the analytic surface itself (Gauss-Newton on the ray's
    # hit point), so neighbouring cells meet exactly and nothing steps at a cell edge
    h = 1.0e-4
    for _ in range(3):
        P0 = Vector(NOSE.point(w, vv))
        Pw = (Vector(NOSE.point(min(1.0, w + h), vv)) - P0) / h
        Pv = (Vector(NOSE.point(w, min(1.0, vv + h))) - P0) / h
        r = p - P0
        m00, m01, m11 = Pw.dot(Pw), Pw.dot(Pv), Pv.dot(Pv)
        det = m00 * m11 - m01 * m01
        if abs(det) < 1e-18:
            break
        dw, dv = (m11 * Pw.dot(r) - m01 * Pv.dot(r)) / det, (m00 * Pv.dot(r) - m01 * Pw.dot(r)) / det
        w, vv = min(1.0, max(0.0, w + dw)), min(1.0, max(0.0, vv + dv))
    return Vector(NOSE.point(w, vv)), Vector(NOSE.normal(w, vv))


# ------------------------------------------------ 2D outlines in photo pixels: smoothing, fills, ribbons
def _cr(P, per):
    """Centripetal Catmull-Rom through the padded points P: the spans P[1] -> P[-2], `per` samples each
    (the last point not included)."""
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        t1 = max(1e-6, math.hypot(p1[0] - p0[0], p1[1] - p0[1])) ** 0.5
        t2 = t1 + max(1e-6, math.hypot(p2[0] - p1[0], p2[1] - p1[1])) ** 0.5
        t3 = t2 + max(1e-6, math.hypot(p3[0] - p2[0], p3[1] - p2[1])) ** 0.5
        for k in range(per):
            t = t1 + (t2 - t1) * k / float(per)
            a1 = [p0[c] + (p1[c] - p0[c]) * (t / t1) for c in (0, 1)]
            a2 = [p1[c] + (p2[c] - p1[c]) * ((t - t1) / (t2 - t1)) for c in (0, 1)]
            a3 = [p2[c] + (p3[c] - p2[c]) * ((t - t2) / (t3 - t2)) for c in (0, 1)]
            b1 = [a1[c] + (a2[c] - a1[c]) * (t / t2) for c in (0, 1)]
            b2 = [a2[c] + (a3[c] - a2[c]) * ((t - t1) / (t3 - t1)) for c in (0, 1)]
            out.append((b1[0] + (b2[0] - b1[0]) * ((t - t1) / (t2 - t1)),
                        b1[1] + (b2[1] - b1[1]) * ((t - t1) / (t2 - t1))))
    return out


def _smooth_open(pts, per=6):
    pts = list(pts)
    pad = [(2 * pts[0][0] - pts[1][0], 2 * pts[0][1] - pts[1][1])] + pts + \
          [(2 * pts[-1][0] - pts[-2][0], 2 * pts[-1][1] - pts[-2][1])]
    return _cr(pad, per) + [pts[-1]]


def _smooth_loop(pts, corners=(), per=6):
    """A closed outline made smooth through its points, except at the `corners` (indices), which stay sharp."""
    pts = list(pts)
    n = len(pts)
    if not corners:
        return _cr([pts[-1]] + pts + [pts[0], pts[1]], per)
    cs = sorted(corners)
    out = []
    for a, b in zip(cs, cs[1:] + [cs[0] + n]):
        run = [pts[i % n] for i in range(a, b + 1)]
        out += _smooth_open(run, per)[:-1]
    return out


def _arc(pts, closed=False):
    seq = list(pts) + ([pts[0]] if closed else [])
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(seq, seq[1:]))


def _resample_loop(pts, step):
    n = max(8, int(round(_arc(pts, True) / step)))
    return _resample(list(pts) + [pts[0]], n + 1)[:-1]


def _area(pts):
    return 0.5 * sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))


def _grow(pts, d):
    """The outline moved `d` pixels outward along its normals."""
    sgn = 1.0 if _area(pts) > 0 else -1.0
    out, n = [], len(pts)
    for i in range(n):
        a, b = pts[i - 1], pts[(i + 1) % n]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1.0
        out.append((pts[i][0] + sgn * ty / L * d, pts[i][1] - sgn * tx / L * d))
    return out


def _inside_np(poly, px, py):
    """Even-odd test of arrays of points against a polygon."""
    import numpy as np
    x = np.array([p[0] for p in poly])
    y = np.array([p[1] for p in poly])
    x2, y2 = np.roll(x, -1), np.roll(y, -1)
    inside = np.zeros(px.shape, bool)
    for i in range(len(x)):
        if y[i] == y2[i]:
            continue
        cond = ((y[i] > py) != (y2[i] > py)) & (px < x[i] + (py - y[i]) * (x2[i] - x[i]) / (y2[i] - y[i]))
        inside ^= cond
    return inside


def _fill(poly, step):
    """Constrained Delaunay triangulation of a polygon in photo pixels: (points, triangles). The boundary is
    sampled every `step`, the inside on a hexagonal lattice kept clear of the boundary."""
    import numpy as np
    bd = _resample_loop(poly, step)
    if _area(bd) < 0.0:
        bd = bd[::-1]
    us, vs = [p[0] for p in bd], [p[1] for p in bd]
    rows = []
    rv, r = min(vs) + 0.5 * step, 0
    while rv < max(vs):
        ru = min(us) + (0.5 * step if r % 2 else 0.0)
        cols = np.arange(ru, max(us), step)
        rows.append(np.stack([cols, np.full(cols.shape, rv)], axis=1))
        rv += step * 0.866
        r += 1
    cand = np.concatenate(rows) if rows else np.zeros((0, 2))
    cand = cand[_inside_np(bd, cand[:, 0], cand[:, 1])]
    B = np.array(bd)
    if len(cand):
        keep = np.ones(len(cand), bool)
        for k in range(0, len(cand), 400):
            blk = cand[k:k + 400]
            dist = np.sqrt(((blk[:, None, :] - B[None, :, :]) ** 2).sum(axis=2)).min(axis=1)
            keep[k:k + 400] = dist > 0.72 * step
        cand = cand[keep]
    pts = [Vector(p) for p in bd] + [Vector((float(a), float(b))) for a, b in cand]
    v2, _e, f2, *_ = G.delaunay_2d_cdt(pts, [], [list(range(len(bd)))], 1, 1e-3)
    return [(p.x, p.y) for p in v2], [tuple(f) for f in f2]


def _region(name, poly, depth, mat, collection, step=18.0, thick=0.0, cam=CAM_L):
    """A sheet over a photo-pixel polygon laid on the paint, `depth` metres along its normal (negative: sunk;
    a number or a function of the pixel)."""
    pts, tris = _fill(poly, step)
    verts = []
    for (u, v) in pts:
        p, n = _on_paint(u, v, cam)
        d = depth(u, v) if callable(depth) else depth
        verts.append(tuple(p + n * d))
    ob = M.obj(name, verts, [list(t) for t in tris], collection, mat)
    M.orient(ob.data, OUT)
    if thick:
        M.solidify(ob, thick)
    M.mirror_y(ob)
    return ob


def _ribbon(name, pts_uv, half_w, depth, mat, collection, step=14.0, thick=0.0008, cam=CAM_L, smooth=True):
    """A strip `half_w` metres either side of a photo-pixel polyline, laid on the paint."""
    pts = _smooth_open(pts_uv, 6) if smooth else list(pts_uv)
    pts = _resample(pts, max(3, int(round(_arc(pts) / step)) + 1))
    hits = [_on_paint(u, v, cam) for (u, v) in pts]
    cols = []
    for i, (p, n) in enumerate(hits):
        t = hits[min(len(hits) - 1, i + 1)][0] - hits[max(0, i - 1)][0]
        t.normalize()
        side = n.cross(t)
        side.normalize()
        d = depth(*pts[i]) if callable(depth) else depth
        c = p + n * d
        hw = half_w(i / float(len(hits) - 1)) if callable(half_w) else half_w
        cols.append([tuple(c - side * hw), tuple(c + side * hw)])
    ob = M.mesh_from_rows(name, cols, collection)
    ob.data.materials.append(mat)
    M.orient(ob.data, OUT)
    if thick:
        M.solidify(ob, thick)
    M.mirror_y(ob)
    return ob


def _band(name, up_px, lo_px, nstat, nk, depth, mat, collection, thick=0.0, paired=False, frac=None, cam=CAM_L):
    """A quad band between two photo-pixel edges, laid on the paint: the shape for a thin sliver, where a
    triangulated fill makes skinny triangles that shade in a zigzag on glossy glass.

    The stations are paired by arc length, or by index (`paired`: equal-length edges built from one chain).
    `frac(t)` -> (centre, half) narrows the band to a part of the way across, as a fraction 0 = lo .. 1 = up: the
    cyan bar in its slot, with its ends rounded."""
    if paired:
        up, lo = _smooth_open(up_px, 2), _smooth_open(lo_px, 2)
        nstat = len(up)
    else:
        up = _resample(_smooth_open(up_px, 6), nstat)
        lo = _resample(_smooth_open(lo_px, 6), nstat)
    rows = []
    for i in range(nstat):
        t = i / float(nstat - 1)
        c, h = frac(t) if frac else (0.5, 0.5)
        row = []
        for k in range(nk + 1):
            f = c + h * (2.0 * k / float(nk) - 1.0)
            u, v = lo[i][0] + (up[i][0] - lo[i][0]) * f, lo[i][1] + (up[i][1] - lo[i][1]) * f
            p, n = _on_paint(u, v, cam)
            row.append(tuple(p + n * (depth(u, v) if callable(depth) else depth)))
        rows.append(row)
    ob = M.mesh_from_rows(name, rows, collection)
    ob.data.materials.append(mat)
    M.orient(ob.data, OUT)
    if thick:
        M.solidify(ob, thick)
    M.mirror_y(ob)
    return ob


def _outline_yz(px, corners, per=2):
    """(y, z) of a photo outline on the paint, for a cutting prism."""
    out = []
    for (u, v) in _smooth_loop(px, corners, per):
        p, _n = _on_paint(u, v)
        out.append((p.y, p.z))
    return out


def _mark_rims_sharp(ob, outlines, tol=0.0007):
    """Mark the edges of the cut's rim sharp. The half sheet's boundary vertices carry the rim wall's normal as well
    as the skin's: the Weighted Normal pass averaged them, and the paint beside every cut shaded as a grey smudge
    two grid cells wide. A sharp rim keeps the skin's own normal up to the edge."""
    import bmesh
    import numpy as np
    segs_a, segs_b = [], []
    for ol in outlines:
        a = np.array(ol)
        segs_a.append(a)
        segs_b.append(np.roll(a, -1, axis=0))
    A, B = np.vstack(segs_a), np.vstack(segs_b)
    AB = B - A
    den = np.maximum((AB * AB).sum(axis=1), 1e-12)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    n = 0
    for e in bm.edges:
        if len(e.link_faces) != 1:
            continue
        m = (e.verts[0].co + e.verts[1].co) * 0.5
        p = np.array([m.y, m.z])
        t = np.clip(((p - A) * AB).sum(axis=1) / den, 0.0, 1.0)
        if np.hypot(*(A + AB * t[:, None] - p).T).min() < tol:
            e.smooth = False
            n += 1
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return n


def _cut_openings(ob):
    """The headlamp "7", the slit lamp under its arm, and everything under the painted bumper edge."""
    lower = [(PAINT_EDGE[-1][0] - 0.02, PAINT_EDGE[-1][1])] + [(y, z) for (y, z) in reversed(PAINT_EDGE)]
    lower += [(PAINT_EDGE[0][0] - 0.01, 0.02), (-0.02, 0.02)]
    x0, x1 = S.HALF_L + 0.30, S.HALF_L - 0.60
    lamp = _outline_yz(LD.SIL, LD.SIL_CORNERS)
    slit = _outline_yz(LD.SLIT, LD.SLIT_CORNERS)
    cutters = [C.prism_x("_cut_lamp_" + ob.name, lamp, x0, x1),
               C.prism_x("_cut_slit_" + ob.name, slit, x0, x1),
               C.prism_x("_cut_lower_" + ob.name, lower, x0, x1)]
    sheet = C.sheet_bvh(ob)
    C.difference(ob, cutters, "front_cuts_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)
    print("lamp rims marked sharp: %d edges" % _mark_rims_sharp(ob, (lamp, slit, lower)))


# ------------------------------------------------------------------ fascia
def build_fascia(collection, lib):
    made = []
    fascia = FA.cap_panel(
        "A06T_Fascia", NOSE, collection, lib, *FASCIA_ROWS, mat="paint", top_to_centre=True,
        cuts=(_cut_openings,))
    made.append(fascia)

    # the dark apron behind every opening, recessed 2.4 cm (it shows only through the cuts); the headlamps'
    # own glass sits just behind the paint (build_lamps)
    rows, _ = BP.cap_rows(NOSE, N.NOSE_Z_LO + 0.002, 0.755, 0.0, 1.0, 20, 32, offset=-0.024)
    ap = M.mesh_from_rows("A06T_Apron", rows, collection)
    M.orient(ap.data, geom.axial(1.0))
    ap.data.materials.append(lib["black_trim"])
    M.mirror_y(ap)
    M.finish(ap, thickness=0.0025, bevel=0.0)
    made.append(ap)
    return made


# --------------------------------------------------------- grille and chin
GRILLE_TOP_Z = None


def build_grille(collection, lib):
    """Two fields of vertical slats either side of a V notch, in the black opening under the plate,
    then the chin blade with its chrome pin-stripe curling down at each outer end."""
    made = []
    y_top = PAINT_EDGE[-1][1]                                       # the opening's top edge (z)
    z_lo = N.NOSE_Z_LO + 0.050
    # dividers: thin vertical bars, a field per side (c1_0010: ~7 panels, ~75 mm pitch)
    verts, faces = [], []
    pitch, wid, dep = 0.078, 0.0035, 0.007
    for side in (1.0, -1.0):
        for i in range(8):
            y = 0.185 + pitch * i
            z_t = y_top - 0.020
            edge_y = None
            # stop where the opening's diagonal edge comes in
            for (ya, za), (yb, zb) in zip(PAINT_EDGE, PAINT_EDGE[1:]):
                if za <= z_t <= zb or zb <= z_t <= za:
                    edge_y = ya
                    break
            if edge_y is not None and y > edge_y - 0.03:
                break
            x_f = min(_face(y, z_t)[0][0], _face(y, z_lo)[0][0]) - 0.020 + dep
            x_b = x_f - dep
            k = len(verts)
            for (xx, zz) in ((x_b, z_lo), (x_f, z_lo), (x_f, z_t), (x_b, z_t)):
                verts.append((xx, side * (y - wid * 0.5), zz))
                verts.append((xx, side * (y + wid * 0.5), zz))
            faces += [[k + 0, k + 1, k + 3, k + 2], [k + 2, k + 3, k + 5, k + 4],
                      [k + 4, k + 5, k + 7, k + 6], [k + 6, k + 7, k + 1, k + 0],
                      [k + 0, k + 2, k + 4, k + 6], [k + 1, k + 7, k + 5, k + 3]]
    made.append(M.obj("A06T_Grille_Slats", verts, faces, collection, lib["black_gloss"], smooth=False))

    # the V-shaped centre notch: a smooth recessed trapezoid pointing down (the radar's cover)
    zt = y_top - 0.004
    notch = [(0.150, zt), (0.115, zt - 0.060), (0.060, zt - 0.112), (0.0, zt - 0.118)]
    rows = []
    for (y, z) in _resample(notch, 14):
        rows.append([_face(y, z, -0.012)[0], _face(y, zt, -0.012)[0]])
    nb = M.mesh_from_rows("A06T_Grille_Notch", rows, collection)
    nb.data.materials.append(lib["radar"])
    M.mirror_y(nb)
    M.finish(nb, thickness=0.0022, bevel=0.0)
    made.append(nb)

    # the chin: a satin black blade along the bumper's lower edge, a thin chrome line along it that
    # curls down at the outer end (c1_0002: the pin-stripe starts at the corner and runs to y 0.55)
    chin = [(y, z) for (y, z) in CHIN]
    made.append(_strip("A06T_Chin_Lip", [(y, z + 0.010) for (y, z) in _resample(chin, 40)], 0.0140, 0.010,
                       collection, lib["black_gloss"], thickness=0.003))
    made.append(_strip("A06T_Chin_Silver", _resample(chin, 44), 0.0021, 0.0135, collection,
                       lib["chrome"], thickness=0.0016))
    return made


# ---------------------------------------------------------------- headlamps
# Depths below are metres along the paint's normal (negative: sunk), in the close-up's own scale: 1 px of c12_0011 is
# 0.23 mm, so a 4 mm step is 18 px and the hairlines are 1.5 px wide.
def _smooth01(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _stem_inner():
    """(v, u) of the stem's inner edge, the light-guide strip's inner line, for v from the stem's top to its tip."""
    import numpy as np
    pts = [(v, u) for (u, v) in LD.GUIDE_IN if v > 800.0]
    pts.sort()
    return np.array([p[0] for p in pts]), np.array([p[1] for p in pts])


_SI = []


def _glass_depth(u, v):
    """The dark glass sits 2.2 mm behind the paint's face; the pocket (right of the stem's inner line and below the
    arm) sinks to 7.7 mm, so the projector units stand in a real recess (c12_0012: the pocket is deep)."""
    import numpy as np
    if not _SI:
        _SI.append(_stem_inner())
    vs, us = _SI[0]
    u_in = float(np.interp(v, vs, us))
    return -0.0022 - 0.0055 * _smooth01((u - u_in - 18.0) / 60.0) * _smooth01((v - 880.0) / 260.0)


def _rrect(box, k=5):
    """Closed rounded rectangle (u0, v0, u1, v1, radius), clockwise on screen; the first point repeated at the end."""
    u0, v0, u1, v1, r = box
    pts = []
    for (cx, cy, a0) in ((u1 - r, v0 + r, -90.0), (u1 - r, v1 - r, 0.0), (u0 + r, v1 - r, 90.0),
                         (u0 + r, v0 + r, 180.0)):
        for i in range(k + 1):
            a = math.radians(a0 + 90.0 * i / k)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _disc(c, r, n=14):
    return [(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _bar_frac(half, t0=0.06, t1=0.962, cap=0.075):
    """The lit bar's cross-section along the slot: a pill, `half` of the slot's height each side of its middle, with
    elliptical ends (c1_0010: the white core runs nearly the slot's length, about half its height, and ends rounded)."""
    def f(t):
        if t < t0 or t > t1:
            return (0.5, 0.0)
        e = min(1.0, (t - t0) / cap, (t1 - t) / cap)
        return (0.5, half * math.sqrt(max(0.0, 1.0 - (1.0 - e) ** 2)))
    return f


def build_lamps(collection, lib):
    """Both headlamps, laid on the uncut paint through the close-up's own rays (a06t_lampdata): the "7" (the dark
    glass, the light-guide strip that wraps its corner, the pocket's units, separators and louvres) and the slit
    lamp under its arm (glass, the lit cyan bar, the silver rim)."""
    made = []
    _PAINT.clear()
    del _SI[:]
    sil = _smooth_loop(LD.SIL, LD.SIL_CORNERS, 3)

    # ---- the "7": one sheet of dark glass over the whole outline (8 px grown, so its edge hides behind the paint)
    made.append(_region("A06T_Lamp_Glass", _grow(sil, 8.0), _glass_depth, lib["lamp_frame"], collection, step=26.0))
    # the light-guide: the arm's lens turns the corner into the stem's fluted strip (c12_0012: one prismatic piece)
    made.append(_band("A06T_Lamp_Guide", LD.GUIDE_OUT, LD.GUIDE_IN, 0, 3, -0.0016, lib["lamp_arm"], collection,
                      thick=0.0, paired=True))

    # ---- the pocket
    floor = _glass_depth
    for name, pts in C_HAIR.items():
        made.append(_ribbon("A06T_Pocket_Hair_" + name, pts, 0.00028, lambda u, v: floor(u, v) + 0.0009,
                            lib["lamp_hair"], collection, thick=0.0004, smooth=False))
    for i, m in enumerate(C_MODULES):
        made.append(_ribbon("A06T_Pocket_Housing%d" % i, _rrect(m["housing"]) + [_rrect(m["housing"])[0]], 0.0013,
                            lambda u, v: floor(u, v) + 0.0010, lib["lamp_housing"], collection, thick=0.0006))
        made.append(_ribbon("A06T_Pocket_Bezel%d" % i, _rrect(m["bezel"]) + [_rrect(m["bezel"])[0]], 0.00045,
                            lambda u, v: floor(u, v) + 0.0016, lib["lamp_hair"], collection, thick=0.0004))
        made.append(_region("A06T_Pocket_Lens%d" % i, _rrect(m["lens"]), lambda u, v: floor(u, v) + 0.0013,
                            lib["lamp_lens"], collection, step=12.0, thick=0.0006))
        for j, c in enumerate(m["dots"]):
            made.append(_region("A06T_Pocket_Dot%d_%d" % (i, j), _disc(c, 7.0), lambda u, v: floor(u, v) + 0.0019,
                                lib["lamp_lens"], collection, step=5.0))
    # the louvre slats along the pocket's upper diagonal (c12_0012: parallel blades, a bright edge on each): hairlines
    # sloping down to the right, from the stem side to just short of the diagonal edge
    import numpy as np
    dx, dy = C_SLAT_DIR
    for k in range(C_SLAT_N):
        u0, v0 = C_SLAT_START[0], C_SLAT_START[1] + C_SLAT_PITCH * k
        end, t = None, 0.0
        while t < 900.0:
            q = (u0 + dx * t, v0 + dy * t)
            if not _inside_np(sil, np.array([q[0]]), np.array([q[1]]))[0]:
                break
            end, t = q, t + 4.0
        if end is None or t < 60.0:
            continue
        end = (end[0] - dx * 18.0, end[1] - dy * 18.0)
        made.append(_ribbon("A06T_Pocket_Slat%d" % k, [(u0, v0), end], 0.00028, lambda u, v: floor(u, v) + 0.0009,
                            lib["lamp_hair"], collection, thick=0.0004, smooth=False))
    for k, (u, v) in enumerate(C_LED_DOTS):
        made.append(_region("A06T_Pocket_LedDot%d" % k, _disc((u, v), 4.5, 10), lambda u, v: floor(u, v) + 0.0016,
                            lib["lamp_lens"], collection, step=4.0))

    # ---- the slit lamp: glass, the lit cyan bar (a halo, then the white-hot core), its lit lower bevel, the rim
    made.append(_region("A06T_Slit_Glass", _grow(_smooth_loop(LD.SLIT, LD.SLIT_CORNERS, 3), 8.0), -0.0020,
                        lib["lamp_frame"], collection, step=26.0))
    made.append(_band("A06T_Slit_Halo", LD.SLIT_UP, LD.SLIT_LO, 70, 4, -0.0017, lib["led_cyan"], collection,
                      frac=_bar_frac(0.235)))
    made.append(_band("A06T_Slit_Core", LD.SLIT_UP, LD.SLIT_LO, 70, 4, -0.0014, lib["led_cyan_core"], collection,
                      frac=_bar_frac(0.125, 0.075, 0.948, 0.07)))
    glow = [(lo[0] + (up[0] - lo[0]) * 0.07, lo[1] + (up[1] - lo[1]) * 0.07)
            for up, lo in zip(_resample(_smooth_open(LD.SLIT_UP, 4), 60), _resample(_smooth_open(LD.SLIT_LO, 4), 60))][3:-2]
    made.append(_ribbon("A06T_Slit_Bevel", glow, lambda t: 0.0011 * math.sin(math.pi * (0.1 + 0.8 * t)) + 0.0002,
                        -0.0018, lib["led_cyan"], collection, thick=0.0))
    rim = _resample(_smooth_open(LD.SLIT_UP[:4][::-1] + LD.SLIT_LO, 4), 90)
    made.append(_ribbon("A06T_Slit_Rim", rim, 0.00045, -0.0006, lib["lamp_hair"], collection, thick=0.0004))
    return made


def relax_lamp_ao(ob, radius=0.045, ring=0.035):
    """Undo the baked occlusion's halo round the lamp openings. The bake darkens every skin vertex on a cut's rim (its
    normal leans into the hole) and its smoothing carries that three rings out: a 5 cm fuzzy black border, ragged
    along the grid's triangles, that the photographs do not have. Every FRONT-SKIN vertex of `ob` (the nose, modifiers
    applied, both halves) within `radius` of an opening's outline takes the average of the front-skin ring `ring`
    beyond it. (The back skin and the rim walls are hidden or dark by right and are left alone: counting them in the
    ring's average, as the first version did, pulled it down to 0.5 and left the smudge.)"""
    import numpy as np
    from mathutils.kdtree import KDTree
    pts = []
    for px, corners in ((LD.SIL, LD.SIL_CORNERS), (LD.SLIT, LD.SLIT_CORNERS)):
        for (u, v) in _resample_loop(_smooth_loop(px, corners, 2), 14.0):
            p, _n = _on_paint(u, v)
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
    bvh = _paint_bvh()[0]
    mw = ob.matrix_world
    d = np.empty(len(me.vertices))
    skin = np.zeros(len(me.vertices), bool)
    for i, v in enumerate(me.vertices):
        w = mw @ v.co
        d[i] = tree.find(w)[2]
        if d[i] < radius + ring:
            hit = bvh.find_nearest(Vector((w.x, abs(w.y), w.z)))
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


# ------------------------------------------------------------ badge, plate, bits
def _font(fn):
    import os
    d = os.path.join(os.path.dirname(bpy.app.binary_path), bpy.app.version_string.rsplit(".", 1)[0],
                     "datafiles", "fonts")
    try:
        return bpy.data.fonts.load(os.path.join(d, fn), check_existing=True)
    except Exception:
        return None


def build_emblem(collection, lib):
    """The Avatr prism badge: a tall kite with a vertical centre bar, ~35 x 42 mm."""
    y, z = _px_yz(*CAM.EMBLEM_PX)
    p, n = _face(0.0, z, 0.002)
    hw, hh, t = 0.0175, 0.021, 0.0035
    ring = [(0.0, hh), (hw, hh * 0.15), (0.0, -hh), (-hw, hh * 0.15)]
    verts, faces = [], []

    def bar(a, b, w):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        ox, oy = -dy / L * w * 0.5, dx / L * w * 0.5
        k = len(verts)
        for q in ((a[0] + ox, a[1] + oy), (b[0] + ox, b[1] + oy), (b[0] - ox, b[1] - oy), (a[0] - ox, a[1] - oy)):
            verts.append((q[0], q[1], 0.0))
        faces.append([k, k + 1, k + 2, k + 3])
    for i in range(len(ring)):
        bar(ring[i], ring[(i + 1) % len(ring)], t)
    bar(ring[0], ring[2], t * 0.8)
    ob = M.obj("A06T_Emblem", verts, faces, collection, lib["chrome"])
    M.solidify(ob, 0.0020)
    P.on_surface(ob, p, n)
    return [ob]


def build_plate(collection, lib):
    """Front show plate (480 x 140 mm) with its dark holder, the camera dot over it, the parking
    sensors and the tow-eye cover."""
    made = []
    p, n = _face(0.0, PLATE_Z, 0.004)
    p_mount = tuple(p[i] - n[i] * 0.002 for i in range(3))
    made += fittings.plate("A06T_Plate_Mount_Front", p_mount, n, collection, lib, w=0.500, h=0.158, depth=0.030,
                           mat="black_gloss", bevel=(0.003, 2, 30))
    made += fittings.plate("A06T_Plate_Front", p, n, collection, lib, w=0.480, h=0.140, depth=0.004,
                           texts=[("AVATR 06T", 0.0, 0.038, False, True)],
                           mat="black_gloss", text_mat="machined")
    y, z = _px_yz(*CAM.CAMERA_PX)
    pc, _nc = _face(0.0, z, 0.002)
    made.append(_box("A06T_Front_Camera", pc, (0.006, 0.018, 0.018), collection, lib["black_gloss"]))
    for i, (u, v) in enumerate(CAM.SENSORS_PX):
        y, z = _px_yz(u, v)
        ps, ns = _face(y, z, 0.0020)
        made += lamps.projector("A06T_Sensor_%d" % i, ps, ns, 0.0100, collection, lib,
                                mats=("lamp_bowl", "lamp_smoked"))
    u0, v0, u1, v1 = CAM.TOWCAP_PX
    y, z = _px_yz(0.5 * (u0 + u1), 0.5 * (v0 + v1))
    made.append(_tow_cap(y, z, collection, lib))
    return made


def _tow_cap(y, z, collection, lib):
    hw, hh = 0.031, 0.027
    ring = [(y + hw * math.copysign(abs(math.cos(a)) ** 0.35, math.cos(a)),
             z + hh * math.copysign(abs(math.sin(a)) ** 0.35, math.sin(a)))
            for a in [2.0 * math.pi * i / 28.0 for i in range(28)]]
    ring.append(ring[0])
    a = [_face(py, pz, 0.0006)[0] for (py, pz) in ring]
    b = [_face(py, pz, -0.0006)[0] for (py, pz) in ring]
    ob = M.strip("A06T_Tow_Cap", a, b, collection, lib["shadow"])
    M.mirror_y(ob)
    return ob


# ------------------------------------------------------------------- lidar
def build_lidar(collection, lib):
    """Huawei 896-line lidar pod on the roof's front edge: x 0.15..0.40, top 1.447 (c1_0004)."""
    cx, a, b, c = 0.275, 0.125, 0.150, 0.047
    zc = S.Z_ROOF(cx) - 0.012
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
    pod = M.obj("A06T_Lidar", verts, faces, collection, lib["black_gloss"])
    M.orient(pod.data, geom.away_from((cx, 0.0, zc - 0.02)))
    # the smoked window across its front face
    win = fittings.rounded_panel("A06T_Lidar_Window", (cx + a * 0.93, 0.0, zc + 0.020), 0.098, 0.013, 0.008,
                                 lambda q, d: ((cx + a * 0.93 + d, q[1], q[2]), (1.0, 0.0, 0.0)),
                                 cx + a * 0.93, collection, lib["lamp_smoked"], d=0.0006,
                                 outward=(1.0, 0.0, 0.0))
    return [pod, win]


def build_all(collection, lib):
    PLACER.reset()
    made = []
    made += build_fascia(collection, lib)
    made += build_grille(collection, lib)
    made += build_lamps(collection, lib)
    made += build_emblem(collection, lib)
    made += build_plate(collection, lib)
    made += build_lidar(collection, lib)
    return made
