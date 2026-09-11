import json
import math
import os
from pathlib import Path

import bmesh
import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("AEVRYND_DEFORMATION_SOURCE", ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-rig-transfer-r250.blend"))
OUTPUT = Path(os.environ.get("AEVRYND_DEFORMATION_REPORT", ROOT / "assets-source/aevrynd-character/female-v249-mainline-cc0-rig-transfer-r250.deformation-audit.json"))
BODY = "AevryndFemaleBody_CC0_R249"
FRAMES = (1, 20)


def evaluated_state(scene, obj, frame):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    edges = [tuple(edge.vertices) for edge in mesh.edges]
    bm = bmesh.new()
    bm.from_mesh(mesh)
    volume = abs(bm.calc_volume(signed=True))
    bm.free()
    evaluated.to_mesh_clear()
    return points, edges, volume


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
states = {frame: evaluated_state(scene, body, frame) for frame in FRAMES}
rest_points, edges, rest_volume = states[1]
pose_points, pose_edges, pose_volume = states[20]
if edges != pose_edges:
    raise RuntimeError("evaluated topology changed between audit frames")

ratios = []
edge_metrics = []
for a, b in edges:
    rest = (rest_points[a] - rest_points[b]).length
    posed = (pose_points[a] - pose_points[b]).length
    if rest > 1e-9:
        ratio = posed / rest
        ratios.append(ratio)
        edge_metrics.append({
            "vertices": [a, b],
            "ratio": ratio,
            "restLengthMm": rest * 1000.0,
            "poseLengthMm": posed * 1000.0,
            "restMidpoint": list((rest_points[a] + rest_points[b]) * 0.5),
        })
displacements = [(pose_points[index] - rest_points[index]).length for index in range(len(rest_points))]
nonfinite = sum(
    not all(math.isfinite(value) for value in point)
    for points, _edges, _volume in states.values()
    for point in points
)
volume_ratio = pose_volume / rest_volume
sorted_ratios = sorted(ratios)
def percentile(fraction):
    return sorted_ratios[min(len(sorted_ratios) - 1, round((len(sorted_ratios) - 1) * fraction))]
severe_edges = [metric for metric in edge_metrics if metric["ratio"] > 2.5 or metric["ratio"] < 0.30]
top_stretched = sorted(edge_metrics, key=lambda metric: metric["ratio"], reverse=True)[:20]
checks = {
    "topologyStable": len(rest_points) == len(pose_points) and edges == pose_edges,
    "finiteCoordinates": nonfinite == 0,
    "minimumEdgeRatioAbove030": min(ratios) > 0.30,
    "maximumEdgeRatioBelow250": max(ratios) < 2.50,
    "volumeRatioWithin15Percent": 0.85 < volume_ratio < 1.15,
}
report = {
    "source": str(SOURCE),
    "frames": list(FRAMES),
    "evaluatedVertices": len(rest_points),
    "evaluatedEdges": len(edges),
    "restVolume": rest_volume,
    "poseVolume": pose_volume,
    "volumeRatio": volume_ratio,
    "minimumEdgeRatio": min(ratios),
    "maximumEdgeRatio": max(ratios),
    "meanEdgeRatio": sum(ratios) / len(ratios),
    "edgeRatioPercentiles": {"p001": percentile(0.001), "p01": percentile(0.01), "p50": percentile(0.5), "p99": percentile(0.99), "p999": percentile(0.999)},
    "severeEdgeCount": len(severe_edges),
    "topStretchedEdges": top_stretched,
    "maximumVertexDisplacementM": max(displacements),
    "meanVertexDisplacementM": sum(displacements) / len(displacements),
    "nonfiniteCoordinates": nonfinite,
    "checks": checks,
    "status": "PASS" if all(checks.values()) else "FAIL",
}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R250_DEFORMATION=" + json.dumps(report, sort_keys=True))
if report["status"] != "PASS":
    raise SystemExit(2)
