"""Material library for the Zeekr 7X: carkit's library in the 7X's finishes.

The Ultra in the Autohome studio photographs (blender/reference/zeekr-7x) is
painted canyon-stone blue, a satin metallic blue-grey; wheels are machined-face
5-spoke over black with orange calipers.
"""
from carkit import materials as _M

LIGHTS_ON = False
TAIL_LIGHTS = 1.3

# canyon-stone blue (Autohome 涧石蓝): swatch #49749C, i.e. sRGB 73/116/156. In the
# studio photographs the flanks read as a soft, satin blue-grey metallic (door
# mid-tones ~sRGB 95/120/140, highlights 160/185/205): first pass, calibrated against
# the photographs once the body is built.
# Calibrated in the web viewer against the studio photographs (2026-10-07, through the
# solved cameras): the photographs' satin metallic reads grey-steel blue (door mid-tones
# sRGB ~80/97/110), and under the showroom's dark rig a dielectric paint of the same hue
# came out a deep saturated blue. A constant metallic 0.2 (the export gate's ceiling), a
# lighter, greyer base and a thin satin coat match it: base sRGB ~#4f6579.
# 2026-11-16 refit (the owner's brief): a metallic slate-blue with metalness 0.6, roughness 0.2 and a
# full clear coat. The old dielectric-with-a-thin-satin-coat recipe above was a workaround for the
# showroom's dark rig; the base is lighter and greyer now, to carry a real metal under it, and the
# viewer's finish for this paint (zeekr-7x.ts) is calibrated against the photographs from these values.
ZX_BLUE = dict(name="M_Paint_ZX_Blue", base=(0.105, 0.159, 0.216),
               roughness=0.20, specular=0.50, coat_rough=0.05, peel=0.004, flake=None)
PAINT_METALLIC = 0.60            # carkit.export.check_paint's ceiling is 0.7 now
PAINT_COAT = 1.0
SHEEN = dict(weight=0.0, tint=(0.72, 0.52, 1.0), roughness=0.35)

_M.CALIPERS.setdefault("orange", dict(base=(0.780, 0.160, 0.012), metallic=0.0,
                                      roughness=0.26, coat=1.0, coat_rough=0.06))
_M.RIMS.setdefault("dark_grey", dict(base=(0.040, 0.041, 0.044), metallic=0.0,
                                     roughness=0.30, coat=1.0, coat_rough=0.06))


def _sheen(m):
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for key, val in (("Sheen Weight", SHEEN["weight"]),
                     ("Sheen Tint", SHEEN["tint"] + (1.0,)),
                     ("Sheen Roughness", SHEEN["roughness"])):
        if key in b.inputs:
            b.inputs[key].default_value = val
    return m


