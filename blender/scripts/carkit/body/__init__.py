"""The body model: flank loft, wrapped end caps, panels and the bumper kit.

    loft     LoftBody - the flank surface S(x, v) from profile curves
    caps     WrapCap - nose and tail patches C(w, v), G1 to the flank
    model    CarBody - loft + caps as one surface: project, proud, side_point
    panels   panel grids with real shut lines, cap grids, shell, liners, tray
    fascia   bumper kit: split nose, recessed mouth, walls, tunnels, blades,
             valances, cap panels
    morph    start a new car from a donor body scaled to its published
             dimensions
"""
from .loft import LoftBody, Section
from .caps import WrapCap
from .model import CarBody
