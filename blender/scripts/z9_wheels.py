"""Denza Z9 wheels: 21-inch Luxury 14-Spoke Machined Alloy wheels
(255/40 R21 front, 275/40 R21 rear).

Matches the luxury multi-spoke alloy wheels shown on the Denza Z9 studio
turnarounds (c1_0001..0008, c1_0033..0040):
- 14 slender radial machined-alloy spokes with dark gloss-black barrel and
  counterbored lug pocket
- Silver/gunmetal multi-piston brake calipers with ventilated discs
- Denza circular center hub cap
"""
import math
from carkit.geom import Curve
from carkit.parts import wheels as W

LIP_21 = 0.2785     # 21-inch rim lip radius (m)

CALIPER = dict(
    span_deg=40.0, span_rear=34.0, r_inner=0.135, d_out=0.032, steps=16
)

DISH = Curve([
    (0.000, 0.052), (0.080, 0.052), (0.110, 0.042), (0.150, 0.028),
    (0.200, 0.016), (0.245, 0.009), (0.278, 0.000),
], mode="pchip")

SPEC_LUXURY = W.preset(
    "multi_10",
    rim_d=2.0 * LIP_21,
    dish=DISH,
    pinstripe=False,
    spokes=dict(
        style="straight", count=14, phase=math.pi / 14.0, depth=0.026,
        bevel=0.0022, params=dict(w_hub=0.020, w_rim=0.015),
    ),
    tyre=dict(bulge=1.042, shoulder=0.015),
    hub=dict(depth=0.062, setback=0.008, cap_rise=0.005),
    lugs=dict(count=5, pcd_r=0.0540, r=0.0120, deg=18.0, rise=0.004),
    disc=dict(style="plain", inner_r=0.118, thickness=0.032),
    caliper=CALIPER,
    mats=dict(
        rim="machined",
        lip="machined",
        spokes="machined",
        accent="black_gloss",
        lugs="black_gloss",
        cap="cap_black",
        disc="iron",
        barrel="black_gloss",
    ),
)

DESIGNS = {
    "luxury": ("DenzaZ9_", SPEC_LUXURY),
}
DEFAULT = "luxury"


def corners(surface):
    """The 4 staggered corners of the Denza Z9: 255 mm front, 275 mm rear."""
    r = surface.WHEEL_R
    return [
        ("FL", surface.FRONT_AXLE,  1, 0.255, r, 0.195, 176.0, surface.TRACK_F / 2.0 + 0.118),
        ("FR", surface.FRONT_AXLE, -1, 0.255, r, 0.195, 184.0, surface.TRACK_F / 2.0 + 0.118),
        ("RL", surface.REAR_AXLE,   1, 0.275, r, 0.185, 176.0, surface.TRACK_R / 2.0 + 0.125),
        ("RR", surface.REAR_AXLE,  -1, 0.275, r, 0.185, 184.0, surface.TRACK_R / 2.0 + 0.125),
    ]


def build_design(collection, surface, lib, name):
    prefix, spec = DESIGNS[name]
    return W.build_set(collection, prefix, lib, spec, corners(surface))


def build_all(collection, surface, lib):
    return build_design(collection, surface, lib, DEFAULT)


def build_options(collection, surface, lib):
    made = []
    for name in DESIGNS:
        if name != DEFAULT:
            made += build_design(collection, surface, lib, name)
    return made
