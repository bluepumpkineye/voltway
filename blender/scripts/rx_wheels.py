"""Luxeed RX wheels: 21 in five-blade, machined faces over dark grey, orange
calipers - the blue show car in the Autohome photographs.

The wheel is carkit's "blade_5" preset: five broad blades widening to the
rim and swept round, each face machined bright on its high side and canted
down to a dark flank (collage_autohome, front34_blue). Calipers orange,
rearward.

Sizes (MIIT): 255/45 R21 front, 275/45 R21 rear; track 1710 front, 1720
rear. Loaded radii 0.369 / 0.378 (rx_camsolve).
"""
from carkit.parts import wheels as W

# The rim's visible lip is at r 0.283 - the J flange stands ~17 mm above the
# 21 in bead seat (the front 3/4 camera was solved on the lip at r 0.285);
# built at the bead seat, the rim read a size small with a balloon sidewall.
# The spokes (collage, both sides of the car): slender at a small hub, swept
# ~13 deg to the rim (compare with the REAR wheel in front34_blue: the front
# ones are steered towards the camera there) and widening to ~100 mm, dark, with a machined triangle
# along the leading edge that grows from nothing at the hub.
SPEC = W.preset(
    "blade_5", rim_d=0.566,
    spokes=dict(params=dict(r_hub=0.066, r_rim=0.272, w_hub=0.032, w_rim=0.100,
                            twist=0.22, twist_power=1.0, split=0.50, split_hub=0.08,
                            drop=0.018),
                face_mat="machined"),
    mats=dict(stripe="machined"))


def build_all(collection, surface, lib):
    corners = [
        # tag, axle x, sign, tyre width, rolling radius, disc radius,
        # caliper deg, outer sidewall y (track/2 + tyre width/2)
        ("FL", surface.FRONT_AXLE, 1, 0.255, 0.369, 0.190, 180.0, 0.9825),
        ("FR", surface.FRONT_AXLE, -1, 0.255, 0.369, 0.190, 180.0, 0.9825),
        ("RL", surface.REAR_AXLE, 1, 0.275, 0.378, 0.180, 200.0, 0.9975),
        ("RR", surface.REAR_AXLE, -1, 0.275, 0.378, 0.180, 160.0, 0.9975),
    ]
    return W.build_set(collection, "RX_", lib, SPEC, corners)
