"""XPeng G9L side details: mirrors, flush door handles, the front fender's sensor patch, the black
rocker strip along the doors, the side step bar, and the hood and fender shut lines.

Positions are read off the white car's side photograph (c1_0028, camera "side_white") through
g9l_panels._flank_pts, which turns pixels into model metres ON the built surface:

  mirror     a body-colour cap over a black underside, 0.19 long, 0.165 wide, 0.17 tall, its glass
             facing aft at x 0.755, centred at z 1.265, y 1.015 (the outer edge at 1.10 as the front
             photograph shows), on a black arm from the door's upper front corner
  handles    flush, outlined, front x 0.11-0.32 at z 1.066, rear x -1.12 to -0.90 at z 1.11
  rocker     a black strip on the doors from the front arch's rear edge (x 1.2) to the rear arch's
             front edge (x -1.0): 0.10 tall at its deepest (z 0.375-0.476), pointed at both ends'
             tapers; below it the body-colour sill and a black step bar at z 0.215-0.255
  fender     a small body-colour teardrop patch with a black lens ahead of the front door (x 1.17-1.31,
             z 0.97-1.05), outlined
"""
import math

import g9l_surface as S
import g9l_nose as N
import g9l_panels as PN
from carkit import geom
from carkit import mesh as M
from carkit.parts import fittings

BODY = N.BODY
proud = BODY.proud


def _pts(px, y0=0.96):
    return PN._flank_pts(px, y0)


# ------------------------------------------------------------------ mirrors
MIRROR_REAR = (0.755, 1.015, 1.265)      # centre of the glass face
MIRROR_SIZE = (0.190, 0.165, 0.170)      # depth, width, height
MIRROR_ARM = (0.880, 0.955, 1.125)       # arm's base on the door skin


def build_mirrors(collection, lib):
    made = fittings.mirror_cap(
        "G9L_Mirror", collection, lib, rear=MIRROR_REAR, size=MIRROR_SIZE, arm_base=MIRROR_ARM,
        proud=proud, nose=0.30, drop=0.22, split=-0.22, arm_t=0.020,
        mats=("paint", "mirror_glass", "black_gloss", "black_gloss"))
    return made


# ------------------------------------------------------------------ handles
HANDLES = (("F", 0.108, 0.318, 1.066), ("R", -1.115, -0.898, 1.110))


def build_handles(collection, lib):
    made = []
    for nm, x0, x1, zc in HANDLES:
        made.append(fittings.flush_handle("G9L_Handle_" + nm, x0, x1, zc, proud, collection,
                                          lib["paint"], h=0.0135, d=0.0012, y_ref=0.97))
        made.append(fittings.outline_ring("G9L_Handle_Rim_" + nm, x0 - 0.002, x1 + 0.002,
                                          zc - 0.0185, zc + 0.0185, 0.0185, proud, collection,
                                          lib["black_gloss"], width=0.0016, d=0.0008, y_ref=0.97,
                                          mirror=True))
    return made


# ------------------------------------------------------------ fender patch
def build_fender_patch(collection, lib):
    made = []
    x0, x1, z0, z1 = 1.172, 1.312, 0.972, 1.048
    made.append(fittings.outline_ring("G9L_Fender_Patch", x0, x1, z0, z1, 0.034, proud, collection,
                                      lib["black_gloss"], width=0.0014, d=0.0006, y_ref=0.93,
                                      mirror=True))
    # the black lens at the patch's rear end
    lo = [(x0 + 0.004, z0 + 0.016), (x0 + 0.050, z0 + 0.016)]
    up = [(x0 + 0.004, z1 - 0.014), (x0 + 0.050, z1 - 0.014)]
    made.append(fittings.flank_patch("G9L_Fender_Lens", lo, up, proud, collection, lib["black_gloss"],
                                     0.0012, nk=2, y_ref=0.93))
    M.mirror_y(made[-1])
    return made


# -------------------------------------------------------------- rocker strip
ROCKER_UP_PX = [(1118, 1850), (1250, 1846), (1500, 1836), (1895, 1826), (2000, 1822), (2250, 1820),
                (2330, 1818), (2400, 1830), (2480, 1845), (2590, 1850)]
ROCKER_LO_PX = [(1121, 1884), (1210, 1882), (1263, 1897), (1342, 1910), (1526, 1905), (1913, 1895),
                (2000, 1887), (2250, 1873), (2400, 1862), (2500, 1855), (2590, 1850)]


def build_rocker(collection, lib):
    made = []
    up = _pts(ROCKER_UP_PX)
    lo = _pts(ROCKER_LO_PX)
    # equal point counts along each edge, ends joined
    n = 64
    strip = fittings.flank_patch("G9L_Rocker_Strip", lo, up, proud, collection, lib["black_trim"],
                                 0.0016, nk=4, n=n, y_ref=0.97)
    M.mirror_y(strip)
    M.finish(strip, thickness=0.0016, bevel=0.0)
    made.append(strip)
    # the side step: a flat black bar under the doors, set out from the sill
    x0, x1 = -0.985, 1.185
    ob = _box("G9L_Step_Bar", x0, x1, 0.935, 1.0, 0.205, 0.256, collection, lib["black_trim"])
    M.mirror_y(ob)
    made.append(ob)
    return made


def _box(name, x0, x1, y0, y1, z0, z1, collection, mat):
    v = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    f = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
    c = (0.5 * (x0 + x1), 0.5 * (y0 + y1), 0.5 * (z0 + z1))
    ob = M.obj(name, v, f, collection, mat)
    M.orient(ob.data, geom.away_from(c))
    M.bevel(ob, 0.006, 2, 40)
    return ob


# --------------------------------------------------------------- shut lines
def _line(name, px, collection, mat, width=0.0028, y0=0.93, d=0.0010):
    pts = _pts(px, y0)
    lo = pts
    up = [(x, z + width) for (x, z) in pts]
    ob = fittings.flank_patch(name, lo, up, proud, collection, mat, d, nk=1, y_ref=y0)
    M.mirror_y(ob)
    return ob


def build_lines(collection, lib):
    made = []
    # the fender's diagonal seam from the lamp bar's end to the arch's crown (a hair-line)
    made.append(_line("G9L_Fender_Seam", __import__("g9l_cam").FENDER_SEAM_PX, collection, lib["black_gloss"],
                      width=0.0022))
    return made


# ------------------------------------------------------------- build all
def build_all(collection, lib):
    made = []
    made += build_mirrors(collection, lib)
    made += build_handles(collection, lib)
    made += build_fender_patch(collection, lib)
    made += build_rocker(collection, lib)
    made += build_lines(collection, lib)
    return made
