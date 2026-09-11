from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-separated-front-lock-layer-r374.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r374-hairline-layer-isolation"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
camera.location = (0.0, -0.57, 1.76)
camera.data.lens = 92
look_at(camera, (0.0, -0.02, 1.64))
front = bpy.data.objects["AevryndFemaleAuthoredFrontLocks_R374"]
transition = bpy.data.objects["AevryndFemaleHairlineTransition_R374"]
OUT.mkdir(parents=True, exist_ok=True)
for label, show_front, show_transition in (
    ("a-all-layers", True, True),
    ("b-without-front-locks", False, True),
    ("c-without-front-locks-or-transition", False, False),
):
    front.hide_render = not show_front
    transition.hide_render = not show_transition
    scene.render.filepath = str(OUT / f"{label}.png")
    bpy.ops.render.render(write_still=True)
print(f"AEVRYND_R374_HAIRLINE_ISOLATION={OUT}")
