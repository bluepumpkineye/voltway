"""Denza Z9 front end, read off the black car's straight-on photograph c1_0034.jpg (3840 x 2880, Autohome series 7838).

Every outline is in PIXELS of that photograph, the LEFT half of the picture only (u < UC); z9_front mirrors it onto the
car's +y half sheet through the solved camera (z9_ref_match "front_black"), so the two sides cannot drift apart. The
black car hides its bumper against itself, so the outlines were read on 2.8x crops with the shadows lifted (CLAHE) and a
labelled 25 px grid, then drawn back over the photograph and corrected (2026-11-19); the white car (c1_0042, c1_0046)
and the grey one (c1_0066) were used to understand what each dark shape IS:

    lamp        one swept blade: tall and blunt at the OUTER end (the fender's crown), a sharp tip low and inboard beside the
                emblem. Its top edge is a straight diagonal, its lower edge a long convex curve. (The first build had it the
                other way up: tip high, outer end hooked upward.)
    drl         the slim dark "eyebrow" under the lamp: a pale glass wedge at the outer end that runs on as a black spear
                to a point below the lamp's tip, with a blue-white line along its lower edge
    cavity      ONE dark opening in the bumper: a swept pocket under each outer top corner (its upper edge is the painted
                fascia's own lower edge), the central radiator grille, and between them the body-colour "wing", a wedge that
                is fixed at the outer end only and points at the centre with a sharp tip
    pad         the long body-colour bar above the plate (the front radar's cover), outlined by a hairline

(Heights are not read from the picture directly: a pixel becomes a point by a ray through the photo's own camera onto the
model's panels, see z9_front._on_surface.)
"""

# the photograph's column of the nose's centre line (the camera sees the nose 17 px right of the silhouette's centre)
UC = 1937.0

# ----------------------------------------------------------------------------------------------- the headlamp
# the outer outline of the lamp's black rim, clockwise from the top-left corner
LAMP_OUT = [(1156, 1536), (1176, 1534), (1200, 1536), (1228, 1543), (1300, 1574), (1400, 1624), (1430, 1635), (1477, 1656),
            (1509, 1681), (1528, 1708), (1541, 1729), (1544, 1738), (1535, 1741), (1512, 1738), (1477, 1731), (1405, 1716),
            (1299, 1693), (1228, 1667), (1157, 1645), (1121, 1634), (1104, 1612), (1103, 1597), (1105, 1580), (1111, 1563),
            (1121, 1550), (1135, 1541), (1147, 1537)]
# (the photographed lamp's top outer corner is at (1141, 1514), on the model's hood / fender / nose junction, where the three
# panels do not meet as the real car's one skin does: a lens laid there bridges a 12 cm step as a flap. The corner is cut off
# 15 px lower, round, so the lens stays on the nose cap.)
# the day-running light guide: a thin bright stripe just under the lens' upper rim, and the silver hairline under the lower
LAMP_DRL = [(1204, 1549), (1230, 1558), (1300, 1581), (1400, 1630), (1445, 1650), (1482, 1668), (1508, 1690), (1523, 1712)]
LAMP_HAIR = [(1150, 1641), (1228, 1662), (1299, 1688), (1405, 1711), (1477, 1726), (1512, 1733)]
# the three LED modules (centre u, v, half width, half height, in px): bright rectangles under the lens
LAMP_MODULES = [(1190, 1582, 29, 14), (1283, 1617, 30, 15), (1412, 1664, 29, 19)]

# ------------------------------------------------------------------------------------------ the eyebrow DRL
DRL_GLASS = [(1107, 1698), (1150, 1710), (1192, 1725), (1260, 1745), (1334, 1766), (1300, 1763), (1260, 1757), (1221, 1750),
             (1157, 1743), (1132, 1735), (1110, 1722)]
DRL_SPEAR = [(1334, 1768), (1405, 1791), (1469, 1814), (1537, 1857)]
DRL_LINE = [(1118, 1724), (1160, 1737), (1221, 1749), (1290, 1761)]

# --------------------------------------------------------------------------------- the cavity (pockets + grille)
# clockwise: the pocket's outer top tip, along the painted fascia's lower edge to the centre line, down the centre line,
# along the bottom to the wing's lower corner, up the wing's lower edge to its tip, back along its upper edge to the outer
# wall, up the wall. The bottom runs below the fascia sheet's own edge (the chin lip closes it).
CAVITY = [(1153, 1827), (1171, 1857), (1199, 1887), (1235, 1910), (1299, 1926), (1370, 1942), (1441, 1957), (1512, 1969),
          (1583, 1978), (1697, 1990), (1937, 1994),
          (1937, 2195), (1340, 2195), (1349, 2150),
          (1405, 2129), (1441, 2111), (1494, 2086), (1535, 2057),
          (1494, 2049), (1441, 2038), (1370, 2028), (1299, 2022), (1235, 2020), (1203, 2026), (1164, 2037), (1136, 2045),
          (1112, 2030), (1105, 2001), (1107, 1974), (1110, 1939), (1116, 1903), (1122, 1868), (1130, 1839), (1143, 1820)]

# the radiator: four rows (v0, v1), from the left end to the radar pod (rows 2-4) or behind the plate (row 1); the ribs
GRILLE_ROWS = [(1987, 2016, 1905), (2029, 2057, 1862), (2070, 2096, 1860), (2109, 2134, 1860)]
GRILLE_U0 = 1614
GRILLE_RIBS = (1661.5, 1772.0)
POD = (1863, 2053, 2017, 2135)           # the radar pod: u0, v0, u1, v1 (centre 1940)
CAMERA = (1941, 2014, 6)                  # the little lens that hangs under the plate: u, v, radius px

# the pocket's contents: a sensor module (dark frame with a white-grey window cylinder and a small dark lens) and a
# square cover beside it
MODULE = (1166, 1940, 1294, 1998)
MODULE_LENS = (1196, 1960, 9)
MODULE_CYL = (1256, 1971, 10, 17)         # u, v, half width, half height
COVER = (1349, 1969, 1391, 1999)

# --------------------------------------------------------------------------------------- the painted fascia
SENSORS = [(1176, 1894), (1610, 1905)]    # parking sensors, ring radius 9 px
WASHER = (1327, 1875, 45, 20, 35.0)       # the washer jet's cap: centre, semi-axes (px), long axis angle (deg, down to the right)
PAD = [(1560, 1800), (1570, 1815), (1596, 1830), (1640, 1836), (1750, 1839), (1850, 1840), (1937, 1840), (1937, 1792),
       (1850, 1790), (1750, 1789), (1640, 1791), (1585, 1795)]
EMBLEM = (1943, 1727, 41)                 # centre u, v and radius (px) of the nose badge
