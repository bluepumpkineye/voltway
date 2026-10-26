"""Wrapped nose and tail caps, parameterised by (w, v).

A nose cannot be an x-loft: it is multi-valued in x (the bumper at z = 0.40 is
behind the bumper at z = 0.60), so a surface parameterised by station x ends
the car in a flat plate, and every front part becomes a box bolted onto it.
Each end is its own patch instead:

    C(w, v)   v = the flank's section parameter, carried round the end
              w = 0 at the centreline, 1 at the shut line where the cap
                  meets the flank (the JOIN curve, x as a function of v)

Four curves describe an end:

    join      x of the cap/flank shut line as a function of v
    x_of_z    the centreline profile: how far forward (or back) the end
              reaches at each height - its peak is the car's extreme
    z_lo/z_hi height range of that profile
    wrap      plan-view roundness g(w): 0 at the centre, 1 at the join;
              flat across the face and turning hard near w = 1

Height is blended so the cap LEAVES THE JOIN ALONG THE FLANK'S OWN SLOPE:
z = zj + s.dx.u + (zt - zj - s.dx).u^2, with u = 1 - g. The first two terms
are the flank's tangent line and the correction is second order at the join,
so the two surfaces meet G1. A blend that ignores the flank's slope arrived at
the join up to 16 degrees off the fender on the SU7, and the zebra render
showed it as a crease ring round the nose.
"""
import math


