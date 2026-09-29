"""Start a new car from a donor body, scaled to its published dimensions.

The slowest part of a new car is its profile curves. A donor - the SU7, or any
later car closer in type - morphed to the target's length, width, height,
wheelbase and overhangs is a far better first surface than a blank one: it
builds immediately, it can be overlaid on the target's photographs through
the matched camera from day one, and every curve is then edited toward the
photographs one at a time.

    m = morph.from_donor(su7_nose.BODY, length=5.020, width=2.007,
                         height=1.585, wheelbase=3.000, front_overhang=0.985,
                         wheel_r=0.3700)
    m["body"]        a CarBody (loft + caps) ready to build panels on
    m["xmap"]        station map donor -> target, for the donor's layout lines
    print(morph.source(m))    the morphed curves as Python, to paste into
                              <car>_surface.py / <car>_nose.py and edit

Stations are mapped piecewise-linearly between the four hardpoints that the
published data fixes exactly - rear end, rear axle, front axle, front end - so
the wheels land exactly and each overhang stretches on its own. Widths scale
with the width, heights with the height. That is only a start: an SUV is not a
tall sedan (the greenhouse and the sill grow differently), which is exactly
what the camera-matched overlay shows next.
"""
from ..geom import Curve, Joined
from .loft import LoftBody
from .caps import WrapCap
from .model import CarBody

Z_CURVES = ("Z_ROOF", "Z_FLOOR", "Z_HIP", "Z_SHOULDER", "Z_CREST")
Y_CURVES = ("Y_HIP", "Y_SHOULDER", "Y_ROOF", "Y_ROCKER", "UNDERCUT")


def station_map(src, dst):
    """Piecewise-linear x map through (rear end, rear axle, front axle, front end)."""
    xs, xd = list(src), list(dst)

    def f(x):
        if x <= xs[0]:
            return xd[0] + (x - xs[0]) * (xd[1] - xd[0]) / (xs[1] - xs[0])
        for i in range(3):
            if x <= xs[i + 1] or i == 2:
                t = (x - xs[i]) / (xs[i + 1] - xs[i])
                return xd[i] + (xd[i + 1] - xd[i]) * t
        return x
    return f


def _map_curve(c, fx, fy):
    return c.mapped(fx, fy)


def from_donor(donor, *, length, width, height, wheelbase, front_overhang,
               wheel_r=None, arch_gap=None, name="new car", crease=None):
    """Morph a CarBody (donor.loft, donor.nose, donor.tail) to new dimensions."""
    L0 = donor.loft
    half_l = length / 2.0
    fa = half_l - front_overhang
    ra = fa - wheelbase
    xmap = station_map((-L0.HALF_L, L0.REAR_AXLE, L0.FRONT_AXLE, L0.HALF_L),
                       (-half_l, ra, fa, half_l))
    ky = width / L0.WIDTH
    kz = height / L0.HEIGHT
    wr = wheel_r or L0.WHEEL_R * kz
    gap = L0.ARCH_R - L0.WHEEL_R if arch_gap is None else arch_gap

    curves = {}
    for n in Z_CURVES:
        curves[n] = _map_curve(getattr(L0, n), xmap, lambda x, y: y * kz)
    for n in Y_CURVES:
        curves[n] = _map_curve(getattr(L0, n), xmap, lambda x, y: y * ky)

    loft = LoftBody(
        name=name, length=length, width=width, height=height,
        front_axle=fa, rear_axle=ra, wheel_r=wr, arch_r=wr + gap,
        z_roof=curves["Z_ROOF"], z_floor=curves["Z_FLOOR"], y_hip=curves["Y_HIP"],
        z_hip=curves["Z_HIP"], z_shoulder=curves["Z_SHOULDER"],
        y_shoulder=curves["Y_SHOULDER"], y_roof=curves["Y_ROOF"],
        y_rocker=curves["Y_ROCKER"], undercut=curves["UNDERCUT"],
        z_crest=curves["Z_CREST"], v_shoulder=L0.V_SHOULDER,
        cowl_x=xmap(L0.COWL_X) if L0.COWL_X is not None else None,
        backlight_x=xmap(L0.BACKLIGHT_X) if L0.BACKLIGHT_X is not None else None,
        sill_height=L0.sill_height * kz, n_lower=L0.n_lower, n_upper=L0.n_upper,
        core_z=L0.core_z * kz, crease=crease or L0.crease, section=L0.k)

    caps = {}
    slope = {}
    for key, cap in (("nose", donor.nose), ("tail", donor.tail)):
        caps[key] = WrapCap(
            loft, front=cap.front,
            join=cap.JOIN.mapped(None, lambda v, x: xmap(x)),
            x_of_z=cap.X_OF_Z.mapped(lambda z: z * kz, lambda z, x: xmap(x)),
            z_lo=cap.Z_LO * kz, z_hi=cap.Z_HI * kz, wrap=cap.WRAP,
            slope_cache=slope)
        curves[key.upper() + "_JOIN"] = caps[key].JOIN
        curves[key.upper() + "_X_OF_Z"] = caps[key].X_OF_Z
        curves[key.upper() + "_WRAP"] = caps[key].WRAP
    body = CarBody(loft, caps["nose"], caps["tail"])
    return dict(body=body, loft=loft, nose=caps["nose"], tail=caps["tail"],
                xmap=xmap, ky=ky, kz=kz, curves=curves,
                dims=dict(length=length, width=width, height=height,
                          wheelbase=wheelbase, front_overhang=front_overhang,
                          rear_overhang=length - wheelbase - front_overhang,
                          front_axle=fa, rear_axle=ra, wheel_r=wr))


def _fmt_curve(c, indent="    "):
    if isinstance(c, Joined):
        return "Joined(%.4f, %s, %s)" % (c.xb, _fmt_curve(c.left, indent),
                                         _fmt_curve(c.right, indent))
    pts = ", ".join("(%.4f, %.4f)" % p for p in c.points())
    mode = "" if c.mode == "c2" else ', mode="%s"' % c.mode
    return "Curve([%s]%s)" % (pts, mode)


def source(m):
    """The morphed body as Python assignments, to paste into a car module."""
    d = m["dims"]
    lines = ["# morphed from a donor: length %.3f, width %.3f, height %.3f, "
             "wheelbase %.3f, overhangs %.3f / %.3f"
             % (d["length"], d["width"], d["height"], d["wheelbase"],
                d["front_overhang"], d["rear_overhang"]),
             "FRONT_AXLE = %.4f" % d["front_axle"],
             "REAR_AXLE = %.4f" % d["rear_axle"],
             "WHEEL_R = %.4f" % d["wheel_r"],
             "ARCH_R = %.4f" % m["loft"].ARCH_R]
    for n in Z_CURVES + Y_CURVES:
        lines.append("%s = %s" % (n, _fmt_curve(m["curves"][n])))
    for key in ("NOSE", "TAIL"):
        for part in ("JOIN", "X_OF_Z", "WRAP"):
            lines.append("%s_%s = %s" % (key, part, _fmt_curve(m["curves"][key + "_" + part])))
        cap = m[key.lower()]
        lines.append("%s_Z_LO, %s_Z_HI = %.4f, %.4f" % (key, key, cap.Z_LO, cap.Z_HI))
    return "\n".join(lines)
