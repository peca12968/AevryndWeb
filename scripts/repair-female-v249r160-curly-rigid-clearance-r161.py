import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-curly-head-binding-r160.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-curly-rigid-clearance-r161.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-curly-rigid-clearance-r161.repair-report.json"
BODY = "AevryndFemaleBodyBaseV118"
HAIR = "AevryndFemaleOwnedCurlyHairMain_v249r160"
FRAMES = (1, 20)
TARGET = 0.0015
NEAR = 0.025
FAIL_LIMIT = -0.0005


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def signed_hit(tree, world):
    hit = tree.find_nearest(world)
    if hit is None or hit[1] is None or hit[3] > NEAR:
        return None
    normal = hit[1].normalized()
    return hit[0], normal, (world - hit[0]).dot(normal)


def prepare(scene, frame):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    return evaluated_tree(bpy.data.objects[BODY], bpy.context.evaluated_depsgraph_get())


def count_penetrations(obj, scene):
    results = {}
    for frame in FRAMES:
        tree = prepare(scene, frame)
        count = 0
        minimum = math.inf
        for point in obj.data.points:
            hit = signed_hit(tree, obj.matrix_world @ point.position)
            if hit is None:
                continue
            minimum = min(minimum, hit[2])
            count += hit[2] < FAIL_LIMIT
        results[str(frame)] = {
            "penetratingCount": count,
            "minimumSignedM": minimum if math.isfinite(minimum) else None,
        }
    return results


def rigid_curve_pass(obj, scene, frame):
    tree = prepare(scene, frame)
    inverse = obj.matrix_world.inverted()
    corrected = 0
    maximum = 0.0
    for curve in obj.data.curves:
        worst = None
        for local_index in range(curve.points_length):
            point = obj.data.points[curve.first_point_index + local_index]
            hit = signed_hit(tree, obj.matrix_world @ point.position)
            if hit is not None and (worst is None or hit[2] < worst[2]):
                worst = hit
        if worst is None or worst[2] >= TARGET:
            continue
        delta = worst[1] * (TARGET - worst[2])
        maximum = max(maximum, delta.length)
        corrected += 1
        for local_index in range(curve.points_length):
            point = obj.data.points[curve.first_point_index + local_index]
            point.position = inverse @ (obj.matrix_world @ point.position + delta)
    obj.data.update_tag()
    return corrected, maximum


def point_pass(obj, scene, frame):
    tree = prepare(scene, frame)
    inverse = obj.matrix_world.inverted()
    corrected = 0
    maximum = 0.0
    for point in obj.data.points:
        world = obj.matrix_world @ point.position
        hit = signed_hit(tree, world)
        if hit is None or hit[2] >= TARGET:
            continue
        delta = hit[1] * (TARGET - hit[2])
        point.position = inverse @ (world + delta)
        corrected += 1
        maximum = max(maximum, delta.length)
    obj.data.update_tag()
    return corrected, maximum


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
hair = bpy.data.objects[HAIR]
before = count_penetrations(hair, scene)
logs = []
max_rigid = 0.0
max_point = 0.0
for pass_index in range(3):
    frame_log = {}
    for frame in FRAMES:
        corrected, maximum = rigid_curve_pass(hair, scene, frame)
        max_rigid = max(max_rigid, maximum)
        frame_log[str(frame)] = {"curvesTranslated": corrected, "maxTranslationMm": maximum * 1000.0}
    logs.append({"kind": "rigid-curve", "pass": pass_index + 1, "frames": frame_log})

for pass_index in range(6):
    frame_log = {}
    total = 0
    for frame in FRAMES:
        corrected, maximum = point_pass(hair, scene, frame)
        max_point = max(max_point, maximum)
        total += corrected
        frame_log[str(frame)] = {"pointsProjected": corrected, "maxProjectionMm": maximum * 1000.0}
    logs.append({"kind": "point-finalize", "pass": pass_index + 1, "frames": frame_log})
    if total == 0:
        break

after = count_penetrations(hair, scene)
passed = all(entry["penetratingCount"] == 0 for entry in after.values())
hair.name = "AevryndFemaleOwnedCurlyHairMain_v249r161"
hair.data.name = hair.name + "Data"
hair["aevrynd_revision"] = "v249r161"
hair["aevrynd_collision_method"] = "rigid curve translation then bounded point projection"
hair["aevrynd_collision_clearance_m"] = TARGET
hair["aevrynd_collision_frames"] = list(FRAMES)
hair["aevrynd_collision_status"] = "PASS" if passed else "FAIL"
scene["aevrynd_revision"] = "v249r161"
scene["aevrynd_candidate_status"] = "VISUAL_REVIEW_PENDING" if passed else "REJECTED_COLLISION"
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE), "output": str(OUTPUT), "hair": hair.name,
    "frames": list(FRAMES), "targetClearanceM": TARGET,
    "before": before, "after": after,
    "maxRigidTranslationMm": max_rigid * 1000.0,
    "maxPointProjectionMm": max_point * 1000.0,
    "passes": logs, "status": "PASS" if passed else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R161_REPAIR=" + json.dumps({
    "output": str(OUTPUT), "before": before, "after": after,
    "maxRigidTranslationMm": max_rigid * 1000.0,
    "maxPointProjectionMm": max_point * 1000.0, "status": report["status"]
}, sort_keys=True))
if not passed:
    raise SystemExit(2)
