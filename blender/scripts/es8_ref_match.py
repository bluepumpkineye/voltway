"""Nio ES8 reference cameras, for carkit.qa.refmatch.

    import es8_ref_match as RM
    RM.ray("front", u, v)

References (blender/reference/nio-es8/official, the maker's press photographs; local only):
    ext_front.jpg  2560 x 1280, the black car square-on from the front   (camera "front")

"front" is a long lens (f 7805 px, about 110 mm in 35 mm terms) 16 m from the nose, 1.61 m up and tipped 2.4 degrees
down, on the car's centre line. The photograph does not fix a long lens' distance, so it was solved from what it does
fix: the horizontal scale (the body's widest section, 0.996 m a side, against the face panel) and the nose's own
landmarks at the centre line (emblem z 0.90, face-panel edges z 0.715 / 0.836, show plate z 0.415 / 0.555, chin
blade z 0.29), which this camera puts within 10 px (2 cm) of where the model has them, and the windscreen's base
against the nose (which gives the height). Features at the nose's depth, which is where the lamps are, do not depend
on the lens' distance. Checked by projecting the model's vertices onto the photograph (docs/3d-pipeline.md).

Model coordinates: +X forward, +Y to the left, Z up, length centred on x = 0. The photograph's left half is the car's
RIGHT (y < 0).
"""
import math

from mathutils import Vector

from carkit.qa.refmatch import *                 # noqa: F401,F403
from carkit.qa import refmatch as _R
import es8_lampdata as _LD

D, ZC, PITCH_DEG, F_PX, X_NOSE = 16.0, 1.61, 2.4, 7805.0, 2.4

_th = math.radians(PITCH_DEG)
_eul = Vector((-math.cos(_th), 0.0, -math.sin(_th))).to_track_quat('-Z', 'Y').to_euler('XYZ')
FRONT_CAM = dict(loc=(X_NOSE + D, 0.0, ZC), rot=tuple(math.degrees(a) for a in _eul), f=F_PX)

_R.register("front", "nio-es8/official/ext_front.jpg", _LD.SIZE, FRONT_CAM["loc"], FRONT_CAM["rot"], FRONT_CAM["f"])
