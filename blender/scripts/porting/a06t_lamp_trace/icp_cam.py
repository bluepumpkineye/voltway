"""Solve a close-up's camera by fitting the lamp outlines the model knows (from c1_0002) onto the close-up's own contours (ICP)."""
import sys, json, math
import os
SCRIPTS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import os
SP = os.environ.get("A06T_TRACE_DIR", ".")   # a folder holding the json files the scripts pass to each other
sys.path.insert(0, SCRIPTS); sys.path.insert(0, SP)
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
import lampseg as S
import a06t_front as FR
from carkit.qa import refmatch as R

loops = json.load(open(SP + "/loops2.json"))
src = {"sil": np.array(loops["c1_0002.sil"]), "slit": np.array(loops["c1_0002.slit"])}
dst = {"sil": np.array(loops["c12_0011.sil"]), "slit": np.array(loops["c12_0011.slit"])}

# 3D points from the c1_0002 outlines (resampled every 2.5 px), car's right side (y < 0)
P3, K3 = [], []
for k, lp in src.items():
    for (u, v) in S.resample(lp, 2.5):
        p, _n = FR._on_paint(float(u), float(v))
        P3.append((p.x, -p.y, p.z)); K3.append(k)
print("3D points", len(P3))
# target points: every 1.5 px of the close-up's contours
T = {k: S.resample(lp, 1.5) for k, lp in dst.items()}
kd = {}
for k, pts in T.items():
    t = KDTree(len(pts))
    for i, (u, v) in enumerate(pts): t.insert((u, v, 0.0), i)
    t.balance(); kd[k] = t

size = (3840, 2880)
import os
cam = json.load(open(SP + ("/cam_c12_0011_icp.json" if os.path.exists(SP + "/cam_c12_0011_icp.json") else "/cam_c12_0011.json")))
loc, rot, f = list(cam["loc"]), list(cam["rot"]), cam["f_px"]
for it in range(30):
    pairs, dists = [], []
    for X, k in zip(P3, K3):
        uv = R._project_raw(size, loc, rot, f, X)
        if uv is None: continue
        _co, i, d = kd[k].find((uv[0], uv[1], 0.0))
        dists.append(d)
        if d < 25:
            pairs.append((tuple(T[k][i]), X))
    sol = R.solve_camera(size, pairs, loc, rot, f, fix=("x",), iters=120)
    loc, rot, f = list(sol["loc"]), list(sol["rot"]), sol["f_px"]
    print("iter %2d pairs %4d  median dist %.1f  rms %.2f  f %.0f  loc %s rot %s" % (it, len(pairs), float(np.median(dists)), sol["rms"], f, [round(c, 3) for c in loc], [round(c, 3) for c in rot]))
json.dump(dict(loc=loc, rot=rot, f_px=f, size=size), open(SP + "/cam_c12_0011_icp.json", "w"))
# project the c1_0002 outlines into the close-up for the overlay
proj = {}
for k in ("sil", "slit"):
    proj[k] = [R._project_raw(size, loc, rot, f, X) for X, kk in zip(P3, K3) if kk == k]
json.dump({"proj." + k: v for k, v in proj.items()}, open(SP + "/proj_c12.json", "w"))
