"""SU7 Ultra nose and tail caps - the curves of its two WrapCaps.

The cap maths lives in carkit.body.caps (WrapCap): a (w, v) patch per end,
joined to the flank along the bumper shut line and blended G1 into it. This
module holds the SU7's four curves per end, builds the caps and the combined
CarBody, and keeps the old function API (cap_point(w, v, front), ...).

    C(w, v)     v = the same section parameter as the body loft
                    (0 = underbody centreline, 1 = top centreline)
                w = 1 at the shut line where the cap meets the loft,
                    0 on the car's centreline plane

The join is a curve in v, not a constant: the bumper shut line on a real car
runs high at the hood, forward-low at the valance and tucks back at mid height.
Making it follow that line means the cap boundary IS the panel gap.

The terminal point for a given v is found by remapping the join ring's height
onto the centreline profile's height range, so parameter lines run nearly
horizontal - a fairer surface, and what lets cap_x_at place details
accurately. WRAP is an authored monotone curve so the corner radius can be
tuned against the reference photograph.
"""
import su7_surface as S
from carkit.geom import Curve
from carkit.body import WrapCap, CarBody

# ---------------------------------------------------------------- shut lines
# x of the cap/flank joint as a function of section parameter v.
JOIN_F = Curve([
    (0.00, 2.238), (0.08, 2.214), (0.18, 2.168), (0.30, 2.116),
    (0.42, 2.082), (0.52, 2.074), (0.62, 2.096), (0.72, 2.146),
    (0.82, 2.212), (0.91, 2.280), (1.00, 2.322),
])

JOIN_R = Curve([
    (0.00, -2.212), (0.10, -2.186), (0.22, -2.140), (0.34, -2.102),
    (0.46, -2.078), (0.56, -2.074), (0.66, -2.092), (0.76, -2.132),
    (0.86, -2.186), (0.94, -2.238), (1.00, -2.268),
])

# ------------------------------------------- centreline profiles, x given z
# The forward-most point of the whole car is the peak of this curve, at about
# z = 0.60 - that peak at mid height is what makes the nose wrap instead of
# terminating in a face.
NOSE_X_OF_Z = Curve([
    # The lower bumper stands nearly upright under the plate. Tucked back to
    # 2.30 at the bottom it left 0.3 m of splitter deck showing ahead of the
    # black intake, where the car shows a lip of ~0.15 m.
    (0.150, 2.3800), (0.200, 2.3980), (0.250, 2.4120), (0.300, 2.4250),
    (0.375, 2.4400), (0.450, 2.4520), (0.525, 2.4620), (0.600, 2.4700),
    (0.650, 2.4670), (0.690, 2.4560), (0.715, 2.4420), (0.735, 2.4180),
    (0.745, 2.3950),
])
NOSE_Z_LO, NOSE_Z_HI = 0.118, 0.745

TAIL_X_OF_Z = Curve([
    # The production Ultra is 5070 mm long: the MIIT filing gives overhangs
    # of 1007 mm front and 1063 mm rear (5115 mm is the filing's alternative,
    # with a 1108 mm rear overhang). From the splitter tip at +2.5575 the tail
    # ends at -2.5125: the black lower bumper, standing 10 mm proud of this surface
    # (su7_panels.build_rear). From there the face stands nearly upright: the
    # plate and reversing camera are 60-90 mm behind the wordmark in all three
    # rear photographs (bundle-adjusted, scratchpad rear/bundle.py). The first
    # cut bulged 45 mm further, at mid height, and rolled away above and below
    # - the "big round bottom". Above the light bar the lid band is concave
    # under a lip that overhangs it by ~15 mm. PCHIP: the lip is a real local
    # extremum, and a C2 spline rings on it.
    (0.132, -2.3650), (0.180, -2.4280), (0.235, -2.4640), (0.300, -2.4860),
    (0.375, -2.4980), (0.455, -2.5025), (0.535, -2.5020), (0.600, -2.4990),
    (0.680, -2.4940), (0.760, -2.4830), (0.800, -2.4750), (0.860, -2.4580),
    (0.890, -2.4480), (0.915, -2.4380), (0.940, -2.4320), (0.965, -2.4360),
    (0.980, -2.4440), (0.990, -2.4500),
], mode="pchip")
# The lip sits ~1.0 m up: 0.47 m above the plate's top edge in every rear
# photograph, with the plate spanning z 0.39-0.53.
TAIL_Z_LO, TAIL_Z_HI = 0.132, 0.990

