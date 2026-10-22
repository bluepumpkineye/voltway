"""BYD Seal centre console, read from the photographs (d0144-d0148 close-ups, d0108 and d0126 overall).

A narrow black bridge between the seats, 0.18-0.25 m wide, standing on a black skirt, with an ORANGE
leather flank on each side and a fine silver line where the flank meets the black frame. Front to back
(positions solved through the overhead camera, seal_cabinsolve):

    x 0.62-0.44   a ramp up to the dash with the front air vent: two long horizontal blades with sliding
                  knobs behind a silver lip
    x 0.43-0.30   the wireless charger: a tray holding a 50 W pad of grey felt
    x 0.26-0.13   the gear selector: a round button panel (eight keys, three knurled rollers) round a
                  U-shaped slot that carries the crystal shift knob
    x 0.12-0.06   two cup holders side by side under a thin silver edge
    x 0.055-...   the padded orange leather armrest, stitched tone-on-tone
"""
import math

from mathutils import Matrix, Vector

import seal_interior as ZI
from carkit import mesh as M
from carkit.geom import Curve
from carkit.interior import fittings as F
from carkit.interior.sweep import grid_mesh, tube, ellipse, smooth_path, stitches, piping, cr_segments

FLOOR_Z = ZI.FLOOR_Z
X0, X1 = 0.640, 0.040                       # the deck's front and rear
HW = Curve([(0.64, 0.130), (0.56, 0.124), (0.46, 0.116), (0.36, 0.100), (0.27, 0.090), (0.20, 0.087),
            (0.13, 0.090), (0.05, 0.094)], mode="pchip")
TOP = Curve([(0.64, 0.805), (0.60, 0.790), (0.56, 0.770), (0.50, 0.752), (0.44, 0.745), (0.30, 0.738),
             (0.20, 0.736), (0.10, 0.739), (0.04, 0.743)], mode="pchip")
Z_FLANK0, Z_FLANK1 = 0.485, 0.668           # the orange band's lower and upper edges
CORNER = 0.012

# features on the deck (x, y in the car's axes)
PAD_X = (0.305, 0.425)
PAD_HY = 0.076
PAD_DEPTH = 0.013
DIAL_C = (0.195, 0.0)
DIAL_R = 0.066
CUP_X = 0.088
CUP_Y = 0.037
CUP_R = 0.0325
CUP_DEPTH = 0.085
VENT_X = (0.465, 0.575)
VENT_HY = 0.098


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _dip(x, y):
    """How far the deck dips at (x, y): the charger tray, the dial's dish, the two cups, the vent slot."""
    d = 0.0
    e = 0.0035
    if PAD_X[0] - e < x < PAD_X[1] + e:
        k = min(_smooth((x - PAD_X[0]) / e), _smooth((PAD_X[1] - x) / e))
        k *= _smooth((PAD_HY - abs(y)) / e)
        d += PAD_DEPTH * k
    r = math.hypot(x - DIAL_C[0], y - DIAL_C[1])
    d += 0.0035 * _smooth((DIAL_R - r) / 0.003)
    for s in (-1.0, 1.0):
        r = math.hypot(x - CUP_X, y - s * CUP_Y)
        d += CUP_DEPTH * _smooth((CUP_R - r) / 0.0025)
    if VENT_X[0] - e < x < VENT_X[1] + e:
        k = min(_smooth((x - VENT_X[0]) / e), _smooth((VENT_X[1] - x) / e)) * _smooth((VENT_HY - abs(y)) / e)
        d += 0.020 * k
    return d


def _stations():
    xs = []
    x = X0
    while x > X1:
        xs.append(x)
        dense = (0.585 > x > 0.45) or (0.44 > x > 0.29) or (0.27 > x > 0.12) or (0.13 > x > 0.04)
        x -= 0.0035 if dense else 0.012
    xs.append(X1)
    return xs


def _ys(hw, n=44):
    inner = hw - CORNER
    return [inner - 2.0 * inner * k / n for k in range(n + 1)]


