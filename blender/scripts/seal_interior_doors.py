"""BYD Seal door cards in the orange "Sardine Coral" cabin, traced from Autohome series 6394:
c0088 (the driver's card, square on), c0092 (its switch pack, close), c0200 (the rear-left card).

A card is a black moulded carrier with upholstery laid on it. From the belt down:

    belt strip   black leather with a light grey stitch line, under the window sill cap
    trim         a glossy black carbon-lattice wedge across the upper card, rising to the front, with the
                 kidney handle bezel (silver ring) in it; the rear card has a round tweeter at its front
    swoop        the big orange panel under the trim, its lower edge a long curve that climbs to the front
    arm ledge    black, sloping down and in from the swoop's lower edge to a lip; the orange padded
                 armrest lies along it and the switch pack sits at its front end
    lower band   orange again under the ledge, ending in a dip
    pocket       the black lower card with a diamond-mesh Dynaudio speaker (and the boot switch, front)

The photographs give each shape as fractions of the card: u along it (front card: 0 at the B-pillar edge to
1 at the hinge edge; rear card: metres behind the front edge) and t up it (0 at the card's foot, 1 at the
belt). `Layout` maps them onto the door skin.
"""
import math

from mathutils import Matrix, Vector

from carkit import mesh as M
from carkit.geom import Curve
from carkit.interior import fittings as F
from carkit.interior.sweep import grid_mesh, piping, tube, ellipse, smooth_path, cr_segments, stitches

import seal_surface as S
import seal_panels as PN
from cabin_parts import smooth as _smooth


def _belt_z(x):
    return S.section_v(max(-1.70, min(0.98, x)), PN.V_BELT)[1]


X_B = PN.X_BPILLAR_F
Z_CARD_LO = 0.335
BELT_LIFT = 0.0185


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


# ------------------------------------------------------------------ layout
def _pl(pts):
    """A smooth curve through (u, t) points, held flat beyond the ends."""
    c = Curve([tuple(p) for p in pts], mode="pchip")
    lo, hi = pts[0][0], pts[-1][0]
    return lambda u: c(min(max(u, lo), hi))


class Layout:
    """Maps the photographs' (u, t) card coordinates onto the model's door card."""

    def __init__(self, dc, front):
        self.dc, self.front = dc, front
        self.side = dc.side

    def belt(self, x):
        return _belt_z(x)

    def x_of(self, u, z):
        dc = self.dc
        if self.front:
            xr, xf = dc.xr(z), dc.xf(z)
            return xr + u * (xf - xr)
        return dc.xf(z) - u

    def u_far(self, z, inset):
        dc = self.dc
        if self.front:
            return 1.0 - inset / max(1e-6, dc.xf(z) - dc.xr(z))
        return dc.xf(z) - dc.xr(z) - inset

    def xz(self, u, t):
        z = 0.7
        for _ in range(5):
            x = self.x_of(u, z)
            z = Z_CARD_LO + t * (self.belt(x) - Z_CARD_LO)
        return self.x_of(u, z), z

    def point(self, u, t, proud=0.0):
        x, z = self.xz(u, t)
        return self.dc.point(x, z, proud)

    def path(self, uts, proud=0.0, n=40):
        """A smooth path on the card through (u, t) points."""
        c = smooth_path([(u, 0.0, t) for (u, t) in uts], n)
        return [self.point(p[0], p[2], proud) for p in c]

    def normal(self):
        return (0.0, -self.side, 0.0)


def region(L, collection, name, mat, ua, ub, tlo, thi, proud, nx=48, nz=10, roll=0.004, inset=0.012,
           grade=None):
    """A panel between t = tlo(u) and thi(u), from u = ua to ub (None: to the card's far edge). proud may
    be a number or proud(g) with g running 0 (at tlo) to 1 (at thi): the arm ledge slopes that way."""
    dc = L.dc
    rows = []
    for i in range(nx + 1):
        f = i / float(nx)
        col = []
        for j in range(nz + 1):
            g = j / float(nz)
            z = 0.7
            for _ in range(5):
                ue = ub if ub is not None else L.u_far(z, inset)
                u = ua + (ue - ua) * f
                t = tlo(u) + (thi(u) - tlo(u)) * g
                x = L.x_of(u, z)
                z = Z_CARD_LO + t * (L.belt(x) - Z_CARD_LO)
            edge = min(j, nz - j, i, nx - i)
            r = roll * max(0.0, 1.0 - edge / 2.0)
            p = grade(g, u) if grade else proud
            col.append(dc.point(L.x_of(u, z), z, p - r))
        rows.append(col)
    ob = grid_mesh(name, rows, collection, mat)
    M.orient(ob.data, lambda c: (0.0, -dc.side, 0.0))
    return ob


