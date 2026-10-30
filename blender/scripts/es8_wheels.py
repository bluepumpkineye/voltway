"""Nio ES8 wheels: the two 22 in wheels the all-new ES8 (NT2 platform) is shown on, both traced from photographs.

    multi22   the standard 22 in (265/40 R22) wheel of the Signature and Luxury trims: a diamond-cut face with twenty
              dark openings, ten bottle slots and ten funnel pockets alternating every 18 degrees, the bright spokes
              between them 3-5 degrees wide; red calipers; a dark cap with the Nio mark. Traced from the REAR wheel of
              the grey Signature car's side photograph (Autohome series 4427, spec 73547, imgs-4427-73547-1-x/11842784:
              ellipse ratio 0.976, axle corrected -3, 0 px, period 36.0 degrees). The openings are the dark regions of
              segment.cjs (lum 115-255, invert=1); the bottle slot's edges and the funnel's were read off the voted
              outline (see the polygons below).
    lanyue    the Lanyue (22 in forged, optional pack with Dawn Gold calipers): a mirror-polished face with eight
              dark pockets that open to the rim, and a large polished cap with a black Nio roundel. Traced from the
              maker's own close-up (blender/reference/nio-es8/official/lanyue_wheel.jpg: ellipse ratio 0.965, period
              45.0 degrees by period.cjs); the pocket is the dark class of segment.cjs (lum 0-75).

The four other wheels of the first build (a 20 in Star Sail, a 21 in Star Glow, a 21 in Carbon Blade and a 22 in Star
Shine) were stand-ins no photograph backs and are gone. A graphite ten-spoke wheel on a black Luxury car (imgs-4427-74331-
1-x/13279102) is not built: it is dark on dark and too little of it shows.

Polygons are (angle in degrees counter-clockwise from 3 o'clock, seen from outside, radius / lip radius).
"""
import copy
import math

from carkit.geom import Curve
from carkit.parts import wheels as W

LIP_22 = 0.2985                 # 22-inch rim lip radius (m) for 265/40 R22 (OD ~0.770 m)
TAB_22 = 0.965                  # the face's edge: outside it the machined flange ring

CALIPER = dict(span_deg=42.0, span_rear=36.0, r_inner=0.148, d_out=0.035, steps=16, groove=True)

# the dish (face depth below the flange plane by radius): flat, as photographed
DISH_22 = Curve([
    (0.000, 0.050), (0.085, 0.050), (0.115, 0.045), (0.150, 0.036),
    (0.190, 0.026), (0.230, 0.015), (0.265, 0.006), (0.290, 0.0018),
    (LIP_22, 0.0),
], mode="pchip")
DISH_LANYUE = Curve([
    (0.000, 0.040), (0.090, 0.040), (0.140, 0.034), (0.190, 0.026),
    (0.240, 0.016), (0.280, 0.007), (LIP_22, 0.0),
], mode="pchip")


