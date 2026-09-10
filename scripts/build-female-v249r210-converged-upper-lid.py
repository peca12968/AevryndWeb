import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-collision-safe-mouth-r200.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-converged-upper-lid-r210.build-report.json"
BODY = "AevryndFemaleBodyBaseV118"
EYES = (0.034528, -0.034443)
TEARS = ("Eye_L_TearMeniscus", "Eye_R_TearMeniscus")
STRENGTH = 1.75
LASH_CLEARANCE = 0.00045
MAX_GUARD_ITERATIONS = 16


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def consolidate(body, name):
    key = body.shape_key_add(name=name, from_mix=True)
    previous = [old.name for old in body.data.shape_keys.key_blocks[1:-1]]
    for old in body.data.shape_keys.key_blocks[1:-1]:
        old.value = 0.0
    key.value = 1.0
    return key, previous


def upper_weight(p, center_x):
    dx = (p.x - center_x) / 0.0315
    if abs(dx) >= 1.05 or p.y > -0.094 or not (1.595 < p.z < 1.626):
        return 0.0
    horizontal = max(0.0, 1.0 - (abs(dx) / 1.05) ** 3) ** 1.35
    return horizontal * gaussian(p.y, -0.126, 0.023) * gaussian(p.z, 1.6096, 0.0037)


def open_upper_lid(key):
    moved = 0
    maximum = 0.0
    for point in key.data:
        weight = max(upper_weight(point.co, center_x) for center_x in EYES)
        delta = STRENGTH * 0.00100 * weight
        if delta <= 1e-7:
            continue
        point.co.z += delta
        moved += 1
        maximum = max(maximum, delta)
    return {"verticesMovedBeforeGuard": moved, "maximumMoveMm": maximum * 1000.0}


def move_lashes(obj):
    obj.data = obj.data.copy()
    inverse = obj.matrix_world.inverted()
    maximum_z = 0.0
    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        horizontal = 0.0
        for center_x in EYES:
            dx = (world.x - center_x) / 0.0315
            if abs(dx) < 1.08:
                horizontal = max(horizontal, max(0.0, 1.0 - (abs(dx) / 1.08) ** 3) ** 1.35)
        delta_z = STRENGTH * 0.00100 * horizontal * gaussian(world.z, 1.6096, 0.0042)
        world.z += delta_z
        world.y -= LASH_CLEARANCE
        vertex.co = inverse @ world
        maximum_z = max(maximum_z, delta_z)
    obj.data.update()
    obj["aevrynd_face_revision"] = "v249r210"
    obj["aevrynd_clearance_offset_mm"] = LASH_CLEARANCE * 1000.0
    return {"verticesMoved": len(obj.data.vertices), "maximumVerticalMoveMm": maximum_z * 1000.0, "outwardClearanceMm": LASH_CLEARANCE * 1000.0}


def geometry(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return points, faces


def overlap_body_faces(body, tear, depsgraph):
    body_points, body_faces = geometry(body, depsgraph)
    tear_points, tear_faces = geometry(tear, depsgraph)
    body_tree = BVHTree.FromPolygons(body_points, body_faces, all_triangles=False)
    tear_tree = BVHTree.FromPolygons(tear_points, tear_faces, all_triangles=False)
    return sorted(set(first for first, _second in body_tree.overlap(tear_tree)))


def converge_tear_guard(scene, body, key, baseline):
    guarded_faces = set()
    guarded_vertices = set()
    iterations = []
    for iteration in range(MAX_GUARD_ITERATIONS):
        frame_layers = {}
        new_faces = set()
        for frame in (1, 20):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            depsgraph = bpy.context.evaluated_depsgraph_get()
            frame_layers[str(frame)] = {}
            for name in TEARS:
                faces = overlap_body_faces(body, bpy.data.objects[name], depsgraph)
                frame_layers[str(frame)][name] = faces
                new_faces.update(faces)
        iterations.append({
            "iteration": iteration,
            "overlaps": {frame: {name: len(faces) for name, faces in layers.items()} for frame, layers in frame_layers.items()},
            "bodyFaces": sorted(new_faces),
        })
        if not new_faces:
            break
        unseen = new_faces - guarded_faces
        if not unseen:
            break
        guarded_faces.update(unseen)
        for face_index in unseen:
            if face_index >= len(body.data.polygons):
                raise RuntimeError(f"evaluated face {face_index} has no base polygon")
            guarded_vertices.update(body.data.polygons[face_index].vertices)
        for vertex_index in guarded_vertices:
            key.data[vertex_index].co = baseline[vertex_index]
        body.data.update()
    final_counts = iterations[-1]["overlaps"]
    passed = all(count == 0 for layers in final_counts.values() for count in layers.values())
    return {
        "iterations": iterations,
        "guardedFaceCount": len(guarded_faces),
        "guardedFaces": sorted(guarded_faces),
        "guardedVertexCount": len(guarded_vertices),
        "status": "PASS" if passed else "FAIL",
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
key, previous = consolidate(body, "Aevrynd_ConvergedUpperLid_R210")
baseline = [point.co.copy() for point in key.data]
metrics = open_upper_lid(key)
metrics["shapeKey"] = key.name
metrics["consolidatedShapeKeys"] = previous
metrics["upperLashes"] = {
    f"Eye_{side}_UpperLashes": move_lashes(bpy.data.objects[f"Eye_{side}_UpperLashes"])
    for side in ("L", "R")
}
body.data.update()
metrics["tearGuard"] = converge_tear_guard(scene, body, key, baseline)
if metrics["tearGuard"]["status"] != "PASS":
    raise RuntimeError("tear guard did not converge")
scene.frame_set(1)
body["aevrynd_face_revision"] = "v249r210"
body["aevrynd_eye_aperture"] = "r205 d-open with converged frame 1/20 topology tear guard and 0.45mm upper-lash clearance"
body["aevrynd_face_layers"] = ["philtrum.consolidated", "eyelid.anatomical.r183", "mouth.placement.r200", "upper_lid.converged_tear_guard.r210"]
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_face_revision"] = "v249r210"
scene["aevrynd_mainline_revision"] = "converged-upper-lid-r210"
scene["aevrynd_release_state"] = "R210_FULL_COLLISION_AND_VISUAL_REVIEW_PENDING"
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "selectedSweepVariant": "r205 d-open",
    "strength": STRENGTH,
    "lashClearanceMm": LASH_CLEARANCE * 1000.0,
    "metrics": metrics,
    "status": "FULL_COLLISION_AND_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249R210_CONVERGED_UPPER_LID=" + json.dumps({
    "output": str(OUTPUT), "tearGuard": metrics["tearGuard"], "status": report["status"]
}, sort_keys=True))
