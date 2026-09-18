"""Break the regular comb silhouette while preserving collision-safe r1098 lash roots."""
from pathlib import Path
import itertools
import json
import math
import os
import random

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-lash-root-alignment-r1098-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-natural-lash-variation-r1099-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1099-natural-lash-variation-sweep.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1099-natural-lash-variation"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
FRAMES = (1, 20, 33, 61)
# label, fibre radius scale, length variation, temporal fan, upward curl, clump offset (metres)
VARIANTS = (
    ("a-restrained", 0.76, 0.08, 0.00022, 0.00020, 0.000045),
    ("b-natural", 0.64, 0.15, 0.00040, 0.00032, 0.000075),
    ("c-delicate", 0.54, 0.20, 0.00052, 0.00040, 0.000095),
)
SELECTED = "c-delicate"
REQUESTED_VARIANT = os.environ.get("AEVRYND_VARIANT")


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def strand_rings(obj):
    adjacency = {vertex.index: set() for vertex in obj.data.vertices}; edges = set()
    for edge in obj.data.edges:
        first, second = edge.vertices; adjacency[first].add(second); adjacency[second].add(first); edges.add(tuple(sorted((first, second))))
    remaining = set(adjacency); strands = []
    while remaining:
        seed = remaining.pop(); stack = [seed]; component = {seed}
        while stack:
            current = stack.pop(); fresh = adjacency[current] & remaining
            remaining.difference_update(fresh); component.update(fresh); stack.extend(fresh)
        rings = []
        for triple in itertools.combinations(component, 3):
            if all(tuple(sorted(pair)) in edges for pair in itertools.combinations(triple, 2)):
                centre = sum((obj.data.vertices[index].co for index in triple), Vector()) / 3.0
                rings.append((centre, triple))
        rings.sort(key=lambda item: item[0].y, reverse=True)
        if not rings: raise RuntimeError(f"no triangular rings in {obj.name}")
        strands.append(rings)
    return strands


def reshape(obj, side, radius_scale, variation, fan_tip, curl_tip, clump_tip):
    strands = strand_rings(obj); sign = 1.0 if side == "L" else -1.0
    ordered = sorted(strands, key=lambda rings: abs((obj.matrix_world @ rings[0][0]).x))
    count = len(ordered); rng = random.Random(109900 + (0 if side == "L" else 1000))
    inverse3 = obj.matrix_world.inverted().to_3x3(); root_moves = []; maximum = 0.0; factors = []
    for order, rings in enumerate(ordered):
        root_local = rings[0][0].copy(); root_world_before = obj.matrix_world @ root_local
        temporal = order / max(1, count - 1)
        hierarchy = 0.82 + 0.24 * temporal
        irregular = variation * (0.58 * math.sin(order * 2.17 + 0.4) + 0.42 * rng.uniform(-1.0, 1.0))
        length_factor = max(0.62, hierarchy + irregular); factors.append(length_factor)
        pair = -1.0 if order % 4 in (0, 1) else 1.0
        random_clump = pair * clump_tip * (0.45 + 0.55 * rng.random())
        for ring_index, (centre, triple) in enumerate(rings):
            t = ring_index / max(1, len(rings) - 1); ease = t * t * (3.0 - 2.0 * t)
            centre_world = obj.matrix_world @ centre
            path_world = root_world_before + (centre_world - root_world_before) * (1.0 + (length_factor - 1.0) * ease)
            path_world.x += sign * fan_tip * (temporal - 0.18) * ease + sign * random_clump * math.sin(math.pi * t)
            path_world.z += curl_tip * (0.38 + 0.62 * temporal) * ease
            new_centre = obj.matrix_world.inverted() @ path_world
            ring_scale = radius_scale * (1.0 - 0.10 * t)
            for index in triple:
                old = obj.data.vertices[index].co.copy()
                radial = old - centre
                obj.data.vertices[index].co = new_centre + radial * ring_scale
                maximum = max(maximum, (obj.data.vertices[index].co - old).length)
        root_after = obj.matrix_world @ (sum((obj.data.vertices[index].co for index in rings[0][1]), Vector()) / 3.0)
        root_moves.append((root_after - root_world_before).length)
    obj.data.update()
    return {
        "strands": count,
        "radiusScale": radius_scale,
        "lengthFactorRange": [min(factors), max(factors)],
        "fanTipMm": fan_tip * 1000.0,
        "curlTipMm": curl_tip * 1000.0,
        "clumpTipMm": clump_tip * 1000.0,
        "rootCentroidMaximumMoveMm": max(root_moves) * 1000.0,
        "maximumVertexMoveMm": maximum * 1000.0,
    }


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph); mesh = evaluated.to_mesh(); vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles(); triangles = [tuple(item.vertices) for item in mesh.loop_triangles]; evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, triangles, all_triangles=True)


