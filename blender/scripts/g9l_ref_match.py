"""XPeng G9L reference cameras, for carkit.qa.refmatch.

    import g9l_ref_match as RM
    RM.overlay("side_left", "check")   # -> renders/match/*_overlay.png

References (blender/reference/xpeng-g9l/exterior, Autohome series 8659, the 2026 755 Ultra AWD
spec 77790 in Provence Purple on a violet studio, 3840 x 2880; local only). Photographs 1-8
are one turntable set: a fixed camera on a tripod (0.85 m high for the front, rear and 3/4
shots, raised to 1.07 m for the left side shot), each shot cropped a little differently by
Autohome (hence a different f in px). Solved by hand from certain things (nothing is fitted
to the model):

    side_left   c1_0004.jpg   level camera. Both hub caps (775.5, 1921.3) and (2934.0, 1915.0)
                px give 696.3 px/m at the hub plane (y 0.93): wheelbase 3.100 m, hub height
                0.377 m (265/40 R22: 0.3854 m free, 8 mm of sag), so the camera is 1.068 m
                high at x 0.006. f = 696.3 * (D - 0.93). The distance is the weak number:
                the rim ellipses' axis ratios (0.970 front, 0.978 rear) say 7.4-7.8 m, the
                roof's near edge (1.79-1.81 m from the hub scale: orthographic) says a long
                lens, the nose-to-tail length against the wheelbase (3280 px for 5.12 m
                against 2173 px for 3.10 m) says 8.5 m if the extremes stand at y 0.2 and
                10.8 m at y 0; D = 11 is used. The silhouette fit (fit_tools) absorbs the rest.
    front       c1_0002.jpg   straight on, 0.847 m high, level. The front tyres' outer walls
                (800 and 3036 px, y +/-0.998 at the axle) give 1120 px/m at depth D - 1.65;
                tyre bottoms on the ground at v 2392. The nose plate is the 480 x 140 mm
                new-energy size (589 px: 1227 px/m at depth D - 2.53): D = 11.7; the roof's
                top edge (v 524 against 638 for D 6.9) says 15. D = 13 is used.
    rear        c1_0006.jpg   straight on from behind, 0.856 m high: the rear tyres' walls at
                805 and 3037 px (y +/-1.007 at x -1.45), bottoms at v 2390; the plate (620
                px = 480 mm) says D = 9.3; D = 13 is used (same turntable distance).

Model coordinates: +X forward, +Y to the left, Z up, the car's length centred on x = 0 (front
axle at +1.65, rear axle at -1.45).
"""
import os

from carkit.qa.refmatch import *                 # noqa: F401,F403
from carkit.qa import refmatch as _R

REF_DIR = os.path.join(_R.REF_ROOT, "xpeng-g9l", "exterior")
SIZE = (3840, 2880)
D_SIDE = 11.0
D_END = 13.0

_R.register("side_left", "xpeng-g9l/exterior/c1_0004.jpg", SIZE,
            (0.0063, D_SIDE, 1.0683), (90.0, 0.28, 180.0), 696.3 * (D_SIDE - 0.93))
_R.register("front", "xpeng-g9l/exterior/c1_0002.jpg", SIZE,
            (D_END, 0.0, 0.847), (90.0, 0.0, 90.0), 1120.0 * (D_END - 1.65), pp=(-2.0, 0.0))
_R.register("rear", "xpeng-g9l/exterior/c1_0006.jpg", SIZE,
            (-D_END, 0.0, 0.856), (90.0, 0.0, 270.0), 1110.0 * (D_END - 1.45), pp=(-2.0, 0.0))

# c1_0028.jpg: the WHITE car (spec 77778?), left side, a grey studio: the shut lines and trim read
# cleanly on white paint. Rim lip ellipses (rms ~1 px): front centre (803.9, 1910.2), rear (2916.6,
# 1896.4), ratios 0.992 / 0.990 (near-orthographic), semi-axes 203.5 / 205 px = lip radius 0.299 m at
# 681.5 px/m; the 14 px between the two centres is a 0.38 degree roll. Camera 1.057 m high.
_R.register("side_white", "xpeng-g9l/exterior/c1_0028.jpg", SIZE,
            (0.0123, D_SIDE, 1.057), (90.0, 0.38, 180.0), 681.5 * (D_SIDE - 0.93))

# c1_0026.jpg: the WHITE car straight on from the front, a grey studio. Solved from the lamp bar's
# centre (2.505, 0, 1.00) and the chin's bottom (2.47, 0, 0.316), both read off the side photograph,
# the front tyres' outer walls (783 and 3057 px: y +/-0.998 at the axle) and the nose plate's four
# corners (the 480 x 148 mm new-energy sign: 633.6 px wide): the camera stands 7.5 m ahead of the
# car's centre, 1.06 m high, 1.5 degrees nose-down, f 6694 px (rms 5 px). Every start distance 6.5-13 m
# converges to this.
_R.register("front_white", "xpeng-g9l/exterior/c1_0026.jpg", SIZE,
            (7.505, 0.0, 1.062), (88.47, 0.0, 90.0), 6694.0)

# c1_0030.jpg: the WHITE car straight on from behind. Solved from the tyres' outer walls (791 and 3053
# px: y +/-1.007 at the rear axle), the nose plate's four corners (the 480 mm new-energy sign, 643 px
# wide; its height is solved: the plate's centre stands at z 0.87), the tail lamp's lower edge (z 1.14,
# x -2.50, read in the side photograph) and the roof spoiler's trailing edge (z 1.64, x -2.03): the
# camera stands 8.4 m behind the car's centre, 1.43 m high, 4.2 degrees nose-down, f 7920 px (rms 12 px).
_R.register("rear_white", "xpeng-g9l/exterior/c1_0030.jpg", SIZE,
            (-8.402, 0.0, 1.428), (85.76, 0.0, 270.0), 7920.0)

# c1_0001.jpg: the PURPLE car's left front three-quarter (2026-10-26, solved free by carkit.qa.refmatch.solve_camera,
# rms 1.2 px, level NOT assumed: the turntable's camera is 1.29 m high here): the front-left wheel's rim lip (fit_rim, 131
# points on the ellipse, 0.5 px), the rear-left rim's visible edge (10 points) and the 480 x 148 mm nose sign's four corners
# (its centre solved: x 2.580, z 0.631). f 6692 px, the same as the white car's end views.
_R.register("f34_purple", "xpeng-g9l/exterior/c1_0001.jpg", SIZE,
            (7.589, 4.432, 1.294), (86.511, 0.967, 122.502), 6692.0)

# c1_0005.jpg: the purple car's left REAR three-quarter. Solved free like the front one, from the rear-left rim lip (17 points
# read on the ellipse), the far front-left rim lip (15 points) and the 480 x 148 mm sign's four corners (its centre solved: x -2.42,
# z 0.87; its corners sit +-15 px off, the sign being tilted on the curved tailgate). rms 8.2 px, f 6676 (the front's 6692).
_R.register("r34_purple", "xpeng-g9l/exterior/c1_0005.jpg", SIZE,
            (-7.445, 4.731, 1.214), (87.418, -0.717, 235.838), 6675.6)
