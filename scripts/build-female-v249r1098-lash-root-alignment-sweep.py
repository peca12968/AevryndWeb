"""Align upper-lash root rings to the authored upper eyelid margin."""
from collections import defaultdict
from pathlib import Path
import itertools
import json

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-palpebral-closure-r1097-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-lash-root-alignment-r1098-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1098-lash-root-alignment-sweep.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1098-lash-root-alignment"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
ORIGINAL_VERTEX_COUNT = 13817
FRAMES = (1, 20, 33, 61)
# label, height above aperture, outward clearance (metres)
VARIANTS = (("a-clearance-0.45", 0.00010, 0.00045), ("b-clearance-0.65", 0.00010, 0.00065), ("c-clearance-0.85", 0.00018, 0.00085))
SELECTED = "b-clearance-0.65"


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def active_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    coordinates = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or block.name in ("Aevrynd_MouthOpenTest_R1030", "Aevrynd_SmileTest_R1030") or abs(block.value) < 1e-8:
            continue
        for index, item in enumerate(block.data):
            coordinates[index] += block.value * (item.co - block.relative_key.data[index].co)
    return [body.matrix_world @ coordinate for coordinate in coordinates]


def ordered_loop(edges):
    adjacency = defaultdict(list)
    for a, b in edges:
        adjacency[a].append(b); adjacency[b].append(a)
    start = min(adjacency); loop, previous, current = [start], None, start
    while True:
        following = adjacency[current][0] if adjacency[current][0] != previous else adjacency[current][1]
        if following == start: break
        loop.append(following); previous, current = current, following
    return loop


def upper_lid_paths(body):
    points = active_coordinates(body); outer_edges = []
    for polygon in body.data.polygons:
        old = [index for index in polygon.vertices if index < ORIGINAL_VERTEX_COUNT]
        wall = [index for index in polygon.vertices if ORIGINAL_VERTEX_COUNT <= index < ORIGINAL_VERTEX_COUNT + 180]
        if len(polygon.vertices) == 4 and len(old) == 2 and len(wall) == 2:
            outer_edges.append(tuple(old))
    unused = set(tuple(sorted(edge)) for edge in outer_edges); loops = []
    while unused:
        seed = next(iter(unused)); component, frontier = set(seed), list(seed)
        while frontier:
            vertex = frontier.pop()
            for edge in list(unused):
                if vertex in edge:
                    unused.remove(edge)
                    for item in edge:
                        if item not in component: component.add(item); frontier.append(item)
        loops.append(ordered_loop([edge for edge in outer_edges if edge[0] in component and edge[1] in component]))
    result = {}
    for loop in loops:
        side = "L" if sum(points[index].x for index in loop) > 0 else "R"
        oriented = lambda index: points[index].x if side == "L" else -points[index].x
        medial, lateral = min(loop, key=oriented), max(loop, key=oriented)
        start = loop.index(medial); rotated = loop[start:] + loop[:start]; split = rotated.index(lateral)
        paths = (rotated[:split + 1], [rotated[0]] + list(reversed(rotated[split:])))
        upper = max(paths, key=lambda path: sum(points[index].z for index in path) / len(path))
        result[side] = sorted((points[index].copy() for index in upper), key=lambda point: point.x)
    if set(result) != {"L", "R"}: raise RuntimeError("paired upper lid paths were not found")
    return result


def sample_by_x(points, x):
    if x <= points[0].x: return points[0].copy()
    if x >= points[-1].x: return points[-1].copy()
    for first, second in zip(points, points[1:]):
        if first.x <= x <= second.x:
            t = (x - first.x) / max(second.x - first.x, 1e-9)
            return first.lerp(second, t)
    return min(points, key=lambda point: abs(point.x - x)).copy()


def strand_components(obj):
    adjacency = {vertex.index: set() for vertex in obj.data.vertices}
    for edge in obj.data.edges:
        a, b = edge.vertices; adjacency[a].add(b); adjacency[b].add(a)
    remaining = set(adjacency); components = []
    while remaining:
        seed = remaining.pop(); stack = [seed]; component = {seed}
        while stack:
            current = stack.pop(); fresh = adjacency[current] & remaining
            remaining.difference_update(fresh); component.update(fresh); stack.extend(fresh)
        components.append(component)
    return components


def root_centroid(obj, component):
    edges = {tuple(sorted(edge.vertices)) for edge in obj.data.edges if edge.vertices[0] in component}
    triangles = []
    for triple in itertools.combinations(component, 3):
        if all(tuple(sorted(pair)) in edges for pair in itertools.combinations(triple, 2)):
            centre = sum((obj.matrix_world @ obj.data.vertices[index].co for index in triple), Vector()) / 3.0
            triangles.append((centre, triple))
    if not triangles: raise RuntimeError(f"no triangular fibre rings in {obj.name}")
    return max(triangles, key=lambda item: item[0].y)


