import json
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-lower-face-clearance-r569.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-optical-aware-canthus-r597.blend"
REPORT = ASSETS / "female-v249-mainline-optical-aware-canthus-r597.build.json"
REVIEW = ASSETS / "reviews/v249r597-optical-aware-canthus"
BODY = "AevryndFemaleBodyBaseV118"
EYES = {"L": 0.03453, "R": -0.03444}
OPTICAL = tuple(f"Eye_{side}_{part}" for side in EYES for part in ("Cornea", "Sclera"))


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def geometry(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return points, faces


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY]
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(depsgraph)
mesh = evaluated.to_mesh()
world_points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
evaluated.to_mesh_clear()

adjacency = defaultdict(set)
for edge in body.data.edges:
    first, second = edge.vertices
    adjacency[first].add(second)
    adjacency[second].add(first)
selected = {}
for index, point in enumerate(world_points):
    if point.y > -0.074 or not (1.600 < point.z < 1.620):
        continue
    for center_x in EYES.values():
        outward = 1.0 if center_x > 0.0 else -1.0
        dx = abs(point.x - (center_x + outward * 0.0104))
        dz = abs(point.z - 1.6102)
        if dx < 0.0090 and dz < 0.0100:
            weight = (1.0 - smoothstep((dx - 0.0040) / 0.0050)) * (1.0 - smoothstep((dz - 0.0050) / 0.0050))
            if weight > 0.01:
                selected[index] = weight
            break

one_iteration = {}
for index, weight in selected.items():
    neighbors = adjacency[index]
    if not neighbors:
        continue
    average = sum((world_points[neighbor] for neighbor in neighbors), Vector()) / len(neighbors)
    proposal = world_points[index].lerp(average, 0.42 * weight)
    proposal.y = world_points[index].y
    delta = proposal - world_points[index]
    if delta.length > 0.00135:
        delta = delta.normalized() * 0.00135
    if delta.length > 0.000001:
        one_iteration[index] = delta

shape_keys = list(body.data.shape_keys.key_blocks)
original = [[point.co.copy() for point in key.data] for key in shape_keys]
inverse3 = body.matrix_world.inverted().to_3x3()


def apply(deltas):
    for key_index, key in enumerate(shape_keys):
        for index, source in enumerate(original[key_index]):
            movement = deltas.get(index)
            key.data[index].co = source if movement is None else source + inverse3 @ movement
    body.data.update()


active = dict(one_iteration)
removed = set()
repair_history = []
final_overlap = {}
for repair_iteration in range(8):
    apply(active)
    scene.frame_set(1)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_points, body_faces = geometry(body, depsgraph)
    body_tree = BVHTree.FromPolygons(body_points, body_faces, all_triangles=False)
    offenders = set()
    overlap_counts = {}
    for name in OPTICAL:
        points, faces = geometry(bpy.data.objects[name], depsgraph)
        pairs = body_tree.overlap(BVHTree.FromPolygons(points, faces, all_triangles=False))
        overlap_counts[name] = len(pairs)
        for body_face, _optical_face in pairs:
            offenders.update(body_faces[body_face])
    final_overlap = overlap_counts
    active_offenders = offenders.intersection(active)
    repair_history.append({
        "iteration": repair_iteration,
        "overlapPairs": overlap_counts,
        "activeOffendingVertices": len(active_offenders),
    })
    if not any(overlap_counts.values()):
        break
    if not active_offenders:
        break
    for index in active_offenders:
        active.pop(index, None)
        removed.add(index)

apply(active)
scene.frame_set(1)
bpy.context.view_layer.update()
scene["aevrynd_mainline_revision"] = "v249r597-optical-aware-canthus"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "OFFLINE_TECHNICAL_CANDIDATE_AUDITS_PENDING"
body["aevrynd_face_revision"] = "v249r597"
body["aevrynd_face_method"] = "single bounded outer-canthus Laplacian step with exact optical-overlap vertex rollback"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)

for obj in bpy.data.objects:
    name = obj.name.lower()
    layer = str(obj.get("aevrynd_layer", "")).lower()
    if "hair" in name or layer.startswith("hair"):
        obj.hide_render = True
        obj.hide_viewport = True
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_percentage = 100
REVIEW.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
for label, location, target, lens, size in (
    ("01-face-front", (0.0, -0.57, 1.565), (0.0, -0.040, 1.555), 104, (1000, 1000)),
    ("02-eye-front", (0.0, -0.405, 1.610), (0.0, -0.105, 1.610), 135, (1400, 760)),
    ("03-eye-oblique", (0.235, -0.405, 1.612), (0.0, -0.105, 1.610), 135, (1400, 760)),
):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(REVIEW / f"{label}.png")
    bpy.ops.render.render(write_still=True)

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "selectedVertices": len(selected),
    "initialMovedVertices": len(one_iteration),
    "retainedMovedVertices": len(active),
    "opticalRollbackVertices": len(removed),
    "maximumRetainedMoveM": max((value.length for value in active.values()), default=0.0),
    "repairHistory": repair_history,
    "frame1FinalOverlapPairs": final_overlap,
    "shapeKeysMovedTogether": [key.name for key in shape_keys],
    "topologyChanged": False,
    "runtimeDependencyAdded": False,
    "status": "BUILT_FRAME1_PASS_PENDING_FULL_DYNAMIC_FACE_AUDIT" if not any(final_overlap.values()) else "REJECTED_FRAME1_COLLISION_REMAINS",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R597_OPTICAL_AWARE_CANTHUS=" + json.dumps(report, sort_keys=True))
if any(final_overlap.values()):
    raise SystemExit(2)
