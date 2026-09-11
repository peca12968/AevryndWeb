from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-runtime-fiber-root-cards-r387.blend"
OUTPUT = ROOT.parent / "Temp/female-realism/v249r387-card-layer-isolation"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
OUTPUT.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
camera.location = (0.0, -0.72, 1.60)
camera.data.lens = 88
look_at(camera, (0.0, -0.025, 1.595))

layers = {
    "front": bpy.data.objects["AevryndFemaleRuntimeCards_front_R387"],
    "crown": bpy.data.objects["AevryndFemaleRuntimeCards_crown_R387"],
    "rear": bpy.data.objects["AevryndFemaleRuntimeCards_rear_R387"],
    "hairline": bpy.data.objects["AevryndFemaleRuntimeCards_hairline_R387"],
    "scalp": bpy.data.objects["AevryndFemaleRuntimeScalpCap_R387"],
}
for label, visible in layers.items():
    for obj in layers.values():
        obj.hide_render = obj is not visible
    scene.render.filepath = str(OUTPUT / f"{label}.png")
    bpy.ops.render.render(write_still=True)

print(f"AEVRYND_R387_CARD_LAYER_ISOLATION={OUTPUT}")
