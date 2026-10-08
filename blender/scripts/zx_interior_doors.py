"""Zeekr 7X cabin: the door cards (zx_interior's second half).

Layout read off c3_0003 (the front-left card seen from outside), c3_0001 and c3_0018, with
x running from the B-pillar (rear, -0.08) to the A-pillar side (front, +1.0):

    taupe rail      the top of the card under the glass; deeper at the rear
    dark strip      a short sweeping gloss strip with a rose-gold line, low on the rail
    cream panel     the big upholstered middle, its top edge low at the rear and rising to
                    the front, perforated
    pod             the padded armrest with the pull recess; at its front end the black
                    window-switch pack and a perforated speaker bar under it
    taupe lower     the lower card, with a darker speaker pocket leaning back in it
"""
import math

from carkit import mesh as M
from carkit.geom import Curve
from carkit.interior import fittings as F
from carkit.interior.sweep import grid_mesh, piping, smooth_path, cr_segments

import zx_surface as S
import zx_panels as PN
from zx_interior import _smooth


def _belt_z(x):
    return PN.BELT_Z(max(PN.X_DLO_TIP, min(0.80, x)))


# skin-to-card depth by height: the dash's ends (|y| 0.76) meet the card at ~0.78; the belt
# cap closes the 5-8 cm to the glass
DOOR_TH = Curve([(0.40, 0.115), (0.60, 0.150), (0.75, 0.172), (0.90, 0.168), (1.00, 0.148),
                 (1.08, 0.102), (1.14, 0.070)], mode="pchip")


def _v_top_front():
    return max(PN.V_BELT(x) for x in (-0.35, 0.0, 0.3, 0.7)) + 0.015


def front_card(side):
    from carkit.interior.door import DoorCard
    return DoorCard(S.BODY, lambda z: PN._DOOR_F_EDGE(z) - 0.022,
                    lambda z: PN._DOOR_B_EDGE(z) + 0.006, 0.40, _belt_z, DOOR_TH,
                    v_top=_v_top_front(), side=side)


def _cream_top(x):
    t = _smooth((x + 0.05) / 1.05)
    return _belt_z(x) - (0.185 - 0.095 * t)


def _pod_top(x):
    return 0.842 + 0.020 * _smooth((x + 0.10) / 0.50)


Z_LOWER_TOP = 0.690
# the door glass stands 10 mm above the skin's belt (zx_panels: V_BELT + 0.010): the cap's outer
# edge rises to it, or the slit shows the mirror's stalk through the window
BELT_LIFT = 0.0185


def _round_end(x_end, z_lo, z_hi, lead=0.07):
    """x0(z) for a band whose rear end is a round nose between z_lo(x) and z_hi(x) at x_end."""
    def f(z):
        a, b = z_lo(x_end + lead), z_hi(x_end + lead)
        m, h = 0.5 * (a + b), max(1e-4, 0.5 * (b - a))
        u = max(-1.0, min(1.0, (z - m) / h))
        return x_end + lead * (1.0 - math.sqrt(max(0.0, 1.0 - u * u)))
    return f


