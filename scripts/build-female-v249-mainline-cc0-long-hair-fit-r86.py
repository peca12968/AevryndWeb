import json
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "assets-source/reference/blender-official-hair/hair_nodes-female_hair_styles.blend"
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-cleanup-r84.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-long-hair-fit-r86.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-cc0-long-hair-fit-r86"
SCALP = "AevryndFemaleScalpCoverage_v378"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def bounds_from_points(points):
    return (
        Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points))),
        Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points))),
    )


def object_bounds(obj):
    return bounds_from_points([obj.matrix_world @ Vector(corner) for corner in obj.bound_box])


def bake_reference(name):
    obj = bpy.data.objects[name]
    for selected in bpy.context.selected_objects:
        selected.select_set(False)
    obj.hide_viewport = False
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="CURVES")
    obj = bpy.context.view_layer.objects.active
    lengths = [curve.points_length for curve in obj.data.curves]
    points = [obj.matrix_world @ point.position for point in obj.data.points]
    return {"lengths": lengths, "points": points}


def make_hair(name, records, source_center, target_center, scale, material, layer, flyaway=False):
    data = bpy.data.hair_curves.new(name + "Data")
    data.add_curves(records["lengths"])
    for index, source_point in enumerate(records["points"]):
        delta = source_point - source_center
        transformed = target_center + Vector((delta.x * scale.x, delta.y * scale.y, delta.z * scale.z))
        data.points[index].position = transformed
    radius = data.attributes.get("radius") or data.attributes.new("radius", "FLOAT", "POINT")
    for curve in data.curves:
        for point_index in range(curve.points_length):
            t = point_index / max(1, curve.points_length - 1)
            if flyaway:
                value = (0.000030 * (1.0 - t) + 0.000007 * t)
            else:
                value = (0.000045 * (1.0 - t) + 0.000010 * t)
            radius.data[curve.first_point_index + point_index].value = value
    if material:
        data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_layer"] = layer
    obj["aevrynd_revision"] = "v249-mainline-cc0-long-hair-fit-r86"
    obj["aevrynd_source"] = "Blender official Hair Nodes female hair styles, CC0; baked and rescaled offline"
    obj["aevrynd_runtime_dependency"] = "none"
    return obj


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    name = obj.name.lower()
    return layer.startswith("hair.") or any(token in name for token in ("hair", "groom", "scalp"))


def render(camera, name, location, target, lens, resolution=(1000, 1000)):
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = resolution
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(REFERENCE))
growth_min, growth_max = object_bounds(bpy.data.objects["long hair growth mesh"])
source_center = (growth_min + growth_max) * 0.5
main_records = bake_reference("long hair main")
fly_records = bake_reference("long hair strands")

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scalp = bpy.data.objects[SCALP]
target_min, target_max = object_bounds(scalp)
target_center = (target_min + target_max) * 0.5
source_size = growth_max - growth_min
target_size = target_max - target_min
scale = Vector((target_size.x / source_size.x, target_size.y / source_size.y, target_size.z / source_size.z))

old_main = bpy.data.objects["AevryndFemaleGuideBob_v249r25"]
material = old_main.data.materials[0] if old_main.data.materials else None
for obj in bpy.data.objects:
    if is_hair(obj):
        obj.hide_render = True
        obj.hide_viewport = True
for name in ():
    obj = bpy.data.objects.get(name)
    if obj:
        obj.hide_render = False
        obj.hide_viewport = False

main = make_hair(
    "AevryndFemaleCC0LongHairFitMain_v249r86", main_records,
    source_center, target_center, scale, material, "hair.study.cc0-baked.main",
)
fly = make_hair(
    "AevryndFemaleCC0LongHairFitFlyaway_v249r86", fly_records,
    source_center, target_center, scale, material, "hair.study.cc0-baked.flyaway", True,
)
rig = bpy.data.objects.get("AevryndFemaleRig")
for obj in (main, fly):
    if rig:
        world = obj.matrix_world.copy()
        obj.parent = rig
        obj.matrix_parent_inverse = rig.matrix_world.inverted()
        obj.matrix_world = world

scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "cc0-long-hair-fit-r86"
scene["aevrynd_release_state"] = "R86_REFERENCE_FIT_VISUAL_REVIEW_ONLY"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("01-front", (0.0, -2.15, 1.55), (0.0, 0.0, 1.55), 82, (1000, 1000)),
    ("02-three-quarter", (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82, (1000, 1000)),
    ("03-profile", (2.15, 0.0, 1.57), (0.0, 0.0, 1.55), 86, (1000, 1000)),
    ("04-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82, (1000, 1000)),
    ("05-top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78, (1000, 1000)),
    ("06-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000)),
)
for args in views:
    render(camera, *args)

report = {
    "reference": str(REFERENCE),
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "license": "CC0",
    "runtime_dependency": "none; Geometry Nodes evaluated and baked to ordinary Curves",
    "scale": list(scale),
    "source_growth_bounds": [list(growth_min), list(growth_max)],
    "target_scalp_bounds": [list(target_min), list(target_max)],
    "main": {"curves": len(main.data.curves), "points": len(main.data.points)},
    "flyaway": {"curves": len(fly.data.curves), "points": len(fly.data.points)},
    "status": "STRICT_VISUAL_REVIEW_REQUIRED",
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_CC0_LONG_HAIR_STUDY_R85=" + json.dumps(report, sort_keys=True))