def _super(uc, tc, hu, ht, p=3.0):
    """Upper and lower t of a superellipse centred (uc, tc): for rounded-square speaker grilles."""
    def half(u):
        a = min(1.0, abs(u - uc) / hu)
        return ht * (1.0 - a ** p) ** (1.0 / p)
    return (lambda u: tc - half(u)), (lambda u: tc + half(u))


def _box(col, lib, name, centre, size, role, frame, r=0.0012):
    """A bevelled block with its local x along the outward normal N, y along the card, z up it."""
    n, along, up = frame
    ob = F.box(col, name, (0.0, 0.0, 0.0), size, lib[role], r=r)
    rot = Matrix((tuple(n), tuple(along), tuple(up))).transposed()
    ob.matrix_world = Matrix.Translation(centre) @ rot.to_4x4()
    return ob


def _frame(L, tilt_deg):
    """(N, along, up) at the card: N leans up by tilt (the arm ledge slopes)."""
    s = L.side
    a = math.radians(tilt_deg)
    n = Vector((0.0, -s * math.cos(a), math.sin(a)))
    along = Vector((s, 0.0, 0.0))
    up = n.cross(along)
    return n, along, up


# ------------------------------------------------------------- the handle
HANDLE = [(-93, 5), (-65, 23), (-5, 39), (65, 37), (97, 23), (97, 5), (75, -20), (55, -30), (20, -35),
          (-25, -30), (-65, -12), (-85, -3)]


def build_handle(L, pre, col, lib, uc, tc, proud=0.0105):
    """The kidney bezel: a silver ring with a dark pocket, a finger lever, set into the trim."""
    made = []
    dc = L.dc
    xc, zc = L.xz(uc, tc)
    ring2 = [(p[0], p[1]) for p in cr_segments([(x * 1e-3, z * 1e-3) for (x, z) in HANDLE], 4, closed=True,
                                               alpha=0.5)]

    def pts(shrink=0.0, p=proud):
        out = []
        for (dx, dz) in ring2:
            k = 1.0 - shrink / max(1e-6, math.hypot(dx, dz) + 1e-6) if shrink else 1.0
            out.append(dc.point(xc + dx * k, zc + dz * k, p))
        return out
    path = pts()
    path.append(path[0])
    made.append(tube(pre + "Handle_Ring", path, ellipse(0.0046, 0.0032, 8), col, lib["brushed"],
                     lateral=L.normal(), cap=False))
    pocket = pts(0.016, proud - 0.0025)
    made.append(F.ngon_cap(col, pre + "Handle_Pocket", pocket, lib["key"], L.normal()))
    inner = pts(0.036, proud - 0.0008)
    made.append(F.ngon_cap(col, pre + "Handle_Lever", inner, lib["satin"], L.normal()))
    return made


# ------------------------------------------------------------- the speakers
def _label(L, name, text, u, t, size, col, lib, proud):
    """A small raised lettering on the card, reading left to right as seen from the cabin."""
    import seal_interior as ZI
    ob = M.text_mesh(name, text, size, col, lib["brushed"], extrude=0.0004, font=ZI._font("Inter.woff2"),
                     resolution=3)
    s = L.side
    ex = Vector((1.0, 0.0, 0.0) if s > 0 else (-1.0, 0.0, 0.0))
    ez = Vector((0.0, -s, 0.0))
    rot = Matrix((tuple(ex), (0.0, 0.0, 1.0), tuple(ez))).transposed().to_4x4()
    ob.matrix_world = Matrix.Translation(Vector(L.point(u, t, proud))) @ rot
    return ob


