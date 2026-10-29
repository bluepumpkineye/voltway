"""Material library for the Voyah Passion S (岚图追光S): carkit's library in Passion S finishes.

The Autohome studio turnaround car (c1_0001..c1_0008.jpg) is finished in
Rosy Mist Pink (烟霞粉, Yanxia Pink): a refined warm pearl champagne-blush metallic
with subtle rose-silver flop under a high-gloss clearcoat. Additional launch colours
include Sunleap Red (跃日红), Starlight Silver (星光银), Obsidian Black (玄英黑),
Lanyue Blue (揽月蓝), and Xuanjing Grey (玄晶灰).

Wheels:
  - 21-inch Feichi (飞驰) forged 5-U/Y-twin-spoke wheel in satin gunmetal (default studio car)
  - 21-inch Starlight Obsidian (星芒黑曜) 15-blade starburst wheel in gloss black
  - High-performance Voyah multi-piston brake calipers in signature amber-orange yellow
"""
from carkit import materials as _M
from carkit.materials import export_safe      # noqa: F401  (re-exported)

LIGHTS_ON = False
TAIL_LIGHTS = 1.35

# Rosy Mist Pink (烟霞粉): warm pearl champagne-blush metallic calibrated to c1_0004 studio mid-tone
VPS_ROSY_PINK = dict(
    name="M_Paint_VPS_RosyMistPink",
    base=(0.355, 0.278, 0.286),
    roughness=0.25,
    specular=0.22,
    coat_rough=0.022,
    peel=0.009,
    flake=dict(scale=3000.0, bump=0.028, metal_max=0.16),
)
SHEEN = dict(weight=0.18, tint=(0.94, 0.80, 0.82), roughness=0.30)

_M.CALIPERS.setdefault("voyah_amber", dict(base=(0.740, 0.255, 0.014), metallic=0.14,
                                           roughness=0.22, coat=1.0, coat_rough=0.04))
_M.RIMS.setdefault("feichi_gunmetal", dict(base=(0.068, 0.072, 0.080), metallic=0.84,
                                           roughness=0.28, coat=0.85, coat_rough=0.05))


def _sheen(m):
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for key, val in (("Sheen Weight", SHEEN["weight"]),
                     ("Sheen Tint", SHEEN["tint"] + (1.0,)),
                     ("Sheen Roughness", SHEEN["roughness"])):
        if key in b.inputs:
            b.inputs[key].default_value = val
    return m


