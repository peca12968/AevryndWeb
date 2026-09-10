import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-guarded-anatomical-lids-r183.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-long-hair-integration-r185.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-long-hair-integration-r185.build-report.json"
OUT = ROOT.parent / "Temp/female-realism/v249r185-long-hair-integration"
VISIBLE = {
    "AevryndFemaleCC0LongHairStudyMain_v249r85": "hair.follow.long.main",
    "AevryndFemaleCC0LongHairStudyFlyaway_v249r85": "hair.flyaway.long.independent",
    "AevryndFemaleDeformMatchedScalp_v249r163": "hair.scalp.foundation",
}


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    lower = obj.name.lower()
    return layer.startswith("hair.") or any(token in lower for token in ("hair", "groom", "scalp"))


def point_count(obj):
    if obj.type == "MESH":
        return len(obj.data.vertices)
    if obj.type == "CURVES":
        return len(obj.data.points)
    if obj.type == "CURVE":
        return sum(len(spline.points) if hasattr(spline, "points") else len(spline.bezier_points) for spline in obj.data.splines)
    return 0


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
layers = {}
for obj in bpy.data.objects:
    if is_hair(obj):
        obj.hide_render = True
        obj.hide_viewport = True
for name, layer in VISIBLE.items():
    obj = bpy.data.objects[name]
    obj.hide_render = False
    obj.hide_viewport = False
    obj["aevrynd_layer"] = layer
    obj["aevrynd_revision"] = "v249r185"
    obj["aevrynd_runtime_dependency"] = "none"
    layers[name] = {
        "layer": layer,
        "type": obj.type,
        "points": point_count(obj),
        "parent": obj.parent.name if obj.parent else None,
        "parentType": obj.parent_type,
        "materials": [material.name for material in obj.data.materials if material],
    }

scene["aevrynd_mainline_revision"] = "long-hair-integration-r185"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_candidate_status"] = "STRICT_VISUAL_AND_COLLISION_REVIEW_PENDING"
scene["aevrynd_runtime_dependency"] = "none"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

OUT.mkdir(parents=True, exist_ok=True)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("01-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("02-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
    ("03-face-profile", (0.70, -0.03, 1.61), (0.0, -0.005, 1.595), 88),
    ("04-hair-back", (0.0, 0.72, 1.60), (0.0, 0.025, 1.60), 88),
    ("05-hair-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
)
for name, location, target, lens in views:
    render(camera, name, location, target, lens)

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "visibleHairLayers": layers,
    "totalVisibleHairPoints": sum(item["points"] for item in layers.values()),
    "runtimeDependency": "none",
    "status": "STRICT_VISUAL_AND_COLLISION_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R185_LONG_HAIR_INTEGRATION=" + json.dumps(report, sort_keys=True))
