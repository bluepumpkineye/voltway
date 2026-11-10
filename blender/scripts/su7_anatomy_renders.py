"""Stills of the SU7's anatomy parts for the web's part cards: blender/renders/xray/<part id>.png, then
`node scripts/to-webp.mjs <png> public/xray/su7-ultra/<id>.webp 82 --width 640` (scripts/xray-tools/render-cards.mjs does all of them).

Run in a Blender that holds the built anatomy (su7_anatomy.spec() -> carkit.anatomy.build.build). Each shot names the nodes
it shows, the offsets that pull the parts apart for the picture (Blender axes: +x forward, +y left, +z up) and the side it is
seen from. The ids are the `id`s of the parts in src/data/vehicles/xiaomi-su7-ultra.ts.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

OUT = os.path.join(os.path.dirname(_HERE), "renders", "xray")


def _unit(uid, ax=1.0):
    """A drive unit pulled apart along its axis: the casing off one way, the rotor out the other, the reducer beyond."""
    p = "XR_Drive_%s_" % uid
    return {
        p + "Casing": (0, -0.34 * ax, 0), p + "Rotor": (0, 0.26 * ax, 0), p + "Reducer": (0, 0.52 * ax, 0),
        p + "Pinion": (0, 0.52 * ax, 0), p + "Gears": (0, 0.58 * ax, 0), p + "Inverter": (0, 0, 0.3),
    }


def shots():
    cells = {"XR_Battery_Cells_%02d" % i: (0, 0, 0.16) for i in range(1, 13)}
    pack = {"XR_Battery_Plate": (0, 0, 0.07), "XR_Battery_Busbars": (0, 0, 0.21), "XR_Battery_Film": (0, 0, 0.255),
            "XR_Battery_Lid": (0, 0, 0.32), "XR_Battery_PDU": (0.18, 0, 0.02)}
    pack.update(cells)
    open_pack = {k: v for k, v in pack.items() if k not in ("XR_Battery_Lid", "XR_Battery_Film")}
    return {
        "pack": (["XR_Battery"], pack, (1.0, -1.15, 0.8)),
        "cells": (["XR_Battery_Cells_01", "XR_Battery_Cells_02", "XR_Battery_Cells_03", "XR_Battery_Cells_04", "XR_Battery_Plate", "XR_Battery_Tray"],
                  {"XR_Battery_Cells_0%d" % i: (0, 0, 0.07) for i in range(1, 5)}, (0.9, -1.0, 0.7)),
        "pdu": (["XR_Battery_PDU"], {}, (1.0, -0.8, 0.55)),
        "motor-rear": (["XR_Drive_RL"], _unit("RL"), (1.15, -0.75, 0.45)),
        "motor-front": (["XR_Drive_F"], _unit("F"), (1.15, -0.75, 0.45)),
        "rotor": (["XR_Drive_RL_Rotor", "XR_Drive_RL_Stator"], {"XR_Drive_RL_Rotor": (0, 0.3, 0)}, (1.0, -0.9, 0.5)),
        "stator": (["XR_Drive_RL_Rotor", "XR_Drive_RL_Stator"], {"XR_Drive_RL_Rotor": (0, 0.3, 0)}, (-0.5, 1.0, 0.45)),
        "inverter": (["XR_Drive_RL_Inverter"], {}, (1.0, -0.9, 0.6)),
        "reducer": (["XR_Drive_RL_Reducer", "XR_Drive_RL_Pinion", "XR_Drive_RL_Gears"], {"XR_Drive_RL_Reducer": (0, 0.22, 0)}, (-1.0, 1.0, 0.5)),
        "rear-casting": (["XR_Frame_SubR"], {}, (1.0, -1.0, 0.85)),
        "front-subframe": (["XR_Frame_SubF", "XR_Frame_CrashF"], {"XR_Frame_CrashF": (0.3, 0, 0.0)}, (1.0, -1.0, 0.8)),
        "floor": (["XR_Frame_Floor"], {}, (1.0, -1.0, 0.8)),
        "wishbone": (["XR_Susp_FL"], {}, (1.0, 1.35, 0.35)),
        "spring": (["XR_Susp_FL_Spring", "XR_Susp_FL_Damper", "XR_Susp_FL_Rod"], {}, (1.0, 1.2, 0.2)),
        "multilink": (["XR_Susp_RL"], {}, (-1.0, 1.35, 0.35)),
        "rack": (["XR_Steering_Rack", "XR_Susp_FL_TieRod", "XR_Susp_FR_TieRod"], {}, (1.0, -0.9, 0.7)),
    }


def render_all(only=None, res=(900, 600)):
    import importlib

    import carkit
    from carkit.anatomy import render as R
    importlib.reload(R)
    done = []
    for pid, (nodes, off, view) in shots().items():
        if only and pid not in only:
            continue
        R.part(pid, nodes, "%s/%s.png" % (OUT, pid), offsets=off, view=view, res=res)
        done.append(pid)
    return done