def build_speaker(L, pre, col, lib, uc, tc, hu, ht, proud, mesh_role="mesh", p=3.0, label=None):
    made = []
    tlo, thi = _super(uc, tc, hu, ht, p)
    made.append(region(L, col, pre + "Speaker", lib[mesh_role], uc - hu, uc + hu, tlo, thi, proud,
                       nx=40, nz=18, roll=0.0))
    ring = []
    for k in range(48):
        a = 2.0 * math.pi * k / 48.0
        c, s = math.cos(a), math.sin(a)
        u = uc + hu * math.copysign(abs(c) ** (2.0 / p), c)
        t = tc + ht * math.copysign(abs(s) ** (2.0 / p), s)
        ring.append(L.point(u, t, proud + 0.0006))
    ring.append(ring[0])
    made.append(tube(pre + "Speaker_Rim", ring, ellipse(0.0030, 0.0020, 6), col, lib["gunmetal"],
                     lateral=L.normal(), cap=False))
    if label:
        made.append(_label(L, pre + "Speaker_Label", "DYNAUDIO", label[0], label[1], 0.0065, col, lib,
                           proud + 0.0016))
    return made


def build_tweeter(L, pre, col, lib, uc, tc, r, proud):
    p = Vector(L.point(uc, tc, proud))
    n = Vector(L.normal())
    return F.disc(col, pre + "Tweeter", tuple(p), tuple(n), r, lib["speaker"], dome=0.002, rim=0.0022,
                  rim_mat=lib["gunmetal"])


# ------------------------------------------------------------ switch packs
def _ledge_proud(tlo, thi, u, t, amp=None):
    g = (t - tlo(u)) / max(1e-6, thi(u) - tlo(u))
    return 0.003 + (amp(u) if amp else LEDGE) * (1.0 - min(1.0, max(0.0, g))) ** 1.4


def build_pack(L, pre, col, lib, uc, tc, proud, driver, tilt=24.0):
    """The window-switch housing on the arm ledge's front end. The driver's has four window keys, two small
    keys at the rear and the mirror dial at the front; the others carry one rocker."""
    made = []
    fr = _frame(L, tilt)
    n, along, up = fr
    base = Vector(L.point(uc, tc, proud))
    xfwd = Vector((1.0, 0.0, 0.0))            # du runs toward the car's front on both cards

    def at(du, dv, lift):
        return base + xfwd * du + up * dv + n * lift

    if driver:
        made.append(_box(col, lib, pre + "Pack", base + n * 0.0045, (0.009, 0.150, 0.056), "key", fr, 0.004))
        cols = (-0.050, -0.017, 0.017)        # window key pairs, rear to front
        for i, du in enumerate(cols[1:]):
            for j, dv in enumerate((0.012, -0.012)):
                made.append(_box(col, lib, pre + "Win%d%d" % (i, j), at(du, dv + (0.006 if i else -0.002), 0.011),
                                 (0.007, 0.028, 0.019), "chrome", fr, 0.0012))
                made.append(_box(col, lib, pre + "WinFace%d%d" % (i, j),
                                 at(du, dv + (0.006 if i else -0.002), 0.0145), (0.002, 0.021, 0.013), "key", fr,
                                 0.0004))
        for j, dv in enumerate((0.015, -0.002)):
            made.append(_box(col, lib, pre + "Small%d" % j, at(-0.060, dv, 0.0095), (0.005, 0.014, 0.013),
                             "key", fr, 0.0010))
        made += F.disc(col, pre + "Mirror", tuple(at(0.053, 0.008, 0.0075)), tuple(n), 0.0105, lib["key"],
                       dome=0.0015, rim=0.0016, rim_mat=lib["chrome"])
    else:
        made.append(_box(col, lib, pre + "Pack", base + n * 0.0040, (0.008, 0.062, 0.030), "key", fr, 0.004))
        made.append(_box(col, lib, pre + "Win", at(0.0, 0.0, 0.0090), (0.007, 0.040, 0.018), "chrome", fr, 0.0012))
        made.append(_box(col, lib, pre + "WinFace", at(0.0, 0.0, 0.0125), (0.002, 0.033, 0.012), "key", fr,
                         0.0004))
    return made


