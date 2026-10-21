"""BYD Seal 07 EV cabin: the door cards (seal_interior's second half).

Layout read off Autohome Series 8462 photographs (c3_0001, c3_0003, c3_0005, c3_0011):
    wedge         Ocean wave metallic trim strip across the upper door with a silver accent line
    main          Cool light grey (Morning Shimmer Grey) Nappa leather body
    pod           Padded armrest with integrated grab handle and satin silver door release lever
    lower         Cool grey lower door card with molded door bin and woofer grille
"""
import math

from carkit import mesh as M
from carkit.geom import Curve
from carkit.interior import fittings as F
from carkit.interior.sweep import grid_mesh, piping, smooth_path, cr_segments

import seal_surface as S
import seal_panels as PN
from cabin_parts import smooth as _smooth


def _belt_z(x):
    return S.section_v(max(-1.70, min(0.98, x)), PN.V_BELT)[1]


X_B = PN.X_BPILLAR_F                 # -0.1001 m
Z_CARD_LO = 0.335


def _door_f_edge(z):
    return PN._DOOR_F_EDGE(z)


DOOR_TH = Curve([(0.40, 0.125), (0.60, 0.155), (0.75, 0.170), (0.90, 0.162), (1.00, 0.145),
                 (1.08, 0.105), (1.14, 0.072)], mode="pchip")


def _v_top_front():
    return PN.V_BELT + 0.015


def front_card(side):
    from carkit.interior.door import DoorCard
    return DoorCard(S.BODY, lambda z: _door_f_edge(z) - 0.022,
                    lambda z: X_B + 0.006, Z_CARD_LO, _belt_z, DOOR_TH,
                    v_top=_v_top_front(), side=side)


def _wedge_lo(x):
    t = _smooth((x + 0.08) / 1.00)
    return _belt_z(x) - (0.145 + 0.055 * t)


def _pod_top(x):
    return 0.795 + 0.030 * _smooth((x + 0.08) / 0.52)


Z_LOWER_TOP = 0.635
BELT_LIFT = 0.0185


def build_doors(col, lib):
    made = []
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        dc = front_card(side)
        pre = "int_door_%s_" % tag
        xr = lambda z: X_B + 0.006
        xf = lambda z: _door_f_edge(z) - 0.022
        made.append(dc.belt_cap(pre + "Belt", col, lib["satin"], xr(0.95), xf(1.0), _belt_z,
                                mirror=False, lift=BELT_LIFT))
        made.append(dc.carrier(pre + "Carrier", col, lib["satin"], lambda x: Z_CARD_LO,
                               lambda x: _belt_z(x) - 0.002, x0=xr, x1=xf, back=0.016, nz=48,
                               mirror=False))
        # Cool grey lower card
        made.append(dc.band(pre + "Lower", col, lib["leather_door"], lambda x: Z_CARD_LO,
                            lambda x: Z_LOWER_TOP, x0=xr, x1=xf, nx=64, nz=18, mirror=False))
        # Dynaudio speaker grille on lower door card
        made.append(dc.band(pre + "Woofer", col, lib["speaker"], lambda x: 0.420,
                            lambda x: 0.585, proud=-0.008,
                            x0=lambda z: 0.38 + 0.30 * (z - 0.42) / 0.165, x1=lambda z: 0.86 + 0.04 * (z - 0.42),
                            nx=30, nz=8, edge_round=0.006, mirror=False))
        # Main body in cool grey leather
        made.append(dc.band(pre + "Main", col, lib["leather_door"], lambda x: Z_LOWER_TOP - 0.002,
                            lambda x: _wedge_lo(x) + 0.002, proud=0.004, x0=xr, x1=xf, nx=64, nz=14,
                            mirror=False))
        # Upper wave trim strip
        made.append(dc.band(pre + "Wedge", col, lib["wood"], _wedge_lo, lambda x: _belt_z(x) - 0.002,
                            proud=-0.002, x0=xr, x1=lambda z: xf(z) - 0.02, nx=64, nz=8,
                            edge_round=0.004, mirror=False))
        # Silver trim piping under wave strip
        pts = dc.curve([(x, _wedge_lo(x) - 0.002) for x in [xr(0.9) + 0.02 + (xf(0.95) - 0.02 - xr(0.9)) * k / 40.0
                                                          for k in range(41)]], proud=0.0035)
        made.append(piping(pre + "Chrome", pts, col, lib["chrome"], r=0.0013, lateral=(0.0, 0.0, 1.0)))
        # Ambient light guide
        pts = dc.curve([(x, 0.695) for x in [0.44 - 0.50 * k / 24.0 for k in range(25)]], proud=0.012)
        made.append(piping(pre + "Ambient", pts, col, lib["ambient"], r=0.0016, lateral=(0.0, 0.0, 1.0)))
        # Silver tweeter grille near inner handle
        made.append(dc.band(pre + "Tweeter", col, lib["gunmetal"], lambda x: 0.890, lambda x: 0.945,
                            proud=0.004, x0=lambda z: 0.640, x1=lambda z: 0.745, nx=14, nz=4,
                            edge_round=0.004, mirror=False))
        # Padded armrest
        made += _door_armrest(dc, pre + "Pod", col, lib, side,
                              [(-0.050, 0.790), (0.090, 0.805), (0.245, 0.818), (0.400, 0.828), (0.575, 0.836)],
                              width=0.080, height=0.078, keep_front=True)
        made += _switch_pack(dc, pre + "Pack", col, lib, side)
    made += build_rear_doors(col, lib)
    return made


