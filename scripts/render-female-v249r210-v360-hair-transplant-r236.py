import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
HAIR_SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-anisotropic-hair-v360.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r236-v360-hair-transplant"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-v360-hair-transplant-r236.render-report.json"
HAIR_OBJECTS = (
    "AevryndFemaleHair_ShapedOverlay_v319_R",
    "AevryndFemaleHair_ShapedOverlay_v319_L",
    "AevryndFemaleHair_CrownRootVeil_v338_R",
    "AevryndFemaleHair_CrownRootVeil_v338_L",
    "AevryndFemaleHair_ContinuousFlow_v317_R",
    "AevryndFemaleHair_ContinuousFlow_v317_L",
)


def is_old_hair(obj):
    layer = str(obj.get("aevrynd_layer", "")).lower()
    name = obj.name.lower()
    return layer.startswith("hair.") or "longhairstudy" in name or "scalp" in name


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, filename, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
removed = []
for obj in list(bpy.context.scene.objects):
    if is_old_hair(obj):
        removed.append(obj.name)
        bpy.data.objects.remove(obj, do_unlink=True)

with bpy.data.libraries.load(str(HAIR_SOURCE), link=False) as (source, target):
    missing = [name for name in HAIR_OBJECTS if name not in source.objects]
    if missing:
        raise RuntimeError(f"Missing v360 hair objects: {missing}")
    target.objects = list(HAIR_OBJECTS)

linked = []
for obj in target.objects:
    if obj is None:
        continue
    bpy.context.scene.collection.objects.link(obj)
    obj.hide_render = False
    obj.hide_viewport = False
    obj["aevrynd_transplant_revision"] = "v249r236-v360-hair-visual-study"
    linked.append({
        "name": obj.name,
        "type": obj.type,
        "layer": obj.get("aevrynd_layer"),
        "curves": len(obj.data.curves) if obj.type == "CURVES" else None,
        "points": len(obj.data.points) if obj.type == "CURVES" else None,
    })

scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
OUT.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd Review Camera"]
for view_name, location, target_point, lens in (
    ("01-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("02-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
    ("03-profile", (0.72, 0.0, 1.60), (0.0, 0.0, 1.58), 88),
    ("04-hair-back", (0.0, 0.72, 1.60), (0.0, 0.025, 1.60), 88),
    ("05-hair-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
):
    render(camera, f"{view_name}.png", location, target_point, lens)

report = {
    "source": str(SOURCE),
    "hairSource": str(HAIR_SOURCE),
    "removed": sorted(removed),
    "linked": linked,
    "status": "STATIC_VISUAL_REVIEW_ONLY_COLLISION_AND_DYNAMIC_BINDING_NOT_PROVEN",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R236_V360_HAIR_TRANSPLANT=" + json.dumps(report, sort_keys=True))
