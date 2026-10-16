"""Denza Z9: photo readings and their conversion to model metres (camera "rear_black" of
z9_ref_match). Lines are written in PIXELS of the black car's rear photograph (c1_0038.jpg, 3840 x 2880)
and turned into (y, z) on the tail's face by rear_yz.

    rear_yz(u, v, x)    (y, z) of the pixel on the plane x; +y is the car's LEFT, the left of the picture
"""
import math

REAR_CAM = dict(loc=(-9.1, 0.0, 0.968), pitch=0.0, f=6483.0)
W, H = 3840, 2880
CU = 1921.0                    # the car's centreline in the picture (the tyres' walls 1068 / 2774)


def rear_yz(u, v, x=-2.58):
    cam = REAR_CAM
    du = (u - CU) / cam["f"]
    dv = -(v - 0.5 * H) / cam["f"]
    t = (x - cam["loc"][0])
    return (-du * t, cam["loc"][2] + dv * t)