# ------------------------------------------------------------- the armrest
def build_pad(L, pre, col, lib, ua, ub, t_top, height=0.074, width=0.072, n=60):
    """The orange padded armrest lying on the ledge: a rounded bolster, its top at t_top, tapering at both ends
    (the front end is blunter), with a tone-on-tone stitch line along the top."""
    from carkit.interior.sweep import cr_segments as crs
    dc, s = L.dc, L.side
    rows, top_path, top_n = [], [], []
    for k in range(n + 1):
        f = k / float(n)
        u = ua + (ub - ua) * f
        x, z = L.xz(u, t_top(u))
        e = min(1.0, min(f / 0.14, (1.0 - f) / 0.07))
        e = e * e * (3 - 2 * e)
        w = 0.004 + (width - 0.004) * e
        y0 = dc.skin_y(x, z) - dc.th(z) - 0.004
        prof = [(0.0, -height), (w * 0.55, -height * 0.92), (w * 0.95, -height * 0.55), (w, -0.012),
                (w * 0.9, -0.002), (w * 0.55, 0.0), (0.0, -0.003)]
        sec = crs(prof, 4)
        rows.append([(x, s * (y0 - a), z + b) for (a, b) in sec])
        top_path.append((x, s * (y0 - 0.46 * w), z + 0.0012))
        top_n.append((0.0, -0.35 * s, 0.94))
    ob = grid_mesh(pre + "Pad", rows, col, lib["leather_door"])
    M.orient(ob.data, lambda c: (0.0, -s, 0.4))
    made = [ob]
    i0, i1 = int(0.14 * n), int(0.93 * n)
    made.append(stitches(pre + "PadStitch", top_path[i0:i1], top_n[i0:i1], col, lib["thread"], side=0.0))
    return made


# ------------------------------------------------------- the front card
F_T_TOP = lambda u: 0.775 + 0.010 * u
F_CARB_TOP = _pl([(0, 0.838), (0.25, 0.862), (0.54, 0.886), (0.74, 0.913), (0.93, 0.955), (1.0, 0.968)])
F_WEDGE_TOP = _pl([(0.30, 0.500), (0.376, 0.533), (0.463, 0.574), (0.541, 0.611), (0.639, 0.648),
                   (0.737, 0.676), (0.839, 0.683), (0.844, 0.721), (0.873, 0.762), (0.885, 0.776), (1.0, 0.776)])
F_A_BOT = _pl([(0, 0.45), (0.30, 0.45), (0.307, 0.500), (0.376, 0.533), (0.463, 0.574), (0.541, 0.611),
               (0.639, 0.648), (0.737, 0.676), (0.839, 0.683), (0.844, 0.721), (0.873, 0.762)])
F_C_BOT = _pl([(0, 0.330), (0.083, 0.336), (0.249, 0.343), (0.405, 0.316), (0.444, 0.326), (0.502, 0.350),
               (0.639, 0.391), (0.785, 0.426), (0.946, 0.460), (1.0, 0.470)])
F_C_TOP = _pl([(0, 0.45), (0.5, 0.45), (0.566, 0.474), (0.659, 0.488), (0.834, 0.529), (0.932, 0.560),
               (1.0, 0.568)])
F_PAD_TOP = lambda u: 0.505
LEDGE = 0.056


def _amp(u):
    """The front ledge's depth: full along the arm, fading out to the card's flat front end."""
    return 0.010 + (LEDGE - 0.010) * (1.0 - _smooth((u - 0.80) / 0.12))


