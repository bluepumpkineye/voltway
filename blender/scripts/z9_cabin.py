"""Denza Z9 cabin: the config cabin_tools reads, and the entry points.

Compare against the photographs (cabin alone, seconds, in a background Blender):

    blender -b --factory-startup --python-expr "import sys; \\
        sys.path.append(r'<repo>/blender/scripts'); import z9_cabin as C; C.compare('v1')"

Cameras (car axes +x forward, +y left, +z up; fov_h the horizontal field of view):

    centre    behind the console at the rear seats' head height, looking at the screen (c10_0001-3)
    axis      on the steering wheel's axis, 0.95 m back (c10_0002)
    viewer    the showroom's driver eye (assets.driverEye) at 1280 x 720
    side_r    from the open passenger door (c3_0036)
    door_l    from the open driver's door (c3_0001)
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
    import z9_interior as ZI
    t = ZI.WHEEL_TILT
    n = Vector((-math.cos(t), 0.0, math.sin(t)))
    return {
        "centre": dict(pos=(-0.55, 0.0, 1.12), aim=(0.85, 0.0, 0.98), fov_h=60.0, res=(1000, 750)),
        "axis": dict(pos=tuple(Vector(ZI.WHEEL_C) + n * 0.95), aim=tuple(ZI.WHEEL_C), fov_h=58.0,
                     res=(1000, 750)),
        "viewer": dict(pos=(0.10, 0.36, 1.18), aim=(0.30, 0.33, 1.15), fov_h=96.6, res=(1280, 720)),
        "side_r": dict(pos=(0.60, -1.70, 1.15), aim=(0.30, 0.0, 0.85), fov_h=62.0, res=(1000, 750)),
        "door_l": dict(pos=(0.20, 1.55, 1.20), aim=(0.30, 0.0, 0.80), fov_h=62.0, res=(1000, 750)),
    }



def _zi():
    import z9_interior as m
    return m


def _join_cards():
    import z9_openings as OP
    OP.join_cards()


def _set_open(on):
    """Every door (cards too) and the trunk lid (its liner too) open or shut, for the open-state bake."""
    import z9_openings as OP
    import z9_gate as RG
    for key, d in OP.DOORS.items():
        OP.set_angle(key, d["deg"] if on else 0.0)
    RG.set_hatch(RG.OPEN_DEG if on else 0.0)


CFG = dict(
    slug="denza-z9",
    interior="z9_interior_shell",
    collection="Z9_Interior",
    node="DenzaZ9_Cabin",
    exterior=("Z9_Body", "Z9_Details", "Z9_Wheels", "Z9_Blackout"),
    blackout=("Z9_Shell_Shadow", "Z9_Greenhouse_Black", "Z9_Roof_Rear_Black", "Z9_Cowl_Black"),
    node_blackout="DenzaZ9_Blackout",
    skip_leak=("Greenhouse_Black", "Shell_Shadow", "Roof_Rear_Black", "Cowl_Black", "Ground"),
    hdri=dict(path=os.path.join(_HERE, "..", "textures", "hdri", "shanghai_riverside_4k.hdr"),
              strength=1.0, rotation=153.6, clamp=8.0),
    probe_at=(0.10, 0.0, 1.10),
    rig_fill=0.8,
    gain=1.0,
    # the door cards and the lid's liner swing with their skins; the X-ray tab takes the headliner away
    protected={"screen_main", "int_headliner", "int_door_L", "int_door_R", "int_rdoor_L", "int_rdoor_R",
               "int_tailgate"},
    join_cards=_join_cards,
    set_open=_set_open,
    eyes={"driver": (0.10, 0.36, 1.18), "passenger": (0.10, -0.36, 1.18),
          "rear_left": (-1.00, 0.38, 1.12), "rear_right": (-1.00, -0.38, 1.12),
          "rear_mid": (-1.00, 0.0, 1.12)},
    cameras=cameras,
    # the cluster and the passenger's display carry their own pictures into the GLB (the centre screen is the live HMI)
    displays={"screen_cluster": lambda: _zi().cluster_image(), "screen_passenger": lambda: _zi().passenger_image()},
    # the infotainment's art (cabin_hmi.hmi_art / hmi_cabin)
    build_module="build_z9",
    export_module="export_z9",
    dims=(5.220, 1.990, 1.500),
    hmi_parts=("dash", "screens", "wheel", "seats", "console", "doors", "shell", "closures", "pedals"),
    hmi_shots={
        # the climate page's wide view from behind the front seats, the seat page's high view from the
        # driver's side with the front of the car at the left
        "climate": dict(pos=(-0.45, 0.0, 1.26), aim=(1.00, 0.0, 0.80), lens=17.0, res=(1800, 585),
                        hide=("seat", "headrest", "pillow", "headliner", "pillar", "roof", "qtr_lower",
                              "parcel", "bulkhead", "int_rdoor", "sill", "visor", "rvmirror", "overhead",
                              "quarter", "head_speaker", "rear_")),
        "seats": dict(pos=(-0.45, 0.62, 3.70), aim=(-0.45, 0.0, 0.88), lens=30.0, res=(1360, 800),
                      hide=("headliner", "pillar", "roof", "int_door_l", "int_rdoor_l", "qtr_lower",
                            "parcel", "bulkhead", "sill", "visor", "rvmirror", "overhead", "head_speaker",
                            "roofrail", "tweeter", "quarter")),
    },
    hmi_seat_points={"FL": (-0.09, 0.36, 0.86), "FR": (-0.09, -0.36, 0.86), "RL": (-1.13, 0.38, 0.84),
                     "RR": (-1.13, -0.38, 0.84), "wheel": (0.60, 0.36, 0.93)},
)


def compare(tag="cmp", **kw):
    return CT.compare(CFG, tag, dump=("wheel", "cluster", "screen", "dash", "visor", "pillar"), **kw)


def leakqa(eyes=None, **kw):
    """Build the exterior and the cabin in one scene and fire rays from the viewer's seat eyes: what
    reaches painted exterior without crossing glass is a gap in the trim. Run in a background Blender,
    BEFORE the parts are split for export:

        blender -b --factory-startup --python-expr "import sys; sys.path.append(r'<repo>/blender/scripts'); \
            import z9_cabin as C; C.leakqa()"
    """
    import build_z9
    build_z9.main(reset=True, scene=False)
    import z9_interior_shell as SH
    SH.main(lights=False)
    out = {}
    for name, eye in (eyes or CFG["eyes"]).items():
        print("=====", name)
        out[name] = CT.leaks(CFG, eye, name[:3], **kw)
    print("LEAK SUMMARY", {k: round(v[1], 3) for k, v in out.items()})
    return out


def hmi_art(**kw):
    """public/hmi/denza-z9/car34.webp and car-top.webp (a background Blender, exterior only)."""
    import cabin_hmi
    return cabin_hmi.hmi_art(CFG, **kw)


def hmi_cabin(**kw):
    """public/hmi/denza-z9/cabin-climate|seats-light|dark.webp; prints HMI_SEATS."""
    import cabin_hmi
    return cabin_hmi.hmi_cabin(CFG, **kw)
