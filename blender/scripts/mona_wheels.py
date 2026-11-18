"""XPeng Mona L05 (小鹏MONA L05) OEM wheel suite:

All three factory wheels verified from XPeng specs & Autohome series 8662 4K reference
photographs (door-jamb tyre placard confirms 245/45 R20 & 225/60 R18 fitments):

  blade20   20" Diamond-Cut Five-V (245/45 R20, Goodyear ElectricDrive, lime caliper).
            Refined from car_blade20_L_11.jpg & blade20_0036.jpg: gloss-black structural
            spoke casting & deep hub with machined diamond-cut V inlays, teardrop darts,
            continuous silver outer rim ring, domed black lug nuts & XPeng X cap emblem.
  roam20    20" ROAM Aero Sport (245/45 R20, Goodyear ElectricDrive, teal/violet caliper).
            Traced from car_roam_purple_L_87.jpg (unwarped + 5-fold polar segmented) &
            roam20_0306.jpg: gloss-black directional frame with continuous black flange,
            recessed satin-black outer aero flaps, machined asymmetrical L-boomerang spoke +
            shark-fin delta hook, dual cooling slots & 5-petal black center hub + X cap.
  aero18    18" Low-Drag Aero (225/60 R18, Linglong Sport Master e, silver caliper).
            Traced from car_aero18_silver_L_95.jpg & aero18_0664/0674/0676.jpg: compact
            18" rim (LIP_18 = 0.2521 m) keeping identical 0.354 m outer tyre radius with
            taller 60-series sidewall; continuous machined outer lip, swept blade spoke &
            silver corner wedge inlaid over a stepped gloss-black / satin-black aero cover.

Angles are degrees CCW from 3 o'clock seen from outside on the left wheel (`roll_left=math.pi`).
Both left and right sides use the same non-handed OEM casting (confirmed on L/R car shots).
"""
import math

from carkit.geom import Curve
from carkit.parts import wheels as W

# ----------------------------------------------------------------------- dimensions & curves
LIP_20 = 0.2775          # 20" rim lip radius (m): 254 mm bead + flange
LIP_18 = 0.2521          # 18" rim lip radius (m): 20" minus 1" radius (0.0254 m); ratio 0.354/0.2521 = 1.404
K_ROAM = 1.028           # roam20 unwarped image pixel lip (1.028) -> true 20" lip (1.000)

CALIPER_20 = dict(span_deg=40.0, span_rear=36.0, r_inner=0.128, d_out=0.032, steps=16, groove=True)
CALIPER_18 = dict(span_deg=32.0, span_rear=28.0, r_inner=0.118, r_out=0.016, rim_clear=0.030,
                  d_out=0.026, bulge=0.008, steps=16, groove=True)

DISH_20 = Curve([
    (0.000, 0.0640), (0.086, 0.0640), (0.102, 0.0580), (0.128, 0.0430),
    (0.158, 0.0280), (0.190, 0.0160), (0.222, 0.0075), (0.252, 0.0025),
    (LIP_20, 0.0),
], mode="pchip")

DISH_ROAM = Curve([
    (0.000, 0.0600), (0.082, 0.0600), (0.100, 0.0530), (0.126, 0.0380),
    (0.156, 0.0240), (0.188, 0.0135), (0.220, 0.0065), (0.252, 0.0020),
    (LIP_20, 0.0),
], mode="pchip")

DISH_18 = Curve([
    (0.000, 0.0580), (0.076, 0.0580), (0.094, 0.0510), (0.118, 0.0370),
    (0.145, 0.0235), (0.175, 0.0130), (0.205, 0.0060), (0.232, 0.0020),
    (LIP_18, 0.0),
], mode="pchip")


def _arc(a0, a1, r, step=4.0):
    n = max(2, int(math.ceil(abs(a1 - a0) / step)))
    return [(round(a0 + (a1 - a0) * i / n, 2), r) for i in range(n + 1)]


def _norm(pts, k=1.0):
    return [(a, round(r / k, 4)) for (a, r) in pts]


def _cap_x_logo(scale=1.0, h=0.0118, mat="wheel_silver"):
    """XPeng butterfly X emblem on the center cap: two facing chevron wings with a subtle center pinch."""
    s = scale
    left_top = [(-0.0175 * s, 0.0098 * s), (-0.0102 * s, 0.0102 * s),
                (-0.0014 * s, 0.0010 * s), (-0.0062 * s, 0.0002 * s)]
    left_bot = [(-0.0175 * s, -0.0098 * s), (-0.0062 * s, -0.0002 * s),
                (-0.0014 * s, -0.0010 * s), (-0.0102 * s, -0.0102 * s)]
    right_top = [(-x, y) for (x, y) in reversed(left_top)]
    right_bot = [(-x, y) for (x, y) in reversed(left_bot)]
    return dict(mat=mat, h=h, quads=[left_top, left_bot, right_top, right_bot])


