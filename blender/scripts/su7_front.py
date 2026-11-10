"""SU7 Ultra front-end details: lamps, splitter, intake mesh, plate, stripes,
lidar and the corner fins - hardpoints from the camera-matched photographs,
built with the carkit catalogue.

Everything SITS ON the body surface (su7_nose.BODY) rather than on a plane:
the first build placed every front part as an axis-aligned box on a flat plate,
which is why the lamps read as fluorescent tubes and the intake as a slatted
radiator grille.

Headlamps
---------
The SU7 lamp is a compact almond (see the section below) whose rounded outboard
end wraps round the fender corner and whose pointed inboard tip sits on the nose
- so it spans BOTH the nose cap and the flank. It is laid by the maker's head-on
photograph's own rays onto the built body panels (carkit.photolay), a few mm
proud. Only the DRL bar and the three projector modules light up.
"""
import math

import su7_surface as S
import su7_nose as N
import su7_panels as PN
import ref_match as RM
import su7_lampdata as LD
from mathutils import Vector
from carkit import geom
from carkit import photolay as PL
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
# The SU7's lamp is a compact ALMOND (~1.4:1, 33 x 24 cm): a rounded outboard end wrapping the fender corner, a straight top
# edge falling to a pointed inboard tip that points at the plate, a full curve along the bottom; a black frame, a grey
# reflector in the upper half, ONE diagonal DRL bar from the outer end to the tip, three projector modules (the Ultra's
# lens is clear: the maker's head-on photograph shows right into it). 2026-11-03, the owner: "the real car has its
# headlight like an almond shape, while our render has something larger that changes the car's front look". The first
# build laid a slanted sliver between two measured edge curves (~5:1, 0.56-0.74 m high, past the fender line): too
# large and the wrong shape.
#
# The outline is read from big_023.jpg through ref_match's "head_on" camera (su7_lampdata, porting/su7_lamp_trace): each
# outline point is sent along the photo's own ray onto the nose, fender and hood panels (carkit.photolay), so it lands
# where the real car has it - on the fender corner as well as on the nose.
SURF_PANELS = ("SU7Ultra_Fascia_Upper", "SU7Ultra_Fascia_Cheek", "SU7Ultra_Fender_Front", "SU7Ultra_Hood")
_SURF = []


def _surf():
    if not _SURF:
        _SURF.append(PL.Surf(SURF_PANELS, x_range=(2.50, 1.80)))
    return _SURF[0]


def _on_surface(u, v, cam="head_on", inset=0.0):
    """(point, outward normal) of the panels under pixel (u, v) of the photo's left half, on the half sheet."""
    o, d = RM.ray(cam, u, v)
    o, d = Vector((o.x, -o.y, o.z)), Vector((d.x, -d.y, d.z))
    h = _surf().hit(o, d, inset)
    if h is None:
        raise RuntimeError("su7_front: the photo ray through (%g, %g) misses the nose" % (u, v))
    return h


LAY = PL.Lay(_on_surface, geom.away_from((1.90, 0.45, 0.60)))

# how far each layer stands off the paint (m): frame, reflector, DRL bar, projector base
FRAME_UP, SILVER_UP, DRL_UP_D, MODULE_UP = 0.0020, 0.0027, 0.0034, 0.0034


def reset_lamp_surf():
    del _SURF[:]


