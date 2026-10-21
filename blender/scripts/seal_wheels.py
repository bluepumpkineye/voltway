"""BYD Seal EV 19-inch 10-spoke angular turbine-blade alloy wheels (235/45 R19 front & rear).

Calibrated to BYD Seal AWD Performance trim wheel designs (Autohome Series 6394, c1_0004.jpg):
- 10 angular swept turbine blades with dual-tone finish (machined bright face + gloss-black pocket)
- Bounded strictly within the 19-inch rim radius (r_rim = 0.240 m < lip 0.254 m) so zero geometry
  ever intersects the tyre sidewall
- Polished machined flange lip and central hub cap with BYD emblem
"""
import math
from carkit.geom import Curve
from carkit.parts import wheels as W

LIP_19 = 0.2540     # 19-inch rim lip radius (m)
TAB = 0.945         # visible machined flange landing

CALIPER = dict(
    span_deg=34.0, span_rear=28.0, r_inner=0.118, d_out=0.028, steps=16
)

# Progressive dish curve dropping from rim flange to central hub
DISH = Curve([
    (0.000, 0.045), (0.070, 0.045), (0.095, 0.036), (0.135, 0.024),
    (0.180, 0.014), (0.220, 0.008), (0.254, 0.000),
], mode="pchip")

# 10-spoke directional turbine/blade-style multi-spoke alloy design for BYD Seal AWD Performance
SPEC_SEAL_TURBINE_10 = W.preset(
    "su7_ultra_hairpin",
    rim_d=2.0 * LIP_19,
    flange=(0.118, 0.125, 0.50),
    flange_face=(1.0 - TAB) * LIP_19,
    dish=DISH,
    pinstripe=False,
    roll_left=math.pi,
    spokes=dict(
        style="blade",
        count=10,
        phase=math.pi / 10.0,
        depth=0.026,
        bevel=0.0016,
        params=dict(
            r_hub=0.084,
            r_rim=0.242,       # Strictly inside rim lip 0.254 m (no tyre sidewall clipping!)
            w_hub=0.018,
            w_rim=0.038,
            twist=0.30,        # Pronounced directional turbine blade sweep
            twist_power=1.35,
            split=0.46,        # Sharp machined leading blade vs gloss-black aero pocket
            drop=0.020,
        ),
        face_mat="machined",
    ),
    hub=dict(
        depth=0.045,
        setback=0.006,
        cap_rise=0.004,
        cap_r=0.030,
        cap_logo=dict(
            quads=[
                ((-0.016, -0.006), (-0.016, 0.006), (-0.008, 0.006), (-0.008, -0.006)),
                ((-0.004, -0.006), (-0.004, 0.006), (0.004, 0.006), (0.004, -0.006)),
                ((0.008, -0.006), (0.008, 0.006), (0.016, 0.006), (0.016, -0.006)),
            ],
            h=0.005,
            mat="logo_chrome",
        ),
    ),
    lugs=dict(count=5, pcd_r=0.0520, r=0.0090, deg=18.0, rise=0.003),
    disc=dict(style="plain", inner_r=0.115, thickness=0.028),
    caliper=CALIPER,
    tyre=dict(bulge=1.035, shoulder=0.014),
    mats=dict(
        tyre="rubber",
        rim="black_gloss",
        lip="machined",
        lugs="wheel_silver",
        cap="black_gloss",
        disc="iron",
        barrel="black_gloss",
        accent="machined",
        caliper="caliper",
    ),
)

DESIGNS = {
    "turbine_10": ("BYDSeal_", SPEC_SEAL_TURBINE_10),
}
DEFAULT = "turbine_10"


def corners(surface):
    """The 4 corners of the BYD Seal: 235/45 R19 front and rear."""
    r = surface.WHEEL_R
    y_f = surface.TRACK_F / 2.0 + 0.095
    y_r = surface.TRACK_R / 2.0 + 0.095
    return [
        ("FL", surface.FRONT_AXLE,  1, 0.235, r, 0.178, 176.0, y_f),
        ("FR", surface.FRONT_AXLE, -1, 0.235, r, 0.178, 184.0, y_f),
        ("RL", surface.REAR_AXLE,   1, 0.235, r, 0.170, 176.0, y_r),
        ("RR", surface.REAR_AXLE,  -1, 0.235, r, 0.170, 184.0, y_r),
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