# ----------------------------------------------------------------------- 1. blade20 (default 20" Five-V)
BLADE_TAB = 0.965

# Wide cooling window between adjacent V's (335/360 = +49..93) and narrow V slot (30..48)
BLADE_WIN_WIDE = [
    (56.2, 0.930), *_arc(59.0, 88.0, 0.940, 5.0), (90.2, 0.935),
    (91.5, 0.770), (93.2, 0.630), (90.5, 0.460), (86.0, 0.365),
    *_arc(83.0, 61.0, 0.335, 5.0),
    (58.0, 0.350), (50.2, 0.420), (52.2, 0.560), (54.0, 0.720),
]
BLADE_WIN_NARROW = [
    (30.6, 0.932), *_arc(33.5, 45.5, 0.940, 4.0), (48.2, 0.932),
    (47.2, 0.800), (45.2, 0.640), (42.8, 0.500), (40.2, 0.436),
    (38.2, 0.436), (36.0, 0.490), (34.2, 0.620), (32.4, 0.780),
]

# Diamond-cut machined silver inlay: V-spoke pair + short teardrop dart beside wide window.
# Outer arm ends overrun BLADE_TAB (1.025) so they merge seamlessly into `lip="wheel_silver"`.
BLADE_V_INLAY = [
    (35.7, 0.340), (37.0, 0.329), (39.3, 0.323), (42.6, 0.322), (44.4, 0.326), (46.2, 0.336),
    (47.7, 0.374), (49.6, 0.446), (51.4, 0.558), (53.1, 0.699), (54.9, 0.950), (56.2, 1.025),
    (49.8, 1.025), (49.1, 0.851), (47.9, 0.736), (45.7, 0.593), (43.3, 0.499), (41.4, 0.446),
    (40.1, 0.433), (38.1, 0.428), (36.6, 0.435), (35.8, 0.453), (33.1, 0.564), (31.7, 0.649),
    (30.3, 0.769), (28.8, 1.025), (26.5, 1.025), (27.8, 0.796), (29.4, 0.610), (31.2, 0.493),
    (32.6, 0.425), (34.0, 0.376),
]
BLADE_DART_INLAY = [
    (91.5, 1.025), (92.1, 0.949), (93.1, 0.743), (96.3, 0.675), (97.0, 0.665),
    (97.5, 0.663), (98.2, 0.673), (98.2, 0.695), (97.6, 0.833), (97.3, 1.025),
]

SPEC_BLADE = W.preset(
    "blade_5", rim_d=2.0 * LIP_20, dish=DISH_20, pinstripe=False,
    flange_face=(1.0 - BLADE_TAB) * LIP_20, roll_left=math.pi,
    tyre=dict(bulge=1.050, shoulder=0.018, ridge=True),
    hub=dict(depth=0.0640, setback=0.008, cap_rise=0.0055, cap_r=0.032,
             cap_logo=_cap_x_logo(1.0, h=0.0118, mat="wheel_silver")),
    lugs=dict(count=5, pcd_r=0.0658, r=0.0145, deg=3.5, rise=0.004, dome=0.0085),
    disc=dict(style="plain", inner_r=0.112, thickness=0.032),
    caliper=CALIPER_20,
    mats=dict(rim="wheel_black", lip="wheel_silver", lugs="wheel_black", cap="wheel_black",
              disc="iron", barrel="black_trim"),
)
SPEC_BLADE["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.018, bevel=0.0020, mat="wheel_black",
    r_in=0.034, r_out=BLADE_TAB * LIP_20, nr=16, seg=72, step_deg=2.2, step_r=0.025,
    windows=[BLADE_WIN_WIDE, BLADE_WIN_NARROW],
    lug_holes=dict(deg=3.5, pcd=0.0658, r=0.0185, count=5),
    inlay=dict(mat="wheel_silver", polys=[BLADE_V_INLAY, BLADE_DART_INLAY], lift=0.0004),
)


# ----------------------------------------------------------------------- 2. roam20 (20" ROAM Aero Sport)
ROAM_TAB = 0.992

# All raw radii normalized by K_ROAM (1.028) so rim bead sits cleanly at 1.000
ROAM_WIN_MAIN = _norm([
    (32.5, 0.935), *_arc(35.0, 41.0, 0.935, 3.0), (47.0, 0.875), (55.5, 0.795),
    (64.5, 0.720), (58.5, 0.575), (52.5, 0.455), (47.5, 0.415), (41.5, 0.445),
    (37.8, 0.545), (34.2, 0.675), (32.2, 0.820),
], K_ROAM)

