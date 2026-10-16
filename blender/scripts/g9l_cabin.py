"""XPeng G9L cabin: the config cabin_tools reads, and the entry points (see z9_cabin.py).

    blender -b --factory-startup --python-expr "import sys; \\
        sys.path.append(r'<repo>/blender/scripts'); import g9l_cabin as C; C.compare('v1')"

Cameras (car axes +x forward, +y left, +z up): centre (behind the console, c10_0002/3), axis (the wheel's
axis, c10_0008), viewer (the showroom's driver eye), side_l (from the open driver's door, c3_0001),
rear (the rear bench from the cargo bay, c3_0020).
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
    import g9l_interior as ZI
    t = ZI.WHEEL_TILT
    n = Vector((-math.cos(t), 0.0, math.sin(t)))
    return {
        "centre": dict(pos=(-0.30, 0.0, 1.30), aim=(1.10, 0.0, 1.05), fov_h=60.0, res=(1000, 750)),
        "axis": dict(pos=tuple(Vector(ZI.WHEEL_C) + n * 0.95), aim=tuple(ZI.WHEEL_C), fov_h=58.0,
                     res=(1000, 750)),
        "viewer": dict(pos=(0.18, 0.40, 1.28), aim=(0.40, 0.37, 1.24), fov_h=96.6, res=(1280, 720)),
        "side_l": dict(pos=(0.30, 1.70, 1.30), aim=(0.30, 0.0, 0.85), fov_h=62.0, res=(1000, 750)),
        "rear": dict(pos=(-2.20, 0.0, 1.10), aim=(-0.90, 0.0, 0.85), fov_h=70.0, res=(1000, 750)),
    }



def _zi():
    import g9l_interior as m
    return m

CFG = dict(
    slug="xpeng-g9l",
    interior="g9l_interior_shell",
    collection="G9L_Interior",
    node="XpengG9L_Cabin",
    exterior=("G9L_Body", "G9L_Details", "G9L_Wheels", "G9L_Blackout"),
    blackout=("G9L_Shell_Shadow", "G9L_Greenhouse_Black", "G9L_Roof_Rear_Black", "G9L_Cowl_Black"),
    node_blackout="XpengG9L_Blackout",
    skip_leak=("Greenhouse_Black", "Shell_Shadow", "Roof_Rear_Black", "Cowl_Black", "Ground"),
    hdri=dict(path=os.path.join(_HERE, "..", "textures", "hdri", "shanghai_riverside_4k.hdr"),
              strength=1.0, rotation=153.6, clamp=8.0),
    probe_at=(0.20, 0.0, 1.25),
    rig_fill=0.8,
    gain=1.0,
    protected={"screen_main", "int_headliner"},
    eyes={"driver": (0.18, 0.40, 1.28), "passenger": (0.18, -0.40, 1.28),
          "rear_left": (-1.00, 0.385, 1.32), "rear_right": (-1.00, -0.385, 1.32),
          "rear_mid": (-1.00, 0.0, 1.32)},
    cameras=cameras,
    # the cluster strip carries its own picture into the GLB (the centre screen is the live HMI)
    displays={"screen_cluster": lambda: _zi().cluster_image()},
    # the infotainment's art (cabin_hmi.hmi_art / hmi_cabin)
    build_module="build_g9l",
    export_module="export_g9l",
    dims=(5.120, 1.999, 1.782),
    hmi_parts=("dash", "screens", "wheel", "seats", "console", "doors", "shell", "closures", "pedals"),
    hmi_shots={
        # the climate page's wide view from behind the front seats, the seat page's high view from the
        # driver's side with the front of the car at the left
        "climate": dict(pos=(-0.35, 0.0, 1.40), aim=(1.10, 0.0, 0.92), lens=17.0, res=(1800, 585),
                        hide=("seat", "headrest", "pillow", "headliner", "pillar", "roof", "qtr_lower",
                              "parcel", "bulkhead", "int_rdoor", "sill", "visor", "rvmirror", "overhead",
                              "quarter", "head_speaker", "rear_", "cargo")),
        "seats": dict(pos=(-0.45, 0.62, 3.90), aim=(-0.45, 0.0, 0.95), lens=30.0, res=(1360, 800),
                      hide=("headliner", "pillar", "roof", "int_door_l", "int_rdoor_l", "qtr_lower",
                            "parcel", "bulkhead", "sill", "visor", "rvmirror", "overhead", "head_speaker",
                            "roofrail", "tweeter", "quarter", "cargo")),
    },
    hmi_seat_points={"FL": (0.03, 0.375, 1.03), "FR": (0.03, -0.375, 1.03), "RL": (-1.13, 0.385, 1.03),
                     "RR": (-1.13, -0.385, 1.03), "wheel": (0.87, 0.375, 1.04)},
)


def compare(tag="cmp", **kw):
    return CT.compare(CFG, tag, dump=("wheel", "cluster", "screen", "dash", "visor", "pillar"), **kw)


def leakqa(eyes=None, **kw):
    """Build the exterior and the cabin in one scene and fire rays from the viewer's seat eyes (see
    z9_cabin.leakqa)."""
    import build_g9l
    build_g9l.main(reset=True, scene=False)
    import g9l_interior_shell as SH
    SH.main(lights=False)
    out = {}
    for name, eye in (eyes or CFG["eyes"]).items():
        print("=====", name)
        out[name] = CT.leaks(CFG, eye, name[:3], **kw)
    print("LEAK SUMMARY", {k: round(v[1], 3) for k, v in out.items()})
    return out


def hmi_art(**kw):
    """public/hmi/xpeng-g9l/car34.webp and car-top.webp (a background Blender, exterior only)."""
    import cabin_hmi
    return cabin_hmi.hmi_art(CFG, **kw)


def hmi_cabin(**kw):
    """public/hmi/xpeng-g9l/cabin-climate|seats-light|dark.webp; prints HMI_SEATS."""
    import cabin_hmi
    return cabin_hmi.hmi_cabin(CFG, **kw)
