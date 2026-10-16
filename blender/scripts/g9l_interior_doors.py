"""XPeng G9L cabin: the door cards (g9l_interior's second half).

Layout read off c3_0003 (the front-left card from outside), c3_0001 and c3_0019, with x running
from the B-pillar (rear, -0.06) to the A-pillar side (front, +1.08):

    main          the bordeaux leather body of the card, flat and tall
    speaker       at the front of the top, a chrome-framed panel of silver mesh slats slanting up to
                  the A-pillar (the tweeter bank)
    pod           the armrest ridge across the middle, a chrome pill-shaped door pull and the small
                  window switches at its front end
    ambient       a purple light line under the shoulder
    lower         the black lower card with a long grille at the bottom
"""
import math

from carkit import mesh as M
from carkit.geom import Curve
from carkit.interior import fittings as F
from carkit.interior.sweep import grid_mesh, piping, smooth_path, cr_segments

import g9l_surface as S
import g9l_panels as PN
from cabin_parts import smooth as _smooth


def _belt_z(x):
    return S.section_v(max(-1.80, min(1.05, x)), PN.V_BELT(x))[1]


X_B = PN.X_BPILLAR(0.5)              # the B-pillar's shut line
Z_CARD_LO = 0.425                    # the cards run down to the sill
Z_LOWER_TOP = 0.660

DOOR_TH = Curve([(0.42, 0.150), (0.60, 0.172), (0.80, 0.178), (1.00, 0.160), (1.10, 0.128),
                 (1.20, 0.100)], mode="pchip")
BELT_LIFT = 0.0185


def _v_top_front():
    return PN.V_BELT(0.0) + 0.015


def front_card(side):
    from carkit.interior.door import DoorCard
    return DoorCard(S.BODY, lambda z: PN.X_DOOR_F(0.5) - 0.022, lambda z: X_B + 0.006, Z_CARD_LO,
                    _belt_z, DOOR_TH, v_top=_v_top_front(), side=side)


def build_doors(col, lib):
    made = []
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        dc = front_card(side)
        pre = "int_door_%s_" % tag
        xr = lambda z: X_B + 0.006
        xf = lambda z: PN.X_DOOR_F(0.5) - 0.022
        made.append(dc.belt_cap(pre + "Belt", col, lib["satin"], xr(0.95), xf(1.0), _belt_z,
                                mirror=False, lift=BELT_LIFT))
        made.append(dc.carrier(pre + "Carrier", col, lib["satin"], lambda x: Z_CARD_LO,
                               lambda x: _belt_z(x) - 0.002, x0=xr, x1=xf, back=0.016, nz=48,
                               mirror=False))
        # the black lower card with its long grille at the foot
        made.append(dc.band(pre + "Lower", col, lib["lower_card"], lambda x: Z_CARD_LO,
                            lambda x: Z_LOWER_TOP, x0=xr, x1=xf, nx=64, nz=12, mirror=False))
        made.append(dc.band(pre + "Grille", col, lib["speaker"], lambda x: 0.450, lambda x: 0.560,
                            proud=-0.006, x0=lambda z: 0.30, x1=lambda z: 0.90, nx=30, nz=6,
                            edge_round=0.004, mirror=False))
        # the red body, up to the belt
        made.append(dc.band(pre + "Main", col, lib["leather_door"], lambda x: Z_LOWER_TOP - 0.002,
                            lambda x: _belt_z(x) - 0.002, proud=0.002, x0=xr, x1=xf, nx=64, nz=18,
                            edge_round=0.004, mirror=False))
        # the tweeter bank at the front of the top: silver mesh slats in a chrome frame
        zt = lambda x: _belt_z(x) - 0.020
        made.append(dc.band(pre + "Speaker", col, lib["mesh_silver"], lambda x: zt(x) - 0.200, zt,
                            proud=0.006, x0=lambda z: 0.66, x1=lambda z: xf(z) - 0.005, nx=36, nz=8,
                            edge_round=0.003, mirror=False))
        for nm, zf in (("Hi", lambda x: zt(x) + 0.0), ("Lo", lambda x: zt(x) - 0.200)):
            pts = dc.curve([(x, zf(x)) for x in [0.66 + (xf(0.9) - 0.005 - 0.66) * k / 24.0
                                                 for k in range(25)]], proud=0.0075)
            made.append(piping(pre + "SpeakerFrame" + nm, pts, col, lib["chrome"], r=0.0015,
                               lateral=(0.0, 0.0, 1.0)))
        # the armrest ridge and its chrome pull
        made += _door_ridge(dc, pre + "Ridge", col, lib, side,
                            [(-0.020, 0.830), (0.150, 0.842), (0.340, 0.850), (0.600, 0.852)],
                            width=0.070, height=0.050)
        pull = F.round_slab(col, pre + "Pull", (0.380, side * (dc.skin_y(0.380, 0.880) - DOOR_TH(0.880) - 0.012), 0.884),
                            0.085, 0.036, 0.010, 0.016, lib["chrome"], tilt=0.0)
        made.append(pull)
        # the window switches: three small chrome toggles at the ridge's front end
        for k in range(3):
            xk = 0.560 + 0.034 * k
            yk = side * (dc.skin_y(xk, 0.870) - DOOR_TH(0.870) - 0.010)
            made.append(F.box(col, pre + "Key%d" % k, (xk, yk, 0.872), (0.020, 0.012, 0.012),
                              lib["chrome"], r=0.002))
        # the purple light line under the shoulder
        pts = dc.curve([(x, _belt_z(x) - 0.250) for x in [0.62 - 0.64 * k / 24.0 for k in range(25)]],
                       proud=0.008)
        made.append(piping(pre + "Ambient", pts, col, lib["ambient"], r=0.0018, lateral=(0.0, 0.0, 1.0)))
    made += build_rear_doors(col, lib)
    return made


