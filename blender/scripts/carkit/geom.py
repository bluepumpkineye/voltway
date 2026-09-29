"""Curves, splines, outlines and small vector maths. Pure Python, no bpy.

Everything a car's hardpoints are written in lives here: profile curves along
the car (Curve, Joined), 2D sections (catmull_rom), 3D edge polylines
(polyline), closed outlines for openings (round_rect, smooth_loop) and an
aerofoil section for wings.
"""
import math


# ------------------------------------------------------------------ scalars
def clamp01(t):
    return 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)


def smoothstep(t):
    t = clamp01(t)
    return t * t * (3.0 - 2.0 * t)


def ramp(x, x_edge, width=0.03):
    """0 behind x_edge - width/2 .. 1 ahead of x_edge + width/2, smoothstep.

    Use this instead of a step wherever a panel limit changes along the car: a
    step needs a pair of columns with different row spacings, and the sheared
    quads between them show as a line across the panel.
    """
    return smoothstep((x - (x_edge - 0.5 * width)) / width)


# ------------------------------------------------------------ profile curves
class Curve:
    """Piecewise cubic through control points.

    mode="c2"    natural cubic spline. Curvature-continuous, which is what a
                 class-A body surface needs: a highlight is an iso-curvature
                 band, so a merely-C1 profile breaks it into straight segments
                 at every control point. That was the single worst artefact in
                 the SU7's first build - the hood and front fender read as flat
                 facets with hard highlight terminators.
    mode="pchip" monotone cubic. C1 only, but cannot overshoot. Kept for
                 profiles where a bulge between control points would be worse
                 than a curvature break.
    """

    __slots__ = ("xs", "ys", "h", "m", "mode", "c")

    def __init__(self, points, mode="c2"):
        pts = sorted(points, key=lambda p: p[0])
        self.xs = [p[0] for p in pts]
        self.ys = [p[1] for p in pts]
        self.mode = mode
        n = len(pts)
        h = [self.xs[i + 1] - self.xs[i] for i in range(n - 1)]
        d = [(self.ys[i + 1] - self.ys[i]) / h[i] for i in range(n - 1)]
        self.h = h
        if mode == "c2" and n > 2:
            # natural cubic spline: solve for second derivatives
            a = [0.0] * n
            b = [1.0] * n
            cc = [0.0] * n
            r = [0.0] * n
            for i in range(1, n - 1):
                a[i] = h[i - 1]
                b[i] = 2.0 * (h[i - 1] + h[i])
                cc[i] = h[i]
                r[i] = 6.0 * (d[i] - d[i - 1])
            # Thomas algorithm
            for i in range(1, n):
                w = a[i] / b[i - 1] if b[i - 1] != 0.0 else 0.0
                b[i] -= w * cc[i - 1]
                r[i] -= w * r[i - 1]
            sig = [0.0] * n
            sig[n - 1] = r[n - 1] / b[n - 1] if b[n - 1] != 0.0 else 0.0
            for i in range(n - 2, -1, -1):
                sig[i] = (r[i] - cc[i] * sig[i + 1]) / b[i] if b[i] != 0.0 else 0.0
            self.c = sig
            self.m = None
        else:
            self.c = None
            m = [0.0] * n
            if n == 2:
                m[0] = m[1] = d[0]
            else:
                m[0], m[-1] = d[0], d[-1]
                for i in range(1, n - 1):
                    if d[i - 1] * d[i] <= 0.0:
                        m[i] = 0.0
                    else:
                        w1 = 2.0 * h[i] + h[i - 1]
                        w2 = h[i] + 2.0 * h[i - 1]
                        m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
            self.m = m

    def _span(self, x):
        xs = self.xs
        lo, hi = 0, len(xs) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if xs[mid] <= x:
                lo = mid
            else:
                hi = mid
        return lo

    def __call__(self, x):
        xs, ys = self.xs, self.ys
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        i = self._span(x)
        h = self.h[i]
        if self.c is not None:
            a = xs[i + 1] - x
            b = x - xs[i]
            s0, s1 = self.c[i], self.c[i + 1]
            return (a * ys[i] + b * ys[i + 1]) / h + \
                   ((a * a * a - h * h * a) * s0 +
                    (b * b * b - h * h * b) * s1) / (6.0 * h)
        t = (x - xs[i]) / h
        t2, t3 = t * t, t * t * t
        m = self.m
        return ((2 * t3 - 3 * t2 + 1) * ys[i]
                + (t3 - 2 * t2 + t) * h * m[i]
                + (-2 * t3 + 3 * t2) * ys[i + 1]
                + (t3 - t2) * h * m[i + 1])

    def curvature(self, x):
        """Second derivative - used by the fairness gate to find facets."""
        xs = self.xs
        if x <= xs[0] or x >= xs[-1]:
            return 0.0
        i = self._span(x)
        h = self.h[i]
        if self.c is not None:
            a = xs[i + 1] - x
            b = x - xs[i]
            return (a * self.c[i] + b * self.c[i + 1]) / h
        e = h * 1e-3
        return (self(x + e) - 2.0 * self(x) + self(x - e)) / (e * e)

    def points(self):
        """The control points, as a list of (x, y)."""
        return list(zip(self.xs, self.ys))

    def mapped(self, fx=None, fy=None):
        """A new Curve of the same mode with every control point transformed."""
        fx = fx or (lambda x: x)
        fy = fy or (lambda x, y: y)
        return Curve([(fx(x), fy(x, y)) for x, y in self.points()], mode=self.mode)


