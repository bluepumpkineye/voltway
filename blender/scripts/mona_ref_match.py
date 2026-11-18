"""XPeng Mona L05 reference cameras, for carkit.qa.refmatch.

    import mona_ref_match as RM
    RM.overlay("side", "check")   # -> renders/match/side_check_overlay.png

References (blender/reference/xpeng-mona-l05/exterior, Autohome series 8662, 3840 x 2880; local only):
    c1_0003  purple car, left side    silhouette, colour, shut lines   (camera "side")
    c1_0009  white car, front head-on                                  (camera "front")
    c1_0005  purple car, rear head-on                                  (camera "rear")
Solved in mona_cam.py (rim lips + the 2.940 m wheelbase; level camera, 24.5 m away).

Model coordinates: +X forward, +Y to the left, Z up, length centred on x = 0.
"""
import math

from carkit.qa.refmatch import *                 # noqa: F401,F403
from carkit.qa import refmatch as _R
import mona_cam as C

SIZE = (C.W, C.H)


def _side(name, photo, cam):
    _R.register(name, "xpeng-mona-l05/exterior/" + photo, SIZE,
                (cam.cx, C.D, cam.cz), (90.0, math.degrees(cam.roll), 180.0), cam.f)


_side("side", "c1_0003.jpg", C.SIDE)

_R.register("front", "xpeng-mona-l05/exterior/c1_0009.jpg", SIZE, C.FRONT_CAM["loc"], (90.0, 0.0, 90.0),
            C.FRONT_CAM["f"], pp=C.FRONT_CAM["pp"])
_R.register("rear", "xpeng-mona-l05/exterior/c1_0005.jpg", SIZE, C.REAR_CAM["loc"], (90.0, 0.0, 270.0),
            C.REAR_CAM["f"], pp=C.REAR_CAM["pp"])

# c1_0001: purple front 3/4 from the car's left (the owner's "front area" photo). Solved 2026-11-17 from the two left
# rim lips (hand-picked ellipse points, 40 points, rms 2.2 px; f is only weakly fixed by one plane, 12 500 - 14 200 fit).
_R.register("f34", "xpeng-mona-l05/exterior/c1_0001.jpg", SIZE, (15.336, 8.400, 1.067), (89.874, 0.069, 119.554), 12643.0)
