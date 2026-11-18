"""XPeng Mona L05 nose and tail caps - WrapCap and G1-continuous TaperedWrapCap.

    C(w, v)     v = the body loft's section parameter
                w = 1 at the shut line where the cap meets the loft, 0 on the centreline
"""
import math
from mathutils import Vector
import mona_surface as S
from carkit.geom import Curve
from carkit.body import WrapCap, CarBody

# ---------------------------------------------------------------- shut lines
# Hood front U-edge / side shut line (single source of truth shared with mona_panels.Y_HOOD).
Y_HOOD = Curve([
    (0.853, 0.813), (1.167, 0.794), (1.402, 0.765), (1.649, 0.732),
    (1.880, 0.695), (2.060, 0.655), (2.170, 0.610), (2.250, 0.545),
    (2.305, 0.460), (2.340, 0.340), (2.358, 0.180), (2.365, 0.000),
], mode="pchip")

_HOOD_CORNER_X = 2.250
_V_CORNER = S.BODY.v_at_y_upper(_HOOD_CORNER_X, Y_HOOD(_HOOD_CORNER_X))


def _solve_hood_join_pts():
    pts = []
    for v in (0.71, 0.74, 0.78, 0.82, 0.86, 0.90, 0.94, 0.97, 1.00):
        if v <= _V_CORNER:
            continue
        if v >= 0.999:
            pts.append((1.00, 2.365))
            continue
        lo, hi = _HOOD_CORNER_X, 2.365
        for _ in range(30):
            mid = 0.5 * (lo + hi)
            if S.BODY.section_v(mid, v)[0] < Y_HOOD(mid):
                lo = mid
            else:
                hi = mid
        pts.append((v, 0.5 * (lo + hi)))
    return pts


# Front fender-to-fascia and hood-front shut line (+140 mm overhang: x_front = 2.575, arch ends ~2.020):
JOIN_F = Curve([
    (0.00, 2.135),
    (0.28, 2.138),
    (0.32, 2.142),   # sill/lip corner (~12 cm ahead of front wheel arch cladding)
    (0.40, 2.185),
    (0.52, 2.255),   # V_SHOULDER: outer headlight apex corner
    (0.60, 2.248),
    (_V_CORNER, _HOOD_CORNER_X),
] + _solve_hood_join_pts(), mode="pchip")

# Rear: behind the rear wheel arch + cladding (REAR_AXLE - 0.532 = -2.007 m),
# rising behind the tail-lamp flank tip to the backlight's foot at x -2.400.
JOIN_R = Curve([
    (0.00, -2.230),
    (0.12, -2.164),
    (0.24, -2.092),
    (0.36, -2.047),
    (0.46, -2.035),
    (0.56, -2.051),
    (0.68, -2.102),
    (0.80, -2.178),
    (0.90, -2.254),
    (0.96, -2.297),
    (1.00, -2.316),
])

# ------------------------------------------- centreline profiles, x given z
# Nose from the side silhouette (c1_0004): chin splitter at z 0.275, recessed lower grille,
# proud painted nose face at x 2.525 (z 0.52..0.79), rolling back to the nose channel at z 0.892.
# 2026-11-17 (owner: the face reads flat and vertical, wants a "shark nose"): the old profile peaked at z 0.56 because the
# Autohome plate sign sticks out 14 cm at z 0.50-0.63 and was read as the nose. Without it (c1_0003) the apex is at the
# badge / blade height (z 0.76), the upper nose rolls back into the bonnet, and the lower face leans back to the chin.
NOSE_X_OF_Z = Curve([
    (0.270, 2.382),
    (0.300, 2.393),
    (0.335, 2.406),  # bottom of painted bumper / top of solid dark-grey lower lip
    (0.450, 2.450),
    (0.550, 2.488),
    (0.650, 2.526),
    (0.750, 2.564),
    (0.770, 2.572),
    (0.780, 2.575),  # crisp pointed apex at horizontal headlight bar & badge height
], mode="pchip")
NOSE_Z_LO, NOSE_Z_APEX = 0.270, 0.780
NOSE_Z_HI = round(S.BODY.section_v(JOIN_F(1.0), 1.0)[1], 4)  # centerline hood shut line (~0.8661)

