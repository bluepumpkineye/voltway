"""Sectioned sweeps: the one primitive almost every trim part is built from.

A trim part is a 2D SECTION swept along a 3D SPINE, with the section allowed to
change along the way:

    dash          spine across the car (door to door), section in the x-z
                  plane: top pad, lip, face, vent, accent band, knee pad
    seat cushion  spine along the seat (bight -> front edge -> down the front
                  face), section across it: side, bolster crown, seam, centre
    wheel rim     closed spine (the D-shaped loop), closed elliptical section

    sw = Sweep(spine_ctrl, section_fn, s_count, t_counts, lateral=(0, 1, 0))
    sw.pts[i][j]          grid point: i along the spine, j along the section
    sw.mesh(name, col, mat, j0=..., j1=...)   a panel: a range of columns

The section is sampled per SEGMENT between consecutive control points with a
fixed count, so every control point lands on a grid column in every section.
That is what makes panels: the seat's centre panel is the columns between the
two seam control points, the bolsters the columns outside them; a seam is
where two panels meet, and piping and stitching run along those columns.
(Fixed per-segment counts are safe here because they never change along the
spine - it was COUNTS THAT VARY along the sweep that sawtoothed the SU7's body
edges.)

Frames: at each spine point T is the tangent, B the `lateral` hint made
perpendicular to T, N = T x B. A section point (a, b) goes to
spine + a*B + b*N. For a spine running +X with lateral +Y, N is +Z (up).
"""
import math

import bpy
from mathutils import Vector

from .. import geom
from .. import mesh as M


# ------------------------------------------------------------------ curves
def cr_segments(pts, counts, closed=False, alpha=0.5):
    """Centripetal Catmull-Rom through 2D (or 3D) points with a FIXED number of
    samples per segment. Open: sum(counts) + 1 points; closed: sum(counts)."""
    n = len(pts)
    dim = len(pts[0])
    segs = n if closed else n - 1
    out = []

    def P(k):
        if closed:
            return pts[k % n]
        return pts[max(0, min(n - 1, k))]

    for i in range(segs):
        p0, p1, p2, p3 = P(i - 1), P(i), P(i + 1), P(i + 2)

        def tj(ti, a, b):
            d = math.sqrt(sum((b[k] - a[k]) ** 2 for k in range(dim)))
            return ti + max(d, 1e-7) ** alpha
        t0 = 0.0
        t1 = tj(t0, p0, p1)
        t2 = tj(t1, p1, p2)
        t3 = tj(t2, p2, p3)
        c = counts[i] if isinstance(counts, (list, tuple)) else counts
        last = (not closed) and (i == segs - 1)
        for j in range(c + (1 if last else 0)):
            t = t1 + (t2 - t1) * (j / float(c))

            def lerp(a, b, ta, tb):
                if abs(tb - ta) < 1e-12:
                    return a
                k = (t - ta) / (tb - ta)
                return tuple(a[q] + (b[q] - a[q]) * k for q in range(dim))
            a1 = lerp(p0, p1, t0, t1)
            a2 = lerp(p1, p2, t1, t2)
            a3 = lerp(p2, p3, t2, t3)
            b1 = lerp(a1, a2, t0, t2)
            b2 = lerp(a2, a3, t1, t3)
            out.append(lerp(b1, b2, t1, t2))
    return out


def resample(pts, n, closed=False):
    """n points evenly spaced by arc length along a polyline (open: ends kept)."""
    P = list(pts) + ([pts[0]] if closed else [])
    acc = [0.0]
    for i in range(1, len(P)):
        acc.append(acc[-1] + math.dist(P[i], P[i - 1]))
    total = acc[-1] or 1.0
    m = n if closed else n - 1
    out, j = [], 0
    for i in range(n):
        s = total * i / float(m)
        while j < len(acc) - 2 and acc[j + 1] < s:
            j += 1
        seg = max(1e-12, acc[j + 1] - acc[j])
        f = min(1.0, max(0.0, (s - acc[j]) / seg))
        out.append(tuple(P[j][k] + (P[j + 1][k] - P[j][k]) * f for k in range(len(P[0]))))
    return out


def smooth_path(ctrl, n, closed=False):
    """A centripetal CR through 3D control points, resampled to n even points."""
    dense = cr_segments(ctrl, 24, closed=closed)
    return resample(dense, n, closed=closed)


