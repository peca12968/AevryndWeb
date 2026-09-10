import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "assets-source/reference/blender-official-hair/hair_nodes-female_hair_styles.blend"
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-hair-material-r129.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r129-cc0-braids-fit-r144-sweep"
REFERENCE_GROWTH = "Braids growth mesh"
REFERENCE_HAIR = "braided hair"
TARGET_SCALP = "AevryndFemaleAnatomicalScalpFoundation_v249r101"
TARGET_MATERIAL = "AevryndOwnedLayeredHairMaterial_v249r129"
VARIANTS = (1.00, 1.04, 1.08)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def bounds_from_points(points):
    return (
        Vector(tuple(min(p[i] for p in points) for i in range(3))),
        Vector(tuple(max(p[i] for p in points) for i in range(3))),
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
    return {
        "lengths": [curve.points_length for curve in obj.data.curves],
        "points": [obj.matrix_world @ point.position for point in obj.data.points],
    }


def is_hair_layer(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    name = obj.name.lower()
    return layer.startswith("hair.") or any(token in name for token in ("hair", "groom", "scalp"))


def make_hair(records, source_center, target_center, base_scale, radial_factor, material):
    name = f"AevryndFemaleCC0BraidsFitStudy_v249r144_{int(radial_factor * 100):03d}"
    data = bpy.data.hair_curves.new(name + "Data")
    data.add_curves(records["lengths"])
    scale = Vector((base_scale.x * radial_factor, base_scale.y * radial_factor, base_scale.z))
    for index, source_point in enumerate(records["points"]):
        delta = source_point - source_center
        data.points[index].position = target_center + Vector((delta.x * scale.x, delta.y * scale.y, delta.z * scale.z))
    radius = data.attributes.get("radius") or data.attributes.new("radius", "FLOAT", "POINT")
    for curve in data.curves:
        for local_index in range(curve.points_length):
            t = local_index / max(1, curve.points_length - 1)
            radius.data[curve.first_point_index + local_index].value = 0.000040 * (1.0 - t) + 0.000009 * t
    data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_layer"] = "hair.study.cc0-baked.braids"
    obj["aevrynd_revision"] = "v249r129-cc0-braids-fit-r144"
    obj["aevrynd_source"] = "Blender official Hair Nodes female hair styles, CC0; braided hair baked offline"
    obj["aevrynd_runtime_dependency"] = "none"
    return obj, scale


def render(camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(REFERENCE))
growth_min, growth_max = object_bounds(bpy.data.objects[REFERENCE_GROWTH])
source_center = (growth_min + growth_max) * 0.5
records = bake_reference(REFERENCE_HAIR)

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
target_min, target_max = object_bounds(bpy.data.objects[TARGET_SCALP])
target_center = (target_min + target_max) * 0.5
source_size = growth_max - growth_min
target_size = target_max - target_min
base_scale = Vector((
    target_size.x / source_size.x,
    target_size.y / source_size.y,
    target_size.z / source_size.z,
))

for obj in bpy.data.objects:
    if is_hair_layer(obj):
        obj.hide_render = True
        obj.hide_viewport = True

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
material = bpy.data.materials[TARGET_MATERIAL]
rig = bpy.data.objects.get("AevryndFemaleRig")
report = {
    "reference": str(REFERENCE),
    "source": str(SOURCE),
    "license": "CC0",
    "runtimeDependency": "none; evaluated Geometry Nodes baked to ordinary Curves",
    "referenceObject": REFERENCE_HAIR,
    "curves": len(records["lengths"]),
    "points": len(records["points"]),
    "sourceGrowthBounds": [list(growth_min), list(growth_max)],
    "targetScalpBounds": [list(target_min), list(target_max)],
    "baseScale": list(base_scale),
    "variants": [],
    "status": "STRICT_VISUAL_REVIEW_REQUIRED",
}

for radial_factor in VARIANTS:
    hair, scale = make_hair(records, source_center, target_center, base_scale, radial_factor, material)
    if rig:
        world = hair.matrix_world.copy()
        hair.parent = rig
        hair.matrix_parent_inverse = rig.matrix_world.inverted()
        hair.matrix_world = world
    code = f"radial-{int(radial_factor * 100):03d}"
    render(camera, f"{code}-front", (0.0, -2.15, 1.55), (0.0, 0.0, 1.55), 82)
    render(camera, f"{code}-three-quarter", (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82)
    render(camera, f"{code}-profile", (2.15, 0.0, 1.57), (0.0, 0.0, 1.55), 86)
    render(camera, f"{code}-top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78)
    report["variants"].append({"name": code, "radialFactor": radial_factor, "scale": list(scale)})
    bpy.data.objects.remove(hair, do_unlink=True)

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R129_CC0_BRAIDS_FIT_R144=" + json.dumps(report, sort_keys=True))
