"""Tail probe: is the rear the length the photograph says, and is its skin taut?

Three tests on the built body (no export), the ones that found the 06T's rear problems on 2026-10-28
(docs/3d-pipeline.md, "The rear of a car is judged by measuring"):

    TAIL ROWS  the tail edge of the model through the car's solved side camera against the photograph's, every
               20 mm of height: the model's alpha (refmatch.render_passes) vs photo_tools.car_mask. A row
               whose photo edge is the floor's shadow or a lamp's reflection reads 100+ px off: ignore it, read the
               run of ordinary rows (the 06T's tail was +4..6 cm at every height; the spoiler tip only +2).
    KINKS      rays along -y over x at fixed heights, listing every place the facet normal jumps more than
               --kink degrees between 10 mm steps, with the object hit (a leftover fixed_x pair, a sheared quad,
               a Bevel-mangled edge each show as a spike 10-30 deg; tessellation is 1-3 deg). The tail's own
               corner roll (Tail_Upper, lamp lenses, x < -2.25) legitimately reads 8-19 deg per 10 mm, and
               the quarter window's tip (x -1.52) is a real edge: look for spikes elsewhere.
    SEAM       the normal jump and the plan slope (dy/dx) on each side where one object hands over to another
               along x (default Tail_Upper > Quarter): the cap leaves the flank at the flank's own taper or the
               seam reads as a vertical ridge.

    blender -b --factory-startup --python blender/scripts/porting/rear_probe.py -- a06t
    blender -b --factory-startup --python blender/scripts/porting/rear_probe.py -- a06t --kink 8 --seam A06T_Tail_Upper A06T_Quarter

The car needs build_<car>.main, <car>_ref_match (a camera named "side" and the photo it registers) and a
<car>_cam module with side_uv(x, z, y). Hide-and-render finds what the numbers cannot: render with one object
hidden at a time (Cycles, camera 130 mm on the spot) until the defect goes.
"""
import importlib
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.normpath(os.path.join(HERE, "..")))
import bpy
import numpy as np
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
CAR = ARGS[0] if ARGS else "a06t"


def _opt(name, default, n=1, cast=str):
    if name not in ARGS:
        return default
    i = ARGS.index(name)
    vals = [cast(a) for a in ARGS[i + 1:i + 1 + n]]
    return vals[0] if n == 1 else vals


KINK_DEG = _opt("--kink", 8.0, cast=float)
SEAM = _opt("--seam", ["A06T_Tail_Upper", "A06T_Quarter"] if CAR == "a06t" else [], n=2)
PX_PER_M = _opt("--scale", 660.0, cast=float)      # the side camera's scale on the tail (hub scale x depth ratio)


def tail_rows(RM, CAM, z0=0.40, z1=1.30, step=0.04):
    from carkit.qa import refmatch as R
    import photo_tools as PT
    import fit_tools as FT
    RM.render_passes("side", "probe")
    photo = PT.load(R.CAMERAS["side"][0])
    mask = PT.car_mask(photo, margin=300, tol=0.06, close=3)
    alpha = FT.model_alpha("side", "probe")

    def edge(m, v, centre, gap=4):
        u, miss = centre, 0
        while u < m.shape[1] - 1:
            if m[v, u]:
                miss = 0
            else:
                miss += 1
                if miss > gap:
                    break
            u += 1
        return u - miss
    centre = int(CAM.side_uv(-1.2, 0.8, 0.6)[0])
    print("TAIL ROWS (+ = model further back than the photo)")
    for z in np.arange(z0, z1, step):
        v = int(round(CAM.side_uv(-2.0, float(z), 0.6)[1]))
        up, um = edge(mask, v, centre), edge(alpha, v, centre)
        print("  z %.2f  photo %d  model %d  %+4d px  %+.3f m%s" % (
            z, up, um, um - up, (um - up) / PX_PER_M, "   (bad row?)" if abs(um - up) > 90 else ""))