# Tail from the side silhouette (c1_0004): rear bumper bulge to -2.525 (z 0.54..0.62),
# concave tailgate cove (-2.456 at z 0.91), full-width smoked taillight ledge (-2.492 at z 1.10),
# ducktail lip (-2.472 at z 1.18) folding into the backlight foot (-2.400 at z 1.218).
TAIL_X_OF_Z = Curve([
    (0.315, -2.335), (0.380, -2.375), (0.460, -2.410), (0.540, -2.435), (0.620, -2.435),
    (0.690, -2.418), (0.745, -2.402), (0.830, -2.390), (0.910, -2.382), (0.985, -2.395),
    (1.060, -2.415), (1.125, -2.415), (1.178, -2.395), (1.202, -2.365), (1.218, -2.3160),
], mode="pchip")
TAIL_Z_LO, TAIL_Z_HI = 0.315, 1.218

# ------------------------------------------------------------- wrap blending
WRAP = Curve([
    (0.00, 0.0000), (0.10, 0.0087), (0.20, 0.0274), (0.30, 0.0614),
    (0.40, 0.1109), (0.50, 0.1739), (0.55, 0.2107), (0.60, 0.2515),
    (0.65, 0.2967), (0.70, 0.3472), (0.75, 0.4041), (0.80, 0.4689),
    (0.84, 0.5285), (0.88, 0.5968), (0.91, 0.6544), (0.94, 0.7260),
    (0.955, 0.7756), (0.97, 0.8305), (0.98, 0.8580), (0.99, 0.8878),
    (0.995, 0.9300), (1.00, 1.0000),
])

TAIL_W0 = 0.12
TAIL_P_RANGE = (2.0, 3.4)


class TaperedWrapCap(WrapCap):
    """WrapCap whose corner roll leaves JOIN_R tangent to the flank's plan taper at every height."""

    def __init__(self, *a, w0=TAIL_W0, p_range=TAIL_P_RANGE, **kw):
        super().__init__(*a, **kw)
        self.w0, self.p_range, self._p = w0, p_range, {}

    def exponent(self, v):
        key = round(v, 4)
        p = self._p.get(key)
        if p is None:
            lo, hi = self.p_range
            xj = self.JOIN(v)
            yj = self.loft.section_v(xj, v)[0]
            h = 0.010
            m = (self.loft.section_v(xj + h, v)[0] - self.loft.section_v(xj - h, v)[0]) / (2.0 * h)
            depth = abs(xj - self.tip_at(v)[0])
            p = hi if (m <= 1e-3 or depth < 1e-3) else yj * (1.0 - self.w0) / (m * depth)
            p = min(hi, max(lo, p))
            self._p[key] = p
        return p

    def point(self, w, v):
        xj = self.JOIN(v)
        yj, zj = self.loft.section_v(xj, v)
        xt, zt = self.tip_at(v)
        s = min(1.0, max(0.0, (w - self.w0) / (1.0 - self.w0)))
        g = s ** self.exponent(v) if s > 0.0 else 0.0
        u = 1.0 - g
        sl = self.flank_slope(v)
        dx = xt - xj
        z = zj + sl * dx * u + (zt - zj - sl * dx) * u * u
        return (xt + (xj - xt) * g, yj * w, z)

    def wrap(self, w):
        s = min(1.0, max(0.0, (w - self.w0) / (1.0 - self.w0)))
        return s ** 4.0 if s > 0.0 else 0.0


