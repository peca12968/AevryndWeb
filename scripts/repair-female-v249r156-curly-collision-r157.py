import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-curly-r156.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-curly-collision-r157.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-owned-curly-collision-r157.repair-report.json"
BODY = "AevryndFemaleBodyBaseV118"
HAIR = "AevryndFemaleOwnedCurlyHairMain_v249r156"
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


def frame_tree(scene, frame):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    return evaluated_tree(bpy.data.objects[BODY], bpy.context.evaluated_depsgraph_get())


def count_penetrations(obj, scene):
    results = {}
    for frame in FRAMES:
        tree = frame_tree(scene, frame)
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


def project_multiframe(obj, scene):
    inverse = obj.matrix_world.inverted()
    maximum = 0.0
    corrected = 0
    pass_log = []
    for pass_index in range(8):
        pass_corrected = 0
        pass_maximum = 0.0
        for frame in FRAMES:
            tree = frame_tree(scene, frame)
            for point in obj.data.points:
                world = obj.matrix_world @ point.position
                hit = signed_hit(tree, world)
                if hit is None or hit[2] >= TARGET:
                    continue
                delta = hit[1] * (TARGET - hit[2])
                point.position = inverse @ (world + delta)
                pass_corrected += 1
                pass_maximum = max(pass_maximum, delta.length)
        obj.data.update_tag()
        corrected += pass_corrected
        maximum = max(maximum, pass_maximum)
        remaining = count_penetrations(obj, scene)
        pass_log.append({
            "pass": pass_index + 1,
            "correctedOperations": pass_corrected,
            "maxCorrectionMm": pass_maximum * 1000.0,
            "remaining": remaining,
        })
        if all(entry["penetratingCount"] == 0 for entry in remaining.values()):
            break
    return corrected, maximum, pass_log


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
hair = bpy.data.objects[HAIR]
before = count_penetrations(hair, scene)
corrected, maximum, passes = project_multiframe(hair, scene)
after = count_penetrations(hair, scene)
passed = all(entry["penetratingCount"] == 0 for entry in after.values())

hair.name = "AevryndFemaleOwnedCurlyHairMain_v249r157"
hair.data.name = hair.name + "Data"
hair["aevrynd_revision"] = "v249r157"
hair["aevrynd_collision_clearance_m"] = TARGET
hair["aevrynd_collision_frames"] = list(FRAMES)
hair["aevrynd_collision_status"] = "PASS" if passed else "FAIL"
scene["aevrynd_revision"] = "v249r157"
scene["aevrynd_candidate_status"] = "VISUAL_REVIEW_PENDING" if passed else "REJECTED_COLLISION"
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "hair": hair.name,
    "frames": list(FRAMES),
    "targetClearanceM": TARGET,
    "before": before,
    "after": after,
    "correctedOperations": corrected,
    "maxSingleCorrectionMm": maximum * 1000.0,
    "passes": passes,
    "status": "PASS" if passed else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R157_REPAIR=" + json.dumps({
    "output": str(OUTPUT),
    "before": before,
    "after": after,
    "maxSingleCorrectionMm": maximum * 1000.0,
    "status": report["status"],
}, sort_keys=True))
if not passed:
    raise SystemExit(2)