# ------------------------------------------------------------------ sweep
class Sweep:
    def __init__(self, spine, section, s_count, t_counts, lateral=(0.0, 1.0, 0.0),
                 closed_spine=False, closed_section=False, spine_is_path=False,
                 outward=1.0):
        """spine: 3D control points (or, spine_is_path, already-sampled points).
        section(i, s) -> [(a, b), ...] control points, same count for every s;
        s runs 0..1 along the spine.

        outward: +1 or -1 so that normal() points OUT of the part. The raw grid
        normal is T x (direction of increasing section index); a section drawn
        from +B to -B across a surface whose outside is +N needs -1.
        """
        self.closed_s = closed_spine
        self.closed_t = closed_section
        self.sign = outward
        path = list(spine) if spine_is_path else smooth_path(spine, s_count + (0 if closed_spine else 1),
                                                              closed=closed_spine)
        self.spine = path
        ns = len(path)
        lat = Vector(lateral)
        self.frames = []
        for i in range(ns):
            if closed_spine:
                a, b = Vector(path[i - 1]), Vector(path[(i + 1) % ns])
            else:
                a = Vector(path[max(0, i - 1)])
                b = Vector(path[min(ns - 1, i + 1)])
            T = (b - a).normalized()
            B = (lat - T * lat.dot(T)).normalized()
            N = T.cross(B).normalized()
            self.frames.append((T, B, N))
        self.pts = []
        for i in range(ns):
            s = i / float(ns if closed_spine else ns - 1)
            ctrl = section(i, s)
            sec = cr_segments(ctrl, t_counts, closed=closed_section)
            o = Vector(path[i])
            T, B, N = self.frames[i]
            self.pts.append([tuple(o + B * a + N * b) for (a, b) in sec])
        self.nt = len(self.pts[0])
        # column index of every section control point
        cols, k = [0], 0
        tc = t_counts if isinstance(t_counts, (list, tuple)) else \
            [t_counts] * (len(section(0, 0.0)) - (0 if closed_section else 1))
        for c in tc:
            k += c
            cols.append(k)
        self.ctrl_cols = cols

    # ----------------------------------------------------------- access
    def col(self, k):
        """Grid column of section control point k."""
        return self.ctrl_cols[k]

    def normal(self, i, j):
        ns, nt = len(self.pts), self.nt
        i0, i1 = max(0, i - 1), min(ns - 1, i + 1)
        j0, j1 = max(0, j - 1), min(nt - 1, j + 1)
        if self.closed_s:
            i0, i1 = (i - 1) % ns, (i + 1) % ns
        if self.closed_t:
            j0, j1 = (j - 1) % nt, (j + 1) % nt
        a = Vector(self.pts[i1][j]) - Vector(self.pts[i0][j])
        b = Vector(self.pts[i][j1]) - Vector(self.pts[i][j0])
        n = a.cross(b) * self.sign
        return n.normalized() if n.length > 1e-12 else Vector((0, 0, 1))

    def iso_col(self, j, i0=0, i1=None, lift=0.0):
        """Points (and normals) along column j - a seam line along the spine."""
        i1 = len(self.pts) - 1 if i1 is None else i1
        pts, nrm = [], []
        for i in range(i0, i1 + 1):
            n = self.normal(i, j)
            pts.append(tuple(Vector(self.pts[i][j]) + n * lift))
            nrm.append(tuple(n))
        return pts, nrm

    def iso_row(self, i, j0=0, j1=None, lift=0.0):
        j1 = self.nt - 1 if j1 is None else j1
        pts, nrm = [], []
        for j in range(j0, j1 + 1):
            n = self.normal(i, j)
            pts.append(tuple(Vector(self.pts[i][j]) + n * lift))
            nrm.append(tuple(n))
        return pts, nrm

    def rows(self, i0=0, i1=None, j0=0, j1=None, offset=0.0):
        i1 = len(self.pts) - 1 if i1 is None else i1
        j1 = self.nt - 1 if j1 is None else j1
        out = []
        for i in range(i0, i1 + 1):
            if offset:
                out.append([tuple(Vector(self.pts[i][j]) + self.normal(i, j) * offset)
                            for j in range(j0, j1 + 1)])
            else:
                out.append([self.pts[i][j] for j in range(j0, j1 + 1)])
        return out

    def mesh(self, name, collection, mat, i0=0, i1=None, j0=0, j1=None,
             offset=0.0, flip=False, full_wrap=False):
        """A panel: grid over rows i0..i1 and columns j0..j1 (inclusive).

        full_wrap: a closed spine and/or section wraps round (tubes, rims).
        Normals follow the sweep's N side (flip for the other side).
        """
        rows = self.rows(i0, i1, j0, j1, offset)
        wrap_s = full_wrap and self.closed_s
        wrap_t = full_wrap and self.closed_t
        ob = grid_mesh(name, rows, collection, mat, wrap_s=wrap_s, wrap_t=wrap_t)
        # orient by the sweep's own normal at the panel's middle
        ic = (i0 + (len(self.pts) - 1 if i1 is None else i1)) // 2
        jc = (j0 + (self.nt - 1 if j1 is None else j1)) // 2
        n_ref = self.normal(ic, jc) * (-1.0 if flip else 1.0)
        c_ref = Vector(self.pts[ic][jc])
        _orient_to(ob, c_ref, n_ref)
        return ob