ROAM_WIN_INNER = _norm([
    (70.5, 0.615), (86.0, 0.545), (89.0, 0.530), (89.2, 0.445), (87.0, 0.418),
    (78.0, 0.425), (69.5, 0.460), (66.0, 0.515),
], K_ROAM)

# Cutout in the front gloss-black frame to expose the recessed satin-black aero flap behind it
ROAM_AERO_CUT = _norm([
    *_arc(54.4, 84.5, 1.005, 4.0), (85.4, 0.932), (87.2, 0.768), (85.2, 0.746),
    (80.5, 0.758), (73.0, 0.778), (62.7, 0.836), (58.0, 0.905), (54.2, 0.995),
], K_ROAM)

ROAM_BOOMERANG_INLAY = _norm([
    (24.3, 1.005), (24.4, 0.966), (25.3, 0.899), (26.7, 0.765), (28.1, 0.655),
    (30.2, 0.545), (32.7, 0.466), (35.3, 0.399), (38.4, 0.352), (40.8, 0.326),
    (43.2, 0.320), (44.8, 0.328), (44.6, 0.352), (43.0, 0.405), (39.5, 0.474),
    (35.4, 0.584), (33.2, 0.676), (30.8, 0.798), (29.8, 0.921), (29.1, 0.975),
    (29.2, 1.008), (34.0, 1.010), (39.0, 1.010), (43.4, 0.990), (47.6, 0.934),
    (54.2, 0.859), (60.5, 0.802), (67.5, 0.747), (74.1, 0.678), (80.2, 0.621),
    (86.4, 0.588), (89.6, 0.582), (90.7, 0.590), (89.4, 0.650), (88.3, 0.706),
    (85.3, 0.728), (79.5, 0.738), (72.0, 0.760), (65.0, 0.785), (58.0, 0.835),
    (51.0, 0.902), (44.0, 0.992), (41.6, 1.012), *_arc(40.0, 26.0, 1.012, 3.0),
    (24.2, 1.010),
], K_ROAM)

SPEC_ROAM = W.preset(
    "blade_5", rim_d=2.0 * LIP_20, dish=DISH_ROAM, pinstripe=False,
    flange_face=(1.0 - ROAM_TAB) * LIP_20, roll_left=math.pi,
    tyre=dict(bulge=1.050, shoulder=0.018, ridge=True),
    hub=dict(depth=0.0600, setback=0.008, cap_rise=0.0055, cap_r=0.032,
             cap_logo=_cap_x_logo(0.96, h=0.0118, mat="wheel_silver")),
    lugs=dict(count=5, pcd_r=0.0620, r=0.0130, deg=38.0, rise=0.004, dome=0.0085),
    disc=dict(style="plain", inner_r=0.112, thickness=0.032),
    caliper=CALIPER_20,
    mats=dict(rim="wheel_black", lip="wheel_black", lugs="wheel_black", cap="wheel_black",
              disc="iron", barrel="black_trim"),
)
SPEC_ROAM["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.018, bevel=0.0018, mat="wheel_black",
    r_in=0.034, r_out=ROAM_TAB * LIP_20, nr=18, seg=72, step_deg=2.0, step_r=0.025,
    windows=[ROAM_WIN_MAIN, ROAM_WIN_INNER, ROAM_AERO_CUT],
    lug_holes=dict(deg=38.0, pcd=0.0620, r=0.0165, count=5),
    inlay=dict(mat="wheel_silver", polys=[ROAM_BOOMERANG_INLAY], lift=0.0004),
    layers=[dict(mat="aero_satin", dz=-0.0045, depth=0.008, bevel=0.0010,
                 r_in=0.40 * LIP_20, windows=[ROAM_WIN_MAIN, ROAM_WIN_INNER])],
)


# ----------------------------------------------------------------------- 3. aero18 (18" Low-Drag Aero)
AERO_TAB = 0.946

AERO_WIN_MAIN = [
    (60.2, 0.892), *_arc(64.0, 79.0, 0.895, 5.0), (82.5, 0.885), (81.0, 0.780),
    (77.0, 0.650), (73.0, 0.520), (71.5, 0.448), *_arc(69.0, 60.0, 0.445, 3.0),
    (57.2, 0.465), (56.8, 0.580), (58.2, 0.730),
]

# Stepped matte/satin-black aero cover panel recessed behind the gloss-black bezel
AERO_SATIN_CUT = [
    *_arc(44.5, 55.5, 0.902, 4.0), (54.2, 0.730), (53.2, 0.560), (53.5, 0.440),
    (44.0, 0.480), (36.5, 0.560), (31.5, 0.655), (34.0, 0.710), (39.5, 0.810),
]

