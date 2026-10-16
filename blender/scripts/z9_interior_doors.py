"""Denza Z9 cabin: the door cards (z9_interior's second half).

Layout read off c3_0003 (the front-left card seen from outside), c3_0001 and c3_0016, with x
running from the B-pillar (rear, -0.145) to the A-pillar side (front, +1.0):

    wedge         a brushed rose-bronze strip across the upper third, its lower edge a long swoop
                  with a chrome line under it; at the front end a black glass monitor (the
                  side-mirror camera's display) in the corner by the A-pillar
    main          the mauve leather body of the card, with a deep sweep down to the lower card
    pod           the padded armrest, a sweeping brown bar with a chrome edge, the black
                  switch pack at its front end and a small silver speaker grille above it
    lower         the brown lower card with a large dark woofer pocket leaning back in it
"""
import math

from carkit import mesh as M
from carkit.geom import Curve
from carkit.interior import fittings as F
from carkit.interior.sweep import grid_mesh, piping, smooth_path, cr_segments

import z9_surface as S
import z9_panels as PN
from cabin_parts import smooth as _smooth


def _belt_z(x):
    return S.section_v(max(-1.75, min(1.0, x)), PN.V_BELT)[1]


X_B = PN.X_BPILLAR_F                 # the B-pillar's shut line
Z_CARD_LO = 0.345                    # the cards run down to the sill


def _door_f_edge(z):
    return PN._DOOR_F_EDGE(z)


# skin-to-card depth by height (z): the dash's ends (|y| 0.765) meet the card at ~0.78; the belt cap
# closes the gap to the glass
DOOR_TH = Curve([(0.40, 0.130), (0.60, 0.160), (0.75, 0.178), (0.90, 0.170), (1.00, 0.150),
                 (1.08, 0.110), (1.14, 0.075)], mode="pchip")


def _v_top_front():
    return PN.V_BELT + 0.015


def front_card(side):
    from carkit.interior.door import DoorCard
    return DoorCard(S.BODY, lambda z: _door_f_edge(z) - 0.022,
                    lambda z: X_B + 0.006, Z_CARD_LO, _belt_z, DOOR_TH,
                    v_top=_v_top_front(), side=side)


# the wedge's lower edge: from 20 cm under the belt at the front to 15 cm at the rear
def _wedge_lo(x):
    t = _smooth((x + 0.10) / 1.05)
    return _belt_z(x) - (0.150 + 0.060 * t)


def _pod_top(x):
    return 0.800 + 0.030 * _smooth((x + 0.10) / 0.55)


