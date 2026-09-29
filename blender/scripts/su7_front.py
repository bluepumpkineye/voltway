"""SU7 Ultra front-end details: lamps, splitter, intake mesh, plate, stripes,
lidar and the corner fins - hardpoints from the camera-matched photographs,
built with the carkit catalogue.

Everything SITS ON the body surface (su7_nose.BODY) rather than on a plane:
the first build placed every front part as an axis-aligned box on a flat plate,
which is why the lamps read as fluorescent tubes and the intake as a slatted
radiator grille.

Headlamps
---------
The SU7 lamp is a slanted sliver ("water-drop", ~5.4:1) whose inboard tip sits
on the nose and whose outboard end wraps round the fender corner - so it spans
BOTH the nose cap and the flank. It is built between two measured 3D edge
curves, placed by radial ray casts from inside the corner onto the built body
meshes and pushed ~4 mm proud, which is where the reference puts the lens.
On the Ultra the lens is smoked: only the DRL blade and four projector modules
in the outboard third light up.
"""
import math

import su7_surface as S
import su7_nose as N
import su7_panels as PN
from carkit import geom
from carkit import mesh as M
from carkit import place as P
from carkit.body import fascia as FA
from carkit.parts import aero, fittings, grilles, lamps

# ------------------------------------------------------------ placement
BODY = N.BODY
project = BODY.project
proud = BODY.proud

# Parts that wrap a corner are placed by casting from a point INSIDE the
# corner out through each authored point, onto the built body meshes.
PLACER = P.Placer(BODY.proud)
reset_bvh = PLACER.reset
_trees = PLACER.trees
surf_radial = PLACER.radial
_hit_along = PLACER.along

# helpers under their old names, for su7_rear and su7_side
_obj = M.obj
_grid = M.grid
_solidify = M.solidify
_polyline = geom.polyline
_lerp = geom.lerp
_away_from = geom.away_from
_smooth_grid = M.smooth_grid
text_mesh = M.text_mesh
_place_on_surface = P.on_surface


def _bevel(ob, w, seg=2, angle=40.0):
    return M.bevel(ob, w, seg, angle)


def _mirror(ob):
    return M.mirror_y(ob)


def body_side_point(x, z):
    """The body's outer surface at (x, z) on the left side, with its normal."""
    return BODY.side_point(x, z)


# --------------------------------------------------------------- headlamps
# Measured edges, left lamp (+Y). Both start at the inboard tip; the upper
# edge is 6 mm higher there so the tip is a sliver rather than a point.
# Heights re-measured through the matched side camera: the lens spans
# z 0.56-0.74 and its upper rear tip sits at (1.985, 0.738). The first cut
# had every point 182 mm higher, above the fender line of the real car.
# The outboard end wraps onto the side of the fender (y ~0.94 at this height).
LAMP_UPPER = [(2.405, 0.400, 0.598), (2.360, 0.600, 0.648), (2.245, 0.740, 0.676),
              (2.090, 0.870, 0.718), (1.975, 0.938, 0.742)]
# The lower edge sags to z 0.56 under the outboard half: from the side the
# lens spans 0.56-0.74 and reads as a fat teardrop, not a sliver.
LAMP_LOWER = [(2.405, 0.400, 0.590), (2.340, 0.600, 0.575), (2.235, 0.745, 0.563),
              (2.110, 0.860, 0.562), (2.040, 0.910, 0.592), (1.995, 0.940, 0.652)]
LAMP_PROUD = 0.0040
NS, NK = 56, 8
LAMP_CENTRE = (1.90, 0.45, 0.62)
LAMP_BODY = ("SU7Ultra_Fascia_Upper", "SU7Ultra_Fascia_Cheek",
             "SU7Ultra_Fender_Front", "SU7Ultra_Hood")
# projector modules crammed into the outboard third, as (y, z)
LAMP_MODULES = [(0.715, 0.678), (0.775, 0.680), (0.812, 0.698), (0.848, 0.700),
                (0.868, 0.670)]


