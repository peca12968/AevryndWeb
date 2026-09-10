import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r38.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r44.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-hair-r44"
OUT.mkdir(parents=True, exist_ok=True)
MATERIAL = "AevryndFemaleHairMaterial_v249r27"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
material = bpy.data.materials[MATERIAL]
hair = next(node for node in material.node_tree.nodes if node.type == "BSDF_HAIR_PRINCIPLED")
settings = {
    "Roughness": 0.42,
    "Radial Roughness": 0.54,
    "Coat": 0.045,
    "Random Roughness": 0.20,
}
for name, value in settings.items():
    hair.inputs[name].default_value = value
material["aevrynd_hair_revision"] = "v249-mainline-hair-r44"
material["aevrynd_hair_method"] = "decorrelated roughness response without geometry changes"

scene = bpy.context.scene
scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_hair_candidate"] = "v249-mainline-hair-r44"
scene["aevrynd_release_state"] = "HAIR_R44_PENDING_STRICT_VISUAL_REVIEW"
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("01-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000)),
    ("02-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88, (1000, 1000)),
    ("03-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82, (900, 900)),
    ("04-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78, (1000, 1000)),
)
for name, location, target, lens, resolution in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)

payload = {"source": str(SOURCE), "output": str(OUTPUT), "settings": settings}
(OUT / "report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_MAINLINE_HAIR_R44=" + json.dumps(payload, sort_keys=True))
