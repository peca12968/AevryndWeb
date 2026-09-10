import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r227-hair-layer-isolation"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-hair-layer-isolation-r227.review.json"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
FLYAWAY = "AevryndFemaleCC0LongHairStudyFlyaway_v249r85"
SCALP = "AevryndFemaleDeformMatchedScalp_v249r163"


def describe(obj):
    data = obj.data
    attributes = {}
    for attribute in data.attributes:
        values = []
        if attribute.data_type == "FLOAT":
            values = [item.value for item in attribute.data]
        attributes[attribute.name] = {
            "domain": attribute.domain,
            "type": attribute.data_type,
            "count": len(attribute.data),
            "minimum": min(values) if values else None,
            "maximum": max(values) if values else None,
            "mean": sum(values) / len(values) if values else None,
        }
    return {
        "type": obj.type,
        "curves": len(data.curves) if hasattr(data, "curves") else None,
        "points": len(data.points) if hasattr(data, "points") else len(data.vertices),
        "materials": [material.name for material in data.materials if material],
        "attributes": attributes,
        "layer": obj.get("aevrynd_layer"),
    }


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, filename, location, target, lens=88):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
OUT.mkdir(parents=True, exist_ok=True)
main = bpy.data.objects[MAIN]
flyaway = bpy.data.objects[FLYAWAY]
scalp = bpy.data.objects[SCALP]
states = {
    "a-current": {MAIN: True, FLYAWAY: True, SCALP: True},
    "b-main-scalp": {MAIN: True, FLYAWAY: False, SCALP: True},
    "c-main-only": {MAIN: True, FLYAWAY: False, SCALP: False},
    "d-scalp-only": {MAIN: False, FLYAWAY: False, SCALP: True},
    "e-flyaway-only": {MAIN: False, FLYAWAY: True, SCALP: False},
}
camera = bpy.data.objects["Aevrynd Review Camera"]
for label, visibility in states.items():
    for name, visible in visibility.items():
        bpy.data.objects[name].hide_render = not visible
    render(camera, f"{label}-01-front.png", (0.0, -2.42, 1.48), (0.0, 0.0, 1.42))
    render(camera, f"{label}-02-three-quarter.png", (1.75, -2.10, 1.52), (0.0, 0.0, 1.42))
    render(camera, f"{label}-03-rear.png", (0.0, 2.42, 1.48), (0.0, 0.0, 1.42))
report = {
    "source": str(SOURCE),
    "layers": {MAIN: describe(main), FLYAWAY: describe(flyaway), SCALP: describe(scalp)},
    "states": states,
    "status": "VISUAL_SELECTION_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R227_HAIR_LAYER_ISOLATION=" + json.dumps(report, sort_keys=True))
