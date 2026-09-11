import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-continuous-front-surface-flow-r377.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-r377.hair-collision-audit.json"
BODY = "AevryndFemaleBody_CC0_R249"
PENETRATION_LIMIT = -0.0005


def body_tree(body, depsgraph):
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def sample_object(obj, depsgraph, tree):
    evaluated = obj.evaluated_get(depsgraph)
    data = evaluated.data
    if evaluated.type == "CURVES":
        local_points = [point.position for point in data.points]
    elif evaluated.type == "MESH":
        local_points = [vertex.co for vertex in data.vertices]
    else:
        return {"sample_count": 0, "penetrating_indices": [], "minimum_signed_m": None}
    penetrating = []
    minimum = math.inf
    for index, local in enumerate(local_points):
        world = evaluated.matrix_world @ local
        nearest = tree.find_nearest(world)
        if nearest is None:
            continue
        location, normal, _face, _distance = nearest
        if normal is None:
            continue
        signed = (world - location).dot(normal.normalized())
        minimum = min(minimum, signed)
        if signed < PENETRATION_LIMIT:
            penetrating.append(index)
    return {
        "sample_count": len(local_points),
        "penetrating_indices": penetrating,
        "minimum_signed_m": minimum if math.isfinite(minimum) else None,
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
hair_names = (
    "AevryndFemaleSemanticPrimary_R377",
    "AevryndFemaleSemanticFill_R377",
    "AevryndFemaleHairlineTransition_R377",
    "AevryndFemaleFrontSurfaceFlow_R377",
)
objects = [bpy.data.objects[name] for name in hair_names]
snapshots = {}
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    tree = body_tree(bpy.data.objects[BODY], depsgraph)
    snapshots[str(frame)] = {
        obj.name: sample_object(obj, depsgraph, tree)
        for obj in objects
    }

regressions = []
for name in snapshots["1"]:
    first = set(snapshots["1"][name].pop("penetrating_indices"))
    posed = set(snapshots["20"][name].pop("penetrating_indices"))
    snapshots["1"][name]["penetrating_count"] = len(first)
    snapshots["20"][name]["penetrating_count"] = len(posed)
    added = posed - first
    removed = first - posed
    snapshots["20"][name]["new_penetrating_count"] = len(added)
    snapshots["20"][name]["resolved_penetrating_count"] = len(removed)
    if added:
        regressions.append({"object": name, "new_penetrating_count": len(added)})

penetration_violations = []
for frame, values in snapshots.items():
    for name, sample in values.items():
        if sample["penetrating_count"]:
            penetration_violations.append({
                "frame": frame,
                "object": name,
                "penetrating_count": sample["penetrating_count"],
            })

report = {
    "source": str(SOURCE),
    "penetration_limit_m": PENETRATION_LIMIT,
    "frames": snapshots,
    "regressions": regressions,
    "penetration_violations": penetration_violations,
    "status": "PASS" if not regressions and not penetration_violations else "FAIL",
}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R377_HAIR_COLLISION_AUDIT=" + json.dumps(report, sort_keys=True))
if regressions or penetration_violations:
    raise SystemExit(2)