def build_headlamps(collection, lib):
    made = []
    reset_lamp_surf()
    # the frame: the whole almond, black glass, with a hair's grow so the paint never shows round it
    made.append(LAY.region("SU7Ultra_Lamp_Frame", PL.grow(LD.LAMP_OUT, 0.8), FRAME_UP, lib["lamp_frame"], collection,
                           step=6.5, thick=0.0016, bevel=0.0008))
    # the reflector that shows through the upper half
    made.append(LAY.region("SU7Ultra_Lamp_Silver", LD.SILVER, SILVER_UP, lib["lamp_silver"], collection,
                           step=5.5, thick=0.0006))
    # one DRL bar from the outer end to the tip: the only emissive geometry in the assembly (the Lights tab lights it)
    made.append(LAY.band("SU7Ultra_Lamp_DRL0", LD.DRL_UP, LD.DRL_LO, 40, 2, DRL_UP_D, lib["led_white"], collection,
                         thick=0.0004))
    # projector modules: a dark bowl with a lens, ahead of the reflector (they light with the low beam)
    for k, (u, v, r_px) in enumerate(LD.MODULES):
        p, n = _on_surface(u, v)
        r = r_px * 0.0022
        made += lamps.projector("SU7Ultra_Lamp_Proj%d" % k, tuple(p + n * MODULE_UP), tuple(n), r, collection, lib)
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
    # 2026-11-03: re-read from the head-on photograph (big_023.jpg through ref_match's "head_on" camera): the plaque spans
    # z 0.37-0.515 (centre 0.443) and 0.49 m across; it sat 0.117 m too high and 5 cm too narrow
    p, n = proud((2.46, 0.0, 0.443), 0.0015)
    return fittings.plate("SU7Ultra_Plate", p, n, collection, lib, w=0.488, h=0.145,
                          texts=(("SU7", -0.080, 0.070, False, True),
                                 ("Ultra", 0.080, 0.070, True, False)))


# ------------------------------------------------------------------ stripes
STRIPE_Y = (0.0075, 0.1075)       # each stripe 100 mm, 15 mm gap on centre
Z_STRIPE_0 = 0.525                # the stripes start at the plaque's top edge (big_023.jpg: z 0.52)


def _centre_path():
    """(x, z) along the car's top centreline: the nose's face from the plate up to its top, then the hood back to the
    cowl. The stretch over the cap's top, between the two, is laid by rays down onto the panels (_stripe_rows)."""
    face, hood = [], []
    for i in range(18):
        z = Z_STRIPE_0 + (N.NOSE_Z_HI - 0.004 - Z_STRIPE_0) * i / 17.0
        face.append((N.NOSE_X_OF_Z(z), z))
    xj = N.JOIN_F(1.0)
    for i in range(1, 60):
        x = xj - (xj - PN.X_COWL - 0.01) * i / 59.0
        hood.append((x, S.Z_ROOF(x)))
    return face, hood


def _stripe_rows(cols=4, d=0.0006):
    """Rows of the two stripes' grid (left half), every point a ray onto the BUILT panels (45 degrees down over the
    nose's face, vertical over the cap's top and the hood). The analytic surface (`proud`) put the stripes 0.5-1 mm
    under the paint in places on the new hood (ragged edges) and cannot place the cap's top at all (`WrapCap.wv_at` is not
    monotone above the join ring's crown): the stripes had a 4.5 cm gap there."""
    face, hood = _centre_path()
    ys = [STRIPE_Y[0] + (STRIPE_Y[1] - STRIPE_Y[0]) * c / float(cols - 1) for c in range(cols)]
    diag = Vector((-1.0, 0.0, -1.0)).normalized()
    down = Vector((0.0, 0.0, -1.0))

    def row(x, z, vertical):
        out = []
        for y in ys:
            o, dr = (Vector((x, y, 1.6)), down) if vertical else (Vector((x + 0.3, y, z + 0.3)), diag)
            p, n = _surf().hit(o, dr)
            out.append(tuple(p + n * d))
        return out
    rows = [row(x, z, False) for (x, z) in face]
    x0, x1 = face[-1][0], N.JOIN_F(1.0)
    rows += [row(x0 + (x1 - x0) * i / 8.0, 0.0, True) for i in range(1, 9)]
    rows += [row(x, z, True) for (x, z) in hood]
    return rows


def build_stripes(collection, lib):
    ob = M.grid("SU7Ultra_Stripes_Hood", _stripe_rows(), collection, lib["stripe"], geom.const((0.0, 0.0, 1.0)))
    M.mirror_y(ob)
    return [ob]


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
