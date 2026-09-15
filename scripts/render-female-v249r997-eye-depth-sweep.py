"""Sweep current owned eye layers inward to find the deepest zero-overlap fit."""

import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-target-native-lashes-r995.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-eye-depth-sweep-r997.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r997-eye-depth-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
EYES = tuple(f"Eye_{side}_{layer}" for side in ("L", "R") for layer in ("Sclera", "Cornea", "Iris"))
OFFSETS = (("a-current", 0.0), ("b-inward-0p5mm", 0.0005),
           ("c-inward-1p0mm", 0.0010), ("d-inward-1p5mm", 0.0015))


def world_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def set_offset(objects, snapshots, offset):
    delta = Vector((0.0, offset, 0.0))
    for obj in objects:
        inverse = obj.matrix_world.inverted()
        for vertex, original in zip(obj.data.vertices, snapshots[obj.name]):
            vertex.co = inverse @ (original + delta)
        obj.data.update()


def overlaps(body_tree, objects):
    return {obj.name: len(world_tree(obj).overlap(body_tree)) for obj in objects}


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
objects = [bpy.data.objects[name] for name in EYES]
snapshots = {obj.name: [obj.matrix_world @ vertex.co for vertex in obj.data.vertices] for obj in objects}
body_tree = world_tree(bpy.data.objects[BODY])
RENDER_DIR.mkdir(parents=True, exist_ok=True)
scene.render.resolution_x = scene.render.resolution_y = 900
camera = scene.camera
scene.camera = camera
camera.location = (0.0, -0.48, 1.485)
camera.data.lens = 105
look_at(camera, (0.0, -0.060, 1.485))
results = []
for label, offset in OFFSETS:
    set_offset(objects, snapshots, offset)
    bpy.context.view_layer.update()
    counts = overlaps(body_tree, objects)
    scene.render.filepath = str(RENDER_DIR / f"{label}.png")
    bpy.ops.render.render(write_still=True)
    results.append({"label": label, "inwardOffsetM": offset, "bodyTriangleOverlaps": counts,
                    "totalBodyTriangleOverlaps": sum(counts.values()),
                    "status": "PASS" if not sum(counts.values()) else "FAIL"})

set_offset(objects, snapshots, 0.0)
report = {"source": str(SOURCE), "studyOnly": True, "eyeObjects": list(EYES),
          "results": results, "selected": None,
          "status": "VISUAL_REVIEW_REQUIRED"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R997_EYE_DEPTH_SWEEP=" + json.dumps(report, sort_keys=True))
