"""Writes blender/scripts/vps_lampdata.py: the Voyah Passion S's front end (upper lamps, nose channel, cheek pockets) read off
the studio front photograph c1_0002.jpg (3840 x 2880, Autohome series 8534) through its solved camera (vps_cam.FRONT_CAM).

Run in Blender:   blender -b --factory-startup --python gen_vps_lampdata.py
(needs ../a06t_lamp_trace/lampseg.py; the reference photographs are local only).

Traced (luminance threshold on the pale paint, pixel-exact boundary chains, Gaussian-smoothed): the lamp's outline, the white
DRL line along it (a per-column ridge), the nose channel's frame and its strip, the outline of the black cheek/grille
recess the paint is cut along. Read by hand from 3x crops of the same photograph: the smoked panel, the two projector
bezels, the slat, the vertical fin. Coordinates are pixels of c1_0002.jpg; the photograph's LEFT half (the car's right) is read
and mirrored onto the model's y >= 0 half sheet by vps_front. The centre line is u = 1920.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "a06t_lamp_trace"))
import lampseg as S                                                               # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
REF = os.path.join(ROOT, "reference", "voyah-passion-s", "exterior", "c1_0002.jpg")
OUT = os.path.join(ROOT, "scripts", "vps_lampdata.py")
CENTRE_U = 1920.0
STEP = 2.2

box = (1040, 1340, 1960, 2060)
ox, oy = box[0], box[1]
L, rgb = S.load_gray(REF, box)
Lb = S.box_blur(L, 1)
yy, xx = np.mgrid[0:L.shape[0], 0:L.shape[1]]
U, V = xx + ox, yy + oy


def biggest(mask, n=1):
    loops = [lp for lp in S.boundary_loops(mask) if S.area(lp) > 0] or S.boundary_loops(mask)
    loops.sort(key=lambda lp: -abs(S.area(lp)))
    return loops[:n]


def shift(lp, sigma, step=STEP):
    p = S.smooth(lp, sigma, 0.5) if sigma else lp
    p = S.resample(p, step)
    return [(round(float(a + ox), 2), round(float(b + oy), 2)) for a, b in p]


data = {}
# ---- the upper lamp: dark hood + lens, left of the seam at u 1408 where the channel starts
dark = S.closing(Lb < 0.50, 4)
lamp_roi = (U > 1072) & (U < 1408) & (V > 1385) & (V < 1550)
data["LAMP_OUT"] = shift(biggest(dark & lamp_roi)[0], 1.5)

# ---- the white DRL line: a hairline across the lens, read by hand from the 5x crop (the brightest ridge per column wandered
# onto the LED rows); it ends at the seam where the channel's strip begins
data["LAMP_LINE"] = [(1100.0, 1437.0), (1115.0, 1442.0), (1165.0, 1457.0), (1225.0, 1471.0), (1285.0, 1483.0),
                     (1345.0, 1495.0), (1375.0, 1500.0), (1404.0, 1506.0)]

# ---- the nose channel: frame (the dark band) and strip, per column from the seam to the emblem
ch_top, ch_bot = [], []
for u in range(1412, 1858, 6):
    col = Lb[:, u - ox]
    band = np.where(col[1470 - oy:1580 - oy] < 0.40)[0]
    if len(band):
        ch_top.append((float(u), float(band[0] + 1470)))
        ch_bot.append((float(u), float(band[-1] + 1470)))


def sm(pts, w=5):
    v = np.array([p[1] for p in pts])
    v = np.convolve(np.pad(v, w // 2, mode='edge'), np.ones(w) / w, mode='valid')
    return [(round(p[0], 1), round(float(b), 1)) for p, b in zip(pts, v)]


data["CH_TOP"], data["CH_BOT"] = sm(ch_top), sm(ch_bot)

# ---- the cheek and grille recess the paint is cut along: the dark component below the nose, up to the centre line
rec = S.closing(S.opening(Lb < 0.46, 1), 5) & (V > 1585) & (V < 2018) & (U < CENTRE_U)
loops = biggest(rec, 3)
print("recess loops", [(len(l), round(abs(S.area(l)))) for l in loops])
# The paint's lower edge (the fang's underside, v > 1975) is a soft shadow, not an edge: the threshold contour wobbles there
# by 5-15 px (it showed as a torn edge in the viewer). Take that stretch from a heavily smoothed copy of the chain.
fine = np.array(S.resample(S.smooth(loops[0], 2.0, 0.5), 3.0))
coarse = np.array(S.resample(S.smooth(loops[0], 14.0, 0.5), 3.0))
if len(coarse) != len(fine):
    coarse = np.array(S.resample(coarse, 3.0))[:len(fine)]
    fine = fine[:len(coarse)]
# the two chains start at different points: match each fine point to its nearest coarse point
d2 = ((fine[:, None, :] - coarse[None, :, :]) ** 2).sum(axis=2)
near = coarse[d2.argmin(axis=1)]
soft = (fine[:, 1] + oy > 1975.0) & (fine[:, 0] + ox < 1480.0)
w = np.convolve(soft.astype(float), np.ones(9) / 9.0, mode="same")[:, None]
blend = fine * (1.0 - w) + near * w
data["CHEEK_OUT"] = [(round(float(a + ox), 2), round(float(b + oy), 2)) for a, b in blend]
# The same outline as a clean polygon for the cut: Douglas-Peucker (2.2 px) keeps the vertices that matter, the corners
# (turning angle over 50 degrees between segments longer than 6 px: the fang's tip, the panel's ends, the centre-line and
# chin corners) stay sharp, the rest is spline-smoothed by the build (carkit.photolay.smooth_loop). The traced chain's
# +-1 px stair-steps, scaled up by the paint's curvature, were the "cutter" edge of the viewer.
simp = S.dp_closed(blend, 2.2)
# the cavity's foot has a 15 px hook (the fang's shadow edge meeting the corner) that stood out as a spike in 3D: drop it
simp = np.array([p for p in simp if not (1128.0 < p[0] + ox < 1150.0 and 1938.0 < p[1] + oy < 1955.0)])
# the panel's top-left corner is round in the photograph; the thresholded chain runs across it in a chord (the paint's lit rim
# is not dark): put the arc back (u, v of c1_0002) between the vertices either side of the chord
arc = np.array([(1102.0, 1662.0), (1107.0, 1642.0), (1119.0, 1626.0), (1138.0, 1618.5), (1160.0, 1616.0)]) - np.array([ox, oy])
a0, a1 = np.array([1099.3, 1681.7]) - np.array([ox, oy]), np.array([1176.4, 1616.4]) - np.array([ox, oy])
for i in range(len(simp)):
    if np.hypot(*(simp[i] - a0)) < 8.0 and np.hypot(*(simp[(i + 1) % len(simp)] - a1)) < 8.0:
        simp = np.vstack([simp[:i + 1], arc, simp[i + 1:]])
        break
n_s = len(simp)
corners = []
for i in range(n_s):
    a, b, c = simp[i - 1], simp[i], simp[(i + 1) % n_s]
    v1, v2 = b - a, c - b
    l1, l2 = float(np.hypot(*v1)), float(np.hypot(*v2))
    if l1 < 6.0 or l2 < 6.0:
        continue
    ang = np.degrees(np.arccos(np.clip(np.dot(v1, v2) / (l1 * l2), -1.0, 1.0)))
    if ang > 50.0:
        corners.append(i)
data["CHEEK_PTS"] = [(round(float(a + ox), 2), round(float(b + oy), 2)) for a, b in simp]
data["CHEEK_CORNERS"] = corners
print("CHEEK_PTS", n_s, "corners", corners)
for k, v in data.items():
    print(k, len(v))

# ---- the intake's grey body (satin plastic): the part of the recess to the right of the pure-black cavity (a curve read by
# hand: v, u) and below the lamp panel, left of the plate
cheek_px = np.array([(a - ox, b - oy) for a, b in data["CHEEK_OUT"]])
inside_recess = S.fill_polygon(cheek_px, L.shape)
cv_v = [1706, 1740, 1767, 1813, 1847, 1890, 1913, 1940]
cv_u = [1213, 1218, 1216, 1212, 1197, 1180, 1170, 1160]
gate = U > np.interp(V, cv_v, cv_u)
grey = S.closing(S.opening(inside_recess & gate & (V > 1702) & (U < 1698) & (V < 2000), 3), 4)
data["BULK"] = shift(biggest(grey)[0], 2.0, 6.0)

# ---- the Kunpeng emblem: the dark loops of its box. Outer loop = the black shield, the holes = the white lit blades (the upper
# arm with the stem's outer bar, the centre pill and the centre bar). Clipped at the centre line u = 1920 (the half sheet is mirrored).
ebox = (1840, 1490, 1950, 1670)
eL, _rgb = S.load_gray(REF, ebox)
eLb = S.box_blur(eL, 1)
eyy, exx = np.mgrid[0:eL.shape[0], 0:eL.shape[1]]
eloops = S.boundary_loops(S.opening((eLb < 0.42) & (eyy + ebox[1] > 1505), 1))
eloops.sort(key=lambda l: -abs(S.area(l)))


def clip_centre(lp, sigma, step=1.6):
    p = S.smooth(lp, sigma, 0.5) if sigma else lp
    p = S.resample(p, step)
    pts = [(min(float(a) + ebox[0], CENTRE_U), float(b) + ebox[1]) for a, b in p]
    out = [pts[0]]
    for q in pts[1:]:
        if abs(q[0] - out[-1][0]) > 1e-6 or abs(q[1] - out[-1][1]) > 1e-6:
            out.append(q)
    return [(round(a, 2), round(b, 2)) for a, b in out]


shield = [(min(float(a) + ebox[0], CENTRE_U), float(b) + ebox[1]) for a, b in S.resample(S.smooth(eloops[0], 1.0, 0.5), 1.6)]
shield = [q for q in shield if q[1] > 1521.0]
data["EMB_SHIELD"] = [(round(a, 2), round(b, 2)) for a, b in shield]
data["EMB_BLADE"] = clip_centre(eloops[1], 0.8)
data["EMB_BAR"] = clip_centre(eloops[2], 0.8)
data["EMB_PILL"] = clip_centre(eloops[3], 0.8)
for k in ("EMB_SHIELD", "EMB_BLADE", "EMB_BAR", "EMB_PILL"):
    print(k, len(data[k]))

HAND = '''
# ---- read by hand from 3x crops of c1_0002.jpg (about 1 px = 1.1 mm)
# the smoked headlamp panel on top of the cheek recess: its top edge follows the paint's curve, the right end curves down
PANEL = [(1112.0, 1676.0), (1114.0, 1640.0), (1122.0, 1625.0), (1140.0, 1618.0), (1250.0, 1614.0), (1330.0, 1620.0),
         (1345.0, 1635.0), (1357.0, 1660.0), (1366.0, 1686.0), (1360.0, 1693.0), (1190.0, 1697.0), (1130.0, 1692.0)]
# the two projector units (silver bezels, 3 px wide; the lens inside is dark with a dot pattern)
BEZEL_1 = (1132.0, 1633.0, 1197.0, 1669.0, 9.0)           # u0, v0, u1, v1, corner radius
BEZEL_2 = (1227.0, 1637.0, 1298.0, 1673.0, 9.0)
# the horizontal aero slat in the intake: a thin black blade with a silver edge, pointed at its inner end
SLAT = [(1148.0, 1783.0), (1252.0, 1784.0), (1268.0, 1790.0), (1281.0, 1803.0), (1262.0, 1802.0), (1148.0, 1797.0)]
# the vertical corner fin (a grey blade with a mesh behind it) at the intake's outer edge
FIN = [(1122.0, 1714.0), (1136.0, 1707.0), (1148.0, 1711.0), (1150.0, 1800.0), (1149.0, 1900.0), (1145.0, 1924.0),
       (1130.0, 1914.0), (1121.0, 1880.0), (1119.0, 1760.0)]
# the round cover (a radar / camera plug) on the intake's inner body
CIRCLE = (1424.0, 1786.0, 34.0)
'''

with open(OUT, "w") as f:
    f.write('"""Voyah Passion S front end, read off c1_0002.jpg (3840 x 2880): generated by porting/vps_lamp_trace/gen_vps_lampdata.py.\n'
            'LAMP_*, CH_*, CHEEK_OUT: traced contours (pixels); PANEL, BEZEL_*, SLAT, FIN, CIRCLE: hand readings. The car\'s right half\n'
            '(picture left); the centre line is u = 1920."""\n')
    f.write("SIZE = (3840, 2880)\nCENTRE_U = 1920.0\n")
    for k, v in data.items():
        if k == "CHEEK_CORNERS":
            f.write("CHEEK_CORNERS = %r\n" % (list(v),))
            continue
        f.write("%s = [\n" % k)
        row = []
        for p in v:
            row.append("(%.2f, %.2f)" % p)
            if len(row) == 6:
                f.write("    " + ", ".join(row) + ",\n"); row = []
        if row:
            f.write("    " + ", ".join(row) + ",\n")
        f.write("]\n")
    f.write(HAND)
print("wrote", OUT)
