"""Screen content for renders: capture the app's own HMI as a texture.

The web app mounts the live HMI on `screen_main`; a Blender render has no DOM,
so a still of the same HMI goes on the screen instead. The app serves each
car's HMI alone at native size at /capture/hmi/<slug>; headless Edge (or
Chrome) screenshots it:

    capture("xiaomi-su7-ultra")          # -> blender/textures/hmi_<slug>.png
    apply(screen_obj, path, strength)    # emissive display material (renders)

Needs the dev server running (npm run dev). Never ship the render material:
materials.export_safe-style, restore_plain() puts the plain dark screen back
before a glTF export (the app draws the live HMI over it).
"""
import os
import subprocess
from urllib.parse import urlencode

import bpy

from ..textures import TEX_DIR

BROWSERS = (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe")


def capture(slug, base="http://localhost:3000", size=(1280, 800), out=None, wait_ms=8000,
            query=None):
    """Screenshot the app's HMI capture route. `query` puts the HMI in a
    state first, e.g. {"screen": "track", "mode": "qualifying"} (see
    src/app/capture/hmi/[slug]/HmiCapture.tsx)."""
    exe = next((b for b in BROWSERS if os.path.exists(b)), None)
    if exe is None:
        raise RuntimeError("no Edge/Chrome found for headless capture")
    out = out or os.path.join(TEX_DIR, "hmi_%s.png" % slug)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    profile = os.path.join(os.environ.get("TEMP", "."), "carkit_hmi_profile")
    cmd = [exe, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
           "--user-data-dir=" + profile, "--window-size=%d,%d" % size,
           "--virtual-time-budget=%d" % wait_ms, "--screenshot=" + out,
           "%s/capture/hmi/%s%s" % (base, slug, "?" + urlencode(query) if query else "")]
    subprocess.run(cmd, capture_output=True, timeout=120)
    if not os.path.exists(out):
        raise RuntimeError("capture failed: " + " ".join(cmd))
    return out


def display_material(name, image_path, strength=1.4):
    """A lit display: the image as emission under a glossy cover glass."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    b.inputs["Roughness"].default_value = 0.04
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = 1.0
        b.inputs["Coat Roughness"].default_value = 0.02
    tex = nt.nodes.new('ShaderNodeTexImage')
    img = bpy.data.images.load(image_path, check_existing=True)
    tex.image = img
    uv = nt.nodes.new('ShaderNodeTexCoord')
    nt.links.new(uv.outputs["UV"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = strength
    nt.links.new(b.outputs[0], out.inputs[0])
    return m


def apply(ob, image_path, strength=1.4, name=None):
    """Swap `ob`'s material for a display showing image_path (renders only)."""
    m = display_material(name or ("INT_Display_" + ob.name), image_path, strength)
    ob["plain_material"] = ob.data.materials[0].name if ob.data.materials else ""
    ob.data.materials.clear()
    ob.data.materials.append(m)
    return m


def restore_plain(ob):
    """Put the plain (exported) screen material back."""
    name = ob.get("plain_material")
    if name and bpy.data.materials.get(name):
        ob.data.materials.clear()
        ob.data.materials.append(bpy.data.materials[name])