def collision_frames(body):
    results, failures = {}, []
    for frame in FRAMES:
        bpy.context.scene.frame_set(frame); deps = bpy.context.evaluated_depsgraph_get(); deps.update(); body_tree = world_tree(body, deps); frame_result = {}
        for side in ("L", "R"):
            upper = world_tree(bpy.data.objects[f"Eye_{side}_UpperLashes"], deps)
            lower = world_tree(bpy.data.objects[f"Eye_{side}_LowerLashes"], deps)
            sclera = world_tree(bpy.data.objects[f"Eye_{side}_Sclera"], deps)
            cornea = world_tree(bpy.data.objects[f"Eye_{side}_Cornea"], deps)
            values = {"upperBody": len(upper.overlap(body_tree)), "upperSclera": len(upper.overlap(sclera)), "upperCornea": len(upper.overlap(cornea)), "upperLower": len(upper.overlap(lower))}
            frame_result[side] = values
            for pair, count in values.items():
                if count: failures.append({"frame": frame, "side": side, "pair": pair, "triangleOverlapCount": count})
        results[str(frame)] = frame_result
    return results, failures


def render(scene, label, view):
    camera = scene.camera
    if view == "eye-front": camera.location, target, camera.data.lens, size = (0.0, -0.405, 1.449), (0.0, -0.105, 1.449), 135, (1400, 760)
    elif view == "eye-oblique": camera.location, target, camera.data.lens, size = (0.235, -0.405, 1.451), (0.0, -0.105, 1.449), 135, (1400, 760)
    else: camera.location, target, camera.data.lens, size = (0.0, -0.72, 1.445), (0.0, -0.025, 1.445), 88, (1000, 1000)
    look_at(camera, target); scene.render.resolution_x, scene.render.resolution_y = size; scene.render.resolution_percentage = 100
    path = OUT / f"{label}-{view}.png"; scene.render.filepath = str(path); bpy.ops.render.render(write_still=True); return str(path)


OUT.mkdir(parents=True, exist_ok=True); variants = []
active_variants = tuple(item for item in VARIANTS if REQUESTED_VARIANT in (None, item[0]))
if not active_variants: raise RuntimeError(f"unknown AEVRYND_VARIANT={REQUESTED_VARIANT}")
for label, radius_scale, variation, fan_tip, curl_tip, clump_tip in active_variants:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); scene = bpy.context.scene; scene.frame_set(1); body = bpy.data.objects[BODY]; edits = {}
    for side in ("L", "R"): edits[side] = reshape(bpy.data.objects[f"Eye_{side}_UpperLashes"], side, radius_scale, variation, fan_tip, curl_tip, clump_tip)
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")): obj.hide_render = True
    bpy.context.view_layer.update(); collisions, failures = collision_frames(body); scene.frame_set(1); bpy.context.view_layer.update(); renders = [render(scene, label, view) for view in ("eye-front", "eye-oblique", "face-front")]
    status = "TECHNICAL_PASS" if not failures and max(edit["rootCentroidMaximumMoveMm"] for edit in edits.values()) < 0.001 else "TECHNICAL_FAIL"
    variants.append({"label": label, "edits": edits, "collisionFrames": collisions, "collisionFailures": failures, "renders": renders, "status": status})
    if label == SELECTED and status == "TECHNICAL_PASS":
        body["aevrynd_revision"] = "v249r1099-natural-lash-variation"; body["aevrynd_source"] = SOURCE.name
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"; scene["aevrynd_website_promotion"] = "forbidden"; bpy.context.preferences.filepaths.save_version = 0; bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {"revision": "v249r1099-natural-lash-variation-sweep", "source": str(SOURCE), "output": str(OUTPUT), "method": "preserve each r1098 root-ring centroid while thinning fibres and adding deterministic human length hierarchy, temporal fan, curl and small paired clumping", "variants": variants, "selectedVariant": SELECTED, "websitePromotionApproved": False, "candidateStatus": "VISUAL_REVIEW_PENDING"}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1099_NATURAL_LASHES=" + json.dumps({"selected": SELECTED, "variants": [{"label": item["label"], "edits": item["edits"], "failures": len(item["collisionFailures"]), "status": item["status"]} for item in variants]}, sort_keys=True))
