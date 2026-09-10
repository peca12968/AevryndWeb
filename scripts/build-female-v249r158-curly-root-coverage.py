import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-curly-collision-r157.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-curly-root-coverage-r158.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-curly-root-coverage-r158.build-report.json"
SCALP = "AevryndFemaleAnatomicalScalpFoundation_v249r101"
MAIN_HAIR = "AevryndFemaleOwnedCurlyHairMain_v249r157"
MATERIAL = "AevryndOwnedLayeredHairMaterial_v249r129"
COVERAGE = "AevryndFemaleOwnedCurlyRootCoverage_v249r158"
POINTS_PER_CURVE = 10
ROOT_CLEARANCE = 0.0018


def score(*parts):
    key = ":".join(str(part) for part in parts).encode("ascii")
    return int.from_bytes(hashlib.blake2b(key, digest_size=8).digest(), "big") / float(2**64 - 1)


def scalp_samples(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    samples = []
    normal_matrix = evaluated.matrix_world.to_3x3()
    for vertex in mesh.vertices:
        world = evaluated.matrix_world @ vertex.co
        normal = (normal_matrix @ vertex.normal).normalized()
        if world.z <= 1.55 or normal.z <= 0.15:
            continue
        samples.append((vertex.index, world, normal))
    evaluated.to_mesh_clear()
    return samples


def tangent_frame(normal):
    reference = Vector((0.0, 0.0, 1.0))
    tangent = normal.cross(reference)
    if tangent.length < 1e-6:
        tangent = normal.cross(Vector((0.0, 1.0, 0.0)))
    tangent.normalize()
    bitangent = normal.cross(tangent).normalized()
    return tangent, bitangent


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scalp = bpy.data.objects[SCALP]
samples = scalp_samples(scalp)
curve_count = len(samples) * 2
data = bpy.data.hair_curves.new(COVERAGE + "Data")
data.add_curves([POINTS_PER_CURVE] * curve_count)

point_index = 0
for vertex_index, root, normal in samples:
    base_tangent, base_bitangent = tangent_frame(normal)
    for family in range(2):
        phase = math.tau * score(vertex_index, family, "phase")
        rotation = phase + family * math.pi * 0.5
        tangent = base_tangent * math.cos(rotation) + base_bitangent * math.sin(rotation)
        bitangent = normal.cross(tangent).normalized()
        length = 0.016 + 0.010 * score(vertex_index, family, "length")
        amplitude = 0.0030 + 0.0020 * score(vertex_index, family, "amplitude")
        turns = 0.70 + 0.35 * score(vertex_index, family, "turns")
        for local_index in range(POINTS_PER_CURVE):
            u = local_index / (POINTS_PER_CURVE - 1)
            angle = phase + math.tau * turns * u
            radial = amplitude * math.sin(math.pi * u)
            position = (
                root
                + normal * (ROOT_CLEARANCE + length * (0.35 * u + 0.25 * u * u))
                + tangent * (math.sin(angle) * radial)
                + bitangent * ((1.0 - math.cos(angle - phase)) * radial * 0.65)
            )
            data.points[point_index].position = position
            point_index += 1

radius = data.attributes.new("radius", "FLOAT", "POINT")
for curve in data.curves:
    for local_index in range(curve.points_length):
        u = local_index / max(1, curve.points_length - 1)
        radius.data[curve.first_point_index + local_index].value = 0.000042 * (1.0 - u) + 0.000008 * u
data.materials.append(bpy.data.materials[MATERIAL])

coverage = bpy.data.objects.new(COVERAGE, data)
scene.collection.objects.link(coverage)
coverage["aevrynd_layer"] = "hair.root.coverage.curly"
coverage["aevrynd_revision"] = "v249r158"
coverage["aevrynd_source"] = "Aevrynd-owned procedural short curl coverage generated from the owned anatomical scalp"
coverage["aevrynd_runtime_dependency"] = "none"
coverage["aevrynd_collision_clearance_m"] = ROOT_CLEARANCE
coverage["aevrynd_collision_status"] = "PENDING_STRICT_AUDIT"

rig = bpy.data.objects.get("AevryndFemaleRig")
if rig:
    world = coverage.matrix_world.copy()
    coverage.parent = rig
    coverage.matrix_parent_inverse = rig.matrix_world.inverted()
    coverage.matrix_world = world

scalp.hide_render = True
scalp.hide_viewport = True
scene["aevrynd_revision"] = "v249r158"
scene["aevrynd_candidate_status"] = "COLLISION_AND_VISUAL_REVIEW_PENDING"
scene["aevrynd_hair_layers"] = [
    bpy.data.objects[MAIN_HAIR].get("aevrynd_layer"),
    coverage.get("aevrynd_layer"),
]
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "layers": [
        {"object": MAIN_HAIR, "layer": bpy.data.objects[MAIN_HAIR].get("aevrynd_layer"), "points": len(bpy.data.objects[MAIN_HAIR].data.points)},
        {"object": COVERAGE, "layer": "hair.root.coverage.curly", "curves": len(data.curves), "points": len(data.points)},
    ],
    "combinedPoints": len(bpy.data.objects[MAIN_HAIR].data.points) + len(data.points),
    "rootClearanceM": ROOT_CLEARANCE,
    "runtimeDependency": "none",
    "status": "COLLISION_AND_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R158_BUILD=" + json.dumps(report, sort_keys=True))
