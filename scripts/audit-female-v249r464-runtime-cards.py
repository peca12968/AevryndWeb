import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-runtime-qualified-cards-r464.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-r464.runtime-card-audit.json"
BODY = "AevryndFemaleBodyBaseV118"
SOLIDS = (
    BODY,
    "Clothing_Bandeau_v160",
    "Clothing_BandeauBinding_v162",
    "Clothing_BodyFitShorts_v135",
)
NEAR = {BODY: 0.025, SOLIDS[1]: 0.010, SOLIDS[2]: 0.010, SOLIDS[3]: 0.010}
LAYERS = tuple(f"AevryndFemaleRuntimeCards_{region}_R464" for region in ("front", "crown", "rear", "hairline"))
SCALP = "AevryndFemaleRuntimeScalpCap_R464"
HAIRLINE_DENSITY = "AevryndFemaleRuntimeHairlineDensity_R464"
PART_ROOT_DENSITY = "AevryndFemaleRuntimePartRootDensity_R464"
RIG = "AevryndFemaleRig"
FRAMES = (1, 20, 33, 61)
VERTICES_PER_CARD = 48
PENETRATION_LIMIT = -0.0005


def surface_tree(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def evaluated_points(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    return [evaluated.matrix_world @ vertex.co for vertex in evaluated.data.vertices]


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * fraction))]


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
objects = [bpy.data.objects[name] for name in LAYERS]
collision_objects = objects + [bpy.data.objects[SCALP], bpy.data.objects[HAIRLINE_DENSITY], bpy.data.objects[PART_ROOT_DENSITY]]
snapshots = {}
collision = {}
failures = []
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    trees = {name: surface_tree(bpy.data.objects[name]) for name in SOLIDS}
    head_inverse = (bpy.data.objects[RIG].matrix_world @ bpy.data.objects[RIG].pose.bones["head"].matrix).inverted()
    snapshots[frame] = {}
    collision[str(frame)] = {}
    for obj in collision_objects:
        points = evaluated_points(obj)
        if obj in objects:
            snapshots[frame][obj.name] = [head_inverse @ point for point in points]
        collision[str(frame)][obj.name] = {}
        for solid, tree in trees.items():
            signed = []
            for point in points:
                hit = tree.find_nearest(point, NEAR[solid])
                if hit is not None and hit[1] is not None:
                    signed.append((point - hit[0]).dot(hit[1].normalized()))
            penetrating = sum(value < PENETRATION_LIMIT for value in signed)
            collision[str(frame)][obj.name][solid] = {
                "nearSamples": len(signed),
                "minimumSignedM": min(signed) if signed else None,
                "penetratingVertices": penetrating,
            }
            if penetrating:
                failures.append({"frame": frame, "object": obj.name, "solid": solid, "penetratingVertices": penetrating})

motion = {}
all_peak = []
all_settle = []
all_roots = []
for obj in objects:
    rest = snapshots[1][obj.name]
    peak = snapshots[33][obj.name]
    settled = snapshots[61][obj.name]
    peak_delta = [(b - a).length for a, b in zip(rest, peak)]
    settle_delta = [(b - a).length for a, b in zip(rest, settled)]
    root_delta = []
    for index in range(0, len(peak_delta), VERTICES_PER_CARD):
        root_delta.extend(peak_delta[index:index + 2])
    all_peak.extend(peak_delta)
    all_settle.extend(settle_delta)
    all_roots.extend(root_delta)
    motion[obj.name] = {
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
    "collision": collision,
    "motion": motion,
    "motionSummary": summary,
    "failures": failures,
    "status": "PASS" if not failures else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R464_RUNTIME_CARD_AUDIT=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