def grid_mesh(name, rows, collection, mat, wrap_s=False, wrap_t=False, smooth=True):
    """Quad mesh from rows of points, optionally wrapping in either direction."""
    ns, nt = len(rows), len(rows[0])
    verts = [p for r in rows for p in r]
    faces = []
    for i in range(ns if wrap_s else ns - 1):
        i2 = (i + 1) % ns
        for j in range(nt if wrap_t else nt - 1):
            j2 = (j + 1) % nt
            faces.append([i * nt + j, i * nt + j2, i2 * nt + j2, i2 * nt + j])
    ob = M.obj(name, verts, faces, collection, mat, smooth=smooth)
    return ob


def _orient_to(ob, c_ref, n_ref):
    """Flip so the face nearest c_ref points along n_ref."""
    me = ob.data
    best, bd = None, 1e18
    for p in me.polygons:
        d = (Vector(p.center) - c_ref).length_squared
        if d < bd:
            bd, best = d, p
    if best is not None and Vector(best.normal).dot(n_ref) < 0.0:
        me.flip_normals()
        me.update()


# ------------------------------------------------------------------ tubes
def ellipse(a, b, n=12, phase=0.0):
    return [(a * math.cos(phase + 2 * math.pi * k / n), b * math.sin(phase + 2 * math.pi * k / n))
            for k in range(n)]


def tube(name, path, profile, collection, mat, closed=False, lateral=(0.0, 0.0, 1.0),
         scale=None, cap=True):
    """Sweep a closed 2D profile along an already-sampled 3D path.

    scale(s) -> (sa, sb) scales the profile along the path (tapers).
    """
    n_prof = len(profile)
    sw = Sweep(path, lambda i, s: [(p[0] * (scale(s)[0] if scale else 1.0),
                                    p[1] * (scale(s)[1] if scale else 1.0)) for p in profile],
               len(path), 1, lateral=lateral, closed_spine=closed, closed_section=True,
               spine_is_path=True)
    rows = sw.rows()
    verts = [p for r in rows for p in r]
    nt = len(rows[0])
    ns = len(rows)
    faces = []
    for i in range(ns if closed else ns - 1):
        i2 = (i + 1) % ns
        for j in range(nt):
            j2 = (j + 1) % nt
            faces.append([i * nt + j, i * nt + j2, i2 * nt + j2, i2 * nt + j])
    if cap and not closed:
        faces.append(list(range(nt - 1, -1, -1)))
        faces.append([(ns - 1) * nt + j for j in range(nt)])
    ob = M.obj(name, verts, faces, collection, mat)
    # outward: away from the path
    me = ob.data
    score = 0.0
    for k, p in enumerate(me.polygons[:ns * nt]):
        i = min(ns - 1, k // nt)
        d = Vector(p.center) - Vector(path[i])
        score += Vector(p.normal).dot(d)
    if score < 0.0:
        me.flip_normals()
        me.update()
    return ob


# ------------------------------------------------------------- stitching
def stitches(name, path, normals, collection, mat, stitch=0.0045, gap=0.0022,
             width=0.0011, lift=0.0005, side=0.0):
    """A dashed stitch line along a surface path.

    path/normals: points on the surface and their normals (e.g. Sweep.iso_col).
    side: lateral offset from the path in metres (use +d and -d for a double
    stitch either side of a seam). Each stitch is a thin raised sliver.
    """
    P = [Vector(p) for p in path]
    Nn = [Vector(n) for n in normals]
    acc = [0.0]
    for k in range(1, len(P)):
        acc.append(acc[-1] + (P[k] - P[k - 1]).length)
    total = acc[-1]

    def at(s):
        j = 0
        while j < len(acc) - 2 and acc[j + 1] < s:
            j += 1
        seg = max(1e-9, acc[j + 1] - acc[j])
        f = min(1.0, max(0.0, (s - acc[j]) / seg))
        p = P[j].lerp(P[j + 1], f)
        n = Nn[j].lerp(Nn[j + 1], f).normalized()
        t = (P[j + 1] - P[j]).normalized()
        return p, n, t

    verts, faces = [], []
    s = 0.5 * gap
    while s + stitch <= total:
        pa, na, ta = at(s)
        pb, nb, tb = at(s + stitch)
        sa = ta.cross(na).normalized()
        sb = tb.cross(nb).normalized()
        a = pa + sa * side + na * lift
        b = pb + sb * side + nb * lift
        w = 0.5 * width
        base = len(verts)
        verts += [tuple(a - sa * w), tuple(b - sb * w), tuple(b + sb * w), tuple(a + sa * w),
                  tuple(0.5 * (a + b) + na * (lift * 0.8))]
        faces += [[base, base + 1, base + 4], [base + 1, base + 2, base + 4],
                  [base + 2, base + 3, base + 4], [base + 3, base, base + 4]]
        s += stitch + gap
    ob = M.obj(name, verts, faces, collection, mat, smooth=False)
    return ob


def piping(name, path, collection, mat, r=0.0022, n=6, lateral=(0.0, 0.0, 1.0)):
    """A welt cord along a seam: a thin tube."""
    return tube(name, path, ellipse(r, r, n), collection, mat, lateral=lateral)
