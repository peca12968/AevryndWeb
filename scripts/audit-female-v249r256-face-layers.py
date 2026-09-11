import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-brow-microclusters-r256.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-brow-microclusters-r256.face-layer-audit.json"
BODY = "AevryndFemaleBody_CC0_R249"
RIG = "AevryndFemaleRig"
HEAD_BONE = "head"
FRAMES = (1, 20)


def evaluated_body_bvh(body, depsgraph):
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
    bvh = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    return evaluated, mesh, bvh


def curve_points_world(obj):
    points = []
    for spline in obj.data.splines:
        for point in spline.points:
            world = obj.matrix_world @ point.co.xyz
            points.append(world)
    return points


def curve_roots_world(obj):
    return [obj.matrix_world @ spline.points[0].co.xyz for spline in obj.data.splines]


def bone_matrix_world(rig):
    return rig.matrix_world @ rig.pose.bones[HEAD_BONE].matrix


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
rig = bpy.data.objects[RIG]
face_objects = [
    obj for obj in scene.objects
    if obj.get("aevrynd_layer", "").startswith(("face.", "eye."))
]
brow_objects = [obj for obj in face_objects if "eyebrow_fibers" in obj.get("aevrynd_layer", "")]
curve_objects = [obj for obj in face_objects if obj.type == "CURVE"]

reference_bone_space = None
frames = {}
violations = []
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated, mesh, bvh = evaluated_body_bvh(body, depsgraph)
    brow_metrics = {}
    for obj in brow_objects:
        signed = []
        for root in curve_roots_world(obj):
            nearest, normal, _index, _distance = bvh.find_nearest(root)
            signed.append((root - nearest).dot(normal))
        penetrating = sum(value < -0.00010 for value in signed)
        brow_metrics[obj.name] = {
            "roots": len(signed),
            "minimumSignedClearanceM": min(signed),
            "maximumSignedClearanceM": max(signed),
            "penetratingRootsBelowMinus0p1mm": penetrating,
        }
        if penetrating:
            violations.append({"frame": frame, "object": obj.name, "type": "brow_root_body_penetration", "count": penetrating})
    inverse_bone = bone_matrix_world(rig).inverted()
    current_bone_space = {
        obj.name: [tuple(inverse_bone @ point) for point in curve_points_world(obj)]
        for obj in curve_objects
    }
    if reference_bone_space is None:
        reference_bone_space = current_bone_space
        drift = {name: 0.0 for name in current_bone_space}
    else:
        drift = {}
        for name, points in current_bone_space.items():
            baseline = reference_bone_space[name]
            drift[name] = max((math.dist(a, b) for a, b in zip(points, baseline)), default=0.0)
            if drift[name] > 1e-6:
                violations.append({"frame": frame, "object": name, "type": "head_space_drift", "maximumM": drift[name]})
    frames[str(frame)] = {"brows": brow_metrics, "maximumHeadSpaceDriftM": drift}
    evaluated.to_mesh_clear()

binding_violations = []
for obj in face_objects:
    if obj.parent != rig or obj.parent_type != "BONE" or obj.parent_bone != HEAD_BONE:
        binding_violations.append(obj.name)
if binding_violations:
    violations.append({"type": "invalid_head_binding", "objects": binding_violations})

scene.frame_set(1)
report = {
    "source": str(SOURCE),
    "frames": frames,
    "faceLayerCount": len(face_objects),
    "curveLayerCount": len(curve_objects),
    "bindingViolations": binding_violations,
    "violations": violations,
    "status": "PASS" if not violations else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R256_FACE_LAYER_AUDIT=" + json.dumps(report, sort_keys=True))