Z_LOWER_TOP = 0.640
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
        # the brown lower card, up to the pod
        made.append(dc.band(pre + "Lower", col, lib["leather_door"], lambda x: Z_CARD_LO,
                            lambda x: Z_LOWER_TOP, x0=xr, x1=xf, nx=64, nz=18, mirror=False))
        # the big woofer pocket, leaning back in the lower card (c3_0003)
        made.append(dc.band(pre + "Woofer", col, lib["speaker"], lambda x: 0.440,
                            lambda x: 0.600, proud=-0.008,
                            x0=lambda z: 0.40 + 0.32 * (z - 0.44) / 0.16, x1=lambda z: 0.90 + 0.04 * (z - 0.44),
                            nx=30, nz=8, edge_round=0.006, mirror=False))
        # the mauve leather body between the lower card and the wedge
        made.append(dc.band(pre + "Main", col, lib["leather_dash"], lambda x: Z_LOWER_TOP - 0.002,
                            lambda x: _wedge_lo(x) + 0.002, proud=0.004, x0=xr, x1=xf, nx=64, nz=14,
                            mirror=False))
        # the wedge: the brushed strip
        made.append(dc.band(pre + "Wedge", col, lib["wood"], _wedge_lo, lambda x: _belt_z(x) - 0.002,
                            proud=-0.002, x0=xr, x1=lambda z: xf(z) - 0.20, nx=64, nz=8,
                            edge_round=0.004, mirror=False))
        # the side-mirror monitor in the front corner: black glass
        made.append(dc.band(pre + "Monitor", col, lib["band_glass"],
                            lambda x: _belt_z(x) - 0.150, lambda x: _belt_z(x) - 0.012, proud=0.002,
                            x0=lambda z: xf(z) - 0.20, x1=lambda z: xf(z) + 0.005, nx=26, nz=8,
                            edge_round=0.004, mirror=False))
        # the chrome line under the wedge
        pts = dc.curve([(x, _wedge_lo(x) - 0.002) for x in [xr(0.9) + 0.02 + (xf(0.95) - 0.02 - xr(0.9)) * k / 40.0
                                                          for k in range(41)]], proud=0.0035)
        made.append(piping(pre + "Chrome", pts, col, lib["chrome"], r=0.0013, lateral=(0.0, 0.0, 1.0)))
        # the ambient light guide along the pod's lower edge
        pts = dc.curve([(x, 0.700) for x in [0.46 - 0.54 * k / 24.0 for k in range(25)]], proud=0.012)
        made.append(piping(pre + "Ambient", pts, col, lib["ambient"], r=0.0016, lateral=(0.0, 0.0, 1.0)))
        # the small silver speaker grille over the pack
        made.append(dc.band(pre + "Tweeter", col, lib["gunmetal"], lambda x: 0.905, lambda x: 0.960,
                            proud=0.004, x0=lambda z: 0.650, x1=lambda z: 0.760, nx=14, nz=4,
                            edge_round=0.004, mirror=False))
        # the armrest pod: a padded bar swelling toward the front, which runs on under the switch
        # pack (c3_0003: the pack sits on the pod's front end, the two read as one piece)
        made += _door_armrest(dc, pre + "Pod", col, lib, side,
                              [(-0.060, 0.800), (0.100, 0.815), (0.260, 0.828), (0.420, 0.838), (0.600, 0.846)],
                              width=0.082, height=0.080, keep_front=True)
        made += _switch_pack(dc, pre + "Pack", col, lib, side)
    made += build_rear_doors(col, lib)
    return made


# the switch pack: a black gloss block on the pod's front end, its top face tilted up toward the
# front and turned to the driver, carrying the door-lock keys, the mirror pad and the window keys
PACK_X = (0.345, 0.605)
PACK_Z = 0.846
PACK_PITCH = math.radians(-8.0)      # F.box: negative lifts the +X (front) end


def _switch_pack(dc, pre, col, lib, side):
    made = []
    cx = 0.5 * (PACK_X[0] + PACK_X[1])
    length, width, height = PACK_X[1] - PACK_X[0], 0.088, 0.044
    # the card's face runs inboard toward the front, so the pack is yawed to follow it
    ya = dc.skin_y(PACK_X[0], PACK_Z) - dc.th(PACK_Z)
    yb = dc.skin_y(PACK_X[1], PACK_Z) - dc.th(PACK_Z)
    yaw = math.atan2(side * (yb - ya), PACK_X[1] - PACK_X[0])
    cyw, syw = math.cos(yaw), math.sin(yaw)
    y0 = 0.5 * (ya + yb)                                # the card's face, as |y|, at the pack's middle
    c = (cx, side * (y0 - 0.5 * width + 0.004), PACK_Z)  # the pack stands on the card, 8.8 cm inboard
    p = PACK_PITCH
    cp, sp = math.cos(p), math.sin(p)
    made.append(F.box(col, pre, c, (length, width, height), lib["piano"], r=0.008, pitch=p, yaw=yaw))

    def at(s, t, n):
        """On the pack's top face: s along it toward the front, t inboard across it, n out of it."""
        xl, yl = s * cp + (0.5 * height + n) * sp, -side * t
        zl = -s * sp + (0.5 * height + n) * cp
        return (c[0] + xl * cyw - yl * syw, c[1] + xl * syw + yl * cyw, c[2] + zl)

    def key(name, s, t, size, mat, lift, r=0.0012):
        made.append(F.box(col, pre + name, at(s, t, lift + 0.5 * size[2]), size, mat, r=r, pitch=p, yaw=yaw))
    # the door-lock keys at the front end, then the mirror pad
    for j, t in enumerate((-0.014, 0.014)):
        key("_lock%d" % j, 0.104, t, (0.016, 0.016, 0.0035), lib["satin"], 0.0, 0.0008)
        key("_lockcap%d" % j, 0.104, t, (0.010, 0.010, 0.0012), lib["chrome"], 0.0035, 0.0004)
    # the pad's normal: the face's, turned by the yaw
    nrm = (sp * cyw, sp * syw, cp)
    made += F.disc(col, pre + "_mirror", at(0.064, 0.0, 0.0), nrm, 0.0185, lib["gunmetal"], dome=0.0015,
                   rim=0.0016, rim_mat=lib["chrome"])
    for j, (s, t) in enumerate(((0.012, 0.0), (-0.012, 0.0), (0.0, 0.012), (0.0, -0.012))):
        key("_arrow%d" % j, 0.064 + s, t, (0.006 if s else 0.003, 0.003 if s else 0.006, 0.0015),
            lib["crystal"], 0.0015, 0.0004)
    # two small keys, then the window keys in two rows of two: a chrome frame, a dark face, a bar
    for j, t in enumerate((-0.017, 0.017)):
        key("_mem%d" % j, 0.030, t, (0.014, 0.020, 0.0035), lib["satin"], 0.0, 0.0008)
    for r, s in enumerate((0.000, -0.045)):
        for j, t in enumerate((-0.022, 0.022)):
            key("_win%d%d" % (r, j), s, t, (0.034, 0.038, 0.0045), lib["chrome"], 0.0, 0.0010)
            key("_wface%d%d" % (r, j), s, t, (0.026, 0.030, 0.0012), lib["piano"], 0.0045, 0.0003)
            key("_wbar%d%d" % (r, j), s - 0.002, t, (0.005, 0.022, 0.0030), lib["chrome"], 0.0057, 0.0010)
    for j, t in enumerate((-0.017, 0.017)):
        key("_lk%d" % j, -0.092, t, (0.014, 0.020, 0.0035), lib["satin"], 0.0, 0.0008)
    return made