def build_front_card(side, pre, col, lib, driver):
    made = []
    dc = front_card(side)
    L = Layout(dc, True)
    xr = lambda z: X_B + 0.006
    xf = lambda z: _door_f_edge(z) - 0.022
    made.append(dc.belt_cap(pre + "Belt", col, lib["satin"], xr(0.95), xf(1.0), _belt_z,
                            mirror=False, lift=BELT_LIFT))
    made.append(dc.carrier(pre + "Carrier", col, lib["soft"], lambda x: Z_CARD_LO,
                           lambda x: _belt_z(x) - 0.002, x0=xr, x1=xf, back=0.016, nz=48, mirror=False))
    # black pocket below the lower band, with the speaker and the boot switch
    made.append(region(L, col, pre + "Pocket", lib["soft"], 0.085, 1.0, lambda u: 0.07,
                       lambda u: F_C_BOT(u) - 0.004, -0.010, nx=64, nz=14, roll=0.0))
    made += build_speaker(L, pre, col, lib, 0.845, 0.280, 0.135, 0.140, -0.005, label=(0.80, 0.150))
    made.append(_box(col, lib, pre + "BootSwitch",
                     Vector(L.point(0.751, 0.295, -0.002)) + Vector(L.normal()) * 0.004,
                     (0.008, 0.040, 0.046), "key", _frame(L, 0.0), 0.005))
    # the lower orange band and the big swoop above the ledge
    made.append(region(L, col, pre + "LowerBand", lib["leather_door"], 0.0, 0.95, F_C_BOT, F_C_TOP, 0.003,
                       nx=72, nz=8))
    made.append(region(L, col, pre + "Swoop", lib["leather_door"], 0.0, 0.873, F_A_BOT, F_T_TOP, 0.003,
                       nx=88, nz=14))
    # the arm ledge: black, sloping from the swoop's edge down and in to the lip
    made.append(region(L, col, pre + "Ledge", lib["soft"], 0.30, 1.0, lambda u: min(F_C_TOP(u), 0.44) if u < 0.566
                       else F_C_TOP(u), F_WEDGE_TOP, 0.0, nx=72, nz=12, roll=0.0,
                       grade=lambda g, u: 0.003 + _amp(u) * (1.0 - g) ** 1.4))
    made += build_pad(L, pre, col, lib, 0.09, 0.55, F_PAD_TOP)
    p = L.path([(0.15, 0.392), (0.30, 0.402), (0.46, 0.418)], 0.0050, 24)
    made.append(piping(pre + "PadLine", p, col, lib["brushed"], r=0.0013, lateral=(0.0, 0.0, 1.0)))
    made += build_pack(L, pre + "Pack", col, lib, 0.675, 0.536,
                       _ledge_proud(lambda u: F_C_TOP(u), F_WEDGE_TOP, 0.675, 0.536, _amp), driver)
    # upper door: carbon trim, black belt strip, handle
    made.append(region(L, col, pre + "Trim", lib["carbon"], 0.0, 1.0, F_T_TOP, F_CARB_TOP, 0.006, nx=80, nz=8,
                       roll=0.003))
    made.append(region(L, col, pre + "Strip", lib["leather_black"], 0.0, 1.0, F_CARB_TOP, lambda u: 0.992,
                       0.0025, nx=80, nz=8, roll=0.0))
    hs = [(u, F_CARB_TOP(u) + 0.5 * (0.992 - F_CARB_TOP(u))) for u in [0.02 + 0.94 * k / 20.0 for k in range(21)]]
    pts = L.path(hs, 0.0042, 48)
    made.append(stitches(pre + "StripStitch", pts, [L.normal()] * len(pts), col, lib["thread_light"]))
    p = L.path([(0.03, F_T_TOP(0.03) - 0.006), (0.30, F_T_TOP(0.30) - 0.006), (0.62, F_T_TOP(0.62) - 0.006)],
               0.0072, 30)
    made.append(piping(pre + "Ambient", p, col, lib["ambient"], r=0.0013, lateral=(0.0, 0.0, 1.0)))
    made += build_handle(L, pre, col, lib, 0.663, 0.879)
    return made


# -------------------------------------------------------- the rear card
R_T_TOP = lambda d: 0.7645 - 0.032 * min(d, 0.95)
R_CARB_TOP = _pl([(0.0, 0.940), (0.20, 0.898), (0.50, 0.862), (0.95, 0.8137), (1.5, 0.780)])
R_WEDGE_TOP = _pl([(0.0, 0.666), (0.211, 0.609), (0.4075, 0.543), (0.5056, 0.514), (0.584, 0.4935),
                   (0.60, 0.488)])
R_A_BOT = _pl([(0.0, 0.666), (0.211, 0.609), (0.4075, 0.543), (0.5056, 0.514), (0.584, 0.4935), (0.60, 0.455),
               (3.0, 0.455)])
