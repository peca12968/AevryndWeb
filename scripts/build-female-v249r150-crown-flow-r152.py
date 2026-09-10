import bisect
import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-dual-layer-root-flow-r150.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-crown-flow-r152.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r150-crown-flow-r152"
SCALP = "AevryndFemaleAnatomicalScalpFoundation_v249r101"
SOURCE_FLOW = "AevryndFemaleOwnedHairRootFlow_v249r150"
MATERIAL = "AevryndOwnedLayeredHairMaterial_v249r129"
COUNT = 2600
SAMPLES = 12
SEED = 249152


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def scalp_distribution(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    matrix = evaluated.matrix_world
    normal_matrix = matrix.to_3x3().inverted().transposed()
    vertices = [matrix @ vertex.co for vertex in mesh.vertices]
    normals = [(normal_matrix @ vertex.normal).normalized() for vertex in mesh.vertices]
    triangles = []
    cumulative = []
    total = 0.0
    for triangle in mesh.loop_triangles:
        indices = tuple(triangle.vertices)
        a, b, c = (vertices[i] for i in indices)
        center = (a + b + c) / 3.0
        if not (0.0035 < abs(center.x) < 0.038 and -0.085 < center.y < 0.078):
            continue
        area = (b - a).cross(c - a).length * 0.5
        if area <= 1e-12:
            continue
        # Concentrate the new roots toward the under-populated central strip.
        central_weight = 0.45 + 1.55 * (1.0 - min(1.0, abs(center.x) / 0.038))
        total += area * central_weight
        triangles.append((indices, a, b, c))
        cumulative.append(total)
    evaluated.to_mesh_clear()
    return {"triangles": triangles, "cumulative": cumulative, "total": total, "normals": normals}


def sample_surface(distribution, rng):
    index = bisect.bisect_left(distribution["cumulative"], rng.random() * distribution["total"])
    indices, a, b, c = distribution["triangles"][min(index, len(distribution["triangles"]) - 1)]
    su = math.sqrt(rng.random())
    v = rng.random()
    wa, wb, wc = 1.0 - su, su * (1.0 - v), su * v
    point = a * wa + b * wb + c * wc
    normals = distribution["normals"]
    normal = (normals[indices[0]] * wa + normals[indices[1]] * wb + normals[indices[2]] * wc).normalized()
    return point + normal * 0.0008, normal


def world_curves(obj):
    curves = []
    for curve in obj.data.curves:
        start = curve.first_point_index
        curves.append([obj.matrix_world @ obj.data.points[start + i].position for i in range(curve.points_length)])
    return curves


def resample_polyline(points, count):
    lengths = [(points[i + 1] - points[i]).length for i in range(len(points) - 1)]
    total = sum(lengths)
    cumulative = [0.0]
    for length in lengths:
        cumulative.append(cumulative[-1] + length)
    result = []
    segment = 0
    for sample in range(count):
        distance = total * sample / max(1, count - 1)
        while segment + 1 < len(cumulative) - 1 and cumulative[segment + 1] < distance:
            segment += 1
        span = max(1e-12, cumulative[segment + 1] - cumulative[segment])
        result.append(points[segment].lerp(points[segment + 1], (distance - cumulative[segment]) / span))
    return result


def generate_crown_curves(source_curves, distribution, rng):
    roots = [curve[0] for curve in source_curves]
    tree = KDTree(len(roots))
    for index, root in enumerate(roots):
        tree.insert(root, index)
    tree.balance()
    curves = []
    for _ in range(COUNT):
        root, normal = sample_surface(distribution, rng)
        neighbors = list(tree.find_n(root, 4))
        inverse = [1.0 / max(1e-6, distance) for _, _, distance in neighbors]
        weight_sum = sum(inverse)
        weights = [weight / weight_sum for weight in inverse]
        blended = []
        for point_index in range(len(source_curves[0])):
            relative = Vector((0.0, 0.0, 0.0))
            for weight, (_, curve_index, _) in zip(weights, neighbors):
                relative += (source_curves[curve_index][point_index] - source_curves[curve_index][0]) * weight
            blended.append(root + relative)
        curve = resample_polyline(blended, SAMPLES)
        tangent = (curve[2] - curve[0]).normalized()
        side = tangent.cross(normal)
        if side.length > 1e-8:
            side.normalize()
        phase = rng.random() * math.tau
        frequency = rng.uniform(0.45, 0.90)
        amplitude = rng.uniform(0.00025, 0.0011)
        for index in range(1, len(curve)):
            t = index / (len(curve) - 1)
            curve[index] += side * math.sin(phase + t * math.tau * frequency) * amplitude * math.sin(math.pi * t)
        curves.append(curve)
    return curves


def make_hair(curves):
    name = "AevryndFemaleOwnedHairCrownFlow_v249r152"
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
            radius.data[curve.first_point_index + local_index].value = 0.000032 * (1.0 - t) + 0.000002 * t
    data.materials.append(bpy.data.materials[MATERIAL])
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.visible_shadow = False
    obj["aevrynd_layer"] = "hair.guides.crown_flow"
    obj["aevrynd_revision"] = "v249-mainline-crown-flow-r152"
    obj["aevrynd_source"] = "Aevrynd-owned generated crown coverage from owned root-flow interpolation"
    obj["aevrynd_runtime_dependency"] = "none"
    return obj


def render(camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scalp = bpy.data.objects[SCALP]
distribution = scalp_distribution(scalp)
source_curves = world_curves(bpy.data.objects[SOURCE_FLOW])
crown_curves = generate_crown_curves(source_curves, distribution, random.Random(SEED))
crown_obj = make_hair(crown_curves)
rig = bpy.data.objects.get("AevryndFemaleRig")
if rig:
    world = crown_obj.matrix_world.copy()
    crown_obj.parent = rig
    crown_obj.matrix_parent_inverse = rig.matrix_world.inverted()
    crown_obj.matrix_world = world
for obj in bpy.data.objects:
    if obj.type == "CURVES":
        obj.visible_shadow = False

scene["aevrynd_mainline_revision"] = "crown-flow-r152"
scene["aevrynd_release_state"] = "R152_VISUAL_STUDY_ONLY"
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
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "runtimeDependency": "none",
    "seed": SEED,
    "sourceRootFlowCurves": len(source_curves),
    "crownFlow": {"curves": len(crown_curves), "points": sum(len(curve) for curve in crown_curves), "samples": SAMPLES},
    "combinedPoints": 333320 + sum(len(curve) for curve in crown_curves),
    "rootRegion": {"absXMin": 0.0035, "absXMax": 0.038, "yMin": -0.085, "yMax": 0.078},
    "status": "STRICT_VISUAL_REVIEW_REQUIRED",
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249R150_CROWN_FLOW_R152=" + json.dumps(report, sort_keys=True))
