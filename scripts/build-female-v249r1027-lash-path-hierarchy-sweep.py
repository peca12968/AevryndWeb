"""Author natural lash length hierarchy, temporal fan and curl with fixed roots."""

import itertools
import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-continuous-lateral-canthus-r1026-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-lash-path-hierarchy-r1027-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1027-lash-path-hierarchy-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1027-lash-path-hierarchy-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
FRAMES = (1, 20, 33, 61)
VARIANTS = (
    ("a-restrained", 0.00025, 0.00020, 0.95, 1.10),
    ("b-human-fan", 0.00045, 0.00035, 0.92, 1.18),
    ("c-bold-fan", 0.00070, 0.00050, 0.88, 1.28),
)


def strand_rings(obj):
    adjacency = {vertex.index: set() for vertex in obj.data.vertices}; edges = set()
    for edge in obj.data.edges:
        first, second = edge.vertices; adjacency[first].add(second); adjacency[second].add(first); edges.add(tuple(sorted((first, second))))
    remaining = set(adjacency); strands = []
    while remaining:
        seed = remaining.pop(); stack = [seed]; component = {seed}
        while stack:
            current = stack.pop(); fresh = adjacency[current] & remaining; remaining.difference_update(fresh); component.update(fresh); stack.extend(fresh)
        rings = []
        for triple in itertools.combinations(component, 3):
            if all(tuple(sorted(pair)) in edges for pair in itertools.combinations(triple, 2)):
                center = sum((obj.data.vertices[index].co for index in triple), Vector()) / 3.0; rings.append((center, triple))
        rings.sort(key=lambda item: item[0].y, reverse=True); strands.append(rings)
    return strands


def reshape_lashes(obj, side, upper, fan_tip, curl_tip, medial_length, temporal_length):
    strands = strand_rings(obj); sign = 1.0 if side == "L" else -1.0; center_x = sign * 0.02815; inverse3 = obj.matrix_world.inverted().to_3x3(); moved = set(); max_move = 0.0; root_max = 0.0; lengths = []
    for rings in strands:
        root_local = rings[0][0]; root_world = obj.matrix_world @ root_local; u = (root_world.x - center_x) / 0.0115; temporal01 = max(0.0, min(1.0, (u * sign + 1.0) * 0.5)); length_factor = medial_length + (temporal_length - medial_length) * temporal01; lengths.append(length_factor)
        for ring_index, (center, triple) in enumerate(rings):
            t = ring_index / max(1, len(rings) - 1); ease = t * t * (3.0 - 2.0 * t)
            path_delta_local = (center - root_local) * ((length_factor - 1.0) * ease)
            fan_world = Vector((sign * fan_tip * (temporal01 - 0.15) * ease, 0.0, (curl_tip if upper else -0.55 * curl_tip) * (0.45 + 0.55 * temporal01) * ease))
            delta = path_delta_local + inverse3 @ fan_world
            for index in triple:
                before = obj.data.vertices[index].co.copy(); obj.data.vertices[index].co += delta; distance = (obj.data.vertices[index].co - before).length; max_move = max(max_move, distance); moved.add(index)
                if ring_index == 0: root_max = max(root_max, distance)
    obj.data.update(); return {"strands": len(strands), "movedVertices": len(moved), "rootMaximumMoveMm": root_max * 1000.0, "maximumMoveMm": max_move * 1000.0, "lengthFactorRange": [min(lengths), max(lengths)], "fanTipMm": fan_tip * 1000.0, "curlTipMm": curl_tip * 1000.0}


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph); mesh = evaluated.to_mesh(); vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]; polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False); evaluated.to_mesh_clear(); return tree