R_C_BOT = _pl([(0.0, 0.465), (0.349, 0.399), (0.45, 0.355), (0.49, 0.333), (0.55, 0.337), (0.65, 0.370),
               (0.776, 0.400), (3.0, 0.400)])
R_C_TOP = _pl([(0.0, 0.520), (0.045, 0.520), (0.30, 0.478), (0.31, 0.455), (3.0, 0.455)])
R_PAD_TOP = lambda d: 0.4895


def build_rear_card(side, pre, col, lib, driver_side):
    made = []
    dc = rear_card(side)
    L = Layout(dc, False)
    xr, xf = dc.xr, dc.xf
    made.append(dc.belt_cap(pre + "Belt", col, lib["satin"], xr(0.95) + 0.004, xf(0.95), _belt_z, mirror=False,
                            lift=BELT_LIFT))
    made.append(dc.carrier(pre + "Carrier", col, lib["soft"], lambda x: Z_CARD_LO,
                           lambda x: _belt_z(x) - 0.002, x0=xr, x1=xf, back=0.016, nz=48, mirror=False))
    made.append(region(L, col, pre + "Pocket", lib["soft"], 0.0, None, lambda d: 0.07,
                       lambda d: R_C_BOT(d) - 0.004, -0.010, nx=48, nz=14, roll=0.0, inset=0.030))
    made += build_speaker(L, pre, col, lib, 0.130, 0.240, 0.135, 0.150, -0.005, label=(0.16, 0.115))
    made.append(region(L, col, pre + "LowerBand", lib["leather_door"], 0.0, None, R_C_BOT, R_C_TOP, 0.003,
                       nx=56, nz=8, inset=0.020))
    made.append(region(L, col, pre + "Swoop", lib["leather_door"], 0.0, None, R_A_BOT, R_T_TOP, 0.003,
                       nx=72, nz=14, inset=0.020))
    made.append(region(L, col, pre + "Ledge", lib["soft"], 0.0, 0.60, R_C_TOP, R_WEDGE_TOP, 0.0, nx=48, nz=12,
                       roll=0.0, grade=lambda g, u: 0.003 + LEDGE * (1.0 - g) ** 1.4))
    made += build_pad(L, pre, col, lib, 0.31, 0.775, R_PAD_TOP)
    p = L.path([(0.32, 0.395), (0.50, 0.382), (0.72, 0.392)], 0.0050, 24)
    made.append(piping(pre + "PadLine", p, col, lib["brushed"], r=0.0013, lateral=(0.0, 0.0, 1.0)))
    made += build_pack(L, pre + "Pack", col, lib, 0.17, 0.525,
                       _ledge_proud(R_C_TOP, R_WEDGE_TOP, 0.17, 0.525), False)
    made.append(region(L, col, pre + "Trim", lib["carbon"], 0.0, None, R_T_TOP, R_CARB_TOP, 0.006, nx=72, nz=8,
                       roll=0.003, inset=0.020))
    made.append(region(L, col, pre + "Strip", lib["leather_black"], 0.0, None, R_CARB_TOP, lambda d: 0.992,
                       0.0025, nx=72, nz=8, roll=0.0, inset=0.020))
    hs = [(d, R_CARB_TOP(d) + 0.5 * (0.992 - R_CARB_TOP(d))) for d in [0.03 + 0.85 * k / 20.0 for k in range(21)]]
    pts = L.path(hs, 0.0042, 48)
    made.append(stitches(pre + "StripStitch", pts, [L.normal()] * len(pts), col, lib["thread_light"]))
    made += build_handle(L, pre, col, lib, 0.2018, 0.8437)
    made += build_tweeter(L, pre, col, lib, 0.0643, 0.8437, 0.040, 0.0085)
    return made


# ------------------------------------------------------------------ build
def build_doors(col, lib):
    made = []
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        made += build_front_card(side, "int_door_%s_" % tag, col, lib, driver=(side > 0))
    made += build_rear_doors(col, lib)
    return made


def build_rear_doors(col, lib):
    made = []
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        made += build_rear_card(side, "int_rdoor_%s_" % tag, col, lib, side > 0)
    return made
