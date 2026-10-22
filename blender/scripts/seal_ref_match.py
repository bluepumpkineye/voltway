"""BYD Seal reference cameras, for carkit.qa.refmatch.

    import seal_ref_match as RM
    RM.overlay("side_white", "check")   # -> renders/match/*_overlay.png

References (blender/reference/byd-seal-ev/exterior, Autohome series 6394, 3840 x 2880; local only):
    c1_0513  blue car, side      silhouette, colour           (camera "side_blue")
    c1_0506  white car, side     shut lines                   (camera "side_white")
    c1_0511 / c1_0515  blue car, front / rear
Solved in seal_cam.py (rim lips + the 2.920 m wheelbase; level cameras 1.2 m high, 14 m away).

Model coordinates: +X forward, +Y to the left, Z up, length centred on x = 0.
"""
import math
import os

from carkit.qa.refmatch import *                 # noqa: F401,F403
from carkit.qa import refmatch as _R
import seal_cam as C

REF_DIR = os.path.join(_R.REF_ROOT, "byd-seal-ev", "exterior")
SIZE = (C.W, C.H)


def _side(name, photo, cam):
    _R.register(name, "byd-seal-ev/exterior/" + photo, SIZE,
                (cam.cx, C.D, cam.cz), (90.0, math.degrees(cam.roll), 180.0), cam.f)


_side("side_blue", "c1_0513.jpg", C.BLUE)
_side("side_white", "c1_0506.jpg", C.WHITE)

# front, c1_0511 (blue car straight on): see seal_cam.FRONT_CAM (camera 0.615 m up, pitched UP 1.43 degrees)
_R.register("front_blue", "byd-seal-ev/exterior/c1_0511.jpg", SIZE,
            C.FRONT_CAM["loc"], (90.0 - math.degrees(C.FRONT_CAM["pitch"]), 0.0, 90.0), C.FRONT_CAM["f"])

# rear, c1_0515 (blue car straight from behind): seal_cam.REAR_CAM (0.624 m up, pitched UP 1.19 degrees)
_R.register("rear_blue", "byd-seal-ev/exterior/c1_0515.jpg", SIZE,
            C.REAR_CAM["loc"], (90.0 - math.degrees(C.REAR_CAM["pitch"]), 0.0, 270.0), C.REAR_CAM["f"],
            pp=(C.REAR_U0 - 0.5 * C.W, 0.0))
