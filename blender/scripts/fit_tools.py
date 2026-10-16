"""Compare the model's silhouette through a matched camera with the photograph's.

Used with photo_tools and carkit.qa.refmatch. The model's alpha comes from
refmatch.render_passes(name, tag) (an object-ID render); the photograph's outline from a
mask the caller builds (the studio backdrops differ, see photo_tools.car_mask).

    err = fit_tools.top_error(name, tag, photo_mask, us)        # px: + = model above the photo
    err = fit_tools.row_error(name, tag, photo_mask, vs, "left")  # px: + = model further out

Errors are in image pixels, v down. Convert to metres with the local scale
f / (D - y) (about 650 px/m on the flank of the G9L's side photograph).
"""
import os

import numpy as np

from carkit.qa import refmatch as R


def model_alpha(name, tag):
    p = os.path.join(R.OUT_DIR, "%s_%s_id.png" % (name, tag))
    return R.load(p)[..., 3] > 0.5


def _first_run(col, min_run=10):
    run = np.convolve(col.astype(np.int32), np.ones(min_run, np.int32), "valid")
    hit = np.flatnonzero(run == min_run)
    return float(hit[0]) if hit.size else float("nan")


def top_error(name, tag, photo_mask, us, alpha=None):
    """v of the model's top edge minus the photograph's, at image columns `us`."""
    a = model_alpha(name, tag) if alpha is None else alpha
    out = []
    for u in us:
        vm = _first_run(a[:, int(u)])
        vp = _first_run(photo_mask[:, int(u)])
        out.append(vm - vp)
    return out


def row_error(name, tag, photo_mask, vs, side, alpha=None, centre=1900, gap=4):
    """Horizontal distance (px) of the model's outer edge beyond the photograph's, on rows vs.

    side "left" (the nose in a left-side photo) or "right" (the tail). + = model further out."""
    a = model_alpha(name, tag) if alpha is None else alpha

    def edge(m, v):
        step = -1 if side == "left" else 1
        u, miss = centre, 0
        while 0 < u < m.shape[1] - 1:
            if m[v, u]:
                miss = 0
            else:
                miss += 1
                if miss > gap:
                    break
            u += step
        return u - step * miss

    out = []
    for v in vs:
        em, ep = edge(a, int(v)), edge(photo_mask, int(v))
        out.append((em - ep) * (-1 if side == "left" else 1))
    return out


def column_edge_profile(mask, us, which="top"):
    return [(_first_run(mask[:, int(u)]) if which == "top" else float("nan")) for u in us]
