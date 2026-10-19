"""The light the cabins are shown in: a bright, even showroom hall, drawn from numbers.

HIMA's hall (docs/hima-benchmark.md, "The cabin") lights every interior material from one soft panorama of a lit
parking hall: ceiling about 1.0, walls about 0.9, floor about 0.27 (linear), long ceiling strips at 8-50, a few dark
columns. Nothing in it is directional daylight, so a cabin reads cream and soft and every highlight is a long strip.
This module draws that kind of room itself: no photograph, no third-party light.

    carkit.hall_env.write(path)        # 1024 x 512 Radiance HDR, y up, strips along +X (the car's length)

Equirect convention of three.js (what the viewer's EquirectangularReflectionMapping reads): u = atan2(z, x)/2pi + 1/2,
v = asin(y)/pi + 1/2 (v = 1 at the top of the picture).
"""
import numpy as np

# the numbers (linear light), tuned against the web viewer's cabin
FLOOR = 0.26
WALL = 0.28
CEILING = 0.95
STRIP = 24.0          # the long ceiling softboxes
WINDOW = 2.2          # the two side windows


def _smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def build(width=1024, height=512, seed=7):
    """The panorama as float RGB, rows top-down."""
    u = (np.arange(width) + 0.5) / width
    v = (np.arange(height) + 0.5) / height
    phi = (u - 0.5) * 2.0 * np.pi                     # azimuth: atan2(z, x)
    el = (0.5 - v) * np.pi                            # elevation, +pi/2 at the top row
    PHI, EL = np.meshgrid(phi, el)
    d = np.stack([np.cos(EL) * np.cos(PHI), np.sin(EL), np.cos(EL) * np.sin(PHI)], axis=-1)
    x, y, z = d[..., 0], d[..., 1], d[..., 2]

    # the room: a ceiling that is a little brighter than the walls, a darker floor
    up = _smooth(0.10, 0.42, y)
    lum = FLOOR + (WALL - FLOOR) * _smooth(-0.35, 0.02, y)
    lum = lum + (CEILING - WALL) * up
    lum = lum * (0.90 + 0.10 * np.cos(2.0 * PHI))     # a slightly brighter end than side
    rgb = np.stack([lum * 1.00, lum * 0.995, lum * 0.975], axis=-1)   # a hair warm, not green

    # the ceiling plane (y = H above the eye): strips run along X, evenly spaced across the room
    H = 2.2
    safe = np.maximum(y, 1e-3)
    px, pz = d[..., 0] * H / safe, d[..., 2] * H / safe
    on_ceiling = y > 0.28
    strips = np.zeros_like(lum)
    for cz, wz in ((-1.5, 0.13), (1.5, 0.13)):
        edge = 1.0 - _smooth(wz * 0.5, wz, np.abs(pz - cz))
        ends = 1.0 - _smooth(5.0, 6.0, np.abs(px))
        strips = np.maximum(strips, edge * ends)
    # a few brighter pods between them: a ceiling's worth of structure for the glass to pick up
    pods = np.zeros_like(lum)
    for cx in (-4.0, 0.0, 4.0):
        for cz in (-3.2, 3.2):
            r = np.hypot(px - cx, pz - cz)
            pods = np.maximum(pods, 1.0 - _smooth(0.14, 0.28, r))
    glow = np.where(on_ceiling, strips * STRIP + pods * STRIP * 0.8, 0.0)

    # side windows (a bright wall on each side, below the ceiling, high enough to sit in a door glass)
    win = np.zeros_like(lum)
    for az in (np.pi / 2, -np.pi / 2):
        da = np.abs(((PHI - az + np.pi) % (2 * np.pi)) - np.pi)
        win = np.maximum(win, (1.0 - _smooth(0.28, 0.42, da)) * _smooth(0.02, 0.10, y) * (1.0 - _smooth(0.40, 0.52, y)))
    glow = glow + win * WINDOW

    # dark columns round the room: a wall is not one flat grey
    cols = np.zeros_like(lum)
    for k in range(12):
        az = k * np.pi / 6 + 0.26
        da = np.abs(((PHI - az + np.pi) % (2 * np.pi)) - np.pi)
        cols = np.maximum(cols, (1.0 - _smooth(0.035, 0.06, da)) * _smooth(-0.30, -0.1, y) * (1.0 - _smooth(0.2, 0.34, y)))
    rgb = rgb * (1.0 - 0.55 * cols)[..., None] + glow[..., None] * np.array([1.0, 0.99, 0.96])
    return rgb.astype(np.float32)


def write(path, width=1024, height=512):
    from . import bake as BK
    rgb = build(width, height)
    BK.write_hdr(path, rgb)
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    cosw = np.cos((0.5 - (np.arange(height) + 0.5) / height) * np.pi)[:, None]
    print("hall_env: %s  mean %.3f  p50 %.3f  p99 %.2f  max %.1f" % (
        path, float((lum * cosw).sum() / (cosw.sum() * width)), float(np.percentile(lum, 50)),
        float(np.percentile(lum, 99)), float(lum.max())))
    return path
