"""Avatr 06T nose and tail caps - the curves of its two WrapCaps.

The cap maths is carkit.body.caps (WrapCap):
    C(w, v)     v = the body loft's section parameter
                w = 1 at the shut line where the cap meets the loft, 0 on
                    the centreline
"""
import a06t_surface as S
from carkit.geom import Curve
from carkit.body import WrapCap, CarBody

# ---------------------------------------------------------------- shut lines
# Front: the fascia meets the fender at the lamp pocket's rear edge (x 2.05, a little ahead of
# the wheel opening, FRONT_AXLE + ARCH_R = 1.985), and runs up over the fender to the hood's
# leading shut line at x 2.26.
JOIN_F = Curve([
    (0.00, 2.300), (0.10, 2.250), (0.22, 2.150), (0.34, 2.075),
    (0.44, 2.052), (0.52, 2.060), (0.62, 2.095), (0.74, 2.155),
    (0.82, 2.205), (0.88, 2.250), (0.94, 2.295), (0.98, 2.318), (1.00, 2.328),
])

# Rear: behind the rear wheel opening (REAR_AXLE - ARCH_R = -1.785), rising behind the lamp
# bar's wrap onto the quarter to the tailgate's top corner.
JOIN_R = Curve([
    (0.00, -2.262), (0.10, -2.226), (0.22, -2.158), (0.34, -2.120),
    (0.46, -2.108), (0.56, -2.122), (0.66, -2.160), (0.76, -2.205),
    (0.86, -2.246), (0.94, -2.272), (1.00, -2.284),
])

# ------------------------------------------- centreline profiles, x given z
# Nose from the side silhouette (c1_0004, plane y 0.25): an upright face at x 2.47 from the
# chin to the bonnet's rounded leading edge, which rolls back over a radius of ~0.35 m.
NOSE_X_OF_Z = Curve([
    (0.195, 2.415), (0.260, 2.425), (0.330, 2.428), (0.390, 2.440),
    (0.440, 2.468), (0.500, 2.470), (0.560, 2.470), (0.610, 2.466),
    (0.655, 2.447), (0.685, 2.418), (0.716, 2.386), (0.746, 2.346),
    (0.759, 2.328),
])
# the cap ends at the bonnet's leading edge (c1_0002: z 0.759 at the centre rising to 0.79 at the corner)
NOSE_Z_LO, NOSE_Z_HI = 0.195, 0.759


# Tail from the silhouette: a bumper bulge to x -2.47 at z 0.52, the tailgate's face at -2.405
# above the lamp bar, folding forward over the tailgate's top edge into the glass.
#
# 2026-10-28 rear refit: the side photograph's tail edge through the solved camera (rows every 20 mm,
# `tail_prof`) put the old profile 4-6 cm too far back at every height (bumper bulge +4.5 cm, gate face
# +6, lamp ledge +3, glass foot +5; the spoiler tip was right within 2). The real tail is an S: a bumper
# bulge at z 0.52, a gate face that tucks 8 cm in over z 0.65-0.80, a small ledge at the lamp, then the
# turn into the glass. Knots are the photo's edge, not the old curve plus an offset. (+22 mm on the face and
# bumper after the corner roll changed, fading to nothing at the glass foot: the roll's silhouette is
# what the side photo sees, and the wider roll stands further back at the same centre depth. +14 mm more
# when the per-height corner exponent replaced the single one.)
TAIL_X_OF_Z = Curve([
    (0.255, -2.286), (0.320, -2.312), (0.400, -2.332), (0.470, -2.364),
    (0.520, -2.388), (0.560, -2.382), (0.600, -2.364), (0.640, -2.336),
    (0.690, -2.314), (0.760, -2.310), (0.850, -2.330), (0.920, -2.338),
    (0.970, -2.339), (1.000, -2.332), (1.025, -2.324), (1.060, -2.303),
    (1.093, -2.282),
], mode="pchip")
TAIL_Z_LO, TAIL_Z_HI = 0.255, 1.093

# ------------------------------------------------------------- wrap blending
WRAP = Curve([
    (0.00, 0.0000), (0.10, 0.0087), (0.20, 0.0274), (0.30, 0.0614),
    (0.40, 0.1109), (0.50, 0.1739), (0.55, 0.2107), (0.60, 0.2515),
    (0.65, 0.2967), (0.70, 0.3472), (0.75, 0.4041), (0.80, 0.4689),
    (0.84, 0.5285), (0.88, 0.5968), (0.91, 0.6544), (0.94, 0.7260),
    (0.955, 0.7756), (0.97, 0.8305), (0.98, 0.8580), (0.99, 0.8878),
    (0.995, 0.9300), (1.00, 1.0000),
])

# The tail's corner roll. g = s^P(v) with s = (w - W0)/(1 - W0): flat across the face to W0 (the gate's shut
# line, y 0.59, is 0.67 of the join's half-width), then rolling into the flank. The END SLOPE is the point: the
# cap must leave the join at the flank's own plan taper, dy/dx = m(v), and it does so at dy/dx = yj / (g'(1) * depth)
# with g'(1) = P / (1 - W0), so P(v) = yj (1 - W0) / (m depth). One P for every height (4.0) left a 6-9 degree
# crease down the corner at the bumper and door-top heights, where the flank tapers at only 0.16-0.20 against
# the cap's 0.31-0.38 (ray probe across the seam, 2026-10-28); the old table had g'(1) ~ 40 and a 9-14 degree one.
TAIL_W0 = 0.67
TAIL_P_RANGE = (3.2, 7.5)


class TaperedWrapCap(WrapCap):
    """A WrapCap whose corner roll leaves the join along the flank's plan taper at every height."""

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
BODY = CarBody(S.BODY, NOSE, TAIL, flank_x_range=(-2.35, 2.30))


def dims_report():
    return BODY.dims_report()
