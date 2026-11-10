"""Parts laid on a body through a photograph's own rays.

A lamp, a vent or a badge read off a photograph is a 2D outline in the photo's pixels. Putting it on the model by eye
(a plane, a clamped height) is wrong wherever the surface wraps, so each outline point is sent along the photo's own
ray (carkit.qa.refmatch.ray of the solved camera) and laid where it meets the body. `Lay` does that with any
`hit(u, v) -> (point, outward normal)` a car supplies; the outlines themselves are smoothed, filled and offset here.

    lay = photolay.Lay(hit, outward)
    lay.region(name, outline_px, depth, material, collection)       # a sheet over an outline (a lens, a plate)
    lay.ribbon(name, polyline_px, half_width, depth, material, collection)   # a strip along a line (a bezel, a hairline)
    lay.band(name, edge_a_px, edge_b_px, stations, nk, depth, material, collection)   # a quad band between two edges

Depths are metres along the surface normal (negative: sunk). Everything is laid on the car's half sheet (y >= 0) and
mirrored: `hit` is expected to return half-sheet points (mirror the photo's pixel/ray yourself).

First used for the Avatr 06T's headlamp (a06t_front keeps its own copy of these helpers) and the Nio ES8's.
"""
import math

import bpy
import mathutils.geometry as G
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from carkit import mesh as M


# ------------------------------------------------ 2D outlines in photo pixels: smoothing, fills
def resample(pts, n):
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


def smooth_open(pts, per=6):
    pts = list(pts)
    pad = [(2 * pts[0][0] - pts[1][0], 2 * pts[0][1] - pts[1][1])] + pts + \
          [(2 * pts[-1][0] - pts[-2][0], 2 * pts[-1][1] - pts[-2][1])]
    return _cr(pad, per) + [pts[-1]]


def smooth_loop(pts, corners=(), per=6):
    """A closed outline made smooth through its points, except at the `corners` (indices), which stay sharp."""
    pts = list(pts)
    n = len(pts)
    if not corners:
        return _cr([pts[-1]] + pts + [pts[0], pts[1]], per)
    cs = sorted(corners)
    out = []
    for a, b in zip(cs, cs[1:] + [cs[0] + n]):
        run = [pts[i % n] for i in range(a, b + 1)]
        out += smooth_open(run, per)[:-1]
    return out


def arc(pts, closed=False):
    seq = list(pts) + ([pts[0]] if closed else [])
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(seq, seq[1:]))


def resample_loop(pts, step):
    n = max(8, int(round(arc(pts, True) / step)))
    return resample(list(pts) + [pts[0]], n + 1)[:-1]


def area(pts):
    return 0.5 * sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))


def grow(pts, d):
    """The outline moved `d` pixels outward along its normals."""
    sgn = 1.0 if area(pts) > 0 else -1.0
    out, n = [], len(pts)
    for i in range(n):
        a, b = pts[i - 1], pts[(i + 1) % n]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1.0
        out.append((pts[i][0] + sgn * ty / L * d, pts[i][1] - sgn * tx / L * d))
    return out


def inside_np(poly, px, py):
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


def fill(poly, step):
    """Constrained Delaunay triangulation of a polygon in photo pixels: (points, triangles). The boundary is
    sampled every `step`, the inside on a hexagonal lattice kept clear of the boundary."""
    import numpy as np
    bd = resample_loop(poly, step)
    if area(bd) < 0.0:
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
    cand = cand[inside_np(bd, cand[:, 0], cand[:, 1])]
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


# ------------------------------------------------------------------------------------------------ the surface
class Surf:
    """BVH of named half-sheet objects' BASE meshes (the car's y >= 0 side, as they stand after any smoothing), with smooth
    vertex normals (area-weighted, oriented away from `inside`), for the photo's rays. `hit` returns (point, outward normal)
    or, for a ray that meets no sheet, the closest approach along the ray (see `hit`)."""

    def __init__(self, names, inside=(1.2, 0.0, 0.6), x_range=(2.50, 1.60)):
        self.x_range = x_range
        _INSIDE = Vector(inside)
        verts, tris, norms = [], [], []
        for nm in names:
            ob = bpy.data.objects[nm]
            me = ob.data
            me.calc_loop_triangles()
            mw = ob.matrix_world
            base = len(verts)
            wv = [mw @ v.co for v in me.vertices]
            acc = [Vector() for _ in wv]
            for poly in me.polygons:
                n = (mw.to_3x3() @ poly.normal) * poly.area
                for i in poly.vertices:
                    acc[i] += n
            out = sum(a.dot(w - _INSIDE) for a, w in zip(acc, wv))
            k = 1.0 if out >= 0.0 else -1.0
            for a in acc:
                if a.length > 0.0:
                    a.normalize()
            verts += wv
            norms += [a * k for a in acc]
            tris += [(base + t.vertices[0], base + t.vertices[1], base + t.vertices[2]) for t in me.loop_triangles]
        self.verts, self.tris, self.norms = verts, tris, norms
        self.misses = 0
        self.tree = BVHTree.FromPolygons(verts, tris)

    def hit(self, o, d, inset=0.0):
        """The first panel the ray meets; a ray that passes through a shut line's gap or just outside the sheets' edge
        (the nose's corner turns up to 2 cm earlier than the photographed car's) takes the nearest point of the
        surface instead, `inset` metres inboard (a cut along a sheet's very edge would tear it)."""
        h = self.tree.ray_cast(o, d)
        missed = h[0] is None
        if missed:
            # where the ray passes closest to the surface (a ray that skims a wall that is a few cm too narrow, as at
            # the DRL's outer end, is carried to the wall where it is widest, not pinned at one x)
            best = None
            for k in range(36):
                x = self.x_range[0] + (self.x_range[1] - self.x_range[0]) * k / 35.0
                f = self.tree.find_nearest(o + d * ((o.x - x) / max(-d.x, 1e-6)))
                if f[0] is not None and (best is None or f[3] < best[3]):
                    best = f
            if best is None:
                return None
            h = best
        p = Vector(h[0])
        if missed:
            p.y -= inset
        a, b, c = (self.verts[i] for i in self.tris[h[2]])
        v0, v1, v2 = b - a, c - a, p - a
        d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
        den = d00 * d11 - d01 * d01 or 1e-18
        wb, wc = (d11 * d20 - d01 * d21) / den, (d00 * d21 - d01 * d20) / den
        wb, wc = min(1.0, max(0.0, wb)), min(1.0, max(0.0, wc))
        na, nb, nc = (self.norms[i] for i in self.tris[h[2]])
        n = na * (1.0 - wb - wc) + nb * wb + nc * wc
        n.normalize()
        self.misses += int(missed)
        return p, n


