"""Fair the medial/lateral canthus contour while preserving r1078 lid walls."""
import json
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-eyelid-inner-wall-r1078-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-canthus-contour-r1079-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1079-canthus-contour-sweep.study.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1079-canthus-contour"
BODY = "AevryndFemaleCC0EyelidInnerWall_R1078"
TARGET = "AevryndFemaleCC0CanthusContour_R1079"
ORIGINAL_VERTEX_COUNT = 13817
RING_SIZE = 90
FRAMES = (1, 20, 33, 61)
# label, fairing strength, maximum horizontal closure in metres
VARIANTS = (
    ("a-control", 0.00, 0.00000),
    ("b-conservative-0.35", 0.35, 0.00012),
    ("c-balanced-0.55", 0.55, 0.00018),
    ("d-strong-0.75", 0.75, 0.00025),
)
SELECTED = "c-balanced-0.55"


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
        if following == start: break
        loop.append(following); previous, current = current, following
    return loop


def aperture_loops(body):
    outer_edges = []
    for polygon in body.data.polygons:
        old = [index for index in polygon.vertices if index < ORIGINAL_VERTEX_COUNT]
        new = [index for index in polygon.vertices if index >= ORIGINAL_VERTEX_COUNT]
        if len(old) == 2 and len(new) == 2:
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


def smoothstep(value):
    value = max(0.0, min(1.0, value)); return value * value * (3.0 - 2.0 * value)


def create_world_deltas(body, fairing, closure):
    points = active_coordinates(body); deltas = {}
    diagnostics = {}
    for loop in aperture_loops(body):
        side, medial, lateral, upper, lower = path_split(loop, points)
        sign = 1.0 if side == "L" else -1.0
        inner, outer = abs(points[medial].x), abs(points[lateral].x)
        side_delta = {index: Vector((0.0, 0.0, 0.0)) for index in loop}
        # Horizontal closure is confined to the first/last 14% of the aperture.
        for index in loop:
            u = (abs(points[index].x) - inner) / (outer - inner)
            if u < 0.14:
                side_delta[index].x += sign * closure * smoothstep((0.14 - u) / 0.14)
            elif u > 0.86:
                side_delta[index].x -= sign * closure * smoothstep((u - 0.86) / 0.14)
        # Fair the long folded lower-lid runs at each corner. Upper contour remains intact.
        u_values = [(abs(points[index].x) - inner) / (outer - inner) for index in lower]
        medial_end = next(i for i, value in enumerate(u_values) if i >= 8 and value >= 0.10)
        lateral_start = next(i for i, value in enumerate(u_values) if value >= 0.86)
        sections = (lower[:medial_end + 1], lower[lateral_start:])
        raw_max = 0.0
        for section in sections:
            first_z, last_z = points[section[0]].z, points[section[-1]].z
            for position, index in enumerate(section):
                t = position / max(1, len(section) - 1)
                target_z = first_z + (last_z - first_z) * t
                correction = (target_z - points[index].z) * fairing
                side_delta[index].z += correction
                raw_max = max(raw_max, abs(target_z - points[index].z))
        deltas.update(side_delta)
        diagnostics[side] = {
            "medialTip": medial, "lateralTip": lateral, "upperCount": len(upper), "lowerCount": len(lower),
            "medialFairingVertices": len(sections[0]), "lateralFairingVertices": len(sections[1]),
            "rawMaximumLowerContourCorrectionMm": raw_max * 1000.0,
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
    if len(set(mapping1.values())) != 90 or len(set(mapping2.values())) != 90:
        raise RuntimeError("wall-ring mapping is not one-to-one")
    inverse3 = body.matrix_world.inverted().to_3x3()
    local = {index: inverse3 @ delta for index, delta in world_deltas.items()}
    for block in body.data.shape_keys.key_blocks:
        for old, delta in local.items():
            for index in (old, mapping1[old], mapping2[old]):
                block.data[index].co += delta
    body.data.update()
    moved = [delta.length for delta in world_deltas.values()]
    return {
        "editedOuterVertices": sum(value > 1e-10 for value in moved),
        "editedVerticesIncludingWalls": 3 * sum(value > 1e-10 for value in moved),
        "maximumOuterDisplacementMm": max(moved) * 1000.0,
        "ring1UniqueMappings": len(set(mapping1.values())), "ring2UniqueMappings": len(set(mapping2.values())),
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
                if count: failures.append({"frame": frame, "side": side, "layer": layer, "triangleOverlapCount": count})
        results[str(frame)] = result
    return results, failures


def render(scene, label, view):
    camera = scene.camera
    if view == "eye-front": camera.location, target, camera.data.lens, size = (0.0, -0.405, 1.449), (0.0, -0.105, 1.449), 135, (1400, 760)
    elif view == "eye-oblique": camera.location, target, camera.data.lens, size = (0.235, -0.405, 1.451), (0.0, -0.105, 1.449), 135, (1400, 760)
    elif view == "face-front": camera.location, target, camera.data.lens, size = (0.0, -0.72, 1.445), (0.0, -0.025, 1.440), 88, (1000, 1000)
    else: camera.location, target, camera.data.lens, size = (0.45, -0.62, 1.460), (0.0, -0.015, 1.440), 88, (1000, 1000)
    look_at(camera, target); scene.render.resolution_x, scene.render.resolution_y = size; scene.render.resolution_percentage = 100
    path = OUT / f"{label}-{view}.png"; scene.render.filepath = str(path); bpy.ops.render.render(write_still=True); return str(path)


OUT.mkdir(parents=True, exist_ok=True); variants = []
for label, fairing, closure in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); scene = bpy.context.scene; scene.frame_set(1); body = bpy.data.objects[BODY]
    scene.view_settings.view_transform = "Standard"; scene.view_settings.look = "None"; scene.view_settings.exposure = 0.0; scene.view_settings.gamma = 1.0
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")): obj.hide_render = True
    deltas, diagnostics = create_world_deltas(body, fairing, closure)
    patch = propagate_and_apply(body, deltas) if fairing or closure else {"editedOuterVertices": 0, "editedVerticesIncludingWalls": 0, "maximumOuterDisplacementMm": 0.0, "ring1UniqueMappings": 90, "ring2UniqueMappings": 90}
    bpy.context.view_layer.update(); collisions, failures = collision_frames(body); scene.frame_set(1); bpy.context.view_layer.update()
    renders = [render(scene, label, view) for view in ("eye-front", "eye-oblique", "face-front", "face-three-quarter")]
    variants.append({"label": label, "fairingStrength": fairing, "maximumHorizontalClosureMm": closure*1000.0, "diagnostics": diagnostics, "patch": patch, "collisionFrames": collisions, "collisionFailures": failures, "renders": renders, "status": "TECHNICAL_PASS" if not failures else "TECHNICAL_FAIL"})
    if label == SELECTED:
        body.name = TARGET; body["aevrynd_revision"] = "v249r1079-canthus-contour"; body["aevrynd_source"] = SOURCE.name
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"; scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0; bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {"revision": "v249r1079-canthus-contour-sweep", "source": str(SOURCE), "output": str(OUTPUT), "method": "preserve r1078 wall topology, fair only folded lower-corner contours and apply sub-quarter-millimetre bilateral horizontal closure", "variants": variants, "selectedVariant": SELECTED, "websitePromotionApproved": False, "candidateStatus": "VISUAL_REVIEW_PENDING"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1079_CANTHUS=" + json.dumps({"selected": SELECTED, "variants": [{"label": item["label"], "patch": item["patch"], "failures": len(item["collisionFailures"]), "status": item["status"]} for item in variants]}, sort_keys=True))