class Joined:
    """Two curves that meet at x_break with a deliberate slope break.

    The windscreen base is a crease: glass meets cowl at an angle. One C2
    spline through both slopes rings - it overshoots on either side of the
    break, which bulged the hood up behind the cowl - so each side is its own
    spline and they share only the value at the break.
    """

    __slots__ = ("xb", "left", "right")

    def __init__(self, x_break, left, right):
        self.xb, self.left, self.right = x_break, left, right

    def __call__(self, x):
        return self.left(x) if x <= self.xb else self.right(x)

    def curvature(self, x):
        return (self.left if x <= self.xb else self.right).curvature(x)

    def mapped(self, fx=None, fy=None):
        fx0 = fx or (lambda x: x)
        return Joined(fx0(self.xb), self.left.mapped(fx, fy), self.right.mapped(fx, fy))


# ---------------------------------------------------------------- 2D splines
def catmull_rom(pts, samples, alpha=0.5, dense_n=24, head=None, tail=None):
    """Centripetal Catmull-Rom through 2D control points, resampled evenly.

    Uniform (alpha = 0) Catmull-Rom takes its tangent at a point from the chord
    between its neighbours, so where the spacing is uneven - a 14 mm step above
    a shoulder followed by a 280 mm run up the tumblehome - the tangent is
    several times the length of the short segment and the curve bulges past the
    control point and comes back. Centripetal parameterisation (alpha = 0.5)
    provably produces no cusps and no self-intersections for any control
    polygon, which is exactly the guarantee a generated section needs.
    Evaluated with the Barry-Goldman pyramid.

    The curve is sampled densely and then resampled to exactly `samples + 1`
    points by arc length. Rounding a per-segment sample count instead changes
    the counts in whole steps as the section moves along the car, which slides
    every point at a given parameter by up to one sample: the surface becomes
    discontinuous and edges set at a constant parameter come out sawtoothed.

    `head` and `tail` are the phantom points beyond each end. By default the
    end points are repeated, which leaves each end's tangent free - that is
    what makes two sections meet at a crease. Passing the neighbouring
    section's point instead makes the join tangent-continuous (a soft shoulder).
    """
    if len(pts) < 2:
        return list(pts)
    ext = [pts[0] if head is None else head] + list(pts) + \
          [pts[-1] if tail is None else tail]
    segs = len(ext) - 3
    counts = [dense_n] * segs

    out = []
    for i in range(segs):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        t0 = 0.0
        t1 = t0 + max(math.hypot(p1[0] - p0[0], p1[1] - p0[1]), 1e-6) ** alpha
        t2 = t1 + max(math.hypot(p2[0] - p1[0], p2[1] - p1[1]), 1e-6) ** alpha
        t3 = t2 + max(math.hypot(p3[0] - p2[0], p3[1] - p2[1]), 1e-6) ** alpha
        n = counts[i]
        last = (i == segs - 1)
        for j in range(n + (1 if last else 0)):
            t = t1 + (t2 - t1) * (j / float(n))
            a1 = (((t1 - t) * p0[0] + (t - t0) * p1[0]) / (t1 - t0),
                  ((t1 - t) * p0[1] + (t - t0) * p1[1]) / (t1 - t0))
            a2 = (((t2 - t) * p1[0] + (t - t1) * p2[0]) / (t2 - t1),
                  ((t2 - t) * p1[1] + (t - t1) * p2[1]) / (t2 - t1))
            a3 = (((t3 - t) * p2[0] + (t - t2) * p3[0]) / (t3 - t2),
                  ((t3 - t) * p2[1] + (t - t2) * p3[1]) / (t3 - t2))
            b1 = (((t2 - t) * a1[0] + (t - t0) * a2[0]) / (t2 - t0),
                  ((t2 - t) * a1[1] + (t - t0) * a2[1]) / (t2 - t0))
            b2 = (((t3 - t) * a2[0] + (t - t1) * a3[0]) / (t3 - t1),
                  ((t3 - t) * a2[1] + (t - t1) * a3[1]) / (t3 - t1))
            out.append((((t2 - t) * b1[0] + (t - t1) * b2[0]) / (t2 - t1),
                        ((t2 - t) * b1[1] + (t - t1) * b2[1]) / (t2 - t1)))

    # uniform arc-length resample to exactly samples + 1 points
    acc = [0.0]
    for i in range(1, len(out)):
        acc.append(acc[-1] + math.hypot(out[i][0] - out[i - 1][0],
                                        out[i][1] - out[i - 1][1]))
    total = acc[-1] or 1.0
    res, j = [], 0
    for i in range(samples + 1):
        s = total * i / float(samples)
        while j < len(acc) - 2 and acc[j + 1] < s:
            j += 1
        seg = max(1e-12, acc[j + 1] - acc[j])
        f = min(1.0, max(0.0, (s - acc[j]) / seg))
        res.append((out[j][0] + (out[j + 1][0] - out[j][0]) * f,
                    out[j][1] + (out[j + 1][1] - out[j][1]) * f))
    return res


