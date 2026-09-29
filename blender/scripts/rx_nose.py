"""Luxeed RX nose and tail caps - the curves of its two WrapCaps.

The cap maths is carkit.body.caps (WrapCap); see su7_nose.py for what each
curve means.

    C(w, v)     v = the body loft's section parameter
                w = 1 at the shut line where the cap meets the loft, 0 on
                    the centreline
"""
import rx_surface as S
from carkit.geom import Curve
from carkit.body import WrapCap, CarBody

# ---------------------------------------------------------------- shut lines
# Front: the bumper meets the fender just ahead of the wheel opening (its
# painted edge reaches x 1.93) and runs up behind the headlamp to the hood.
JOIN_F = Curve([
    (0.00, 2.300), (0.10, 2.250), (0.22, 2.160), (0.34, 2.080),
    (0.44, 2.050), (0.52, 2.060), (0.62, 2.090), (0.74, 2.130),
    (0.86, 2.165), (0.94, 2.185), (1.00, 2.190),
])

# Rear: just behind the wheel opening (painted edge at x -2.16, z 0.58),
# up behind the lamp's wrap-round to the ducktail.
JOIN_R = Curve([
    (0.00, -2.330), (0.10, -2.300), (0.22, -2.260), (0.34, -2.240),
    (0.46, -2.235), (0.56, -2.250), (0.66, -2.280), (0.76, -2.320),
    (0.86, -2.370), (0.94, -2.410), (1.00, -2.440),
])

# ------------------------------------------- centreline profiles, x given z
# The nose: the side outline reaches x 2.48 from z 0.36 to 0.52 and rolls
# back to 2.19 at the hood's centreline (z 0.877); the lip under the lower
# grille tucks back to 2.44. (Sept 2026: the side photograph's outline,
# formed at the corners y ~0.45-0.52, stood 11-16 px - 7-9 cm - ahead of the
# photo's at z 0.37-0.64: the face came back ~2.5 cm and the corners round
# off (WRAP); the tail gained what the nose lost, keeping 5.02 m.)
NOSE_X_OF_Z = Curve([
    (0.262, 2.440), (0.300, 2.465), (0.360, 2.480), (0.440, 2.482),
    (0.520, 2.480), (0.600, 2.465), (0.680, 2.430), (0.740, 2.385),
    (0.790, 2.330), (0.820, 2.295), (0.845, 2.262), (0.862, 2.232),
    (0.877, 2.190),
])
# the top meets the hood's centreline at the join, along its slope (~-0.32)
NOSE_Z_LO, NOSE_Z_HI = 0.262, 0.877

# The tail: nearly upright from the diffuser to the ducktail lip, the
# rearmost point of the car at the top. 25 mm further back than first built
# (the side outline stood 6-16 px short; the nose gave the length up).
TAIL_X_OF_Z = Curve([
    (0.300, -2.455), (0.360, -2.495), (0.440, -2.515), (0.550, -2.522),
    (0.650, -2.517), (0.750, -2.507), (0.850, -2.503), (0.950, -2.511),
    (1.050, -2.525), (1.110, -2.533), (1.150, -2.535),
], mode="pchip")
TAIL_Z_LO, TAIL_Z_HI = 0.300, 1.150

# ------------------------------------------------------------- wrap blending
# The RX nose wraps round its corners, 60 % of the way from the broad first
# cut to the SU7's round one: the side photograph's outline (formed at the
# corners) wanted them 7-9 cm further back. The blue front 3/4, which put
# the headlamps' inner tips level with the nose's centre, was solved with
# its front rim - and its front wheels are steered, so it cannot say.
WRAP = Curve([
    (0.00, 0.0000), (0.10, 0.0087), (0.20, 0.0274), (0.30, 0.0614),
    (0.40, 0.1109), (0.50, 0.1739), (0.55, 0.2107), (0.60, 0.2515),
    (0.65, 0.2967), (0.70, 0.3472), (0.75, 0.4041), (0.80, 0.4689),
    (0.84, 0.5285), (0.88, 0.5968), (0.91, 0.6544), (0.94, 0.7260),
    (0.955, 0.7756), (0.97, 0.8305), (0.98, 0.8580), (0.99, 0.8878),
    (0.995, 0.9300), (1.00, 1.0000),
])
# The RX's tail is broad and square in plan: the side photograph's outline
# (formed ~27 deg off rearward, at the corner) is 0.2 m further back than a
# round tail puts it.
# Squarer again (the side silhouette's tail stood 13-21 px short of the
# photo's, ~9 cm): the corner stays full until late and turns tighter -
# and fuller still with the longer tail (Sept 2026).
TAIL_WRAP = Curve([
    (0.00, 0.000), (0.20, 0.004), (0.40, 0.016), (0.55, 0.034),
    (0.68, 0.062), (0.78, 0.105), (0.86, 0.170), (0.92, 0.270),
    (0.96, 0.420), (0.985, 0.640), (0.996, 0.840), (1.00, 1.000),
])

NOSE = WrapCap(S.BODY, front=True, join=JOIN_F, x_of_z=NOSE_X_OF_Z,
               z_lo=NOSE_Z_LO, z_hi=NOSE_Z_HI, wrap=WRAP)
TAIL = WrapCap(S.BODY, front=False, join=JOIN_R, x_of_z=TAIL_X_OF_Z,
               z_lo=TAIL_Z_LO, z_hi=TAIL_Z_HI, wrap=TAIL_WRAP)
BODY = CarBody(S.BODY, NOSE, TAIL, flank_x_range=(-2.40, 2.35))


def dims_report():
    return BODY.dims_report()