# ------------------------------------------------------------------------------------------------ laying
class Lay:
    """`hit(u, v)` -> (Vector point, Vector outward normal) of the body under photo pixel (u, v), on the half sheet;
    `outward` orients new faces (a function of a face centre, see carkit.mesh.orient)."""

    def __init__(self, hit, outward):
        self.hit = hit
        self.outward = outward

    def _dep(self, depth, u, v):
        return depth(u, v) if callable(depth) else depth

    def region(self, name, poly, depth, mat, collection, step=18.0, thick=0.0, bevel=0.0):
        """A sheet over a photo-pixel polygon laid on the body, `depth` metres along its normal (a number or a
        function of the pixel). `thick` solidifies it inward; `bevel` rounds its edge."""
        pts, tris = fill(poly, step)
        verts = []
        for (u, v) in pts:
            p, n = self.hit(u, v)
            verts.append(tuple(p + n * self._dep(depth, u, v)))
        ob = M.obj(name, verts, [list(t) for t in tris], collection, mat)
        M.orient(ob.data, self.outward)
        if thick:
            M.solidify(ob, thick)
        if bevel:
            M.bevel(ob, bevel, 2, 50.0)
        M.mirror_y(ob)
        return ob

    def ribbon(self, name, pts_uv, half_w, depth, mat, collection, step=14.0, thick=0.0008, smooth=True, closed=False):
        """A strip `half_w` metres either side of a photo-pixel polyline, laid on the body (`closed`: a ring)."""
        if closed:
            pts = smooth_loop(pts_uv, (), 4) if smooth else list(pts_uv)
            pts = pts + [pts[0]]
        else:
            pts = smooth_open(pts_uv, 6) if smooth else list(pts_uv)
        pts = resample(pts, max(3, int(round(arc(pts) / step)) + 1))
        hits = [self.hit(u, v) for (u, v) in pts]
        cols = []
        for i, (p, n) in enumerate(hits):
            t = hits[min(len(hits) - 1, i + 1)][0] - hits[max(0, i - 1)][0]
            t.normalize()
            side = n.cross(t)
            side.normalize()
            c = p + n * self._dep(depth, *pts[i])
            hw = half_w(i / float(len(hits) - 1)) if callable(half_w) else half_w
            cols.append([tuple(c - side * hw), tuple(c + side * hw)])
        ob = M.mesh_from_rows(name, cols, collection)
        ob.data.materials.append(mat)
        M.orient(ob.data, self.outward)
        if thick:
            M.solidify(ob, thick)
        M.mirror_y(ob)
        return ob

    def band(self, name, up_px, lo_px, nstat, nk, depth, mat, collection, thick=0.0, paired=False, frac=None):
        """A quad band between two photo-pixel edges: the shape for a thin sliver, where a triangulated fill
        makes skinny triangles that shade in a zigzag on glossy glass. The stations are paired by arc length, or by
        index (`paired`). `frac(t)` -> (centre, half) narrows the band to a part of the way across (0 = lo .. 1 = up)."""
        if paired:
            up, lo = smooth_open(up_px, 2), smooth_open(lo_px, 2)
            nstat = len(up)
        else:
            up = resample(smooth_open(up_px, 6), nstat)
            lo = resample(smooth_open(lo_px, 6), nstat)
        rows = []
        for i in range(nstat):
            t = i / float(nstat - 1)
            c, h = frac(t) if frac else (0.5, 0.5)
            row = []
            for k in range(nk + 1):
                f = c + h * (2.0 * k / float(nk) - 1.0)
                u, v = lo[i][0] + (up[i][0] - lo[i][0]) * f, lo[i][1] + (up[i][1] - lo[i][1]) * f
                p, n = self.hit(u, v)
                row.append(tuple(p + n * self._dep(depth, u, v)))
            rows.append(row)
        ob = M.mesh_from_rows(name, rows, collection)
        ob.data.materials.append(mat)
        M.orient(ob.data, self.outward)
        if thick:
            M.solidify(ob, thick)
        M.mirror_y(ob)
        return ob