def _lamp_place(p, d):
    return surf_radial(p, LAMP_CENTRE, LAMP_BODY, d)


def _crown(k, extra=0.0):
    """How proud the lens sits at edge fraction k: 4 mm plus a 1.6 mm crown."""
    crown = 0.0016 * math.sin(math.pi * max(0.0, min(1.0, k)))
    return LAMP_PROUD + crown + extra


def build_headlamps(collection, lib):
    made = []
    lo = _polyline(LAMP_LOWER, NS)
    up = _polyline(LAMP_UPPER, NS)
    out = _away_from((2.15, 0.60, 0.70))

    # lens: smoked, opaque gloss black with a faint crown
    made.append(lamps.lens("SU7Ultra_Lamp_Lens", lo, up, _lamp_place, collection,
                           lib["lamp_smoked"], NK, lambda k, nk: _crown(k / float(nk)),
                           out, thickness=0.0035, bevel=(0.0012, 2, 30)))
    # seal bands just outside both edges: set into the body, not a sticker
    made += lamps.seals("SU7Ultra_Lamp_Seal", lo, up, _lamp_place, collection,
                        lib["grille"], out, width=0.0055, d=0.0010)
    # DRL: one light guide in the lower third, running most of the lamp - the
    # only emissive geometry in the assembly
    k0, k1 = 0.16, 0.30
    made.append(lamps.band_between("SU7Ultra_Lamp_DRL0", lo, up, range(1, int(NS * 0.86)),
                                   [k0 + (k1 - k0) * c / 2.0 for c in range(3)],
                                   _lamp_place, lambda k: _crown(k, 0.0006), collection,
                                   lib["led_white"], out))
    # projector modules, crammed into the outboard third
    for m_i, (yy, zz) in enumerate(LAMP_MODULES):
        best = lamps.station_nearest_y(lo, up, yy)
        zl, zu = lo[best][2], up[best][2]
        k = max(0.25, min(0.85, (zz - zl) / max(1e-4, zu - zl)))
        c, n = surf_radial(_lerp(lo[best], up[best], k), LAMP_CENTRE, LAMP_BODY,
                           LAMP_PROUD + 0.0022)
        made += lamps.projector("SU7Ultra_Lamp_Proj%d" % m_i, c, n, 0.0135, collection, lib)
    return made


# ---------------------------------------------------------------- splitter
# Measured leading edge in plan, left half: (y, x_leading_edge, z_top).
# Swept back as a shallow V: through the matched side camera the splitter's
# silhouette never passes u = 13 px, which caps its leading edge at
# x = 2.55 - 0.34 y. No strakes and no endplate: the corner fin is the fence.
SPLITTER_LE = [(0.000, 2.5575, 0.119), (0.140, 2.5050, 0.119),
               (0.280, 2.4520, 0.120), (0.400, 2.4080, 0.123),
               (0.500, 2.3720, 0.130), (0.600, 2.3380, 0.140),
               (0.700, 2.3020, 0.150), (0.780, 2.2750, 0.154),
               (0.850, 2.2450, 0.158), (0.905, 2.1500, 0.162)]


def build_splitter(collection, lib):
    # the deck runs back under the black U
    return aero.splitter(
        "SU7Ultra_Splitter_", collection, lib, SPLITTER_LE,
        zones=(("Centre", 0.0, 0.52, "carbon"), ("Wing", 0.52, 0.905, "paint")),
        x_te=lambda y, xle: min(xle - 0.080, 2.285 - 0.10 * max(0.0, (y - 0.55) / 0.36)),
        thickness=0.014, bevel=(0.0035, 3, 30))


# -------------------------------------------------------------- intake mesh
def build_intake_mesh(collection, lib):
    x_on_u = FA.recessed_x(N.NOSE, PN.U_DEPTH)
    made = []
    for nm, box, back in (("Main", (0.0, 0.370, 0.252, 0.460), 0.032),
                          ("Corner", (0.442, 0.770, 0.208, 0.445), 0.036)):
        m = grilles.diamond("SU7Ultra_Intake_Mesh_" + nm, box[0], box[1], box[2], box[3],
                            x_on_u, back, collection, lib["grille"])
        _mirror(m)
        made.append(m)
    return made


