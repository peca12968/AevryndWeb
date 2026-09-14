import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-sorted-tear-film-r499.blend"
REPORT = ASSETS / "female-v249-mainline-upper-lash-fibers-r499.inspection.json"
BODY = "AevryndFemaleBodyBaseV118"


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
body_tree = world_tree(bpy.data.objects[BODY], depsgraph)
report = {"source": str(SOURCE), "sides": {}}
for side in ("L", "R"):
    obj = bpy.data.objects[f"Eye_{side}_UpperLashes"]
    if len(obj.data.vertices) % 20:
        raise RuntimeError(f"Unexpected {obj.name} vertex count")
    fibers = []
    for fiber_index in range(len(obj.data.vertices) // 20):
        rings = []
        for row in range(5):
            local = sum((obj.data.vertices[fiber_index * 20 + row * 4 + column].co for column in range(4)), Vector()) / 4.0
            world = obj.matrix_world @ local
            nearest = body_tree.find_nearest(world)
            rings.append({
                "local": list(local),
                "world": list(world),
                "bodyDistanceM": nearest[3] if nearest else None,
            })
        root_row = min(range(5), key=lambda row: rings[row]["bodyDistanceM"])
        tip_row = max(range(5), key=lambda row: rings[row]["bodyDistanceM"])
        root = Vector(rings[root_row]["world"])
        tip = Vector(rings[tip_row]["world"])
        fibers.append({
            "index": fiber_index,
            "rootRow": root_row,
            "tipRow": tip_row,
            "rootWorld": list(root),
            "tipWorld": list(tip),
            "rootBodyDistanceM": rings[root_row]["bodyDistanceM"],
            "tipBodyDistanceM": rings[tip_row]["bodyDistanceM"],
            "rootToTipM": (tip - root).length,
            "rings": rings,
        })
    report["sides"][side] = {
        "object": obj.name,
        "vertices": len(obj.data.vertices),
        "polygons": len(obj.data.polygons),
        "fibers": fibers,
        "rootRows": sorted(set(fiber["rootRow"] for fiber in fibers)),
        "tipRows": sorted(set(fiber["tipRow"] for fiber in fibers)),
    }
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R499_UPPER_LASH_FIBERS=" + json.dumps({side: {
    "fibers": len(value["fibers"]),
    "rootRows": value["rootRows"],
    "tipRows": value["tipRows"],
    "lengthRangeM": [min(fiber["rootToTipM"] for fiber in value["fibers"]), max(fiber["rootToTipM"] for fiber in value["fibers"])],
} for side, value in report["sides"].items()}, sort_keys=True))
