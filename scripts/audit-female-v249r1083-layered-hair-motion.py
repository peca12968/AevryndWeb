"""Audit r1083 root pinning, motion, settle and per-frame hair/body clearance."""
import hashlib
import json
import struct
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-regional-skin-r1082-study.blend"
CANDIDATE = ASSETS / "aevrynd-female-cc0-layered-hair-motion-r1083-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1083-layered-hair-motion.audit.json"
BODY = "AevryndFemaleCC0BalancedEyeOptics_R1080"
HAIR = "AevryndFemaleGradedHairlineGroom_R1081"
FRAMES = (1, 11, 20, 21, 31, 33, 41, 51, 61)


def source_digest(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = bpy.data.objects[BODY]
    hair = bpy.data.objects[HAIR]
    value = hashlib.sha256()
    for block in body.data.shape_keys.key_blocks:
        value.update(block.name.encode())
        for point in block.data:
            value.update(struct.pack("<3f", *point.co))
    body_shapes = value.hexdigest()
    value = hashlib.sha256()
    for curve in hair.data.curves:
        value.update(struct.pack("<II", curve.first_point_index, curve.points_length))
    for point in hair.data.points:
        value.update(struct.pack("<3f", *point.position))
    return {"bodyShapeGeometry": body_shapes, "hairBaseGeometry": value.hexdigest(), "bodyMaterials": [material.name if material else None for material in body.data.materials], "objects": len(bpy.data.objects)}


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * fraction))]


def evaluated_hair_points(hair, deps):
    evaluated = hair.evaluated_get(deps)
    local = [point.position.copy() for point in evaluated.data.points]
    world = [evaluated.matrix_world @ point for point in local]
    return local, world


def body_tree(body, deps):
    evaluated = body.evaluated_get(deps)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


source = source_digest(SOURCE)
candidate = source_digest(CANDIDATE)
bpy.ops.wm.open_mainfile(filepath=str(CANDIDATE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
hair = bpy.data.objects[HAIR]
root_indices = [curve.first_point_index for curve in hair.data.curves]
tip_indices = [curve.first_point_index + curve.points_length - 1 for curve in hair.data.curves]
snapshots = {}
frames = {}
for frame in FRAMES:
    scene.frame_set(frame)
    deps = bpy.context.evaluated_depsgraph_get()
    deps.update()
    local, world = evaluated_hair_points(hair, deps)
    snapshots[frame] = local
    tree = body_tree(body, deps)
    signed = []
    for point in world:
        hit = tree.find_nearest(point)
        if hit and hit[1] is not None:
            signed.append((point - hit[0]).dot(hit[1].normalized()))
    frames[str(frame)] = {
        "pointsTested": len(signed),
        "minimumSignedClearanceM": min(signed),
        "penetratingPoints": sum(value < -0.00005 for value in signed),
    }

reference = snapshots[1]
motion = {}
for frame in FRAMES:
    delta = [(point - reference[index]).length for index, point in enumerate(snapshots[frame])]
    roots = [delta[index] for index in root_indices]
    tips = [delta[index] for index in tip_indices]
    motion[str(frame)] = {
        "allMeanM": sum(delta) / len(delta),
        "allP95M": percentile(delta, 0.95),
        "allMaximumM": max(delta),
        "rootMaximumM": max(roots),
        "tipMeanM": sum(tips) / len(tips),
        "tipP95M": percentile(tips, 0.95),
        "tipMaximumM": max(tips),
    }

peak_frame = max(FRAMES, key=lambda frame: motion[str(frame)]["tipP95M"])
modifier = hair.modifiers.get("Aevrynd Layered Hair Motion R1083")
vector = hair.data.attributes.get("aevrynd_motion_vector_r1083")
phase = hair.data.attributes.get("aevrynd_motion_phase_r1083")
checks = {
    "bodyShapeGeometryIdentical": source["bodyShapeGeometry"] == candidate["bodyShapeGeometry"],
    "skinMaterialStackIdentical": source["bodyMaterials"] == candidate["bodyMaterials"],
    "hairBaseGeometryIdentical": source["hairBaseGeometry"] == candidate["hairBaseGeometry"],
    "pointAndCurveCountsPreserved": len(hair.data.points) == 73840 and len(hair.data.curves) == 3770,
    "headBoneBindingPreserved": hair.parent is not None and hair.parent.name == "AevryndFemaleRig" and hair.parent_type == "BONE" and hair.parent_bone == "head",
    "motionAttributesPresent": vector is not None and vector.domain == "POINT" and phase is not None and phase.domain == "POINT",
    "geometryNodesModifierPresent": modifier is not None and modifier.node_group is not None,
    "rootsPinned": max(item["rootMaximumM"] for item in motion.values()) <= 0.000005,
    "visibleTipMotion": motion[str(peak_frame)]["tipP95M"] >= 0.0015,
    "boundedTipMotion": motion[str(peak_frame)]["tipMaximumM"] <= 0.0070,
    "settlesAtFrame61": motion["61"]["allMaximumM"] <= 0.00005,
    "allFramesNoPenetration": all(item["penetratingPoints"] == 0 for item in frames.values()),
    "allFramesPositiveClearance": all(item["minimumSignedClearanceM"] >= 0.0005 for item in frames.values()),
    "objectCountPreserved": len(bpy.data.objects) == 27,
    "materialSlotsPreserved": len(hair.data.materials) == 1,
}
report = {
    "revision": "v249r1083-layered-hair-motion-audit",
    "source": str(SOURCE),
    "candidate": str(CANDIDATE),
    "sourceSummary": source,
    "candidateSummary": candidate,
    "frames": frames,
    "motion": motion,
    "peakFrame": peak_frame,
    "thresholds": {"maximumRootDriftM": 0.000005, "minimumTipP95MotionM": 0.0015, "maximumTipMotionM": 0.0070, "maximumSettleErrorM": 0.00005, "minimumSignedClearanceM": 0.0005},
    "checks": checks,
    "status": "PASS" if all(checks.values()) else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1083_MOTION_AUDIT=" + json.dumps({"status": report["status"], "peakFrame": peak_frame, "peak": motion[str(peak_frame)], "frames": frames, "checks": checks}, sort_keys=True))
if report["status"] != "PASS":
    raise SystemExit(2)
