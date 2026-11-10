"""Procedural, tileable PBR texture sets for the anatomy (numpy only, no files: the images are made in the .blend and the glTF
exporter encodes them).

Each family returns three float arrays in [0, 1], shape (n, n, 3) with row 0 = v 0 (Blender's own pixel order, v up):

    albedo   sRGB colour (multiplied by the material's tint, so it is kept near white where the tint carries the colour)
    normal   tangent-space normal, OpenGL convention (green up), Non-Color
    orm      R = 1 (no baked AO here), G = roughness, B = metalness (glTF's layout, Non-Color)

Everything is built from spectral noise (white noise filtered in the Fourier domain, which is periodic, so every set tiles) plus
a few drawn patterns (laminations, strands, corrugation, print). The scale of the pattern is set by the material's tile size in
metres (see materials.py): a texture is `tile` metres across, so `cast` (0.5 m) has grain a few millimetres wide.
"""
import numpy as np


# ----------------------------------------------------------------------------- noise
def _freq(n):
    f = np.fft.fftfreq(n) * n
    return f[None, :], f[:, None]            # (fx, fy)


def fbm(n, beta, seed, sx=1.0, sy=1.0, lo=0.0):
    """Periodic noise with a 1/f^beta power spectrum, unit standard deviation. sx/sy stretch it: a large sx makes features
    long along u (brushing). `lo` removes the lowest frequencies (a band-pass for fine grain)."""
    rng = np.random.default_rng(seed)
    F = np.fft.fft2(rng.standard_normal((n, n)))
    fx, fy = _freq(n)
    r = np.sqrt((fx * sx) ** 2 + (fy * sy) ** 2)
    r[0, 0] = 1.0
    amp = r ** (-beta / 2.0)
    if lo:
        amp = amp * (r > lo)
    amp[0, 0] = 0.0
    out = np.fft.ifft2(F * amp).real
    out -= out.mean()
    out /= out.std() + 1e-9
    return out


def worley(n, cells, seed):
    """Periodic cellular noise: distance to the nearest of `cells` x `cells` jittered points (0 at a point, about 1 at the
    farthest). Pebbles, pores."""
    rng = np.random.default_rng(seed)
    pts = rng.random((cells, cells, 2))
    c = (np.arange(n) + 0.5) / n * cells
    X, Y = np.meshgrid(c, c)
    ix, iy = np.floor(X).astype(int), np.floor(Y).astype(int)
    best = np.full((n, n), 9.0)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            cx, cy = (ix + dx) % cells, (iy + dy) % cells
            px = ix + dx + pts[cy, cx, 0]
            py = iy + dy + pts[cy, cx, 1]
            best = np.minimum(best, np.hypot(X - px, Y - py))
    return best


def blur(a, k=1):
    for _ in range(k):
        a = (4 * a + np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1)) / 8.0
    return a


def normal_from_height(h, s):
    """Tangent-space normal map (0..1 encoded) of height `h` (any scale), strength `s` (about 1 = clearly visible)."""
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    nx, ny, nz = -gx * s, -gy * s, np.ones_like(h)
    L = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / L * 0.5 + 0.5, ny / L * 0.5 + 0.5, nz / L * 0.5 + 0.5], -1)


def _grey(a):
    return np.stack([a, a, a], -1)


def _orm(rough, metal):
    return np.stack([np.ones_like(rough), np.clip(rough, 0.04, 1.0), np.clip(metal, 0.0, 1.0) * np.ones_like(rough)], -1)


def _grid(n):
    c = (np.arange(n) + 0.5) / n
    return np.meshgrid(c, c)                  # U, V in [0, 1)


