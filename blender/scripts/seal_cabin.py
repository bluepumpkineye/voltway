"""BYD Seal 07 EV cabin: the config cabin_tools reads, and the entry points.

Cameras (car axes +x forward, +y left, +z up; fov_h horizontal FOV):
    centre    behind console at rear head height, looking at screen
    axis      on steering wheel axis, 0.95 m back
    viewer    driver eye (assets.driverEye) at 1280 x 720
    side_r    from open passenger door
    door_l    from open driver door
"""
import math
import os
import sys

from mathutils import Vector

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

import cabin_tools as CT


def cameras():
    import seal_interior as ZI
    t = ZI.WHEEL_TILT
    n = Vector((-math.cos(t), 0.0, math.sin(t)))
    return {
        "centre": dict(pos=(-0.52, 0.0, 1.10), aim=(0.82, 0.0, 0.96), fov_h=60.0, res=(1000, 750)),
        "axis": dict(pos=tuple(Vector(ZI.WHEEL_C) + n * 0.95), aim=tuple(ZI.WHEEL_C), fov_h=58.0,
                     res=(1000, 750)),
        "viewer": dict(pos=(0.08, 0.35, 1.16), aim=(0.28, 0.32, 1.13), fov_h=96.6, res=(1280, 720)),
        "side_r": dict(pos=(0.58, -1.65, 1.12), aim=(0.28, 0.0, 0.83), fov_h=62.0, res=(1000, 750)),
        "door_l": dict(pos=(0.18, 1.50, 1.18), aim=(0.28, 0.0, 0.78), fov_h=62.0, res=(1000, 750)),
    }


def _zi():
    import seal_interior as m
    return m


def _join_cards():
    import seal_openings as OP
    OP.join_cards()


def _set_open(on):
    """Every door (cards too) and the trunk lid (its liner too) open or shut, for the open-state bake."""
    import seal_openings as OP
    import seal_gate as RG
    for key, d in OP.DOORS.items():
        OP.set_angle(key, d["deg"] if on else 0.0)
    RG.set_hatch(RG.OPEN_DEG if on else 0.0)


CFG = dict(
    slug="byd-seal",
    interior="seal_interior_shell",
    collection="Seal_Interior",
    node="BYDSeal_Cabin",
    exterior=("Seal_Body", "Seal_Details", "Seal_Wheels", "Seal_Blackout"),
    blackout=("Seal_Shell_Shadow", "Seal_Greenhouse_Black", "Seal_Roof_Rear_Black", "Seal_Cowl_Black"),
    node_blackout="BYDSeal_Blackout",
    skip_leak=("Greenhouse_Black", "Shell_Shadow", "Roof_Rear_Black", "Cowl_Black", "Ground"),
    hdri=dict(path=os.path.join(_HERE, "..", "textures", "hdri", "shanghai_riverside_4k.hdr"),
              strength=1.0, rotation=153.6, clamp=8.0),
    probe_at=(0.10, 0.0, 1.08),
    rig_fill=0.8,
    gain=1.0,
    protected={"screen_main", "int_headliner", "int_door_L", "int_door_R", "int_rdoor_L", "int_rdoor_R",
               "int_tailgate"},
    join_cards=_join_cards,
    set_open=_set_open,
    eyes={"driver": (0.06, 0.355, 1.12), "passenger": (0.06, -0.355, 1.12),
          "rear_left": (-0.95, 0.43, 1.08), "rear_right": (-0.95, -0.43, 1.08),
          "rear_mid": (-0.95, 0.0, 1.08)},
    cameras=cameras,
    displays={"screen_cluster": lambda: _zi().cluster_image()},
    build_module="build_seal",
    export_module="export_seal",
    dims=(4.800, 1.875, 1.460),
    hmi_parts=("dash", "screens", "wheel", "seats", "console", "doors", "shell", "closures", "pedals"),
    hmi_shots={
        "climate": dict(pos=(-0.40, 0.0, 1.20), aim=(0.90, 0.0, 0.76), lens=17.0, res=(1800, 585),
                        hide=("seat", "headrest", "pillow", "headliner", "pillar", "roof", "qtr_lower",
                              "parcel", "bulkhead", "int_rdoor", "sill", "visor", "rvmirror", "overhead",
                              "quarter", "head_speaker", "rear_")),
        "seats": dict(pos=(-0.40, 0.58, 3.55), aim=(-0.40, 0.0, 0.84), lens=30.0, res=(1360, 800),
                      hide=("headliner", "pillar", "roof", "int_door_l", "int_rdoor_l", "qtr_lower",
                            "parcel", "bulkhead", "sill", "visor", "rvmirror", "overhead", "head_speaker",
                            "roofrail", "tweeter", "quarter")),
    },
    hmi_seat_points={"FL": (0.00, 0.36, 0.82), "FR": (0.00, -0.36, 0.82), "RL": (-1.02, 0.43, 0.80),
                     "RR": (-1.02, -0.43, 0.80), "wheel": (0.50, 0.385, 0.89)},
)


def compare(tag="cmp", **kw):
    return CT.compare(CFG, tag, dump=("wheel", "cluster", "screen", "dash", "visor", "pillar"), **kw)


def leakqa(eyes=None, **kw):
    """Build exterior + cabin and fire rays from eye points to verify light seal."""
    import build_seal
    build_seal.main(reset=True, scene=False)
    import seal_interior_shell as SH
    SH.main(lights=False)
    out = {}
    for name, eye in (eyes or CFG["eyes"]).items():
        print("=====", name)
        out[name] = CT.leaks(CFG, eye, name[:3], **kw)
    print("LEAK SUMMARY", {k: round(v[1], 3) for k, v in out.items()})
    return out


def hmi_art(**kw):
    """public/hmi/byd-seal/car34.webp and car-top.webp."""
    import cabin_hmi
    return cabin_hmi.hmi_art(CFG, **kw)


def hmi_cabin(**kw):
    """public/hmi/byd-seal/cabin-climate|seats-light|dark.webp."""
    import cabin_hmi
    return cabin_hmi.hmi_cabin(CFG, **kw)
