"""Contours of dark regions in a photograph (pixel-exact boundary chains, smoothed). Runs in Blender's Python (numpy)."""
import math
import numpy as np
import bpy


def load_gray(path, box=None, linear=False):
    """Luminance 0..1 (display values, not linearised) of an image, optionally cropped box=(u0, v0, u1, v1);
    also the RGB crop. Row 0 is the TOP."""
    img = bpy.data.images.load(path, check_existing=False)
    img.colorspace_settings.name = 'Non-Color'
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    a = a.reshape(h, w, 4)[::-1]
    bpy.data.images.remove(img)
    if box:
        u0, v0, u1, v1 = box
        a = a[v0:v1, u0:u1]
    rgb = np.ascontiguousarray(a[..., :3])
    L = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    return L, rgb


def box_blur(a, r):
    if r <= 0:
        return a
    k = 2 * r + 1
    c = np.cumsum(np.pad(a, ((r + 1, r), (0, 0)), mode='edge'), axis=0)
    a = (c[k:] - c[:-k]) / k
    c = np.cumsum(np.pad(a, ((0, 0), (r + 1, r)), mode='edge'), axis=1)
    return (c[:, k:] - c[:, :-k]) / k


def boundary_loops(mask):
    """All closed boundary chains of a boolean mask, as arrays of (u, v) grid-vertex coordinates (pixel (j, i) covers
    [j, j+1] x [i, i+1]); the mask is on the right-hand side of each edge as walked."""
    h, w = mask.shape
    m = np.pad(mask, 1)
    edges = {}
    # vertex (x, y) -> list of next vertices. An edge keeps the mask on its right (screen coordinates, y down).
    top = m[1:-1, 1:-1] & ~m[:-2, 1:-1]          # pixel set, pixel above not: edge along the pixel's top, walked +x? (right side = below = inside)
    bot = m[1:-1, 1:-1] & ~m[2:, 1:-1]
    lef = m[1:-1, 1:-1] & ~m[1:-1, :-2]
    rig = m[1:-1, 1:-1] & ~m[1:-1, 2:]
    for (i, j) in zip(*np.nonzero(top)):         # walking +x along the top edge keeps "below" on the right in y-down coords
        edges.setdefault((j, i), []).append((j + 1, i))
    for (i, j) in zip(*np.nonzero(bot)):         # bottom edge walked -x
        edges.setdefault((j + 1, i + 1), []).append((j, i + 1))
    for (i, j) in zip(*np.nonzero(lef)):         # left edge walked -y (up)
        edges.setdefault((j, i + 1), []).append((j, i))
    for (i, j) in zip(*np.nonzero(rig)):         # right edge walked +y (down)
        edges.setdefault((j + 1, i), []).append((j + 1, i + 1))
    loops = []
    while edges:
        start = next(iter(edges))
        loop = [start]
        cur = start
        prev_dir = None
        while True:
            nxt = edges.get(cur)
            if not nxt:
                break
            if len(nxt) > 1 and prev_dir is not None:
                # two ways out (pixels touching at a corner): turn right first (keeps pieces apart)
                def turn(n):
                    d = (n[0] - cur[0], n[1] - cur[1])
                    return prev_dir[0] * d[1] - prev_dir[1] * d[0]
                nxt.sort(key=turn, reverse=True)
            n = nxt.pop(0)
            if not nxt:
                del edges[cur]
            prev_dir = (n[0] - cur[0], n[1] - cur[1])
            cur = n
            if cur == start:
                break
            loop.append(cur)
        if len(loop) > 8:
            loops.append(np.array(loop, float))
    return loops


def area(loop):
    x, y = loop[:, 0], loop[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def inside(loop, p):
    x, y = loop[:, 0], loop[:, 1]
    x2, y2 = np.roll(x, -1), np.roll(y, -1)
    c = ((y > p[1]) != (y2 > p[1])) & (p[0] < x + (p[1] - y) * (x2 - x) / np.where(y2 == y, 1e-9, y2 - y))
    return bool(np.count_nonzero(c) % 2)


def resample(loop, step):
    seg = np.hypot(*(np.roll(loop, -1, axis=0) - loop).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    n = max(8, int(round(s[-1] / step)))
    t = np.linspace(0, s[-1], n, endpoint=False)
    p = np.vstack([loop, loop[:1]])
    return np.stack([np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])], axis=1)


def smooth(loop, sigma_px, step=1.0, keep=()):
    """Periodic Gaussian smoothing of a closed outline sampled every `step` px."""
    p = resample(loop, step)
    n = len(p)
    r = int(3 * sigma_px / step) + 1
    k = np.exp(-0.5 * (np.arange(-r, r + 1) * step / sigma_px) ** 2)
    k /= k.sum()
    out = np.empty_like(p)
    for c in (0, 1):
        ext = np.concatenate([p[-r:, c], p[:, c], p[:r, c]])
        out[:, c] = np.convolve(ext, k, mode='valid')
    return out


def opening(mask, r):
    """Binary opening with a (2r+1) square: erosion then dilation, through box blurs."""
    m = mask.astype(np.float32)
    e = box_blur(m, r) > 0.999
    return box_blur(e.astype(np.float32), r) > 0.001


def closing(mask, r):
    m = mask.astype(np.float32)
    d = box_blur(m, r) > 0.001
    return box_blur(d.astype(np.float32), r) > 0.999


