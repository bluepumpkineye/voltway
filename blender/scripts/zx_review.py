"""Review sheets: the model's outline (magenta) and panel lines (cyan) over several
of the studio photographs at once, one image to look at.

    import zx_review as RV
    RV.sheet("v10")                 # side, front, both front 3/4s -> renders/match/sheet_v10.png
    RV.sheet("v10", ("r34_left",))  # any registered cameras
"""
import os

import numpy as np

import zx_ref_match as RM
from carkit.qa import refmatch as R

# (left, top, right, bottom) crop of each photograph's car, in photo px
CROPS = {
    "side_left": (330, 1050, 3600, 2330),
    "front": (900, 820, 2940, 2330),
    "f34_left": (300, 850, 3600, 2500),
    "f34_right": (300, 850, 3600, 2500),
    "r34_left": (300, 850, 3600, 2500),
    "r34_right": (300, 850, 3600, 2500),
}


def sheet(tag, cams=("side_left", "front", "f34_left", "f34_right"), cols=2, stride=3,
          hide=()):
    # the lookdev's wall, floor and softboxes are not part of the car
    hide = tuple(hide) + ("LD_",)
    tiles = []
    for name in cams:
        l, t, r, b = CROPS.get(name, (0, 0, 3840, 2880))
        photo = R.load(RM.CAMERAS[name][0])
        idp = R.render_passes(name, tag, hide)
        inner, sil = R.boundaries(R.load(idp))
        tile = photo[t:b, l:r, :3].copy()
        for mask, col in ((inner, (0.0, 0.95, 1.0)), (sil, (1.0, 0.0, 1.0))):
            m = mask[t:b, l:r]
            d = m.copy()
            for dy in (-2, -1, 0, 1, 2):
                for dx in (-2, -1, 0, 1, 2):
                    d |= np.roll(np.roll(m, dy, 0), dx, 1)
            tile[d] = col
        tiles.append(tile[::stride, ::stride].copy())
    h = max(t.shape[0] for t in tiles)
    w = max(t.shape[1] for t in tiles)
    rows = (len(tiles) + cols - 1) // cols
    out = np.ones((rows * h, cols * w, 4), np.float32)
    for i, t in enumerate(tiles):
        y, x = (i // cols) * h, (i % cols) * w
        out[y:y + t.shape[0], x:x + t.shape[1], :3] = t
    path = os.path.join(R.OUT_DIR, "sheet_%s.png" % tag)
    R.save(out, path)
    return path
