"""Validate the r1035 topology study across rig frames and expression stacking."""

import json
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
CANDIDATE = ASSETS / "aevrynd-female-cc0-contiguous-mouth-aperture-r1035-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1035-mouth-dynamic-audit.json"
BODY = "AevryndFemaleCC0Baseline_v259"
FRAMES = (1, 20, 33, 61)
EXPRESSIONS = ("Aevrynd_MouthOpenTest_R1030", "Aevrynd_SmileTest_R1030")
ORAL_LAYERS = (
    "Aevrynd_OralBackWall_R1035", "Aevrynd_UpperGum_R1035", "Aevrynd_LowerGum_R1035",
    "Aevrynd_UpperTeeth_R1035", "Aevrynd_LowerTeeth_R1035", "Aevrynd_Tongue_R1035",
)
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
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    tree, triangles = world_tree(body, depsgraph)
    pairs = [(first, second) for first, second in tree.overlap(tree) if first < second and set(triangles[first]).isdisjoint(triangles[second])]
    return {"nonAdjacentPairs": len(pairs), "samplePairs": [list(pair) for pair in pairs[:24]], "status": "PASS" if not pairs else "FAIL"}


def layer_collisions(body, layers):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    body_tree, _ = world_tree(body, depsgraph)
    trees = {}
    body_counts = {}
    for obj in layers:
        tree, _ = world_tree(obj, depsgraph)
        trees[obj.name] = tree
        body_counts[obj.name] = len(body_tree.overlap(tree))
    pair_counts = {}
    for first_index, first in enumerate(layers):
        for second in layers[first_index + 1:]:
            pair_counts[first.name + "::" + second.name] = len(trees[first.name].overlap(trees[second.name]))
    return body_counts, pair_counts


bpy.ops.wm.open_mainfile(filepath=str(CANDIDATE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
layers = [bpy.data.objects[name] for name in ORAL_LAYERS]
frames = {}
failures = []
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    body_self = self_collision(body)
    body_oral, oral_pairs = layer_collisions(body, layers)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    body_tree, _ = world_tree(body, depsgraph)
    attachments = {}
    for name in FACE_ATTACHMENTS:
        if name not in bpy.data.objects:
            continue
        tree, _ = world_tree(bpy.data.objects[name], depsgraph)
        attachments[name] = len(body_tree.overlap(tree))
    frames[str(frame)] = {"bodySelfCollision": body_self, "bodyOralLayerOverlap": body_oral, "oralInterLayerOverlap": oral_pairs, "bodyFaceAttachmentOverlap": attachments}
    if body_self["status"] != "PASS":
        failures.append({"frame": frame, "gate": "bodySelfCollision", "count": body_self["nonAdjacentPairs"]})
    for gate, values in (("bodyOralLayerOverlap", body_oral), ("oralInterLayerOverlap", oral_pairs), ("bodyFaceAttachmentOverlap", attachments)):
        for name, count in values.items():
            if count:
                failures.append({"frame": frame, "gate": gate, "object": name, "count": count})

scene.frame_set(1)
blocks = body.data.shape_keys.key_blocks
expressions = {}
for expression in EXPRESSIONS:
    block = blocks.get(expression)
    if block is None:
        expressions[expression] = {"status": "FAIL_MISSING_KEY"}
        failures.append({"expression": expression, "gate": "missingKey"})
        continue
    previous = float(block.value)
    block.value = 1.0
    bpy.context.view_layer.update()
    body_self = self_collision(body)
    body_oral, oral_pairs = layer_collisions(body, layers)
    expressions[expression] = {"bodySelfCollision": body_self, "bodyOralLayerOverlap": body_oral, "oralInterLayerOverlap": oral_pairs}
    if body_self["status"] != "PASS":
        failures.append({"expression": expression, "gate": "bodySelfCollision", "count": body_self["nonAdjacentPairs"]})
    for gate, values in (("bodyOralLayerOverlap", body_oral), ("oralInterLayerOverlap", oral_pairs)):
        for name, count in values.items():
            if count:
                failures.append({"expression": expression, "gate": gate, "object": name, "count": count})
    block.value = previous

report = {
    "candidate": str(CANDIDATE),
    "sceneRevision": scene.get("aevrynd_mainline_revision"),
    "websitePromotion": scene.get("aevrynd_website_promotion"),
    "frames": frames,
    "expressions": expressions,
    "failures": failures,
    "bodyTopology": {"vertices": len(body.data.vertices), "edges": len(body.data.edges), "polygons": len(body.data.polygons)},
    "shapeKeys": len(blocks),
    "materialSlots": len(body.data.materials),
    "oralLayers": list(ORAL_LAYERS),
    "status": "PASS" if not failures else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1035_DYNAMIC_AUDIT=" + json.dumps({"status": report["status"], "failures": len(failures), "frameSelfPairs": {frame: item["bodySelfCollision"]["nonAdjacentPairs"] for frame, item in frames.items()}, "expressionSelfPairs": {name: item.get("bodySelfCollision", {}).get("nonAdjacentPairs") for name, item in expressions.items()}, "shapeKeys": len(blocks)}, sort_keys=True))