def _row_side(x, side):
    """One side wall at x: (y, z) from the floor up to just short of the deck's edge (16 points)."""
    hw = HW(x)
    zt = TOP(x)
    pts = [(side * hw, FLOOR_Z), (side * hw, Z_FLANK0 - 0.012), (side * hw, Z_FLANK0)]
    n = 7
    for k in range(1, n):                                  # the flank, a little proud in the middle
        t = k / float(n)
        z = Z_FLANK0 + (Z_FLANK1 - Z_FLANK0) * t
        bulge = 0.0045 * math.sin(math.pi * t) ** 0.7
        pts.append((side * (hw + bulge), z))
    pts += [(side * hw, Z_FLANK1), (side * hw, Z_FLANK1 + 0.008), (side * hw, zt - CORNER)]
    for k in range(1, 5):                                  # the rounded top edge (the 5th point is the deck's)
        a = 0.5 * math.pi * k / 5.0
        pts.append((side * (hw - CORNER + CORNER * math.cos(a)), zt - CORNER + CORNER * math.sin(a)))
    return pts


NL = 16                                                    # points in a side wall


def build_body(col, lib):
    made = []
    xs = _stations()
    rows = []
    for x in xs:
        left = _row_side(x, +1.0)
        right = _row_side(x, -1.0)
        deck = [(y, TOP(x) - _dip(x, y)) for y in _ys(HW(x))]
        rows.append([(x, y, z) for (y, z) in left] + [(x, y, z) for (y, z) in deck]
                    + [(x, y, z) for (y, z) in right[::-1]])
    nd = len(_ys(1.0))
    total = len(rows[0])
    assert total == 2 * NL + nd

    def panel(name, j0, j1, mat, outward):
        ob = grid_mesh(name, [r[j0:j1 + 1] for r in rows], col, mat)
        M.orient(ob.data, outward)
        return ob

    side_out = lambda c: (0.0, c[1], 0.0)
    up = lambda c: (0.0, 0.0, 1.0)
    d0, d1 = NL, NL + nd - 1                    # the deck's first and last columns
    r0 = NL + nd                                # the right wall's first column (its top arc)
    # left wall (columns 0..NL-1): skirt 0-2, flank 2-9, frame 9..deck start
    made.append(panel("int_console_SkirtL", 0, 2, lib["soft"], side_out))
    made.append(panel("int_console_FlankL", 2, 9, lib["leather_door"], side_out))
    made.append(panel("int_console_FrameL", 9, d0, lib["plastic"], side_out))
    made.append(panel("int_console_Deck", d0, d1, lib["plastic"], up))
    # right wall, reversed: columns d1 (arc end) then r0.. = arc4 .. floor
    made.append(panel("int_console_FrameR", d1, r0 + 6, lib["plastic"], side_out))
    made.append(panel("int_console_FlankR", r0 + 6, r0 + 13, lib["leather_door"], side_out))
    made.append(panel("int_console_SkirtR", r0 + 13, r0 + 15, lib["soft"], side_out))
    # silver line where the flank meets the frame, ambient strips under the deck's edge
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        line = [(x, side * (HW(x) + 0.0008), Z_FLANK1 + 0.004) for x in xs[::3]] + \
               [(xs[-1], side * (HW(xs[-1]) + 0.0008), Z_FLANK1 + 0.004)]
        made.append(tube("int_console_Line" + tag, line, ellipse(0.0011, 0.0011, 6), col, lib["brushed"],
                         lateral=(0.0, 0.0, 1.0)))
        amb = [(x, side * (HW(x) - 0.004), Z_FLANK0 - 0.010) for x in xs[::4]]
        made.append(tube("int_console_Ambient" + tag, amb, ellipse(0.0016, 0.0016, 6), col, lib["ambient"],
                         lateral=(0.0, 0.0, 1.0)))
    # front and rear caps
    for x, nrm, nm in ((xs[0], (1.0, 0.0, 0.0), "Front"), (xs[-1], (-1.0, 0.0, 0.0), "Rear")):
        left = _row_side(x, 1.0)
        outline = [(x, y, z) for (y, z) in left] + [(x, -y, z) for (y, z) in left[::-1]]
        made.append(F.ngon_cap(col, "int_console_Cap" + nm, outline, lib["plastic"], nrm))
    return made