def fill_polygon(loop, shape):
    """Boolean mask of the pixels whose centres lie inside the closed loop (pixel coordinates, shape = (h, w))."""
    h, w = shape
    x0, y0 = loop[:, 0], loop[:, 1]
    x1, y1 = np.roll(x0, -1), np.roll(y0, -1)
    mask = np.zeros(shape, bool)
    ylo, yhi = int(max(0, math.floor(y0.min()))), int(min(h - 1, math.ceil(y0.max())))
    for y in range(ylo, yhi + 1):
        yc = y + 0.5
        sel = (y0 > yc) != (y1 > yc)
        if not sel.any():
            continue
        xs = x0[sel] + (yc - y0[sel]) * (x1[sel] - x0[sel]) / (y1[sel] - y0[sel])
        xs.sort()
        for a, b in zip(xs[0::2], xs[1::2]):
            mask[y, int(max(0, math.ceil(a - 0.5))):int(min(w, math.floor(b - 0.5) + 1))] = True
    return mask


def dp(pts, tol, closed=False):
    """Douglas-Peucker simplification of a polyline (indices kept)."""
    pts = np.asarray(pts, float)
    n = len(pts)
    keep = np.zeros(n, bool)
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        p, q = pts[a], pts[b]
        d = q - p
        L = math.hypot(*d) or 1e-9
        t = pts[a + 1:b] - p
        dist = np.abs(t[:, 0] * d[1] - t[:, 1] * d[0]) / L
        i = int(np.argmax(dist))
        if dist[i] > tol:
            m = a + 1 + i
            keep[m] = True
            stack += [(a, m), (m, b)]
    return pts[keep]


def offset_polyline(pts, dist_fn, side=1.0):
    """Move each point of an open polyline along its normal by dist_fn(point); side = +1 / -1 picks the normal."""
    pts = np.asarray(pts, float)
    out = np.empty_like(pts)
    for i in range(len(pts)):
        a, b = pts[max(0, i - 2)], pts[min(len(pts) - 1, i + 2)]
        t = b - a
        t /= (math.hypot(*t) or 1.0)
        n = np.array([-t[1], t[0]]) * side
        out[i] = pts[i] + n * dist_fn(pts[i])
    return out


def dp_closed(pts, tol):
    pts = np.asarray(pts, float)
    far = int(np.argmax(np.hypot(*(pts - pts[0]).T)))
    a = dp(pts[:far + 1], tol)
    b = dp(np.vstack([pts[far:], pts[:1]]), tol)
    return np.vstack([a[:-1], b[:-1]])


def thin(img):
    """Zhang-Suen thinning of a boolean image (vectorised)."""
    a = np.pad(img.astype(np.uint8), 1)
    while True:
        changed = False
        for step in (0, 1):
            p2, p3, p4, p5 = a[:-2, 1:-1], a[:-2, 2:], a[1:-1, 2:], a[2:, 2:]
            p6, p7, p8, p9 = a[2:, 1:-1], a[2:, :-2], a[1:-1, :-2], a[:-2, :-2]
            c = a[1:-1, 1:-1]
            seq = [p2, p3, p4, p5, p6, p7, p8, p9, p2]
            N = sum(p.astype(np.int16) for p in (p2, p3, p4, p5, p6, p7, p8, p9))
            Sx = sum(((seq[i] == 0) & (seq[i + 1] == 1)).astype(np.int16) for i in range(8))
            if step == 0:
                m = (p2 * p4 * p6 == 0) & (p4 * p6 * p8 == 0)
            else:
                m = (p2 * p4 * p8 == 0) & (p2 * p6 * p8 == 0)
            kill = (c == 1) & (N >= 2) & (N <= 6) & (Sx == 1) & m
            if kill.any():
                a[1:-1, 1:-1][kill] = 0
                changed = True
        if not changed:
            break
    return a[1:-1, 1:-1].astype(bool)


def skeleton_paths(sk, min_len=25):
    """Trace a thinned image into ordered pixel paths (junction pixels split paths)."""
    ys, xs = np.nonzero(sk)
    pix = set(zip(xs.tolist(), ys.tolist()))
    nb = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
    deg = {p: sum((p[0] + dx, p[1] + dy) in pix for dx, dy in nb) for p in pix}
    junction = {p for p, d in deg.items() if d >= 3}
    rest = pix - junction
    seen, paths = set(), []
    def nbrs(p):
        return [(p[0] + dx, p[1] + dy) for dx, dy in nb if (p[0] + dx, p[1] + dy) in rest]
    ends = [p for p in rest if len(nbrs(p)) <= 1]
    for start in ends + list(rest):
        if start in seen:
            continue
        path = [start]
        seen.add(start)
        cur = start
        while True:
            nxt = [q for q in nbrs(cur) if q not in seen]
            if not nxt:
                break
            cur = nxt[0]
            seen.add(cur)
            path.append(cur)
        if len(path) >= min_len:
            paths.append(np.array(path, float))
    return paths


def remove_spurs(poly, gap=3.5, window=500, min_len=16):
    """Cut dead-end spurs out of a closed 1-px-spaced outline: where the contour comes back within `gap` px of a point
    it passed more than `min_len` px earlier (along the contour) it is retracing itself, so the loop between is dropped."""
    P = np.asarray(poly, float)
    keep = np.ones(len(P), bool)
    i = 0
    n = len(P)
    removed = 0
    while i < n - 1:
        hi = min(n, i + window)
        d = np.hypot(*(P[i + min_len:hi] - P[i]).T) if i + min_len < hi else np.array([])
        j = None
        if len(d):
            hit = np.nonzero(d < gap)[0]
            if len(hit):
                j = i + min_len + int(hit[-1])      # the LAST return within the window: swallow the whole excursion
        if j is not None and j > i + min_len:
            keep[i + 1:j] = False
            removed += j - i - 1
            i = j
        else:
            i += 1
    return P[keep], removed
