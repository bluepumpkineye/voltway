"""Material library for the Avatr 06T: carkit's library in the 06T's finishes.

The Autohome studio turnaround car (c1_0001..c1_0012.jpg) is finished in
Misty Purple (云紫, Yunzi): a sophisticated pearl lavender-violet metallic
with a warm lilac sheen under an 8-layer clearcoat. Official hero renders also
feature Solar Bronze (鎏棕) and Skylight Silk (晴蓝).

Wheels: 20-inch 5-twin-spoke machined face over gloss black pockets, with
high-performance dark grey / silver multi-piston brake calipers.
"""
from carkit import materials as _M
from carkit.materials import export_safe      # noqa: F401  (re-exported)

LIGHTS_ON = False
TAIL_LIGHTS = 1.35

# Misty Purple (云紫): pearl lavender-violet metallic with warm lilac sheen
A06T_PURPLE = dict(
    name="M_Paint_A06T_MistyPurple",
    base=(0.235, 0.195, 0.295),
    roughness=0.25,
    specular=0.24,
    coat_rough=0.022,
    peel=0.010,
    flake=dict(scale=2800.0, bump=0.032, metal_max=0.16),
)
SHEEN = dict(weight=0.25, tint=(0.82, 0.72, 0.96), roughness=0.30)

_M.CALIPERS.setdefault("silver_grey", dict(base=(0.28, 0.29, 0.31), metallic=0.80,
                                           roughness=0.24, coat=1.0, coat_rough=0.05))
_M.RIMS.setdefault("dark_grey", dict(base=(0.035, 0.036, 0.040), metallic=0.0,
                                     roughness=0.28, coat=1.0, coat_rough=0.05))


def _sheen(m):
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for key, val in (("Sheen Weight", SHEEN["weight"]),
                     ("Sheen Tint", SHEEN["tint"] + (1.0,)),
                     ("Sheen Roughness", SHEEN["roughness"])):
        if key in b.inputs:
            b.inputs[key].default_value = val
    return m


def build_library():
    lib = _M.build_library(paint=A06T_PURPLE, rim="dark_grey", caliper="silver_grey",
                           lights_on=LIGHTS_ON, tail_lights=TAIL_LIGHTS)
    _sheen(lib["paint"])

    # F-type headlamp crystal lens over dark matrix projector housing
    m, nt, b = _M.mat("M_Lamp_Clear")
    _M.set_inputs(b, base=(0.065, 0.068, 0.075), metallic=0.50, roughness=0.22,
                  coat=1.0, coat_rough=0.02, ior=1.52)
    lib["lamp_clear"] = m

    # Star-ring taillamp lens: deep wine-red smoked acrylic over dual LED blades
    m, nt, b = _M.mat("M_Lamp_RedLens")
    _M.set_inputs(b, base=(0.030, 0.003, 0.004), metallic=0.0, roughness=0.06,
                  coat=1.0, coat_rough=0.02, ior=1.52, specular=0.5)
    lib["lamp_red_lens"] = m

    # Diffuser satin gunmetal aero insert
    m, nt, b = _M.mat("M_Pod_Grey")
    _M.set_inputs(b, base=(0.075, 0.078, 0.084), metallic=0.35, roughness=0.30,
                  coat=0.5, coat_rough=0.08)
    lib["pod"] = m

    # Ceramic frit band around rear glass
    m, nt, b = _M.mat("M_Frit_Black")
    _M.set_inputs(b, base=(0.003, 0.003, 0.004), metallic=0.0, roughness=0.07,
                  specular=0.30, coat=0.0)
    lib["frit"] = m

    # mmWave radar cover in lower grille
    m, nt, b = _M.mat("M_Radar_Grey")
    _M.set_inputs(b, base=(0.032, 0.033, 0.036), metallic=0.0, roughness=0.38)
    lib["radar"] = m

    # Bright diamond-cut machined aluminium wheel face and roof rail bar
    m, nt, b = _M.mat("M_Alu_Machined")
    _M.set_inputs(b, base=(0.80, 0.81, 0.83), metallic=1.0, roughness=0.18)
    lib["machined"] = m

    # Dark graphite wheel barrel / optional forged rim
    m, nt, b = _M.mat("M_Wheel_Graphite")
    _M.set_inputs(b, base=(0.012, 0.013, 0.016), metallic=0.0, roughness=0.20,
                  coat=1.0, coat_rough=0.03, ior=1.45)
    lib["graphite"] = m

    # Wheel accent / gloss black pocket
    m, nt, b = _M.mat("M_Wheel_Accent")
    _M.set_inputs(b, base=(0.010, 0.010, 0.012), metallic=0.0, roughness=0.12,
                  coat=1.0, coat_rough=0.03, ior=1.45)
    lib["accent"] = m

    # Satin black plastic trim (rocker cladding, lower intakes, aprons, bumper blacks)
    m, nt, b = _M.mat("M_Black_Trim")
    _M.set_inputs(b, base=(0.012, 0.012, 0.013), metallic=0.0, roughness=0.30, coat=0.0)
    lib["black_trim"] = m

    # Ventilated cast-iron brake disc
    m, nt, b = _M.mat("M_Disc_Iron")
    _M.set_inputs(b, base=(0.140, 0.125, 0.110), metallic=0.0, roughness=0.52)
    lib["iron"] = m
    return lib
