import sys, json, math
import os
SP = os.environ.get("A06T_TRACE_DIR", ".")   # a folder holding the json files the scripts pass to each other
sys.path.insert(0, SP)
import numpy as np
import lampseg as S
REF = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "reference", "avatr-06t")).replace("\\", "/") + "/"

def pick(loops, ox, oy, seed, minarea=2000):
    best = None
    for lp in loops:
        a = S.area(lp)
        if abs(a) < minarea: continue
        if S.inside(lp, (seed[0] - ox, seed[1] - oy)):
            if best is None or abs(a) > abs(S.area(best)):
                best = lp
    return best

def shift(lp, ox, oy):
    return (lp + np.array([ox, oy])).tolist()

out = {}
# ---------------------------------------------------------------- c12_0011
box = (900, 300, 3500, 2600)
L, rgb = S.load_gray(REF + "details/c12_0011.jpg", box)
Lb = S.box_blur(L, 1)
ox, oy = box[0], box[1]
loops = S.boundary_loops(S.opening(Lb < 0.30, 3))
sil = pick(loops, ox, oy, (1215, 1700)); slit = pick(loops, ox, oy, (2100, 1025))
print("c12 sil", len(sil), int(abs(S.area(sil))), "slit", len(slit), int(abs(S.area(slit))))
out["c12_0011.sil"] = shift(sil, ox, oy); out["c12_0011.slit"] = shift(slit, ox, oy)
# arm lens: lit pixels inside the silhouette in the arm's zone, the hairlines opened away, the biggest piece
inside_sil = S.fill_polygon(sil, L.shape)
yy, xx = np.mgrid[0:L.shape[0], 0:L.shape[1]]
zone = (yy + oy < 1000) & (xx + ox > 1250)
lens_mask = S.opening(inside_sil & (Lb > 0.20) & zone, 3)
cl = S.boundary_loops(lens_mask)
cl = [lp for lp in cl if S.area(lp) > 0] or cl
cl.sort(key=lambda lp: -abs(S.area(lp)))
print("lens loops", [(len(lp), int(abs(S.area(lp)))) for lp in cl[:4]])
out["c12_0011.lens"] = shift(cl[0], ox, oy)
# sensor ring and tow cap (for the camera solve)
loops3 = S.boundary_loops(S.opening(Lb < 0.55, 1))
for nm, seed in (("sensor1", (1821, 2194)), ("tow", (3341, 1776))):
    best = None
    for lp in loops3:
        a = abs(S.area(lp))
        if 400 < a < 400000 and S.inside(lp, (seed[0] - ox, seed[1] - oy)):
            if best is None or a < abs(S.area(best)): best = lp
    if best is not None:
        c = best.mean(axis=0) + np.array([ox, oy]); print(nm, "centre", c.round(1), "area", int(abs(S.area(best))))
        out["c12_0011." + nm] = shift(best, ox, oy)
# ---------------------------------------------------------------- c1_0002
box = (1000, 1480, 1700, 2100)
L, rgb = S.load_gray(REF + "exterior/c1_0002.jpg", box)
Lb = S.box_blur(L, 1)
ox, oy = box[0], box[1]
loops = S.boundary_loops(S.opening(Lb < 0.36, 2))
sil = pick(loops, ox, oy, (1135, 1800)); slit = pick(loops, ox, oy, (1300, 1692))
print("c1 sil", None if sil is None else (len(sil), int(abs(S.area(sil)))), "slit", None if slit is None else (len(slit), int(abs(S.area(slit)))))
if sil is not None: out["c1_0002.sil"] = shift(sil, ox, oy)
if slit is not None: out["c1_0002.slit"] = shift(slit, ox, oy)
json.dump(out, open(SP + "/loops2.json", "w"))
