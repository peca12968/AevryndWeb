import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "assets-source/reference/blender-official-hair/hair_nodes-female_hair_styles.blend"
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-hair-material-r129.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-dual-layer-root-flow-r148.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r129-dual-layer-root-flow-r148"
REFERENCE_GROWTH = "Braids growth mesh"
REFERENCE_HAIR = "braided hair"
TARGET_SCALP = "AevryndFemaleAnatomicalScalpFoundation_v249r101"
TARGET_MATERIAL = "AevryndOwnedLayeredHairMaterial_v249r129"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def object_bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return (
        Vector(tuple(min(p[i] for p in points) for i in range(3))),
        Vector(tuple(max(p[i] for p in points) for i in range(3))),
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
        curves.append([obj.matrix_world @ obj.data.points[start + i].position for i in range(curve.points_length)])
    return curves


def stable_score(index, root):
    key = f"{index}:{root.x:.5f}:{root.y:.5f}:{root.z:.5f}".encode("ascii")
    return int.from_bytes(hashlib.blake2b(key, digest_size=8).digest(), "big") / float(2**64 - 1)


def resample_polyline(points, count, end_fraction=1.0):
    if len(points) <= 1:
        return [points[0].copy() for _ in range(count)]
    segments = [(points[i + 1] - points[i]).length for i in range(len(points) - 1)]
    total = sum(segments)
    cumulative = [0.0]
    for length in segments:
        cumulative.append(cumulative[-1] + length)
    result = []
    segment = 0
    maximum = total * end_fraction
    for sample in range(count):
        distance = maximum * sample / max(1, count - 1)
        while segment + 1 < len(cumulative) - 1 and cumulative[segment + 1] < distance:
            segment += 1
        span = max(1e-12, cumulative[segment + 1] - cumulative[segment])
        result.append(points[segment].lerp(points[segment + 1], (distance - cumulative[segment]) / span))
    return result


def transform_curve(curve, source_bounds, target_bounds, narrow_part):
    source_min, source_max = source_bounds
    target_min, target_max = target_bounds
    source_center = (source_min + source_max) * 0.5
    target_center = (target_min + target_max) * 0.5
    scale = Vector(tuple((target_max[i] - target_min[i]) / (source_max[i] - source_min[i]) for i in range(3)))
    result = []
    for index, point in enumerate(curve):
        delta = point - source_center
        transformed = target_center + Vector((delta.x * scale.x, delta.y * scale.y, delta.z * scale.z))
        if narrow_part:
            t = index / max(1, len(curve) - 1)
            dx = transformed.x - target_center.x
            influence = max(0.0, 1.0 - abs(dx) / 0.026) * max(0.0, 1.0 - t / 0.34)
            transformed.x -= math.copysign(0.0038 * influence, dx) if abs(dx) > 1e-9 else 0.0
        result.append(transformed)
    return result


def make_hair(name, curves, material, layer, root_radius, tip_radius):
    data = bpy.data.hair_curves.new(name + "Data")
    data.add_curves([len(curve) for curve in curves])
    point_index = 0
    for curve in curves:
        for point in curve:
            data.points[point_index].position = point
            point_index += 1
    radius = data.attributes.new("radius", "FLOAT", "POINT")
    for curve in data.curves:
        for local_index in range(curve.points_length):
            t = local_index / max(1, curve.points_length - 1)
            radius.data[curve.first_point_index + local_index].value = root_radius * (1.0 - t) + tip_radius * t
    data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_layer"] = layer
    obj["aevrynd_revision"] = "v249-mainline-dual-layer-root-flow-r148"
    obj["aevrynd_source"] = "Aevrynd-owned baked derivative; Blender official female hair styles used as CC0 offline reference"
    obj["aevrynd_runtime_dependency"] = "none"
    return obj


def is_hair_layer(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    name = obj.name.lower()
    return layer.startswith("hair.") or any(token in name for token in ("hair", "groom", "scalp"))


def render(camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(REFERENCE))
source_bounds = object_bounds(bpy.data.objects[REFERENCE_GROWTH])
source_curves = bake_reference(REFERENCE_HAIR)
scores = [stable_score(i, curve[0]) for i, curve in enumerate(source_curves)]

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scalp = bpy.data.objects[TARGET_SCALP]
target_bounds = object_bounds(scalp)
for obj in bpy.data.objects:
    if is_hair_layer(obj):
        obj.hide_render = True
        obj.hide_viewport = True

outer_source = [curve for curve, score in zip(source_curves, scores) if score < 0.25]
root_source = [curve for curve, score in zip(source_curves, scores) if 0.25 <= score < 0.62]
outer = [transform_curve(resample_polyline(curve, 48), source_bounds, target_bounds, True) for curve in outer_source]
root_flow = [transform_curve(resample_polyline(curve, 12, 0.27), source_bounds, target_bounds, True) for curve in root_source]
material = bpy.data.materials[TARGET_MATERIAL]
outer_obj = make_hair("AevryndFemaleOwnedHairOuterShape_v249r148", outer, material, "hair.follow.outer_shape", 0.000070, 0.000011)
root_obj = make_hair("AevryndFemaleOwnedHairRootFlow_v249r148", root_flow, material, "hair.root_flow.medium", 0.000040, 0.000017)
rig = bpy.data.objects.get("AevryndFemaleRig")
for obj in (outer_obj, root_obj):
    if rig:
        world = obj.matrix_world.copy()
        obj.parent = rig
        obj.matrix_parent_inverse = rig.matrix_world.inverted()
        obj.matrix_world = world
scalp.hide_render = False
scalp.hide_viewport = False

scene["aevrynd_mainline_revision"] = "dual-layer-root-flow-r148"
scene["aevrynd_release_state"] = "R148_VISUAL_STUDY_ONLY"
scene["aevrynd_runtime_dependency"] = "none"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("01-front", (0.0, -2.15, 1.55), (0.0, 0.0, 1.55), 82),
    ("02-three-quarter", (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82),
    ("03-profile", (2.15, 0.0, 1.57), (0.0, 0.0, 1.55), 86),
    ("04-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82),
    ("05-top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78),
    ("06-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
)
for args in views:
    render(camera, *args)

report = {
    "reference": str(REFERENCE),
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "license": "CC0 reference; Aevrynd-owned baked derivative",
    "runtimeDependency": "none",
    "layers": {
        "outerShape": {"curves": len(outer), "points": sum(len(c) for c in outer), "sourceFraction": 0.25, "samples": 48},
        "rootFlow": {"curves": len(root_flow), "points": sum(len(c) for c in root_flow), "sourceFraction": 0.37, "pathFraction": 0.27, "samples": 12},
    },
    "totalPoints": sum(len(c) for c in outer) + sum(len(c) for c in root_flow),
    "status": "STRICT_VISUAL_REVIEW_REQUIRED",
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249R129_DUAL_LAYER_ROOT_FLOW_R148=" + json.dumps(report, sort_keys=True))
