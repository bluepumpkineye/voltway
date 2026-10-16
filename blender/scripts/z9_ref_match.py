"""Denza Z9 reference cameras, for carkit.qa.refmatch.

    import z9_ref_match as RM
    RM.overlay("side_black", "check")   # -> renders/match/*_overlay.png

References (blender/reference/denza-z9/exterior, Autohome series 7838; local only):
    c1_0033-0040  the BLACK car in a white studio, a turntable set (3840 x 2880)
    c1_0041-0048  a white car in a showroom (wide lens, strong perspective: shut lines only)
    c1_0065-0072  a grey car outdoors against the sky (sharp, level; the right side faces the camera)

side_black  c1_0036.jpg: the car's LEFT side, nose to the left. Hub caps read at (954, 2042.5) and
            (2937.5, 2042.5) px: 634.7 px/m at the hub plane over the 3.125 m wheelbase, both on one
            row (level), so the camera stands 1.311 m high; the lip ring of the 21 in wheel measures
            186 px (0.293 m). Distance D = 15 m (weakly fixed, like the G9L's; fitted below).
"""
import os

from carkit.qa.refmatch import *                 # noqa: F401,F403
from carkit.qa import refmatch as _R

REF_DIR = os.path.join(_R.REF_ROOT, "denza-z9", "exterior")
SIZE = (3840, 2880)
FRONT_AXLE = 1.625
D_SIDE = 15.0
_K = 634.7
_ZC = 0.362 + (2042.5 - 1440.0) / _K

_R.register("side_black", "denza-z9/exterior/c1_0036.jpg", SIZE,
            (FRONT_AXLE + (954.0 - 1920.0) / _K, D_SIDE, _ZC), (90.0, 0.0, 180.0), _K * (D_SIDE - 0.93))

# c1_0038.jpg: the black car straight on from behind. Pitch 0 (the camera is level): the rear tyres' outer
# walls (1068 and 2774 px, 1.9994 m: 853 px/m at depth D - 1.5) and the plate (478 px = the 480 mm sign:
# 996 px/m at depth D - 2.6) give D = 9.1 m and f = 6483 px; the tyre bottoms (v 2266) then put the camera
# 0.968 m up, which puts the tail lamp at z 0.91 (the side photograph's 0.90) and the roundel at 0.89.
_R.register("rear_black", "denza-z9/exterior/c1_0038.jpg", SIZE,
            (-9.1, 0.0, 0.968), (90.0, 0.0, 270.0), 6483.0)

# c1_0034.jpg: the black car straight on from the front, level. The front tyres' outer walls (1066 and 2774
# px: +/-0.9825 at the front axle: 869 px/m at depth D - 1.625) and the nose plate (493 px = the 480 mm
# sign: 1027 px/m at depth D - 2.6) give D = 7.96 m, f = 5505 px; the tyres' contact (v 2246) puts the
# camera 0.927 m up.
_R.register("front_black", "denza-z9/exterior/c1_0034.jpg", SIZE,
            (7.96, 0.0, 0.927), (90.0, 0.0, 90.0), 5505.0)
