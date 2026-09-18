"""Reduce the over-round palpebral aperture while preserving the r1078 inner walls."""
from collections import defaultdict
from pathlib import Path
import json

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-defined-skin-response-r1096-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-palpebral-closure-r1097-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1097-palpebral-closure-sweep.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1097-palpebral-closure"
BODY = "AevryndFemaleCC0BalancedEyeOptics_R1080"
TARGET = "AevryndFemaleCC0PalpebralClosure_R1097"
ORIGINAL_VERTEX_COUNT = 13817
FRAMES = (1, 20, 33, 61)
# label, maximum upper-lid descent, maximum lower-lid lift (metres)
VARIANTS = (
    ("a-control", 0.0, 0.0),
    ("b-subtle", 0.00070, 0.00045),
    ("c-balanced", 0.00100, 0.00065),
    ("d-strong", 0.00130, 0.00085),
)
SELECTED = "c-balanced"


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
    if not all(len(values) == 2 for values in adjacency.values()):
        raise RuntimeError("outer aperture is not a simple loop")
    start = min(adjacency); loop, previous, current = [start], None, start
    while True:
        following = adjacency[current][0] if adjacency[current][0] != previous else adjacency[current][1]
        if following == start:
            break
        loop.append(following); previous, current = current, following
    return loop


def aperture_loops(body):
    outer_edges = []
    for polygon in body.data.polygons:
        old = [index for index in polygon.vertices if index < ORIGINAL_VERTEX_COUNT]
        # Later revisions appended unrelated body details after the 180 r1078 wall vertices.
        # Restrict detection to those two 90-vertex rings so they cannot masquerade as apertures.
        new = [index for index in polygon.vertices if ORIGINAL_VERTEX_COUNT <= index < ORIGINAL_VERTEX_COUNT + 180]
        if len(polygon.vertices) == 4 and len(old) == 2 and len(new) == 2 and all(index < ORIGINAL_VERTEX_COUNT + 180 for index in polygon.vertices):
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
                        if item not in component:
                            component.add(item); frontier.append(item)
        loops.append(ordered_loop([edge for edge in outer_edges if edge[0] in component and edge[1] in component]))
    if sorted(len(loop) for loop in loops) != [45, 45]:
        raise RuntimeError(f"expected paired 45-point loops, got {[len(loop) for loop in loops]}")
    return loops


def path_split(loop, points):
    side = "L" if sum(points[index].x for index in loop) > 0 else "R"
    oriented_x = lambda index: points[index].x if side == "L" else -points[index].x
    medial = min(loop, key=oriented_x); lateral = max(loop, key=oriented_x)
    start = loop.index(medial); rotated = loop[start:] + loop[:start]; split = rotated.index(lateral)
    path_a, path_b = rotated[:split + 1], [rotated[0]] + list(reversed(rotated[split:]))
    upper, lower = sorted((path_a, path_b), key=lambda path: sum(points[index].z for index in path) / len(path), reverse=True)
    return side, medial, lateral, upper, lower


def smooth_arch(u):
    # Zero displacement at both canthi; broad centre support avoids a pinched circular arc.
    edge = min(max(u / 0.22, 0.0), 1.0, max((1.0 - u) / 0.22, 0.0))
    edge = edge * edge * (3.0 - 2.0 * edge)
    centre = 1.0 - 0.12 * abs(2.0 * u - 1.0)
    return edge * centre


def create_world_deltas(body, upper_descent, lower_lift):
    points = active_coordinates(body); deltas = {}; diagnostics = {}
    for loop in aperture_loops(body):
        side, medial, lateral, upper, lower = path_split(loop, points)
        inner, outer = abs(points[medial].x), abs(points[lateral].x)
        side_delta = {index: Vector((0.0, 0.0, 0.0)) for index in loop}
        for path, amount, direction in ((upper, upper_descent, -1.0), (lower, lower_lift, 1.0)):
            for index in path:
                u = (abs(points[index].x) - inner) / max(outer - inner, 1e-8)
                side_delta[index].z += direction * amount * smooth_arch(u)
        deltas.update(side_delta)
        before_height = max(points[index].z for index in loop) - min(points[index].z for index in loop)
        after_z = [points[index].z + side_delta[index].z for index in loop]
        diagnostics[side] = {
            "medialTip": medial, "lateralTip": lateral,
            "upperCount": len(upper), "lowerCount": len(lower),
            "apertureHeightBeforeMm": before_height * 1000.0,
            "apertureHeightAfterMm": (max(after_z) - min(after_z)) * 1000.0,
        }
    return deltas, diagnostics


