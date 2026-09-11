import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-per-chain-collision-r278.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-per-chain-collision-r278.audit.json"
BODY = "AevryndFemaleBody_CC0_R249"
RIG = "AevryndFemaleRig"
HAIR = "AevryndFemaleRuntimeHairCards_R276"
FRAMES = (1, 17, 25, 33, 41, 61)
POINTS_PER_CARD = 24
VERTS_PER_POINT = 2
PENETRATION_LIMIT = 0.0


def body_tree(depsgraph):
    evaluated = bpy.data.objects[BODY].evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
reference = None
frames = {}
failures = []
for frame in FRAMES:
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    hair_eval = bpy.data.objects[HAIR].evaluated_get(depsgraph)
    mesh = hair_eval.to_mesh()
    world = [hair_eval.matrix_world @ vertex.co for vertex in mesh.vertices]
    rig_inverse = bpy.data.objects[RIG].evaluated_get(depsgraph).matrix_world.inverted()
    rig_local = [rig_inverse @ point for point in world]
    hair_eval.to_mesh_clear()
    if reference is None:
        reference = rig_local
    root_ids = [i for i in range(len(world)) if (i % (POINTS_PER_CARD * VERTS_PER_POINT)) < 4]
    tip_ids = [i for i in range(len(world)) if (i % (POINTS_PER_CARD * VERTS_PER_POINT)) >= 42]
    free_ids = [i for i in range(len(world)) if (i % (POINTS_PER_CARD * VERTS_PER_POINT)) >= 6]
    root_drift = max((rig_local[i] - reference[i]).length for i in root_ids)
    tip_displacements = sorted((rig_local[i] - reference[i]).length for i in tip_ids)
    tip_motion = sum(tip_displacements) / len(tip_displacements)
    tip_p95 = tip_displacements[int(0.95 * (len(tip_displacements) - 1))]
    tree = body_tree(depsgraph)
    penetrating = []
    minimum = math.inf
    for index in free_ids:
        hit = tree.find_nearest(world[index], 0.20)
        if hit is None or hit[1] is None:
            continue
        signed = (world[index] - hit[0]).dot(hit[1].normalized())
        minimum = min(minimum, signed)
        if signed < PENETRATION_LIMIT:
            penetrating.append(index)
    frames[str(frame)] = {
        "rootMaxDriftM": root_drift,
        "tipMeanMotionM": tip_motion,
        "tipP95MotionM": tip_p95,
        "sampledFreeVertices": len(free_ids),
        "penetratingVertices": len(penetrating),
        "minimumSignedM": minimum if math.isfinite(minimum) else None,
        "penetratingSample": penetrating[:24],
    }
    if root_drift > 0.0015:
        failures.append({"frame": frame, "rootMaxDriftM": root_drift})
    if penetrating:
        failures.append({"frame": frame, "penetratingVertices": len(penetrating)})
peak_tip = max(item["tipMeanMotionM"] for item in frames.values())
peak_tip_p95 = max(item["tipP95MotionM"] for item in frames.values())
settle = frames["61"]["tipMeanMotionM"]
if peak_tip < 0.001:
    failures.append({"tipMotionTooSmallM": peak_tip})
if peak_tip_p95 < 0.005:
    failures.append({"tipP95MotionTooSmallM": peak_tip_p95})
if settle > 0.002:
    failures.append({"settleErrorM": settle})
report = {
    "model": str(MODEL), "frames": frames,
    "thresholds": {"maxRootDriftM": 0.0015, "minTipMeanMotionM": 0.001, "minTipP95MotionM": 0.005, "maxSettleErrorM": 0.002, "penetrationLimitM": PENETRATION_LIMIT},
    "peakTipMeanMotionM": peak_tip, "peakTipP95MotionM": peak_tip_p95, "settleErrorM": settle,
    "failures": failures, "status": "FAIL" if failures else "PASS",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R278_RUNTIME_HAIR_AUDIT=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)







