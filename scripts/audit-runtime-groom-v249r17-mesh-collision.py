import json
import math
import os
import struct
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get(
    "AEVRYND_RUNTIME_GROOM_SOURCE",
    ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r17.blend",
))
DATA_DIR = Path(os.environ.get(
    "AEVRYND_RUNTIME_GROOM_PREVIEW_DIR",
    ROOT.parent / "Temp/female-realism/v249-mainline-hair-r17-dynamics",
))
OUTPUT = Path(os.environ.get(
    "AEVRYND_RUNTIME_GROOM_COLLISION_REPORT",
    ROOT / "assets-source/aevrynd-character/runtime-groom-v249r17/dynamic-mesh-collision-audit.json",
))
SOLIDS = (
    "AevryndFemaleBodyBaseV118",
    "Clothing_Bandeau_v160",
    "Clothing_BandeauBinding_v162",
    "Clothing_BodyFitShorts_v135",
)
RIGID_LAYERS = tuple(filter(None, os.environ.get(
    "AEVRYND_RIGID_COLLISION_LAYERS", "",
).split(";")))
PENETRATION_LIMIT = -0.0005
NEAR_SURFACE_LIMITS = {
    "AevryndFemaleBodyBaseV118": 0.025,
    "Clothing_Bandeau_v160": 0.010,
    "Clothing_BandeauBinding_v162": 0.010,
    "Clothing_BodyFitShorts_v135": 0.010,
}


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


def evaluated_points(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    evaluated.to_mesh_clear()
    return points


def sample(points, tree, near_surface_limit):
    penetrating = []
    penetrating_details = []
    minimum = math.inf
    for index, world in enumerate(points):
        nearest = tree.find_nearest(world)
        if nearest is None or nearest[1] is None:
            continue
        location, normal, distance = nearest[0], nearest[1].normalized(), nearest[3]
        if distance > near_surface_limit:
            continue
        signed = (world - location).dot(normal)
        minimum = min(minimum, signed)
        if signed < PENETRATION_LIMIT:
            penetrating.append(index)
            if len(penetrating_details) < 20:
                penetrating_details.append({
                    "index": index,
                    "point": list(world),
                    "nearest": list(location),
                    "normal": list(normal),
                    "signed_m": signed,
                })
    return {
        "sample_count": len(points),
        "minimum_signed_m": minimum if math.isfinite(minimum) else None,
        "penetrating_count": len(penetrating),
        "penetrating_indices_sample": penetrating[:20],
        "penetrating_details_sample": penetrating_details,
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
head = bpy.data.objects["AevryndFemaleRig"].pose.bones["head"]
head.rotation_mode = "XYZ"
metadata = json.loads((DATA_DIR / "frames.json").read_text(encoding="utf-8"))
points_per_curve = metadata["pointsPerCurve"]
main_points = metadata["mainCurveCount"] * points_per_curve
total_points = metadata["curveCount"] * points_per_curve
simulated_layers = metadata.get("simulatedLayers", [
    {"id": "hair.guide_follow.main", "curveCount": metadata["mainCurveCount"]},
    {"id": "hair.nape.fiber-underlayer", "curveCount": metadata["fillCurveCount"]},
])

states = {}
violations = []
for state in metadata["saved"]:
    head.rotation_euler = (0.0, state.get("yawDeg", 0.0) * math.pi / 180.0, 0.0)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    trees = {name: evaluated_tree(bpy.data.objects[name], depsgraph) for name in SOLIDS}
    payload = (DATA_DIR / state["filename"]).read_bytes()
    values = struct.unpack(f"<{total_points * 3}f", payload)
    points = [Vector(values[index:index + 3]) for index in range(0, len(values), 3)]
    layers = {}
    layer_start = 0
    for layer in simulated_layers:
        layer_end = layer_start + layer["curveCount"] * points_per_curve
        layers[layer["id"]] = points[layer_start:layer_end]
        layer_start = layer_end
    for name in RIGID_LAYERS:
        obj = bpy.data.objects[name]
        layer = str(obj.get("aevrynd_layer", name))
        layers[layer] = evaluated_points(obj, depsgraph)
    state_report = {}
    for layer, layer_points in layers.items():
        state_report[layer] = {}
        for solid, tree in trees.items():
            result = sample(layer_points, tree, NEAR_SURFACE_LIMITS[solid])
            state_report[layer][solid] = result
            if result["penetrating_count"]:
                violations.append({
                    "state": state["frame"],
                    "layer": layer,
                    "solid": solid,
                    "penetrating_count": result["penetrating_count"],
                })
    states[str(state["frame"])] = state_report

report = {
    "source": str(SOURCE),
    "runtimeGroom": str(DATA_DIR),
    "states": states,
    "penetrationLimitM": PENETRATION_LIMIT,
    "nearSurfaceLimitsM": NEAR_SURFACE_LIMITS,
    "rigidLayers": list(RIGID_LAYERS),
    "violations": violations,
    "status": "PASS" if not violations else "FAIL",
}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R17_DYNAMIC_MESH_COLLISION=" + json.dumps({
    "output": str(OUTPUT),
    "states": len(states),
    "runtimePointsPerState": total_points,
    "rigidLayers": list(RIGID_LAYERS),
    "violations": violations,
    "status": report["status"],
}, sort_keys=True))
if violations:
    raise SystemExit(2)
