import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-long-hair-bound-r88.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-long-hair-multiframe-r89.blend"
BODY = "AevryndFemaleBodyBaseV118"
HAIR = (
    "AevryndFemaleCC0LongHairFitMain_v249r86",
    "AevryndFemaleCC0LongHairFitFlyaway_v249r86",
)
TARGET = 0.0015
NEAR = 0.030


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def correct_frame(obj, tree):
    inverse = obj.matrix_world.inverted()
    corrected = 0
    maximum = 0.0
    for point in obj.data.points:
        world = obj.matrix_world @ point.position
        hit = tree.find_nearest(world)
        if hit is None or hit[1] is None or hit[3] > NEAR:
            continue
        normal = hit[1].normalized()
        signed = (world - hit[0]).dot(normal)
        if signed >= TARGET:
            continue
        delta = normal * (TARGET - signed)
        point.position = inverse @ (world + delta)
        corrected += 1
        maximum = max(maximum, delta.length)
    obj.data.update_tag()
    return corrected, maximum


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
passes = []
for pass_index in range(3):
    record = {"pass": pass_index + 1, "frames": {}}
    for frame in (1, 20):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        tree = evaluated_tree(bpy.data.objects[BODY], bpy.context.evaluated_depsgraph_get())
        values = {}
        for name in HAIR:
            corrected, maximum = correct_frame(bpy.data.objects[name], tree)
            values[name] = {"corrected": corrected, "max_correction_mm": maximum * 1000.0}
        record["frames"][str(frame)] = values
    passes.append(record)

for name in HAIR:
    obj = bpy.data.objects[name]
    obj["aevrynd_revision"] = "v249-mainline-cc0-long-hair-multiframe-r89"
    obj["aevrynd_collision_frames"] = "1,20"
    obj["aevrynd_collision_clearance_m"] = TARGET
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "cc0-long-hair-multiframe-r89"
scene["aevrynd_release_state"] = "R89_STATIC_REAUDIT_AND_DYNAMIC_GROOM_REQUIRED"
scene.frame_set(1)
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "target_clearance_m": TARGET,
    "passes": passes, "status": "REAUDIT_REQUIRED",
}
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_CC0_LONG_HAIR_MULTIFRAME_R89=" + json.dumps(report, sort_keys=True))
