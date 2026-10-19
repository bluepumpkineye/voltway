"""Nio ES8 nose & tail wrap caps and composite CarBody.

Nio ES8 features the signature Shark-Nose X-Bar front fascia peaking at z ~ 0.925 m
and an upright architectural SUV tailgate with the Super-Red illumiBlade full-width
tail lightbar at z ~ 1.065-1.115 m.
"""
import es8_surface as S
from carkit.geom import Curve
from carkit.body import WrapCap, CarBody


def _by_v(pts_zx, top=None):
    out = []
    for (z, x) in pts_zx:
        v = S.BODY.v_at_z(x, z, 0.0, 1.0)
        if out and v <= out[-1][0] + 1e-4:
            continue
        out.append((v, x))
    if top is not None:
        while out and out[-1][0] > 0.96:
            out.pop()
        out.append((1.0, top))
    return Curve(out, mode="pchip")


# Front bumper-to-fender / hood join line (around front wheel arch x = 1.565 + 0.485 = 2.05)
JOIN_F = _by_v([
    (0.22, 2.300), (0.30, 2.160), (0.40, 2.075), (0.52, 2.050),
    (0.65, 2.065), (0.78, 2.150), (0.85, 2.290), (0.91, 2.450),
], top=2.520)

# Rear bumper/tailgate-to-quarter join line
JOIN_R = _by_v([
    (0.23, -2.200), (0.32, -2.090), (0.40, -2.055), (0.52, -2.020),
    (0.64, -1.970), (0.76, -1.910), (0.86, -1.950), (0.96, -2.120),
    (1.04, -2.320), (1.10, -2.480),
], top=-2.530)

NOSE_Z_LO, NOSE_Z_HI = 0.268, 0.920
NOSE_X_OF_Z = Curve([
    (0.268, 2.615),
    (0.310, 2.628),
    (0.460, 2.638),
    (0.680, 2.638),
    (0.760, 2.624),   # flat recessed horizontal fascia band under Shark-Nose
    (0.835, 2.630),
    (0.865, 2.640),   # Shark-Nose X-Bar horizontal ridge (+2.640 m)
    (0.900, 2.585),   # sloped upper nose plane (NIO emblem surface)
    (0.920, 2.520),   # clamshell hood leading edge
])

TAIL_Z_LO, TAIL_Z_HI = 0.285, 1.115
TAIL_X_OF_Z = Curve([
    (0.285, -2.530),
    (0.360, -2.605),
    (0.460, -2.640),  # rear bumper apex (-2.640 m)
    (0.560, -2.625),
    (0.680, -2.595),  # tailgate lower edge
    (0.800, -2.590),  # smooth flush plate zone
    (0.940, -2.585),
    (1.060, -2.605),  # Super-Red illumiBlade face
    (1.115, -2.590),  # base of rear glass
], mode="pchip")

WRAP = Curve([
    (0.00, 0.0000), (0.15, 0.0030), (0.30, 0.0100), (0.45, 0.0220),
    (0.58, 0.0400), (0.68, 0.0680), (0.76, 0.1150), (0.83, 0.1850),
    (0.89, 0.2950), (0.94, 0.4600), (0.97, 0.6500), (0.99, 0.8450),
    (1.00, 1.0000),
])

TAIL_WRAP = Curve([
    (0.00, 0.000), (0.20, 0.004), (0.40, 0.016), (0.55, 0.034),
    (0.68, 0.062), (0.78, 0.105), (0.86, 0.170), (0.92, 0.270),
    (0.96, 0.420), (0.985, 0.640), (0.996, 0.840), (1.00, 1.000),
])

NOSE = WrapCap(S.BODY, front=True, join=JOIN_F, x_of_z=NOSE_X_OF_Z,
               z_lo=NOSE_Z_LO, z_hi=NOSE_Z_HI, wrap=WRAP)
TAIL = WrapCap(S.BODY, front=False, join=JOIN_R, x_of_z=TAIL_X_OF_Z,
               z_lo=TAIL_Z_LO, z_hi=TAIL_Z_HI, wrap=TAIL_WRAP)
BODY = CarBody(S.BODY, NOSE, TAIL, flank_x_range=(-2.55, 2.53))


def top_point(x, y, d=0.0):
    v = S.v_at_y_upper(x, abs(y))
    p = S.surface_offset(x, v, d)
    n = S.surface_normal(x, v)
    if y < 0.0:
        p = (p[0], -p[1], p[2])
        n = (n[0], -n[1], n[2])
    return p, n


BODY.top_point = top_point


def dims_report():
    return BODY.dims_report()
