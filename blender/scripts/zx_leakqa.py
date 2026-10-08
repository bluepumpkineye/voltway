"""Zeekr 7X cabin leak QA from the eyes the web viewer looks out of.

The showroom's Interior tab turns the camera about a seat's eye (assets.driverEye, 64 deg
vertical field) and the viewer draws the panes translucent and hides the *_blackout nodes,
so a ray from an eye that reaches painted exterior WITHOUT first crossing glass is a gap in
the cabin's trim (carkit.qa.leaks). Run in a scene that holds the build and the cabin:

    import zx_leakqa as LQ
    LQ.run(LQ.EYES["driver"], "drv")           # 8 yaws x 3 pitches at the driver's eye
    LQ.all_eyes()

The camera's 16 mm lens on the 36 mm sensor is the viewer's 64 deg vertical field at 16:9
(96 deg across).
"""
import math

from mathutils import Vector

from carkit.qa import leaks as LK

EYES = {
    "driver": (0.16, 0.37, 1.22),
    "passenger": (0.16, -0.37, 1.22),
    "rear_left": (-0.85, 0.35, 1.20),
    "rear_right": (-0.85, -0.35, 1.20),
    "rear_mid": (-0.85, 0.0, 1.20),
}
EXTERIOR = ("ZX_Body", "ZX_Details", "ZX_Wheels", "ZX_Blackout", "ZX_BonnetGrp", "ZX_GateGrp",
            "ZX_GreenhouseGrp", "ZX_DoorGrp_FL", "ZX_DoorGrp_FR", "ZX_DoorGrp_RL", "ZX_DoorGrp_RR",
            "ZX_DoorFrameGrp_FL", "ZX_DoorFrameGrp_FR", "ZX_DoorFrameGrp_RL", "ZX_DoorFrameGrp_RR")
SKIP = ("Greenhouse_Black", "Shell_Shadow", "Roof_Rear_Black", "Ground")


def aim(eye, yaw, pitch):
    """A point 1 m from the eye: yaw 0 forward (+x), +90 left (+y); pitch up positive."""
    y, p = math.radians(yaw), math.radians(pitch)
    d = Vector((math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), math.sin(p)))
    return tuple(Vector(eye) + d)


def run(eye, tag, yaws=(0, 45, 90, 135, 180, -135, -90, -45), pitches=(0, 45, -40), lens=16.0,
        res=(192, 108), top=25, interior="ZX_Interior", exterior=EXTERIOR, skip=SKIP):
    specs = {}
    for yw in yaws:
        for pt in pitches:
            specs["%s_y%d_p%d" % (tag, yw, pt)] = (eye, aim(eye, yw, pt), lens)
    cams = LK.cameras(specs)
    rep = LK.find(cams, interior=interior, exterior=exterior, see_through=("Glass",), skip=skip,
                  res=res)
    LK.print_report(rep, top=top)
    return rep


def all_eyes(**kw):
    out = {}
    for name, eye in EYES.items():
        print("=====", name)
        out[name] = run(eye, name[:3], **kw)
    return out


def view(eye, yaw, pitch, tag, lens=16.0, res=(1280, 720), samples=4):
    """A flat render of what the viewer would show from `eye`: the cabin grey, painted
    exterior magenta (a gap), panes and the black underlay left out. Returns the PNG path
    (blender/renders/lookdev)."""
    import zx_lookdev as LD
    return LD.view(eye, aim(eye, yaw, pitch), lens, "leak_" + tag, res=res, samples=samples,
                   mode="ids", clip=0.02,
                   colors={"int_": (0.55, 0.55, 0.55), "screen_": (0.15, 0.15, 0.2),
                           "ZX_": (1.0, 0.0, 1.0)},
                   skip=("ZX_Glass", "ZX_Greenhouse_Black", "ZX_Shell", "ZX_Roof_Rear_Black",
                         "ZX_Underbody", "Ground"))


def worst(rep):
    W, H = rep["res"]
    return max(rep["per_camera"].values()) * 100.0 / (W * H)
