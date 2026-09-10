import json
import runpy
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-skin-baked-r76.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-eyelid-r78.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-eyelid-r78"
BODY = "AevryndFemaleBodyBaseV118"
STRENGTH = 1.2


helpers = runpy.run_path(str(ROOT / "scripts/sweep-female-v249-mainline-eyelid-r78.py"))
look_at = helpers["look_at"]
is_hair = helpers["is_hair"]
sculpt = helpers["sculpt"]


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects[BODY]
body.data = body.data.copy()
geometry = sculpt(body, STRENGTH)
body["aevrynd_face_revision"] = "v249-mainline-eyelid-r78"
body["aevrynd_eyelid_refinement"] = "narrow upper crease, tarsal roll, lower-lid roll and infraorbital transition"
scene = bpy.context.scene
scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "eyelid-r78"
scene["aevrynd_release_state"] = "R78_STRICT_VISUAL_COLLISION_AND_RUNTIME_REVIEW_REQUIRED"
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
hair_objects = [obj for obj in bpy.data.objects if is_hair(obj)]
for obj in hair_objects:
    obj.hide_render = True
render(camera, "01-face-front-face-only", (0.0, -0.56, 1.605), (0.0, -0.060, 1.605), 118)
render(camera, "02-face-three-quarter-face-only", (0.40, -0.56, 1.625), (0.0, -0.020, 1.605), 104)
render(camera, "03-face-profile-face-only", (0.70, -0.03, 1.61), (0.0, -0.005, 1.595), 88)
for obj in hair_objects:
    obj.hide_render = False
render(camera, "04-face-front-with-hair", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88)
report = {"source": str(SOURCE), "output": str(OUTPUT), "strength": STRENGTH, "geometry": geometry}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_EYELID_R78=" + json.dumps(report, sort_keys=True))
