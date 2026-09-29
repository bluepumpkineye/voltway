"""SU7 Ultra side details: mirrors, flush handles, carbon skirts, side stripe
and script, fender vent and charge-flap line - hardpoints from the
camera-matched side photograph, built with the carkit catalogue.

The side reference shows, beyond the sheet metal: carbon wing mirrors on the
doors, flush door handles, a carbon side skirt with a grey stripe above it on
the doors carrying the gold "Ultra" script at its forward end.
"""
import su7_surface as S
from su7_surface import Curve
import su7_front as FR
from carkit.parts import aero, fittings

proud = FR.proud


# ------------------------------------------------------------------ mirrors
def build_mirrors(collection, lib):
    """Teardrop head on a short chunky arm from the door skin."""
    return fittings.mirror_head("SU7Ultra_Mirror", collection, lib,
                                centre=(0.705, 1.000, 1.000), size=(0.235, 0.105, 0.095),
                                stalk_base=(0.760, 0.95, 0.940), proud=proud,
                                mats=("carbon", "mirror_glass", "black_gloss"))


# ------------------------------------------------------------------ handles
# Camera-matched: front handle 0.164 -> -0.066 at z 0.80, rear -0.867 ->
# -1.085 at 0.818. The first cut had them 0.25 m forward and 80 mm high.
HANDLES = (("F", 0.164, -0.066, 0.800), ("R", -0.867, -1.085, 0.818))


def build_handles(collection, lib):
    """Flush handles: a gloss black blade with rounded ends, set in the door."""
    return [fittings.flush_handle("SU7Ultra_Handle_" + nm, x0, x1, zc, proud,
                                  collection, lib["black_gloss"])
            for nm, x0, x1, zc in HANDLES]


# ------------------------------------------------------------- fender vent
# The black blade behind the front wheel, pointed at the front and square at
# the door edge: x 0.995-1.292, z 0.636-0.712 on the camera-matched photo.
VENT_UP = [(1.292, 0.707), (1.200, 0.712), (1.100, 0.712), (0.995, 0.710)]
VENT_LO = [(1.292, 0.703), (1.200, 0.672), (1.100, 0.648), (0.995, 0.636)]


def build_fender_vent(collection, lib):
    return fittings.vent("SU7Ultra_FenderVent", VENT_LO, VENT_UP, proud, collection, lib)


# ------------------------------------------------------------- charge door
def build_charge_door(collection, lib):
    """The shut line of the charge flap on the rear quarter: a thin dark ring.
    Rounded rectangle x -1.917..-1.685, z 0.827..0.969, measured."""
    return [fittings.outline_ring("SU7Ultra_ChargeDoor_Line", -1.917, -1.685, 0.827,
                                  0.969, 0.028, proud, collection, lib["shadow"])]


# ---------------------------------------------------------- skirt + stripe
X_SKIRT_F = 1.130            # just behind the front arch
X_SKIRT_R = -1.015           # just ahead of the rear arch

# The grey stripe sits ON the doors, not on the skirt: z 0.34-0.42 at the
# front door's leading edge rising to 0.39-0.45 where it ends, cut on a slant,
# at x = -0.75/-0.84.
STRIPE_TOP = Curve([(-0.860, 0.449), (-0.060, 0.443), (0.960, 0.419)], mode="pchip")
STRIPE_BOT = Curve([(-0.860, 0.392), (-0.060, 0.379), (0.960, 0.339)], mode="pchip")
STRIPE_FRONT = 0.948
STRIPE_END_LO, STRIPE_END_UP = -0.752, -0.841
B_SHUT = -0.160              # rear edge of the front door (su7_panels.X_BPILLAR_F)


def build_skirts(collection, lib):
    made = [aero.side_skirt("SU7Ultra_SideSkirt", collection, lib, proud,
                            lambda x: S.Y_ROCKER(x) + 0.02, X_SKIRT_R, X_SKIRT_F,
                            S.Z_FLOOR(0.0) + 0.012, 0.260)]

    # the stripe is a decal on each door, so it breaks at the shut line
    for nm, xa, xb, nx in (
            ("F", lambda k: B_SHUT + 0.004, lambda k: STRIPE_FRONT, 40),
            ("R", lambda k: STRIPE_END_LO + (STRIPE_END_UP - STRIPE_END_LO) * k,
             lambda k: B_SHUT - 0.004, 34)):
        made.append(fittings.surface_band("SU7Ultra_SideStripe_" + nm, xa, xb, STRIPE_BOT,
                                          STRIPE_TOP, proud, collection, lib["stripe"], nx))

    # Gold "Ultra" script at the stripe's forward end, and a small one on the
    # skirt near the rear. One object per side: a Mirror modifier would render
    # the right-hand script back to front.
    xs = 0.815
    zs = 0.5 * (STRIPE_BOT(xs) + STRIPE_TOP(xs))
    for tag, (px, pz, size, d) in (("", (xs, zs, 0.085, 0.0014)),
                                    ("_Skirt", (-0.620, 0.205, 0.030, 0.0100))):
        p, n = proud((px, 0.95, pz), d)
        for side, sgn in (("L", 1.0), ("R", -1.0)):
            made.append(fittings.text_badge(
                "SU7Ultra_Side_Ultra%s_%s" % (tag, side), "Ultra", size,
                (p[0], sgn * p[1], p[2]), (n[0], sgn * n[1], n[2]), collection,
                lib["rim_lip"], italic=True))
    return made


def build_all(collection, lib):
    made = []
    made += build_mirrors(collection, lib)
    made += build_handles(collection, lib)
    made += build_skirts(collection, lib)
    made += build_fender_vent(collection, lib)
    made += build_charge_door(collection, lib)
    return made
