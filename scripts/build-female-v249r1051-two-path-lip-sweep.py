"""Replace the r1033 vermilion field with a welded two-path upper/lower patch."""

import json
import math
from collections import defaultdict
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-lower-lip-rim-turn-r1033-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1051-two-path-lip-sweep.study.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1051-two-path-lip-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
CENTER_Z = 1.3862
RADIUS_X = 0.034
RADIUS_Z = 0.005
Y_MAX = -0.105
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
VARIANTS = (
    ("a-restrained", -0.1465, -0.1445),
    ("b-balanced", -0.1490, -0.1460),
    ("c-projected", -0.1515, -0.1475),
)


def connected(items, neighbours):
    remaining = set(items)
    groups = []
    while remaining:
        seed = remaining.pop()
        group = {seed}
        stack = [seed]
        while stack:
            fresh = neighbours(stack.pop()) & remaining
            remaining.difference_update(fresh)
            group.update(fresh)
            stack.extend(fresh)
        groups.append(group)
    return sorted(groups, key=len, reverse=True)


def mixed_local(body, source):
    blocks = body.data.shape_keys.key_blocks
    coords = [point.copy() for point in source[blocks[0].name]]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        relative = source[block.relative_key.name]
        for index in range(len(coords)):
            coords[index] += block.value * (source[block.name][index] - relative[index])
    return coords


