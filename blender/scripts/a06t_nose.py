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
    (0.00, -2.290), (0.10, -2.250), (0.22, -2.170), (0.34, -2.130),
    (0.46, -2.120), (0.56, -2.140), (0.66, -2.190), (0.76, -2.245),
    (0.86, -2.290), (0.94, -2.318), (1.00, -2.330),
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
TAIL_X_OF_Z = Curve([
    (0.255, -2.405), (0.320, -2.435), (0.400, -2.455), (0.470, -2.466),
    (0.520, -2.470), (0.560, -2.466), (0.600, -2.440), (0.640, -2.414),
    (0.690, -2.404), (0.760, -2.405), (0.850, -2.414), (0.920, -2.412),
    (0.970, -2.408), (1.000, -2.402), (1.025, -2.390), (1.060, -2.360), (1.093, -2.330),
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

TAIL_WRAP = Curve([
    (0.00, 0.000), (0.20, 0.004), (0.40, 0.016), (0.55, 0.034),
    (0.68, 0.062), (0.78, 0.105), (0.86, 0.170), (0.92, 0.270),
    (0.96, 0.420), (0.985, 0.640), (0.996, 0.840), (1.00, 1.000),
])

NOSE = WrapCap(S.BODY, front=True, join=JOIN_F, x_of_z=NOSE_X_OF_Z,
               z_lo=NOSE_Z_LO, z_hi=NOSE_Z_HI, wrap=WRAP)
TAIL = WrapCap(S.BODY, front=False, join=JOIN_R, x_of_z=TAIL_X_OF_Z,
               z_lo=TAIL_Z_LO, z_hi=TAIL_Z_HI, wrap=TAIL_WRAP)
BODY = CarBody(S.BODY, NOSE, TAIL, flank_x_range=(-2.35, 2.30))


def dims_report():
    return BODY.dims_report()