PACK_X = (0.330, 0.575)
PACK_Z = 0.836
PACK_PITCH = math.radians(-8.0)


def _switch_pack(dc, pre, col, lib, side):
    made = []
    cx = 0.5 * (PACK_X[0] + PACK_X[1])
    length, width, height = PACK_X[1] - PACK_X[0], 0.085, 0.042
    ya = dc.skin_y(PACK_X[0], PACK_Z) - dc.th(PACK_Z)
    yb = dc.skin_y(PACK_X[1], PACK_Z) - dc.th(PACK_Z)
    yaw = math.atan2(side * (yb - ya), PACK_X[1] - PACK_X[0])
    cyw, syw = math.cos(yaw), math.sin(yaw)
    y0 = 0.5 * (ya + yb)
    c = (cx, side * (y0 - 0.5 * width + 0.004), PACK_Z)
    p = PACK_PITCH
    cp, sp = math.cos(p), math.sin(p)
    made.append(F.box(col, pre, c, (length, width, height), lib["piano"], r=0.008, pitch=p, yaw=yaw))

    def at(s, t, n):
        xl, yl = s * cp + (0.5 * height + n) * sp, -side * t
        zl = -s * sp + (0.5 * height + n) * cp
        return (c[0] + xl * cyw - yl * syw, c[1] + xl * syw + yl * cyw, c[2] + zl)

    def key(name, s, t, size, mat, lift, r=0.0012):
        made.append(F.box(col, pre + name, at(s, t, lift + 0.5 * size[2]), size, mat, r=r, pitch=p, yaw=yaw))

    for j, t in enumerate((-0.014, 0.014)):
        key("_lock%d" % j, 0.098, t, (0.015, 0.015, 0.0035), lib["satin"], 0.0, 0.0008)
        key("_lockcap%d" % j, 0.098, t, (0.009, 0.009, 0.0012), lib["chrome"], 0.0035, 0.0004)

    for r, s in enumerate((0.000, -0.042)):
        for j, t in enumerate((-0.020, 0.020)):
            key("_win%d%d" % (r, j), s, t, (0.032, 0.036, 0.0045), lib["chrome"], 0.0, 0.0010)
            key("_wface%d%d" % (r, j), s, t, (0.024, 0.028, 0.0012), lib["piano"], 0.0045, 0.0003)
            key("_wbar%d%d" % (r, j), s - 0.002, t, (0.005, 0.020, 0.0030), lib["chrome"], 0.0057, 0.0010)
    return made