def build_doors(col, lib):
    made = []
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        dc = front_card(side)
        pre = "int_door_%s_" % tag
        xr = lambda z: PN._DOOR_B_EDGE(z) + 0.006
        xf = lambda z: PN._DOOR_F_EDGE(z) - 0.022
        made.append(dc.belt_cap(pre + "Belt", col, lib["satin"], xr(0.95), xf(1.0), _belt_z,
                                mirror=False, lift=BELT_LIFT))
        # fine rows and 16 mm behind the bands: a coarse carrier's chord cuts the curved flank at
        # the shoulder and pokes through the rail as black lens-shaped slits
        made.append(dc.carrier(pre + "Carrier", col, lib["satin"], lambda x: 0.40,
                               lambda x: _belt_z(x) - 0.002, x0=xr, x1=xf, back=0.016, nz=48,
                               mirror=False))
        # the taupe lower card, up to the pod
        made.append(dc.band(pre + "Lower", col, lib["leather_taupe"], lambda x: 0.40,
                            lambda x: Z_LOWER_TOP, x0=xr, x1=xf, nx=64, nz=18, mirror=False))
        # a speaker pocket, leaning back, in the lower card
        made.append(dc.band(pre + "Pocket", col, lib["leather_taupe"], lambda x: 0.425,
                            lambda x: 0.575, proud=-0.006,
                            x0=lambda z: 0.24 + 0.05 * (z - 0.425),
                            x1=lambda z: 0.86 + 0.02 * (z - 0.425), nx=30, nz=8,
                            edge_round=0.005, mirror=False))
        # the taupe rail under the glass: the whole top of the card
        made.append(dc.band(pre + "Rail", col, lib["leather_taupe"], _cream_top,
                            lambda x: _belt_z(x) - 0.002, proud=-0.002, x0=xr, x1=xf, nx=64,
                            nz=10, edge_round=0.006, mirror=False))
        # the cream upper panel, from the pod to the rail's lower edge
        made.append(dc.band(pre + "Cream", col, lib["leather_white"], _pod_top,
                            lambda x: _cream_top(x) + 0.002, proud=0.008,
                            x0=_round_end(-0.060, _pod_top, _cream_top), x1=xf, nx=64, nz=14,
                            mirror=False))
        # the dark strip with its rose-gold line, short and sweeping, low on the rail
        made.append(dc.band(pre + "Strip", col, lib["trim_dark"], lambda x: _belt_z(x) - 0.092,
                            lambda x: _belt_z(x) - 0.068, proud=0.006,
                            x0=lambda z: 0.24, x1=lambda z: 0.60, nx=40, nz=4, edge_round=0.003,
                            mirror=False))
        pts = dc.curve([(x, _belt_z(x) - 0.068) for x in [0.62 - 0.38 * k / 24.0
                                                          for k in range(25)]], proud=0.0075)
        made.append(piping(pre + "Rose", pts, col, lib["rose"], r=0.0013, lateral=(0.0, 0.0, 1.0)))
        # the ambient light guide along the pod's lower edge
        pts = dc.curve([(x, 0.700) for x in [0.46 - 0.54 * k / 24.0 for k in range(25)]],
                       proud=0.012)
        made.append(piping(pre + "Ambient", pts, col, lib["ambient"], r=0.0016,
                           lateral=(0.0, 0.0, 1.0)))
        # the window switches: a black gloss pack at the pod's front end, a speaker bar under it
        made.append(dc.band(pre + "Switches", col, lib["piano"], lambda x: 0.742,
                            lambda x: 0.835, proud=0.004, x0=lambda z: 0.520,
                            x1=lambda z: 0.700, nx=16, nz=5, edge_round=0.004, mirror=False))
        for k in range(4):
            xk = 0.552 + 0.040 * k
            yk = side * (dc.skin_y(xk, 0.788) - DOOR_TH(0.788) - 0.008)
            made.append(F.box(col, pre + "Key%d" % k, (xk, yk, 0.800), (0.026, 0.014, 0.012),
                              lib["satin"], r=0.002))
        made.append(dc.band(pre + "Speaker", col, lib["speaker"], lambda x: 0.690,
                            lambda x: 0.725, proud=0.003, x0=lambda z: 0.500, x1=lambda z: 0.720,
                            nx=24, nz=3, edge_round=0.0, mirror=False))
        # the armrest pod: a padded cream bar with the pull recess, swelling toward the front
        made += _door_armrest(dc, pre + "Pod", col, lib, side,
                              [(-0.040, 0.835), (0.150, 0.852), (0.340, 0.868), (0.480, 0.874)],
                              width=0.082, height=0.090)
    made += build_rear_doors(col, lib)
    return made


def _door_armrest(dc, name, col, lib, side, path_xz, width=0.070, height=0.050, n=40):
    """A padded bar along the card through side-elevation points (x, z of its top), its ends
    tapering into the card."""
    path = smooth_path([(x, 0.0, z) for (x, z) in path_xz], n + 1)
    rows = []
    for k, p in enumerate(path):
        s = k / float(n)
        e = min(1.0, min(s, 1.0 - s) * 6.0)
        e = e * e * (3 - 2 * e)
        w = 0.004 + (width - 0.004) * e
        x, z = p[0], p[2]
        y0 = dc.skin_y(x, z) - dc.th(z)
        prof = [(0.0, -height), (w * 0.55, -height * 0.92), (w * 0.95, -height * 0.55),
                (w, -0.012), (w * 0.9, -0.002), (w * 0.55, 0.0), (0.0, -0.003)]
        sec = cr_segments(prof, 4)
        rows.append([(x, side * (y0 - a), z + b) for (a, b) in sec])
    ob = grid_mesh(name, rows, col, lib["leather_white"])
    M.orient(ob.data, lambda c: (0.0, -side, 0.4))
    return [ob]