def cr_point(p0, p1, p2, p3, u, alpha=0.5):
    """Centripetal Catmull-Rom between p1 and p2 at u in [0, 1] (2D)."""
    def tj(ti, a, b):
        return ti + max(math.hypot(b[0] - a[0], b[1] - a[1]), 1e-6) ** alpha
    t0 = 0.0
    t1 = tj(t0, p0, p1)
    t2 = tj(t1, p1, p2)
    t3 = tj(t2, p2, p3)
    t = t1 + (t2 - t1) * u

    def lerp2(a, b, ta, tb):
        k = (t - ta) / (tb - ta)
        return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)
    a1 = lerp2(p0, p1, t0, t1)
    a2 = lerp2(p1, p2, t1, t2)
    a3 = lerp2(p2, p3, t2, t3)
    b1 = lerp2(a1, a2, t0, t2)
    b2 = lerp2(a2, a3, t1, t3)
    return lerp2(b1, b2, t1, t2)


def smooth_loop(pts, samples=6):
    """Closed centripetal Catmull-Rom loop through 2D control points."""
    n = len(pts)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        for j in range(samples):
            out.append(cr_point(p0, p1, p2, p3, j / float(samples)))
    return out


def round_rect(y0, y1, z0, z1, r, n=6, open_inboard=False):
    """Rounded rectangle outline in a 2D plane.

    open_inboard=True leaves the y0 side square and pushed 20 mm past the
    centreline, for an opening that is cut in a half sheet and then mirrored:
    the two halves then meet as one opening instead of two.
    """
    r = min(r, abs(y1 - y0) * 0.49, abs(z1 - z0) * 0.49)
    pts = []

    def arc(cy, cz, a0, a1):
        for i in range(n + 1):
            a = a0 + (a1 - a0) * i / float(n)
            pts.append((cy + r * math.cos(a), cz + r * math.sin(a)))

    if open_inboard:
        pts.append((y0 - 0.02, z0))
        arc(y1 - r, z0 + r, -math.pi / 2, 0.0)
        arc(y1 - r, z1 - r, 0.0, math.pi / 2)
        pts.append((y0 - 0.02, z1))
    else:
        arc(y0 + r, z0 + r, math.pi, 1.5 * math.pi)
        arc(y1 - r, z0 + r, -math.pi / 2, 0.0)
        arc(y1 - r, z1 - r, 0.0, math.pi / 2)
        arc(y0 + r, z1 - r, math.pi / 2, math.pi)
    return pts


