"""Write blender/scripts/a06t_lampdata.py from the extractions (run in Blender -b)."""
import sys, json, math
import os
SCRIPTS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import os
SP = os.environ.get("A06T_TRACE_DIR", ".")   # a folder holding the json files the scripts pass to each other
sys.path.insert(0, SP)
import numpy as np
import lampseg as S
loops = json.load(open(SP + "/loops2.json"))
cam = json.load(open(SP + "/cam_c12_0011_icp.json"))
D = json.load(open(SP + "/lamp_data.json"))

sil = S.smooth(S.remove_spurs(S.resample(np.array(loops["c12_0011.sil"]), 1.0))[0], 1.6, 1.0)
i0 = int(np.argmin(sil[:, 1])); sil = np.roll(sil, -i0, axis=0)
n = len(sil)
i_tip = int(np.argmax(np.where(sil[:, 1] < 1000, sil[:, 0], -1)))
i_bot = int(np.argmax(sil[:, 1]))
silc = np.vstack([sil, sil[:1]])
# chain C: arm tip -> along the upper edge -> round the corner -> down the stem's outer edge -> bottom tip
C = np.vstack([sil[i_tip:0:-1], sil[n - 1:i_bot - 1:-1]])
top_edge = sil[:i_tip + 1]
j_in = i_tip + int(np.argmax(sil[i_tip:, 0] < 1290))
low_edge = sil[i_tip:j_in + 1]
# inward normal: pick the sign that moves the first point into the silhouette
def normals(P):
    out = np.empty_like(P)
    for i in range(len(P)):
        a, b = P[max(0, i - 4)], P[min(len(P) - 1, i + 4)]
        t = b - a; t /= (math.hypot(*t) or 1.0)
        out[i] = (-t[1], t[0])
    return out
# the corner's own radius is smaller than the strip's offsets: round the guide's path there before offsetting
def gsmooth(P, sig):
    r = int(3 * sig)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sig) ** 2); k /= k.sum()
    out = np.empty_like(P)
    for c in (0, 1):
        ext = np.concatenate([np.full(r, P[0, c]) + (P[0, c] - P[1:r + 1, c][::-1] + P[0, c]) * 0.0, P[:, c], np.full(r, P[-1, c])])
        out[:, c] = np.convolve(ext, k, mode="valid")
    return out
