import json
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cornea-response-r175.blend"
CANDIDATE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-soft-clearance-lids-r182.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-soft-clearance-lids-r182.self-intersection-diagnostic.json"
BODY = "AevryndFemaleBodyBaseV118"


def pairs(path, frame):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj = bpy.data.objects[BODY].evaluated_get(depsgraph)
    mesh = obj.to_mesh()
    points = [obj.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    bvh = BVHTree.FromPolygons(points, faces, all_triangles=False)
    vertex_sets = [set(face) for face in faces]
    centers = [sum((points[index] for index in face), points[face[0]] * 0.0) / len(face) for face in faces]
    found = {}
    for first, second in bvh.overlap(bvh):
        pair = tuple(sorted((first, second)))
        if first == second or pair in found or vertex_sets[first] & vertex_sets[second]:
            continue
        if not any(abs(point.x) < 0.12 and point.y < 0.045 and 1.40 < point.z < 1.64 for point in (centers[first], centers[second])):
            continue
        found[pair] = [tuple(centers[first]), tuple(centers[second])]
    obj.to_mesh_clear()
    return found


report = {"baseline": str(BASELINE), "candidate": str(CANDIDATE), "frames": {}}
for frame in (1, 20):
    before = pairs(BASELINE, frame)
    after = pairs(CANDIDATE, frame)
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    report["frames"][str(frame)] = {
        "baselineCount": len(before), "candidateCount": len(after),
        "added": [{"polygons": pair, "centers": after[pair]} for pair in added],
        "removed": [{"polygons": pair, "centers": before[pair]} for pair in removed],
    }
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R182_SELF_INTERSECTION_DIAGNOSTIC=" + json.dumps(report, sort_keys=True))