# -------------------------------------------------------------- features
def _deck_z(x, y):
    return TOP(x) - _dip(x, y)


def build_vent(col, lib):
    made = []
    xa, xb = VENT_X
    zf = TOP(0.5 * (xa + xb)) - 0.020
    # a recess floor and its silver lip toward the driver
    made.append(F.box(col, "int_console_VentFloor", (0.5 * (xa + xb), 0.0, zf - 0.0015),
                      (xb - xa - 0.004, 2 * VENT_HY - 0.004, 0.003), lib["satin"], r=0.0005))
    lip_z = TOP(xa) + 0.0015
    made.append(F.box(col, "int_console_VentLip", (xa - 0.0025, 0.0, lip_z), (0.0075, 2 * VENT_HY + 0.006, 0.0065),
                      lib["brushed"], r=0.0022))
    for k, f in enumerate((0.30, 0.60)):
        x = xa + (xb - xa) * f
        made.append(F.box(col, "int_console_VentBlade%d" % k, (x, 0.0, zf + 0.007),
                          (0.0030, 2 * VENT_HY - 0.012, 0.0125), lib["key"], r=0.0008, pitch=0.35))
    for k, (x, y) in enumerate(((xa + 0.5 * (xb - xa) * 0.9, -0.022), (xa + 0.5 * (xb - xa) * 0.9, 0.040))):
        made.append(F.box(col, "int_console_VentKnob%d" % k, (xa + 0.45 * (xb - xa), y, zf + 0.0105),
                          (0.0095, 0.034, 0.0105), lib["key"], r=0.003, pitch=0.35))
    return made


def build_charger(col, lib):
    made = []
    xa, xb = PAD_X
    z = TOP(0.5 * (xa + xb)) - PAD_DEPTH
    # the pad: a thin slab of grey felt at the tray's floor, clear of its walls
    made.append(F.box(col, "int_console_Pad", (0.5 * (xa + xb) + 0.002, 0.0, z + 0.0015),
                      (xb - xa - 0.020, 2 * PAD_HY - 0.020, 0.0035), lib["suede"], r=0.0012))
    # a thin silver edge round the tray (c0144 shows a bright bevel on the rear)
    ring = [(xa - 0.001, -PAD_HY, TOP(xa)), (xa - 0.001, PAD_HY, TOP(xa)), (xb + 0.001, PAD_HY, TOP(xb)),
            (xb + 0.001, -PAD_HY, TOP(xb))]
    return made


def _wedge(col, lib, name, ang0, ang1, r0, r1, z, mat, h=0.003, centre=DIAL_C):
    """An annular wedge key (angles in degrees seen from above, from +x toward +y), h tall."""
    n = 8
    ring = []
    for i in range(n + 1):
        a = math.radians(ang0 + (ang1 - ang0) * i / n)
        ring.append((centre[0] + r1 * math.cos(a), centre[1] + r1 * math.sin(a)))
    for i in range(n, -1, -1):
        a = math.radians(ang0 + (ang1 - ang0) * i / n)
        ring.append((centre[0] + r0 * math.cos(a), centre[1] + r0 * math.sin(a)))
    m = len(ring)
    verts = [(x, y, z + h) for (x, y) in ring] + [(x, y, z) for (x, y) in ring]
    faces = [list(range(m)), list(range(2 * m - 1, m - 1, -1))]
    for i in range(m):
        j = (i + 1) % m
        faces.append([i, i + m, j + m, j])
    ob = M.obj(name, verts, faces, col, mat, smooth=False)
    M.orient(ob.data, lambda c: (c[0] - centre[0], c[1] - centre[1], 0.0))
    M.bevel(ob, min(0.0009, 0.3 * h), 2, 40)
    return ob


