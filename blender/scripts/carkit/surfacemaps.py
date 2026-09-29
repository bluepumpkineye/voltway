"""Tileable surface maps for trim materials, generated as real pixels.

Leather, Alcantara, carpet, brushed metal and grille perforation all read as
what they are through their fine SURFACE STRUCTURE under a light: a plain
colour at the right roughness still looks like plastic. The structure has to
be pixels, not procedural nodes, or it vanishes on glTF export (see
textures.py), and it has to TILE, or the repeat shows as a grid of seams.

Every map is built from band-limited noise made in the frequency domain
(numpy FFT), which is periodic by construction, so it tiles perfectly:

    leather_grain   pebbled grain: creases along the zero-crossings of a
                    band of ~1.5 mm noise, pebbles between them
    alcantara       fine fibre nap, very low relief
    carpet          loop pile
    brushed         streaks along U (brushed aluminium)
    perforation     a hex grid of round holes (speaker grilles, perforated
                    leather) - also returns a darkening mask for the holes

Each returns a normal map (and optionally a mask) as a Blender image saved in
blender/textures/, ready for materials.textured(). Sizes are powers of two;
a map's TILE (metres) sets its real-world scale via world-space UVs.
"""
import os

import numpy as np
import bpy

from .textures import TEX_DIR


def band_noise(size, f_lo, f_hi, seed=0, aniso=(1.0, 1.0)):
    """Zero-mean, unit-variance periodic noise with energy between f_lo and
    f_hi cycles per tile. aniso stretches the spectrum: (1, 20) makes streaks
    along U."""
    rng = np.random.default_rng(seed)
    white = rng.standard_normal((size, size))
    fu = np.fft.fftfreq(size)[None, :] * size * aniso[0]
    fv = np.fft.fftfreq(size)[:, None] * size * aniso[1]
    r = np.sqrt(fu * fu + fv * fv)
    mid, half = 0.5 * (f_lo + f_hi), max(1e-3, 0.5 * (f_hi - f_lo))
    band = np.exp(-0.5 * ((r - mid) / half) ** 2)
    n = np.real(np.fft.ifft2(np.fft.fft2(white) * band))
    return (n - n.mean()) / (n.std() + 1e-9)


def height_to_normal(h, strength):
    """Tangent-space (OpenGL, +Y up) normal map from a periodic height field."""
    dx = 0.5 * (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1))
    dy = 0.5 * (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0))
    nx, ny = -dx * strength, -dy * strength
    nz = np.ones_like(h)
    L = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / L, ny / L, nz / L], axis=-1) * 0.5 + 0.5


def _image(name, rgb, non_color=True, filename=None):
    """Store an (h, w, 3) float array as a Blender image and save it as PNG."""
    size = rgb.shape[0]
    old = bpy.data.images.get(name)
    if old:
        bpy.data.images.remove(old)
    img = bpy.data.images.new(name, size, size, alpha=False, is_data=non_color)
    rgba = np.ones((size, size, 4), dtype=np.float32)
    rgba[..., :3] = rgb
    img.pixels.foreach_set(rgba.ravel())
    img.update()
    os.makedirs(TEX_DIR, exist_ok=True)
    img.filepath_raw = os.path.join(TEX_DIR, filename or (name.lower() + ".png"))
    img.file_format = 'PNG'
    img.save()
    if non_color:
        img.colorspace_settings.name = 'Non-Color'
    return img


# Real-world size of one tile of each map, metres. Materials scale their UVs
# (which are world-space metres, build.ensure_uvs) by 1 / TILE.
TILE = {"leather": 0.10, "alcantara": 0.05, "carpet": 0.08, "brushed": 0.10,
        "perforation": 0.04}


def leather_grain(size=1024, seed=7, strength=5.0):
    """Pebbled Nappa grain, ~1.5 mm pebbles on a 100 mm tile."""
    cells = TILE["leather"] / 0.0015
    n = band_noise(size, 0.7 * cells, 1.3 * cells, seed)
    fine = band_noise(size, 2.5 * cells, 4.0 * cells, seed + 1)
    broad = band_noise(size, 3.0, 8.0, seed + 2)
    h = -np.abs(n) * 0.9 + 0.12 * fine + 0.25 * broad       # creases at zero crossings
    return _image("T_Leather_Normal", height_to_normal(h, strength / size * 60.0))


def alcantara(size=512, seed=11, strength=1.6):
    """Microsuede nap: very fine, faintly directional fibre noise."""
    f = TILE["alcantara"] / 0.00035
    n = band_noise(size, 0.4 * f, 1.0 * f, seed, aniso=(1.0, 1.6))
    m = band_noise(size, 6.0, 14.0, seed + 3)                 # brushed-nap patches
    h = n * 0.6 + 0.4 * m
    return _image("T_Alcantara_Normal", height_to_normal(h, strength / size * 60.0))


def carpet(size=512, seed=19, strength=6.0):
    f = TILE["carpet"] / 0.0022
    n = band_noise(size, 0.6 * f, 1.4 * f, seed)
    h = np.tanh(1.5 * n)
    return _image("T_Carpet_Normal", height_to_normal(h, strength / size * 60.0))


def brushed(size=1024, seed=23, strength=2.0):
    """Brushed aluminium: long fine streaks along U."""
    n = band_noise(size, 40.0, 220.0, seed, aniso=(40.0, 1.0))
    return _image("T_Brushed_Normal", height_to_normal(n, strength / size * 60.0))


def perforation(size=512, pitch_px=32, radius=0.30, strength=10.0):
    """Hex grid of round holes. Returns (normal map, darkening mask image)."""
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    row = np.floor(yy / (pitch_px * 0.866))
    cx = (xx + (row % 2) * pitch_px * 0.5) % pitch_px - pitch_px * 0.5
    cy = (yy % (pitch_px * 0.866)) - pitch_px * 0.433
    d = np.sqrt(cx * cx + cy * cy) / pitch_px
    hole = np.clip((radius - d) / 0.05, 0.0, 1.0)
    h = -hole
    nrm = _image("T_Perforation_Normal", height_to_normal(h, strength / size * 60.0))
    mask = np.repeat((1.0 - 0.85 * hole)[..., None], 3, axis=2)
    msk = _image("T_Perforation_Mask", mask, non_color=True,
                 filename="t_perforation_mask.png")
    return nrm, msk


def build_all():
    """Generate every map (a few seconds). Returns {name: image}."""
    out = {"leather": leather_grain(), "alcantara": alcantara(), "carpet": carpet(),
           "brushed": brushed()}
    out["perforation"], out["perforation_mask"] = perforation()
    return out
