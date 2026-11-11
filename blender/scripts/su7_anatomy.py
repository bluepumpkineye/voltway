"""The Xiaomi SU7 Ultra's anatomy: its dimensions and the call into carkit.anatomy.

Measured off the shipped exterior (public/models/su7-ultra.glb, imported into Blender, 2026-11-02):
  hubs  FL (1.558, 0.830, 0.359)   RL (-1.442, 0.812, 0.358)   -> wheelbase 3.000
  the flat underbody is 0.15 m above the road, the cabin floor's underside 0.32 m, its half
  width between the sills 0.70 m; the lowest body panel is 0.098 m.
Published: 265/35 R21 front, 305/30 R21 rear (CarNewsChina database), track 1,672 / 1,649 mm,
93.7 kWh pack, three motors (front V6s 288 kW / 500 N.m; rear 2 x V8s, 425 kW / 635 N.m each,
27,200 rpm), carbon-ceramic discs 430 x 40 front / 410 x 32 rear, double-wishbone front and
multi-link rear (Xiaomi via CarNewsChina). The shapes are ours: see docs/xray.md.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

from carkit.anatomy.spec import CarSpec, Motor


def spec():
    s = CarSpec(
        name="su7",
        wheelbase=3.000,
        hub_f=(1.558, 0.830, 0.359),
        hub_r=(-1.442, 0.812, 0.358),
        tyre_r=0.359,
        rim_r=0.2667,
        floor_z=0.32,
        under_z=0.15,
        floor_half_w=0.70,
        sill_y=0.80,
        body_len=5.07,
        body_w=1.97,
        kwh=93.7,
        pack_style="qilin",
        drive_style="su7",
        chassis_style="su7",
        susp_style="su7",
        motors=[
            Motor("F", "front", None, 288, 500, 21000, "Front V6s"),
            Motor("RL", "rear", "left", 425, 635, 27200, "Rear left V8s"),
            Motor("RR", "rear", "right", 425, 635, 27200, "Rear right V8s"),
        ],
    )
    return s.derive()