class MonaNoseCap:
    """Pole-free wrap-around front nose cap with WrapCap-compatible API.

    Canonical (w, tau) parameters:
      - w in [0, 1]: centreline (0) sweeping backward to JOIN_F / fender corner (1).
      - tau in [0, TAU_APEX]: lower rearward-raked bumper face from chin (z=Z_LO) to pointed apex.
      - tau in [TAU_APEX, 1]: sleek upper nose sloping from pointed apex into the flush hood U-edge.
    """

    def __init__(self, loft, join, x_of_z_lo, v_corner, z_lo=0.270, z_apex=0.780,
                 v_apex=S.V_SHOULDER, tau_apex=0.72):
        self.loft = loft
        self.front = True
        self.JOIN = join
        self.X_OF_Z = x_of_z_lo
        self.Z_LO = z_lo
        self.Z_APEX = z_apex
        self.V_APEX = v_apex
        self.V_CORNER = v_corner
        self.TAU_APEX = tau_apex
        self.name = "nose"
        self.inside = (S.X_FRONT - 0.66, 0.0, 0.58)
        zs = [loft.section_v(join(k / 400.0), k / 400.0)[1] for k in range(401)]
        self.Z_HI = loft.section_v(join(1.0), 1.0)[1]
        self._z_range = (min(zs), max(zs))
        self._xj_ap = join(v_apex)
        self._yj_ap, self._zj_ap = loft.section_v(self._xj_ap, v_apex)
        self._xj_cor = join(v_corner)
        self._yj_cor, self._zj_cor = loft.section_v(self._xj_cor, v_corner)
        lo_v, hi_v = 0.25, v_apex
        for _ in range(30):
            mv = 0.5 * (lo_v + hi_v)
            if loft.section_v(join(mv), mv)[1] < z_lo:
                lo_v = mv
            else:
                hi_v = mv
        self._v_bot = 0.5 * (lo_v + hi_v)
        self._hood_u_cache = {}
        n_arc = 200
        pts_arc = [
            Vector((join(v_apex + (v_corner - v_apex) * i / n_arc),
                    *loft.section_v(join(v_apex + (v_corner - v_apex) * i / n_arc),
                                    v_apex + (v_corner - v_apex) * i / n_arc)))
            for i in range(n_arc + 1)
        ]
        arc = [0.0]
        for i in range(n_arc):
            arc.append(arc[-1] + (pts_arc[i + 1] - pts_arc[i]).length)
        tot = arc[-1] or 1.0
        self._arc_s = [a / tot for a in arc]
        self._arc_v = [v_apex + (v_corner - v_apex) * i / n_arc for i in range(n_arc + 1)]

    def join_z_range(self):
        return self._z_range

    def _v_upper(self, s):
        s = min(1.0, max(0.0, s))
        lo, hi = 0, len(self._arc_s) - 1
        while lo + 1 < hi:
            mid = (lo + hi) // 2
            if self._arc_s[mid] <= s:
                lo = mid
            else:
                hi = mid
        a0, a1 = self._arc_s[lo], self._arc_s[hi]
        f = (s - a0) / max(1e-9, a1 - a0)
        return self._arc_v[lo] + (self._arc_v[hi] - self._arc_v[lo]) * f

    def _tau_of_v(self, v):
        if v <= self._v_bot:
            return 0.0
        if v <= self.V_APEX:
            return (v - self._v_bot) / max(1e-6, self.V_APEX - self._v_bot) * self.TAU_APEX
        if v >= self.V_CORNER:
            return 1.0
        return self.TAU_APEX + (v - self.V_APEX) / max(1e-6, self.V_CORNER - self.V_APEX) * (1.0 - self.TAU_APEX)

    def _v_of_tau(self, tau):
        tau = min(1.0, max(0.0, tau))
        if tau <= self.TAU_APEX:
            return self._v_bot + (self.V_APEX - self._v_bot) * (tau / self.TAU_APEX)
        return self.V_APEX + (self.V_CORNER - self.V_APEX) * ((tau - self.TAU_APEX) / (1.0 - self.TAU_APEX))

    def apex_point(self, w):
        w = min(1.0, max(0.0, w))
        xt = self.X_OF_Z(self.Z_APEX)
        xj = self._xj_ap
        yj = self._yj_ap
        zj = self._zj_ap
        s = w * w * (0.68 + 0.32 * w * w)
        x = xt + (xj - xt) * s
        y = yj * w
        sz = w * w * (3.0 - 2.0 * w)
        z = self.Z_APEX + (zj - self.Z_APEX) * sz
        return (x, y, z)

    def hood_u_edge(self, w):
        key = round(w, 6)
        c = self._hood_u_cache.get(key)
        if c is not None:
            return c
        S_b = self.loft
        target_y = self._yj_cor * w
        if w <= 1e-6:
            v = 1.0
        elif w >= 1.0 - 1e-6:
            v = self.V_CORNER
        else:
            lo, hi = self.V_CORNER, 1.0
            for _ in range(28):
                mid = 0.5 * (lo + hi)
                if S_b.section_v(self.JOIN(mid), mid)[0] > target_y:
                    lo = mid
                else:
                    hi = mid
            v = 0.5 * (lo + hi)
        xj = self.JOIN(v)
        yj, zj = S_b.section_v(xj, v)
        n = Vector(S_b.surface_normal(min(xj, S.X_FRONT - 0.005), v))
        p_ap = self.apex_point(w)
        d = Vector((p_ap[0] - xj, p_ap[1] - yj, 0.0))
        if d.length < 1e-6:
            d = Vector((1.0, 0.0, 0.0))
        t = d - n * d.dot(n)
        t.normalize()
        c = ((xj, yj, zj), tuple(t), n, v)
        self._hood_u_cache[key] = c
        return c

    def _fender_tangent(self, v):
        S_b = self.loft
        xj = self.JOIN(v)
        n = Vector(S_b.surface_normal(min(xj, S.X_FRONT - 0.005), v))
        d = Vector((-0.35, 0.85, 0.0))
        t = d - n * d.dot(n)
        if t.length < 1e-6:
            t = Vector((0.0, 1.0, 0.0))
        return t.normalized(), n

    def _lower_base(self, w, f):
        S_b = self.loft
        v = self._v_bot + (self.V_APEX - self._v_bot) * f
        xj = self.JOIN(v)
        yj, zj = S_b.section_v(xj, v)
        zt = self.Z_LO + f * (self.Z_APEX - self.Z_LO)
        xt = self.X_OF_Z(zt)
        s = w * w * (0.68 + 0.32 * w * w)
        x = xt + (xj - xt) * s
        y = yj * w
        sz = w * w * (3.0 - 2.0 * w)
        z = zt + (zj - zt) * sz
        return Vector((x, y, z)), v, yj

    def _upper_base(self, w, s):
        p0 = Vector(self.apex_point(w))
        p1_raw, t_hood, _, _ = self.hood_u_edge(w)
        p1 = Vector(p1_raw)
        q = 1.0 - s
        chord = p0 - p1
        th = Vector(t_hood)
        delta = (th * chord.dot(th)) - chord
        b_q = q * (1.0 - q) * (1.0 - q)
        return p0 * q + p1 * s + delta * b_q

    def surface_point(self, w, tau):
        S_b = self.loft
        w = min(1.0, max(0.0, w))
        tau = min(1.0, max(0.0, tau))
        if tau <= self.TAU_APEX:
            f = tau / self.TAU_APEX
            p, v, _ = self._lower_base(w, f)
            w0 = 0.72
            if w > w0:
                u = (w - w0) / (1.0 - w0)
                dw = 1e-3
                p_b1, _, _ = self._lower_base(1.0, f)
                p_bm, _, _ = self._lower_base(1.0 - dw, f)
                dp_du = ((p_b1 - p_bm) / dw) * (1.0 - w0)
                _, n_body = self._fender_tangent(v)
                dp_tan = dp_du - n_body * dp_du.dot(n_body)
                p = p + (dp_tan - dp_du) * (u * u * (u - 1.0))
            return (p.x, p.y, p.z)
        s = (tau - self.TAU_APEX) / (1.0 - self.TAU_APEX)
        p_base = self._upper_base(w, s)
        w0 = 0.68
        if w > w0:
            u = (w - w0) / (1.0 - w0)
            v = self._v_upper(s)
            xj = self.JOIN(v)
            yj, zj = S_b.section_v(xj, v)
            pf = Vector((xj, yj, zj))
            pb_r = self._upper_base(1.0, s)
            diff_r = pf - pb_r
            bw = u * u * (3.0 - 2.0 * u)
            dw = 1e-3
            pb_m = self._upper_base(1.0 - dw, s)
            dp_du = ((pb_r - pb_m) / dw) * (1.0 - w0)
            n_body = Vector(S_b.surface_normal(min(xj, S.X_FRONT - 0.005), v))
            dp_tan = dp_du - n_body * dp_du.dot(n_body)
            slope_corr = (dp_tan - dp_du) * (u * u * (u - 1.0)) * (1.0 - s * s)
            p_base = p_base + diff_r * bw + slope_corr
        return (p_base.x, p_base.y, p_base.z)

    def surface_normal(self, w, tau, h=2.0e-3):
        w0, w1 = max(0.0, w - h), min(1.0, w + h)
        if tau <= self.TAU_APEX:
            t1 = min(self.TAU_APEX, tau + h)
            t0 = max(0.0, t1 - 2.0 * h) if tau < h else max(0.0, tau - h)
        else:
            t0 = max(self.TAU_APEX, tau - h)
            t1 = min(1.0, t0 + 2.0 * h) if tau > 1.0 - h else min(1.0, tau + h)
        pw0, pw1 = self.surface_point(w0, tau), self.surface_point(w1, tau)
        pt0, pt1 = self.surface_point(w, t0), self.surface_point(w, t1)
        a = [pw1[i] - pw0[i] for i in range(3)]
        b = [pt1[i] - pt0[i] for i in range(3)]
        n = [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
        L = math.sqrt(sum(c * c for c in n))
        if L < 1e-9:
            return (0.4, 0.0, 0.916) if tau > self.TAU_APEX else (0.94, 0.0, -0.34)
        n = [c / L for c in n]
        p = self.surface_point(w, tau)
        d = [p[i] - self.inside[i] for i in range(3)]
        if sum(n[i] * d[i] for i in range(3)) < 0.0:
            n = [-c for c in n]
        return tuple(n)

    def point(self, w, v):
        return self.surface_point(w, self._tau_of_v(v))

    def normal(self, w, v, h=2.0e-3):
        return self.surface_normal(w, self._tau_of_v(v), h=h)

    def offset(self, w, v, dist):
        tau = self._tau_of_v(v)
        p = self.surface_point(w, tau)
        n = self.surface_normal(w, tau)
        return tuple(p[i] + n[i] * dist for i in range(3))

    def v_at_z(self, z, w=0.0):
        lo, hi = 0.0, 1.0
        for _ in range(32):
            mid = 0.5 * (lo + hi)
            if self.surface_point(w, mid)[2] < z:
                lo = mid
            else:
                hi = mid
        return self._v_of_tau(0.5 * (lo + hi))

    def _w_tau_at(self, y, z):
        y = max(0.0, y)
        best_d = 1e9
        best = (0.0, 0.5)
        for it in range(25):
            tau = it / 24.0
            for iw in range(15):
                w = iw / 14.0
                p = self.surface_point(w, tau)
                d = (p[1] - y) ** 2 + (p[2] - z) ** 2
                if d < best_d:
                    best_d = d
                    best = (w, tau)
        w, tau = best
        step = 0.04
        for _ in range(18):
            improved = False
            for dw, dt in ((step, 0.0), (-step, 0.0), (0.0, step), (0.0, -step)):
                ww = min(1.0, max(0.0, w + dw))
                tt = min(1.0, max(0.0, tau + dt))
                p = self.surface_point(ww, tt)
                d = (p[1] - y) ** 2 + (p[2] - z) ** 2
                if d < best_d:
                    best_d = d
                    w, tau = ww, tt
                    improved = True
            if not improved:
                step *= 0.5
        return w, tau

    def wv_at(self, y, z):
        w, tau = self._w_tau_at(y, z)
        return w, self._v_of_tau(tau)

    def wv_at_xz(self, x, z):
        best_d = 1e9
        best = (0.0, 0.5)
        for it in range(25):
            tau = it / 24.0
            for iw in range(15):
                w = iw / 14.0
                p = self.surface_point(w, tau)
                d = (p[0] - x) ** 2 + (p[2] - z) ** 2
                if d < best_d:
                    best_d = d
                    best = (w, tau)
        return best[0], self._v_of_tau(best[1])

    def x_at(self, y, z):
        w, tau = self._w_tau_at(y, z)
        return self.surface_point(w, tau)[0]

    def half_width(self, z):
        return self.point(1.0, self.v_at_z(z, 1.0))[1]

    def rows(self, nw=52, n_lo=36, n_hi=18, z_lo=None, offset=0.0):
        """Non-degenerate wrap-around quad grid for MONA_Fascia, bracketing the sharp apex crease."""
        ws = [1.0 - (1.0 - i / float(nw)) ** 1.35 for i in range(nw + 1)]
        tau_min = 0.0 if z_lo is None else max(
            0.0, (z_lo - self.Z_LO) / (self.Z_APEX - self.Z_LO) * self.TAU_APEX
        )
        taus = [tau_min + (self.TAU_APEX - tau_min) * k / float(n_lo) for k in range(n_lo)]
        # Tight ~5-6 mm bracket rows right around TAU_APEX for a crisp specular apex highlight!
        taus += [max(tau_min, self.TAU_APEX - 0.010), self.TAU_APEX, min(1.0, self.TAU_APEX + 0.012)]
        taus += [self.TAU_APEX + (1.0 - self.TAU_APEX) * k / float(n_hi) for k in range(1, n_hi + 1)]
        # Ensure strict monotonicity & remove near-duplicates
        clean = []
        for t in sorted(taus):
            if not clean or t - clean[-1] > 1e-4:
                clean.append(t)
        grid = []
        for w in ws:
            col = []
            for tau in clean:
                p = self.surface_point(w, tau)
                if offset:
                    n = self.surface_normal(w, tau)
                    p = (p[0] + n[0] * offset, p[1] + n[1] * offset, p[2] + n[2] * offset)
                col.append(p)
            grid.append(col)
        return grid


NOSE = MonaNoseCap(S.BODY, JOIN_F, NOSE_X_OF_Z, _V_CORNER,
                   z_lo=NOSE_Z_LO, z_apex=NOSE_Z_APEX, v_apex=S.V_SHOULDER)
TAIL = TaperedWrapCap(S.BODY, front=False, join=JOIN_R, x_of_z=TAIL_X_OF_Z,
                      z_lo=TAIL_Z_LO, z_hi=TAIL_Z_HI, wrap=None)
TAIL.inside = (-2.435 + 0.66, 0.0, 0.58)
BODY = CarBody(S.BODY, NOSE, TAIL, flank_x_range=(-2.33, 2.35))


def dims_report():
    return BODY.dims_report()
