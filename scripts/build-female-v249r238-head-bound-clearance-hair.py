import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-layered-flow-hair-r237.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-head-bound-clearance-hair-r238.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-head-bound-clearance-hair-r238.build-report.json"
RIG = "AevryndFemaleRig"
BODY = "AevryndFemaleBodyBaseV118"
HEAD_BONE = "head"
ROOT_VEILS = (
    "AevryndFemaleHair_CrownRootVeil_v338_L",
    "AevryndFemaleHair_CrownRootVeil_v338_R",
)
CLEARANCE = 0.010
MAX_DISTANCE = 0.12


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


def bind_to_head(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = HEAD_BONE
    obj.matrix_world = world


def project_clear(obj, body_tree):
    obj.data = obj.data.copy()
    inverse = obj.matrix_world.inverted()
    moved = 0
    maximum = 0.0
    minimum_before = math.inf
    for point in obj.data.points:
        world = obj.matrix_world @ point.position
        nearest = body_tree.find_nearest(world, MAX_DISTANCE)
        if nearest is None or nearest[1] is None:
            continue
        location, normal, _face, _distance = nearest
        normal = normal.normalized()
        signed = (world - location).dot(normal)
        minimum_before = min(minimum_before, signed)
        if signed >= CLEARANCE:
            continue
        target = location + normal * CLEARANCE
        delta = (target - world).length
        point.position = inverse @ target
        moved += 1
        maximum = max(maximum, delta)
    obj.data.update_tag()
    return {
        "pointsMoved": moved,
        "maximumMoveMm": maximum * 1000.0,
        "minimumSignedBeforeMm": minimum_before * 1000.0 if math.isfinite(minimum_before) else None,
        "targetClearanceMm": CLEARANCE * 1000.0,
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
rig = bpy.data.objects[RIG]
if HEAD_BONE not in rig.pose.bones:
    raise RuntimeError(f"Missing head bone: {HEAD_BONE}")

hair = [
    obj for obj in bpy.context.scene.objects
    if obj.type == "CURVES" and bool(obj.get("aevrynd_mainline_hair_collision"))
]
for obj in hair:
    bind_to_head(obj, rig)
    obj["aevrynd_revision"] = "v249r238-head-bound-clearance-hair"
    obj["aevrynd_root_binding"] = "rig head bone; world transform preserved at frame 1"

scene.frame_set(1)
bpy.context.view_layer.update()
body_tree = evaluated_tree(bpy.data.objects[BODY], bpy.context.evaluated_depsgraph_get())
repair = {name: project_clear(bpy.data.objects[name], body_tree) for name in ROOT_VEILS}

head_world_1 = rig.matrix_world @ rig.pose.bones[HEAD_BONE].matrix
root_local_1 = {
    obj.name: list(head_world_1.inverted() @ (obj.matrix_world @ obj.data.points[0].position))
    for obj in hair if len(obj.data.points)
}
scene.frame_set(20)
bpy.context.view_layer.update()
head_world_20 = rig.matrix_world @ rig.pose.bones[HEAD_BONE].matrix
root_local_20 = {
    obj.name: list(head_world_20.inverted() @ (obj.matrix_world @ obj.data.points[0].position))
    for obj in hair if len(obj.data.points)
}
root_drift = {
    name: sum((root_local_20[name][axis] - values[axis]) ** 2 for axis in range(3)) ** 0.5
    for name, values in root_local_1.items()
}

scene.frame_set(1)
scene["aevrynd_mainline_revision"] = "v249r238-head-bound-clearance-hair"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_hair_dynamic_binding"] = "HEAD_BONE_RIGID_BASELINE"
scene["aevrynd_release_state"] = "FULL_STATIC_COLLISION_AUDIT_PENDING"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "headBone": HEAD_BONE,
    "boundObjects": [obj.name for obj in hair],
    "maximumRootDriftM": max(root_drift.values(), default=0.0),
    "rootDriftM": root_drift,
    "rootVeilRepair": repair,
    "secondaryMotion": False,
    "status": "FULL_STATIC_COLLISION_AUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R238_HEAD_BOUND_CLEARANCE_HAIR=" + json.dumps(report, sort_keys=True))
