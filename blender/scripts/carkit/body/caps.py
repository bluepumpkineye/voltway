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
