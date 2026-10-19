"""Material library for Denza Z9: carkit's library in the Z9's factory finishes.

Signature colour: Night Purple (暗夜紫, swatch #3B384E), a deep metallic
violet-indigo shown in Autohome reference set c1_0009..0016.
Metallic is capped at 0.19 to respect the export quality gate (metallic <= 0.20).
"""
from carkit import materials as _M

LIGHTS_ON = False
TAIL_LIGHTS = 1.3

# Night Purple (暗夜紫): swatch #3B384E -> linear RGB (0.048, 0.042, 0.082)
Z9_NIGHT_PURPLE = dict(
    name="M_Paint_Z9_Purple",
    base=(0.048, 0.042, 0.082),
    roughness=0.36,
    specular=0.26,
    coat_rough=0.05,
    peel=0.008,
    flake=None,
)
PAINT_METALLIC = 0.19            # strictly under the export gate's 0.20 ceiling
PAINT_COAT = 0.42
SHEEN = dict(weight=0.05, tint=(0.72, 0.65, 0.92), roughness=0.30)

_M.CALIPERS.setdefault("gunmetal", dict(
    base=(0.22, 0.23, 0.25),
    metallic=0.78,
    roughness=0.26,
    coat=0.8,
    coat_rough=0.08,
))
_M.RIMS.setdefault("z9_luxury_alloy", dict(
    base=(0.78, 0.79, 0.82),
    metallic=0.92,
    roughness=0.18,
    coat=1.0,
    coat_rough=0.04,
))


def _sheen(m):
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for key, val in (("Sheen Weight", SHEEN["weight"]),
                     ("Sheen Tint", SHEEN["tint"] + (1.0,)),
                     ("Sheen Roughness", SHEEN["roughness"])):
        if key in b.inputs:
            b.inputs[key].default_value = val
    return m


