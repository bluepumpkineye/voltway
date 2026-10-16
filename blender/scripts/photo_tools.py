"""Measuring a studio photograph: car mask, outline, crops with a labelled grid.

Run inside Blender (bpy loads the image; numpy does the work), headless is fine:

    import photo_tools as PT
    img = PT.load(path)                       # float [h, w, 3], row 0 at the TOP
    mask = PT.car_mask(img)                   # bool [h, w], True on the car
    top = PT.top_outline(mask)                # v of the first car pixel per column (nan: none)
    PT.save(PT.annotate(img, [(u, v, "label")]), out)

The studio backdrops (a wall and a floor) are flat colours with a vertical gradient, so the
background of each ROW is the median of the photo's left and right margins; the car is
whatever differs from it by more than `tol` (RGB distance, 0-1). The floor's shadow under the
car also differs: use the mask's top and ends, not its bottom.
"""
import os

import bpy
import numpy as np


def load(path):
    path = os.path.normpath(path)
    im = bpy.data.images.load(path, check_existing=False)
    w, h = im.size
    a = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(a)
    bpy.data.images.remove(im)
    a = a.reshape(h, w, 4)[::-1, :, :3].copy()          # Blender stores bottom-up
    return a


def save(arr, path):
    h, w = arr.shape[:2]
    im = bpy.data.images.new("tmp_save", w, h, alpha=True)
    rgba = np.ones((h, w, 4), np.float32)
    rgba[..., :3] = np.clip(arr[..., :3], 0.0, 1.0)
    im.pixels.foreach_set(rgba[::-1].reshape(-1))
    im.filepath_raw = os.path.normpath(path)
    im.file_format = "PNG" if path.lower().endswith(".png") else "JPEG"
    im.save()
    bpy.data.images.remove(im)


def car_mask(img, margin=300, tol=0.10, close=3):
    """True where the pixel differs from its row's background (margins of the photo)."""
    h, w = img.shape[:2]
    left = img[:, :margin]
    right = img[:, w - margin:]
    bg = np.median(np.concatenate([left, right], axis=1), axis=1)         # [h, 3]
    d = np.sqrt(((img - bg[:, None, :]) ** 2).sum(-1))
    m = d > tol
    if close:
        m = _close(m, close)
    return m


def _shift(m, dy, dx):
    out = np.zeros_like(m)
    h, w = m.shape
    ys = slice(max(dy, 0), h + min(dy, 0))
    yd = slice(max(-dy, 0), h + min(-dy, 0))
    xs = slice(max(dx, 0), w + min(dx, 0))
    xd = slice(max(-dx, 0), w + min(-dx, 0))
    out[ys, xs] = m[yd, xd]
    return out


def _close(m, r):
    """Dilate then erode by r px (fills 1-2 px gaps along edges)."""
    d = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dy or dx:
                d |= _shift(m, dy, dx)
    e = d.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dy or dx:
                e &= _shift(d, dy, dx)
    return e


def top_outline(mask, min_run=12):
    """For each column the v of the first car pixel that starts a run of >= min_run (nan: none)."""
    h, w = mask.shape
    out = np.full(w, np.nan)
    for u in range(w):
        col = mask[:, u]
        idx = np.flatnonzero(col)
        if idx.size == 0:
            continue
        # first run of min_run consecutive True
        run = np.convolve(col.astype(np.int32), np.ones(min_run, np.int32), "valid")
        hit = np.flatnonzero(run == min_run)
        if hit.size:
            out[u] = hit[0]
    return out


def bottom_outline(mask, min_run=12):
    h, w = mask.shape
    out = np.full(w, np.nan)
    for u in range(w):
        col = mask[:, u]
        run = np.convolve(col.astype(np.int32), np.ones(min_run, np.int32), "valid")
        hit = np.flatnonzero(run == min_run)
        if hit.size:
            out[u] = hit[-1] + min_run - 1
    return out


def left_right_extent(mask, v):
    """First and last car pixel on row v."""
    idx = np.flatnonzero(mask[int(v)])
    return (int(idx[0]), int(idx[-1])) if idx.size else (None, None)


def crop(img, u0, v0, w, h, scale=1.0):
    a = img[int(v0):int(v0 + h), int(u0):int(u0 + w)]
    if scale != 1.0:
        a = _resize(a, scale)
    return a


def _resize(a, s):
    h, w = a.shape[:2]
    nh, nw = max(1, int(h * s)), max(1, int(w * s))
    ys = np.minimum((np.arange(nh) / s).astype(int), h - 1)
    xs = np.minimum((np.arange(nw) / s).astype(int), w - 1)
    return a[ys][:, xs]


