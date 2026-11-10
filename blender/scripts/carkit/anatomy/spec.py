"""What the anatomy kit needs to know about a car: a handful of measured dimensions.

Everything is in metres and Blender axes (+X forward, +Y left, +Z up). The two hubs are the
LEFT wheel centres (y > 0); the right side is the mirror. Measure them off the shipped
exterior model (the wheel nodes' origins), so the hardware lines up with the wheels exactly.

A new car is one `CarSpec(...)` call (see su7_anatomy.py): the kit derives the pack, the
frames and the suspension hardpoints from it, so a longer or wider car gets longer, wider parts.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class Motor:
    id: str                      # 'F', 'RL', 'RR'
    axle: str                    # 'front' | 'rear'
    side: Optional[str]          # 'left' | 'right' | None (one motor across the axle)
    kw: float
    nm: float
    rpm: float
    label: str = ""


@dataclass
class CarSpec:
    name: str
    wheelbase: float
    hub_f: Tuple[float, float, float]      # front-left hub centre
    hub_r: Tuple[float, float, float]      # rear-left hub centre
    tyre_r: float
    rim_r: float                           # rim lip radius (21 in = 0.2667)
    floor_z: float                         # underside of the cabin floor
    under_z: float                         # the flat underbody's height above the ground
    floor_half_w: float                    # half-width of the cabin floor between the sills
    sill_y: float                          # centre of the side sill beam
    body_len: float
    body_w: float
    kwh: float
    motors: List[Motor] = field(default_factory=list)
    # derived (filled by derive())
    pack: dict = field(default_factory=dict)

    @property
    def front_x(self):
        return self.hub_f[0]

    @property
    def rear_x(self):
        return self.hub_r[0]

    @classmethod
    def from_dims(cls, name, hub_f, hub_r, tyre_r, body_len, body_w, kwh, motors, rim_r=None, under_z=None, floor_z=None):
        """A spec from what is easy to know about a car: its hubs, tyre, size, pack and motors.

        The underbody's height, the floor's and the sills' places come from the SU7's proportions (an underbody
        0.42 tyre radii off the road, a floor 0.17 m over it, a floor 0.355 of the body's width across) unless
        the car's own are given (measure them off the cabin model, as su7_anatomy.py does).
        """
        uz = tyre_r * 0.42 if under_z is None else under_z
        fz = uz + 0.17 if floor_z is None else floor_z
        return cls(
            name=name, wheelbase=hub_f[0] - hub_r[0], hub_f=hub_f, hub_r=hub_r, tyre_r=tyre_r,
            rim_r=rim_r if rim_r is not None else tyre_r * 0.74, floor_z=fz, under_z=uz,
            floor_half_w=0.355 * body_w, sill_y=0.405 * body_w, body_len=body_len, body_w=body_w, kwh=kwh,
            motors=list(motors),
        ).derive()

    def derive(self):
        """The pack and the frame's stations from the hubs and the floor."""
        p = {}
        p["x0"] = self.rear_x + 0.32            # behind the rear seat, ahead of the rear subframe
        p["x1"] = self.front_x - 0.46           # under the footwell, behind the front subframe
        p["hw"] = self.floor_half_w + 0.03
        p["z0"] = self.under_z + 0.02
        p["z1"] = self.floor_z - 0.01
        p["kwh"] = self.kwh
        self.pack = p
        return self


def hub(spec, corner):
    """World hub centre of a corner ('FL', 'FR', 'RL', 'RR')."""
    x, y, z = spec.hub_f if corner[0] == 'F' else spec.hub_r
    return (x, y if corner[1] == 'L' else -y, z)
