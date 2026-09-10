import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-curly-head-binding-r160.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-curly-collision-prune-r162.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-curly-collision-prune-r162.build-report.json"
BODY = "AevryndFemaleBodyBaseV118"
HAIR = "AevryndFemaleOwnedCurlyHairMain_v249r160"
FRAMES = (1, 20)
NEAR = 0.025
LIMIT = -0.0005


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def unsafe_curve_indices(obj, scene):
    unsafe = set()
    per_frame = {}
    minimum = math.inf
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        tree = evaluated_tree(bpy.data.objects[BODY], bpy.context.evaluated_depsgraph_get())
        frame_unsafe = set()
        for curve_index, curve in enumerate(obj.data.curves):
            for local_index in range(curve.points_length):
                point = obj.data.points[curve.first_point_index + local_index]
                world = obj.matrix_world @ point.position
                hit = tree.find_nearest(world)
                if hit is None or hit[1] is None or hit[3] > NEAR:
                    continue
                signed = (world - hit[0]).dot(hit[1].normalized())
                minimum = min(minimum, signed)
                if signed < LIMIT:
                    frame_unsafe.add(curve_index)
                    break
        unsafe.update(frame_unsafe)
        per_frame[str(frame)] = len(frame_unsafe)
    return unsafe, per_frame, minimum


def rebuild(source, unsafe):
    safe_curves = [
        (index, curve) for index, curve in enumerate(source.data.curves)
        if index not in unsafe
    ]
    name = "AevryndFemaleOwnedCurlyHairMain_v249r162"
    data = bpy.data.hair_curves.new(name + "Data")
    data.add_curves([curve.points_length for _, curve in safe_curves])
    source_radius = source.data.attributes.get("radius")
    target_radius = data.attributes.new("radius", "FLOAT", "POINT")
    target_index = 0
    for _, curve in safe_curves:
        for local_index in range(curve.points_length):
            source_index = curve.first_point_index + local_index
            data.points[target_index].position = source.data.points[source_index].position
            target_radius.data[target_index].value = source_radius.data[source_index].value
            target_index += 1
    for material in source.data.materials:
        data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    world = source.matrix_world.copy()
    obj.parent = source.parent
    obj.parent_type = source.parent_type
    obj.parent_bone = source.parent_bone
    obj.matrix_parent_inverse = source.matrix_parent_inverse.copy()
    obj.matrix_world = world
    for key, value in source.items():
        obj[key] = value
    obj["aevrynd_revision"] = "v249r162"
    obj["aevrynd_collision_method"] = "remove complete curves penetrating at frame 1 or 20"
    obj["aevrynd_collision_frames"] = list(FRAMES)
    obj["aevrynd_collision_status"] = "PENDING_STRICT_AUDIT"
    return obj, len(safe_curves)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
source = bpy.data.objects[HAIR]
unsafe, per_frame, minimum = unsafe_curve_indices(source, scene)
scene.frame_set(1)
replacement, safe_count = rebuild(source, unsafe)
source.hide_render = True
source.hide_viewport = True
source["aevrynd_replaced_by"] = replacement.name
scene["aevrynd_revision"] = "v249r162"
scene["aevrynd_candidate_status"] = "COLLISION_AND_VISUAL_REVIEW_PENDING"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE), "output": str(OUTPUT),
    "sourceCurves": len(source.data.curves), "sourcePoints": len(source.data.points),
    "unsafeCurvesByFrame": per_frame, "removedUnionCurves": len(unsafe),
    "remainingCurves": safe_count, "remainingPoints": len(replacement.data.points),
    "retainedCurveRatio": safe_count / len(source.data.curves),
    "minimumSignedM": minimum if math.isfinite(minimum) else None,
    "runtimeDependency": "none", "status": "COLLISION_REAUDIT_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R162_BUILD=" + json.dumps(report, sort_keys=True))
