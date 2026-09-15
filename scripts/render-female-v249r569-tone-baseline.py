from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-orbital-brow-refit-r526.blend"
OUTPUT = ASSETS / "reviews/v249r569-lower-face-clearance/00-r526-front.png"


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
for obj in bpy.data.objects:
    name = obj.name.lower()
    layer = str(obj.get("aevrynd_layer", "")).lower()
    if "hair" in name or layer.startswith("hair"):
        obj.hide_render = True
        obj.hide_viewport = True
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
camera.location = (0.0, -0.57, 1.565)
camera.data.lens = 104
camera.rotation_euler = (Vector((0.0, -0.040, 1.555)) - camera.location).to_track_quat("-Z", "Y").to_euler()
scene.render.filepath = str(OUTPUT)
bpy.ops.render.render(write_still=True)
print(f"AEVRYND_R569_TONE_BASELINE={OUTPUT}")
