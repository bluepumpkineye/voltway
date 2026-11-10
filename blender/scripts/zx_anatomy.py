"""The Zeekr 7X's anatomy, built from its measured hubs: a second car on carkit.anatomy, to show the parts re-scale.

Hubs measured off public/models/zeekr-7x.glb with scripts/xray-tools/hubs.mjs (2026-11-02). One motor on each axle (the 7X 4WD),
a 103 kWh pack. The motor figures here are placeholders for the geometry (the kit sizes a motor from its torque): the 7X is not yet
wired into the web viewer, which needs its own labels and sources.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

from carkit.anatomy.spec import CarSpec, Motor


def spec():
    return CarSpec.from_dims(
        "zx7",
        hub_f=(1.543, 0.825, 0.365), hub_r=(-1.383, 0.827, 0.365),
        tyre_r=0.365, body_len=4.825, body_w=1.93, kwh=103,
        motors=[Motor("F", "front", None, 200, 360, 16000, "Front"), Motor("R", "rear", None, 310, 440, 16000, "Rear")],
    )
