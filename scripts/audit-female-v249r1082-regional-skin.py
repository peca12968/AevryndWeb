"""Verify the r1082 material-only contract and repeat the four-pose hair clearance gate."""
import hashlib
import json
import struct
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-graded-hairline-r1081-study.blend"
CANDIDATE = ASSETS / "aevrynd-female-cc0-regional-skin-r1082-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1082-regional-skin.audit.json"
BODY = "AevryndFemaleCC0BalancedEyeOptics_R1080"
HAIR = "AevryndFemaleGradedHairlineGroom_R1081"
SCALP = "AevryndFemaleTargetScalp_R976"
FRAMES = (1, 20, 33, 61)


def mesh_digest(obj, positions=True):
    value = hashlib.sha256()
    if positions:
        for vertex in obj.data.vertices:
            value.update(struct.pack("<3f", *vertex.co))
    for polygon in obj.data.polygons:
        for index in polygon.vertices:
            value.update(struct.pack("<I", index))
    return value.hexdigest()


def body_shape_digest(body):
    value = hashlib.sha256()
    for block in body.data.shape_keys.key_blocks:
        value.update(block.name.encode())
        for item in block.data:
            value.update(struct.pack("<3f", *item.co))
    return value.hexdigest()


def weight_digest(body):
    value = hashlib.sha256()
    for vertex in body.data.vertices:
        for item in sorted(vertex.groups, key=lambda x: x.group):
            value.update(struct.pack("<If", item.group, item.weight))
    return value.hexdigest()


def curve_digest(obj):
    value = hashlib.sha256()
    for curve in obj.data.curves:
        value.update(struct.pack("<II", curve.first_point_index, curve.points_length))
    for point in obj.data.points:
        value.update(struct.pack("<3f", *point.position))
    return value.hexdigest()


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = bpy.data.objects[BODY]
    hair = bpy.data.objects[HAIR]
    scalp = bpy.data.objects[SCALP]
    eyes = [f"Eye_{side}_{layer}" for side in ("L", "R") for layer in ("Sclera", "Cornea", "Iris")]
    return {
        "bodyTopology": mesh_digest(body, False),
        "bodyGeometryAndShapeKeys": body_shape_digest(body),
        "bodyWeights": weight_digest(body),
        "shapeKeys": [block.name for block in body.data.shape_keys.key_blocks],
        "eyeGeometry": {name: mesh_digest(bpy.data.objects[name], True) for name in eyes},
        "hairGeometry": curve_digest(hair),
        "hairParent": [hair.parent.name if hair.parent else None, hair.parent_type, hair.parent_bone],
        "scalpGeometry": mesh_digest(scalp, True),
        "scalpParent": [scalp.parent.name if scalp.parent else None, scalp.parent_type, scalp.parent_bone],
        "objectCount": len(bpy.data.objects),
        "bodyMaterialSlots": len(body.data.materials),
        "hairMaterialSlots": len(hair.data.materials),
        "scalpMaterialSlots": len(scalp.data.materials),
    }


source = snapshot(SOURCE)
candidate = snapshot(CANDIDATE)
bpy.ops.wm.open_mainfile(filepath=str(CANDIDATE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
hair = bpy.data.objects[HAIR]
material = body.data.materials[0]
node_names = {node.name for node in material.node_tree.nodes}
frames = {}
for frame in FRAMES:
    scene.frame_set(frame)
    deps = bpy.context.evaluated_depsgraph_get()
    deps.update()
    evaluated_body = body.evaluated_get(deps)
    mesh = evaluated_body.to_mesh()
    vertices = [evaluated_body.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated_body.to_mesh_clear()
    evaluated_hair = hair.evaluated_get(deps)
    signed = []
    for point in evaluated_hair.data.points:
        world = evaluated_hair.matrix_world @ point.position
        hit = tree.find_nearest(world)
        if hit and hit[1] is not None:
            signed.append((world - hit[0]).dot(hit[1].normalized()))
    frames[str(frame)] = {"pointsTested": len(signed), "minimumSignedClearanceM": min(signed), "penetratingPoints": sum(value < -0.00005 for value in signed)}

checks = {
    "bodyTopologyIdentical": source["bodyTopology"] == candidate["bodyTopology"],
    "bodyGeometryAndShapeKeysIdentical": source["bodyGeometryAndShapeKeys"] == candidate["bodyGeometryAndShapeKeys"],
    "bodyWeightsIdentical": source["bodyWeights"] == candidate["bodyWeights"],
    "all35ShapeKeysPreserved": source["shapeKeys"] == candidate["shapeKeys"] and len(candidate["shapeKeys"]) == 35,
    "eyeGeometryIdentical": source["eyeGeometry"] == candidate["eyeGeometry"],
    "hairGeometryIdentical": source["hairGeometry"] == candidate["hairGeometry"],
    "hairBindingIdentical": source["hairParent"] == candidate["hairParent"],
    "scalpGeometryIdentical": source["scalpGeometry"] == candidate["scalpGeometry"],
    "scalpBindingIdentical": source["scalpParent"] == candidate["scalpParent"],
    "objectCountIdentical": source["objectCount"] == candidate["objectCount"] == 27,
    "materialSlotsIdentical": source["bodyMaterialSlots"] == candidate["bodyMaterialSlots"] == 3 and source["hairMaterialSlots"] == candidate["hairMaterialSlots"] == 1 and source["scalpMaterialSlots"] == candidate["scalpMaterialSlots"] == 1,
    "regionalColorAttributePresent": body.data.attributes.get("aevrynd_skin_color_r1082") is not None,
    "regionalRoughnessAttributePresent": body.data.attributes.get("aevrynd_skin_roughness_r1082") is not None,
    "explicitSkinLayersPresent": {"Aevrynd Regional Complexion R1082", "Aevrynd TZone Cheek Roughness R1082", "Aevrynd Fine Chromatic Mottle R1082", "Aevrynd Secondary Micro Pore Normal R1082"}.issubset(node_names),
    "fourFrameHairClearancePass": all(item["penetratingPoints"] == 0 and item["minimumSignedClearanceM"] >= 0.00159 for item in frames.values()),
}
report = {
    "revision": "v249r1082-regional-skin-audit",
    "source": str(SOURCE),
    "candidate": str(CANDIDATE),
    "sourceSummary": source,
    "candidateSummary": candidate,
    "skinMaterial": {"name": material.name, "nodeCount": len(material.node_tree.nodes), "layerNodes": sorted(name for name in node_names if "R1082" in name)},
    "fourFrameHairBodyClearance": frames,
    "checks": checks,
    "drawCallDelta": 0,
    "status": "PASS" if all(checks.values()) else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1082_SKIN_AUDIT=" + json.dumps({"status": report["status"], "frames": frames, "checks": checks}, sort_keys=True))
if report["status"] != "PASS":
    raise SystemExit(2)