def _door_armrest(dc, name, col, lib, side, path_xz, width=0.070, height=0.050, n=40,
                  role="leather_door", keep_front=False):
    path = smooth_path([(x, 0.0, z) for (x, z) in path_xz], n + 1)
    rows = []
    for k, p in enumerate(path):
        s = k / float(n)
        e = min(1.0, (s if keep_front else min(s, 1.0 - s)) * 6.0)
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
    B = S.BODY
    r = B.ARCH_R + 0.0021 + margin
    dz = max(0.0, z - B.WHEEL_R)
    return B.REAR_AXLE + math.sqrt(max(0.0, r * r - dz * dz)) if dz < r else -9.0


def rear_card(side):
    from carkit.interior.door import DoorCard
    th = Curve([(0.40, 0.100), (0.60, 0.130), (0.75, 0.145), (0.90, 0.135), (1.05, 0.100),
                (1.20, 0.072), (1.30, 0.058)], mode="pchip")
    return DoorCard(S.BODY, lambda z: X_B - 0.006,
                    lambda z: max(PN._DOOR_R_EDGE(z) + 0.006, _arch_front(z)), Z_CARD_LO, _belt_z, th,
                    v_top=PN.V_BELT + 0.015, side=side)


def build_rear_doors(col, lib):
    made = []
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        dc = rear_card(side)
        pre = "int_rdoor_%s_" % tag
        xr, xf = dc.xr, dc.xf
        wl = lambda x: _belt_z(x) - 0.185
        made.append(dc.band(pre + "Lower", col, lib["leather_door"], lambda x: Z_CARD_LO,
                            lambda x: 0.655, x0=xr, x1=xf, nx=40, nz=16, mirror=False))
        made.append(dc.band(pre + "Main", col, lib["leather_door"], lambda x: 0.653,
                            lambda x: wl(x) + 0.002, proud=0.005, x0=xr, x1=xf, nx=40, nz=12,
                            mirror=False))
        made.append(dc.band(pre + "Wedge", col, lib["wood"], wl, lambda x: _belt_z(x) - 0.002,
                            proud=-0.002, x0=xr, x1=xf, nx=40, nz=8, edge_round=0.004, mirror=False))
        made.append(dc.belt_cap(pre + "Belt", col, lib["satin"], xr(0.95) + 0.004, xf(0.95),
                                _belt_z, mirror=False, lift=BELT_LIFT))
        made.append(dc.carrier(pre + "Carrier", col, lib["satin"], lambda x: Z_CARD_LO,
                               lambda x: _belt_z(x) - 0.002, x0=xr, x1=xf, back=0.016, nz=48,
                               mirror=False))
        pts = dc.curve([(x, wl(x) - 0.002) for x in [xr(0.9) - 0.02 + (xf(0.95) + 0.02 - xr(0.9)) * k / 30.0
                                                    for k in range(31)]], proud=0.0035)
        made.append(piping(pre + "Chrome", pts, col, lib["chrome"], r=0.0013, lateral=(0.0, 0.0, 1.0)))
        made += _door_armrest(dc, pre + "Pod", col, lib, side,
                              [(-0.95, 0.770), (-0.74, 0.785), (-0.52, 0.795)], width=0.068,
                              height=0.072)
        made.append(dc.band(pre + "Switches", col, lib["piano"], lambda x: 0.790, lambda x: 0.855,
                            proud=0.005, x0=lambda z: -0.38, x1=lambda z: -0.21, nx=10, nz=4,
                            edge_round=0.004, mirror=False))
        made.append(dc.band(pre + "Speaker", col, lib["speaker"], lambda x: 0.45, lambda x: 0.58,
                            proud=0.002, x0=lambda z: -0.76, x1=lambda z: -0.38, nx=14, nz=6,
                            mirror=False))
    return made