# Continuous diamond-cut silver spoke + corner wedge; outer points extend cleanly into `lip="wheel_silver"`
AERO_SILVER_INLAY = [
    (16.6, 1.025), (18.6, 0.914), (20.8, 0.851), (23.5, 0.784), (25.6, 0.740),
    (28.6, 0.685), (29.4, 0.677), (30.8, 0.681), (31.6, 0.674), (32.1, 0.674),
    (35.1, 0.720), (38.7, 0.794), (43.4, 0.918), (44.3, 0.934), (45.6, 0.948),
    (46.8, 0.968), (50.8, 0.969), (69.9, 0.974), (78.5, 0.969), (80.1, 0.964),
    (80.9, 0.956), (83.4, 0.864), (86.5, 0.770), (89.9, 0.688), (93.5, 0.618),
    (97.7, 0.554), (104.0, 0.486), (108.6, 0.449), (114.9, 0.412), (119.0, 0.393),
    (125.0, 0.371), (132.9, 0.349), (140.1, 0.338), (154.5, 0.332), (162.1, 0.337),
    (167.8, 0.347), (169.3, 0.368), (168.1, 0.377), (166.5, 0.382), (155.9, 0.374),
    (147.1, 0.377), (140.6, 0.386), (132.1, 0.404), (126.0, 0.425), (120.6, 0.449),
    (117.1, 0.469), (109.9, 0.524), (102.9, 0.593), (98.7, 0.656), (95.4, 0.711),
    (91.7, 0.805), (87.7, 0.939), (86.4, 0.973), (85.0, 1.025),
    *_arc(83.0, 18.0, 1.025, 4.0),
]

SPEC_AERO = W.preset(
    "blade_5", rim_d=2.0 * LIP_18, dish=DISH_18, pinstripe=False,
    flange_face=(1.0 - AERO_TAB) * LIP_18, roll_left=math.pi,
    tyre=dict(bulge=1.062, shoulder=0.022, ridge=True),
    hub=dict(depth=0.0580, setback=0.008, cap_rise=0.0055, cap_r=0.031,
             cap_logo=_cap_x_logo(0.95, h=0.0118, mat="wheel_silver")),
    lugs=dict(count=5, pcd_r=0.0658, r=0.0110, deg=6.0, rise=0.001, dome=0.0065),
    disc=dict(style="plain", inner_r=0.106, thickness=0.028),
    caliper=CALIPER_18,
    mats=dict(rim="wheel_black", lip="wheel_silver", lugs="wheel_black", cap="wheel_black",
              disc="iron", barrel="black_trim"),
)
SPEC_AERO["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.016, bevel=0.0018, mat="wheel_black",
    r_in=0.032, r_out=AERO_TAB * LIP_18, nr=18, seg=72, step_deg=2.0, step_r=0.025,
    windows=[AERO_WIN_MAIN, AERO_SATIN_CUT],
    lug_holes=dict(deg=6.0, pcd=0.0658, r=0.0155, count=5),
    inlay=dict(mat="wheel_silver", polys=[AERO_SILVER_INLAY], lift=0.0003),
    layers=[dict(mat="aero_satin", dz=-0.0040, depth=0.008, bevel=0.0010,
                 r_in=0.38 * LIP_18, windows=[AERO_WIN_MAIN])],
)


# ----------------------------------------------------------------------- the set
DESIGNS = {
    "blade20": ("MONA_", SPEC_BLADE),
    "roam20": ("MONA_Roam_", SPEC_ROAM),
    "aero18": ("MONA_Aero_", SPEC_AERO),
}
DEFAULT = "blade20"


def corners(surface, design=DEFAULT):
    tyre_w = 0.225 if design == "aero18" else 0.245
    disc_f, disc_r = (0.150, 0.144) if design == "aero18" else (0.160, 0.154)
    return [
        ("FL", surface.FRONT_AXLE, 1, tyre_w, surface.WHEEL_R, disc_f, 350.0, 0.9425),
        ("FR", surface.FRONT_AXLE, -1, tyre_w, surface.WHEEL_R, disc_f, 10.0, 0.9425),
        ("RL", surface.REAR_AXLE, 1, tyre_w, surface.WHEEL_R, disc_r, 190.0, 0.9515),
        ("RR", surface.REAR_AXLE, -1, tyre_w, surface.WHEEL_R, disc_r, 170.0, 0.9515),
    ]


def build_design(collection, surface, lib, name):
    prefix, spec = DESIGNS[name]
    return W.build_set(collection, prefix, lib, spec, corners(surface, name))


def build_all(collection, surface, lib):
    return build_design(collection, surface, lib, DEFAULT)


def build_options(collection, surface, lib):
    made = []
    for name in DESIGNS:
        if name != DEFAULT:
            made += build_design(collection, surface, lib, name)
    return made