def build_library():
    lib = _M.build_library(paint=VPS_ROSY_PINK, rim="feichi_gunmetal", caliper="voyah_amber",
                           lights_on=LIGHTS_ON, tail_lights=TAIL_LIGHTS)
    _sheen(lib["paint"])

    # Smoked crystal lens over upper winged DRL and lower twin-projector pod
    m, nt, b = _M.mat("M_Lamp_Clear")
    _M.set_inputs(b, base=(0.052, 0.056, 0.064), metallic=0.45, roughness=0.18,
                  coat=1.0, coat_rough=0.02, ior=1.52)
    lib["lamp_clear"] = m

    # Full-width smoked taillight acrylic lens over horizontal red LED bar & VOYAH script
    m, nt, b = _M.mat("M_Lamp_RedLens")
    _M.set_inputs(b, base=(0.024, 0.004, 0.005), metallic=0.0, roughness=0.07,
                  coat=1.0, coat_rough=0.02, ior=1.52, specular=0.50)
    lib["lamp_red_lens"] = m

    # Soft illuminated white DRL / Kunpeng emblem glow even in studio daylight
    m, nt, b = _M.mat("M_Lamp_SoftWhite")
    _M.set_inputs(b, base=(0.82, 0.85, 0.90), metallic=0.10, roughness=0.16,
                  coat=0.8, coat_rough=0.03)
    if "Emission Color" in b.inputs:
        b.inputs["Emission Color"].default_value = (0.88, 0.92, 1.0, 1.0)
        b.inputs["Emission Strength"].default_value = 0.65 if not LIGHTS_ON else 4.5
    lib["lamp_white_bar"] = m

    # Rear diffuser satin gunmetal aero insert
    m, nt, b = _M.mat("M_Pod_Grey")
    _M.set_inputs(b, base=(0.055, 0.058, 0.064), metallic=0.35, roughness=0.28,
                  coat=0.6, coat_rough=0.06)
    lib["pod"] = m

    # Rear bumper slim retro-reflectors
    _M.set_inputs(next(n for n in lib["reflector"].node_tree.nodes if n.type == 'BSDF_PRINCIPLED'),
                  base=(0.220, 0.018, 0.016), metallic=0.0, roughness=0.22, coat=0.7, coat_rough=0.06)

    # Ceramic black frit band around panoramic roof and rear liftback glass
    m, nt, b = _M.mat("M_Frit_Black")
    _M.set_inputs(b, base=(0.003, 0.003, 0.004), metallic=0.0, roughness=0.07,
                  specular=0.30, coat=0.0)
    lib["frit"] = m

    # Square mmWave radar cover in lower active-shutter grille
    m, nt, b = _M.mat("M_Radar_Grey")
    _M.set_inputs(b, base=(0.028, 0.030, 0.033), metallic=0.0, roughness=0.22,
                  coat=0.8, coat_rough=0.04)
    lib["radar"] = m

    # Red 'S' sport badge on tailgate ('追光S')
    m, nt, b = _M.mat("M_Badge_Red")
    _M.set_inputs(b, base=(0.560, 0.016, 0.016), metallic=0.22, roughness=0.18,
                  coat=1.0, coat_rough=0.03)
    lib["badge_red"] = m

    # Satin gunmetal face for the 21" Feichi forged wheel
    m, nt, b = _M.mat("M_Wheel_Gunmetal")
    _M.set_inputs(b, base=(0.068, 0.072, 0.080), metallic=0.84, roughness=0.28,
                  coat=0.85, coat_rough=0.05)
    lib["gunmetal"] = m

    # Brushed satin aluminium for subtle interior/projector accents
    m, nt, b = _M.mat("M_Alu_Machined")
    _M.set_inputs(b, base=(0.54, 0.55, 0.57), metallic=0.95, roughness=0.26)
    lib["machined"] = m

    # Gloss obsidian black for the 21" Starlight Obsidian wheel
    m, nt, b = _M.mat("M_Wheel_Obsidian")
    _M.set_inputs(b, base=(0.012, 0.013, 0.015), metallic=0.25, roughness=0.15,
                  coat=1.0, coat_rough=0.03, ior=1.48)
    lib["obsidian"] = m

    # Dark graphite inner wheel barrel
    m, nt, b = _M.mat("M_Wheel_Graphite")
    _M.set_inputs(b, base=(0.016, 0.017, 0.020), metallic=0.20, roughness=0.22,
                  coat=1.0, coat_rough=0.04, ior=1.45)
    lib["graphite"] = m

    # Gloss black wheel pocket accent
    m, nt, b = _M.mat("M_Wheel_Accent")
    _M.set_inputs(b, base=(0.009, 0.009, 0.011), metallic=0.0, roughness=0.12,
                  coat=1.0, coat_rough=0.03, ior=1.45)
    lib["accent"] = m

    # Satin black trim (undertrays, aprons, active grille louvers)
    m, nt, b = _M.mat("M_Black_Trim")
    _M.set_inputs(b, base=(0.012, 0.012, 0.013), metallic=0.0, roughness=0.30, coat=0.0)
    lib["black_trim"] = m

    # Ventilated cast-iron brake disc
    m, nt, b = _M.mat("M_Disc_Iron")
    _M.set_inputs(b, base=(0.115, 0.112, 0.108), metallic=0.68, roughness=0.38)
    lib["iron"] = m
    return lib
