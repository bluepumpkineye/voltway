"""SU7 Ultra reference cameras, for carkit.qa.refmatch.

    import ref_match
    ref_match.overlay("side_turntable", "check")   # -> renders/match/*_overlay.png

References (blender/reference/su7-ultra):
    side_turntable.png   730 x 730, the car's left side, 50.9 mm-equivalent lens

The side camera: both wheel centres land within 0.1 px of the photo
(117.2 / 586.0 px) and the ground line within 0.2 px (479.1 px). The same
camera comes out of carkit's solver:

    refmatch.solve_side_camera((730, 730), 117.2, 586.0, 422.9, 479.1, 3.0,
                               1.5575, 0.3595, 0.955, f_px=1032.0)
    -> loc (-0.028, 7.559, 0.730)
"""
import os

from carkit.qa.refmatch import *                 # noqa: F401,F403
from carkit.qa import refmatch as _R

REF_DIR = os.path.join(_R.REF_ROOT, "su7-ultra")
_R.register("side_turntable", "su7-ultra/side_turntable.png", (730, 730),
            (-0.028, 7.559, 0.731), (90.0, 0.0, 180.0), 1032.0)

# The Ultra press render of the cabin (1280 x 960): a very wide lens (f 835 px,
# ~27 mm equivalent) between the front seats, 1.39 m up, looking down 25.4
# degrees - the backrests fall outside the frame, so the black-and-yellow
# shapes at the bottom are the seat CUSHIONS seen from above. Fitted to the
# windscreen header and A-pillars, the two fender crowns visible over the
# dash, the belt lines and the door mirrors (carkit.qa.refmatch, 12-18 px rms:
# the photo shows trim edges, which sit inboard of the glass edges by varying
# amounts). It puts the windscreen base exactly on the modelled cowl.
_R.register("cabin_front", "su7-ultra/interior/ultra_cabin_front.png", (1280, 960),
            (-0.7144, 0.0, 1.3895), (90.0 - 25.3822, 0.0, -90.0), 835.29)
# Hide these to see out of the cabin in an overlay: the glass (except the
# windscreen, whose outline is the header and A-pillars), the inner shell,
# the greenhouse underlay, and the wheels.
CABIN_HIDE = ("Glass_Door", "Glass_Quarter", "Glass_Rear", "Shell_Shadow",
              "Greenhouse_Black", "Roof_Rear_Black", "Underbody", "Liner", "Tyre_",
              "Rim", "Spokes_", "Hub", "Disc", "Caliper_", "Lugs_")
# The maker's head-on press photograph of the yellow car (xiaomi-su7-ultra/lights/cat53/big_023.jpg, 1600 x 1200): a long
# lens (f 3860 px, ~100 mm equivalent) 8.3 m from the nose, 1.16 m up, tipped 2.55 degrees down, on the centre line.
# Solved from what a head-on photograph fixes: the body's width (the fender silhouette at 0.995 m a side) for the scale,
# the splitter / corner-blade bottoms and the hood's crown for the height and pitch. Checked by projecting the built
# panels' vertices over the photograph (docs/3d-pipeline.md): the fender outline and the blades' bottoms land within
# 2-3 px (5 mm). The photograph's LEFT half is the car's RIGHT (y < 0).
import math as _math
from mathutils import Vector as _V

FRONT_D, FRONT_ZC, FRONT_PITCH, FRONT_F, FRONT_X_NOSE = 8.3, 1.16, 2.55, 3860.0, 2.4
_th = _math.radians(FRONT_PITCH)
_eul = _V((-_math.cos(_th), 0.0, -_math.sin(_th))).to_track_quat('-Z', 'Y').to_euler('XYZ')
FRONT_CAM = dict(loc=(FRONT_X_NOSE + FRONT_D, 0.0, FRONT_ZC), rot=tuple(_math.degrees(a) for a in _eul), f=FRONT_F)
_R.register("head_on", "xiaomi-su7-ultra/lights/cat53/big_023.jpg", (1600, 1200),
            FRONT_CAM["loc"], FRONT_CAM["rot"], FRONT_CAM["f"])

CAMERAS = _R.CAMERAS
