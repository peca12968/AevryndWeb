"""Audit the selected r1033 mouth candidate across pose and expression gates."""

import json
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-soft-lip-boundary-r1032-study.blend"
CANDIDATE = ASSETS / "aevrynd-female-cc0-lower-lip-rim-turn-r1033-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1033-mouth-collision-audit.json"
BODY = "AevryndFemaleCC0Baseline_v259"
RIM_KEY = "Aevrynd_LowerLipRimTurn_R1033"
EXPRESSIONS = ("Aevrynd_MouthOpenTest_R1030", "Aevrynd_SmileTest_R1030")
FRAMES = (1, 20, 33, 61)
FACE_ATTACHMENTS = (
    "Brow_L", "Brow_L_Density", "Brow_R", "Brow_R_Density",
    "Eye_L_Sclera", "Eye_L_Cornea", "Eye_L_UpperLashes", "Eye_L_LowerLashes",
    "Eye_R_Sclera", "Eye_R_Cornea", "Eye_R_UpperLashes", "Eye_R_LowerLashes",
    "Eye_L_MedialCaruncle_R1023", "Eye_R_MedialCaruncle_R1023",
)


def mixed_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    coordinates = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        for index, coordinate in enumerate(coordinates):
            coordinate += block.value * (block.data[index].co - block.relative_key.data[index].co)
    return coordinates


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles()
    triangles = [tuple(triangle.vertices) for triangle in mesh.loop_triangles]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, triangles, all_triangles=True), triangles


def body_self_collision(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    tree, triangles = world_tree(body, depsgraph)
    disjoint = []
    for first, second in tree.overlap(tree):
        if first < second and set(triangles[first]).isdisjoint(triangles[second]):
            disjoint.append((first, second))
    return {
        "nonAdjacentPairs": len(disjoint),
        "samplePairs": [list(pair) for pair in disjoint[:24]],
        "status": "PASS" if not disjoint else "FAIL",
    }


def collect_mixed(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    body = bpy.data.objects[BODY]
    return mixed_coordinates(body), body.matrix_world.copy()


source_coordinates, source_matrix = collect_mixed(SOURCE)
bpy.ops.wm.open_mainfile(filepath=str(CANDIDATE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY]
candidate_coordinates = mixed_coordinates(body)
candidate_matrix = body.matrix_world.copy()

ratios = []
for edge in body.data.edges:
    first, second = edge.vertices
    old_a = source_matrix @ source_coordinates[first]
    old_b = source_matrix @ source_coordinates[second]
    new_a = candidate_matrix @ candidate_coordinates[first]
    new_b = candidate_matrix @ candidate_coordinates[second]
    center = (old_a + old_b) * 0.5
    if abs(center.x) > 0.058 or center.y > -0.090 or not (1.342 < center.z < 1.416):
        continue
    old_length = (old_a - old_b).length
    if old_length > 1e-9:
        ratios.append((new_a - new_b).length / old_length)

frame_self = {}
frame_attachments = {}
failures = []
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    frame_self[str(frame)] = body_self_collision(body)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    body_tree, _ = world_tree(body, depsgraph)
    values = {}
    for name in FACE_ATTACHMENTS:
        if name not in bpy.data.objects:
            continue
        other_tree, _ = world_tree(bpy.data.objects[name], depsgraph)
        count = len(body_tree.overlap(other_tree))
        values[name] = count
        if count:
            failures.append({"frame": frame, "object": name, "triangleOverlapCount": count})
    frame_attachments[str(frame)] = values

scene.frame_set(1)
blocks = body.data.shape_keys.key_blocks
expression_self = {}
for name in EXPRESSIONS:
    block = blocks.get(name)
    if block is None:
        expression_self[name] = {"status": "FAIL_MISSING_KEY"}
        continue
    previous = float(block.value)
    block.value = 1.0
    bpy.context.view_layer.update()
    expression_self[name] = body_self_collision(body)
    block.value = previous

edge_report = {
    "edgeCount": len(ratios),
    "minimum": min(ratios),
    "maximum": max(ratios),
    "mean": sum(ratios) / len(ratios),
    "threshold": [0.30, 2.50],
}
edge_report["status"] = "PASS" if edge_report["minimum"] >= 0.30 and edge_report["maximum"] <= 2.50 else "FAIL"
keys = blocks
report = {
    "source": str(SOURCE),
    "candidate": str(CANDIDATE),
    "sceneRevision": scene.get("aevrynd_mainline_revision"),
    "sceneParent": scene.get("aevrynd_mainline_parent"),
    "websitePromotion": scene.get("aevrynd_website_promotion"),
    "selectedRimKey": {"name": RIM_KEY, "value": float(keys[RIM_KEY].value)},
    "mouthEdgeRatiosVersusR1032": edge_report,
    "fourFrameBodySelfCollision": frame_self,
    "fourFrameBodyAttachmentCollision": frame_attachments,
    "attachmentFailures": failures,
    "expressionSelfCollision": expression_self,
    "bodyTopology": {
        "vertices": len(body.data.vertices),
        "edges": len(body.data.edges),
        "polygons": len(body.data.polygons),
    },
    "materialSlots": len(body.material_slots),
    "shapeKeys": len(keys),
}
checks = [edge_report["status"] == "PASS", not failures]
checks.extend(item["status"] == "PASS" for item in frame_self.values())
checks.extend(item.get("status") == "PASS" for item in expression_self.values())
report["status"] = "PASS" if all(checks) else "FAIL"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1033_MOUTH_AUDIT=" + json.dumps({
    "status": report["status"],
    "edge": edge_report,
    "selfPairs": {frame: item["nonAdjacentPairs"] for frame, item in frame_self.items()},
    "attachmentFailures": len(failures),
    "expressionPairs": {name: item.get("nonAdjacentPairs") for name, item in expression_self.items()},
    "shapeKeys": len(keys),
}, sort_keys=True))
