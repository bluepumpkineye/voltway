"""Zeekr 7X side details: mirrors with their camera pods, flush door handles, the black
fender gill with its camera, the charge flap, sills with a silver strip, the roof lidar.

Positions were read off the side photograph (side_left_studio.jpg, the solved camera
zx_ref_match / zx_camsolve.side_xz) in PIXELS and converted at the plane each part
lies on; the zoomed, gridded crops (gh_front, sA, sB, sC, 25 px grid) are in the
scratch notes.

    mirrors     silver caps over a black underside, glass on the rear face: head
                x 0.69-0.87, z 1.10-1.24, tips at y +/-1.02; under each a black pod with
                the side camera (x 0.71-0.90, z 1.025-1.087)
    handles     flush, recessed: front door x -0.02..0.20 at z 0.96, rear door
                x -1.11..-0.88 at z 1.00
    gill        a black panel behind the front wheel opening, from the hood line down
                to z 0.79, ending at the door's leading edge (x 1.05), with a camera
    charge flap left rear quarter only: x -1.62..-1.36, z 0.90-1.075
    sills       black rocker z 0.204-0.343 from arch to arch, a silver blade z 0.24-0.29
    lidar       a low black pod on the roof's leading edge: x 0.29-0.42, 0.236 m wide
"""
import math

import zx_surface as S
import zx_nose as N
import zx_panels as PN
import zx_camsolve as CS
from carkit import geom
from carkit import mesh as M
from carkit.parts import aero, fittings, lamps

BODY = N.BODY
proud = BODY.proud


def _xz(px, y):
    """Side-photo pixels -> [(x, z)] on the plane y."""
    return [CS.side_xz(u, v, y) for (u, v) in px]


# ------------------------------------------------------------------ mirrors
MIRROR_REAR = (0.691, 0.950, 1.168)      # the glass face's centre
MIRROR_SIZE = (0.175, 0.150, 0.142)      # depth, width, height
MIRROR_ARM = (0.780, 0.890, 1.098)       # where the arm leaves the door


def build_mirrors(collection, lib):
    made = fittings.mirror_cap("ZX_Mirror", collection, lib, rear=MIRROR_REAR,
                               size=MIRROR_SIZE, arm_base=MIRROR_ARM, proud=proud, arm_t=0.030,
                               mats=("trim_silver", "mirror_glass", "black_gloss", "black_gloss"))
    # the camera pod under it (sB crop: a black wedge with the lens facing down and out)
    x0, x1, z0, z1 = 0.713, 0.900, 1.025, 1.087
    cx, cy = 0.5 * (x0 + x1), 0.915
    rows = []
    for (x, dz) in ((x1, 0.0), (0.5 * (x0 + x1), 0.012), (x0, 0.004)):
        rows.append([(x, cy + dy, z0 + dz + (z1 - z0) * f)
                     for dy, f in ((-0.062, 0.45), (-0.040, 0.0), (0.040, 0.0), (0.062, 0.45))])
    pod = M.grid("ZX_Mirror_Pod", rows, collection, lib["black_gloss"], geom.away_from((cx, 0.8, 1.1)))
    M.solidify(pod, 0.012)
    M.mirror_y(pod)
    made.append(pod)
    made += lamps.projector("ZX_Mirror_Cam", (cx + 0.02, cy, z0 + 0.0075), (0.0, 0.0, -1.0), 0.011,
                            collection, lib)
    return made


# ------------------------------------------------------------------ handles
HANDLES = (("F", -0.021, 0.203, 0.961), ("R", -1.107, -0.881, 1.001))


def build_handles(collection, lib):
    made = []
    for nm, x0, x1, zc in HANDLES:
        made.append(fittings.flush_handle("ZX_Handle_" + nm, x0, x1, zc, proud, collection,
                                          lib["black_gloss"], h=0.019, d=0.0012, y_ref=0.90))
        made.append(fittings.outline_ring("ZX_Handle_Rim_" + nm, x0 - 0.002, x1 + 0.002,
                                          zc - 0.0235, zc + 0.0235, 0.0235, proud, collection,
                                          lib["chrome"], width=0.0012, d=0.0010, y_ref=0.90,
                                          mirror=True))
    return made


# ------------------------------------------------------------- the fender gill
GILL_UP = [(1.403, 0.923), (1.255, 0.934), (1.107, 0.921), (1.053, 0.910)]
GILL_LO = [(1.403, 0.923), (1.344, 0.861), (1.256, 0.813), (1.137, 0.788), (1.053, 0.792)]


def build_gill(collection, lib):
    made = [fittings.side_patch("ZX_Gill", GILL_LO, GILL_UP, BODY.side_point, collection,
                                lib["black_gloss"], d=0.0022, n=28, nk=4, y_ref=0.85,
                                outward=(0.0, 1.0, 0.0))]
    # its camera: a small wedge with a lens, at the panel's lower edge
    p, n = BODY.side_point(1.093, 0.822)
    c = (p[0] + n[0] * 0.0045, p[1] + n[1] * 0.0045, p[2] + n[2] * 0.0045)
    made += lamps.projector("ZX_Gill_Cam", c, n, 0.012, collection, lib)
    return made


