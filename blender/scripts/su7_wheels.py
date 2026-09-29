"""SU7 Ultra wheels: forged double-five-spoke U, carbon-ceramic brakes.

The wheel is carkit's "su7_ultra_hairpin" preset (carkit.parts.wheels): 21 in,
five closed U-shaped ribs in 72 degree symmetry, each closed round the hub with
two slender legs out to the rim, gloss black with a thin gold pinstripe on the
flange. Its identity is DEPTH: the spoke crest stands ~14 mm below the flange
at the rim and plunges to the hub plate, and behind it a dark matte
carbon-ceramic rotor fills most of the rim diameter, so the face reads as three
layers - black spokes, disc, gold caliper - with black voids between them.

Sizes: 265/35 R21 front, 305/30 R21 rear; carbon-ceramic discs 430 mm front,
410 mm rear; Akebono calipers, 6-piston front at 3 o'clock (straight
rearward), 4-piston rear at about 2 o'clock.
"""
from carkit.parts import wheels as W

SPEC = W.PRESETS["su7_ultra_hairpin"]
RIM_D = SPEC["rim_d"]
RIM_R = RIM_D / 2.0


def build_all(collection, surface, lib):
    """Four corners, sized and tracked to the real car."""
    corners = [
        # tag, axle x, sign, tyre width, rolling radius, disc radius,
        # caliper deg, outer sidewall y (~20 mm inside the arch lip)
        ("FL", surface.FRONT_AXLE, 1, 0.265, 0.3595, 0.215, 180.0, 0.9625),
        ("FR", surface.FRONT_AXLE, -1, 0.265, 0.3595, 0.215, 180.0, 0.9625),
        # On the left, local +Y maps to world -Z, so "rearward and 30 degrees
        # up" is 210 there and 150 on the right.
        ("RL", surface.REAR_AXLE, 1, 0.305, 0.3582, 0.205, 210.0, 0.9650),
        ("RR", surface.REAR_AXLE, -1, 0.305, 0.3582, 0.205, 150.0, 0.9650),
    ]
    return W.build_set(collection, "SU7Ultra_", lib, SPEC, corners)
