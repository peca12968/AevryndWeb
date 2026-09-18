"""Audit the selected r1078 eyelid-wall candidate across pose and expression gates."""
import json
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
CANDIDATE = ASSETS / "aevrynd-female-cc0-eyelid-inner-wall-r1078-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1078-eyelid-inner-wall.collision-audit.json"
BODY = "AevryndFemaleCC0EyelidInnerWall_R1078"
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


def self_collision(body):
    depsgraph = bpy.context.evaluated_depsgraph_get(); depsgraph.update()
    tree, triangles = world_tree(body, depsgraph)
    pairs = [(a, b) for a, b in tree.overlap(tree) if a < b and set(triangles[a]).isdisjoint(triangles[b])]
    return {"nonAdjacentPairs": len(pairs), "samplePairs": [list(pair) for pair in pairs[:24]], "status": "PASS" if not pairs else "FAIL"}


bpy.ops.wm.open_mainfile(filepath=str(CANDIDATE))
scene, body = bpy.context.scene, bpy.data.objects[BODY]
blocks = body.data.shape_keys.key_blocks
zero_weights = sum(1 for vertex in body.data.vertices if sum(item.weight for item in vertex.groups) < 1e-8)
frames, attachments, failures = {}, {}, []
for frame in FRAMES:
    scene.frame_set(frame); bpy.context.view_layer.update()
    frames[str(frame)] = self_collision(body)
    depsgraph = bpy.context.evaluated_depsgraph_get(); body_tree, _ = world_tree(body, depsgraph)
    attachments[str(frame)] = {}
    for name in FACE_ATTACHMENTS:
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        count = len(body_tree.overlap(world_tree(obj, depsgraph)[0]))
        attachments[str(frame)][name] = count
        if count:
            failures.append({"frame": frame, "object": name, "triangleOverlapCount": count})

scene.frame_set(1)
expressions = {}
stored = {name: blocks[name].value for name in EXPRESSIONS}
for name in EXPRESSIONS:
    for reset in EXPRESSIONS: blocks[reset].value = 0.0
    blocks[name].value = 1.0; bpy.context.view_layer.update()
    expressions[name] = self_collision(body)
for name, value in stored.items(): blocks[name].value = value

checks = [len(blocks) == 35, zero_weights == 0, not failures]
checks += [item["status"] == "PASS" for item in frames.values()]
checks += [item["status"] == "PASS" for item in expressions.values()]
report = {
    "revision": "v249r1078-eyelid-inner-wall-collision", "candidate": str(CANDIDATE), "body": BODY,
    "bodyTopology": {"vertices": len(body.data.vertices), "edges": len(body.data.edges), "polygons": len(body.data.polygons)},
    "shapeKeys": len(blocks), "zeroWeightVertices": zero_weights,
    "fourFrameBodySelfCollision": frames, "fourFrameBodyAttachmentCollision": attachments,
    "attachmentFailures": failures, "expressionSelfCollision": expressions,
    "status": "PASS" if all(checks) else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1078_COLLISION=" + json.dumps({"status": report["status"], "selfPairs": {k:v["nonAdjacentPairs"] for k,v in frames.items()}, "expressionPairs": {k:v["nonAdjacentPairs"] for k,v in expressions.items()}, "attachmentFailures": len(failures), "zeroWeightVertices": zero_weights}, sort_keys=True))