class WrapCap:
    """One end of the car. `front` True for the nose, False for the tail."""

    def __init__(self, loft, *, front, join, x_of_z, z_lo, z_hi, wrap,
                 inside_offset=0.66, inside_z=0.58, name=None, slope_cache=None):
        self.loft = loft
        self.front = front
        self.JOIN = join
        self.X_OF_Z = x_of_z
        self.Z_LO, self.Z_HI = z_lo, z_hi
        self.WRAP = wrap
        self.name = name or ("nose" if front else "tail")
        # a point well inside the end, for orienting normals outward
        self.inside = (loft.HALF_L - inside_offset if front else -loft.HALF_L + inside_offset,
                       0.0, inside_z)
        self._z_range = None
        self._runmax = None
        # Nose and tail may share one slope cache (keyed by end), which is how
        # the SU7 was built. The cache is keyed on v rounded to 1e-5 but holds
        # the slope at the first v seen, so values depend on call order by up
        # to ~0.04 mm; sharing keeps builds bit-identical to the original.
        self._slope = {} if slope_cache is None else slope_cache

    # ------------------------------------------------------------ the ring
    def join_z_range(self):
        """(lowest, highest) height anywhere on the join ring.

        The highest point is NOT the ring's end at v = 1. Over a hood with twin
        fender crowns the ring rises to a crown and dips to the centreline.
        Taking the end as the top made the remap saturate at the crown, and the
        whole top of the SU7's nose between crown and centreline was unbuilt.
        """
        if self._z_range is None:
            S, j = self.loft, self.JOIN
            zs = [S.section_v(j(k / 200.0), k / 200.0)[1] for k in range(201)]
            self._z_range = (min(zs), max(max(zs), min(zs) + 1e-4))
        return self._z_range

    def t_of_v(self, v):
        """Monotone height fraction of the join ring at v (running maximum)."""
        tab = self._runmax
        if tab is None:
            S, j = self.loft, self.JOIN
            zl, zh = self.join_z_range()
            tab, best = [], -1.0
            for k in range(401):
                vv = k / 400.0
                z = S.section_v(j(vv), vv)[1]
                best = max(best, (z - zl) / (zh - zl))
                tab.append(min(1.0, max(0.0, best)))
            self._runmax = tab
        f = min(1.0, max(0.0, v)) * 400.0
        i = min(399, int(f))
        return tab[i] + (tab[i + 1] - tab[i]) * (f - i)

    def wrap(self, w):
        return min(1.0, max(0.0, self.WRAP(min(1.0, max(0.0, w)))))

    def tip_at(self, v):
        """Terminal centreline point for section parameter v, as (x, z)."""
        t = self.t_of_v(v)
        zt = self.Z_LO + t * (self.Z_HI - self.Z_LO)
        return (self.X_OF_Z(zt), zt)

    def flank_slope(self, v):
        """dz/dx of the flank at constant v, right at the join."""
        key = (self.front, round(v, 5))
        s = self._slope.get(key)
        if s is None:
            S = self.loft
            xj = self.JOIN(v)
            h = 0.010
            s = (S.section_v(xj + h, v)[1] - S.section_v(xj - h, v)[1]) / (2.0 * h)
            if len(self._slope) > 20000:
                self._slope.clear()
            self._slope[key] = s
        return s

    # ------------------------------------------------------------ surface
    def point(self, w, v):
        """A point on the half cap, y >= 0."""
        xj = self.JOIN(v)
        yj, zj = self.loft.section_v(xj, v)
        xt, zt = self.tip_at(v)
        g = self.wrap(w)
        u = 1.0 - g
        s = self.flank_slope(v)
        dx = xt - xj
        z = zj + s * dx * u + (zt - zj - s * dx) * u * u
        return (xt + (xj - xt) * g, yj * w, z)

    def normal(self, w, v, h=2.5e-3):
        """Outward unit normal, by central difference on the patch."""
        w0, w1 = max(0.0, w - h), min(1.0, w + h)
        v0, v1 = max(0.0, v - h), min(1.0, v + h)
        pw0, pw1 = self.point(w0, v), self.point(w1, v)
        pv0, pv1 = self.point(w, v0), self.point(w, v1)
        a = [pw1[i] - pw0[i] for i in range(3)]
        b = [pv1[i] - pv0[i] for i in range(3)]
        n = [a[1] * b[2] - a[2] * b[1],
             a[2] * b[0] - a[0] * b[2],
             a[0] * b[1] - a[1] * b[0]]
        L = math.sqrt(sum(c * c for c in n))
        if L < 1e-9:
            return (1.0 if self.front else -1.0, 0.0, 0.0)
        n = [c / L for c in n]
        p = self.point(w, v)
        d = [p[i] - self.inside[i] for i in range(3)]
        if sum(n[i] * d[i] for i in range(3)) < 0.0:
            n = [-c for c in n]
        return tuple(n)

    def offset(self, w, v, dist):
        p = self.point(w, v)
        n = self.normal(w, v)
        return tuple(p[i] + n[i] * dist for i in range(3))

    # ------------------------------------------------------------ lookups
    def v_at_z(self, z, w=0.0, iters=30):
        """Section parameter whose cap point sits at height z, at a given w."""
        a, b = 0.0, 1.0
        for _ in range(iters):
            m = 0.5 * (a + b)
            if self.point(w, m)[2] < z:
                a = m
            else:
                b = m
        return 0.5 * (a + b)

    def wv_at(self, y, z, passes=5):
        """The (w, v) whose cap point sits at elevation position (y, z)."""
        w, v = 0.0, self.v_at_z(z, 0.0)
        for _ in range(passes):
            v = self.v_at_z(z, w)
            yj = self.loft.section_v(self.JOIN(v), v)[0]
            w = 0.0 if yj <= 1e-6 else min(1.0, max(0.0, abs(y) / yj))
        return (w, v)

    def wv_at_xz(self, x, z, w=0.95, iters=8):
        """The (w, v) whose cap point has this x and z (2D Newton), for side
        placement round the corner of the end."""
        v = self.v_at_z(z, w)
        for _ in range(iters):
            p = self.point(w, v)
            fx, fz = p[0] - x, p[2] - z
            if abs(fx) < 2e-5 and abs(fz) < 2e-5:
                break
            h = 1e-4
            pw = self.point(min(1.0, w + h), v)
            pv = self.point(w, min(1.0, v + h))
            a11, a21 = (pw[0] - p[0]) / h, (pw[2] - p[2]) / h
            a12, a22 = (pv[0] - p[0]) / h, (pv[2] - p[2]) / h
            det = a11 * a22 - a12 * a21
            if abs(det) < 1e-12:
                break
            dw = (a22 * fx - a12 * fz) / det
            dv = (-a21 * fx + a11 * fz) / det
            w = min(1.0, max(0.0, w - dw))
            v = min(1.0, max(0.0, v - dv))
        return w, v

    def x_at(self, y, z):
        """Depth of the cap surface at an elevation position (y, z).

        Place detail parts with this instead of at a constant x - a lens on a
        plane floats at the centre and sinks into the body at the corners.
        """
        w, v = self.wv_at(y, z)
        return self.point(w, v)[0]

    def half_width(self, z):
        """Half-width of the cap's silhouette at height z."""
        v = self.v_at_z(z, 1.0)
        return abs(self.loft.section_v(self.JOIN(v), v)[0])


