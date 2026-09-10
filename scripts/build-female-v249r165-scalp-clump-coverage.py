import bisect
import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-scalp-shadow-proxy-r164.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-scalp-clump-coverage-r165.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-scalp-clump-coverage-r165.build-report.json"
SCALP = "AevryndFemaleDeformMatchedScalp_v249r163"
MAIN_HAIR = "AevryndFemaleOwnedCurlyHairMain_v249r162"
CLUMPS = "AevryndFemaleOwnedCurlyScalpClumps_v249r165"
MATERIAL = "AevryndOwnedLayeredHairMaterial_v249r129"
RIG = "AevryndFemaleRig"
CURVE_COUNT = 2800
POINTS_PER_CURVE = 14
ROOT_CLEARANCE = 0.0007
SEED = 249165


def triangle_samples(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    normal_matrix = evaluated.matrix_world.to_3x3()
    triangles = []
    cumulative = []
    total = 0.0
    for polygon in mesh.polygons:
        if len(polygon.vertices) < 3:
            continue
        indices = polygon.vertices
        for offset in range(1, len(indices) - 1):
            vertices = [mesh.vertices[index] for index in (indices[0], indices[offset], indices[offset + 1])]
            points = [evaluated.matrix_world @ vertex.co for vertex in vertices]
            center = sum(points, Vector()) / 3.0
            normal = sum(((normal_matrix @ vertex.normal).normalized() for vertex in vertices), Vector()).normalized()
            if center.z < 1.595 or normal.z < 0.05:
                continue
            area = (points[1] - points[0]).cross(points[2] - points[0]).length * 0.5
            if area <= 1e-10:
                continue
            normals = [(normal_matrix @ vertex.normal).normalized() for vertex in vertices]
            total += area
            cumulative.append(total)
            triangles.append((points, normals))
    evaluated.to_mesh_clear()
    return triangles, cumulative, total


def sample_root(rng, triangles, cumulative, total):
    triangle = triangles[bisect.bisect_left(cumulative, rng.random() * total)]
    r1 = math.sqrt(rng.random())
    r2 = rng.random()
    weights = (1.0 - r1, r1 * (1.0 - r2), r1 * r2)
    point = sum((triangle[0][index] * weights[index] for index in range(3)), Vector())
    normal = sum((triangle[1][index] * weights[index] for index in range(3)), Vector()).normalized()
    return point, normal


def flow_frame(root, normal):
    crown = Vector((0.0, 0.018, 1.704))
    flow = root - crown
    flow -= normal * flow.dot(normal)
    if flow.length < 1e-6:
        flow = normal.cross(Vector((1.0, 0.0, 0.0)))
    flow.normalize()
    side = normal.cross(flow).normalized()
    return flow, side


def bone_parent(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scalp = bpy.data.objects[SCALP]
triangles, cumulative, total_area = triangle_samples(scalp)
rng = random.Random(SEED)
curves = []
for curve_index in range(CURVE_COUNT):
    root, normal = sample_root(rng, triangles, cumulative, total_area)
    flow, side = flow_frame(root, normal)
    length = rng.uniform(0.014, 0.026)
    amplitude = rng.uniform(0.0018, 0.0038)
    turns = rng.uniform(0.65, 1.15)
    phase = rng.random() * math.tau
    points = []
    for point_index in range(POINTS_PER_CURVE):
        u = point_index / (POINTS_PER_CURVE - 1)
        envelope = math.sin(math.pi * u)
        coil = math.sin(phase + math.tau * turns * u)
        lift = ROOT_CLEARANCE + 0.0045 * envelope + 0.0025 * u * u
        point = root + normal * lift + flow * (length * u) + side * (amplitude * coil * envelope)
        points.append(point)
    curves.append(points)

data = bpy.data.hair_curves.new(CLUMPS + "Data")
data.add_curves([POINTS_PER_CURVE] * CURVE_COUNT)
radius = data.attributes.new("radius", "FLOAT", "POINT")
flat = 0
for curve_index, points in enumerate(curves):
    root_radius = 0.000070 + 0.000025 * ((curve_index * 37) % 101) / 100.0
    for point_index, point in enumerate(points):
        u = point_index / (POINTS_PER_CURVE - 1)
        data.points[flat].position = point
        radius.data[flat].value = root_radius * (1.0 - u) + 0.000015 * u
        flat += 1
data.materials.append(bpy.data.materials[MATERIAL])
clumps = bpy.data.objects.new(CLUMPS, data)
scene.collection.objects.link(clumps)
bone_parent(clumps, bpy.data.objects[RIG])
clumps.visible_shadow = True
clumps["aevrynd_layer"] = "hair.clump.scalp-coverage"
clumps["aevrynd_revision"] = "v249r165"
clumps["aevrynd_source"] = "Aevrynd-owned area sampling and crown-flow generation from r163 deform-matched scalp"
clumps["aevrynd_runtime_dependency"] = "none"
clumps["aevrynd_collision_status"] = "PENDING_STRICT_AUDIT"
clumps["aevrynd_shadow_role"] = "limited clump shadow detail"
scene["aevrynd_revision"] = "v249r165"
scene["aevrynd_candidate_status"] = "COLLISION_AND_VISUAL_REVIEW_PENDING"
scene["aevrynd_hair_layers"] = ["hair.scalp.shadow-proxy", "hair.clump.scalp-coverage", "hair.follow.curly.main"]
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

main_points = len(bpy.data.objects[MAIN_HAIR].data.points)
report = {
    "source": str(SOURCE), "output": str(OUTPUT),
    "object": CLUMPS, "layer": "hair.clump.scalp-coverage",
    "curves": len(data.curves), "points": len(data.points),
    "mainHairPoints": main_points, "combinedHairPoints": main_points + len(data.points),
    "sampledScalpAreaM2": total_area, "rootClearanceM": ROOT_CLEARANCE,
    "mainHairVisibleShadow": bpy.data.objects[MAIN_HAIR].visible_shadow,
    "clumpVisibleShadow": clumps.visible_shadow,
    "runtimeDependency": "none", "status": "COLLISION_AND_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R165_BUILD=" + json.dumps(report, sort_keys=True))
