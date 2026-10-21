import bpy
import os

render_dir = r"c:\Users\User\Documents\4 - Website_ WebApp Project\Chinese EV Configurator\blender\renders"
os.makedirs(render_dir, exist_ok=True)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32
scene.render.resolution_x = 960
scene.render.resolution_y = 540

# Setup studio render cameras
cams = {
    "front_34": ((3.8, 2.5, 1.4), (1.1, 0.0, 0.6)),
    "rear_34": ((-3.8, 2.4, 1.3), (-1.2, 0.0, 0.7)),
    "side": ((0.0, 4.2, 0.95), (0.0, 0.0, 0.7)),
    "front": ((4.2, 0.0, 0.85), (1.8, 0.0, 0.65)),
    "rear": ((-4.2, 0.0, 0.95), (-1.8, 0.0, 0.75)),
}

from mathutils import Vector, Matrix

for name, (pos, aim) in cams.items():
    cam_name = f"Verify_Cam_{name}"
    cam_data = bpy.data.cameras.get(cam_name) or bpy.data.cameras.new(cam_name)
    cam_ob = bpy.data.objects.get(cam_name) or bpy.data.objects.new(cam_name, cam_data)
    if cam_ob.name not in scene.collection.objects:
        scene.collection.objects.link(cam_ob)
    
    cam_data.lens = 45
    cam_ob.location = Vector(pos)
    
    # Orient towards aim
    direction = Vector(aim) - Vector(pos)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_ob.rotation_euler = rot_quat.to_euler()
    
    scene.camera = cam_ob
    out_path = os.path.join(render_dir, f"verify_seal_{name}.png")
    scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {name} -> {out_path}")

print("ALL_RENDERS_FINISHED")
