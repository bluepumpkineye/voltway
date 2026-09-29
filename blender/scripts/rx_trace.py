"""Luxeed RX: outlines traced off the reference photographs, in photo px.

Read off gridded 3-5x crops (scratchpad imgtool). Each is ordered along the
outline. carkit.qa.refmatch.silhouette_report() measures the model's outline
against them through the solved camera (rx_ref_match).
"""

# side_left.jpg - top outline, nose to tail. The lidar pod (u 482-502) is
# left out: it stands ~13 px above the roof line.
SIDE_TOP = [
    (78.3, 360.0), (85.0, 350.0), (98.3, 333.3), (115.0, 318.3), (131.7, 310.0),
    (165.0, 300.0), (198.3, 292.7), (231.7, 288.3), (265.0, 286.0), (298.3, 284.7),
    (331.7, 283.3), (366.7, 276.0), (386.7, 270.0), (430.0, 245.0), (470.0, 226.7),
    (503.3, 213.3), (536.7, 206.0), (570.0, 202.7), (620.0, 200.0), (650.0, 200.0),
    (700.0, 203.3), (750.0, 210.7), (800.0, 220.0), (830.0, 228.3), (853.3, 233.3),
    (883.3, 248.3), (916.7, 266.7), (940.0, 273.3),
]
# tail outline, top of the lamp down to the diffuser
SIDE_TAIL = [
    (942.5, 275.0), (945.0, 300.0), (946.2, 325.0), (950.0, 350.0), (952.5, 375.0),
    (950.0, 400.0),
]
# front34_blue.jpg - roof and rear outline, from above the lidar round the
# rear haunch to the top of the rear tyre (the lamp's end shows at the
# corner, u ~1000)
F34_TOP = [
    (560.0, 225.0), (640.0, 224.5), (720.0, 225.0), (780.0, 230.0), (820.0, 233.3),
    (860.0, 240.0), (890.0, 250.0), (913.3, 263.3), (933.3, 283.3), (950.0, 303.3),
    (970.0, 320.0), (990.0, 330.0), (1000.0, 340.0), (1006.7, 360.0),
    (1011.7, 386.7), (1013.3, 406.7),
]

# front34_blue.jpg - the far (right-hand) front corner's outline, from the
# fender top down past the far lamp and intake to the chin
F34_NOSE = [
    (222.5, 362.5), (210.0, 377.5), (197.5, 395.0), (192.5, 410.0), (186.2, 430.0),
    (183.7, 447.5), (181.2, 467.5), (178.7, 492.5), (177.5, 517.5), (178.7, 530.0),
]

# rear.jpg - the car's left-hand outline seen from behind (image left),
# from the C-pillar's top down the haunch to the bumper corner. Between
# v 280 and 340 the mirror hides it. The black arch cladding shows as a thin
# strip ~25 px further out at v 600-1000: this is the PAINTED edge.
REAR_LEFT = [
    (790.0, 140.0), (760.0, 165.0), (730.0, 200.0), (700.0, 250.0), (682.0, 280.0),
    (530.0, 350.0), (505.0, 400.0), (495.0, 450.0), (490.0, 500.0), (487.0, 550.0),
    (484.0, 650.0), (482.0, 750.0), (482.0, 850.0), (486.0, 950.0),
]

# nose outline, bumper top down to the lip
SIDE_NOSE = [
    (78.3, 360.0), (78.8, 375.0), (79.5, 390.0), (78.0, 410.0), (76.0, 430.0),
]
