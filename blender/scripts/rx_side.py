"""Luxeed RX side details: mirrors, flush handles, gloss black arch
cladding, side skirts, the fender vent's pocket, the charge flap - read off
the camera-matched side photograph (rx_ref_match).

    mirrors     body-colour caps on black bases at the door's front corner:
                x 0.28-0.56, z 1.05-1.23 (side photo), tips at y +/-1.10
    handles     flush, black: front door x -0.05..-0.25 at z 0.945, rear door
                x -1.07..-1.28 at z 1.00
    cladding    gloss black round both wheel openings, ~60 mm (front) and
                ~70 mm (rear) wide, flaring out: from behind (rear.jpg) it is
                the car's outermost edge over the rear wheels, 35 mm outside
                the paint
    skirts      black from arch to arch, z 0.215-0.33, a satin silver line on
                top (front34_blue, side photo)
    charge flap left rear quarter only: x -1.77..-2.04, z 0.98-1.13
"""
import math

import rx_surface as S
import rx_nose as N
import rx_panels as PN
from carkit import geom
from carkit import mesh as M
from carkit.parts import aero, fittings

BODY = N.BODY
proud = BODY.proud


def on_flank(x, z, d=0.0):
    p, n = BODY.side_point(x, z)
    return (p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d), n


# ------------------------------------------------------------------ mirrors
def build_mirrors(collection, lib):
    """Side photo: the head from x 0.27 (glass) to 0.53 (nose), z 1.13-1.26,
    a flat underside and a crown rising to the glass; rear photo: the glass
    face y 0.88-1.10 (its z there reads ~5 cm high - the rear camera is 12 m
    off; the side camera's z is used); front 3/4: a painted cap over a gloss
    black underside, on a slim black arm from the door's upper front corner
    (side photo: the arm meets the door at x 0.46, z 1.04)."""
    return fittings.mirror_cap("RX_Mirror", collection, lib,
                               rear=(0.275, 0.990, 1.205), size=(0.240, 0.215, 0.118),
                               arm_base=(0.470, 0.93, 1.045), proud=proud,
                               mats=("paint", "mirror_glass", "black_gloss", "black_gloss"))


# ------------------------------------------------------------------ handles
HANDLES = (("F", -0.050, -0.250, 0.945), ("R", -1.070, -1.280, 1.000))


def build_handles(collection, lib):
    return [fittings.flush_handle("RX_Handle_" + nm, x0, x1, zc, proud, collection,
                                  lib["black_gloss"], h=0.012, d=0.0012)
            for nm, x0, x1, zc in HANDLES]


# ----------------------------------------------------------- arch cladding
def _arch_path(axle, r, z_bot, n_arc=48, n_leg=6):
    """Side-elevation path round a wheel opening: up the front leg, over the
    arch, down the rear leg (the opening's straight sides run into the sill)."""
    zc = S.WHEEL_R
    pts = [(axle + r, z_bot + (zc - z_bot) * i / float(n_leg)) for i in range(n_leg)]
    pts += [(axle + r * math.cos(math.pi * i / n_arc), zc + r * math.sin(math.pi * i / n_arc))
            for i in range(n_arc + 1)]
    pts += [(axle - r, zc - (zc - z_bot) * i / float(n_leg)) for i in range(1, n_leg + 1)]
    return pts


def build_cladding(collection, lib):
    made = []
    for tag, axle, width, flare, z_bot in (("F", S.FRONT_AXLE, 0.058, 0.022, 0.300),
                                             ("R", S.REAR_AXLE, 0.068, 0.036, 0.320)):
        r_out = S.ARCH_R + 0.010                 # laps 10 mm over the paint
        r_in = S.ARCH_R - width
        outer = _arch_path(axle, r_out, z_bot)
        inner = _arch_path(axle, r_in, z_bot)
        rows = []
        m = len(outer)
        for i in range(m):
            # flare: full over the top, easing out down the legs
            s = i / float(m - 1)
            f = flare * (0.35 + 0.65 * math.sin(math.pi * s))
            po, no = on_flank(outer[i][0], outer[i][1], 0.0025)
            pi, ni = on_flank(inner[i][0], inner[i][1], 0.0025 + f)
            lip = (pi[0], pi[1] - 0.045, pi[2])
            rows.append([po, pi, lip])
        ob = M.grid("RX_Clad_" + tag, rows, collection, lib["black_gloss"],
                    geom.const((0.0, 1.0, 0.0)))
        M.solidify(ob, 0.003)
        M.mirror_y(ob)
        made.append(ob)
    return made


# ---------------------------------------------------------------- skirts
X_SKIRT_F = S.FRONT_AXLE - S.ARCH_R + 0.005
X_SKIRT_R = S.REAR_AXLE + S.ARCH_R - 0.005


def build_skirts(collection, lib):
    made = [aero.side_skirt("RX_Skirt", collection, lib, proud,
                            lambda x: S.Y_ROCKER(x) + 0.02, X_SKIRT_R, X_SKIRT_F,
                            0.215, 0.318, nx=60, nz=6, d=0.010, mat="black_gloss")]
    made.append(fittings.surface_band("RX_Skirt_Line", lambda k: X_SKIRT_R + 0.02,
                                      lambda k: X_SKIRT_F - 0.02,
                                      lambda x: 0.300, lambda x: 0.309,
                                      lambda p, d: proud(p, 0.0205), collection,
                                      lib["stripe"], 60))
    return made


# ------------------------------------------------------------ fender vent
def build_vent(collection, lib):
    """The dark pocket behind the fender vent's cut, and a gloss black frame
    lining its edge (side photo: a black blade ahead of the door)."""
    ring = geom.polyline([(x, 0.95, z) for (x, z) in PN.VENT_OUTLINE + PN.VENT_OUTLINE[:1]],
                         40)[:-1]
    a, b, c = [], [], []
    for (x, _y, z) in ring:
        p, n = on_flank(x, z)
        a.append(p)
        b.append(tuple(p[k] - n[k] * 0.012 for k in range(3)))
        c.append(tuple(p[k] - n[k] * 0.035 for k in range(3)))
    a.append(a[0]); b.append(b[0]); c.append(c[0])
    frame = M.strip("RX_Vent_Frame", a, b, collection, lib["black_gloss"])
    M.mirror_y(frame)
    cx = [sum(p[k] for p in c) / len(c) for k in range(3)]
    back = M.grid("RX_Vent_Pocket", [[b[i], c[i], tuple(cx)] for i in range(len(b))],
                  collection, lib["shadow"], geom.const((0.0, 1.0, 0.0)))
    M.mirror_y(back)
    return [frame, back]


# ------------------------------------------------------------ charge flap
def build_charge_door(collection, lib):
    return [fittings.outline_ring("RX_Charge_Line", -2.037, -1.774, 0.978, 1.127, 0.030,
                                  proud, collection, lib["shadow"], y_ref=0.90)]


def build_all(collection, lib):
    made = []
    made += build_mirrors(collection, lib)
    made += build_handles(collection, lib)
    made += build_cladding(collection, lib)
    made += build_skirts(collection, lib)
    made += build_vent(collection, lib)
    made += build_charge_door(collection, lib)
    return made
