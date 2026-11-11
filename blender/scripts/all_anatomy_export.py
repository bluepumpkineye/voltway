"""Build and export the X-ray anatomy GLBs for all 9 showcase models with OEM-specific hardware.

    blender -b --factory-startup -P blender/scripts/all_anatomy_export.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import su7_anatomy
from carkit.anatomy import build as B
from carkit.anatomy.spec import CarSpec, Motor


SPECS = [
    ("su7-ultra", su7_anatomy.spec()),
    (
        "byd-seal",
        CarSpec.from_dims(
            name="BYDSeal",
            hub_f=(1.520, 0.788, 0.343),
            hub_r=(-1.400, 0.790, 0.343),
            tyre_r=0.343,
            body_len=4.800,
            body_w=1.875,
            kwh=82.56,
            pack_style="blade",
            drive_style="byd_8in1",
            chassis_style="ctb",
            susp_style="disus_c_coil",
            rear_steer=False,
            motors=[
                Motor("F", "front", None, kw=160.0, nm=310.0, rpm=20000.0, label="Front AC induction"),
                Motor("R", "rear", None, kw=230.0, nm=380.0, rpm=23000.0, label="Rear 8-in-1 SiC PM"),
            ],
        ),
    ),
    (
        "denza-z9",
        CarSpec.from_dims(
            name="DenzaZ9",
            hub_f=(1.625, 0.845, 0.362),
            hub_r=(-1.500, 0.845, 0.362),
            tyre_r=0.362,
            body_len=5.220,
            body_w=1.990,
            kwh=100.0,
            pack_style="blade",
            drive_style="byd_e3",
            chassis_style="e3_ctb",
            susp_style="disus_a",
            rear_steer=True,
            motors=[
                Motor("F", "front", None, kw=230.0, nm=430.0, rpm=21000.0, label="e3 front AC induction"),
                Motor("RL", "rear", "left", kw=240.0, nm=360.0, rpm=21000.0, label="e3 rear-left PM"),
                Motor("RR", "rear", "right", kw=240.0, nm=360.0, rpm=21000.0, label="e3 rear-right PM"),
            ],
        ),
    ),
    (
        "luxeed-rx",
        CarSpec.from_dims(
            name="LuxeedRX",
            hub_f=(1.430, 0.855, 0.369),
            hub_r=(-1.570, 0.860, 0.378),
            tyre_r=0.373,
            body_len=5.042,
            body_w=1.986,
            kwh=100.4,
            pack_style="whale_800v",
            drive_style="driveone",
            chassis_style="tuling",
            susp_style="vkp_air",
            rear_steer=False,
            motors=[
                Motor("F", "front", None, kw=160.0, nm=277.0, rpm=22000.0, label="DriveONE front induction"),
                Motor("R", "rear", None, kw=277.0, nm=400.0, rpm=22000.0, label="DriveONE rear SiC PM"),
            ],
        ),
    ),
    (
        "zeekr-7x",
        CarSpec.from_dims(
            name="Zeekr7X",
            hub_f=(1.543, 0.825, 0.365),
            hub_r=(-1.383, 0.827, 0.365),
            tyre_r=0.365,
            body_len=4.825,
            body_w=1.930,
            kwh=103.0,
            pack_style="qilin",
            drive_style="zeekr_sic",
            chassis_style="sea_dome",
            susp_style="vkp_air",
            rear_steer=False,
            motors=[
                Motor("F", "front", None, kw=215.0, nm=315.0, rpm=20000.0, label="Front induction"),
                Motor("R", "rear", None, kw=370.0, nm=500.0, rpm=22000.0, label="Rear 900V SiC PM"),
            ],
        ),
    ),
    (
        "xpeng-g9l",
        CarSpec.from_dims(
            name="XpengG9L",
            hub_f=(1.650, 0.820, 0.377),
            hub_r=(-1.450, 0.823, 0.377),
            tyre_r=0.377,
            body_len=5.250,
            body_w=2.000,
            kwh=110.0,
            pack_style="cib",
            drive_style="sepa",
            chassis_style="cib_megacast",
            susp_style="air_cdc",
            rear_steer=True,
            motors=[
                Motor("F", "front", None, kw=160.0, nm=285.0, rpm=20000.0, label="XPower front induction"),
                Motor("R", "rear", None, kw=270.0, nm=410.0, rpm=21000.0, label="XPower rear SiC PM"),
            ],
        ),
    ),
    (
        "avatr-06t",
        CarSpec.from_dims(
            name="Avatr06T",
            hub_f=(1.570, 0.831, 0.369),
            hub_r=(-1.370, 0.833, 0.369),
            tyre_r=0.369,
            body_len=4.855,
            body_w=1.960,
            kwh=82.16,
            pack_style="whale_800v",
            drive_style="driveone",
            chassis_style="chn",
            susp_style="vkp_air",
            rear_steer=False,
            motors=[
                Motor("F", "front", None, kw=190.0, nm=280.0, rpm=21000.0, label="DriveONE front induction"),
                Motor("R", "rear", None, kw=250.0, nm=365.0, rpm=22000.0, label="DriveONE rear SiC PM"),
            ],
        ),
    ),
    (
        "nio-es8",
        CarSpec.from_dims(
            name="NioES8",
            hub_f=(1.565, 0.860, 0.385),
            hub_r=(-1.565, 0.867, 0.385),
            tyre_r=0.385,
            body_len=5.280,
            body_w=2.010,
            kwh=100.0,
            pack_style="swap",
            drive_style="xpt",
            chassis_style="nt2_swap",
            susp_style="air_cdc",
            rear_steer=False,
            motors=[
                Motor("F", "front", None, kw=180.0, nm=280.0, rpm=18000.0, label="XPT front 180 kW PM"),
                Motor("R", "rear", None, kw=340.0, nm=420.0, rpm=20000.0, label="XPT rear 340 kW SiC"),
            ],
        ),
    ),
    (
        "voyah-passion-s",
        CarSpec.from_dims(
            name="VoyahPassionS",
            hub_f=(1.525, 0.860, 0.375),
            hub_r=(-1.475, 0.862, 0.375),
            tyre_r=0.375,
            body_len=5.125,
            body_w=1.985,
            kwh=100.0,
            pack_style="mica",
            drive_style="essa",
            chassis_style="essa",
            susp_style="air_cdc",
            rear_steer=False,
            motors=[
                Motor("F", "front", None, kw=220.0, nm=340.0, rpm=20000.0, label="ESSA front 220 kW"),
                Motor("R", "rear", None, kw=290.0, nm=430.0, rpm=21000.0, label="ESSA rear 290 kW SiC"),
            ],
        ),
    ),
]


def main():
    out_dir = os.path.join(ROOT, "public", "models")
    os.makedirs(out_dir, exist_ok=True)
    for slug, spec in SPECS:
        print("\n=== Building X-ray anatomy for %s (%s) ===" % (slug, spec.name))
        B.build(spec)
        out = os.path.join(out_dir, "%s-xray.glb" % slug)
        B.export_glb(out)
        print("=== Exported %s ===" % out)


if __name__ == "__main__":
    main()