def grid_crop(img, u0, v0, w, h, step=50, scale=1.0, label_every=2):
    """A crop with a labelled pixel grid (photo coordinates), for reading points by eye."""
    a = crop(img, u0, v0, w, h, 1.0).copy()
    ch, cw = a.shape[:2]
    for u in range((int(u0) // step + 1) * step, int(u0) + cw, step):
        a[:, u - int(u0)] = a[:, u - int(u0)] * 0.4 + np.array([1.0, 1.0, 0.0]) * 0.6
    for v in range((int(v0) // step + 1) * step, int(v0) + ch, step):
        a[v - int(v0), :] = a[v - int(v0), :] * 0.4 + np.array([0.0, 1.0, 1.0]) * 0.6
    if scale != 1.0:
        a = _resize(a, scale)
    return a


def draw_polyline(img, pts, colour=(1.0, 0.0, 1.0), width=2):
    """Draw a polyline of (u, v) onto img (in place)."""
    h, w = img.shape[:2]
    for (u0, v0), (u1, v1) in zip(pts[:-1], pts[1:]):
        n = int(max(abs(u1 - u0), abs(v1 - v0))) + 1
        for t in np.linspace(0.0, 1.0, n):
            u = int(round(u0 + (u1 - u0) * t))
            v = int(round(v0 + (v1 - v0) * t))
            for dv in range(-(width // 2), width // 2 + 1):
                for du in range(-(width // 2), width // 2 + 1):
                    if 0 <= v + dv < h and 0 <= u + du < w:
                        img[v + dv, u + du] = colour
    return img


# ----------------------------------------------------------------- wheels
def _lum(img):
    return (img * np.array([0.299, 0.587, 0.114], np.float32)).sum(-1)


def _bilinear(lum, u, v):
    u0 = int(np.floor(u)); v0 = int(np.floor(v)); fu = u - u0; fv = v - v0
    return (lum[v0, u0] * (1 - fu) * (1 - fv) + lum[v0, u0 + 1] * fu * (1 - fv)
            + lum[v0 + 1, u0] * (1 - fu) * fv + lum[v0 + 1, u0 + 1] * fu * fv)


def fit_conic(pts):
    """Least-squares ellipse through pts [n, 2]: (centre, semi-axes, eigvecs)."""
    x = pts[:, 0]; y = pts[:, 1]
    A = np.column_stack([x * x, x * y, y * y, x, y, np.ones_like(x)])
    _, _, Vt = np.linalg.svd(A)
    a, b, c, d, e, f = Vt[-1]
    M = np.array([[a, b / 2], [b / 2, c]])
    cen = np.linalg.solve(2 * M, -np.array([d, e]))
    k = a * cen[0] ** 2 + b * cen[0] * cen[1] + c * cen[1] ** 2 + d * cen[0] + e * cen[1] + f
    w, V = np.linalg.eigh(M)
    return cen, np.sqrt(-k / w), V


def fit_rim(img, cu, cv, rmin, rmax, bright=0.42, step_deg=2.0):
    """The rim lip of a wheel: the OUTERMOST bright-to-dark crossing along rays from (cu, cv)
    between rmin and rmax px, then a robust ellipse fit. Returns dict(centre, axes, ratio,
    points) or None."""
    lum = _lum(img)
    pts = []
    rs = np.arange(rmin, rmax, 0.5)
    for a in np.arange(0, 360, step_deg):
        t = np.radians(a); du, dv = np.cos(t), np.sin(t)
        l = np.array([_bilinear(lum, cu + r * du, cv + r * dv) for r in rs])
        l = np.convolve(l, np.ones(3) / 3, "same")
        for i in range(len(rs) - 2, 2, -1):
            if l[i] > bright and l[i + 1] <= bright and l[i - 3:i].mean() > bright + 0.03:
                pts.append((cu + rs[i] * du, cv + rs[i] * dv))
                break
    pts = np.array(pts)
    if len(pts) < 20:
        return None
    keep = np.ones(len(pts), bool)
    for _ in range(4):
        cen, ax, V = fit_conic(pts[keep])
        q = (pts - cen) @ V
        rr = np.sqrt((q[:, 0] / ax[0]) ** 2 + (q[:, 1] / ax[1]) ** 2)
        err = np.abs(rr - 1) * ax.mean()
        keep = err < max(2.5, np.percentile(err, 70))
    cen, ax, V = fit_conic(pts[keep])
    return dict(centre=cen, axes=ax, ratio=float(ax.min() / ax.max()), points=pts[keep])
