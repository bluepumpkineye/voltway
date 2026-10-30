"""Voyah Passion S reference cameras, for carkit.qa.refmatch.

    import vps_ref_match as RM
    RM.overlay("side", "check")   # -> renders/match/side_check_overlay.png

References (blender/reference/voyah-passion-s/exterior, Autohome series 8534, 3840 x 2880; local only):
    c1_0004  Rosy Mist Pink car, left side   silhouette, colour, shut lines   (camera "side")
    c1_0002  front view                                                       (camera "front")
    c1_0006  rear view                                                        (camera "rear")
Solved in vps_cam.py (rim lips + the 3.000 m wheelbase; level camera, 24.5 m away).

Model coordinates: +X forward, +Y to the left, Z up, length centred on x = 0.
"""
import math

from carkit.qa.refmatch import *                 # noqa: F401,F403
from carkit.qa import refmatch as _R
import vps_cam as C

SIZE = (C.W, C.H)


def _side(name, photo, cam):
    _R.register(name, "voyah-passion-s/exterior/" + photo, SIZE,
                (cam.cx, C.D, cam.cz), (90.0, math.degrees(cam.roll), 180.0), cam.f)


_side("side", "c1_0004.jpg", C.SIDE)

_R.register("front", "voyah-passion-s/exterior/c1_0002.jpg", SIZE, C.FRONT_CAM["loc"], (90.0, 0.0, 90.0),
            C.FRONT_CAM["f"], pp=C.FRONT_CAM["pp"])
_R.register("rear", "voyah-passion-s/exterior/c1_0006.jpg", SIZE, C.REAR_CAM["loc"], (90.0, 0.0, 270.0),
            C.REAR_CAM["f"], pp=C.REAR_CAM["pp"])
