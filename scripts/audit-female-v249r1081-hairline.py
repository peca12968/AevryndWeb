"""Audit r1081 hair/body clearance and preservation of the r1080 character contract."""
import hashlib
import json
import struct
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-balanced-eye-optics-r1080-study.blend"
CANDIDATE = ASSETS / "aevrynd-female-cc0-graded-hairline-r1081-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1081-graded-hairline.audit.json"
BODY = "AevryndFemaleCC0BalancedEyeOptics_R1080"
SOURCE_HAIR = "AevryndFemaleCoherentClumpGroom_R981"
CANDIDATE_HAIR = "AevryndFemaleGradedHairlineGroom_R1081"
SCALP = "AevryndFemaleTargetScalp_R976"
FRAMES = (1, 20, 33, 61)


def digest_mesh(obj, include_positions=True):
    value = hashlib.sha256()
    if include_positions:
        for vertex in obj.data.vertices:
            value.update(struct.pack("<3f", *vertex.co))
    for polygon in obj.data.polygons:
        for index in polygon.vertices:
            value.update(struct.pack("<I", index))
    return value.hexdigest()


def body_digest(body):
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


def snapshot(path, hair_name):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = bpy.data.objects[BODY]
    hair = bpy.data.objects[hair_name]
    scalp = bpy.data.objects[SCALP]
    eye_names = [f"Eye_{side}_{layer}" for side in ("L", "R") for layer in ("Sclera", "Cornea", "Iris")]
    return {
        "bodyGeometry": body_digest(body),
        "bodyWeights": weight_digest(body),
        "bodyTopology": digest_mesh(body, False),
        "bodyShapeKeys": [block.name for block in body.data.shape_keys.key_blocks],
        "eyeGeometry": {name: digest_mesh(bpy.data.objects[name], True) for name in eye_names},
        "eyeTopology": {name: digest_mesh(bpy.data.objects[name], False) for name in eye_names},
        "objectCount": len(bpy.data.objects),
        "hair": {
            "curves": len(hair.data.curves),
            "points": len(hair.data.points),
            "materialSlots": len(hair.data.materials),
            "modifiers": len(hair.modifiers),
        },
        "scalp": {
            "vertices": len(scalp.data.vertices),
            "faces": len(scalp.data.polygons),
            "topology": digest_mesh(scalp, False),
            "materialSlots": len(scalp.data.materials),
        },
    }


source = snapshot(SOURCE, SOURCE_HAIR)
candidate = snapshot(CANDIDATE, CANDIDATE_HAIR)

bpy.ops.wm.open_mainfile(filepath=str(CANDIDATE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
hair = bpy.data.objects[CANDIDATE_HAIR]
scalp = bpy.data.objects[SCALP]
clearance = float(hair.get("aevrynd_collision_clearance_m", 0.0016))
frames = {}

for frame in FRAMES:
    scene.frame_set(frame)
    deps = bpy.context.evaluated_depsgraph_get()
    deps.update()
    evaluated_body = body.evaluated_get(deps)
    body_mesh = evaluated_body.to_mesh()
    body_vertices = [evaluated_body.matrix_world @ vertex.co for vertex in body_mesh.vertices]
    body_faces = [tuple(poly.vertices) for poly in body_mesh.polygons]
    body_tree = BVHTree.FromPolygons(body_vertices, body_faces, all_triangles=False)
    evaluated_hair = hair.evaluated_get(deps)
    points = [evaluated_hair.matrix_world @ point.position for point in evaluated_hair.data.points]
    signed = []
    for point in points:
        hit = body_tree.find_nearest(point)
        if hit and hit[1] is not None:
            signed.append((point - hit[0]).dot(hit[1].normalized()))
    evaluated_body.to_mesh_clear()
    frames[str(frame)] = {
        "pointsTested": len(signed),
        "minimumSignedClearanceM": min(signed),
        "penetratingPoints": sum(value < -0.00005 for value in signed),
        "subHalfMillimeterClearancePoints": sum(value < 0.0005 for value in signed),
        "targetClearanceM": clearance,
    }

fade = scalp.data.attributes.get("aevrynd_hairline_fade_r1081")
checks = {
    "bodyGeometryIdentical": source["bodyGeometry"] == candidate["bodyGeometry"],
    "bodyWeightsIdentical": source["bodyWeights"] == candidate["bodyWeights"],
    "bodyTopologyIdentical": source["bodyTopology"] == candidate["bodyTopology"],
    "bodyShapeKeysIdentical": source["bodyShapeKeys"] == candidate["bodyShapeKeys"] and len(candidate["bodyShapeKeys"]) == 35,
    "eyeGeometryIdentical": source["eyeGeometry"] == candidate["eyeGeometry"],
    "eyeTopologyIdentical": source["eyeTopology"] == candidate["eyeTopology"],
    "objectCountIdentical": source["objectCount"] == candidate["objectCount"] == 27,
    "hairMaterialSlotsIdentical": source["hair"]["materialSlots"] == candidate["hair"]["materialSlots"] == 1,
    "hairObjectCountUnchanged": candidate["hair"]["curves"] == source["hair"]["curves"] + 130,
    "hairPointDeltaExpected": candidate["hair"]["points"] == source["hair"]["points"] + 1040,
    "scalpTopologyIdentical": source["scalp"]["topology"] == candidate["scalp"]["topology"],
    "scalpMaterialSlotsIdentical": source["scalp"]["materialSlots"] == candidate["scalp"]["materialSlots"] == 1,
    "scalpFadeAttributePresent": fade is not None and fade.domain == "POINT",
    "fourFrameNoPenetration": all(item["penetratingPoints"] == 0 for item in frames.values()),
}

report = {
    "revision": "v249r1081-graded-hairline-audit",
    "source": str(SOURCE),
    "candidate": str(CANDIDATE),
    "sourceSummary": source,
    "candidateSummary": candidate,
    "fourFrameHairBodyClearance": frames,
    "checks": checks,
    "performanceDelta": {
        "curvesPercent": (candidate["hair"]["curves"] / source["hair"]["curves"] - 1.0) * 100.0,
        "pointsPercent": (candidate["hair"]["points"] / source["hair"]["points"] - 1.0) * 100.0,
        "objects": 0,
        "materialSlots": 0,
    },
    "motionGate": "STATIC_ONLY_NO_SECONDARY_MOTION_CLAIM",
    "status": "PASS" if all(checks.values()) else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1081_AUDIT=" + json.dumps({"status": report["status"], "frames": frames, "checks": checks}, sort_keys=True))
if report["status"] != "PASS":
    raise SystemExit(2)
