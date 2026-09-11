import json
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-recessed-natural-eyes-r301.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-eyelid-control-ring-r310.study.json"
BODY = "AevryndFemaleBody_CC0_R249"
EYES = {"L": (0.034528, 1.607765), "R": (-0.034443, 1.607765)}


def tree_for(obj):
    vertices = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    polygons = [tuple(polygon.vertices) for polygon in obj.data.polygons]
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY]
neighbors = {vertex.index: set() for vertex in body.data.vertices}
for edge in body.data.edges:
    a, b = edge.vertices
    neighbors[a].add(b)
    neighbors[b].add(a)

result = {}
for side, (cx, cz) in EYES.items():
    sclera = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
    tree = tree_for(sclera)
    rows = []
    for vertex in body.data.vertices:
        world = body.matrix_world @ vertex.co
        if abs(world.x - cx) > 0.022 or abs(world.z - cz) > 0.014 or world.y > -0.120:
            continue
        nearest, normal, _face, distance = tree.find_nearest(world)
        if nearest is None:
            continue
        signed = (world - nearest).dot(normal.normalized())
        rows.append({
            "index": vertex.index,
            "world": list(world),
            "scleraDistanceM": distance,
            "scleraSignedM": signed,
            "valence": len(neighbors[vertex.index]),
            "neighbors": sorted(neighbors[vertex.index]),
        })
    rows.sort(key=lambda row: row["scleraDistanceM"])
    result[side] = {
        "candidateCount": len(rows),
        "within1mm": sum(row["scleraDistanceM"] <= 0.001 for row in rows),
        "within2mm": sum(row["scleraDistanceM"] <= 0.002 for row in rows),
        "within3mm": sum(row["scleraDistanceM"] <= 0.003 for row in rows),
        "candidates": rows,
    }

report = {"source": str(SOURCE), "body": BODY, "eyes": result, "status": "CONTROL_RING_CANDIDATES_READY"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R310_EYELID_CONTROL_RING=" + json.dumps({side: {key: value for key, value in rows.items() if key != "candidates"} for side, rows in result.items()}, sort_keys=True))
