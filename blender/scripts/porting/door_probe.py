"""Doors-open probe: does anything stand in a doorway when the doors swing?

A door's own parts (skin, glass, handle, mirror, trim strips) are one glTF node that swings about its hinge.
Anything LEFT on the body inside the door's outline stays behind: a long trim strip (the belt chrome / gloss
belt trim, a crease line) mirrors the studio as a white bar across the open doorway; a piece of the black
greenhouse underlay or the shadow hull stands as a black wedge. This is the family of bugs reported on the RX
(silver bar), the 7X (black wedge, three times), the Z9 (white line, 2026-10-21) and the Seal (belt trim,
2026-10-22): see docs/3d-pipeline.md, "Nothing may span a doorway".

The test is geometric, not visual. It builds the exterior, runs the car's own prepare_exterior() (which splits
the doors off), opens every door, and then looks at every vertex of every object that is NOT a door part, against
each door's skin outline (the custom property "outline" on the door node: closed position, side elevation),
for |y| > 0.45:
    STRIP  a thin run of vertices along 70% or more of the door's width, inside the outline or within 8 mm
           above its top edge: a belt/crease/chrome strip that was never split into the door
    SHEET  20 or more vertices more than 3 cm inside the outline: a leftover piece of the greenhouse underlay
           or the shadow hull
It prints one STANDING line per offending object and writes three Workbench stills (side, front 3/4, rear 3/4)
with the offenders in red to blender/renders/door_probe_<car>_*.png.

    blender -b --factory-startup --python blender/scripts/porting/door_probe.py -- seal
    blender -b --factory-startup --python blender/scripts/porting/door_probe.py -- z9 --skip split_belt

--skip NAME switches a function of <car>_openings off (to prove the probe still catches the bug it was written
for: `-- seal --skip split_belt` must report Seal_Window_Belt_Trim).  The car needs build_<car>.main,
export_<car>.prepare_exterior / open_all and an openings module that sets door["outline"] (all of them do).
Exit status: the line "DOOR PROBE: n object(s) standing in a doorway" ends the run; n must be 0.
"""
import importlib
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.normpath(os.path.join(HERE, "..")))
import bpy
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
CAR = ARGS[0] if ARGS else "seal"
SKIP = ARGS[ARGS.index("--skip") + 1] if "--skip" in ARGS else None
Y_MIN = 0.45          # the doorway's plane is at the skin, well outside the centre
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "renders"))

# parts that legitimately live in a doorway: the door nodes and their frames/rings/beads, and the wheels
# (the rocker/sill is lower body that the door skin overlaps in side elevation)
EXEMPT = ("Door", "Wheel", "Tyre", "Rim", "Caliper", "Disc", "Brake", "Rocker", "Sill")


