import json
import runpy
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-eyelid-r78.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-philtrum-r80.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-philtrum-r80"
BODY = "AevryndFemaleBodyBaseV118"
ITERATIONS = 20
FACTOR = 0.50


helpers = runpy.run_path(str(ROOT / "scripts/sweep-female-v249-mainline-philtrum-r80.py"))
look_at = helpers["look_at"]
is_hair = helpers["is_hair"]
topology_smooth = helpers["topology_smooth"]


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
original = [vertex.co.copy() for vertex in body.data.vertices]
geometry = topology_smooth(body, ITERATIONS, FACTOR)
corrected = [vertex.co.copy() for vertex in body.data.vertices]
for vertex, coordinate in zip(body.data.vertices, original):
    vertex.co = coordinate
body.data.update()
basis = body.shape_key_add(name="Basis", from_mix=False)
key = body.shape_key_add(name="Aevrynd_Philtrum_Topology_R80", from_mix=False)
for point, coordinate in zip(key.data, corrected):
    point.co = coordinate
key.value = 1.0
key.slider_min = 0.0
key.slider_max = 1.0
body["aevrynd_face_revision"] = "v249-mainline-philtrum-r80"
body["aevrynd_philtrum_method"] = "editable adjacency-topology depth smoothing shape key"
scene = bpy.context.scene
scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "philtrum-r80"
scene["aevrynd_release_state"] = "R80_STRICT_VISUAL_COLLISION_AND_RUNTIME_REVIEW_REQUIRED"
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
hair_objects = [obj for obj in bpy.data.objects if is_hair(obj)]
for obj in hair_objects:
    obj.hide_render = True
render(camera, "01-face-front-face-only", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108)
render(camera, "02-face-three-quarter-face-only", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88)
render(camera, "03-mouth-close-face-only", (0.0, -0.50, 1.555), (0.0, -0.070, 1.545), 118)
for obj in hair_objects:
    obj.hide_render = False
render(camera, "04-face-front-with-hair", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88)
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "shapeKey": key.name,
    "shapeKeyValue": key.value, "geometry": geometry,
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_PHILTRUM_R80=" + json.dumps(report, sort_keys=True))
