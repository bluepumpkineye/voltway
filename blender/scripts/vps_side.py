"""Voyah Passion S (岚图追光S) side details, calibrated to c1_0004.jpg via vps_cam.SIDE.

  - Door-mounted flag mirrors (`VPS_Mirror_Head/Glass/Stalk/Strip/Cam*`) at x 0.56..0.75, z 1.19..1.38
  - Flush pocket door handles (`VPS_Handle_Pocket_F/R` + painted upper flap `VPS_Handle_Flap_F/R`)
  - Gloss-black SUV wheel-arch cladding (`VPS_Clad_F/R`, r_in 0.466 .. r_out 0.532, flaring to 1998 mm width)
  - Vertical front-fender ADAS camera/LiDAR gill (`VPS_Vent_Frame/Pocket` + dual ADAS lenses)
  - Left-rear quarter rounded-square charge port shut-line (`VPS_Charge_Line`)
"""
import math

import vps_surface as S
import vps_nose as N
import vps_panels as PN
from carkit import geom
from carkit import mesh as M
from carkit.parts import fittings, lamps

BODY = N.BODY
proud = BODY.proud


def on_flank(x, z, d=0.0):
    p, n = BODY.side_point(x, z)
    return (p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d), n


# ------------------------------------------------------------------ mirrors
def build_mirrors(collection, lib):
    """Door-mounted two-tone flag mirrors (side_grid_mid u 1480..1595, front_grid y_tip 1.075)."""
    made = fittings.mirror_cap(
        "VPS_Mirror", collection, lib,
        rear=(0.565, 1.005, 1.288),
        size=(0.192, 0.176, 0.154),
        arm_base=(0.665, 0.945, 1.132),
        proud=proud,
        drop=0.22,
        split=-0.24,
        mats=("paint", "mirror_glass", "black_gloss", "black_gloss"),
    )
    # Horizontal LED turn-indicator strip across the mirror cap (front_grid v 1245, side_grid_mid v 1480)
    rows = []
    for i in range(13):
        t = i / 12.0
        y = 0.955 + 0.128 * t
        x = 0.725 - 0.055 * (1.0 - t) ** 1.3
        rows.append([(x + 0.002, y, 1.258), (x + 0.004, y, 1.266)])
    strip = M.grid("VPS_Mirror_Strip", rows, collection, lib["lamp_white_bar"],
                   geom.away_from((0.64, 1.00, 1.26)))
    M.solidify(strip, 0.0020)
    M.mirror_y(strip)
    made.append(strip)

    # Surround-view camera pod on the gloss-black mirror arm underside
    made += lamps.projector("VPS_Mirror_Cam", (0.655, 0.985, 1.122), (0.0, 0.25, -0.97), 0.012,
                            collection, lib, mats=("black_gloss", "lamp_smoked"))
    return made


# ------------------------------------------------------------------ handles
# Read off side_grid_mid.png: front x -0.053..0.188 z 0.968..1.044; rear x -1.130..-0.889 z 0.992..1.066
HANDLES = (
    ("F", 0.188, -0.053, 1.006),
    ("R", -0.889, -1.130, 1.028),
)


def build_handles(collection, lib):
    made = []
    for nm, x0, x1, zc in HANDLES:
        # Lower gloss-black recessed finger pocket
        made.append(fittings.flush_handle("VPS_Handle_Pocket_" + nm, x0, x1, zc - 0.017, proud,
                                          collection, lib["black_gloss"], h=0.019, d=0.0008))
        # Upper body-coloured flush grip flap with slim shadow reveal
        made.append(fittings.flush_handle("VPS_Handle_Flap_" + nm, x0 - 0.003, x1 + 0.003, zc + 0.018,
                                          proud, collection, lib["paint"], h=0.017, d=0.0018))
    return made