def roof_cols(RM, CAM, x0=-2.35, x1=1.25, step=0.05, y=0.65):
    """The model's top edge through the side camera against the photograph's, per column: + = model higher.
    The silhouette's top is the roof rail where there is one, so a hump of the roof under the rail reads here
    only if the rail rides on it."""
    from carkit.qa import refmatch as R
    import photo_tools as PT
    import fit_tools as FT
    RM.render_passes("side", "probe")
    photo = PT.load(R.CAMERAS["side"][0])
    mask = PT.car_mask(photo, margin=300, tol=0.06, close=3)
    alpha = FT.model_alpha("side", "probe")

    lum = PT._lum(photo)

    def top(m, u, v0, run=6):
        """first row below v0 that starts a run of `run` set pixels"""
        col = m[v0:, u]
        for i in range(len(col) - run):
            if col[i:i + run].all():
                return v0 + i
        return None

    def top_photo(u, v0, thr=0.045, run=4):
        """the photo's top edge: first row below v0 that leaves the column's own background (the studio's vignette
        fills the top of the photo, so the per-row margin mask does not do)"""
        bg = float(np.median(lum[v0 - 120:v0 - 20, u]))
        col = np.abs(lum[v0:, u] - bg) > thr
        for i in range(len(col) - run):
            if col[i:i + run].all():
                return v0 + i
        return None
    print("ROOF COLUMNS (+ = model higher than the photo)")
    for x in np.arange(x0, x1, step):
        u, v0 = (int(round(c)) for c in CAM.side_uv(float(x), 1.75, y))
        vp, vm = top_photo(u, v0), top(alpha, u, v0)
        if vp is None or vm is None:
            print("  x %+.2f  no edge" % x)
            continue
        zp, zm = CAM.side_xz(u, vp, y)[1], CAM.side_xz(u, vm, y)[1]
        print("  x %+.2f  photo z %.3f  model z %.3f  %+5.1f mm%s" % (
            x, zp, zm, (zm - zp) * 1000, "   (bad col?)" if abs(zm - zp) > 0.12 else ""))


def heights(n=10):
    """the highest objects of the built car (evaluated bbox): the spec height is to the top of the roof rails"""
    dg = bpy.context.evaluated_depsgraph_get()
    rows = []
    for ob in bpy.context.scene.objects:
        if ob.type != 'MESH' or ob.hide_render:
            continue
        ev = ob.evaluated_get(dg)
        zs = [(ob.matrix_world @ Vector(c)).z for c in ev.bound_box]
        rows.append((max(zs), ob.name))
    rows.sort(reverse=True)
    print("HEIGHTS (top of each object, m)")
    for z, name in rows[:n]:
        print("  %.3f  %s" % (z, name))


class Skin:
    def __init__(self):
        self.dg = bpy.context.evaluated_depsgraph_get()
        self.scn = bpy.context.scene

    def cast(self, x, z):
        ok, loc, n, _i, ob, mw = self.scn.ray_cast(self.dg, Vector((x, 1.6, z)), Vector((0, -1, 0)), distance=3.0)
        return (loc, (mw.to_3x3() @ n).normalized(), ob.name) if ok else None


def kinks(skin, x0=-2.34, x1=-1.20):
    print("KINKS (> %.0f deg between 10 mm steps)" % KINK_DEG)
    for z in (0.72, 0.85, 0.95, 1.02, 1.10):
        prev, out, x = None, [], x0
        while x < x1:
            h = skin.cast(x, z)
            if h and prev and h[2] == prev[2]:
                a = math.degrees(prev[1].angle(h[1]))
                if a > KINK_DEG:
                    out.append("x%.2f %.0fdeg %s" % (x, a, h[2]))
            elif h and prev and h[2] != prev[2]:
                out.append("x%.2f [%s > %s]" % (x, prev[2], h[2]))
            prev, x = h, x + 0.01
        print("  z %.2f  " % z + ("  ".join(out) if out else "clean"))


def seam(skin, a_name, b_name, x0=-2.34):
    print("SEAM %s > %s" % (a_name, b_name))
    for z in (0.60, 0.72, 0.85, 0.95, 1.02):
        prev, xt, x = None, None, x0
        while x < x0 + 0.40:
            h = skin.cast(x, z)
            if h and prev and prev[2] == a_name and h[2] == b_name:
                xt = x
                break
            prev, x = (h if h else prev), x + 0.002
        if xt is None:
            print("  z %.2f  no seam" % z)
            continue
        b, a = skin.cast(xt - 0.008, z), skin.cast(xt + 0.008, z)
        c1, c2 = skin.cast(xt - 0.030, z), skin.cast(xt + 0.030, z)
        if not (a and b and c1 and c2):
            print("  z %.2f  miss" % z)
            continue
        sb = (b[0].y - c1[0].y) / (b[0].x - c1[0].x)
        sa = (c2[0].y - a[0].y) / (c2[0].x - a[0].x)
        print("  z %.2f  x %.3f  normal jump %.1f deg   plan slope %.2f | %.2f" % (
            z, xt, math.degrees(b[1].angle(a[1])), sb, sa))


def main():
    build = importlib.import_module("build_" + CAR)
    build.main(scene=False)
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    scn.cycles.device = 'CPU'
    RM = importlib.import_module(CAR + "_ref_match")
    CAM = importlib.import_module(CAR + "_cam")
    heights()
    tail_rows(RM, CAM)
    roof_cols(RM, CAM)
    skin = Skin()
    kinks(skin)
    if len(SEAM) == 2:
        seam(skin, *SEAM)


if __name__ == "__main__":
    main()
