"""Zeekr 7X reference cameras, for carkit.qa.refmatch.

    import zx_ref_match as RM
    RM.overlay("side_left", "check")   # -> renders/match/*_overlay.png

References (blender/reference/zeekr-7x, Autohome series 7777, the 2026 Ultra in
canyon-stone blue on a white studio floor, 3840 x 2880; local only), solved in
zx_camsolve.py with the front axle at x = 0 and shifted here by
zx_surface.FRONT_AXLE:

    side_left_studio.jpg   the car's left side, ~120 mm equivalent from ~19.5 m
                           to the car's centre plane (f 12650 px, fixed from the
                           roof: the silhouette's peak on y = 0 comes out at
                           1.655 against the published 1.656). Both rim lips fit
                           to 0.27 px, so the wheels are the scale and level.
"""
import os

from carkit.qa.refmatch import *                 # noqa: F401,F403
from carkit.qa import refmatch as _R

import zx_surface as S

REF_DIR = os.path.join(_R.REF_ROOT, "zeekr-7x")
FA = S.FRONT_AXLE

# (name, file, size, loc in axle coordinates, rot, f_px) - zx_camsolve
_SOLVED = (
    ("side_left", "zeekr-7x/side_left_studio.jpg", (3840, 2880),
     (-1.5007, 19.6008, 1.1009), (90.3701, 0.4034, 179.9898), 12650.0),
)
for _n, _f, _sz, _loc, _rot, _fp in _SOLVED:
    _R.register(_n, _f, _sz, (_loc[0] + FA, _loc[1], _loc[2]), _rot, _fp)

# The other seven photographs of the set are the same studio: a turntable and a fixed
# camera ~20 m from the car's centre at ~0.47 m height (only the side shot, 1.10 m, was
# raised), each cropped differently by Autohome (hence a different f in px). Solved in
# MODEL coordinates (zx_camsolve.solve_34): the REAR rim lip of the near/far side (the
# front wheels are steered) on the circle D = 20 m, z = 0.47, azimuth from the side axis
# (+ towards the nose, left side positive). Rim fit rms 2-6 px.
# (the front 3/4s add the front hub's centre, the front door handle - read off the side
# photograph, (0.0915, +/-0.92, 0.964) - and, on the left, the lidar pod: D 21-22 m,
# z 0.73-0.81, a 1 deg roll, f ~16000; the roof outline then lies within ~1 cm)
_R.register("f34_left", "zeekr-7x/front34_left_studio.jpg", (3840, 2880),
            (19.4471, 10.8480, 0.7288), (90.8600, 1.0086, 119.6458), 16347.6)
_R.register("f34_right", "zeekr-7x/front34_right_studio.jpg", (3840, 2880),
            (18.6975, -10.5744, 0.8066), (90.5868, 0.8744, 60.0777), 15453.6)
_R.register("r34_left", "zeekr-7x/rear34_left_studio.jpg", (3840, 2880),
            (-17.4693, 9.6656, 0.47), (91.7349, 0.0, 240.8336), 15453.9)
_R.register("r34_right", "zeekr-7x/rear34_right_studio.jpg", (3840, 2880),
            (-17.6353, -9.3586, 0.47), (91.3304, 1.1359, 298.0635), 17668.8)
# front_studio.jpg: straight on, from tyre walls (+/-0.957 at the front axle), the
# ground line, the lidar pod's top (0.31, 0, 1.575) and the chin lip: ~20.8 m ahead of the
# origin at 0.46 m, looking 1.4 deg up (zx_camsolve / pinhole fit, cost 373 px^2)
_R.register("front", "zeekr-7x/front_studio.jpg", (3840, 2880),
            (20.83, 0.0, 0.464), (91.37, 0.0, 90.0), 17272.0)

# rear_studio.jpg: straight on from behind: the same studio distance as the front shot
# (the turntable: 20.83 m from the origin, f 17293 vs 17272), height and pitch solved from
# the rear tyres' walls (+/-0.9595 at the rear axle), the ground line and the roof's crown
# (-0.49, 0, 1.649) - zx_camsolve.REAR_CAM
_R.register("rear", "zeekr-7x/rear_studio.jpg", (3840, 2880),
            (-20.83, 0.0, 0.755), (90.53, 0.0, 270.0), 17293.0)

CAMERAS = _R.CAMERAS
