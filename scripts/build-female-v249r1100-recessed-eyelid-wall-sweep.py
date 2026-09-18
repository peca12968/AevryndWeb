"""Recess the two eyelid wall rings so they read as lid thickness instead of slabs."""
from collections import defaultdict
from pathlib import Path
import json
import os

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-natural-lash-variation-r1099-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-recessed-eyelid-wall-r1100-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1100-recessed-eyelid-wall-sweep.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1100-recessed-eyelid-wall"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
ORIGINAL_VERTEX_COUNT = 13817
FRAMES = (1, 20, 33, 61)
# label, ring-one depth, ring-two depth, retained compatibility fields
VARIANTS = (
    ("a-shallow", 0.00010, 0.00020, 0.35, 0.55),
    ("b-anatomical", 0.00018, 0.00036, 0.55, 0.78),
    ("c-deep", 0.00026, 0.00052, 0.70, 0.90),
)
SELECTED = "c-deep"
REQUESTED_VARIANT = os.environ.get("AEVRYND_VARIANT")


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def wall_mapping(body):
    adjacency = defaultdict(list)
    for edge in body.data.edges:
        a, b = edge.vertices; adjacency[a].append(b); adjacency[b].append(a)
    outer = set()
    for polygon in body.data.polygons:
        old = [index for index in polygon.vertices if index < ORIGINAL_VERTEX_COUNT]
        wall = [index for index in polygon.vertices if ORIGINAL_VERTEX_COUNT <= index < ORIGINAL_VERTEX_COUNT + 180]
        if len(polygon.vertices) == 4 and len(old) == 2 and len(wall) == 2: outer.update(old)
    mapping1 = {}
    for old in outer:
        candidates = [index for index in adjacency[old] if ORIGINAL_VERTEX_COUNT <= index < ORIGINAL_VERTEX_COUNT + 180]
        if len(candidates) != 1: raise RuntimeError(f"outer vertex {old} has {len(candidates)} first-ring neighbours")
        mapping1[old] = candidates[0]
    first_ring = set(mapping1.values()); mapping2 = {}
    for old, first in mapping1.items():
        candidates = [index for index in adjacency[first] if ORIGINAL_VERTEX_COUNT <= index < ORIGINAL_VERTEX_COUNT + 180 and index not in first_ring]
        if len(candidates) != 1: raise RuntimeError(f"first-ring vertex {first} has {len(candidates)} second-ring neighbours")
        mapping2[old] = candidates[0]
    if len(outer) != 90 or len(set(mapping1.values())) != 90 or len(set(mapping2.values())) != 90: raise RuntimeError("expected 90 paired wall vertices per ring")
    return mapping1, mapping2


def recess_walls(body, depth1, depth2, shrink1, shrink2):
    mapping1, mapping2 = wall_mapping(body); local_depth1 = body.matrix_world.inverted().to_3x3() @ Vector((0.0, depth1, 0.0)); local_depth2 = body.matrix_world.inverted().to_3x3() @ Vector((0.0, depth2, 0.0)); maximum = 0.0
    basis = body.data.shape_keys.key_blocks[0]
    weights = {}
    for side in ("L", "R"):
        indices = [index for index in mapping1 if (basis.data[index].co.x > 0) == (side == "L")]
        inner = min(abs(basis.data[index].co.x) for index in indices); outer = max(abs(basis.data[index].co.x) for index in indices)
        for index in indices:
            u = (abs(basis.data[index].co.x) - inner) / max(outer - inner, 1e-9)
            value = max(0.0, min(1.0, (0.27 - u) / 0.27)); weights[index] = value * value * (3.0 - 2.0 * value)
    for block in body.data.shape_keys.key_blocks:
        for old, first in mapping1.items():
            source = block.data[old].co.copy()
            for index, depth, collapse in ((first, local_depth1, shrink1), (mapping2[old], local_depth2, shrink2)):
                target = block.data[index].co.copy()
                target.y += ((source + depth).y - target.y) * weights[old]
                target.x += (source.x - target.x) * collapse * weights[old]
                target.z += (source.z - target.z) * collapse * weights[old]
                maximum = max(maximum, (block.data[index].co - target).length); block.data[index].co = target
    body.data.update()
    return {"outerVertices": 90, "ring1Vertices": 90, "ring2Vertices": 90, "medialWeightedVertices": sum(value > 0.0 for value in weights.values()), "shapeKeysUpdated": len(body.data.shape_keys.key_blocks), "ring1DepthMm": depth1 * 1000.0, "ring2DepthMm": depth2 * 1000.0, "ring1RadialShrink": shrink1, "ring2RadialShrink": shrink2, "maximumCorrectionMm": maximum * 1000.0}


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph); mesh = evaluated.to_mesh(); vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles(); triangles = [tuple(item.vertices) for item in mesh.loop_triangles]; evaluated.to_mesh_clear(); return BVHTree.FromPolygons(vertices, triangles, all_triangles=True)


