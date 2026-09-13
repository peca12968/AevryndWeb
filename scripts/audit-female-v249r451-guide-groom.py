import json
import os
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
MODEL = Path(os.environ.get(
    "AEVRYND_GUIDE_GROOM_MODEL",
    ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-aligned-continuous-guide-groom-r451-study.blend",
))
REPORT = Path(os.environ.get(
    "AEVRYND_GUIDE_GROOM_REPORT",
    ROOT / "assets-source/aevrynd-character/female-v249-mainline-r451.guide-groom-audit.json",
))
AUDIT_LABEL = os.environ.get("AEVRYND_GUIDE_GROOM_AUDIT_LABEL", "V249R451")
BODY = "AevryndFemaleBodyBaseV118"
SOLIDS = (
    BODY,
    "Clothing_Bandeau_v160",
    "Clothing_BandeauBinding_v162",
    "Clothing_BodyFitShorts_v135",
)
NEAR = {BODY: 0.025, SOLIDS[1]: 0.010, SOLIDS[2]: 0.010, SOLIDS[3]: 0.010}
CURVE_LAYERS = (
    "AevryndFemaleFrontSurfaceFlow_R383",
    "AevryndFemaleCrownSurfaceFlow_R383",
    "AevryndFemaleRearSurfaceFlow_R383",
    "AevryndFemaleHairlineTransition_R383",
)
SCALP = "AevryndFemaleSemanticScalp_R383"
RIG = "AevryndFemaleRig"
FRAMES = (1, 20, 33, 61)
POINTS_PER_CURVE = 24
PENETRATION_LIMIT = -0.0005


def surface_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def evaluated_points(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    if evaluated.type == "CURVES":
        local = [point.position.copy() for point in evaluated.data.points]
    elif evaluated.type == "MESH":
        local = [vertex.co.copy() for vertex in evaluated.data.vertices]
    else:
        raise TypeError(f"Unsupported collision layer type: {evaluated.type}")
    return [evaluated.matrix_world @ point for point in local]


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * fraction))]


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
curve_names = [name for name in CURVE_LAYERS if not bpy.data.objects[name].hide_render]
curve_names.extend(sorted(
    obj.name for obj in bpy.data.objects
    if obj.type == "CURVES" and obj.get("aevrynd_collision_audit", False) and obj.name not in curve_names
))
curves = [bpy.data.objects[name] for name in curve_names]
collision_objects = curves + [bpy.data.objects[SCALP]]
for obj in curves:
    if len(obj.data.points) % POINTS_PER_CURVE:
        raise RuntimeError(f"{obj.name} does not use the expected {POINTS_PER_CURVE}-point guide layout")

snapshots = {}
collision = {}
failures = []
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    trees = {name: surface_tree(bpy.data.objects[name], depsgraph) for name in SOLIDS}
    head_inverse = (bpy.data.objects[RIG].matrix_world @ bpy.data.objects[RIG].pose.bones["head"].matrix).inverted()
    snapshots[frame] = {}
    collision[str(frame)] = {}
    for obj in collision_objects:
        points = evaluated_points(obj, depsgraph)
        if obj in curves:
            snapshots[frame][obj.name] = [head_inverse @ point for point in points]
        collision[str(frame)][obj.name] = {}
        for solid, tree in trees.items():
            minimum = None
            near_samples = 0
            penetrating_indices = []
            for index, point in enumerate(points):
                hit = tree.find_nearest(point, NEAR[solid])
                if hit is None or hit[1] is None:
                    continue
                signed = (point - hit[0]).dot(hit[1].normalized())
                near_samples += 1
                minimum = signed if minimum is None else min(minimum, signed)
                if signed < PENETRATION_LIMIT:
                    penetrating_indices.append(index)
            result = {
                "points": len(points),
                "nearSamples": near_samples,
                "minimumSignedM": minimum,
                "penetratingPoints": len(penetrating_indices),
            }
            if obj in curves:
                result["affectedCurves"] = len({index // POINTS_PER_CURVE for index in penetrating_indices})
                if solid == BODY and penetrating_indices:
                    local_penetrations = [head_inverse @ points[index] for index in penetrating_indices]
                    segment_histogram = {"root_0_3": 0, "upper_4_11": 0, "lower_12_23": 0}
                    for index in penetrating_indices:
                        segment = index % POINTS_PER_CURVE
                        bucket = "root_0_3" if segment < 4 else "upper_4_11" if segment < 12 else "lower_12_23"
                        segment_histogram[bucket] += 1
                    result["penetrationSegments"] = segment_histogram
                    result["penetrationHeadLocalBoundsM"] = {
                        "minimum": [min(point[axis] for point in local_penetrations) for axis in range(3)],
                        "maximum": [max(point[axis] for point in local_penetrations) for axis in range(3)],
                    }
            collision[str(frame)][obj.name][solid] = result
            if penetrating_indices:
                failures.append({
                    "frame": frame,
                    "object": obj.name,
                    "solid": solid,
                    "penetratingPoints": len(penetrating_indices),
                    **({"affectedCurves": result["affectedCurves"]} if obj in curves else {}),
                })

motion = {}
all_peak = []
all_settle = []
all_roots = []
for obj in curves:
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
        "curves": len(peak_delta) // POINTS_PER_CURVE,
        "points": len(peak_delta),
        "peakMeanM": sum(peak_delta) / len(peak_delta),
        "peakP95M": percentile(peak_delta, 0.95),
        "peakMaximumM": max(peak_delta),
        "rootMaximumM": max(root_delta),
        "settleMaximumM": max(settle_delta),
    }

summary = {
    "peakMeanM": sum(all_peak) / len(all_peak),
    "peakP95M": percentile(all_peak, 0.95),
    "peakMaximumM": max(all_peak),
    "rootMaximumM": max(all_roots),
    "settleMaximumM": max(all_settle),
}
if summary["peakP95M"] < 0.002:
    failures.append({"motion": "peak P95 below 2mm", "valueM": summary["peakP95M"]})
if summary["rootMaximumM"] > 0.00002:
    failures.append({"motion": "root drift above 0.02mm", "valueM": summary["rootMaximumM"]})
if summary["settleMaximumM"] > 0.00005:
    failures.append({"motion": "frame 61 not settled", "valueM": summary["settleMaximumM"]})

report = {
    "model": str(MODEL),
    "frames": list(FRAMES),
    "solids": list(SOLIDS),
    "penetrationLimitM": PENETRATION_LIMIT,
    "pointsPerCurve": POINTS_PER_CURVE,
    "collision": collision,
    "motion": motion,
    "motionSummary": summary,
    "failures": failures,
    "status": "PASS" if not failures else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(f"AEVRYND_{AUDIT_LABEL}_GUIDE_GROOM_AUDIT=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