def build_selector(col, lib):
    made = []
    cx, cy = DIAL_C
    z0 = TOP(cx) - 0.0035
    # the ring: a graphite annulus round the panel, then eight keys and the slot
    ring = [(cx + (DIAL_R + 0.0012) * math.cos(2 * math.pi * k / 64), cy + (DIAL_R + 0.0012) * math.sin(2 * math.pi * k / 64),
             z0 + 0.0014) for k in range(64)]
    made.append(tube("int_console_DialRing", ring, ellipse(0.0024, 0.0016, 8), col, lib["gunmetal"],
                     lateral=(0.0, 0.0, 1.0), closed=True))
    made += F.disc(col, "int_console_DialFace", (cx, cy, z0 + 0.0004), (0.0, 0.0, 1.0), DIAL_R, lib["soft"],
                   rim=None)
    # keys: wedges around the dial, a gap at the front (+x) for the slot (the car faces +x: top of the photo)
    ang0 = 28.0
    names = ("Start", "Park", "AutoHold", "Regen", "Hazard", "Mode", "Defrost", "Fan")
    for k in range(8):
        a0 = ang0 + 38.0 * k + 2.0
        # keys run from the slot's right side (front-right) round the back to its left
        made.append(_wedge(col, lib, "int_console_Key%s" % names[k], a0, a0 + 34.0, 0.028, DIAL_R - 0.006,
                           z0 + 0.0006, lib["key"], h=0.0016))
    # two knurled rollers on the right-hand keys (front right and back right in the photograph)
    for k, (ang, rr) in enumerate(((-48.0, 0.0475), (-132.0, 0.0475))):
        a = math.radians(ang)
        c = (cx + rr * math.cos(a), cy + rr * math.sin(a), z0 + 0.0046)
        made.append(F.box(col, "int_console_Roller%d" % k, c, (0.012, 0.020, 0.0060), lib["knurl"], r=0.0025,
                          yaw=a + math.pi / 2))
    # the U-shaped slot and the crystal knob: the slot opens to the front, the knob at its rear end
    slot = [(cx + 0.060, cy - 0.019), (cx + 0.060, cy + 0.019), (cx - 0.001, cy + 0.019), (cx - 0.012, cy + 0.010),
            (cx - 0.012, cy - 0.010), (cx - 0.001, cy - 0.019)]
    made.append(F.plate_with_hole("int_console_Slot", F.round_rect_xy(cx - 0.012, cx + 0.060, cy - 0.021, cy + 0.021, 0.010),
                                  [], lambda x, y: z0 + 0.0043, col, lib["satin"], nx=14, ny=8))
    made.append(F.box(col, "int_console_ParkPad", (cx - 0.034, cy, z0 + 0.0030), (0.026, 0.040, 0.0016),
                      lib["key"], r=0.0006))
    # ribbed gear track between the knob and the park key (the silver ladder in c0147)
    for k in range(9):
        made.append(F.box(col, "int_console_Track%d" % k, (cx + 0.006 + 0.0062 * k, cy, z0 + 0.0052),
                          (0.0026, 0.024, 0.0034), lib["brushed"], r=0.0007))
    # the crystal knob: a glass cube leaning toward the driver, a slim silver cap line on top
    made.append(F.box(col, "int_console_Knob", (cx + 0.052, cy, z0 + 0.0205), (0.034, 0.036, 0.034),
                      lib["crystal"], r=0.0075, pitch=-0.10))
    made.append(F.box(col, "int_console_KnobFace", (cx + 0.0352 - 0.0, cy, z0 + 0.0215), (0.0012, 0.0225, 0.0225),
                      lib["screen_glass"], r=0.0008, pitch=-0.10))
    return made


