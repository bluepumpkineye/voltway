"""SU7 Ultra wheels: forged double-five-spoke U, carbon-ceramic brakes.

21 in, five closed U-shaped ribs in 72 degree symmetry, each closed round the
hub with two legs out to a rim ring, gloss black with a thin yellow pinstripe
on the lip. Its identity is DEPTH: the face stands ~12 mm below the lip at the
rim and plunges to the hub plate, and behind it a dark carbon-ceramic rotor
fills most of the rim diameter, so the face reads as three layers - black
ribs, disc, yellow caliper - with black voids between them.

The face is TRACED, like the Luxeed RX's (rx_wheels.py): the front wheel of the
silver car (Autohome 12793832, owner approved) unwarped face-on, unrolled into
polar coordinates, and the outlines of the two openings of one repeat read off
as half-widths by radius and mirrored about the hairpin's own axis - the real
wheel is symmetric, the photograph's perspective is not. The outlines are the
ribs' SILHOUETTES: a leg is 16 mm wide at the lip, 25 at 0.8 of its radius and
30-34 mm round the bend, because its flanks slope and the camera sees them; the
top edges are rounded (the bevel) to carry that.

Sizes: 265/35 R21 front, 305/30 R21 rear; carbon-ceramic discs 430 mm front,
410 mm rear; Akebono calipers, 6-piston front at 3 o'clock (straight
rearward), 4-piston rear at about 2 o'clock.
"""
import math

from carkit.parts import wheels as W

AXIS = 270.0            # the hairpin that points down, as the photographs show the wheel

# Half-widths of the two openings of one repeat, (radius / lip radius, degrees from the
# opening's own axis), top to bottom. Both close against the rim ring at 0.918.
#   SLOT  the inside of a hairpin: a leg's inner silhouette to the other's, round the bight
#   GAP   between two hairpins, centred 36 degrees on: a narrow slit down to the hub plate
SLOT_HW = [(0.918, 11.2), (0.885, 11.3), (0.808, 11.85), (0.746, 12.6), (0.677, 13.35),
           (0.620, 14.0), (0.569, 14.6), (0.530, 14.75), (0.490, 14.1), (0.446, 12.8),
           (0.408, 10.4), (0.385, 8.4), (0.358, 5.0), (0.346, 2.0), (0.342, 0.0)]
GAP_HW = [(0.918, 19.9), (0.846, 18.2), (0.777, 16.35), (0.708, 14.5), (0.638, 12.35),
          (0.577, 10.3), (0.523, 8.75), (0.469, 7.2), (0.431, 6.5), (0.400, 6.3),
          (0.388, 5.0), (0.381, 3.0), (0.378, 0.0)]


def _outline(axis, hw):
    """Closed (angle, radius) polygon from half-widths by radius, mirrored about `axis`."""
    left = [(axis - w, r) for (r, w) in hw]
    right = [(axis + w, r) for (r, w) in reversed(hw[:-1])]
    return left + right


SPEC = W.preset(
    "su7_ultra_hairpin", roll_left=math.pi,
    flange_face=0.0040, stripe_r=(0.0040, 0.0003),
    hub=dict(cap_r=0.0227, cap_rise=0.007),
    lugs=dict(count=5, r=0.0135, deg=AXIS - 180.0, rise=0.010, dome=True),
    # Akebono: 6 pistons on the front axle (yellow from -61 to +55 degrees round the disc in the
    # photographs), 4 on the rear (-19 to +63)
    caliper=dict(span_deg=57.0, span_rear=41.0, r_inner=0.14, steps=16),
    mats=dict(lugs="black_gloss", barrel="grille"))
RIM_D = SPEC["rim_d"]
RIM_R = RIM_D / 2.0
SPEC["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.030, bevel=0.0060, bevel_segs=2, mat="rim",
    r_in=0.026, r_out=RIM_R - SPEC["flange_face"], nr=16, seg=60, step_deg=2.5, step_r=0.03,
    windows=[_outline(AXIS, SLOT_HW), _outline(AXIS + 36.0, GAP_HW)],
    lug_holes=dict(deg=AXIS - 180.0, pcd=0.05715, r=0.0165, count=5))


def build_all(collection, surface, lib):
    """Four corners, sized and tracked to the real car."""
    corners = [
        # tag, axle x, sign, tyre width, rolling radius, disc radius,
        # caliper deg, outer sidewall y (~20 mm inside the arch lip)
        ("FL", surface.FRONT_AXLE, 1, 0.265, 0.3595, 0.215, 177.0, 0.9625),
        ("FR", surface.FRONT_AXLE, -1, 0.265, 0.3595, 0.215, 183.0, 0.9625),
        # On the left, local +Y maps to world -Z, so "rearward and 22 degrees
        # up" is 202 there and 158 on the right (the front axle's, 3 degrees
        # below the horizontal, are 177 and 183).
        ("RL", surface.REAR_AXLE, 1, 0.305, 0.3582, 0.205, 202.0, 0.9650),
        ("RR", surface.REAR_AXLE, -1, 0.305, 0.3582, 0.205, 158.0, 0.9650),
    ]
    return W.build_set(collection, "SU7Ultra_", lib, SPEC, corners)
