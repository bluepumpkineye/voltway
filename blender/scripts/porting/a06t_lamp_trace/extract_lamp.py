"""Everything the headlamp is built from, in the pixels of the close-up c12_0011 (camera solved in cam_c12_0011_icp.json)."""
import sys, json, math
import os
SCRIPTS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import os
SP = os.environ.get("A06T_TRACE_DIR", ".")   # a folder holding the json files the scripts pass to each other
sys.path.insert(0, SCRIPTS); sys.path.insert(0, SP)
import numpy as np
import lampseg as S
loops = json.load(open(SP + "/loops2.json"))
cam = json.load(open(SP + "/cam_c12_0011_icp.json"))
out = {}
sil0 = S.resample(np.array(loops["c12_0011.sil"]), 1.0)
sil1, rem = S.remove_spurs(sil0)
print('spurs removed from sil:', rem)
sil = S.smooth(sil1, 1.6, 1.0)
slit0 = S.resample(np.array(loops["c12_0011.slit"]), 1.0)
slit1, rem2 = S.remove_spurs(slit0)
print('spurs removed from slit:', rem2)
slit = S.smooth(slit1, 1.6, 1.0)
n = len(sil)
i_top = int(np.argmin(sil[:, 1]))
sil = np.roll(sil, -i_top, axis=0)                      # start at the top-left corner, clockwise on screen
i_tip = int(np.argmax(np.where(sil[:, 1] < 1000, sil[:, 0], -1)))
i_bot = int(np.argmax(sil[:, 1]))
print("n", n, "tip idx", i_tip, sil[i_tip].round(1), "bottom idx", i_bot, sil[i_bot].round(1))
# the silhouette chains
top_edge = sil[:i_tip + 1]                              # corner -> arm tip, the arm's upper edge
low_chain = sil[i_tip:]                                 # tip -> inner corner -> stem inner edge -> pocket -> bottom tip -> outer edge back
# inner corner of the 7: the first point after the tip whose u is below 1300 on the arm's lower edge
j = i_tip + int(np.argmax(sil[i_tip:, 0] < 1290))
inner_corner = sil[j]
print("inner corner idx", j, inner_corner.round(1))
low_edge = sil[i_tip:j + 1]                             # the arm's lower edge, tip -> inner corner
stem_out = sil[i_bot:]                                  # bottom tip -> up the outer edge -> (wraps) corner
stem_out = np.vstack([stem_out, sil[:40]])[::-1]        # corner -> bottom tip, top to bottom
out["sil"] = S.dp_closed(sil, 0.45).round(1).tolist()
out["slit"] = S.dp_closed(slit, 0.45).round(1).tolist()
out["corners_sil"] = [int(np.argmin(np.hypot(*(np.array(out["sil"]) - sil[k]).T))) for k in (i_tip, i_bot)]
out["corners_slit"] = [int(np.argmin(np.hypot(*(np.array(out["slit"]) - slit[np.argmax(slit[:, 0])]).T)))]
print("sil pts", len(out["sil"]), "slit pts", len(out["slit"]))
# lens: between the arm's two edges, inset by the bezel bands read off the luminance profiles
d_bot_tab = [(1250, 74), (1500, 68), (1800, 46), (2100, 28), (2400, 30), (2600, 20)]
def d_bot(p): return float(np.interp(p[0], [a for a, _ in d_bot_tab], [b for _, b in d_bot_tab]))
def d_top(p): return 40.0
ti = S.offset_polyline(top_edge[::8], d_top, side=+1.0)   # inward = below the upper edge
bi = S.offset_polyline(low_edge[::8], d_bot, side=+1.0)
print("top inset sample", ti[:3].round(0), ti[-3:].round(0)); print("bot inset sample", bi[:3].round(0), bi[-3:].round(0))
out["_top_edge"] = top_edge[::6].round(1).tolist(); out["_low_edge"] = low_edge[::6].round(1).tolist()
out["_ti"] = ti.round(1).tolist(); out["_bi"] = bi.round(1).tolist()
out["stem_out"] = S.dp(stem_out, 0.5).round(1).tolist()

# lens ends: the left diagonal read on c1_0002 ((1218,1578) -> (1257,1607)), projected into this camera through the model
import a06t_front as FR
from carkit.qa import refmatch as R
def to_l11(u, v):
    p, _n = FR._on_paint(u, v)
    return np.array(R._project_raw(tuple(cam["size"]), cam["loc"], cam["rot"], cam["f_px"], (p.x, -p.y, p.z)))
U_L = 1340.0
L0 = np.array([U_L, float(np.interp(U_L, ti[:, 0], ti[:, 1]))]); L1 = np.array([U_L, float(np.interp(U_L, bi[::-1][:, 0], bi[::-1][:, 1]))])
print("lens left diagonal", L0.round(0), L1.round(0))
top_pts = np.array([q for q in ti if q[0] >= L0[0]])
bot_pts = np.array([q for q in bi[::-1] if q[0] >= L1[0]])
# right end: where the two insets meet
k = len(top_pts)
for a in range(len(top_pts)):
    vb = np.interp(top_pts[a, 0], bot_pts[:, 0], bot_pts[:, 1])
    if top_pts[a, 1] >= vb - 5:
        k = a; break
top_pts = top_pts[:k]
bot_pts = bot_pts[bot_pts[:, 0] <= top_pts[-1, 0]]
lens = np.vstack([[L0], top_pts, bot_pts[::-1], [L1]])
out["lens"] = lens.round(1).tolist()
print("lens pts", len(lens), "right end", top_pts[-1].round(0))
json.dump(out, open(SP + "/lamp_data.json", "w"))