def align_upper_lashes(obj, lid_path, height, clearance):
    inverse3 = obj.matrix_world.inverted().to_3x3(); moved = []; root_before = []; root_after = []
    for component in strand_components(obj):
        root, _triple = root_centroid(obj, component); target = sample_by_x(lid_path, root.x)
        target.z += height; target.y -= clearance
        delta_world = target - root; delta_local = inverse3 @ delta_world
        for index in component: obj.data.vertices[index].co += delta_local
        moved.append(delta_world.length); root_before.append(root.z); root_after.append(target.z)
    obj.data.update()
    return {"strands": len(moved), "maximumRootMoveMm": max(moved) * 1000.0, "meanRootMoveMm": sum(moved) / len(moved) * 1000.0, "meanRootZBefore": sum(root_before) / len(root_before), "meanRootZAfter": sum(root_after) / len(root_after), "heightAboveMarginMm": height * 1000.0, "outwardClearanceMm": clearance * 1000.0}


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph); mesh = evaluated.to_mesh(); vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles(); triangles = [tuple(item.vertices) for item in mesh.loop_triangles]; evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, triangles, all_triangles=True)


def collision_frames(body):
    results, failures = {}, []
    for frame in FRAMES:
        bpy.context.scene.frame_set(frame); deps = bpy.context.evaluated_depsgraph_get(); deps.update(); body_tree = world_tree(body, deps); result = {}
        for side in ("L", "R"):
            upper = world_tree(bpy.data.objects[f"Eye_{side}_UpperLashes"], deps); sclera = world_tree(bpy.data.objects[f"Eye_{side}_Sclera"], deps); cornea = world_tree(bpy.data.objects[f"Eye_{side}_Cornea"], deps)
            values = {"upperBody": len(upper.overlap(body_tree)), "upperSclera": len(upper.overlap(sclera)), "upperCornea": len(upper.overlap(cornea))}; result[side] = values
            for pair, count in values.items():
                if count: failures.append({"frame": frame, "side": side, "pair": pair, "triangleOverlapCount": count})
        results[str(frame)] = result
    return results, failures


def render(scene, label, view):
    camera = scene.camera
    if view == "eye-front": camera.location, target, camera.data.lens, size = (0.0, -0.405, 1.449), (0.0, -0.105, 1.449), 135, (1400, 760)
    elif view == "eye-oblique": camera.location, target, camera.data.lens, size = (0.235, -0.405, 1.451), (0.0, -0.105, 1.449), 135, (1400, 760)
    else: camera.location, target, camera.data.lens, size = (0.0, -0.72, 1.445), (0.0, -0.025, 1.445), 88, (1000, 1000)
    look_at(camera, target); scene.render.resolution_x, scene.render.resolution_y = size; scene.render.resolution_percentage = 100
    path = OUT / f"{label}-{view}.png"; scene.render.filepath = str(path); bpy.ops.render.render(write_still=True); return str(path)


OUT.mkdir(parents=True, exist_ok=True); variants = []
for label, height, clearance in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); scene = bpy.context.scene; scene.frame_set(1); body = bpy.data.objects[BODY]; paths = upper_lid_paths(body); edits = {}
    for side in ("L", "R"): edits[side] = align_upper_lashes(bpy.data.objects[f"Eye_{side}_UpperLashes"], paths[side], height, clearance)
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")): obj.hide_render = True
    bpy.context.view_layer.update(); collisions, failures = collision_frames(body); scene.frame_set(1); bpy.context.view_layer.update(); renders = [render(scene, label, view) for view in ("eye-front", "eye-oblique", "face-front")]
    status = "TECHNICAL_PASS" if not failures else "TECHNICAL_FAIL"; variants.append({"label": label, "edits": edits, "collisionFrames": collisions, "collisionFailures": failures, "renders": renders, "status": status})
    if label == SELECTED and status == "TECHNICAL_PASS":
        body["aevrynd_revision"] = "v249r1098-lash-root-alignment"; body["aevrynd_source"] = SOURCE.name
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"; scene["aevrynd_website_promotion"] = "forbidden"; bpy.context.preferences.filepaths.save_version = 0; bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {"revision": "v249r1098-lash-root-alignment-sweep", "source": str(SOURCE), "output": str(OUTPUT), "method": "move each complete upper-lash fibre rigidly so its triangular root ring follows the current upper eyelid margin; preserve authored fibre length, fan and curl", "variants": variants, "selectedVariant": SELECTED, "websitePromotionApproved": False, "candidateStatus": "VISUAL_REVIEW_PENDING"}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1098_LASH_ROOTS=" + json.dumps({"selected": SELECTED, "variants": [{"label": item["label"], "edits": item["edits"], "failures": len(item["collisionFailures"]), "status": item["status"]} for item in variants]}, sort_keys=True))