def collision_frames():
    scene = bpy.context.scene; results = {}; failures = []
    for frame in FRAMES:
        scene.frame_set(frame); depsgraph = bpy.context.evaluated_depsgraph_get(); depsgraph.update(); body = world_tree(bpy.data.objects[BODY], depsgraph); frame_result = {}
        for side in ("L", "R"):
            upper = world_tree(bpy.data.objects[f"Eye_{side}_UpperLashes"], depsgraph); lower = world_tree(bpy.data.objects[f"Eye_{side}_LowerLashes"], depsgraph); sclera = world_tree(bpy.data.objects[f"Eye_{side}_Sclera"], depsgraph); cornea = world_tree(bpy.data.objects[f"Eye_{side}_Cornea"], depsgraph)
            values = {"upperBody": len(upper.overlap(body)), "lowerBody": len(lower.overlap(body)), "upperSclera": len(upper.overlap(sclera)), "lowerSclera": len(lower.overlap(sclera)), "upperCornea": len(upper.overlap(cornea)), "lowerCornea": len(lower.overlap(cornea)), "upperLower": len(upper.overlap(lower))}; frame_result[side] = values
            for pair, count in values.items():
                if count: failures.append({"frame": frame, "side": side, "pair": pair, "triangleOverlapCount": count})
        results[str(frame)] = frame_result
    return results, failures


def look_at(camera, target): camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


RENDER_DIR.mkdir(parents=True, exist_ok=True); variants = []
for label, fan_tip, curl_tip, medial_length, temporal_length in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); scene = bpy.context.scene; scene.frame_set(1); bpy.context.view_layer.update(); edits = {}
    for side in ("L", "R"):
        edits[f"Eye_{side}_UpperLashes"] = reshape_lashes(bpy.data.objects[f"Eye_{side}_UpperLashes"], side, True, fan_tip, curl_tip, medial_length, temporal_length)
        edits[f"Eye_{side}_LowerLashes"] = reshape_lashes(bpy.data.objects[f"Eye_{side}_LowerLashes"], side, False, fan_tip * 0.45, curl_tip * 0.55, 0.96, 1.08)
    bpy.context.view_layer.update(); collisions, failures = collision_frames(); scene.frame_set(1); bpy.context.view_layer.update(); hidden = []
    for obj in scene.objects:
        is_hair = obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES"; is_brow_or_lash = "Brow" in obj.name or obj.name.endswith(("UpperLashes", "LowerLashes"))
        if is_hair and not is_brow_or_lash and not obj.hide_render: obj.hide_render = True; hidden.append(obj.name)
    scene.render.resolution_x = scene.render.resolution_y = 1000; camera = scene.camera; camera.data.lens = 105; rendered = []
    for view, location, target in (("front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.484)), ("three-quarter-left", (0.205, -0.425, 1.490), (0.0, -0.057, 1.482)), ("three-quarter-right", (-0.205, -0.425, 1.490), (0.0, -0.057, 1.482))):
        camera.location = location; look_at(camera, target); path = RENDER_DIR / f"{label}-{view}.png"; scene.render.filepath = str(path); bpy.ops.render.render(write_still=True); rendered.append(str(path))
    for name in hidden: bpy.data.objects[name].hide_render = False
    status = "TECHNICAL_PASS" if not failures and all(edit["rootMaximumMoveMm"] < 1e-6 for edit in edits.values()) else "TECHNICAL_FAIL"; variants.append({"label": label, "edits": edits, "collisionFrames": collisions, "collisionFailures": failures, "rendered": rendered, "status": status})
    if label == "b-human-fan" and status == "TECHNICAL_PASS":
        scene["aevrynd_mainline_revision"] = "v249r1027-human-lash-path-hierarchy"; scene["aevrynd_mainline_parent"] = SOURCE.name; scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_REQUIRED"; scene["aevrynd_website_promotion"] = "forbidden"; bpy.context.preferences.filepaths.save_version = 0; bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {"source": str(SOURCE), "output": str(OUTPUT), "method": "keep every triangular root ring fixed, shorten medial fibres, lengthen temporal fibres and add progressive temporal fan plus upper/lower curl", "variants": variants, "selectedVariant": None, "status": "VISUAL_REVIEW_REQUIRED", "websitePromotionApproved": False}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1027_LASH_PATH_HIERARCHY=" + json.dumps({"output": str(OUTPUT), "variants": [{"label": item["label"], "collisionFailures": len(item["collisionFailures"]), "status": item["status"], "upper": item["edits"]["Eye_L_UpperLashes"], "lower": item["edits"]["Eye_L_LowerLashes"]} for item in variants]}, sort_keys=True))
