"""Luxeed RX reference cameras, for carkit.qa.refmatch.

    import rx_ref_match as RM
    RM.overlay("side_left", "check")   # -> renders/match/*_overlay.png

References (blender/reference/luxeed-rx), solved in rx_camsolve.py with the
front axle at x = 0 and shifted here by rx_surface.FRONT_AXLE:

    side_left.jpg        1023 x 682, grey RX Ultra, left side, 43 mm eq.,
                         yawed 7.6 deg (rear further away), 2.5 px rms
    front34_blue.jpg     1200 x 900, the blue/purple show car from ahead-left,
                         140 mm eq., 2.1 px rms; a 480 x 140 NEV plate on
                         the nose, its face 1.131 m ahead of the front axle.
                         Its FRONT WHEELS ARE STEERED towards the camera (~15-20
                         deg): the projected rear rim and tyre sit on the photo's,
                         the front ones do not - compare wheels on the rear one

Also in the folder (Sept 2026 additions): side_left_green.webp (a green
standard RX, clean profile), fender_closeup_left.jpg, rear34_left_high.jpg,
rear_high.jpg, rear34_right_forest.webp (the silver car's RIGHT side from
behind - the nose points right in the frame).

    rear34_forest        2000 x 1125, rear 3/4 from the right, 31 mm eq.,
                         8.4 px rms from both right-hand rims, the door
                         handles and the lamp's flank tip (rx_camsolve).
                         Close and wide: good for the greenhouse and C-pillar
                         by eye, not for the tail's x (it reads ~10 cm short
                         where the side photo, 2.5 px, agrees within 4 px).

rear34_left_high and rear_high did not solve better than 15 px: that street
car's plate recess and reflectors do not sit where the studio car's do.

Not used for measurement: rear34_left_small.jpg - its tailgate badge reads
"智界 R7", not RX.
"""
import os

from carkit.qa.refmatch import *                 # noqa: F401,F403
from carkit.qa import refmatch as _R

import rx_surface as S

REF_DIR = os.path.join(_R.REF_ROOT, "luxeed-rx")
FA = S.FRONT_AXLE

# (name, file, size, loc in axle coordinates, rot, f_px) - rx_camsolve.solve_all()
_SOLVED = (
    ("side_left", "luxeed-rx/side_left.jpg", (1023, 682),
     (-0.5059, 7.2862, 1.1995), (86.292, -0.723, 172.433), 1210.4),
    ("front34_blue", "luxeed-rx/front34_blue.jpg", (1200, 900),
     (16.5191, 9.6547, 0.9608), (88.95, 0.313, 118.624), 4659.1),
)
for _n, _f, _sz, _loc, _rot, _fp in _SOLVED:
    _R.register(_n, _f, _sz, (_loc[0] + FA, _loc[1], _loc[2]), _rot, _fp)

# rear.jpg, 2277 x 1280, the grey car square from behind, solved in MODEL
# coordinates (rx_camsolve.solve_rear): rear tyre contacts and walls (the
# 1720 mm track), the roof crest at the side photo's (-0.9, 1.585), and the
# mirror tips taken at y +/-1.10 - they are 2 m deeper than the axle and are
# what fixes the focal length (+/-30 mm of tip half-width moves f by ~15 %).
_R.register("rear", "luxeed-rx/rear.jpg", (2277, 1280),
            (-11.708, 0.067, 0.870), (89.53, -0.04, -90.47), 6747.0)

# front_silver.jpg, 1320 x 1547, a silver car straight on from ahead and a
# little above (96 mm eq.), solved in MODEL coordinates, 2.6 px rms, from the
# headlamps' inner tips (2.366, +/-0.524, 0.740), the emblem (on the face at
# z 0.762), the chin strip's centre and the mirror heads' outer ends (y
# +/-1.0975 - these fix the focal length). Read off it: the hood's shield
# outline, its smile, the domes, the corner intakes. It grazes the hood, so
# x read off it by casting depends on the hood's height.
_R.register("front_silver", "luxeed-rx/front_silver.jpg", (1320, 1547),
            (7.3819, -0.015, 1.3692), (85.2051, -0.2593, 89.6418), 3508.5)

CAMERAS = _R.CAMERAS

# rear34_right_forest.webp, 2000 x 1125, solved in MODEL coordinates
# (rx_camsolve.solve_forest), 8.4 px rms
_R.register("rear34_forest", "luxeed-rx/rear34_right_forest.webp", (2000, 1125),
            (-3.1422, -4.0383, 0.9257), (86.959, 2.376, -30.241), 1748.9)

# ---------------------------------------------------------------- the cabin
# interior/cabin_front_black.jpg, 1600 x 900, Luxeed's straight-on cabin press
# render (black and tan trim), solved in MODEL coordinates (rx_camsolve.
# solve_cabin), 7.9 px rms: a camera between the front seats at head height,
# from the windscreen's side edges and the door glass's front edges up both
# A-pillars, the door belts, and the centre screen's corners (16.1 in 16:10
# plus a 6 mm glass border; its centre and tilt solved with the camera:
# (0.446, 0, 1.077), 9.9 deg back).
_R.register("cabin_front", "luxeed-rx/interior/cabin_front_black.jpg", (1600, 900),
            (-0.470, -0.007, 1.204), (77.97, 0.0, -89.71), 858.1)

# interior/passenger34_high_white.jpg, 1920 x 1440, the showroom car from over
# the passenger seat (an iPhone ultra-wide), solved from points on the BUILT
# cabin (the screen's corners, both cupholder rims, the hazard button, the
# wheel hub, the RX badge, the band's vent): 16 px rms. For side-by-side
# comparisons, not for measuring - its points are the model's own.
_R.register("passenger34", "luxeed-rx/interior/passenger34_high_white.jpg", (1920, 1440),
            (-0.142, -0.375, 1.121), (58.95, -5.47, -59.75), 620.0)
