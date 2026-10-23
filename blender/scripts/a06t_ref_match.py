"""Avatr 06T reference cameras, for carkit.qa.refmatch.

    import a06t_ref_match as RM
    RM.overlay("side", "check")   # -> renders/match/side_check_overlay.png

References (blender/reference/avatr-06t/exterior, Autohome series 8538, 3840 x 2880; local only):
    c1_0004  light-blue car, left side   silhouette, colour, shut lines   (camera "side")
Solved in a06t_cam.py (rim lips + the 2.940 m wheelbase; level camera, 16 m away).

Model coordinates: +X forward, +Y to the left, Z up, length centred on x = 0.
"""
import math

from carkit.qa.refmatch import *                 # noqa: F401,F403
from carkit.qa import refmatch as _R
import a06t_cam as C

SIZE = (C.W, C.H)


def _side(name, photo, cam):
    _R.register(name, "avatr-06t/exterior/" + photo, SIZE,
                (cam.cx, C.D, cam.cz), (90.0, math.degrees(cam.roll), 180.0), cam.f)


_side("side", "c1_0004.jpg", C.SIDE)

_R.register("front", "avatr-06t/exterior/c1_0002.jpg", SIZE, C.FRONT_CAM["loc"], (90.0, 0.0, 90.0),
            C.FRONT_CAM["f"], pp=C.FRONT_CAM["pp"])
_R.register("rear", "avatr-06t/exterior/c1_0006.jpg", SIZE, C.REAR_CAM["loc"], (90.0, 0.0, 270.0),
            C.REAR_CAM["f"], pp=C.REAR_CAM["pp"])
