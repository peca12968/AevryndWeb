import json
import os
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("AEVRYND_TEAR_DIAGNOSTIC_SOURCE", ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-masked-upper-lid-r207.blend"))
REPORT = Path(os.environ.get("AEVRYND_TEAR_DIAGNOSTIC_OUTPUT", ROOT / "assets-source/aevrynd-character/female-v249-mainline-tear-overlap-r208.diagnostic.json"))
BODY = "AevryndFemaleBodyBaseV118"
TEARS = ("Eye_L_TearMeniscus", "Eye_R_TearMeniscus")


def geometry(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return points, faces


def center(points, face):
    return sum((points[index] for index in face), points[face[0]] * 0.0) / len(face)


def overlap_detail(first_obj, second_obj, depsgraph):
    first_points, first_faces = geometry(first_obj, depsgraph)
    second_points, second_faces = geometry(second_obj, depsgraph)
    first_tree = BVHTree.FromPolygons(first_points, first_faces, all_triangles=False)
    second_tree = BVHTree.FromPolygons(second_points, second_faces, all_triangles=False)
    pairs = first_tree.overlap(second_tree)
    first_indices = sorted(set(pair[0] for pair in pairs))
    second_indices = sorted(set(pair[1] for pair in pairs))
    first_centers = [center(first_points, first_faces[index]) for index in first_indices]
    second_centers = [center(second_points, second_faces[index]) for index in second_indices]

    def bounds(values):
        if not values:
            return None
        return {
            "min": [min(value[axis] for value in values) for axis in range(3)],
            "max": [max(value[axis] for value in values) for axis in range(3)],
        }

    return {
        "pairCount": len(pairs),
        "bodyFaces": first_indices,
        "tearFaces": second_indices,
        "bodyFaceCenterBounds": bounds(first_centers),
        "tearFaceCenterBounds": bounds(second_centers),
        "bodyFaceCenters": [list(value) for value in first_centers],
        "tearFaceCenters": [list(value) for value in second_centers],
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
report = {"source": str(SOURCE), "frames": {}}
for frame in (1, 20):
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    report["frames"][str(frame)] = {
        name: overlap_detail(bpy.data.objects[BODY], bpy.data.objects[name], depsgraph)
        for name in TEARS
    }
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R208_TEAR_OVERLAP=" + json.dumps({
    frame: {name: detail["pairCount"] for name, detail in layers.items()}
    for frame, layers in report["frames"].items()
}, sort_keys=True))