# --------------------------------------------------------- plate + lettering
def build_plate(collection, lib):
    """The 'SU7 Ultra' show plaque in the plate plinth."""
    p, n = proud((2.46, 0.0, 0.560), 0.0015)
    return fittings.plate("SU7Ultra_Plate", p, n, collection, lib, w=0.440, h=0.140,
                          texts=(("SU7", -0.080, 0.070, False, True),
                                 ("Ultra", 0.080, 0.070, True, False)))


# ------------------------------------------------------------------ stripes
STRIPE_Y = (0.0075, 0.1075)       # each stripe 100 mm, 15 mm gap on centre


def _centre_path():
    """(x, z) along the car's top centreline, from the plate up over the nose
    and back along the hood to the cowl."""
    path = []
    for i in range(18):
        z = 0.636 + (N.NOSE_Z_HI - 0.004 - 0.636) * i / 17.0
        path.append((N.NOSE_X_OF_Z(z), z))
    xj = N.JOIN_F(1.0)
    for i in range(1, 60):
        x = xj - (xj - PN.X_COWL - 0.01) * i / 59.0
        path.append((x, S.Z_ROOF(x)))
    return path


def build_stripes(collection, lib):
    return [fittings.centre_stripes("SU7Ultra_Stripes_Hood", _centre_path(),
                                    STRIPE_Y[0], STRIPE_Y[1], proud, collection,
                                    lib["stripe"])]


# --------------------------------------------------------------- corner fin
# The air-curtain fin at each front corner: a body-colour plate standing proud
# of the bumper, low at the nose (z 0.25) and rising to 0.47 at the wheel
# arch, its rear edge just ahead of the wheel opening. Above its front end the
# corner intake shows black. Measured off the side photos.
FIN_TOP = [(2.300, 0.252), (2.230, 0.285), (2.150, 0.330), (2.060, 0.395),
           (2.005, 0.440), (1.976, 0.462)]
FIN_Z0 = 0.168
FIN_STAND = 0.022
FIN_INTAKE_TOP = [(2.330, 0.440), (2.290, 0.420), (2.230, 0.385), (2.160, 0.340),
                  (2.120, 0.318)]


def build_corner_fin(collection, lib):
    """The fin is the body's smooth surface pushed out 22 mm and made solid,
    from the ANALYTIC flank and nose surfaces - rays onto the meshes hit the
    painted cheek, the recessed black mouth and the lower lip in turn at the
    bottom of the corner, and the fin crumpled."""
    fin = aero.corner_fin("SU7Ultra_CornerFin", collection, lib, FIN_TOP, FIN_Z0,
                          FIN_STAND, BODY.side_point, n=30, nk=7, smooth_passes=2)
    # the corner intake above the fin's front end: dark, just proud of the body
    hole = fittings.side_patch("SU7Ultra_CornerIntake",
                               [(x, z + 0.004) for (x, z) in FIN_TOP[:4]],
                               FIN_INTAKE_TOP, BODY.side_point, collection,
                               lib["shadow"], d=0.0015, n=12, nk=3)
    return [fin, hole]


# ------------------------------------------------------------------- lidar
def build_lidar(collection, lib):
    """The roof lidar pod at the windscreen header - the small black bump in
    every side and front photograph of the car."""
    cx = 0.325
    return [fittings.lidar_pod("SU7Ultra_Lidar", collection, lib["black_gloss"], cx,
                               S.Z_ROOF(cx) - 0.012)]


def build_all(collection, lib):
    reset_bvh()
    made = []
    made += build_headlamps(collection, lib)
    made += build_splitter(collection, lib)
    made += build_intake_mesh(collection, lib)
    made += build_plate(collection, lib)
    made += build_stripes(collection, lib)
    made += build_lidar(collection, lib)
    made += build_corner_fin(collection, lib)
    return made