# ------------------------------------------------------------- wrap blending
# g(w): 0 at the centreline, 1 at the shut line. Flat across the middle of the
# face, turning hard near w = 1 so the cap leaves the flank close to tangent.
# A plain w**2 meets the loft at roughly 45 degrees and leaves a crease ring
# right around the nose.
WRAP = Curve([
    # Rounder in plan than the first cut. Through the matched camera the
    # nose's side silhouette at bumper height sits 0.1 m further back than
    # the old, nearly flat face put it; the last few percent still turn hard
    # so the cap leaves the flank close to tangent.
    (0.00, 0.000), (0.15, 0.022), (0.30, 0.085), (0.45, 0.190),
    (0.60, 0.320), (0.72, 0.440), (0.82, 0.560), (0.90, 0.680),
    (0.95, 0.790), (0.98, 0.870), (0.995, 0.930), (1.00, 1.000),
])

# The tail is rounder in plan than the nose, but less than the first cut's:
# the side photograph's tail outline is formed where the surface faces 18 deg
# off rearward, which only bounds the corners (g(w) >= 0.727 w - 0.134 with
# the tail at -2.5125). Halfway between the two keeps the face broad and the
# corners taut, instead of one continuous round bottom.
TAIL_WRAP = Curve([
    (0.00, 0.000), (0.15, 0.024), (0.30, 0.092), (0.45, 0.205),
    (0.60, 0.335), (0.72, 0.445), (0.82, 0.555), (0.90, 0.665),
    (0.95, 0.775), (0.98, 0.865), (0.995, 0.930), (1.00, 1.000),
])

# ------------------------------------------------------------------ the caps
_SLOPE = {}                  # shared by both ends, as the SU7 was built
NOSE = WrapCap(S.BODY, front=True, join=JOIN_F, x_of_z=NOSE_X_OF_Z,
               z_lo=NOSE_Z_LO, z_hi=NOSE_Z_HI, wrap=WRAP, slope_cache=_SLOPE)
TAIL = WrapCap(S.BODY, front=False, join=JOIN_R, x_of_z=TAIL_X_OF_Z,
               z_lo=TAIL_Z_LO, z_hi=TAIL_Z_HI, wrap=TAIL_WRAP, slope_cache=_SLOPE)
BODY = CarBody(S.BODY, NOSE, TAIL, flank_x_range=(-2.45, 2.40))


def _cap(front):
    return NOSE if front else TAIL


# The module's function API, as the SU7 modules call it.
def tip_at(v, front=True):
    return _cap(front).tip_at(v)


def cap_point(w, v, front=True):
    return _cap(front).point(w, v)


def cap_normal(w, v, front=True, h=2.5e-3):
    return _cap(front).normal(w, v, h)


def cap_offset(w, v, dist, front=True):
    return _cap(front).offset(w, v, dist)


def v_at_cap_z(z, front=True, w=0.0, iters=30):
    return _cap(front).v_at_z(z, w, iters)


def cap_wv_at(y, z, front=True, passes=5):
    return _cap(front).wv_at(y, z, passes)


def cap_x_at(y, z, front=True):
    return _cap(front).x_at(y, z)


def cap_half_width(z, front=True):
    return _cap(front).half_width(z)


def dims_report():
    return BODY.dims_report()
