import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "assets-source/reference/blender-official-hair/hair_nodes-female_hair_styles.blend"
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-hair-material-r129.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-curly-r156.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-owned-curly-r156.build-report.json"
REFERENCE_GROWTH = "curly growth mesh"
REFERENCE_HAIR = "curly hair"
TARGET_SCALP = "AevryndFemaleAnatomicalScalpFoundation_v249r101"
TARGET_MATERIAL = "AevryndOwnedLayeredHairMaterial_v249r129"
TARGET_HAIR = "AevryndFemaleOwnedCurlyHairMain_v249r156"
KEEP = 0.40
ROOT_RADIUS = 0.000055
TIP_RADIUS = 0.000010


def object_bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return (
        Vector(tuple(min(point[axis] for point in points) for axis in range(3))),
        Vector(tuple(max(point[axis] for point in points) for axis in range(3))),
    )


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
    curves = []
    for curve in obj.data.curves:
        start = curve.first_point_index
        curves.append([
            obj.matrix_world @ obj.data.points[start + offset].position
            for offset in range(curve.points_length)
        ])
    return curves


def stable_score(index, root):
    key = f"{index}:{root.x:.5f}:{root.y:.5f}:{root.z:.5f}".encode("ascii")
    digest = hashlib.blake2b(key, digest_size=8).digest()
    return int.from_bytes(digest, "big") / float(2**64 - 1)


def is_hair_layer(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    name = obj.name.lower()
    return layer.startswith("hair.") or any(token in name for token in ("hair", "groom", "scalp"))


bpy.ops.wm.open_mainfile(filepath=str(REFERENCE))
growth_min, growth_max = object_bounds(bpy.data.objects[REFERENCE_GROWTH])
source_center = (growth_min + growth_max) * 0.5
source_curves = bake_reference(REFERENCE_HAIR)
selected_curves = [
    curve for index, curve in enumerate(source_curves)
    if stable_score(index, curve[0]) < KEEP
]

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
target_scalp = bpy.data.objects[TARGET_SCALP]
target_min, target_max = object_bounds(target_scalp)
target_center = (target_min + target_max) * 0.5
source_size = growth_max - growth_min
target_size = target_max - target_min
scale = Vector((
    target_size.x / source_size.x,
    target_size.y / source_size.y,
    target_size.z / source_size.z,
))

hidden_layers = []
for obj in bpy.data.objects:
    if is_hair_layer(obj):
        obj.hide_render = True
        obj.hide_viewport = True
        hidden_layers.append(obj.name)

data = bpy.data.hair_curves.new(TARGET_HAIR + "Data")
data.add_curves([len(curve) for curve in selected_curves])
point_index = 0
for curve in selected_curves:
    for source_point in curve:
        delta = source_point - source_center
        data.points[point_index].position = target_center + Vector((
            delta.x * scale.x,
            delta.y * scale.y,
            delta.z * scale.z,
        ))
        point_index += 1

radius = data.attributes.new("radius", "FLOAT", "POINT")
for curve in data.curves:
    for local_index in range(curve.points_length):
        t = local_index / max(1, curve.points_length - 1)
        radius.data[curve.first_point_index + local_index].value = ROOT_RADIUS * (1.0 - t) + TIP_RADIUS * t
data.materials.append(bpy.data.materials[TARGET_MATERIAL])

hair = bpy.data.objects.new(TARGET_HAIR, data)
scene.collection.objects.link(hair)
hair["aevrynd_layer"] = "hair.follow.curly.main"
hair["aevrynd_revision"] = "v249r156"
hair["aevrynd_source"] = "Blender official Hair Nodes female hair styles, CC0; baked and deterministically sampled"
hair["aevrynd_source_license"] = "CC0"
hair["aevrynd_runtime_dependency"] = "none"
hair["aevrynd_density_keep"] = KEEP
hair["aevrynd_collision_status"] = "PENDING_STRICT_AUDIT"

rig = bpy.data.objects.get("AevryndFemaleRig")
if rig:
    world = hair.matrix_world.copy()
    hair.parent = rig
    hair.matrix_parent_inverse = rig.matrix_world.inverted()
    hair.matrix_world = world

target_scalp.hide_render = True
target_scalp.hide_viewport = True
scene["aevrynd_revision"] = "v249r156"
scene["aevrynd_candidate_status"] = "TECHNICAL_REVIEW_PENDING"
scene["aevrynd_runtime_dependency"] = "none"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "reference": str(REFERENCE),
    "referenceLicense": "CC0",
    "runtimeDependency": "none",
    "output": str(OUTPUT),
    "object": TARGET_HAIR,
    "layer": "hair.follow.curly.main",
    "keep": KEEP,
    "curves": len(data.curves),
    "points": len(data.points),
    "rootRadiusM": ROOT_RADIUS,
    "tipRadiusM": TIP_RADIUS,
    "scale": list(scale),
    "hiddenPriorHairLayers": hidden_layers,
    "status": "TECHNICAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R156_BUILD=" + json.dumps(report, sort_keys=True))