class WrapCapG1(WrapCap):
    """A WrapCap that meets the flank G1 at EVERY height, by construction.

    WrapCap blends one fixed plan-view curve g(w) into every v, so the cap leaves the join at the
    same plan angle everywhere. Where the flank's own direction differs (the fender crown at a nose,
    the sail at a tail) the two surfaces break by 10-20 degrees: the pinch at a hood's front corner.

    Here, for each v, the plan outline from the centreline tip to the join is a cubic Bezier:

        P0 = (xt, 0)                  the tip; the face runs flat across the centre
        P1 = (xt, k1 * yj)            how long the face stays flat before the corner turns
        P2 = join + k2 * dx * dir     the corner's other handle, along the flank's own direction
        P3 = (xj, yj)                 the join

    `dir` is the car's x axis projected onto the flank's tangent plane at the join (its outward
    normal, smoothed over v), so the cap's leaving direction lies IN that plane: G1 whatever the
    flank's section does there. Height blends as WrapCap's does (the flank's own z-slope at the
    join, a quadratic to the tip), with u = 1 - g and g the fraction of the plan's x travel.
    y stays y = yj * w, so every lookup that inverts it (wv_at, x_at, half_width) keeps working.

    k1, k2: floats or callables of v. A larger k1 keeps the face flatter, a larger k2 squares the
    corner (k1 0.75-0.85 and k2 0.5-0.6 give a corner radius of about the cap's forward reach).
    """

    def __init__(self, loft, *, front, join, x_of_z, z_lo, z_hi, k1=0.78, k2=0.55, smooth=0.012,
                 inside_offset=0.66, inside_z=0.58, name=None, slope_cache=None):
        WrapCap.__init__(self, loft, front=front, join=join, x_of_z=x_of_z, z_lo=z_lo, z_hi=z_hi,
                         wrap=lambda w: w, inside_offset=inside_offset, inside_z=inside_z,
                         name=name, slope_cache=slope_cache)
        self._k1, self._k2 = k1, k2
        self._smooth = smooth
        self._sgn = 1.0 if front else -1.0
        self._rings = {}

    @staticmethod
    def _k(k, v):
        return float(k(v)) if callable(k) else float(k)

    def ring(self, v):
        """Everything the cap needs at section parameter v, cached."""
        key = round(v, 6)
        r = self._rings.get(key)
        if r is not None:
            return r
        S = self.loft
        xj = self.JOIN(v)
        yj, zj = S.section_v(xj, v)
        xt, zt = self.tip_at(v)
        # the flank's outward normal at the ring, smoothed over v (the section is a polyline: its
        # normals are facets a few tenths of a degree apart)
        d = self._smooth
        acc = [0.0, 0.0, 0.0]
        for vv, wt in ((max(0.0, v - d), 1.0), (v, 2.0), (min(1.0, v + d), 1.0)):
            n = S.surface_normal(self.JOIN(vv), vv)
            for i in range(3):
                acc[i] += n[i] * wt
        L = math.sqrt(sum(c * c for c in acc)) or 1.0
        nx, ny, nz = (c / L for c in acc)
        den = max(1e-3, 1.0 - nx * nx)
        r_y = -nx * ny / den                       # plan slope dy/dx of the forward direction on the plane
        s = -nx * nz / den                         # its dz/dx
        sgn = self._sgn
        if r_y * sgn > 0.0:                        # widening toward the end: keep y monotone in w
            r_y = 0.0
        dxt = xt - xj
        L2 = self._k(self._k2, v) * abs(dxt)
        x2 = xj + sgn * L2
        y2 = max(0.25 * yj, yj + r_y * sgn * L2)
        k1 = min(self._k(self._k1, v) * yj, y2 - 0.02 * yj)
        r = dict(xj=xj, yj=yj, zj=zj, xt=xt, zt=zt, s=s, dx=dxt, x2=x2, y2=y2, k1=max(0.0, k1))
        if len(self._rings) > 20000:
            self._rings.clear()
        self._rings[key] = r
        return r

    def plan(self, r, w):
        """(x, g) of the plan outline at w: x along the Bezier, g the fraction of the travel from the
        tip (0) to the join (1)."""
        yj = r["yj"]
        if abs(r["dx"]) < 1e-6 or yj < 1e-6:
            g = w ** 8
            return r["xt"] + (r["xj"] - r["xt"]) * g, g
        target = yj * w
        y1, y2 = r["k1"], r["y2"]
        lo, hi = 0.0, 1.0
        t = w
        for _ in range(7):                         # Newton from t = w, bisection as the safety net
            m = 1.0 - t
            y = 3.0 * m * m * t * y1 + 3.0 * m * t * t * y2 + t * t * t * yj
            dy = (3.0 * m * m * y1 + 6.0 * m * t * (y2 - y1) + 3.0 * t * t * (yj - y2))
            if y < target:
                lo = t
            else:
                hi = t
            if abs(y - target) < 1e-7:
                break
            tn = t - (y - target) / dy if dy > 1e-9 else 0.5 * (lo + hi)
            t = tn if lo < tn < hi else 0.5 * (lo + hi)
        for _ in range(30):                        # polish: bisection to 1e-9 of y when Newton stalled
            m = 1.0 - t
            y = 3.0 * m * m * t * y1 + 3.0 * m * t * t * y2 + t * t * t * yj
            if abs(y - target) < 1e-8:
                break
            if y < target:
                lo = t
            else:
                hi = t
            t = 0.5 * (lo + hi)
        m = 1.0 - t
        xt, x2, xj = r["xt"], r["x2"], r["xj"]
        x = xt * (m * m * m + 3.0 * m * m * t) + x2 * 3.0 * m * t * t + xj * t * t * t
        g = (x - xt) / (xj - xt)
        return x, min(1.0, max(0.0, g))

    def point(self, w, v):
        r = self.ring(v)
        if w >= 1.0:
            return (r["xj"], r["yj"], r["zj"])
        w = max(0.0, w)
        x, g = self.plan(r, w)
        u = 1.0 - g
        dx = r["dx"]
        z = r["zj"] + r["s"] * dx * u + (r["zt"] - r["zj"] - r["s"] * dx) * u * u
        return (x, r["yj"] * w, z)
