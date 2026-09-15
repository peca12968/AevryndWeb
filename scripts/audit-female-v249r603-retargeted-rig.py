import json
import math
import os
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = Path(os.environ.get("AEVRYND_RIG_AUDIT_SOURCE", ASSETS / "aevrynd-female-cc0-retargeted-rig-r603.blend"))
REPORT = Path(os.environ.get("AEVRYND_RIG_AUDIT_REPORT", ASSETS / "female-v249-mainline-cc0-retargeted-rig-r603.audit.json"))
BODY = "AevryndFemaleCC0Baseline_v259"
RIG = "AevryndFemaleRig"
FRAMES = (1, 20, 33, 61)
EYES = tuple(f"Eye_{side}_{part}" for side in ("L", "R") for part in ("Sclera", "Cornea", "Iris"))
DEFORM_BONES = {
    "pelvis", "spine_01", "spine_02", "chest", "neck", "head",
    "clavicle.L", "upper_arm.L", "forearm.L", "hand.L",
    "clavicle.R", "upper_arm.R", "forearm.R", "hand.R",
    "thigh.L", "shin.L", "foot.L", "thigh.R", "shin.R", "foot.R",
}


def visible_indices(obj):
    group = obj.vertex_groups["body"]
    result = set()
    for vertex in obj.data.vertices:
        try:
            if group.weight(vertex.index) > 0.0:
                result.add(vertex.index)
        except RuntimeError:
            pass
    return result


def evaluated_mesh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    edges = [tuple(edge.vertices) for edge in mesh.edges]
    mesh.calc_loop_triangles()
    triangles = [tuple(tri.vertices) for tri in mesh.loop_triangles]
    evaluated.to_mesh_clear()
    return points, edges, triangles


def volume(points, triangles, allowed):
    signed = 0.0
    for indices in triangles:
        if not all(index in allowed for index in indices):
            continue
        a, b, c = (points[index] for index in indices)
        signed += a.dot(b.cross(c)) / 6.0
    return abs(signed)


def tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
rig = bpy.data.objects[RIG]
allowed = visible_indices(body)
states = {}
collisions = {}
bone_motion = {}
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    points, edges, triangles = evaluated_mesh(body, depsgraph)
    evaluated_visible = set(range(len(points)))
    states[frame] = {
        "points": points,
        "edges": edges,
        "triangles": triangles,
        "volume": volume(points, triangles, evaluated_visible),
    }
    body_tree = tree(body, depsgraph)
    collisions[str(frame)] = {
        name: len(body_tree.overlap(tree(bpy.data.objects[name], depsgraph)))
        for name in EYES
    }
    bone_motion[str(frame)] = {
        name: list(rig.pose.bones[name].matrix.translation)
        for name in DEFORM_BONES
    }

rest = states[1]
evaluated_visible = set(range(len(rest["points"])))
frame_reports = {}
all_checks = []
for frame in FRAMES[1:]:
    current = states[frame]
    if rest["edges"] != current["edges"]:
        raise RuntimeError(f"evaluated topology changed at frame {frame}")
    ratios = []
    edge_metrics = []
    for a, b in rest["edges"]:
        rest_length = (rest["points"][a] - rest["points"][b]).length
        if rest_length <= 1e-9:
            continue
        ratio = (current["points"][a] - current["points"][b]).length / rest_length
        ratios.append(ratio)
        edge_metrics.append({
            "vertices": [a, b],
            "ratio": ratio,
            "restPoints": [list(rest["points"][a]), list(rest["points"][b])],
            "posedPoints": [list(current["points"][a]), list(current["points"][b])],
            "restMidpoint": list((rest["points"][a] + rest["points"][b]) * 0.5),
            "posedMidpoint": list((current["points"][a] + current["points"][b]) * 0.5),
            "restLengthMm": rest_length * 1000.0,
        })
    displacements = [
        (current["points"][index] - rest["points"][index]).length
        for index in evaluated_visible
    ]
    nonfinite = sum(
        not all(math.isfinite(value) for value in current["points"][index])
        for index in evaluated_visible
    )
    volume_ratio = current["volume"] / rest["volume"] if rest["volume"] else 0.0
    checks = {
        "finiteCoordinates": nonfinite == 0,
        "minimumEdgeRatioAbove030": min(ratios) > 0.30,
        "maximumEdgeRatioBelow250": max(ratios) < 2.50,
        "volumeRatioWithin15Percent": 0.85 < volume_ratio < 1.15,
        "eyeBodyCollisionFree": not any(collisions[str(frame)].values()),
    }
    all_checks.extend(checks.values())
    frame_reports[str(frame)] = {
        "volumeRatio": volume_ratio,
        "minimumEdgeRatio": min(ratios),
        "maximumEdgeRatio": max(ratios),
        "severeEdgeCount": sum(ratio < 0.30 or ratio > 2.50 for ratio in ratios),
        "severeEdges": sorted(
            (metric for metric in edge_metrics if metric["ratio"] < 0.30 or metric["ratio"] > 2.50),
            key=lambda metric: metric["ratio"], reverse=True,
        )[:40],
        "maximumVertexDisplacementM": max(displacements),
        "meanVertexDisplacementM": sum(displacements) / len(displacements),
        "nonfiniteCoordinates": nonfinite,
        "checks": checks,
    }

deform_group_indices = {
    body.vertex_groups[name].index for name in DEFORM_BONES if body.vertex_groups.get(name)
}
weight_sums = [
    sum(entry.weight for entry in vertex.groups if entry.group in deform_group_indices)
    for vertex in body.data.vertices
]
motion = max(
    abs(bone_motion[str(frame)][name][axis] - bone_motion["1"][name][axis])
    for frame in FRAMES[1:] for name in DEFORM_BONES for axis in range(3)
)
static_checks = {
    "visibleBodyVertexSetPresent": len(allowed) == 13380,
    "shapeKeysPreserved": body.data.shape_keys is not None and len(body.data.shape_keys.key_blocks) == 23,
    "allVerticesWeighted": min(weight_sums) > 0.9999,
    "weightsNormalized": max(weight_sums) < 1.0001,
    "neutralEyeBodyCollisionFree": not any(collisions["1"].values()),
    "animationProducesMotion": motion > 0.01,
}
all_checks.extend(static_checks.values())
report = {
    "source": str(SOURCE),
    "frames": list(FRAMES),
    "visibleBodyVertices": len(allowed),
    "evaluatedVertices": len(rest["points"]),
    "evaluatedEdges": len(rest["edges"]),
    "neutralVisibleVolume": rest["volume"],
    "deformGroups": len(deform_group_indices),
    "weightSum": {"min": min(weight_sums), "max": max(weight_sums)},
    "maximumBoneTranslationDeltaM": motion,
    "collisions": collisions,
    "frameReports": frame_reports,
    "checks": static_checks,
    "status": "PASS" if all(all_checks) else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R603_RETARGETED_RIG_AUDIT=" + json.dumps({
    "status": report["status"], "motion": motion, "frames": frame_reports,
    "static": static_checks, "collisions": collisions,
}, sort_keys=True))
if report["status"] != "PASS":
    raise SystemExit(2)
