"""XPeng G9L nose and tail caps - the curves of its two WrapCaps.

The cap maths is carkit.body.caps (WrapCap).

    C(w, v)     v = the body loft's section parameter
                w = 1 at the shut line where the cap meets the loft, 0 on
                    the centreline

The profiles are the side photograph's nose and tail outlines through its camera
(g9l_ref_match "side_left"): the nose is a blunt, nearly upright face (x 2.50-2.575 from the
chin to the lamp bar) that rolls back over the lamp bar into the bonnet (x 2.25 at z 1.17); the
tail is an upright face at x -2.55 from the bumper to the backlight's foot at z 1.27.
The blocks between `fit:` markers are rewritten by g9l_fit.py.
"""
import g9l_surface as S
from carkit.geom import Curve
from carkit.body import WrapCap, CarBody

# ---------------------------------------------------------------- shut lines
# fit:join  x of the cap/flank construction seam by section parameter v
JOIN_F = Curve([
    (0.00, 2.380), (0.20, 2.380), (0.34, 2.300), (0.45, 2.220), (0.52, 2.200),
    (0.70, 2.230), (0.85, 2.265), (1.00, 2.300),
], mode="pchip")
JOIN_R = Curve([
    (0.00, -2.3525), (0.15, -2.3575), (0.30, -2.3625), (0.45, -2.358), (0.60, -2.350),
    (0.80, -2.346), (1.00, -2.3375),
], mode="pchip")
# /fit:join

# ------------------------------------------- centreline profiles, x given z
# fit:nose  (z, x)
NOSE_PTS = [
    (0.312, 2.455), (0.400, 2.508), (0.550, 2.548), (0.750, 2.568), (0.880, 2.572),
    (0.940, 2.548), (0.990, 2.502), (1.035, 2.455), (1.068, 2.415), (1.088, 2.365),
    (1.098, 2.300),
]
# /fit:nose
NOSE_X_OF_Z = Curve(NOSE_PTS, mode="pchip")
NOSE_Z_LO, NOSE_Z_HI = NOSE_PTS[0][0], NOSE_PTS[-1][0]

# fit:tail  (z, x)
# Sporty forward-undercut Kamm-tail: furthest aft at the taillight crest (x -2.550, z 1.195),
# sloping cleanly forward toward the plate and sweeping upward/inward at the lower diffuser (z 0.390, x -2.375)
TAIL_PTS = [
    (0.405, -2.330), (0.495, -2.405), (0.600, -2.448), (0.720, -2.462),
    (0.850, -2.478), (0.980, -2.512), (1.100, -2.542),
    (1.195, -2.556), (1.258, -2.544),
]
# /fit:tail
TAIL_X_OF_Z = Curve(TAIL_PTS, mode="pchip")
TAIL_Z_LO, TAIL_Z_HI = TAIL_PTS[0][0], TAIL_PTS[-1][0]

# ------------------------------------------------------------- wrap blending
WRAP = Curve([
    (0.00, 0.0000), (0.10, 0.0087), (0.20, 0.0274), (0.30, 0.0614),
    (0.40, 0.1109), (0.50, 0.1739), (0.55, 0.2107), (0.60, 0.2515),
    (0.65, 0.2967), (0.70, 0.3472), (0.75, 0.4041), (0.80, 0.4689),
    (0.84, 0.5285), (0.88, 0.5968), (0.91, 0.6544), (0.94, 0.7260),
    (0.955, 0.7756), (0.97, 0.8305), (0.98, 0.8580), (0.99, 0.8878),
    (0.995, 0.9300), (1.00, 1.0000),
])
# The cap must leave the join in the flank's own plan direction (dy/dx 0.2-0.5 at the rear quarter): the
# last stretch of g rises at ~18 per unit w (it was 40: a 9-14 degree plan crease, the rear quarter's pleat).
TAIL_WRAP = Curve([
    (0.00, 0.000), (0.20, 0.004), (0.40, 0.016), (0.55, 0.034),
    (0.68, 0.062), (0.78, 0.108), (0.86, 0.180), (0.92, 0.300),
    (0.96, 0.470), (0.98, 0.640), (0.99, 0.770), (0.995, 0.880), (1.00, 1.000),
])

import os as _os
if _os.environ.get("G9L_OLDCAPS"):
    NOSE = WrapCap(S.BODY, front=True, join=JOIN_F, x_of_z=NOSE_X_OF_Z,
                   z_lo=NOSE_Z_LO, z_hi=NOSE_Z_HI, wrap=WRAP)
    TAIL = WrapCap(S.BODY, front=False, join=JOIN_R, x_of_z=TAIL_X_OF_Z,
                   z_lo=TAIL_Z_LO, z_hi=TAIL_Z_HI, wrap=TAIL_WRAP)
else:
    from carkit.body import WrapCapG1
    _K1 = float(_os.environ.get("G9L_K1", "0.78"))
    _K2 = float(_os.environ.get("G9L_K2", "0.55"))
    NOSE = WrapCapG1(S.BODY, front=True, join=JOIN_F, x_of_z=NOSE_X_OF_Z,
                     z_lo=NOSE_Z_LO, z_hi=NOSE_Z_HI, k1=_K1, k2=_K2)
    TAIL = WrapCapG1(S.BODY, front=False, join=JOIN_R, x_of_z=TAIL_X_OF_Z,
                     z_lo=TAIL_Z_LO, z_hi=TAIL_Z_HI, k1=_K1, k2=_K2)
BODY = CarBody(S.BODY, NOSE, TAIL, flank_x_range=(-2.40, 2.35))


def dims_report():
    return BODY.dims_report()
