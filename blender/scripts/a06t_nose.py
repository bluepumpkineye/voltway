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
# Front: bumper meets the front fender just ahead of the wheel opening
# (FRONT_AXLE + ARCH_R = 1.962) and runs up behind the F-type headlamp wing
# to the hood shut line at x 2.18.
JOIN_F = Curve([
    (0.00, 2.260), (0.10, 2.210), (0.22, 2.130), (0.34, 2.055),
    (0.44, 2.030), (0.52, 2.040), (0.62, 2.075), (0.74, 2.115),
    (0.86, 2.155), (0.94, 2.175), (1.00, 2.180),
])

# Rear: behind the rear wheel opening (REAR_AXLE - ARCH_R = -1.862), rising
# behind the star-ring taillamp wrap-around to the shooting-brake ducktail.
JOIN_R = Curve([
    (0.00, -2.290), (0.10, -2.260), (0.22, -2.215), (0.34, -2.195),
    (0.46, -2.190), (0.56, -2.205), (0.66, -2.240), (0.76, -2.285),
    (0.86, -2.340), (0.94, -2.380), (1.00, -2.415),
])

# ------------------------------------------- centreline profiles, x given z
# Diving peregrine-falcon nose, read off c1_0001/c1_0004: the face is nearly
# upright from the splitter lip (z 0.15) to a rounded top edge at z ~0.70, then
# the hood rolls back and up to x 2.18 at z 0.80.
NOSE_X_OF_Z = Curve([
    (0.150, 2.405), (0.190, 2.438), (0.240, 2.458), (0.300, 2.468),
    (0.400, 2.470), (0.500, 2.468), (0.600, 2.462), (0.650, 2.450),
    (0.700, 2.420), (0.740, 2.370), (0.770, 2.300), (0.790, 2.230),
    (0.800, 2.180),
])
NOSE_Z_LO, NOSE_Z_HI = 0.150, 0.800


# Shooting-brake tail: sculpted ducktail at z 1.035, slightly recessed band
# under the star-ring taillamps (z 0.72..0.88), and athletic lower diffuser
# extending to x -2.470.
TAIL_X_OF_Z = Curve([
    (0.255, -2.420), (0.320, -2.455), (0.410, -2.470), (0.520, -2.470),
    (0.620, -2.458), (0.720, -2.446), (0.820, -2.445), (0.910, -2.458),
    (0.980, -2.468), (1.015, -2.470), (1.035, -2.470),
], mode="pchip")
TAIL_Z_LO, TAIL_Z_HI = 0.255, 1.035

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