def _pip(x, z, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        ax, az = poly[i - 1]
        bx, bz = poly[i]
        if (az > z) != (bz > z) and x < (bx - ax) * (z - az) / (bz - az) + ax:
            inside = not inside
    return inside


def _edge_dist(x, z, poly):
    best = 1e9
    for i in range(len(poly)):
        ax, az = poly[i - 1]
        bx, bz = poly[i]
        dx, dz = bx - ax, bz - az
        l2 = dx * dx + dz * dz
        t = 0.0 if l2 < 1e-12 else max(0.0, min(1.0, ((x - ax) * dx + (z - az) * dz) / l2))
        best = min(best, math.hypot(x - (ax + t * dx), z - (az + t * dz)))
    return best


def main():
    build = importlib.import_module("build_" + CAR)
    build.main(reset=True, scene=False)
    export = importlib.import_module("export_" + CAR)
    if SKIP:
        openings = importlib.import_module(CAR + "_openings")
        setattr(openings, SKIP, lambda *a, **k: None)
        print("SKIPPING %s_openings.%s" % (CAR, SKIP))
    export.prepare_exterior()
    export.open_all(True)
    bpy.context.view_layer.update()

    doors = {}
    for o in bpy.data.objects:
        flat = o.get("outline")
        if flat is not None and o.type == 'MESH':
            doors[o.name] = [(flat[i], flat[i + 1]) for i in range(0, len(flat), 2)]
    print("doors with an outline:", sorted(doors))
    if not doors:
        raise SystemExit("no door node carries an 'outline' property: split_doors() must set it")

    # (1) a STRIP: a thin run of vertices along the door's width, in the outline or in the 8 mm above its top
    #     edge (a belt strip is centred on the belt line, half of it above the skin). Panels that merely touch the
    #     outline's edges (rocker, quarter, fender) have no such run.
    # (2) a SHEET: 20 or more vertices well inside the outline (3 cm from its edge): a leftover piece of the
    #     greenhouse underlay or the shadow hull
    offenders = {}
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.visible_get() or o.name in doors or any(s in o.name for s in EXEMPT):
            continue
        allv = [o.matrix_world @ v.co for v in o.data.vertices]
        verts = [p for p in allv if abs(p.y) >= Y_MIN]
        # a strip is a thin object: a big sheet's edge along the belt (the underlay's cut) is not one
        thin = bool(allv) and (max(p.z for p in allv) - min(p.z for p in allv)) < 0.45
        for dn, poly in doors.items():
            xs = [q[0] for q in poly]
            zs = [q[1] for q in poly]
            x0, x1 = min(xs), max(xs)
            z_mid = 0.5 * (min(zs) + max(zs))
            run = [p for p in verts if thin and p.z >= z_mid and x0 <= p.x <= x1
                   and (_pip(p.x, p.z, poly) or _pip(p.x, p.z - 0.008, poly))]
            deep = [p for p in verts if _pip(p.x, p.z, poly) and _edge_dist(p.x, p.z, poly) > 0.03]
            kind = None
            if len(run) >= 6:
                cov = (max(p.x for p in run) - min(p.x for p in run)) / (x1 - x0)
                dz = max(p.z for p in run) - min(p.z for p in run)
                if cov >= 0.70 and dz < 0.08:
                    kind, pts = "STRIP", run
            if kind is None and len(deep) >= 20:
                kind, pts = "SHEET", deep
            if kind:
                prev = offenders.get(o.name)
                where = (prev[1] if prev else set()) | {dn.rsplit("_", 1)[-1]}
                offenders[o.name] = (kind, where, min(p.x for p in pts), max(p.x for p in pts),
                                     min(p.z for p in pts), max(p.z for p in pts))
    for name, (kind, where, x0, x1, z0, z1) in sorted(offenders.items()):
        print("STANDING %-6s %-34s doorway %s  x %.2f..%.2f  z %.2f..%.2f" % (
            kind, name, "/".join(sorted(where)), x0, x1, z0, z1))
    print("DOOR PROBE: %d object(s) standing in a doorway" % len(offenders))
    render(offenders)


def render(offenders):
    os.makedirs(OUT, exist_ok=True)
    scn = bpy.context.scene
    scn.render.engine = 'BLENDER_WORKBENCH'
    sh = scn.display.shading
    sh.light = 'STUDIO'
    sh.color_type = 'OBJECT'
    scn.render.resolution_x, scn.render.resolution_y = 1500, 760
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        if o.name in offenders:
            o.color = (1.0, 0.0, 0.0, 1.0)
        elif "Door" in o.name:
            o.color = (0.55, 0.65, 0.85, 1.0)
        elif "Glass" in o.name:
            o.hide_render = True
        else:
            o.color = (0.75, 0.75, 0.78, 1.0)
    for name, p, t, fov in (("side", (0.0, 5.5, 1.0), (-0.1, 0.0, 0.95), 28.0),
                            ("f34", (4.0, 3.5, 1.4), (0.0, 0.6, 0.85), 30.0),
                            ("r34", (-4.0, 3.5, 1.4), (-0.6, 0.6, 0.85), 30.0)):
        cam = bpy.data.cameras.new("probe")
        cam.angle = math.radians(fov)
        co = bpy.data.objects.new("probe", cam)
        scn.collection.objects.link(co)
        co.location = Vector(p)
        co.rotation_euler = (Vector(t) - Vector(p)).to_track_quat('-Z', 'Y').to_euler()
        scn.camera = co
        scn.render.filepath = os.path.join(OUT, "door_probe_%s%s_%s.png" % (CAR, "_skip" if SKIP else "", name))
        bpy.ops.render.render(write_still=True)
        print("WROTE", scn.render.filepath)


main()