def build_library():
    lib = _M.build_library(
        paint=Z9_NIGHT_PURPLE,
        rim="z9_luxury_alloy",
        caliper="gunmetal",
        lights_on=LIGHTS_ON,
        tail_lights=TAIL_LIGHTS,
    )
    _sheen(lib["paint"])
    pb = next(n for n in lib["paint"].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    _M.set_inputs(pb, metallic=PAINT_METALLIC, coat=PAINT_COAT)

    # Front lamp clear outer lens (clean crystalline smoked polycarbonate)
    m, nt, b = _M.mat("M_Lamp_Clear")
    _M.set_inputs(b, base=(0.120, 0.125, 0.138), metallic=0.0, roughness=0.05,
                  coat=1.0, coat_rough=0.02, ior=1.52, specular=0.5)
    lib["lamp_clear"] = m

    # Tail lamp red lens
    m, nt, b = _M.mat("M_Lamp_RedLens")
    _M.set_inputs(b, base=(0.100, 0.003, 0.005), metallic=0.0, roughness=0.06,
                  coat=1.0, coat_rough=0.02, ior=1.52, specular=0.5)
    lib["lamp_red_lens"] = m

    # Corona front DRL & crystal projector emission
    m, nt, b = _M.mat("M_LED_White")
    _M.set_inputs(b, base=(0.95, 0.97, 1.00), metallic=0.0, roughness=0.12,
                  emission=(0.95, 0.97, 1.00), emission_strength=1.6)
    lib["led_white"] = m

    # Time Hourglass tail light & rear fog LED emission
    m, nt, b = _M.mat("M_LED_Red")
    _M.set_inputs(b, base=(0.90, 0.02, 0.03), metallic=0.0, roughness=0.12,
                  emission=(0.95, 0.02, 0.03), emission_strength=1.5)
    lib["led_red"] = m

    # Bright anodized chrome / satin silver trim (window surround, fender blade, rocker strip)
    m, nt, b = _M.mat("M_Trim_Chrome")
    _M.set_inputs(b, base=(0.86, 0.87, 0.90), metallic=0.95, roughness=0.12)
    lib["trim_chrome"] = m

    # Machined luxury alloy face (14-spoke wheel face)
    m, nt, b = _M.mat("M_Alu_Machined")
    _M.set_inputs(b, base=(0.84, 0.85, 0.87), metallic=1.0, roughness=0.16)
    lib["machined"] = m

    # The photographed wheel's faces: satin silver blades (c1_0036: 170 sRGB, flat, with bright chamfers), not
    # mirror chrome, and the white roundel cap
    m, nt, b = _M.mat("M_Wheel_Silver")
    _M.set_inputs(b, base=(0.30, 0.31, 0.33), metallic=1.0, roughness=0.40)
    lib["wheel_silver"] = m
    m, nt, b = _M.mat("M_Wheel_Cap")
    _M.set_inputs(b, base=(0.55, 0.56, 0.60), metallic=0.0, roughness=0.28, coat=0.5, coat_rough=0.10)
    lib["wheel_cap"] = m

    # Gloss black body trim (aero side curtains, lower grille, rocker panel, rear bumper apron)
    m, nt, b = _M.mat("M_Black_Gloss")
    _M.set_inputs(b, base=(0.010, 0.010, 0.012), metallic=0.0, roughness=0.10,
                  coat=1.0, coat_rough=0.03)
    lib["black_gloss"] = m

    # Wheel hub cap & Denza logo chrome
    m, nt, b = _M.mat("M_Cap_Black")
    _M.set_inputs(b, base=(0.012, 0.012, 0.014), metallic=0.0, roughness=0.32, specular=0.30)
    lib["cap_black"] = m

    m, nt, b = _M.mat("M_Logo_Chrome")
    _M.set_inputs(b, base=(0.89, 0.90, 0.93), metallic=1.0, roughness=0.10)
    lib["logo_chrome"] = m

    # Brake discs
    m, nt, b = _M.mat("M_Disc_Iron")
    _M.set_inputs(b, base=(0.140, 0.120, 0.105), metallic=0.1, roughness=0.52)
    lib["iron"] = m

    # Wheel arch cladding & underbody liner
    m, nt, b = _M.mat("M_Cladding")
    _M.set_inputs(b, base=(0.018, 0.019, 0.022), metallic=0.0, roughness=0.50, specular=0.30)
    lib["cladding"] = m

    # Ceramic frit border behind glass
    m, nt, b = _M.mat("M_Frit_Black")
    _M.set_inputs(b, base=(0.003, 0.003, 0.004), metallic=0.0, roughness=0.07, specular=0.30, coat=0.0)
    lib["frit"] = m

    # Authentic white automotive license plate (汽车之家 style)
    m, nt, b = _M.mat("M_License_Plate_White")
    _M.set_inputs(b, base=(0.92, 0.93, 0.95), metallic=0.0, roughness=0.35, specular=0.35)
    lib["plate_white"] = m

    # Black plastic trim (the lower intakes, aprons, rocker strips, bumper blacks): a soft satin black. A piano-black
    # (coat 1) panel facing the camera mirrors the studio's white room and reads mid-grey in the showroom (95 sRGB
    # against 60 for this); real trim is not a mirror either (c1_0002/c1_0034: dark, with a soft sheen).
    m, nt, b = _M.mat("M_Black_Trim")
    _M.set_inputs(b, base=(0.012, 0.012, 0.013), metallic=0.0, roughness=0.30, coat=0.0)
    lib["black_trim"] = m

    return lib


GLASS_SAFE = {
    "M_Glass": (0.015, 0.018, 0.024),
    "M_Glass_Privacy": (0.007, 0.009, 0.012),
}


def export_safe():
    """carkit's export_safe, then Z9 glass tints."""
    _M.export_safe()
    import bpy
    for name, base in GLASS_SAFE.items():
        m = bpy.data.materials.get(name)
        b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m else None
        if b is not None:
            _M.set_inputs(b, base=base)