def collision_frames(body):
    results, failures = {}, []
    for frame in FRAMES:
        bpy.context.scene.frame_set(frame); deps = bpy.context.evaluated_depsgraph_get(); deps.update(); body_tree = world_tree(body, deps); result = {}
        for side in ("L", "R"):
            result[side] = {}
            for layer in ("Sclera", "Cornea", "Iris", "UpperLashes", "LowerLashes"):
                count = len(body_tree.overlap(world_tree(bpy.data.objects[f"Eye_{side}_{layer}"], deps))); result[side][layer] = count
                if count: failures.append({"frame": frame, "side": side, "layer": layer, "triangleOverlapCount": count})
        results[str(frame)] = result
    return results, failures


def render(scene, label, view):
    camera = scene.camera
    if view == "eye-front": camera.location, target, camera.data.lens, size = (0.0, -0.405, 1.449), (0.0, -0.105, 1.449), 135, (1400, 760)
    elif view == "eye-oblique": camera.location, target, camera.data.lens, size = (0.235, -0.405, 1.451), (0.0, -0.105, 1.449), 135, (1400, 900)
    else: camera.location, target, camera.data.lens, size = (0.0, -0.72, 1.445), (0.0, -0.025, 1.445), 88, (1000, 1000)
    look_at(camera, target); scene.render.resolution_x, scene.render.resolution_y = size; scene.render.resolution_percentage = 100
    path = OUT / f"{label}-{view}.png"; scene.render.filepath = str(path); bpy.ops.render.render(write_still=True); return str(path)


OUT.mkdir(parents=True, exist_ok=True); variants = []
active_variants = tuple(item for item in VARIANTS if REQUESTED_VARIANT in (None, item[0]))
if not active_variants: raise RuntimeError(f"unknown AEVRYND_VARIANT={REQUESTED_VARIANT}")
for label, depth1, depth2, shrink1, shrink2 in active_variants:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); scene = bpy.context.scene; scene.frame_set(1); body = bpy.data.objects[BODY]; patch = recess_walls(body, depth1, depth2, shrink1, shrink2)
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")): obj.hide_render = True
    bpy.context.view_layer.update(); collisions, failures = collision_frames(body); scene.frame_set(1); bpy.context.view_layer.update(); renders = [render(scene, label, view) for view in ("eye-front", "eye-oblique", "face-front")]
    status = "TECHNICAL_PASS" if not failures else "TECHNICAL_FAIL"; variants.append({"label": label, "patch": patch, "collisionFrames": collisions, "collisionFailures": failures, "renders": renders, "status": status})
    if label == SELECTED and status == "TECHNICAL_PASS":
        body["aevrynd_revision"] = "v249r1100-recessed-eyelid-wall"; body["aevrynd_source"] = SOURCE.name
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"; scene["aevrynd_website_promotion"] = "forbidden"; bpy.context.preferences.filepaths.save_version = 0; bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {"revision": "v249r1100-recessed-eyelid-wall-sweep", "source": str(SOURCE), "output": str(OUTPUT), "method": "rebuild both existing eyelid wall rings from each current aperture vertex, moving them progressively inward along view depth and slightly toward the scleral centre across every shape key", "variants": variants, "selectedVariant": SELECTED, "websitePromotionApproved": False, "candidateStatus": "VISUAL_REVIEW_PENDING"}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1100_RECESSED_WALL=" + json.dumps({"selected": SELECTED, "variants": [{"label": item["label"], "patch": item["patch"], "failures": len(item["collisionFailures"]), "status": item["status"]} for item in variants]}, sort_keys=True))