def build_cups(col, lib):
    made = []
    for k, s in enumerate((-1.0, 1.0)):
        c = (CUP_X, s * CUP_Y)
        z = TOP(CUP_X) - CUP_DEPTH
        made += F.disc(col, "int_console_Cup%d" % k, (c[0], c[1], z + 0.002), (0.0, 0.0, 1.0), CUP_R - 0.001,
                       lib["rubber"], rim=None)
    # a thin silver rim along the rear edge of the cups, where the armrest meets the deck
    edge = [(CUP_X - 0.036, y, TOP(CUP_X - 0.036) + 0.0004) for y in [-0.090 + 0.180 * k / 16.0 for k in range(17)]]
    made.append(tube("int_console_CupEdge", edge, ellipse(0.0013, 0.0013, 6), col, lib["brushed"],
                     lateral=(1.0, 0.0, 0.0)))
    return made


# --------------------------------------------------------------- armrest
ARM_X = (0.058, -0.200)
ARM_HW = 0.088
ARM_Z0, ARM_Z1 = 0.742, 0.793


def build_armrest(col, lib):
    made = []
    n = 40
    xs = [ARM_X[0] + (ARM_X[1] - ARM_X[0]) * k / n for k in range(n + 1)]
    rows = []
    for x in xs:
        t = (ARM_X[0] - x) / (ARM_X[0] - ARM_X[1])
        # rounded front and rear, a slight crown, flat sides
        edge = min(1.0, min(t, 1.0 - t) / 0.10)
        edge = math.sqrt(max(0.0, 1.0 - (1.0 - edge) ** 2))
        hw = ARM_HW * (0.86 + 0.14 * edge) * edge ** 0.30
        top = ARM_Z0 + (ARM_Z1 - ARM_Z0) * edge ** 0.55
        prof = []
        for k in range(17):
            a = math.pi * k / 16.0
            u = math.cos(a)
            # a rounded-rectangle section: a flat crown with fillets of radius 0.020
            prof.append((hw * u, ARM_Z0 + (top - ARM_Z0) * (math.sin(a) ** 0.5)))
        rows.append([(x, y, z) for (y, z) in prof])
    ob = grid_mesh("int_console_Armrest", rows, col, lib["leather_door"])
    M.orient(ob.data, lambda c: (0.0, c[1], c[2] - 0.74))
    made.append(ob)
    # a lid-edge seam and a tone-on-tone stitch line round the crown
    for sd, tag in ((1.0, "L"), (-1.0, "R")):
        path = []
        nrm = []
        for k in range(8, n - 7):
            x = xs[k]
            t = (ARM_X[0] - x) / (ARM_X[0] - ARM_X[1])
            edge = min(1.0, min(t, 1.0 - t) / 0.10)
            edge = math.sqrt(max(0.0, 1.0 - (1.0 - edge) ** 2))
            hw = ARM_HW * (0.86 + 0.14 * edge) * edge ** 0.30
            top = ARM_Z0 + (ARM_Z1 - ARM_Z0) * edge ** 0.55
            y = sd * hw * 0.80
            path.append((x, y, ARM_Z0 + (top - ARM_Z0) * (math.sin(math.acos(0.80)) ** 0.5)))
            nrm.append((0.0, 0.3 * sd, 0.95))
        made.append(stitches("int_console_ArmStitch" + tag, path, nrm, col, lib["thread"]))
    return made


def build_rear(col, lib):
    """The rear air vent block and its two ports at the back of the console."""
    made = []
    x = ARM_X[1] - 0.004
    made.append(F.box(col, "int_console_RearVent", (x, 0.0, 0.600), (0.012, 0.150, 0.050), lib["plastic"], r=0.006))
    for k in range(7):
        made.append(F.box(col, "int_console_RearSlat%d" % k, (x - 0.003, -0.054 + 0.018 * k, 0.600),
                          (0.004, 0.0035, 0.036), lib["key"], r=0.0008))
    return made


def build(col, lib):
    made = []
    made += build_body(col, lib)
    made += build_vent(col, lib)
    made += build_charger(col, lib)
    made += build_selector(col, lib)
    made += build_cups(col, lib)
    made += build_armrest(col, lib)
    return made