def _on_flank(x, z, d=0.0):
    p, n = BODY.side_point(x, z)
    return (p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d), n


# ------------------------------------------------------------ charge flap
def build_charge_door(collection, lib):
    return [fittings.outline_ring("ZX_Charge_Line", -1.620, -1.358, 0.903, 1.075, 0.040,
                                  proud, collection, lib["shadow"], y_ref=0.88)]


# ----------------------------------------------------------- arch cladding
# The black plastic ring round each wheel opening (side photograph: its outer edge on the
# paint at ~0.515 from the hub, its inner lip at ~0.435, a thin line outside the tyre)
# and the flare that carries the car out to its 1930 mm: the painted flank is only
# ~0.89 (front) / 0.85 (rear) from the centreline, the tyres' walls are at 0.957, and the
# cladding's inner edge stands out to ~0.945 over the top and ~0.962 down the legs (the
# front and rear photographs: body and tyre outlines are flush at the arches).
CLAD = (("F", S.FRONT_AXLE, 0.080, 0.300, 0.962, 0.946),
        ("R", S.REAR_AXLE, 0.082, 0.300, 0.962, 0.946))      # tag, axle, width, z_bot, y_leg, y_top


def _arch_path(axle, r, z_bot, n_arc=48, n_leg=6):
    """Side-elevation path round a wheel opening: up the front leg, over the arch, down
    the rear leg (the opening's straight sides run into the sill)."""
    zc = S.WHEEL_R
    pts = [(axle + r, z_bot + (zc - z_bot) * i / float(n_leg)) for i in range(n_leg)]
    pts += [(axle + r * math.cos(math.pi * i / n_arc), zc + r * math.sin(math.pi * i / n_arc))
            for i in range(n_arc + 1)]
    pts += [(axle - r, zc - (zc - z_bot) * i / float(n_leg)) for i in range(1, n_leg + 1)]
    return pts


def build_cladding(collection, lib):
    made = []
    for tag, axle, width, z_bot, y_leg, y_top in CLAD:
        r_out = S.ARCH_R + 0.012                 # laps 12 mm over the paint
        r_in = S.ARCH_R - width
        outer = _arch_path(axle, r_out, z_bot)
        inner = _arch_path(axle, r_in, z_bot)
        rows = []
        m = len(outer)
        for i in range(m):
            s = i / float(m - 1)
            po, _ = _on_flank(outer[i][0], outer[i][1], 0.0025)
            pb, _ = _on_flank(inner[i][0], inner[i][1], 0.0)
            # the inner edge stands out to its target width: full over the top, wider down the legs
            k = (1.0 - math.sin(math.pi * s)) ** 1.3
            yt = y_top + (y_leg - y_top) * k
            pi = (pb[0], max(pb[1] + 0.02, yt), pb[2])
            lip = (pi[0], pi[1] - 0.050, pi[2])
            rows.append([po, pi, lip])
        ob = M.grid("ZX_Clad_" + tag, rows, collection, lib["cladding"], geom.const((0.0, 1.0, 0.0)))
        M.solidify(ob, 0.003)
        M.mirror_y(ob)
        made.append(ob)
    return made


# ------------------------------------------------------------------ sills
X_SKIRT_F = S.FRONT_AXLE - S.ARCH_R + 0.005
X_SKIRT_R = S.REAR_AXLE + S.ARCH_R - 0.005


def build_sills(collection, lib):
    made = [aero.side_skirt("ZX_Skirt", collection, lib, proud,
                            lambda x: S.Y_ROCKER(x) + 0.02, X_SKIRT_R, X_SKIRT_F,
                            0.204, 0.343, nx=60, nz=6, d=0.006, mat="black_gloss")]
    # the silver blade: z 0.236 at the front, 0.29 behind the doors (the sill rises)
    made.append(fittings.surface_band("ZX_Skirt_Strip",
                                      lambda k: X_SKIRT_R + 0.02, lambda k: X_SKIRT_F - 0.02,
                                      lambda x: 0.236 + (0.975 - x) * 0.0470 / 1.056,
                                      lambda x: 0.2645 + (0.975 - x) * 0.0470 / 1.056,
                                      lambda p, d: proud(p, 0.0105), collection,
                                      lib["chrome"], 60, nk=3, y_ref=0.90))
    return made


# ------------------------------------------------------------------ lidar
def build_lidar(collection, lib):
    cx = 0.355
    zc = S.Z_ROOF(cx) - 0.018
    return [fittings.lidar_pod("ZX_Lidar", collection, lib["black_gloss"], cx, zc,
                               a=0.067, b=0.118, c=0.058)]


def build_all(collection, lib):
    made = []
    made += build_mirrors(collection, lib)
    made += build_handles(collection, lib)
    made += build_gill(collection, lib)
    made += build_charge_door(collection, lib)
    made += build_cladding(collection, lib)
    made += build_sills(collection, lib)
    made += build_lidar(collection, lib)
    return made