def _door_ridge(dc, name, col, lib, side, path_xz, width=0.070, height=0.050, n=40, role="leather_door"):
    """A padded ridge along the card through side-elevation points (x, z of its top), its ends
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
    ob = grid_mesh(name, rows, col, lib[role])
    M.orient(ob.data, lambda c: (0.0, -side, 0.4))
    return [ob]


def _arch_front(z, margin=0.020):
    """The rear wheel opening's front edge at height z: the rear door's lower rear corner is cut away
    by it, so its card stops short of it."""
    B = S.BODY
    r = B.ARCH_R + 0.0021 + margin
    dz = max(0.0, z - B.WHEEL_R)
    return B.REAR_AXLE + math.sqrt(max(0.0, r * r - dz * dz)) if dz < r else -9.0


def rear_card(side):
    from carkit.interior.door import DoorCard
    th = Curve([(0.42, 0.130), (0.60, 0.152), (0.80, 0.160), (1.00, 0.140), (1.10, 0.115),
                (1.20, 0.090)], mode="pchip")
    return DoorCard(S.BODY, lambda z: X_B - 0.006,
                    lambda z: max(PN.X_DOOR_R(0.5) + 0.006, _arch_front(z)), Z_CARD_LO, _belt_z, th,
                    v_top=_v_top_front(), side=side)


def build_rear_doors(col, lib):
    """The rear cards (c3_0019, c3_0021): red body, black lower card, a ridge and a chrome pull,
    a light line."""
    made = []
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        dc = rear_card(side)
        pre = "int_rdoor_%s_" % tag
        xr, xf = dc.xr, dc.xf
        made.append(dc.band(pre + "Lower", col, lib["lower_card"], lambda x: Z_CARD_LO,
                            lambda x: Z_LOWER_TOP, x0=xr, x1=xf, nx=40, nz=10, mirror=False))
        made.append(dc.band(pre + "Main", col, lib["leather_door"], lambda x: Z_LOWER_TOP - 0.002,
                            lambda x: _belt_z(x) - 0.002, proud=0.002, x0=xr, x1=xf, nx=40, nz=16,
                            edge_round=0.004, mirror=False))
        made.append(dc.belt_cap(pre + "Belt", col, lib["satin"], xr(0.95) + 0.004, xf(0.95),
                                _belt_z, mirror=False, lift=BELT_LIFT))
        made.append(dc.carrier(pre + "Carrier", col, lib["satin"], lambda x: Z_CARD_LO,
                               lambda x: _belt_z(x) - 0.002, x0=xr, x1=xf, back=0.016, nz=48,
                               mirror=False))
        made += _door_ridge(dc, pre + "Ridge", col, lib, side,
                            [(-1.00, 0.835), (-0.78, 0.845), (-0.30, 0.852)], width=0.066, height=0.048)
        made.append(F.round_slab(col, pre + "Pull", (-0.46, side * (dc.skin_y(-0.46, 0.885) - dc.th(0.885) - 0.012), 0.886),
                                 0.080, 0.034, 0.010, 0.015, lib["chrome"], tilt=0.0))
        pts = dc.curve([(x, _belt_z(x) - 0.250) for x in [-0.20 - 0.80 * k / 24.0 for k in range(25)]],
                       proud=0.008)
        made.append(piping(pre + "Ambient", pts, col, lib["ambient"], r=0.0018, lateral=(0.0, 0.0, 1.0)))
    return made