Cs = gsmooth(C, 90.0)
dc = np.hypot(*(C - np.array([1289.0, 467.0])).T)
wb = np.clip(1.0 - (dc - 120.0) / 320.0, 0.0, 1.0)
wb = wb * wb * (3 - 2 * wb)
C = C * (1 - wb[:, None]) + Cs * wb[:, None]
N = normals(C)
probe = C[len(C) // 2] + N[len(C) // 2] * 6.0
if not S.inside(silc, probe):
    N = -N
n_arm = len(sil[i_tip:0:-1])
# strip width along the chain
tu = top_edge[:, 0]; tv = top_edge[:, 1]
lu = low_edge[::-1, 0]; lv = low_edge[::-1, 1]
d_bot_tab = [(1250, 74), (1500, 68), (1800, 46), (2100, 28), (2400, 30), (2600, 20)]
W = np.zeros(len(C))
for k in range(len(C)):
    u, v = C[k]
    if k < n_arm:
        thick = float(np.interp(u, lu, lv) - np.interp(u, tu, tv))
        dbot = float(np.interp(u, [a for a, _ in d_bot_tab], [b for _, b in d_bot_tab]))
        W[k] = max(0.0, thick - 40.0 - dbot)
        W[k] = min(W[k], 34.0 + max(0.0, u - 1330.0) * 0.10)
        if u < 1330:
            W[k] = 34.0
    else:
        W[k] = 34.0
# the stem narrows to nothing at the bottom tip
vmax = C[:, 1].max()
for k in range(n_arm, len(C)):
    t = (vmax - 70.0 - C[k, 1]) / 230.0
    W[k] *= max(0.0, min(1.0, t)) ** 0.8 * (3 - 2 * max(0.0, min(1.0, t))) if t < 1 else 1.0
# blend the arm/stem junction
k = 90
Wp = np.concatenate([np.full(k, W[0]), W, np.full(k, W[-1])])
Ws = np.convolve(Wp, np.ones(2 * k + 1) / (2 * k + 1), mode="same")[k:-k]
keep = Ws >= 3.0
idx = np.nonzero(keep)[0]
a, b = idx[0], idx[-1]
D_OUT = 44.0
OUT = C[a:b + 1] + N[a:b + 1] * D_OUT
INN = C[a:b + 1] + N[a:b + 1] * (D_OUT + Ws[a:b + 1])[:, None]
# stations: where the outer curve needs them
sel = S.dp(OUT, 0.5)
ids = [int(np.argmin(np.hypot(*(OUT - p).T))) for p in sel]
ids = sorted(set(ids))
# add stations so no gap exceeds 40 px
dense = [ids[0]]
for q in ids[1:]:
    while q - dense[-1] > 40:
        dense.append(dense[-1] + 40)
    dense.append(q)
ids = dense
GUIDE_OUT = OUT[ids].round(1).tolist(); GUIDE_IN = INN[ids].round(1).tolist()
print("guide stations", len(ids), "arm width max %.0f" % Ws.max(), "start", GUIDE_OUT[0], "end", GUIDE_OUT[-1])

# the slit: upper and lower chains from the left end to the tip
slit = S.smooth(S.remove_spurs(S.resample(np.array(loops["c12_0011.slit"]), 1.0))[0], 1.6, 1.0)
il = int(np.argmin(slit[:, 0])); it = int(np.argmax(slit[:, 0]))
m = len(slit)
cw = [slit[(il + k) % m] for k in range((it - il) % m + 1)]
ccw = [slit[(il - k) % m] for k in range((il - it) % m + 1)]
cw, ccw = np.array(cw), np.array(ccw)
up, lo = (cw, ccw) if cw[:, 1].mean() < ccw[:, 1].mean() else (ccw, cw)
SLIT_UP = S.dp(up, 0.5).round(1).tolist(); SLIT_LO = S.dp(lo, 0.5).round(1).tolist()
print("slit chains", len(SLIT_UP), len(SLIT_LO))

stem_out = np.array(D["stem_out"])
def fmt(name, pts, per=6):
    rows = ["(%.1f, %.1f)" % (p[0], p[1]) for p in pts]
    s = name + " = [\n"
    for i in range(0, len(rows), per):
        s += "    " + ", ".join(rows[i:i + per]) + ",\n"
    return s + "]\n"
src = '''"""Avatr 06T headlamp outlines, read from the close-up c12_0011 (details/, 3840 x 2880, the car's RIGHT lamp).

The camera was solved by fitting the model's own lamp outlines (known from c1_0002) onto this photograph's contours
(ICP, 887 pairs, median 3.1 px, rms 6 px: it is the turntable camera 16 m away at f = 59879 px, the car yawed 2.8
degrees, so 1 px is 0.23 mm). Every outline below is a contour traced from this photograph (dark glass against paint,
pixel-exact boundary chains, smoothed and simplified to 0.45 px) and is in ITS pixels; a06t_front lays them on the
nose by casting this camera's rays. Regenerated by blender/scripts/porting/a06t_lamp_trace (see its README).
"""
SIZE = (3840, 2880)
CAM = dict(loc=(%r, %r, %r), rot=(%r, %r, %r), f_px=%r)

# the whole lamp: arm, stem and pocket, clockwise from the arm's top-left corner; the arm's tip and the pocket's bottom tip are sharp
SIL_CORNERS = %r
%s
# the slit lamp under the arm, and its upper and lower edges from the rounded outer end to the pointed tip
SLIT_CORNERS = %r
%s
%s
%s
# the light-guide strip: the arm's lens, turning the corner into the stem's fluted band; outer and inner edges, paired by index
%s
%s
# the stem's outer edge, corner to bottom tip
%s''' % (cam["loc"][0], cam["loc"][1], cam["loc"][2], cam["rot"][0], cam["rot"][1], cam["rot"][2], cam["f_px"],
         tuple(D["corners_sil"]), fmt("SIL", D["sil"]), tuple(D["corners_slit"]), fmt("SLIT", D["slit"]),
         fmt("SLIT_UP", SLIT_UP), fmt("SLIT_LO", SLIT_LO), fmt("GUIDE_OUT", GUIDE_OUT), fmt("GUIDE_IN", GUIDE_IN),
         fmt("STEM_OUT", stem_out[::1]))
open(SCRIPTS + "/a06t_lampdata.py", "w", encoding="utf-8", newline="\n").write(src)
print("written", len(src))