def topology(body, points):
    mesh = body.data
    edge_faces = defaultdict(set)
    face_edges = defaultdict(set)
    for polygon in mesh.polygons:
        ids = list(polygon.vertices)
        for offset, first in enumerate(ids):
            edge = tuple(sorted((first, ids[(offset + 1) % len(ids)])))
            edge_faces[edge].add(polygon.index)
            face_edges[polygon.index].add(edge)
    face_groups = connected(range(len(mesh.polygons)), lambda face: set().union(*(edge_faces[e] for e in face_edges[face])))
    main = face_groups[0]
    selected = set()
    for face in main:
        polygon = mesh.polygons[face]
        center = sum((points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
        ellipse = (center.x / RADIUS_X) ** 2 + ((center.z - CENTER_Z) / RADIUS_Z) ** 2
        if center.y < Y_MAX and ellipse < 1.0:
            selected.add(face)
    boundary = {
        edge for face in selected for edge in face_edges[face]
        if len(edge_faces[edge] & selected) == 1 and bool(edge_faces[edge] - selected)
    }
    vertex_edges = defaultdict(set)
    for edge in boundary:
        for vertex in edge:
            vertex_edges[vertex].add(edge)
    loops = connected(boundary, lambda edge: set().union(*(vertex_edges[v] for v in edge)))
    outer_edges = loops[0]
    adjacency = defaultdict(set)
    for first, second in outer_edges:
        adjacency[first].add(second)
        adjacency[second].add(first)
    start = min(adjacency, key=lambda index: points[index].x)
    first = max(adjacency[start], key=lambda index: points[index].z)
    order = [start]
    previous, current = start, first
    while current != start:
        order.append(current)
        following = adjacency[current] - {previous}
        previous, current = current, next(iter(following))
        if len(order) > len(adjacency):
            raise RuntimeError("outer loop traversal failed")
    if len(order) != len(adjacency):
        raise RuntimeError("outer loop is not simple")
    return selected, loops, order


def path_parameters(order, points):
    left_pos = min(range(len(order)), key=lambda i: points[order[i]].x)
    right_pos = max(range(len(order)), key=lambda i: points[order[i]].x)

    def walk(start, end, step):
        result = [start]
        current = start
        while current != end:
            current = (current + step) % len(order)
            result.append(current)
        return result

    first = walk(left_pos, right_pos, 1)
    second = walk(left_pos, right_pos, -1)
    first_mean = sum(points[order[i]].z for i in first) / len(first)
    second_mean = sum(points[order[i]].z for i in second) / len(second)
    upper, lower = (first, second) if first_mean > second_mean else (second, first)
    parameters = {}
    for label, path in (("upper", upper), ("lower", lower)):
        lengths = [0.0]
        for offset in range(1, len(path)):
            a = points[order[path[offset - 1]]]
            b = points[order[path[offset]]]
            lengths.append(lengths[-1] + (b - a).length)
        total = lengths[-1] or 1.0
        for position, length in zip(path, lengths):
            parameters[position] = (label, -1.0 + 2.0 * length / total)
    return parameters


def smooth_loop(points, iterations=12):
    result = [point.copy() for point in points]
    for _ in range(iterations):
        result = [
            result[index] * 0.50
            + result[(index - 1) % len(result)] * 0.25
            + result[(index + 1) % len(result)] * 0.25
            for index in range(len(result))
        ]
    return result


def profile(label, u, crest_y, inner_y):
    envelope = max(0.0, 1.0 - u * u)
    x_crest = 0.0325 * u
    x_inner = 0.0308 * u
    if label == "upper":
        paired = math.exp(-0.5 * ((abs(u) - 0.33) / 0.16) ** 2)
        notch = math.exp(-0.5 * (u / 0.12) ** 2)
        crest_z = CENTER_Z + 0.0040 * envelope + 0.00055 * paired - 0.00030 * notch
        inner_z = CENTER_Z + 0.00070 * envelope + 0.00042 * paired - 0.00020 * notch
    else:
        tubercle = math.exp(-0.5 * (u / 0.30) ** 2)
        crest_z = CENTER_Z - 0.0041 * envelope - 0.00035 * tubercle
        inner_z = CENTER_Z - 0.00085 * envelope - 0.00042 * tubercle
    return Vector((x_crest, crest_y, crest_z)), Vector((x_inner, inner_y, inner_z))


def build_patch(body, crest_y, inner_y):
    mesh = body.data
    blocks = list(mesh.shape_keys.key_blocks)
    source = {block.name: [item.co.copy() for item in block.data] for block in blocks}
    local_mixed = mixed_local(body, source)
    points = [body.matrix_world @ point for point in local_mixed]
    selected, loops, order = topology(body, points)
    if [len(loop) for loop in loops] != [76, 60]:
        raise RuntimeError(f"unexpected boundary loops: {[len(loop) for loop in loops]}")
    parameters = path_parameters(order, points)
    outer_world = [points[index] for index in order]
    smoothed = smooth_loop(outer_world)
    weights = {
        index: {membership.group: membership.weight for membership in mesh.vertices[index].groups}
        for index in order
    }
    lip_group = body.vertex_groups.get("lips")
    lip_group_index = lip_group.index if lip_group else None
    inverse = body.matrix_world.inverted()

    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    body.active_shape_key_index = 0
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    deform = bm.verts.layers.deform.verify()
    bmesh.ops.delete(bm, geom=[bm.faces[index] for index in sorted(selected)], context="FACES_ONLY")
    bm.verts.ensure_lookup_table()
    rows = [[bm.verts[index] for index in order]]
    descriptors = []
    added_faces = []
    for ring_name in ("transition", "crest", "inner"):
        row = []
        for position, boundary_index in enumerate(order):
            path_label, u = parameters[position]
            crest, inner = profile(path_label, u, crest_y, inner_y)
            if ring_name == "transition":
                target = smoothed[position].lerp(crest, 0.42)
                lip_weight = 0.72
            elif ring_name == "crest":
                target = crest
                lip_weight = 1.0
            else:
                target = inner
                lip_weight = 1.0
            vertex = bm.verts.new(inverse @ target)
            for group, weight in weights[boundary_index].items():
                vertex[deform][group] = weight
            if lip_group_index is not None:
                vertex[deform][lip_group_index] = max(vertex[deform].get(lip_group_index, 0.0), lip_weight)
            row.append(vertex)
            descriptors.append((vertex, target.copy(), boundary_index, ring_name, path_label))
        previous = rows[-1]
        for index in range(len(order)):
            face = bm.faces.new((previous[index], previous[(index + 1) % len(order)], row[(index + 1) % len(order)], row[index]))
            face.material_index = 0
            added_faces.append(face)
        rows.append(row)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.verts.index_update()
    new_indices = [vertex.index for vertex, *_ in descriptors]
    bmesh.update_edit_mesh(mesh, loop_triangles=True, destructive=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    mesh.update()

    for (_vertex, target_world, boundary_index, ring_name, path_label), new_index in zip(descriptors, new_indices):
        deformations = {}
        for block in blocks[1:]:
            relative = source[block.relative_key.name][boundary_index]
            delta = source[block.name][boundary_index] - relative
            scale = 1.0
            if block.name == OPEN_KEY and path_label == "lower":
                scale = 1.18 if ring_name == "inner" else 1.08
            elif block.name == OPEN_KEY and path_label == "upper":
                scale = 0.82 if ring_name == "inner" else 0.92
            deformations[block.name] = delta * scale
        active_offset = Vector()
        for block in blocks[1:]:
            if not block.mute:
                active_offset += block.value * deformations[block.name]
        basis = inverse @ target_world - active_offset
        blocks[0].data[new_index].co = basis
        for block in blocks[1:]:
            block.data[new_index].co = basis + deformations[block.name]
    new_set = set(new_indices)
    for polygon in mesh.polygons:
        if any(index in new_set for index in polygon.vertices):
            polygon.use_smooth = True
    mesh.update()
    return {
        "deletedFaces": len(selected),
        "sourceBoundaryLoops": [len(loop) for loop in loops],
        "outerBoundaryVertices": len(order),
        "addedVertices": len(new_indices),
        "addedFaces": len(added_faces),
        "shapeKeys": len(blocks),
        "shapeKeyCompatible": all(len(block.data) == len(mesh.vertices) for block in blocks),
        "minimumNewVertexGroupCount": min(len(mesh.vertices[index].groups) for index in new_indices),
    }


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, label, expression=None):
    body = bpy.data.objects[BODY]
    keys = body.data.shape_keys.key_blocks
    keys[OPEN_KEY].value = 1.0 if expression == "open" else 0.0
    keys[SMILE_KEY].value = 1.0 if expression == "smile" else 0.0
    camera = scene.camera
    camera.location = (0.0, -0.43, 1.388)
    camera.data.lens = 135
    look_at(camera, (0.0, -0.112, 1.386))
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    keys[OPEN_KEY].value = 0.0
    keys[SMILE_KEY].value = 0.0
    return str(path)


OUT.mkdir(parents=True, exist_ok=True)
variants = []
for label, crest_y, inner_y in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    body = bpy.data.objects[BODY]
    build = build_patch(body, crest_y, inner_y)
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")):
                obj.hide_render = True
    renders = [
        render(scene, f"{label}-neutral"),
        render(scene, f"{label}-mouth-open", "open"),
        render(scene, f"{label}-smile", "smile"),
    ]
    variants.append({
        "label": label,
        "crestY": crest_y,
        "innerY": inner_y,
        "build": build,
        "renders": renders,
        "status": "VISUAL_REVIEW_PENDING",
    })

report = {
    "revision": "v249r1051-two-path-lip-sweep",
    "source": str(SOURCE),
    "method": "delete the measured 296-face r1033 vermilion field; preserve its welded 76-edge outer seam; damp seam irregularity through one transition row; author separate upper/lower crest and aperture paths",
    "variants": variants,
    "websitePromotionApproved": False,
    "status": "VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1051_TWO_PATH=" + json.dumps({item["label"]: item["build"] for item in variants}, sort_keys=True))
