"""Voyah Passion S nose and tail caps - WrapCap and G1-continuous TaperedWrapCap.

    C(w, v)     v = the body loft's section parameter
                w = 1 at the shut line where the cap meets the loft, 0 on the centreline
"""
import vps_surface as S
from carkit.geom import Curve
from carkit.body import WrapCap, CarBody

# ---------------------------------------------------------------- shut lines
# Front: stays ahead of the front wheel arch + cladding (FRONT_AXLE + 0.532 = 2.057 m),
# rising over the upper DRL corner to the bonnet's leading nose-channel edge at x 2.360.
JOIN_F = Curve([
    (0.00, 2.340), (0.10, 2.260), (0.22, 2.160), (0.34, 2.085),
    (0.44, 2.065), (0.54, 2.080), (0.64, 2.125), (0.76, 2.205),
    (0.86, 2.285), (0.94, 2.338), (0.98, 2.354), (1.00, 2.360),
])

# Rear: behind the rear wheel arch + cladding (REAR_AXLE - 0.532 = -2.007 m),
# rising behind the tail-lamp flank tip to the backlight's foot at x -2.400.
JOIN_R = Curve([
    (0.00, -2.310), (0.12, -2.240), (0.24, -2.165), (0.36, -2.118),
    (0.46, -2.105), (0.56, -2.122), (0.68, -2.175), (0.80, -2.255),
    (0.90, -2.335), (0.96, -2.380), (1.00, -2.400),
])

# ------------------------------------------- centreline profiles, x given z
# Nose from the side silhouette (c1_0004): chin splitter at z 0.275, recessed lower grille,
# proud painted nose face at x 2.525 (z 0.52..0.79), rolling back to the nose channel at z 0.892.
NOSE_X_OF_Z = Curve([
    (0.264, 2.455), (0.285, 2.505), (0.315, 2.488), (0.355, 2.465),
    (0.435, 2.468), (0.485, 2.502), (0.535, 2.522), (0.620, 2.525),
    (0.735, 2.525), (0.795, 2.520), (0.835, 2.495), (0.868, 2.448),
    (0.892, 2.360),
], mode="pchip")
NOSE_Z_LO, NOSE_Z_HI = 0.264, 0.892

# Tail from the side silhouette (c1_0004): rear bumper bulge to -2.525 (z 0.54..0.62),
# concave tailgate cove (-2.456 at z 0.91), full-width smoked taillight ledge (-2.492 at z 1.10),
# ducktail lip (-2.472 at z 1.18) folding into the backlight foot (-2.400 at z 1.218).
TAIL_X_OF_Z = Curve([
    (0.315, -2.425), (0.380, -2.462), (0.460, -2.495), (0.540, -2.525),
    (0.620, -2.525), (0.690, -2.502), (0.745, -2.482), (0.830, -2.466),
    (0.910, -2.456), (0.985, -2.472), (1.060, -2.492), (1.125, -2.490),
    (1.178, -2.472), (1.202, -2.438), (1.218, -2.400),
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

TAIL_W0 = 0.67
TAIL_P_RANGE = (3.2, 7.5)


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


NOSE = WrapCap(S.BODY, front=True, join=JOIN_F, x_of_z=NOSE_X_OF_Z,
               z_lo=NOSE_Z_LO, z_hi=NOSE_Z_HI, wrap=WRAP)
TAIL = TaperedWrapCap(S.BODY, front=False, join=JOIN_R, x_of_z=TAIL_X_OF_Z,
                      z_lo=TAIL_Z_LO, z_hi=TAIL_Z_HI, wrap=None)
BODY = CarBody(S.BODY, NOSE, TAIL, flank_x_range=(-2.42, 2.36))


def dims_report():
    return BODY.dims_report()