def _bar(p, q, w):
    """A flat bar of half-width w from p to q (metres): one quad of an emblem."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln * w, dx / ln * w
    return [(p[0] + nx, p[1] + ny), (q[0] + nx, q[1] + ny), (q[0] - nx, q[1] - ny), (p[0] - nx, p[1] - ny)]


# the Nio mark on the cap: two nested chevrons, bright on the dark cap
NIO_MARK = dict(mat="machined", h=0.0128, quads=[
    _bar((-0.0115, -0.0030), (0.0, 0.0085), 0.0015), _bar((0.0, 0.0085), (0.0115, -0.0030), 0.0015),
    _bar((-0.0075, -0.0095), (0.0, -0.0020), 0.0013), _bar((0.0, -0.0020), (0.0075, -0.0095), 0.0013)])

# ========================================================================= 1. 22" multi-spoke (Signature / Luxury)
# one 36-degree repeat: the bottle slot (narrow at the rim, wide at the hub end) and the funnel pocket (wide at the rim,
# narrow at the hub), 17.9 degrees apart
SLOT = [(39.8, 0.950), (39.1, 0.916), (39.2, 0.875), (38.6, 0.780), (37.9, 0.641), (36.9, 0.530), (35.8, 0.411),
        (35.6, 0.360), (36.2, 0.320), (38.0, 0.305), (43.6, 0.298), (49.5, 0.305), (51.2, 0.325), (51.9, 0.389),
        (50.8, 0.466), (49.9, 0.530), (48.8, 0.749), (48.3, 0.790), (48.1, 0.880), (47.6, 0.945), (47.0, 0.950)]
POCKET = [(57.8, 0.948), (56.4, 0.940), (54.5, 0.936), (53.5, 0.922), (52.8, 0.904), (51.3, 0.900), (51.1, 0.848),
          (51.4, 0.784), (52.9, 0.630), (54.4, 0.504), (56.6, 0.404), (56.2, 0.366), (57.8, 0.328), (60.5, 0.305),
          (63.5, 0.302), (66.0, 0.318), (66.5, 0.350), (67.1, 0.393), (67.4, 0.454), (69.6, 0.564), (70.2, 0.636),
          (71.7, 0.797), (72.0, 0.856), (71.9, 0.880), (71.4, 0.905), (70.5, 0.908), (69.2, 0.926), (67.4, 0.934),
          (65.9, 0.946)]

SPEC_MULTI = W.preset(
    "blade_5", rim_d=2.0 * LIP_22, dish=DISH_22, pinstripe=False,
    flange_face=(1.0 - TAB_22) * LIP_22, roll_left=math.pi,
    tyre=dict(bulge=1.045, shoulder=0.016, ridge=True),
    hub=dict(depth=0.050, setback=0.008, cap_rise=0.0055, cap_r=0.032, cap_logo=NIO_MARK),
    lugs=dict(count=5, pcd_r=0.0580, r=0.0120, deg=18.0, rise=0.004, hidden=True),
    disc=dict(style="plain", inner_r=0.125, thickness=0.034),
    caliper=CALIPER,
    mats=dict(rim="wheel_black", lip="machined", lugs="wheel_black", cap="cap_black",
              disc="iron", barrel="wheel_black", accent="wheel_black"),
)
SPEC_MULTI["spokes"] = dict(
    style="traced", count=10, phase=0.0, depth=0.016, bevel=0.0016, mat="machined",
    r_in=0.038, r_out=TAB_22 * LIP_22, nr=16, seg=80, step_deg=1.5, step_r=0.025,
    windows=[SLOT, POCKET],
)
SPEC_MULTI["tyre_w"] = 0.265

# ========================================================================= 2. 22" Lanyue
# one 45-degree repeat: a pocket that opens up to the rim
LANYUE_POCKET = [(6.8, 0.960), (6.2, 0.948), (6.2, 0.929), (7.7, 0.854), (9.8, 0.782), (11.2, 0.748), (12.1, 0.736),
                 (13.0, 0.728), (14.8, 0.721), (20.0, 0.714), (27.1, 0.719), (28.8, 0.728), (30.0, 0.741),
                 (31.0, 0.762), (33.3, 0.835), (35.3, 0.932), (34.9, 0.956), (33.4, 0.960), (24.8, 0.960),
                 (22.9, 0.960), (11.4, 0.960), (7.6, 0.960)]

SPEC_LANYUE = W.preset(
    "blade_5", rim_d=2.0 * LIP_22, dish=DISH_LANYUE, pinstripe=False,
    flange_face=(1.0 - TAB_22) * LIP_22, roll_left=math.pi,
    tyre=dict(bulge=1.045, shoulder=0.016, ridge=True),
    # a large flat cap standing proud of the face, a black roundel in it with the mark
    hub=dict(depth=0.040, setback=0.008, cap_rise=0.0055,
             cap_pts=[(0.0, 0.0150), (0.060, 0.0146), (0.078, 0.0130), (0.0835, 0.0105)],
             cap_inner=dict(mat="wheel_cap", r=0.030, h=0.0154), cap_logo=dict(NIO_MARK, h=0.0158)),
    lugs=dict(count=5, pcd_r=0.0580, r=0.0120, deg=18.0, rise=0.004, hidden=True),
    disc=dict(style="plain", inner_r=0.125, thickness=0.034),
    caliper=CALIPER,
    mats=dict(rim="wheel_black", lip="polished", lugs="wheel_black", cap="polished",
              disc="iron", barrel="wheel_black", accent="wheel_black"),
)
SPEC_LANYUE["spokes"] = dict(
    style="traced", count=8, phase=0.0, depth=0.016, bevel=0.0016, mat="polished",
    r_in=0.038, r_out=TAB_22 * LIP_22, nr=16, seg=80, step_deg=1.5, step_r=0.025,
    windows=[LANYUE_POCKET],
)
SPEC_LANYUE["tyre_w"] = 0.265

# Map internal design ID -> (object prefix, spec dict)
DESIGNS = {
    "multi22": ("ES8_", SPEC_MULTI),
    "lanyue": ("ES8_Lanyue_", SPEC_LANYUE),
}
DEFAULT = "multi22"
SPEC = SPEC_MULTI


def corners(surface, tyre_w=0.265):
    """4 wheel corners (FL, FR, RL, RR) with ES8 track and axle positions."""
    r = surface.WHEEL_R
    outer_f = surface.TRACK_F / 2.0 + tyre_w / 2.0
    outer_r = surface.TRACK_R / 2.0 + tyre_w / 2.0
    return [
        ("FL", surface.FRONT_AXLE,  1, tyre_w, r, 0.192, 176.0, outer_f),
        ("FR", surface.FRONT_AXLE, -1, tyre_w, r, 0.192, 184.0, outer_f),
        ("RL", surface.REAR_AXLE,   1, tyre_w, r, 0.182, 176.0, outer_r),
        ("RR", surface.REAR_AXLE,  -1, tyre_w, r, 0.182, 184.0, outer_r),
    ]


def build_design(collection, surface, lib, name):
    prefix, spec = DESIGNS[name]
    tyre_w = spec.get("tyre_w", 0.265)
    return W.build_set(collection, prefix, lib, spec, corners(surface, tyre_w=tyre_w))


def build_all(collection, surface, lib):
    """Build the car's default wheels."""
    return build_design(collection, surface, lib, DEFAULT)


def build_options(collection, surface, lib):
    """Build every non-default wheel design into the collection for multi-wheel export."""
    made = []
    for name in DESIGNS:
        if name != DEFAULT:
            made += build_design(collection, surface, lib, name)
    return made