def _arch_front(z, margin=0.020):
    """The rear wheel opening's front edge at height z (carkit.cut.arch_outline: a semicircle
    about the wheel's centre, straight down below it): the rear door's lower rear corner is
    cut away by it (c3_0020), so its card stops short of it."""
    B = S.BODY
    r = B.ARCH_R + 0.0021 + margin
    dz = max(0.0, z - B.WHEEL_R)
    return B.REAR_AXLE + math.sqrt(max(0.0, r * r - dz * dz)) if dz < r else -9.0


def rear_card(side):
    from carkit.interior.door import DoorCard
    th = Curve([(0.40, 0.095), (0.60, 0.125), (0.75, 0.140), (0.90, 0.130), (1.05, 0.100),
                (1.20, 0.072), (1.30, 0.060)], mode="pchip")
    return DoorCard(S.BODY, lambda z: PN._DOOR_B_EDGE(z) - 0.006,
                    lambda z: max(PN._DOOR_R_EDGE(z) + 0.006, _arch_front(z)), 0.40, _belt_z, th,
                    v_top=max(PN.V_BELT(x) for x in (-1.39, -1.0, -0.4)) + 0.015, side=side)


def build_rear_doors(col, lib):
    """The rear cards (c3_0018): a taupe rail, a cream panel, a taupe lower card with a
    speaker pocket, a dark strip and the pod."""
    made = []
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        dc = rear_card(side)
        pre = "int_rdoor_%s_" % tag
        xr, xf = dc.xr, dc.xf
        rt = lambda x: _belt_z(x) - 0.150
        made.append(dc.band(pre + "Lower", col, lib["leather_taupe"], lambda x: 0.40,
                            lambda x: 0.700, x0=xr, x1=xf, nx=40, nz=16, mirror=False))
        made.append(dc.band(pre + "Rail", col, lib["leather_taupe"], rt,
                            lambda x: _belt_z(x) - 0.002, proud=-0.002, x0=xr, x1=xf, nz=8,
                            edge_round=0.006, mirror=False))
        made.append(dc.band(pre + "Cream", col, lib["leather_white"], lambda x: 0.700,
                            lambda x: rt(x) + 0.002, proud=0.007, x0=xr, x1=xf, nx=40, nz=12,
                            mirror=False))
        made.append(dc.belt_cap(pre + "Belt", col, lib["satin"], xr(0.95) + 0.004, xf(0.95),
                                _belt_z, mirror=False, lift=BELT_LIFT))
        # fine rows and 16 mm behind the bands: a coarse carrier's chord cuts the curved flank at
        # the shoulder and pokes through the rail as black lens-shaped slits
        made.append(dc.carrier(pre + "Carrier", col, lib["satin"], lambda x: 0.40,
                               lambda x: _belt_z(x) - 0.002, x0=xr, x1=xf, back=0.016, nz=48,
                               mirror=False))
        made.append(dc.band(pre + "Strip", col, lib["trim_dark"],
                            lambda x: _belt_z(x) - 0.105, lambda x: _belt_z(x) - 0.082,
                            proud=0.006, x0=lambda z: -0.70, x1=lambda z: -0.22, nx=24, nz=4,
                            edge_round=0.003, mirror=False))
        made += _door_armrest(dc, pre + "Pod", col, lib, side,
                              [(-1.00, 0.775), (-0.78, 0.790), (-0.55, 0.800)], width=0.070,
                              height=0.075)
        made.append(dc.band(pre + "Speaker", col, lib["speaker"], lambda x: 0.52, lambda x: 0.62,
                            proud=0.003, x0=lambda z: -0.80, x1=lambda z: -0.42, nx=14, nz=6,
                            mirror=False))
    return made
