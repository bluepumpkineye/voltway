"""Screenshot the WEB viewer through a matched camera, to judge the real-time
result against the reference photo and the Cycles render from one viewpoint.

The app serves the viewer alone, full window, with a locked camera at
/capture/view/<slug>?mode=&pos=&target=&fov= (src/app/capture/view). Headless
Edge/Chrome screenshots it (software WebGL: slow, ~20 s, but deterministic):

    from carkit.qa import web_capture as W
    path = W.capture_camera("xiaomi-su7-ultra", "cabin_front")   # refmatch camera
    W.triptych("cabin_front", path, cycles_render, out)           # photo | web | Cycles
    W.patches(path, {"dash face": (x0, y0, x1, y1), ...})        # mean sRGB per box

Needs the dev server (npm run dev). Coordinates: Blender (x fwd, y left, z up)
map to glTF/three (x, z, -y).
"""
import math
import os
import subprocess
from urllib.parse import urlencode

import numpy as np
from mathutils import Euler, Vector

from . import refmatch as R
from .hmi_capture import BROWSERS

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))), "renders", "web")


def to_three(v):
    return (v[0], v[2], -v[1])


def shot(loc, rot_deg, f_px, size, dist=0.2):
    """A Blender camera (location, XYZ euler degrees, focal in px) as the
    viewer's (pos, target, vertical fov). The target sits `dist` ahead: the
    viewer's orbit limits clamp the pivot distance."""
    e = Euler([math.radians(a) for a in rot_deg], 'XYZ')
    fwd = e.to_matrix() @ Vector((0.0, 0.0, -1.0))
    tgt = Vector(loc) + fwd * dist
    vfov = math.degrees(2.0 * math.atan(size[1] * 0.5 / f_px))
    return to_three(loc), to_three(tgt), vfov


def capture(slug, pos, target, fov, size=(1280, 960), mode="interior", out=None,
            base="http://localhost:3000", wait_ms=30000):
    exe = next((b for b in BROWSERS if os.path.exists(b)), None)
    if exe is None:
        raise RuntimeError("no Edge/Chrome found for headless capture")
    os.makedirs(OUT_DIR, exist_ok=True)
    out = out or os.path.join(OUT_DIR, "%s_%s.png" % (slug, mode))
    if os.path.exists(out):
        os.remove(out)
    q = urlencode({"mode": mode, "pos": "%.4f,%.4f,%.4f" % tuple(pos),
                   "target": "%.4f,%.4f,%.4f" % tuple(target), "fov": "%.3f" % fov})
    profile = os.path.join(os.environ.get("TEMP", "."), "carkit_view_profile")
    cmd = [exe, "--headless=new", "--hide-scrollbars", "--no-first-run",
           "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
           "--user-data-dir=" + profile, "--window-size=%d,%d" % size,
           "--virtual-time-budget=%d" % wait_ms, "--screenshot=" + out,
           "%s/capture/view/%s?%s" % (base, slug, q)]
    subprocess.run(cmd, capture_output=True, timeout=240)
    if not os.path.exists(out):
        raise RuntimeError("capture failed: " + " ".join(cmd))
    return out


def capture_camera(slug, camera, mode="interior", out=None):
    """Through a camera solved in carkit.qa.refmatch (register())."""
    ref, size, loc, rot, f = R.CAMERAS[camera]
    pos, tgt, fov = shot(loc, rot, f, size)
    out = out or os.path.join(OUT_DIR, "%s_%s.png" % (slug, camera))
    return capture(slug, pos, tgt, fov, size=size, mode=mode, out=out)


def triptych(camera, web_png, render_png=None, out=None):
    """Photo | web capture [| Cycles render], side by side."""
    ref = R.load(R.CAMERAS[camera][0])
    tiles = [ref, R.load(web_png)]
    if render_png:
        tiles.append(R.load(render_png))
    h = min(t.shape[0] for t in tiles)
    row = np.concatenate([t[:h] for t in tiles], axis=1)
    out = out or web_png.replace(".png", "_triptych.png")
    R.save(row, out)
    return out


def patches(png, boxes):
    """Mean sRGB 0-255 inside each (x0, y0, x1, y1) box, image y down."""
    a = R.load(png)
    return {k: tuple(int(round(c * 255)) for c in a[y0:y1, x0:x1, :3].reshape(-1, 3).mean(0))
            for k, (x0, y0, x1, y1) in boxes.items()}
