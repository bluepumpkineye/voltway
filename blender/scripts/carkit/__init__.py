"""carkit - the parametric car kit, extracted from the Xiaomi SU7 Ultra build.

Every car in the showcase is built the same way: a master surface from profile
curves, wrapped nose and tail caps, panels cut from that surface with real shut
lines, then parts placed onto it, then lookdev, QA against the reference
photographs, and a glTF export. This package is everything in that pipeline that
does not depend on which car it is.

    geom        curves, splines, outlines, small vector maths (no bpy)
    mesh        mesh construction and modifier helpers
    cut         cutting prisms and exact booleans
    place       putting parts on a body: BVH ray casts, surface frames
    body/       the body model: loft (flank), caps (nose, tail), panels,
                fascia (bumper kit), morph (start a new car from a donor)
    parts/      the catalogue: wheels, lamps, aero, grilles, fittings
    materials   material library and paint presets
    textures    procedural maps baked to real pixels (carbon weave)
    scene       studio rig, camera book, Cycles and colour management
    qa/         camera-matched overlays, zebra renders, build checks,
                build fingerprints
    export      merge for draw calls, glTF export
    build       collections, UVs, the standard build checks
    preview     the catalogue contact sheet

The SU7 modules (su7_*.py) are the first car built on it: they hold only that
car's data - hardpoints, curves, panel layout - and call into carkit for the
rest. See README.md in this folder for the catalogue and
docs/3d-pipeline.md at the repo root for the workflow.
"""
import sys

VERSION = "1.0.0"


def reload():
    """Drop every carkit module from sys.modules so the next import is fresh.

    Blender keeps modules loaded between script runs; without this an edit to
    carkit is silently ignored until Blender restarts.
    """
    for name in [m for m in sys.modules if m == "carkit" or m.startswith("carkit.")]:
        sys.modules.pop(name, None)
