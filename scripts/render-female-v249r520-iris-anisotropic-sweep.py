import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-natural-eye-ratio-r520.blend"
OUT = ROOT / "assets-source/aevrynd-character/reviews/v249r520-iris-anisotropic-sweep"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
irises = [bpy.data.objects[f"Eye_{side}_Iris"] for side in ("L", "R")]
original = []
for obj in irises:
    scale = obj.scale.copy()
    scale /= 0.60
    original.append(scale)
OUT.mkdir(parents=True, exist_ok=True)
for label, fx, fy in (("a-uniform-060", 0.60, 0.60), ("b-wide-075x065", 0.75, 0.65), ("c-wide-085x065", 0.85, 0.65)):
    for obj, source in zip(irises, original):
        obj.scale.x = source.x * fx
        obj.scale.y = source.y * fy
        obj.scale.z = source.z * 0.60
    scene.frame_set(1)
    bpy.context.view_layer.update()
    for view, location, target, lens, size in (
        ("eye-close", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700)),
        ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000)),
    ):
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.resolution_x, scene.render.resolution_y = size
        scene.render.filepath = str(OUT / f"{label}-{view}.png")
        bpy.ops.render.render(write_still=True)
print("AEVRYND_R520_IRIS_ANISOTROPIC_RENDER=" + json.dumps({"variants": [[0.60, 0.60], [0.75, 0.65], [0.85, 0.65]]}))
