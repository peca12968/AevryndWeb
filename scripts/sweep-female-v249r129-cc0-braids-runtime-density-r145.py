import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "assets-source/reference/blender-official-hair/hair_nodes-female_hair_styles.blend"
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-hair-material-r129.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r129-cc0-braids-runtime-density-r145-sweep"
REFERENCE_GROWTH = "Braids growth mesh"
REFERENCE_HAIR = "braided hair"
TARGET_SCALP = "AevryndFemaleAnatomicalScalpFoundation_v249r101"
TARGET_MATERIAL = "AevryndOwnedLayeredHairMaterial_v249r129"
VARIANTS = (
    {"name": "keep-50-resample-24", "keep": 0.50, "samples": 24, "radius": 0.000052},
    {"name": "keep-40-resample-28", "keep": 0.40, "samples": 28, "radius": 0.000058},
)


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


def resample_polyline(points, count):
    if len(points) <= 1:
        return [points[0].copy() for _ in range(count)]
    segments = [(points[i + 1] - points[i]).length for i in range(len(points) - 1)]
    total = sum(segments)
    if total <= 1e-12:
        return [points[0].copy() for _ in range(count)]
    cumulative = [0.0]
    for length in segments:
        cumulative.append(cumulative[-1] + length)
    result = []
    segment = 0
    for sample in range(count):
        distance = total * sample / max(1, count - 1)
        while segment + 1 < len(cumulative) - 1 and cumulative[segment + 1] < distance:
            segment += 1
        span = max(1e-12, cumulative[segment + 1] - cumulative[segment])
        t = (distance - cumulative[segment]) / span
        result.append(points[segment].lerp(points[segment + 1], t))
    return result


def is_hair_layer(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    name = obj.name.lower()
    return layer.startswith("hair.") or any(token in name for token in ("hair", "groom", "scalp"))


def make_hair(curves, source_center, target_center, scale, variant, material):
    chosen = [curve for i, curve in enumerate(curves) if stable_score(i, curve[0]) < variant["keep"]]
    sampled = [resample_polyline(curve, variant["samples"]) for curve in chosen]
    name = "AevryndFemaleCC0BraidsRuntimeStudy_v249r145_" + variant["name"].replace("-", "_")
    data = bpy.data.hair_curves.new(name + "Data")
    data.add_curves([len(curve) for curve in sampled])
    point_index = 0
    for curve in sampled:
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
            radius.data[curve.first_point_index + local_index].value = variant["radius"] * (1.0 - t) + 0.000010 * t
    data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_layer"] = "hair.study.cc0-baked.braids.runtime-density"
    obj["aevrynd_revision"] = "v249r129-cc0-braids-runtime-density-r145"
    obj["aevrynd_source"] = "Blender official Hair Nodes female hair styles, CC0; deterministic curve sampling and arc-length resampling"
    obj["aevrynd_runtime_dependency"] = "none"
    return obj


def render(camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(REFERENCE))
growth_min, growth_max = object_bounds(bpy.data.objects[REFERENCE_GROWTH])
source_center = (growth_min + growth_max) * 0.5
curves = bake_reference(REFERENCE_HAIR)
original_points = sum(len(curve) for curve in curves)

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
target_min, target_max = object_bounds(bpy.data.objects[TARGET_SCALP])
target_center = (target_min + target_max) * 0.5
source_size = growth_max - growth_min
target_size = target_max - target_min
scale = Vector((target_size.x / source_size.x, target_size.y / source_size.y, target_size.z / source_size.z))
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
scalp = bpy.data.objects[TARGET_SCALP]
report = {
    "reference": str(REFERENCE),
    "source": str(SOURCE),
    "license": "CC0",
    "runtimeDependency": "none",
    "original": {"curves": len(curves), "points": original_points},
    "variants": [],
    "status": "STRICT_VISUAL_REVIEW_REQUIRED",
}

for variant in VARIANTS:
    hair = make_hair(curves, source_center, target_center, scale, variant, material)
    if rig:
        world = hair.matrix_world.copy()
        hair.parent = rig
        hair.matrix_parent_inverse = rig.matrix_world.inverted()
        hair.matrix_world = world
    entry = {
        "name": variant["name"],
        "keep": variant["keep"],
        "samplesPerCurve": variant["samples"],
        "curves": len(hair.data.curves),
        "points": len(hair.data.points),
        "rootRadius": variant["radius"],
        "renders": [],
    }
    for scalp_state in (False, True):
        scalp.hide_render = not scalp_state
        scalp.hide_viewport = not scalp_state
        state = "scalp-on" if scalp_state else "scalp-off"
        prefix = f"{variant['name']}-{state}"
        render(camera, f"{prefix}-front", (0.0, -2.15, 1.55), (0.0, 0.0, 1.55), 82)
        render(camera, f"{prefix}-three-quarter", (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82)
        render(camera, f"{prefix}-top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78)
        entry["renders"].append(state)
    report["variants"].append(entry)
    bpy.data.objects.remove(hair, do_unlink=True)

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R129_CC0_BRAIDS_RUNTIME_DENSITY_R145=" + json.dumps(report, sort_keys=True))
