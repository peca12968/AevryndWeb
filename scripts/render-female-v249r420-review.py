from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-layered-optical-stack-r420.blend"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r420-layered-optical-stack"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.exposure = 0.0
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
scene.camera = camera
RENDER_DIR.mkdir(parents=True, exist_ok=True)
views = (
    (1, "front-f01", (0.0, -0.90, 1.59), (0.0, 0.0, 1.56), 82),
    (20, "front-f20", (0.0, -0.90, 1.59), (0.0, 0.0, 1.56), 82),
    (1, "face-close-f01", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
    (1, "eyes-close-f01", (0.0, -0.46, 1.615), (0.0, -0.035, 1.610), 105),
    (1, "three-quarter-f01", (0.45, -0.62, 1.62), (0.0, -0.02, 1.605), 90),
)
for frame, name, location, target, lens in views:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)
print(f"AEVRYND_R420_REVIEW={RENDER_DIR}")