# ----------------------------------------------------------------------------- families
def cast(n=1024):
    """Sand-cast aluminium: a fine, even grain with a faint orange-peel swell and a very few pores. The colour barely moves (the
    tint carries it); the character is in the grain catching light."""
    mid, fine, grit = fbm(n, 2.2, 12, lo=10), fbm(n, 0.5, 13, lo=70), fbm(n, 0.2, 16, lo=150)
    pores = worley(n, 40, 14)
    pit = np.clip(1.0 - pores / 0.11, 0, 1) * (fbm(n, 0.4, 15) > 2.0)
    pit = blur(pit, 1)
    h = 0.10 * mid + 0.42 * fine + 0.30 * grit - 1.1 * pit
    albedo = _grey(np.clip(0.93 + 0.025 * mid + 0.02 * fine - 0.22 * pit, 0, 1))
    rough = 0.52 + 0.04 * mid + 0.05 * fine + 0.16 * pit
    return albedo, normal_from_height(h, 0.34), _orm(rough, 0.86 - 0.2 * pit)


def machined(n=1024):
    """Brushed, machined aluminium: long soft streaks along u, a faint tool-chatter band. Kept subtle: it should catch the light
    in a highlight, not read as scratches."""
    U, V = _grid(n)
    st = fbm(n, 1.4, 21, sx=30.0, sy=1.0)
    st2 = fbm(n, 1.9, 22, sx=70.0, sy=1.2, lo=2)
    chat = np.sin(2 * np.pi * V * 9 + 2.0 * fbm(n, 3.0, 23))
    h = 0.55 * st + 0.35 * st2 + 0.12 * chat
    albedo = _grey(np.clip(0.95 + 0.02 * st + 0.012 * chat, 0, 1))
    rough = 0.30 + 0.035 * st + 0.015 * chat
    return albedo, normal_from_height(h, 0.16), _orm(rough, 0.95)


def forged(n=1024):
    """Forged aluminium: smooth with a faint flow direction and a fine skin."""
    big, flow, fine = fbm(n, 3.2, 31), fbm(n, 1.6, 32, sx=5.0, sy=1.0), fbm(n, 0.8, 33, lo=60)
    h = 0.25 * big + 0.35 * flow + 0.16 * fine
    albedo = _grey(np.clip(0.9 + 0.05 * big + 0.03 * flow, 0, 1))
    rough = 0.36 + 0.05 * flow + 0.03 * big
    return albedo, normal_from_height(h, 0.22), _orm(rough, 0.92)


def steel(n=512):
    """Dark machined steel: fine grain, faint lathe lines."""
    g, st = fbm(n, 1.4, 41, lo=8), fbm(n, 1.2, 42, sx=14.0, sy=1.0)
    h = 0.5 * g + 0.4 * st
    albedo = _grey(np.clip(0.9 + 0.05 * g, 0, 1))
    rough = 0.42 + 0.06 * st + 0.04 * g
    return albedo, normal_from_height(h, 0.25), _orm(rough, 0.94)


def lam(n=512, stripes=32):
    """An electrical-steel stack: sheets edge-on. Stripes run along u (round the circumference, one per sheet along the axis);
    every few sheets one is a little proud, as in a real stack, and the sheets differ a hair in tone."""
    U, V = _grid(n)
    k = (V * stripes) % 1.0
    sheet = np.floor(V * stripes).astype(int)
    rng = np.random.default_rng(51)
    tone = rng.random(stripes)[sheet % stripes]
    proud = (rng.random(stripes) > 0.82)[sheet % stripes] * 0.35
    edge = np.minimum(k, 1 - k)                                  # 0 at a sheet boundary
    h = np.clip(edge * 6.0, 0, 1) * 0.8 - 0.4 + proud * 0.5 + 0.15 * fbm(n, 1.2, 52, sx=8.0)
    albedo = _grey(np.clip(0.80 + 0.14 * tone - 0.28 * (1 - np.clip(edge * 9.0, 0, 1)), 0, 1))
    rough = 0.34 + 0.10 * (1 - np.clip(edge * 9.0, 0, 1)) + 0.04 * tone
    return albedo, normal_from_height(h, 1.1), _orm(rough, 0.80)


