from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-damped-outer-card-motion-r587.blend"
OUT = ROOT / "assets-source/aevrynd-character/reviews/v249r587-damped-outer-card-motion"
FRAMES = (1, 20, 33, 45, 61)
VIEWS = (
    ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_x = 600
scene.render.resolution_y = 600
scene.render.resolution_percentage = 100
OUT.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    for view, location, target, lens in VIEWS:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.filepath = str(OUT / f"frame-{frame:02d}-{view}.png")
        bpy.ops.render.render(write_still=True)
print("AEVRYND_R587_MOTION_REVIEW=" + str(OUT))
