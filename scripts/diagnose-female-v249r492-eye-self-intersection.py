import json
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
BASELINE = ASSETS / "aevrynd-female-authoring-v249-mainline-balanced-skin-r491.blend"
CANDIDATE = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-eye-aperture-r492.blend"
REPORT = ASSETS / "female-v249-mainline-natural-eye-aperture-r492.self-intersection-diagnostic.json"
BODY = "AevryndFemaleBodyBaseV118"


def snapshot(path, frame):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj = bpy.data.objects[BODY]
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    surface = BVHTree.FromPolygons(points, faces, all_triangles=False)
    face_sets = [set(face) for face in faces]
    pairs = {
        (first, second) if first < second else (second, first)
        for first, second in surface.overlap(surface)
        if first != second and not face_sets[first].intersection(face_sets[second])
    }
    evaluated.to_mesh_clear()
    return points, faces, pairs


report = {"baseline": str(BASELINE), "candidate": str(CANDIDATE), "frames": {}}
for frame in (1, 20):
    _base_points, _base_faces, baseline_pairs = snapshot(BASELINE, frame)
    points, faces, candidate_pairs = snapshot(CANDIDATE, frame)
    added = sorted(candidate_pairs - baseline_pairs)
    report["frames"][str(frame)] = {
        "baselinePairs": len(baseline_pairs),
        "candidatePairs": len(candidate_pairs),
        "added": [
            {
                "faces": [first, second],
                "vertices": [list(faces[first]), list(faces[second])],
                "centers": [
                    list(sum((points[index] for index in faces[face]), points[faces[face][0]] * 0.0) / len(faces[face]))
                    for face in (first, second)
                ],
            }
            for first, second in added
        ],
    }
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R492_SELF_DIAGNOSTIC=" + json.dumps(report["frames"], sort_keys=True))