def build_library():
    lib = _M.build_library(paint=ZX_BLUE, rim="dark_grey", caliper="orange",
                           lights_on=LIGHTS_ON, tail_lights=TAIL_LIGHTS)
    _sheen(lib["paint"])
    # 2026-11-16: the showroom's white studio turned carkit's piano-black (roughness 0.09, a full clear coat, a
    # full specular) into a mirror: the fender piece, the bumper, the sill and the wheels' faces read chrome-white.
    # The 7X's black is gloss but not a mirror: rougher, no coat, half the specular (calibrated live in the viewer)
    bg = next(n for n in lib["black_gloss"].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    _M.set_inputs(bg, roughness=0.30, coat=0.0, specular=0.25)
    pb = next(n for n in lib["paint"].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    _M.set_inputs(pb, metallic=PAINT_METALLIC, coat=PAINT_COAT)
    # the headlamp lens strip: a dark smoked grey under clear glass (front photograph:
    # sRGB ~58/62/68 where it is not reflecting)
    m, nt, b = _M.mat("M_Lamp_Clear")
    _M.set_inputs(b, base=(0.020, 0.022, 0.026), metallic=0.0, roughness=0.10,
                  coat=1.0, coat_rough=0.02, ior=1.52, specular=0.5)
    lib["lamp_clear"] = m
    # tail-lamp lens: deep red smoked glass over the lit pipes (rear photo:
    # dark wine red where the pipes do not show)
    m, nt, b = _M.mat("M_Lamp_RedLens")
    _M.set_inputs(b, base=(0.090, 0.004, 0.006), metallic=0.0, roughness=0.06,
                  coat=1.0, coat_rough=0.02, ior=1.52, specular=0.5)
    lib["lamp_red_lens"] = m
    # the grey pods in the rear bumper: satin grey, a shade darker than the
    # grey car's paint (rear photo)
    m, nt, b = _M.mat("M_Pod_Grey")
    _M.set_inputs(b, base=(0.100, 0.104, 0.110), metallic=0.3, roughness=0.32,
                  coat=0.5, coat_rough=0.10)
    lib["pod"] = m
    # the black band across the rear glass's top: ceramic frit behind the
    # glass, so glass-smooth - one reflection, no clearcoat (a gloss black's
    # coat mirrored the web studio's ceiling grey). Matte, once the rear top
    # was crowned it read as a rubber mat laid over the glass.
    m, nt, b = _M.mat("M_Frit_Black")
    _M.set_inputs(b, base=(0.003, 0.003, 0.004), metallic=0.0, roughness=0.07,
                  specular=0.30, coat=0.0)
    lib["frit"] = m
    # the radar box in the lower grille: charcoal plastic, a shade lighter
    # than the gloss frame round it (front_silver)
    m, nt, b = _M.mat("M_Radar_Grey")
    _M.set_inputs(b, base=(0.035, 0.036, 0.038), metallic=0.0, roughness=0.40)
    lib["radar"] = m
    # the mirror caps and pillar trim: a bright gloss silver, clearly lighter than the body
    m, nt, b = _M.mat("M_Trim_Silver")
    _M.set_inputs(b, base=(0.52, 0.54, 0.58), metallic=0.65, roughness=0.22,
                  coat=1.0, coat_rough=0.03, ior=1.45)
    lib["trim_silver"] = m
    # the wheels' machined faces and lip ring: bright satin aluminium
    m, nt, b = _M.mat("M_Alu_Machined")
    _M.set_inputs(b, base=(0.78, 0.78, 0.80), metallic=1.0, roughness=0.20)
    lib["machined"] = m
    # the Yufeng's star: glossy graphite with a blue cast. The photographs' mid-tones
    # are sRGB ~62/64/70, but those are reflections of an outdoor sky; under the
    # showroom's white studio a lighter base (#424449) read as gunmetal, so the base
    # is #1d1e22 and the clearcoat carries the rest
    m, nt, b = _M.mat("M_Wheel_Graphite")
    _M.set_inputs(b, base=(0.0123, 0.0130, 0.0159), metallic=0.0, roughness=0.22,
                  coat=1.0, coat_rough=0.03, ior=1.45)
    lib["graphite"] = m
    # the twin-fork's machined bands, spikes and lip: gloss black as shipped; the viewer turns this
    # one material into satin silver metal for the two-tone finish (colour, metalness, roughness:
    # WheelOption.accent), so both finishes are one model
    m, nt, b = _M.mat("M_Wheel_Accent")
    _M.set_inputs(b, base=(0.013, 0.013, 0.014), metallic=0.0, roughness=0.12,
                  coat=1.0, coat_rough=0.03, ior=1.45)
    lib["accent"] = m
    # the multi-spoke's polished disc and its hub cap's ring: bright chrome, a little soft so it
    # reads under the showroom's dark rig (a mirror there shows whatever dark shape faces it)
    m, nt, b = _M.mat("M_Wheel_Chrome")
    _M.set_inputs(b, base=(0.80, 0.81, 0.83), metallic=1.0, roughness=0.17)
    lib["chrome_polish"] = m
    # the black plates of the wheels' caps: satin, so a flat disc does not mirror the studio's white
    # cove (a gloss plate read light grey face-on, where the photographs' read black)
    m, nt, b = _M.mat("M_Cap_Black")
    _M.set_inputs(b, base=(0.011, 0.011, 0.012), metallic=0.0, roughness=0.36, specular=0.30)
    lib["cap_black"] = m
    # the multi-spoke cap's emblem: a flat light grey (the photographs' ~205 sRGB), satin
    m, nt, b = _M.mat("M_Logo_Grey")
    _M.set_inputs(b, base=(0.52, 0.53, 0.55), metallic=0.0, roughness=0.42, specular=0.35)
    lib["logo_grey"] = m
    # the twin-fork's lug-nut caps: dark brushed grey metal, lighter than the black face (the
    # photograph's caps read sRGB ~90-150 where the face is ~10-40)
    m, nt, b = _M.mat("M_Lug_Grey")
    _M.set_inputs(b, base=(0.11, 0.115, 0.12), metallic=0.85, roughness=0.34)
    lib["lug_grey"] = m
    # the brake discs: cast iron, a dull grey-brown (every photograph), not the
    # SU7's carbon-ceramic
    m, nt, b = _M.mat("M_Disc_Iron")
    _M.set_inputs(b, base=(0.135, 0.118, 0.102), metallic=0.0, roughness=0.55)
    lib["iron"] = m
    # the arch cladding and flares: satin black plastic, a shade lighter than the gloss
    # black round it (side photograph: charcoal where it faces the light)
    # 2026-11-16: gloss black, as the brief asks (it was satin: roughness 0.52)
    m, nt, b = _M.mat("M_Cladding")
    _M.set_inputs(b, base=(0.012, 0.013, 0.015), metallic=0.0, roughness=0.34, specular=0.25,
                  coat=0.0, coat_rough=0.05)
    lib["cladding"] = m
    # the roof's arch (A-pillar, rail, C-pillar and the roof spoiler's wing): a matte silver, clearly
    # lighter than the blue under it (side and rear photographs: pale silver grey, satin)
    m, nt, b = _M.mat("M_Roof_Silver")
    # (it read white in the viewer at base 0.52 / metal 0.70: the white studio does the rest; the photographs' silver is
    # sRGB ~150-205)
    _M.set_inputs(b, base=(0.34, 0.355, 0.385), metallic=0.55, roughness=0.45, specular=0.5,
                  coat=0.25, coat_rough=0.25)
    lib["roof_silver"] = m
    # the roof's glass panel between the rails: black glass, a faint blue cast (front 3/4 photograph)
    # (2026-11-19: the whole roof is this one surface now, the front glass included. Roughness 0.06 / coat roughness
    # 0.02 mirrored the studio's softbox as a hard-edged grey slab with ragged edges, which read as outlines on the
    # black; 0.12 / 0.10 and a lighter coat give the same gloss with a soft highlight)
    m, nt, b = _M.mat("M_Roof_Glass")
    _M.set_inputs(b, base=(0.006, 0.008, 0.012), metallic=0.0, roughness=0.12, specular=0.5,
                  coat=0.7, coat_rough=0.10)
    lib["roof_black"] = m
    # the visor (2026-11-16): black smoked glass over the lamp housing; roughness 0.10 and a low specular so
    # the white studio does not wash it grey (a piano-black coat mirrored the whole cove)
    m, nt, b = _M.mat("M_Visor")
    _M.set_inputs(b, base=(0.004, 0.004, 0.005), metallic=0.0, roughness=0.10, specular=0.30, coat=0.0)
    lib["visor"] = m
    m, nt, b = _M.mat("M_Visor_Glass")
    _M.set_inputs(b, base=(0.010, 0.011, 0.013), metallic=0.0, roughness=0.08, specular=0.35, coat=0.0)
    lib["visor_glass"] = m
    # the diffuser's recess: the darkest thing on the car, so its fins read (they were black on grey)
    m, nt, b = _M.mat("M_Diffuser_Back")
    _M.set_inputs(b, base=(0.003, 0.003, 0.004), metallic=0.0, roughness=0.90, specular=0.05, coat=0.0)
    lib["diff_back"] = m
    return lib


# glazing as shipped: dark, a touch cool - the Autohome photographs' glass is neutral
# grey-blue where it is not showing the cabin (carkit's own is green-biased)
GLASS_SAFE = {"M_Glass": (0.016, 0.020, 0.025), "M_Glass_Privacy": (0.008, 0.010, 0.013)}


def export_safe():
    """carkit's export_safe, then the 7X's glass tints."""
    _M.export_safe()
    import bpy
    for name, base in GLASS_SAFE.items():
        m = bpy.data.materials.get(name)
        b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m else None
        if b is not None:
            _M.set_inputs(b, base=base)