def copper(n=512, strands=14):
    """Copper winding: strands along u with a bright crown and a dark seam between them, a little oxide drift."""
    U, V = _grid(n)
    k = (V * strands) % 1.0
    band = np.sin(np.pi * k)                                     # 1 at the strand's crown, 0 at the seam
    h = band ** 0.6 * 0.9 + 0.12 * fbm(n, 1.3, 61, sx=10.0)
    drift = fbm(n, 2.4, 62)
    albedo = _grey(np.clip(0.93 + 0.03 * drift - 0.22 * (1 - band), 0, 1))
    rough = 0.26 + 0.20 * (1 - band) + 0.03 * drift
    return albedo, normal_from_height(h, 1.0), _orm(rough, 1.0)


def cellfilm(n=1024):
    """The blue wrap of a cell: faint wrinkles, and a printed band of dashes, arrows and a polarity block."""
    U, V = _grid(n)
    w = fbm(n, 2.8, 71) * 0.5 + fbm(n, 1.4, 72, lo=20) * 0.25
    base = np.array([0.184, 0.392, 0.702])                       # #2f64b3, the film (sRGB): this set is used untinted
    albedo = np.clip(base[None, None, :] * (0.97 + 0.06 * w[..., None]), 0, 1)
    # printed dashes: rows of short white bars, a thin rule above and below
    ink = np.zeros((n, n))
    rng = np.random.default_rng(73)
    for row in range(5):
        y0 = int(n * (0.60 + row * 0.055))
        x = int(rng.integers(0, 40))
        while x < n - 30:
            wlen = int(rng.integers(14, 64))
            ink[y0:y0 + 9, x:x + wlen] = 1.0
            x += wlen + int(rng.integers(8, 24))
    ink[int(n * 0.57):int(n * 0.57) + 4, :] = 1.0
    ink[int(n * 0.91):int(n * 0.91) + 4, :] = 1.0
    # a '+' block and an arrow near the top
    ink[int(n * 0.16):int(n * 0.16) + 54, 60:200] = 1.0
    ink[int(n * 0.16) + 21:int(n * 0.16) + 33, 100:160] = 0.0
    ink[int(n * 0.16) + 11:int(n * 0.16) + 43, 124:136] = 0.0
    for i in range(46):
        ink[int(n * 0.25) + 8 + i // 2:int(n * 0.25) + 26 - i // 2, 300 + i * 3:303 + i * 3] = 1.0
    ink = blur(ink, 1)
    albedo = albedo * (1 - ink[..., None]) + np.array([0.93, 0.95, 0.98])[None, None, :] * ink[..., None]
    rough = 0.38 + 0.05 * w + 0.12 * ink
    return albedo, normal_from_height(0.6 * w + 0.15 * ink, 0.45), _orm(rough, 0.08 * np.ones_like(rough))


def rubber(n=512):
    """Rubber: a fine pebble, matte."""
    p = worley(n, 90, 81)
    g = fbm(n, 0.7, 82, lo=30)
    h = np.clip(p, 0, 1) * 0.6 + 0.3 * g
    albedo = _grey(np.clip(0.96 + 0.03 * g, 0, 1))
    return albedo, normal_from_height(h, 0.5), _orm(0.80 + 0.07 * g, 0.0 * g)


def plastic(n=512):
    """Textured black plastic (a leather-like grain), a satin sheen."""
    p = worley(n, 64, 91)
    g = fbm(n, 1.0, 92, lo=20)
    h = np.clip(p * 1.4, 0, 1) * 0.7 + 0.2 * g
    albedo = _grey(np.clip(0.95 + 0.03 * g, 0, 1))
    return albedo, normal_from_height(h, 0.65), _orm(0.50 + 0.09 * g + 0.1 * (p > 0.7), 0.0 * g)


def hvsheath(n=512, rings=10):
    """A corrugated orange cable sheath: rings across u... the tube's UV has u along the cable, v round it."""
    U, V = _grid(n)
    ring = 0.5 - 0.5 * np.cos(2 * np.pi * U * rings)             # crest 1, root 0
    g = fbm(n, 1.0, 101, lo=20)
    h = ring ** 0.7 + 0.04 * g
    albedo = _grey(np.clip(0.74 + 0.26 * ring, 0, 1))
    return albedo, normal_from_height(h, 1.3), _orm(0.46 - 0.08 * ring + 0.03 * g, 0.0 * g)


def insulator(n=512):
    """Amber polyimide film: soft wrinkles, a glassy sheen."""
    w, f = fbm(n, 3.6, 111), fbm(n, 1.6, 112, lo=18)
    h = 0.5 * w + 0.12 * f
    albedo = np.stack([np.clip(0.97 + 0.02 * w, 0, 1), np.clip(0.86 + 0.04 * w, 0, 1), np.clip(0.55 + 0.05 * w, 0, 1)], -1)
    return albedo, normal_from_height(h, 0.5), _orm(0.46 + 0.07 * w, 0.0 * w)


def pcb(n=512, green=True):
    """A circuit board: solder mask, copper traces routed in 45/90 degree runs, pads and vias, a little silkscreen."""
    rng = np.random.default_rng(121 if green else 122)
    trace = np.zeros((n, n))
    pad = np.zeros((n, n))
    for _ in range(46):
        x, y = int(rng.integers(8, n - 8)), int(rng.integers(8, n - 8))
        for _seg in range(int(rng.integers(3, 7))):
            L = int(rng.integers(30, 150))
            wd = 3
            if rng.random() < 0.5:
                sgn = 1 if rng.random() < 0.5 else -1
                x2 = max(2, min(n - 3, x + sgn * L))
                trace[y:y + wd, min(x, x2):max(x, x2) + wd] = 1.0
                x = x2
            else:
                sgn = 1 if rng.random() < 0.5 else -1
                y2 = max(2, min(n - 3, y + sgn * L))
                trace[min(y, y2):max(y, y2) + wd, x:x + wd] = 1.0
                y = y2
        pad[max(0, y - 4):y + 5, max(0, x - 4):x + 5] = 1.0
    for _ in range(40):                                          # SMD pads in pairs
        x, y = int(rng.integers(10, n - 28)), int(rng.integers(10, n - 20))
        pad[y:y + 8, x:x + 7] = 1.0
        pad[y:y + 8, x + 13:x + 20] = 1.0
    silk = np.zeros((n, n))
    for _ in range(14):
        x, y = int(rng.integers(10, n - 60)), int(rng.integers(10, n - 10))
        silk[y:y + 2, x:x + int(rng.integers(20, 56))] = 1.0
    copper_m = np.clip(trace + pad, 0, 1)
    mask = np.array([0.04, 0.34, 0.18]) if green else np.array([0.55, 0.30, 0.04])
    cu = np.array([0.80, 0.55, 0.30])
    alb = mask[None, None, :] * (1 - copper_m[..., None]) + cu[None, None, :] * copper_m[..., None]
    alb = alb * (1 - silk[..., None]) + np.array([0.9, 0.9, 0.86])[None, None, :] * silk[..., None]
    g = fbm(n, 1.0, 123, lo=30)
    rough = 0.42 - 0.12 * copper_m + 0.03 * g + 0.1 * silk
    metal = 0.9 * copper_m
    return alb, normal_from_height(blur(copper_m, 1) * 0.5 + 0.15 * g, 0.7), _orm(rough, metal)


def fpc(n=512):
    """A flexible printed circuit: amber polyimide with copper traces (the cell-voltage sensing strips)."""
    return pcb(n, green=False)


def hazard(n=256):
    """Yellow and black warning stripes."""
    U, V = _grid(n)
    s = (((U + V) * 8.0) % 1.0) < 0.5
    alb = np.where(s[..., None], np.array([0.96, 0.78, 0.05])[None, None, :], np.array([0.05, 0.05, 0.05])[None, None, :])
    return alb, normal_from_height(np.zeros((n, n)), 1.0), _orm(0.55 * np.ones((n, n)), np.zeros((n, n)))


# ----------------------------------------------------------------------------- label atlas
def _tri(n, cx, cy, r):
    """A boolean mask of an upward triangle."""
    Y, X = np.mgrid[0:n, 0:n]
    h = r * 1.5
    inside = (Y >= cy - h * 0.5) & (Y <= cy + h * 0.5)
    t = (Y - (cy - h * 0.5)) / h
    return inside & (np.abs(X - cx) <= t * r)


def labels(n=1024):
    """A 4 x 4 atlas of stickers (each 256 px): (0,0) HV warning, (1,0) QR plate, (2,0) barcode strip, (3,0) data plate, (0,1) coolant
    flow arrows, (1,1) earth symbol, (2,1) hazard stripes, (3,1) a hot-surface warning. Cell (cu, cv) occupies u in [cu/4, (cu+1)/4].
    Nothing here is a maker's mark or a figure."""
    c = n // 4
    alb = np.ones((n, n, 3)) * 0.92
    rough = np.ones((n, n)) * 0.5
    ink = np.zeros((n, n))
    rng = np.random.default_rng(131)

    def cell(i, j):
        return slice(j * c, (j + 1) * c), slice(i * c, (i + 1) * c)

    def paint(i, j, col):
        sy, sx = cell(i, j)
        alb[sy, sx] = col

    # (0,0) the high-voltage warning: yellow triangle with a black border and a bolt
    paint(0, 0, [0.96, 0.80, 0.08])
    sy, sx = cell(0, 0)
    sub = np.zeros((c, c))
    tri = _tri(c, c // 2, int(c * 0.52), int(c * 0.40))
    tri_in = _tri(c, c // 2, int(c * 0.56), int(c * 0.30))
    sub[tri & ~tri_in] = 1
    bolt = [(0.56, 0.34), (0.40, 0.58), (0.50, 0.58), (0.44, 0.78), (0.62, 0.52), (0.52, 0.52), (0.58, 0.34)]
    Y, X = np.mgrid[0:c, 0:c]
    P = np.stack([X / c, Y / c], -1)
    # a polygon fill by even-odd rule
    ins = np.zeros((c, c), bool)
    for k in range(len(bolt)):
        (x1, y1), (x2, y2) = bolt[k], bolt[(k + 1) % len(bolt)]
        cond = ((y1 > P[..., 1]) != (y2 > P[..., 1])) & (P[..., 0] < (x2 - x1) * (P[..., 1] - y1) / (y2 - y1 + 1e-9) + x1)
        ins ^= cond
    sub[ins] = 1
    ink[sy, sx] = sub
    # (1,0) a QR-style plate
    paint(1, 0, [0.96, 0.96, 0.96])
    sy, sx = cell(1, 0)
    q = np.zeros((c, c))
    m = 29
    k = int(c * 0.72) // m
    mat_ = (rng.random((m, m)) > 0.5).astype(float)
    for (r0, c0) in ((0, 0), (0, m - 7), (m - 7, 0)):
        mat_[r0:r0 + 7, c0:c0 + 7] = 1
        mat_[r0 + 1:r0 + 6, c0 + 1:c0 + 6] = 0
        mat_[r0 + 2:r0 + 5, c0 + 2:c0 + 5] = 1
    off = (c - m * k) // 2
    q[off:off + m * k, off:off + m * k] = np.kron(mat_, np.ones((k, k)))
    ink[sy, sx] = q
    # (2,0) a barcode strip with text bars
    paint(2, 0, [0.95, 0.95, 0.93])
    sy, sx = cell(2, 0)
    b = np.zeros((c, c))
    x = int(c * 0.08)
    while x < int(c * 0.92):
        wd = int(rng.integers(2, 9))
        b[int(c * 0.28):int(c * 0.66), x:x + wd] = 1
        x += wd + int(rng.integers(2, 8))
    for row in range(3):
        y0 = int(c * 0.74) + row * 12
        b[y0:y0 + 5, int(c * 0.08):int(c * 0.08) + int(rng.integers(90, 200))] = 1
    ink[sy, sx] = b
    # (3,0) a data plate: silver, rows of text-like bars and two small boxes
    paint(3, 0, [0.78, 0.8, 0.83])
    sy, sx = cell(3, 0)
    d = np.zeros((c, c))
    for row in range(9):
        y0 = int(c * 0.10) + row * 22
        d[y0:y0 + 7, int(c * 0.08):int(c * 0.08) + int(rng.integers(60, 190))] = 1
    d[int(c * 0.82):int(c * 0.92), int(c * 0.08):int(c * 0.30)] = 1
    d[int(c * 0.82):int(c * 0.92), int(c * 0.40):int(c * 0.62)] = 1
    ink[sy, sx] = d * 0.9
    rough[sy, sx] = 0.32
    # (0,1) coolant flow arrows on blue
    paint(0, 1, [0.12, 0.45, 0.85])
    sy, sx = cell(0, 1)
    a = np.zeros((c, c))
    for y0 in (int(c * 0.28), int(c * 0.62)):
        a[y0:y0 + 14, int(c * 0.1):int(c * 0.64)] = 1
        for i in range(30):
            a[y0 - 12 + i // 2 + 0:y0 + 26 - i // 2, int(c * 0.64) + i:int(c * 0.64) + i + 1] = 1
    ink[sy, sx] = a
    # (1,1) the earth symbol on green/yellow
    paint(1, 1, [0.12, 0.62, 0.22])
    sy, sx = cell(1, 1)
    e = np.zeros((c, c))
    e[int(c * 0.2):int(c * 0.5), int(c * 0.47):int(c * 0.53)] = 1
    for i, wlen in enumerate((0.5, 0.34, 0.18)):
        y0 = int(c * (0.5 + 0.12 * i))
        e[y0:y0 + 12, int(c * (0.5 - wlen / 2)):int(c * (0.5 + wlen / 2))] = 1
    ink[sy, sx] = e
    # (2,1) hazard stripes
    sy, sx = cell(2, 1)
    h = hazard(c)[0]
    alb[sy, sx] = h
    # (3,1) hot surface: yellow triangle with a wavy mark
    paint(3, 1, [0.96, 0.80, 0.08])
    sy, sx = cell(3, 1)
    sub = np.zeros((c, c))
    sub[tri & ~tri_in] = 1
    xs = np.arange(c)
    for off_ in (-26, 0, 26):
        yy = (c * 0.6 + 16 * np.sin(xs / c * 6.0 * np.pi * 0.9 + 0.5)).astype(int) + 0
        for x in range(int(c * 0.3), int(c * 0.7)):
            y = int(c * 0.50 + 16 * np.sin((x - c * 0.3) / (c * 0.4) * 2.5 * np.pi)) + off_ // 3
            sub[y:y + 6, x] = 1
    ink[sy, sx] = sub
    ink = blur(ink, 1)
    col = np.where(ink[..., None] > 0, 0.04, 1.0)
    # inks: black on all but the blue and the green plates, where they are white
    for (i, j) in ((0, 1), (1, 1)):
        sy, sx = cell(i, j)
        alb[sy, sx] = alb[sy, sx] * (1 - ink[sy, sx][..., None]) + np.array([0.96, 0.97, 0.97]) * ink[sy, sx][..., None]
    for (i, j) in ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1)):
        sy, sx = cell(i, j)
        alb[sy, sx] = alb[sy, sx] * (1 - ink[sy, sx][..., None]) + np.array([0.03, 0.03, 0.03]) * ink[sy, sx][..., None]
    return np.clip(alb, 0, 1), normal_from_height(blur(ink, 1) * 0.1, 0.4), _orm(rough, np.zeros((n, n)))


FAMILIES = dict(cast=cast, machined=machined, forged=forged, steel=steel, lam=lam, copper=copper, cellfilm=cellfilm,
                rubber=rubber, plastic=plastic, hvsheath=hvsheath, insulator=insulator, pcb=pcb, fpc=fpc, hazard=hazard, labels=labels)