def rounded_loop(x0, x1, z0, z1, r, per_corner=7, closed=True):
    """Rounded rectangle as a loop starting at the top-right corner, CCW.

    Used for outline rings (charge flaps, fuel doors, sensor covers).
    """
    loop = []
    for cx, cz, a0 in ((x1 - r, z1 - r, 0.0), (x0 + r, z1 - r, 0.5 * math.pi),
                       (x0 + r, z0 + r, math.pi), (x1 - r, z0 + r, 1.5 * math.pi)):
        for k in range(per_corner):
            a = a0 + 0.5 * math.pi * k / float(per_corner - 1)
            loop.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    if closed:
        loop.append(loop[0])
    return loop


# ------------------------------------------------------------- 3D polylines
def polyline(ctrl, n):
    """Resample a uniform 3D Catmull-Rom through ctrl to n points, by arc length."""
    dense = []
    m = len(ctrl)
    for i in range(m - 1):
        p0 = ctrl[max(0, i - 1)]
        p1, p2 = ctrl[i], ctrl[i + 1]
        p3 = ctrl[min(m - 1, i + 2)]
        for j in range(24):
            t = j / 24.0
            t2, t3 = t * t, t * t * t
            dense.append(tuple(
                0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t
                       + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                       + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3)
                for k in range(3)))
    dense.append(tuple(ctrl[-1]))
    acc = [0.0]
    for i in range(1, len(dense)):
        acc.append(acc[-1] + math.dist(dense[i], dense[i - 1]))
    total = acc[-1]
    out, j = [], 0
    for i in range(n):
        s = total * i / float(n - 1)
        while j < len(acc) - 2 and acc[j + 1] < s:
            j += 1
        seg = max(1e-9, acc[j + 1] - acc[j])
        t = (s - acc[j]) / seg
        out.append(tuple(dense[j][k] + (dense[j + 1][k] - dense[j][k]) * t
                         for k in range(3)))
    return out


def lerp(a, b, t):
    """Linear interpolation between two 3-tuples."""
    return tuple(a[k] + (b[k] - a[k]) * t for k in range(3))


def inset_edges(lo, up, f):
    """Two (x, z) edge lists pulled toward each other by fraction f.

    For the inner line of a frame: a vent's opening inside its bezel.
    """
    return ([(a[0], a[1] + (b[1] - a[1]) * f) for a, b in zip(lo, up)],
            [(b[0], b[1] + (a[1] - b[1]) * f) for a, b in zip(lo, up)])


# ------------------------------------------------------------------ vectors
def vadd(a, b, s=1.0):
    """a + s * b for 3-tuples."""
    return (a[0] + b[0] * s, a[1] + b[1] * s, a[2] + b[2] * s)


def vnorm(v):
    L = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / L for c in v)


def vcross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def vdot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


# ------------------------------------------------ outward-direction helpers
# Every generated sheet is oriented by an "outward" function of a face centre
# (mesh.orient). These are the common ones.
def away_from(c0):
    """Outward = away from a point inside the part."""
    return lambda c: (c[0] - c0[0], c[1] - c0[1], c[2] - c0[2])


def axial(sign):
    """Outward = along +X (nose parts) or -X (tail parts)."""
    return lambda c: (sign, 0.0, 0.0)


def radial(core_z=0.70):
    """Outward = away from the car's long axis at height core_z (flank panels)."""
    def f(c):
        ry, rz = c[1], c[2] - core_z
        L = math.hypot(ry, rz)
        return None if L < 1e-5 else (0.0, ry / L, rz / L)
    return f


def const(d):
    """Outward = one fixed direction."""
    return lambda c: d


# ------------------------------------------------------------------ aerofoil
def aerofoil(thickness=0.093, camber=0.040, camber_pos=0.40, n=22, inverted=True):
    """NACA 4-digit style section as (s, z) lists, upper then lower, s in [0, 1].

    `inverted` flips the camber so the wing pulls down, as a car's wing does.
    Points cluster at the leading and trailing edges (cosine spacing).
    """
    m, pk = camber, camber_pos
    sgn = -1.0 if inverted else 1.0
    up, lo = [], []
    for i in range(n + 1):
        s = 0.5 * (1.0 - math.cos(math.pi * i / n))
        yt = 5 * thickness * (0.2969 * math.sqrt(s) - 0.1260 * s - 0.3516 * s * s
                              + 0.2843 * s ** 3 - 0.1036 * s ** 4)
        if s < pk:
            yc = sgn * m / pk ** 2 * (2 * pk * s - s * s)
        else:
            yc = sgn * m / (1 - pk) ** 2 * ((1 - 2 * pk) + 2 * pk * s - s * s)
        up.append((s, yc + yt))
        lo.append((s, yc - yt))
    return up, lo
