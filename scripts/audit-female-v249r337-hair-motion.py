import json
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-natural-sclera-r337.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-natural-sclera-r337.hair-motion-audit.json"
BODY = "AevryndFemaleBody_CC0_R249"
LAYERS = ("AevryndFemalePrimaryClumps_R264", "AevryndFemaleSecondaryFill_R264", "AevryndFemaleFlyaways_R264")
FRAMES = (1, 33, 61)
POINTS_PER_CURVE = 24


def body_tree(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * fraction))]


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
objects = [bpy.data.objects[name] for name in LAYERS]
snapshots = {}
collision = {}
failures = []
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    tree = body_tree(body)
    snapshots[frame] = {}
    collision[str(frame)] = {}
    for obj in objects:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated = obj.evaluated_get(depsgraph)
        local = [point.position.copy() for point in evaluated.data.points]
        world = [evaluated.matrix_world @ point for point in local]
        snapshots[frame][obj.name] = local
        signed = []
        for point in world:
            hit = tree.find_nearest(point, 0.20)
            if hit is not None and hit[1] is not None:
                signed.append((point - hit[0]).dot(hit[1].normalized()))
        penetrating = sum(value < -1e-7 for value in signed)
        collision[str(frame)][obj.name] = {"samples": len(signed), "minimumSignedM": min(signed), "penetratingVertices": penetrating}
        if penetrating:
            failures.append({"frame": frame, "object": obj.name, "penetratingVertices": penetrating})

motion = {}
all_peak, all_settle, all_roots = [], [], []
for obj in objects:
    rest = snapshots[1][obj.name]
    peak = snapshots[33][obj.name]
    settled = snapshots[61][obj.name]
    peak_delta = [(b - a).length for a, b in zip(rest, peak)]
    settle_delta = [(b - a).length for a, b in zip(rest, settled)]
    root_delta = [peak_delta[index] for index in range(0, len(peak_delta), POINTS_PER_CURVE)]
    all_peak.extend(peak_delta)
    all_settle.extend(settle_delta)
    all_roots.extend(root_delta)
    motion[obj.name] = {
        "peakMeanM": sum(peak_delta) / len(peak_delta), "peakP95M": percentile(peak_delta, 0.95),
        "peakMaximumM": max(peak_delta), "rootMaximumM": max(root_delta), "settleMaximumM": max(settle_delta),
    }
summary = {
    "peakMeanM": sum(all_peak) / len(all_peak), "peakP95M": percentile(all_peak, 0.95),
    "peakMaximumM": max(all_peak), "rootMaximumM": max(all_roots), "settleMaximumM": max(all_settle),
}
if summary["peakP95M"] < 0.002:
    failures.append({"motion": "peak P95 below 2mm", "valueM": summary["peakP95M"]})
if summary["rootMaximumM"] > 0.00002:
    failures.append({"motion": "root drift above 0.02mm", "valueM": summary["rootMaximumM"]})
if summary["settleMaximumM"] > 0.00005:
    failures.append({"motion": "frame 61 not settled", "valueM": summary["settleMaximumM"]})
report = {
    "model": str(MODEL), "frames": list(FRAMES), "collision": collision, "motion": motion,
    "motionSummary": summary, "failures": failures, "status": "PASS" if not failures else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R337_HAIR_MOTION_AUDIT=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