def _door_armrest(dc, name, col, lib, side, path_xz, width=0.070, height=0.050, n=40,
                  role="leather_door", keep_front=False):
    """A padded bar along the card through side-elevation points (x, z of its top), its ends
    tapering into the card (the front end stays full when it runs on under something)."""
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
    """The rear wheel opening's front edge at height z: the rear door's lower rear corner is cut
    away by it, so its card stops short of it."""
    B = S.BODY
    r = B.ARCH_R + 0.0021 + margin
    dz = max(0.0, z - B.WHEEL_R)
    return B.REAR_AXLE + math.sqrt(max(0.0, r * r - dz * dz)) if dz < r else -9.0


def rear_card(side):
    from carkit.interior.door import DoorCard
    th = Curve([(0.40, 0.105), (0.60, 0.135), (0.75, 0.150), (0.90, 0.140), (1.05, 0.105),
                (1.20, 0.075), (1.30, 0.060)], mode="pchip")
    return DoorCard(S.BODY, lambda z: X_B - 0.006,
                    lambda z: max(PN._DOOR_R_EDGE(z) + 0.006, _arch_front(z)), Z_CARD_LO, _belt_z, th,
                    v_top=PN.V_BELT + 0.015, side=side)


def build_rear_doors(col, lib):
    """The rear cards (c3_0016/17): the same wedge, a mauve main body, a brown lower card with a
    woofer pocket, the pod and a small switch pack."""
    made = []
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        dc = rear_card(side)
        pre = "int_rdoor_%s_" % tag
        xr, xf = dc.xr, dc.xf
        wl = lambda x: _belt_z(x) - 0.190
        made.append(dc.band(pre + "Lower", col, lib["leather_door"], lambda x: Z_CARD_LO,
                            lambda x: 0.660, x0=xr, x1=xf, nx=40, nz=16, mirror=False))
        made.append(dc.band(pre + "Main", col, lib["leather_dash"], lambda x: 0.658,
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
                              [(-1.00, 0.775), (-0.78, 0.790), (-0.55, 0.800)], width=0.070,
                              height=0.075)
        made.append(dc.band(pre + "Switches", col, lib["piano"], lambda x: 0.800, lambda x: 0.865,
                            proud=0.005, x0=lambda z: -0.40, x1=lambda z: -0.22, nx=10, nz=4,
                            edge_round=0.004, mirror=False))
        made.append(dc.band(pre + "Speaker", col, lib["speaker"], lambda x: 0.46, lambda x: 0.60,
                            proud=0.002, x0=lambda z: -0.80, x1=lambda z: -0.40, nx=14, nz=6,
                            mirror=False))
    return made