def propagate_and_apply(body, world_deltas):
    adjacency = defaultdict(list)
    for edge in body.data.edges:
        a, b = edge.vertices; adjacency[a].append(b); adjacency[b].append(a)
    mapping1 = {}
    for old in world_deltas:
        candidates = [index for index in adjacency[old] if index >= ORIGINAL_VERTEX_COUNT]
        if len(candidates) != 1:
            raise RuntimeError(f"outer vertex {old} has {len(candidates)} first-ring neighbours")
        mapping1[old] = candidates[0]
    first_ring = set(mapping1.values()); mapping2 = {}
    for old, first in mapping1.items():
        candidates = [index for index in adjacency[first] if index >= ORIGINAL_VERTEX_COUNT and index not in first_ring]
        if len(candidates) != 1:
            raise RuntimeError(f"first-ring vertex {first} has {len(candidates)} second-ring neighbours")
        mapping2[old] = candidates[0]
    # Carry the contour into two exterior skin rings. This prevents the aperture
    # edge from becoming a thin, stretched line and gives the lids visible mass.
    aperture = set(world_deltas)
    wall = set(mapping1.values()) | set(mapping2.values())
    outer1 = {neighbor for old in aperture for neighbor in adjacency[old] if neighbor < ORIGINAL_VERTEX_COUNT and neighbor not in aperture}
    outer2 = {neighbor for first in outer1 for neighbor in adjacency[first] if neighbor < ORIGINAL_VERTEX_COUNT and neighbor not in aperture and neighbor not in outer1}
    expanded = dict(world_deltas)
    for ring, weight in ((outer1, 0.60), (outer2, 0.22)):
        for index in ring:
            sources = [old for old in aperture if index in adjacency[old]]
            if not sources and ring is outer2:
                first_sources = [first for first in outer1 if index in adjacency[first]]
                sources = [old for first in first_sources for old in aperture if first in adjacency[old]]
            if sources:
                expanded[index] = sum((world_deltas[old] for old in sources), Vector()) / len(sources) * weight
    inverse3 = body.matrix_world.inverted().to_3x3()
    local = {index: inverse3 @ delta for index, delta in expanded.items()}
    for block in body.data.shape_keys.key_blocks:
        for index, delta in local.items():
            block.data[index].co += delta
        for old in aperture:
            for index in (mapping1[old], mapping2[old]):
                block.data[index].co += local[old]
    body.data.update()
    moved = [delta.length for delta in world_deltas.values()]
    return {
        "editedOuterVertices": sum(value > 1e-10 for value in moved),
        "editedVerticesIncludingWalls": 3 * sum(value > 1e-10 for value in moved),
        "maximumOuterDisplacementMm": max(moved) * 1000.0,
        "exteriorSkinRing1Vertices": len(outer1),
        "exteriorSkinRing2Vertices": len(outer2),
        "shapeKeyCount": len(body.data.shape_keys.key_blocks),
    }


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph); mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles(); triangles = [tuple(triangle.vertices) for triangle in mesh.loop_triangles]
    evaluated.to_mesh_clear(); return BVHTree.FromPolygons(vertices, triangles, all_triangles=True)


def collision_frames(body):
    results, failures = {}, []
    for frame in FRAMES:
        bpy.context.scene.frame_set(frame); depsgraph = bpy.context.evaluated_depsgraph_get(); depsgraph.update()
        body_tree = world_tree(body, depsgraph); result = {}
        for side in ("L", "R"):
            result[side] = {}
            for layer in ("Sclera", "Cornea", "Iris", "UpperLashes", "LowerLashes"):
                count = len(body_tree.overlap(world_tree(bpy.data.objects[f"Eye_{side}_{layer}"], depsgraph)))
                result[side][layer] = count
                if count:
                    failures.append({"frame": frame, "side": side, "layer": layer, "triangleOverlapCount": count})
        results[str(frame)] = result
    return results, failures


def render(scene, label, view):
    camera = scene.camera
    if view == "eye-front":
        camera.location, target, camera.data.lens, size = (0.0, -0.405, 1.449), (0.0, -0.105, 1.449), 135, (1400, 760)
    elif view == "eye-oblique":
        camera.location, target, camera.data.lens, size = (0.235, -0.405, 1.451), (0.0, -0.105, 1.449), 135, (1400, 760)
    else:
        camera.location, target, camera.data.lens, size = (0.0, -0.72, 1.445), (0.0, -0.025, 1.445), 88, (1000, 1000)
    look_at(camera, target); scene.render.resolution_x, scene.render.resolution_y = size; scene.render.resolution_percentage = 100
    path = OUT / f"{label}-{view}.png"; scene.render.filepath = str(path); bpy.ops.render.render(write_still=True); return str(path)


OUT.mkdir(parents=True, exist_ok=True); variants = []
for label, upper_descent, lower_lift in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); scene = bpy.context.scene; scene.frame_set(1); body = bpy.data.objects[BODY]
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")):
                obj.hide_render = True
    deltas, diagnostics = create_world_deltas(body, upper_descent, lower_lift)
    patch = propagate_and_apply(body, deltas) if upper_descent or lower_lift else {"editedOuterVertices": 0, "editedVerticesIncludingWalls": 0, "maximumOuterDisplacementMm": 0.0, "shapeKeyCount": len(body.data.shape_keys.key_blocks)}
    bpy.context.view_layer.update(); collisions, failures = collision_frames(body); scene.frame_set(1); bpy.context.view_layer.update()
    renders = [render(scene, label, view) for view in ("eye-front", "eye-oblique", "face-front")]
    variants.append({"label": label, "upperDescentMm": upper_descent * 1000.0, "lowerLiftMm": lower_lift * 1000.0, "diagnostics": diagnostics, "patch": patch, "collisionFrames": collisions, "collisionFailures": failures, "renders": renders, "status": "TECHNICAL_PASS" if not failures else "TECHNICAL_FAIL"})
    if label == SELECTED:
        body.name = TARGET; body["aevrynd_revision"] = "v249r1097-palpebral-closure"; body["aevrynd_source"] = SOURCE.name
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"; scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0; bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {"revision": "v249r1097-palpebral-closure-sweep", "source": str(SOURCE), "output": str(OUTPUT), "method": "reduce the over-round eye aperture with a broad smooth upper/lower lid closure while propagating identical deltas through both eyelid inner-wall rings and every shape key", "variants": variants, "selectedVariant": SELECTED, "websitePromotionApproved": False, "candidateStatus": "VISUAL_REVIEW_PENDING"}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1097_PALPEBRAL=" + json.dumps({"selected": SELECTED, "variants": [{"label": item["label"], "diagnostics": item["diagnostics"], "failures": len(item["collisionFailures"]), "status": item["status"]} for item in variants]}, sort_keys=True))
