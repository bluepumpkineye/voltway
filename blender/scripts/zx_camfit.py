"""Helpers for fitting the Zeekr 7X studio cameras: the model's projected top
envelope against the photograph's top edge (quick, no render)."""
import json
import math
import os

import bpy
import numpy as np
from mathutils import Euler

# where the camera-solve JSON files were saved (kept outside the repo): set VOLTWAY_SCRATCH to that folder
SP = os.path.join(os.environ.get("VOLTWAY_SCRATCH", "."), "")


def skin_vertices(names=("ZX_Skin", "ZX_CapF", "ZX_CapR")):
    dg = bpy.context.evaluated_depsgraph_get()
    V = []
    for nm in names:
        ob = bpy.data.objects.get(nm)
        if ob is None:
            continue
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        V += [tuple(ob.matrix_world @ v.co) for v in me.vertices]
        ev.to_mesh_clear()
    return np.array(V)


def project_all(V, loc, rot, f, size=(3840, 2880)):
    Rm = np.array(Euler(tuple(math.radians(a) for a in rot), 'XYZ').to_matrix())
    c = (V - np.array(loc)) @ Rm
    z = -c[:, 2]
    ok = z > 0.1
    u = 0.5 * size[0] + f * c[ok, 0] / z[ok]
    v = 0.5 * size[1] - f * c[ok, 1] / z[ok]
    return u, v


def top_env(u, v, bins, half=5):
    out = []
    for b0 in bins:
        m = (u >= b0 - half) & (u < b0 + half)
        out.append(v[m].min() if m.any() else None)
    return out


def top_error(V, loc, rot, f, top, x_range):
    sel = [p for p in top if x_range[0] <= p["x"] <= x_range[1]]
    u, v = project_all(V, loc, rot, f)
    e = top_env(u, v, [p["x"] for p in sel])
    d = [e[i] - sel[i]["y"] for i in range(len(sel)) if e[i] is not None]
    if not d:
        return 0.0, 0.0
    return sum(d) / len(d), (sum(x * x for x in d) / len(d)) ** 0.5


def load_top(name):
    return json.load(open(SP + name))


def row_extents(name, tag, rows, hide=("Glass", "LD_")):
    """The model's silhouette through camera `name`: (left u, right u) of the
    id-render's alpha at each photo row (None where empty)."""
    import zx_ref_match as RM
    from carkit.qa import refmatch as R
    path = R.render_passes(name, tag, hide)
    a = R.load(path)[..., 3] > 0.5
    out = {}
    for v in rows:
        cols = np.nonzero(a[int(v)])[0]
        out[v] = (int(cols.min()), int(cols.max())) if len(cols) else None
    return out


def compare_rows(name, tag, photo_L, photo_R, scale_px_per_m):
    """Print photo vs model edge per row, and the model's excess in metres (+ = model
    wider than the photo): photo_L / photo_R are scanmask outputs [{x, y}, ...]."""
    rows = sorted({p["y"] for p in photo_L})
    ext = row_extents(name, tag, rows)
    L = {p["y"]: p["x"] for p in photo_L}
    Rr = {p["y"]: p["x"] for p in photo_R}
    for v in rows:
        e = ext.get(v)
        if e is None:
            print(v, "model empty")
            continue
        dl = (L[v] - e[0]) / scale_px_per_m      # model left edge further left -> wider
        dr = (e[1] - Rr[v]) / scale_px_per_m
        print("v %4d  photo %4d..%4d  model %4d..%4d  excess L %+.3f R %+.3f m" % (
            v, L[v], Rr[v], e[0], e[1], dl, dr))
