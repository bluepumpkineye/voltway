"""The lookdev scene - moved to carkit.scene; kept so old imports keep working.

    import scene_setup as SC
    SC.main()                       # rig, floor, camera book, Cycles, colour
    SC.render("hero_f34", "x.png")  # -> blender/renders/x.png
"""
from carkit.scene import *                      # noqa: F401,F403
from carkit.scene import aim as _aim            # noqa: F401  (old private name)
