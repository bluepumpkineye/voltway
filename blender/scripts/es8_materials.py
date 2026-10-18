"""Material library for the Nio ES8: carkit's library in the ES8's finishes.

Default studio finish: Starlight Grey (星澜灰, Xinglan Grey) with a fine metallic flake
(metal_max=0.16 < 0.20 for glTF paint export) and Nio's signature Air Glow Orange (气辉橙)
Brembo 6-piston brake calipers.
"""
from carkit import materials as _M

LIGHTS_ON = False
TAIL_LIGHTS = 1.35

# Starlight Grey (星澜灰): refined pearl titanium-grey metallic (calibrated for studio rig)
ES8_STARLIGHT_GREY = dict(
    name="M_Paint_ES8_StarlightGrey",
    base=(0.095, 0.102, 0.115),
    roughness=0.28,
    specular=0.22,
    coat_rough=0.045,
    peel=0.010,
    flake=dict(scale=2800.0, bump=0.028, metal_max=0.18),
)
SHEEN = dict(weight=0.20, tint=(0.78, 0.82, 0.90), roughness=0.28)

# Air Glow Orange (气辉橙) Brembo 6-piston caliper finish
_M.CALIPERS.setdefault("nio_orange", dict(
    base=(0.82, 0.16, 0.03), metallic=0.35, roughness=0.22, coat=1.0, coat_rough=0.04))
_M.RIMS.setdefault("dark_grey", dict(
    base=(0.032, 0.034, 0.038), metallic=0.0, roughness=0.26, coat=1.0, coat_rough=0.05))


def _sheen(m):
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for key, val in (("Sheen Weight", SHEEN["weight"]),
                     ("Sheen Tint", SHEEN["tint"] + (1.0,)),
                     ("Sheen Roughness", SHEEN["roughness"])):
        if key in b.inputs:
            b.inputs[key].default_value = val
    return m


def build_library():
    lib = _M.build_library(paint=ES8_STARLIGHT_GREY, rim="dark_grey", caliper="nio_orange",
                           lights_on=LIGHTS_ON, tail_lights=TAIL_LIGHTS)
    _sheen(lib["paint"])

    # Double-Dash & HDPL crystal headlamp lens
    m, nt, b = _M.mat("M_Lamp_Clear")
    _M.set_inputs(b, base=(0.060, 0.065, 0.072), metallic=0.50, roughness=0.20,
                  coat=1.0, coat_rough=0.02, ior=1.52)
    lib["lamp_clear"] = m

    # Super-Red illumiBlade taillamp smoked acrylic lens
    m, nt, b = _M.mat("M_Lamp_RedLens")
    _M.set_inputs(b, base=(0.090, 0.004, 0.006), metallic=0.0, roughness=0.06,
                  coat=1.0, coat_rough=0.02, ior=1.52, specular=0.5)
    lib["lamp_red_lens"] = m

    # Diffuser & bumper satin insert
    m, nt, b = _M.mat("M_Pod_Grey")
    _M.set_inputs(b, base=(0.070, 0.074, 0.080), metallic=0.35, roughness=0.30,
                  coat=0.5, coat_rough=0.08)
    lib["pod"] = m

    # Ceramic frit band
    m, nt, b = _M.mat("M_Frit_Black")
    _M.set_inputs(b, base=(0.003, 0.003, 0.004), metallic=0.0, roughness=0.07,
                  specular=0.30, coat=0.0)
    lib["frit"] = m

    # mmWave radar cover
    m, nt, b = _M.mat("M_Radar_Grey")
    _M.set_inputs(b, base=(0.030, 0.032, 0.035), metallic=0.0, roughness=0.38)
    lib["radar"] = m

    # Satin silver trim (chin blade, door spears, rear bumper strip)
    m, nt, b = _M.mat("M_Trim_Silver")
    _M.set_inputs(b, base=(0.56, 0.58, 0.62), metallic=0.72, roughness=0.22,
                  coat=1.0, coat_rough=0.03, ior=1.45)
    lib["trim_silver"] = m

    # Bright diamond-cut machined aluminium wheel face
    m, nt, b = _M.mat("M_Alu_Machined")
    _M.set_inputs(b, base=(0.82, 0.83, 0.85), metallic=1.0, roughness=0.17)
    lib["machined"] = m

    # Dark graphite wheel barrel
    m, nt, b = _M.mat("M_Wheel_Graphite")
    _M.set_inputs(b, base=(0.012, 0.013, 0.016), metallic=0.0, roughness=0.20,
                  coat=1.0, coat_rough=0.03, ior=1.45)
    lib["graphite"] = m

    # Gloss black wheel pocket accent
    m, nt, b = _M.mat("M_Wheel_Accent")
    _M.set_inputs(b, base=(0.010, 0.010, 0.012), metallic=0.0, roughness=0.12,
                  coat=1.0, coat_rough=0.03, ior=1.45)
    lib["accent"] = m

    # Polished chrome wheel ring
    m, nt, b = _M.mat("M_Wheel_Chrome")
    _M.set_inputs(b, base=(0.82, 0.83, 0.85), metallic=1.0, roughness=0.16)
    lib["chrome_polish"] = m

    # Wheel hub cap black & logo grey
    m, nt, b = _M.mat("M_Cap_Black")
    _M.set_inputs(b, base=(0.011, 0.011, 0.012), metallic=0.0, roughness=0.34, specular=0.30)
    lib["cap_black"] = m

    m, nt, b = _M.mat("M_Logo_Grey")
    _M.set_inputs(b, base=(0.55, 0.56, 0.58), metallic=0.0, roughness=0.40, specular=0.35)
    lib["logo_grey"] = m

    m, nt, b = _M.mat("M_Lug_Grey")
    _M.set_inputs(b, base=(0.11, 0.115, 0.12), metallic=0.85, roughness=0.34)
    lib["lug_grey"] = m

    # Ventilated cast-iron brake disc
    m, nt, b = _M.mat("M_Disc_Iron")
    _M.set_inputs(b, base=(0.145, 0.130, 0.115), metallic=0.0, roughness=0.50)
    lib["iron"] = m

    # Arch cladding
    m, nt, b = _M.mat("M_Cladding")
    _M.set_inputs(b, base=(0.018, 0.019, 0.022), metallic=0.0, roughness=0.48, specular=0.35)
    lib["cladding"] = m
    return lib


GLASS_SAFE = {"M_Glass": (0.016, 0.020, 0.025), "M_Glass_Privacy": (0.008, 0.010, 0.013)}


def export_safe():
    _M.export_safe()
    import bpy
    for name, base in GLASS_SAFE.items():
        m = bpy.data.materials.get(name)
        b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m else None
        if b is not None:
            _M.set_inputs(b, base=base)
