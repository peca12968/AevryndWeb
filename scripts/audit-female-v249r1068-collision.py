"""Audit the r1060 transferred smooth-mouth body across pose and expression gates."""

import json
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
CANDIDATE = ASSETS / "aevrynd-female-cc0-exact-edge-support-r1068-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1068-exact-edge-support.collision-audit.json"
BODY = "AevryndFemaleCC0ExactEdgeSupport_R1068"
EXPRESSIONS = ("Aevrynd_MouthOpenTest_R1030", "Aevrynd_SmileTest_R1030")
FRAMES = (1, 20, 33, 61)
FACE_ATTACHMENTS = (
    "Brow_L", "Brow_L_Density", "Brow_R", "Brow_R_Density",
    "Eye_L_Sclera", "Eye_L_Cornea", "Eye_L_UpperLashes", "Eye_L_LowerLashes",
    "Eye_R_Sclera", "Eye_R_Cornea", "Eye_R_UpperLashes", "Eye_R_LowerLashes",
    "Eye_L_MedialCaruncle_R1023", "Eye_R_MedialCaruncle_R1023",
)


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


bpy.ops.wm.open_mainfile(filepath=str(CANDIDATE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
blocks = body.data.shape_keys.key_blocks

weight_sums = []
zero_weight_vertices = 0
for vertex in body.data.vertices:
    total = sum(membership.weight for membership in vertex.groups)
    weight_sums.append(total)
    if total < 1e-8:
        zero_weight_vertices += 1

frame_self = {}
frame_attachments = {}
failures = []
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    frame_self[str(frame)] = body_self_collision(body)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree, _ = world_tree(body, depsgraph)
    attachments = {}
    for name in FACE_ATTACHMENTS:
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        other_tree, _ = world_tree(obj, depsgraph)
        count = len(body_tree.overlap(other_tree))
        attachments[name] = count
        if count:
            failures.append({"frame": frame, "object": name, "triangleOverlapCount": count})
    frame_attachments[str(frame)] = attachments

scene.frame_set(1)
expression_self = {}
stored_expression_values = {name: blocks[name].value for name in EXPRESSIONS}
for name in EXPRESSIONS:
    for reset in EXPRESSIONS:
        blocks[reset].value = 0.0
    blocks[name].value = 1.0
    bpy.context.view_layer.update()
    expression_self[name] = body_self_collision(body)
for name, value in stored_expression_values.items():
    blocks[name].value = value

report = {
    "revision": "v249r1068-exact-edge-support-collision",
    "candidate": str(CANDIDATE),
    "body": BODY,
    "bodyTopology": {
        "vertices": len(body.data.vertices),
        "edges": len(body.data.edges),
        "polygons": len(body.data.polygons),
    },
    "shapeKeys": len(blocks),
    "deformWeights": {
        "zeroWeightVertices": zero_weight_vertices,
        "minimumSum": min(weight_sums),
        "maximumSum": max(weight_sums),
    },
    "fourFrameBodySelfCollision": frame_self,
    "fourFrameBodyAttachmentCollision": frame_attachments,
    "attachmentFailures": failures,
    "expressionSelfCollision": expression_self,
}
checks = [len(blocks) == 35, zero_weight_vertices == 0, not failures]
checks.extend(item["status"] == "PASS" for item in frame_self.values())
checks.extend(item["status"] == "PASS" for item in expression_self.values())
report["status"] = "PASS" if all(checks) else "FAIL"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1068_COLLISION=" + json.dumps({
    "status": report["status"],
    "selfPairs": {frame: item["nonAdjacentPairs"] for frame, item in frame_self.items()},
    "expressionPairs": {name: item["nonAdjacentPairs"] for name, item in expression_self.items()},
    "attachmentFailures": len(failures),
    "shapeKeys": len(blocks),
    "zeroWeightVertices": zero_weight_vertices,
}, sort_keys=True))


