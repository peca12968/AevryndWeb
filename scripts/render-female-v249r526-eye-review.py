import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
MODELS = (
    ("r522", ASSETS / "aevrynd-female-authoring-v249-mainline-natural-commissures-r522.blend"),
    ("r526", ASSETS / "aevrynd-female-authoring-v249-mainline-orbital-brow-refit-r526.blend"),
)
OUT = ASSETS / "reviews/v249r526-orbital-brow-refit-eye"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


OUT.mkdir(parents=True, exist_ok=True)
for revision, model in MODELS:
    bpy.ops.wm.open_mainfile(filepath=str(model))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
    scene.camera = camera
    for frame, view, location, target, lens, size in (
        (1, "eye-front", (0.0, -0.405, 1.610), (0.0, -0.105, 1.610), 135, (1400, 760)),
        (1, "eye-oblique", (0.235, -0.405, 1.612), (0.0, -0.105, 1.610), 135, (1400, 760)),
        (20, "eye-front-pose", (0.0, -0.405, 1.610), (0.0, -0.105, 1.610), 135, (1400, 760)),
        (20, "eye-oblique-pose", (0.235, -0.405, 1.612), (0.0, -0.105, 1.610), 135, (1400, 760)),
    ):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.resolution_x, scene.render.resolution_y = size
        scene.render.filepath = str(OUT / f"{revision}-{view}.png")
        bpy.ops.render.render(write_still=True)
print("AEVRYND_R526_EYE_REVIEW=" + json.dumps({"models": [revision for revision, _ in MODELS], "frames": [1, 20]}))

