import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-eyelid-r78.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-philtrum-r80-diagnostic"
BODY = "AevryndFemaleBodyBaseV118"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    lower = obj.name.lower()
    return layer.startswith("hair.") or any(token in lower for token in ("hair", "groom", "scalp"))


def render(name):
    scene = bpy.context.scene
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
for obj in bpy.data.objects:
    if is_hair(obj):
        obj.hide_render = True
body = bpy.data.objects[BODY]
source = body.data.materials[0]
camera = bpy.data.objects["Aevrynd Review Camera"]
camera.location = (0.0, -0.50, 1.555)
camera.data.lens = 118
look_at(camera, (0.0, -0.070, 1.545))
render("01-current")

base_only = source.copy()
base_only.name = "Aevrynd Diagnostic BaseColor Only"
shader = next(node for node in base_only.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
for socket_name in ("Normal", "Roughness"):
    for link in list(shader.inputs[socket_name].links):
        base_only.node_tree.links.remove(link)
shader.inputs["Roughness"].default_value = 1.0
shader.inputs["Specular IOR Level"].default_value = 0.0
shader.inputs["Subsurface Weight"].default_value = 0.0
shader.inputs["Coat Weight"].default_value = 0.0
body.data.materials[0] = base_only
render("02-base-color-only")

clay = base_only.copy()
clay.name = "Aevrynd Diagnostic Clay"
shader = next(node for node in clay.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
for link in list(shader.inputs["Base Color"].links):
    clay.node_tree.links.remove(link)
shader.inputs["Base Color"].default_value = (0.42, 0.34, 0.30, 1.0)
body.data.materials[0] = clay
render("03-clay-geometry")
report = {
    "source": str(SOURCE),
    "views": ["current", "base-color-only", "clay-geometry"],
    "purpose": "isolate persistent philtrum streaks between geometry, base color, and reflectance/normal layers",
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249_PHILTRUM_R80_DIAGNOSTIC=" + json.dumps(report, sort_keys=True))