# ----------------------------------------------------------- arch cladding
def _arch_path(axle, r, z_bot, n_arc=48, n_leg=6):
    zc = S.WHEEL_R
    pts = [(axle + r, z_bot + (zc - z_bot) * i / float(n_leg)) for i in range(n_leg)]
    pts += [(axle + r * math.cos(math.pi * i / n_arc), zc + r * math.sin(math.pi * i / n_arc))
            for i in range(n_arc + 1)]
    pts += [(axle - r, zc - (zc - z_bot) * i / float(n_leg)) for i in range(1, n_leg + 1)]
    return pts


def build_cladding(collection, lib):
    """Gloss-black SUV wheel-arch cladding (r_in 0.466 .. r_out 0.532 m, flaring to 1.998 m width)."""
    made = []
    for tag, axle, width, flare, z_bot in (
        ("F", S.FRONT_AXLE, 0.056, 0.018, 0.285),
        ("R", S.REAR_AXLE, 0.056, 0.019, 0.305),
    ):
        r_out = S.ARCH_R + 0.010
        r_in = S.ARCH_R - width
        outer = _arch_path(axle, r_out, z_bot)
        inner = _arch_path(axle, r_in, z_bot)
        rows = []
        m = len(outer)
        for i in range(m):
            s = i / float(m - 1)
            f = flare * (0.35 + 0.65 * math.sin(math.pi * s))
            po, _no = on_flank(outer[i][0], outer[i][1], 0.0022)
            pi, _ni = on_flank(inner[i][0], inner[i][1], 0.0022 + f)
            lip = (pi[0], pi[1] - 0.048, pi[2])
            rows.append([po, pi, lip])
        ob = M.grid("VPS_Clad_" + tag, rows, collection, lib["black_gloss"],
                    geom.const((0.0, 1.0, 0.0)))
        M.solidify(ob, 0.003)
        M.mirror_y(ob)
        made.append(ob)
    return made


# ------------------------------------------------------------ fender ADAS gill
def build_vent(collection, lib):
    """Vertical gloss-black front-fender ADAS camera/LiDAR gill ahead of the front door."""
    ring = geom.polyline([(x, 0.95, z) for (x, z) in PN.VENT_OUTLINE + PN.VENT_OUTLINE[:1]], 40)[:-1]
    a, b, c = [], [], []
    for (x, _y, z) in ring:
        p, n = on_flank(x, z)
        a.append(p)
        b.append(tuple(p[k] - n[k] * 0.010 for k in range(3)))
        c.append(tuple(p[k] - n[k] * 0.028 for k in range(3)))
    a.append(a[0]); b.append(b[0]); c.append(c[0])
    frame = M.strip("VPS_Vent_Frame", a, b, collection, lib["black_gloss"])
    M.mirror_y(frame)
    cx = [sum(p[k] for p in c) / len(c) for k in range(3)]
    back = M.grid("VPS_Vent_Pocket", [[b[i], c[i], tuple(cx)] for i in range(len(b))],
                  collection, lib["black_gloss"], geom.const((0.0, 1.0, 0.0)))
    M.mirror_y(back)
    made = [frame, back]
    # Dual rearward-angled side ADAS cameras inside the fender gill (side_grid_mid u 1318, v 1665 & 1712)
    for i, zz in enumerate((0.935, 0.865)):
        pv, nv = on_flank(1.002, zz, -0.006)
        made += lamps.projector("VPS_Vent_Cam%d" % i, pv, (-0.55, 0.83, -0.05), 0.010,
                                collection, lib, mats=("chrome", "lamp_smoked"))
    return made


# ------------------------------------------------------------ charge flap
def build_charge_door(collection, lib):
    return [fittings.outline_ring("VPS_Charge_Line", -2.015, -1.735, 0.965, 1.135, 0.032,
                                  proud, collection, lib["shadow"], y_ref=0.91)]


def build_all(collection, lib):
    made = []
    made += build_mirrors(collection, lib)
    made += build_handles(collection, lib)
    made += build_cladding(collection, lib)
    made += build_vent(collection, lib)
    made += build_charge_door(collection, lib)
    return made
