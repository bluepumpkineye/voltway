import sys
import os
import json

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from eval_blender import eval_code

code = """
import sys, os, time
p = r'c:\\Users\\User\\Documents\\4 - Website_ WebApp Project\\Chinese EV Configurator\\blender\\scripts'
if p not in sys.path:
    sys.path.insert(0, p)

for mod in list(sys.modules):
    if mod.startswith('seal_') or mod in ('build_seal', 'export_seal', 'cabin_parts', 'cabin_tools'):
        del sys.modules[mod]

import export_seal
t0 = time.time()
res = export_seal.web(draco=True)
t_elapsed = time.time() - t0
print(f"EXPORT_SEAL_WEB_SUCCESS: {res} in {t_elapsed:.1f}s")
import scene_setup
scene_setup.main()
exec(open(os.path.join(p, "render_verify_views.py"), encoding="utf-8").read())
"""

print("Triggering export_seal.web(draco=True) + render_verify_views in Blender...")
res = eval_code(code, timeout=600)
print("Response from Blender:")
print(json.dumps(res, indent=2))
