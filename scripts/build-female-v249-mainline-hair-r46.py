import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r45.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r46.blend"
MAIN = "AevryndFemaleGuideBob_v249r45"
BODY = "AevryndFemaleBodyBaseV118"
POINTS = 20
CURVE = 6827
CENTER = 10
TARGET_CLEARANCE = 0.0025


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
depsgraph = bpy.context.evaluated_depsgraph_get()
body_tree = evaluated_tree(bpy.data.objects[BODY], depsgraph)
hair = bpy.data.objects[MAIN]
inverse = hair.matrix_world.inverted()
changed = []
for point_index in range(7, 14):
    index = CURVE * POINTS + point_index
    point = hair.data.points[index]
    world = hair.matrix_world @ point.position
    nearest = body_tree.find_nearest(world)
    if nearest is None or nearest[1] is None:
        continue
    location, normal = nearest[0], nearest[1].normalized()
    signed = (world - location).dot(normal)
    envelope = 0.5 + 0.5 * math.cos((point_index - CENTER) * math.pi / 4.0)
    correction = max(0.0, TARGET_CLEARANCE - signed) * envelope
    point.position = inverse @ (world + normal * correction)
    changed.append({
        "point_index": point_index,
        "flat_index": index,
        "before_signed_m": signed,
        "correction_m": correction,
    })
hair.data.update_tag()
hair.name = "AevryndFemaleGuideBob_v249r46"
hair.data.name = "AevryndFemaleGuideBobData_v249r46"
hair["aevrynd_candidate"] = "v249-mainline-hair-r46"
hair["aevrynd_dynamic_collision_repair"] = "curve 6827 points 7-13 outward body-normal clearance"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_hair_candidate"] = "v249-mainline-hair-r46"
scene["aevrynd_release_state"] = "HAIR_R46_PENDING_STATIC_RUNTIME_AND_DYNAMIC_COLLISION_REVIEW"

payload = {"source": str(SOURCE), "output": str(OUTPUT), "curve": CURVE, "changed": changed}
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_MAINLINE_HAIR_R46=" + json.dumps(payload, sort_keys=True))
