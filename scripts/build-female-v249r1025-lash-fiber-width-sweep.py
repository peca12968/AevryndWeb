"""Increase existing triangular lash-fibre width with root-safe tapering."""

import itertools
import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-upper-lid-orbital-volume-r1024-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-visible-lash-fibers-r1025-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1025-lash-fiber-width-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1025-lash-fiber-width-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
FRAMES = (1, 20, 33, 61)
VARIANTS = (
    ("a-visible", 2.00, 1.60),
    ("b-human-diameter", 2.80, 2.20),
    ("c-bold", 3.60, 2.80),
)


def components(obj):
    adjacency = {vertex.index: set() for vertex in obj.data.vertices}
    edges = set()
    for edge in obj.data.edges:
        first, second = edge.vertices; adjacency[first].add(second); adjacency[second].add(first); edges.add(tuple(sorted((first, second))))
    remaining = set(adjacency); result = []
    while remaining:
        seed = remaining.pop(); stack = [seed]; component = {seed}
        while stack:
            current = stack.pop(); fresh = adjacency[current] & remaining; remaining.difference_update(fresh); component.update(fresh); stack.extend(fresh)
        result.append(component)
    return result, edges


def widen_fibres(obj, tip_factor):
    strands, edges = components(obj); ring_count = 0; moved = set(); maximum = 0.0
    for strand in strands:
        rings = []
        for triple in itertools.combinations(strand, 3):
            if all(tuple(sorted(pair)) in edges for pair in itertools.combinations(triple, 2)):
                center = sum((obj.data.vertices[index].co for index in triple), Vector()) / 3.0
                rings.append((center, triple))
        # The authored fibres are seven triangular rings. Max local Y is the
        # skin-side root; width ramps toward the free tip to preserve clearance.
        rings.sort(key=lambda item: item[0].y, reverse=True)
        ring_count += len(rings)
        for position, (center, triple) in enumerate(rings):
            t = position / max(1, len(rings) - 1); factor = 1.0 + (tip_factor - 1.0) * (t ** 0.75)
            for index in triple:
                vertex = obj.data.vertices[index]; before = vertex.co.copy(); vertex.co = center + (vertex.co - center) * factor
                maximum = max(maximum, (vertex.co - before).length); moved.add(index)
    obj.data.update()
    return {"strandComponents": len(strands), "triangularRings": ring_count, "movedVertices": len(moved), "tipWidthFactor": tip_factor, "maximumVertexMoveMm": maximum * 1000.0}


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph); mesh = evaluated.to_mesh(); vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]; polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False); evaluated.to_mesh_clear(); return tree


def collision_frames():
    scene = bpy.context.scene; results = {}; failures = []
    for frame in FRAMES:
        scene.frame_set(frame); depsgraph = bpy.context.evaluated_depsgraph_get(); depsgraph.update(); body = world_tree(bpy.data.objects[BODY], depsgraph); frame_result = {}
        for side in ("L", "R"):
            upper = world_tree(bpy.data.objects[f"Eye_{side}_UpperLashes"], depsgraph); lower = world_tree(bpy.data.objects[f"Eye_{side}_LowerLashes"], depsgraph)
            sclera = world_tree(bpy.data.objects[f"Eye_{side}_Sclera"], depsgraph); cornea = world_tree(bpy.data.objects[f"Eye_{side}_Cornea"], depsgraph)
            values = {"upperBody": len(upper.overlap(body)), "lowerBody": len(lower.overlap(body)), "upperSclera": len(upper.overlap(sclera)), "lowerSclera": len(lower.overlap(sclera)), "upperCornea": len(upper.overlap(cornea)), "lowerCornea": len(lower.overlap(cornea)), "upperLower": len(upper.overlap(lower))}
            frame_result[side] = values
            for pair, count in values.items():
                if count: failures.append({"frame": frame, "side": side, "pair": pair, "triangleOverlapCount": count})
        results[str(frame)] = frame_result
    return results, failures


def look_at(camera, target): camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


RENDER_DIR.mkdir(parents=True, exist_ok=True); variants = []
for label, upper_factor, lower_factor in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); scene = bpy.context.scene; scene.frame_set(1); bpy.context.view_layer.update(); edits = {}
    for side in ("L", "R"):
        edits[f"Eye_{side}_UpperLashes"] = widen_fibres(bpy.data.objects[f"Eye_{side}_UpperLashes"], upper_factor)
        edits[f"Eye_{side}_LowerLashes"] = widen_fibres(bpy.data.objects[f"Eye_{side}_LowerLashes"], lower_factor)
    bpy.context.view_layer.update(); collisions, failures = collision_frames(); scene.frame_set(1); bpy.context.view_layer.update(); hidden = []
    for obj in scene.objects:
        is_hair = obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES"; is_brow_or_lash = "Brow" in obj.name or obj.name.endswith(("UpperLashes", "LowerLashes"))
        if is_hair and not is_brow_or_lash and not obj.hide_render: obj.hide_render = True; hidden.append(obj.name)
    scene.render.resolution_x = scene.render.resolution_y = 1000; camera = scene.camera; camera.data.lens = 105; rendered = []
    for view, location, target in (("front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.484)), ("three-quarter-left", (0.205, -0.425, 1.490), (0.0, -0.057, 1.482)), ("three-quarter-right", (-0.205, -0.425, 1.490), (0.0, -0.057, 1.482))):
        camera.location = location; look_at(camera, target); path = RENDER_DIR / f"{label}-{view}.png"; scene.render.filepath = str(path); bpy.ops.render.render(write_still=True); rendered.append(str(path))
    for name in hidden: bpy.data.objects[name].hide_render = False
    status = "TECHNICAL_PASS" if not failures else "TECHNICAL_FAIL"; variants.append({"label": label, "upperTipWidthFactor": upper_factor, "lowerTipWidthFactor": lower_factor, "edits": edits, "collisionFrames": collisions, "collisionFailures": failures, "rendered": rendered, "status": status})
    if label == "b-human-diameter" and status == "TECHNICAL_PASS":
        scene["aevrynd_mainline_revision"] = "v249r1025-human-diameter-lash-fibres"; scene["aevrynd_mainline_parent"] = SOURCE.name; scene["aevrynd_release_state"] = "LOCAL_TECHNICAL_PASS_VISUAL_HERO_FAIL"; scene["aevrynd_website_promotion"] = "forbidden"; bpy.context.preferences.filepaths.save_version = 0; bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {"source": str(SOURCE), "output": str(OUTPUT), "method": "detect each seven-ring triangular lash fibre and widen cross-sections progressively from unchanged root to free tip", "variants": variants, "selectedVariant": None, "status": "VISUAL_REVIEW_REQUIRED", "websitePromotionApproved": False}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1025_LASH_WIDTH=" + json.dumps({"output": str(OUTPUT), "variants": [{"label": item["label"], "collisionFailures": len(item["collisionFailures"]), "status": item["status"], "upper": item["edits"]["Eye_L_UpperLashes"], "lower": item["edits"]["Eye_L_LowerLashes"]} for item in variants]}, sort_keys=True))
