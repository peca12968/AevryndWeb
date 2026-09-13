import json
import math
import os
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
BASELINE = Path(os.environ.get("AEVRYND_COLLISION_BASELINE", ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"))
CANDIDATE = Path(os.environ.get("AEVRYND_COLLISION_CANDIDATE", ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-open-topology-physical-skin-r446.blend"))
OUTPUT = Path(os.environ.get("AEVRYND_COLLISION_OUTPUT", ROOT / "assets-source/aevrynd-character/female-v249-mainline-open-topology-physical-skin-r446.collision-audit.json"))
BODY = "AevryndFemaleBodyBaseV118"
MOUTH = ("Lip_Lower", "Lip_Upper", "Mouth_OralCavity", "Mouth_Tongue", "Mouth_UpperTeeth", "Mouth_WetLine")
EYES = tuple(f"Eye_{side}_{part}" for side in ("L", "R") for part in ("Caruncle", "Cornea", "Iris", "Pupil", "Sclera", "TearMeniscus", "UpperLashes"))
HAIR = ("AevryndFemaleCC0LongHairStudyMain_v249r85", "AevryndFemaleCC0LongHairStudyFlyaway_v249r85", "AevryndFemaleDeformMatchedScalp_v249r163")
SOLIDS = (BODY, "Clothing_Bandeau_v160", "Clothing_BandeauBinding_v162", "Clothing_BodyFitShorts_v135")
NEAR = {BODY: 0.025, SOLIDS[1]: 0.010, SOLIDS[2]: 0.010, SOLIDS[3]: 0.010}
LIMIT = -0.0005


def geometry(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return points, faces


def tree(obj, depsgraph):
    points, faces = geometry(obj, depsgraph)
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def face_self_intersections(obj, depsgraph):
    points, faces = geometry(obj, depsgraph)
    bvh = BVHTree.FromPolygons(points, faces, all_triangles=False)
    vertex_sets = [set(face) for face in faces]
    centers = [sum((points[index] for index in face), points[face[0]] * 0.0) / len(face) for face in faces]
    pairs = set()
    for first, second in bvh.overlap(bvh):
        if first == second:
            continue
        pair = tuple(sorted((first, second)))
        if pair in pairs or vertex_sets[first] & vertex_sets[second]:
            continue
        if not any(abs(point.x) < 0.12 and point.y < 0.045 and 1.40 < point.z < 1.64 for point in (centers[first], centers[second])):
            continue
        pairs.add(pair)
    return len(pairs)


def hair_points(obj, depsgraph):
    if obj.type == "MESH":
        return geometry(obj, depsgraph)[0]
    evaluated = obj.evaluated_get(depsgraph)
    return [evaluated.matrix_world @ point.position for point in evaluated.data.points]


def penetration_count(points, target, near):
    count = 0
    for point in points:
        hit = target.find_nearest(point)
        if hit is None or hit[1] is None or hit[3] > near:
            continue
        if (point - hit[0]).dot(hit[1].normalized()) < LIMIT:
            count += 1
    return count


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    frames = {}
    for frame in (1, 20):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        body_tree = tree(bpy.data.objects[BODY], depsgraph)
        layers = {name: len(body_tree.overlap(tree(bpy.data.objects[name], depsgraph))) for name in MOUTH + EYES}
        pairwise = {}
        mouth_trees = {name: tree(bpy.data.objects[name], depsgraph) for name in MOUTH}
        for index, first in enumerate(MOUTH):
            for second in MOUTH[index + 1:]:
                pairwise[f"{first}|{second}"] = len(mouth_trees[first].overlap(mouth_trees[second]))
        solid_trees = {name: tree(bpy.data.objects[name], depsgraph) for name in SOLIDS}
        hair = {}
        for layer in HAIR:
            points = hair_points(bpy.data.objects[layer], depsgraph)
            hair[layer] = {solid: penetration_count(points, solid_trees[solid], NEAR[solid]) for solid in SOLIDS}
        frames[str(frame)] = {"bodyLayerOverlaps": layers, "mouthPairOverlaps": pairwise, "bodyFaceSelfIntersections": face_self_intersections(bpy.data.objects[BODY], depsgraph), "hairPenetrations": hair}
    nonfinite = sum(not all(math.isfinite(value) for value in point.co) for key in bpy.data.objects[BODY].data.shape_keys.key_blocks for point in key.data)
    return {"frames": frames, "nonfiniteShapeKeyPoints": nonfinite}


baseline = snapshot(BASELINE)
candidate = snapshot(CANDIDATE)
regressions = []
for frame in ("1", "20"):
    for category in ("bodyLayerOverlaps", "mouthPairOverlaps"):
        for layer, count in candidate["frames"][frame][category].items():
            previous = baseline["frames"][frame][category][layer]
            if count > previous:
                regressions.append({"frame": frame, "category": category, "layer": layer, "baseline": previous, "candidate": count})
    previous = baseline["frames"][frame]["bodyFaceSelfIntersections"]
    current = candidate["frames"][frame]["bodyFaceSelfIntersections"]
    if current > previous:
        regressions.append({"frame": frame, "category": "bodyFaceSelfIntersections", "baseline": previous, "candidate": current})
    for layer, solids in candidate["frames"][frame]["hairPenetrations"].items():
        for solid, count in solids.items():
            if count:
                regressions.append({"frame": frame, "category": "hairPenetration", "layer": layer, "solid": solid, "candidate": count})
if candidate["nonfiniteShapeKeyPoints"]:
    regressions.append({"category": "nonfiniteShapeKeyPoints", "candidate": candidate["nonfiniteShapeKeyPoints"]})
report = {"baseline": str(BASELINE), "candidate": str(CANDIDATE), "baselineResults": baseline, "candidateResults": candidate, "regressions": regressions, "status": "PASS" if not regressions else "FAIL"}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R446_COLLISION=" + json.dumps({"candidate": str(CANDIDATE), "status": report["status"], "regressions": regressions}, sort_keys=True))
if regressions:
    raise SystemExit(2)
