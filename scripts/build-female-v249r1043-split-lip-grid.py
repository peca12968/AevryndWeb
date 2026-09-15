"""Replace the r1039 mouth patch with separate upper/lower horizontal grids."""

import json
import math
from collections import defaultdict
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-separated-vermilion-r1039-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-split-lip-grid-r1043-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1043-split-lip-grid.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1043-split-lip-grid"
BODY = "AevryndFemaleCC0Baseline_v259"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
ORAL_LAYERS = (
    "Aevrynd_OralBackWall_R1035", "Aevrynd_UpperGum_R1035", "Aevrynd_LowerGum_R1035",
    "Aevrynd_UpperTeeth_R1035", "Aevrynd_LowerTeeth_R1035", "Aevrynd_Tongue_R1035",
)
CENTER_WORLD_Z = 1.4823
RADIUS_X = 0.040
RADIUS_Z = 0.016
RADIAL_LEVELS = (0.15, 0.30, 0.45, 0.60, 0.72, 0.80, 0.87, 0.93, 1.0)


def edge_maps(mesh):
    edge_faces = defaultdict(set)
    face_edges = defaultdict(set)
    for polygon in mesh.polygons:
        ids = list(polygon.vertices)
        for offset, first in enumerate(ids):
            edge = tuple(sorted((first, ids[(offset + 1) % len(ids)])))
            edge_faces[edge].add(polygon.index)
            face_edges[polygon.index].add(edge)
    return edge_faces, face_edges


def connected_faces(candidates, edge_faces, face_edges):
    remaining = set(candidates)
    groups = []
    while remaining:
        seed = remaining.pop()
        group = {seed}
        stack = [seed]
        while stack:
            fresh = set().union(*(edge_faces[e] for e in face_edges[stack.pop()])) & remaining
            remaining.difference_update(fresh)
            group.update(fresh)
            stack.extend(fresh)
        groups.append(group)
    return sorted(groups, key=len, reverse=True)


def order_loop(edges, points, center_z):
    adjacency = defaultdict(set)
    for first, second in edges:
        adjacency[first].add(second)
        adjacency[second].add(first)
    if not adjacency or any(len(items) != 2 for items in adjacency.values()):
        raise RuntimeError("Boundary is not one simple closed loop")
    start = max(adjacency, key=lambda index: (points[index].x, -abs(points[index].z - center_z)))
    neighbours = list(adjacency[start])
    current = max(neighbours, key=lambda index: points[index].z)
    result = [start]
    previous = start
    while current != start:
        result.append(current)
        following = adjacency[current] - {previous}
        if not following:
            raise RuntimeError("Open boundary encountered")
        previous, current = current, next(iter(following))
        if len(result) > len(adjacency):
            raise RuntimeError("Boundary traversal repeated before closure")
    if len(result) != len(adjacency):
        raise RuntimeError("Boundary traversal did not cover every vertex")
    return result


def original_inner_loop(mesh, points_world):
    edge_faces, _ = edge_maps(mesh)
    boundary = [edge for edge, users in edge_faces.items() if len(users) == 1]
    vertex_edges = defaultdict(set)
    for edge in boundary:
        for vertex in edge:
            vertex_edges[vertex].add(edge)
    remaining = set(boundary)
    groups = []
    while remaining:
        seed = remaining.pop()
        group = {seed}
        stack = [seed]
        while stack:
            fresh = set().union(*(vertex_edges[v] for v in stack.pop())) & remaining
            remaining.difference_update(fresh)
            group.update(fresh)
            stack.extend(fresh)
        groups.append(group)
    for group in groups:
        vertices = {v for edge in group for v in edge}
        center = sum((points_world[v] for v in vertices), Vector()) / len(vertices)
        if len(group) == 120 and abs(center.x) < 0.010:
            return order_loop(group, points_world, center.z)
    raise RuntimeError("Original 120-edge oral boundary not found")


def angle_distance(first, second):
    return abs((first - second + math.pi) % (2.0 * math.pi) - math.pi)


def capture_weights(body, indices):
    return {
        index: {membership.group: membership.weight for membership in body.data.vertices[index].groups}
        for index in indices
    }


def build_patch(body):
    mesh = body.data
    key_blocks = list(mesh.shape_keys.key_blocks)
    source_coords = {block.name: [item.co.copy() for item in block.data] for block in key_blocks}
    neutral_local = [coordinate.copy() for coordinate in source_coords[key_blocks[0].name]]
    for block in key_blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        relative = source_coords[block.relative_key.name]
        for index, coordinate in enumerate(neutral_local):
            coordinate += block.value * (source_coords[block.name][index] - relative[index])
    points_world = [body.matrix_world @ coordinate for coordinate in neutral_local]
    inner_loop = original_inner_loop(mesh, points_world)
    center_z = sum(points_world[index].z for index in inner_loop) / len(inner_loop)
    edge_faces, face_edges = edge_maps(mesh)
    candidates = set()
    for polygon in mesh.polygons:
        center = sum((points_world[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
        ellipse = (center.x / RADIUS_X) ** 2 + ((center.z - center_z) / RADIUS_Z) ** 2
        if center.y < -0.105 and ellipse < 1.0:
            candidates.add(polygon.index)
    selected = connected_faces(candidates, edge_faces, face_edges)[0]
    deleted_material_faces = {
        str(index): sum(1 for face in selected if mesh.polygons[face].material_index == index)
        for index in range(len(mesh.materials))
    }
    boundary_edges = {
        edge for edge, users in edge_faces.items()
        if len(users & selected) == 1 and len(users - selected) >= 1
    }
    outer_loop = order_loop(boundary_edges, points_world, center_z)

    def split_loop(loop):
        left = min(range(len(loop)), key=lambda i: points_world[loop[i]].x)
        upper = list(reversed(loop[:left + 1]))
        lower = loop[left:] + [loop[0]]
        return upper, lower

    outer_upper, outer_lower = split_loop(outer_loop)
    inner_upper, inner_lower = split_loop(inner_loop)
    inverse = body.matrix_world.inverted()
    all_sources = set(outer_loop) | set(inner_loop)
    source_weights = capture_weights(body, all_sources)

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
    outer_bm = {index: bm.verts[index] for index in outer_loop}
    descriptors = []
    new_faces = []
    shared_poles = {}

    def nearest_inner(inner_arc, x):
        return min(inner_arc, key=lambda index: abs(points_world[index].x - x))

    def add_vertex(target_world, outer_index, inner_index, blend):
        vertex = bm.verts.new(inverse @ target_world)
        outer_groups = source_weights[outer_index]
        inner_groups = source_weights[inner_index]
        values = {
            group: (1.0 - blend) * outer_groups.get(group, 0.0) + blend * inner_groups.get(group, 0.0)
            for group in set(outer_groups) | set(inner_groups)
        }
        total = sum(values.values()) or 1.0
        for group, weight in values.items():
            if weight > 1e-8:
                vertex[deform][group] = weight / total
        descriptors.append((vertex, target_world.copy(), outer_index, inner_index, blend))
        return vertex

    def build_half(outer_arc, inner_arc, upper):
        rows = [[outer_bm[index] for index in outer_arc]]
        count = len(outer_arc)
        smoothed_arc = [points_world[index].copy() for index in outer_arc]
        for _ in range(8):
            smoothed_arc = [
                smoothed_arc[0],
                *[
                    smoothed_arc[index] * 0.50 + smoothed_arc[index - 1] * 0.25 + smoothed_arc[index + 1] * 0.25
                    for index in range(1, count - 1)
                ],
                smoothed_arc[-1],
            ]
        for level in RADIAL_LEVELS:
            row = []
            for column, outer_index in enumerate(outer_arc):
                u = -1.0 + 2.0 * column / (count - 1)
                x = 0.0315 * u
                arch = math.sqrt(max(0.0, 1.0 - u * u))
                bow = math.exp(-0.5 * ((abs(x) - 0.0105) / 0.0040) ** 2)
                notch = math.exp(-0.5 * (x / 0.0038) ** 2)
                if upper:
                    inner_z = center_z + 0.00008 + 0.00012 * arch + 0.00016 * bow - 0.00012 * notch
                else:
                    inner_z = center_z - 0.00008 - 0.00012 * arch
                inner_y = smoothed_arc[column].y - 0.0010
                outer_point = points_world[outer_index]
                smooth = level * level * (3.0 - 2.0 * level)
                fairing = min(1.0, level / 0.45)
                fairing = fairing * fairing * (3.0 - 2.0 * fairing)
                guide = outer_point.lerp(smoothed_arc[column], fairing)
                target = guide.lerp(Vector((x, inner_y, inner_z)), smooth)
                lip_profile = math.exp(-0.5 * ((level - 0.80) / 0.16) ** 2) * arch
                target.y -= lip_profile * (0.0012 if upper else 0.0015)
                target.z += lip_profile * (0.00065 if upper else -0.00080)
                inner_index = nearest_inner(inner_arc, x)
                pole_key = "left" if column == 0 else ("right" if column == count - 1 else None)
                if level == 1.0 and pole_key is not None and pole_key in shared_poles:
                    vertex = shared_poles[pole_key]
                else:
                    vertex = add_vertex(target, outer_index, inner_index, smooth)
                    if level == 1.0 and pole_key is not None:
                        shared_poles[pole_key] = vertex
                row.append(vertex)
            previous = rows[-1]
            midpoint = (0.0 if len(rows) == 1 else RADIAL_LEVELS[len(rows) - 2] + level) * 0.5
            material = 0 if midpoint < 0.52 else (3 if midpoint < 0.93 else 2)
            for column in range(count - 1):
                face = bm.faces.new((previous[column], previous[column + 1], row[column + 1], row[column]))
                face.material_index = material
                new_faces.append(face)
            rows.append(row)
        return rows

    upper_rows = build_half(outer_upper, inner_upper, True)
    lower_rows = build_half(outer_lower, inner_lower, False)
    for side in (0, -1):
        for row in range(len(RADIAL_LEVELS)):
            upper_a, upper_b = upper_rows[row][side], upper_rows[row + 1][side]
            lower_a, lower_b = lower_rows[row][side], lower_rows[row + 1][side]
            unique = []
            for vertex in (upper_a, upper_b, lower_b, lower_a):
                if vertex not in unique:
                    unique.append(vertex)
            if len(unique) < 3:
                continue
            face = bm.faces.new(tuple(unique))
            midpoint = (0.0 if row == 0 else RADIAL_LEVELS[row - 1] + RADIAL_LEVELS[row]) * 0.5
            face.material_index = 0 if midpoint < 0.52 else (3 if midpoint < 0.93 else 2)
            new_faces.append(face)

    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.verts.index_update()
    new_indices = [vertex.index for vertex, *_ in descriptors]
    bmesh.update_edit_mesh(mesh, loop_triangles=True, destructive=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    mesh.update()

    for (_vertex, neutral_world, outer_index, inner_index, smooth), new_index in zip(descriptors, new_indices):
        neutral_target = inverse @ neutral_world
        deformations = {}
        for block in key_blocks[1:]:
            outer_relative = source_coords[block.relative_key.name][outer_index]
            inner_relative = source_coords[block.relative_key.name][inner_index]
            outer_delta = source_coords[block.name][outer_index] - outer_relative
            inner_delta = source_coords[block.name][inner_index] - inner_relative
            deformations[block.name] = outer_delta.lerp(inner_delta, smooth) if block.name in (OPEN_KEY, SMILE_KEY) else outer_delta
        active_offset = Vector()
        for block in key_blocks[1:]:
            if not block.mute:
                active_offset += block.value * deformations[block.name]
        new_basis = neutral_target - active_offset
        key_blocks[0].data[new_index].co = new_basis
        for block in key_blocks[1:]:
            block.data[new_index].co = new_basis + deformations[block.name]
    new_set = set(new_indices)
    for polygon in mesh.polygons:
        if any(vertex in new_set for vertex in polygon.vertices):
            polygon.use_smooth = True
    mesh.update()
    used = {vertex for polygon in mesh.polygons for vertex in polygon.vertices}
    return {
        "deletedFaces": len(selected),
        "deletedMaterialFaces": deleted_material_faces,
        "outerUpperVertices": len(outer_upper),
        "outerLowerVertices": len(outer_lower),
        "horizontalRowsPerHalf": len(RADIAL_LEVELS),
        "sharedCommissurePoles": len(shared_poles),
        "addedVertices": len(new_indices),
        "addedFaces": len(new_faces),
        "bodyVertices": len(mesh.vertices),
        "bodyPolygons": len(mesh.polygons),
        "unusedVertices": len(mesh.vertices) - len(used),
        "shapeKeyCount": len(key_blocks),
        "shapeKeyCompatibility": all(len(block.data) == len(mesh.vertices) for block in key_blocks),
        "newVerticesWithWeights": sum(bool(mesh.vertices[index].groups) for index in new_indices),
        "newVertexMinimumWeightGroupCount": min(len(mesh.vertices[index].groups) for index in new_indices),
    }

def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles()
    triangles = [tuple(triangle.vertices) for triangle in mesh.loop_triangles]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, triangles, all_triangles=True), triangles


def body_self_collision(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    tree, triangles = evaluated_tree(body, depsgraph)
    pairs = [(a, b) for a, b in tree.overlap(tree) if a < b and set(triangles[a]).isdisjoint(triangles[b])]
    return {"nonAdjacentPairs": len(pairs), "samplePairs": [list(pair) for pair in pairs[:24]], "status": "PASS" if not pairs else "FAIL"}


def oral_collision(body, layers):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    body_tree, _ = evaluated_tree(body, depsgraph)
    overlaps = {}
    for layer in layers:
        layer_tree, _ = evaluated_tree(layer, depsgraph)
        overlaps[layer.name] = len(body_tree.overlap(layer_tree))
    return {"triangleOverlap": overlaps, "status": "PASS" if not any(overlaps.values()) else "FAIL"}


def audit_state(scene, body, layers, frame, expression=None):
    scene.frame_set(frame)
    keys = body.data.shape_keys.key_blocks
    keys[OPEN_KEY].value = 1.0 if expression == OPEN_KEY else 0.0
    keys[SMILE_KEY].value = 1.0 if expression == SMILE_KEY else 0.0
    bpy.context.view_layer.update()
    result = {"frame": frame, "expression": expression or "neutral", "bodySelf": body_self_collision(body), "bodyOral": oral_collision(body, layers)}
    result["status"] = "PASS" if result["bodySelf"]["status"] == "PASS" and result["bodyOral"]["status"] == "PASS" else "FAIL"
    keys[OPEN_KEY].value = 0.0
    keys[SMILE_KEY].value = 0.0
    bpy.context.view_layer.update()
    return result


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, label, location, target, lens, size):
    camera = scene.camera
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    path = RENDER_DIR / (label + ".png")
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
layers = [bpy.data.objects[name] for name in ORAL_LAYERS]
scene.frame_set(1)
body.data.shape_keys.key_blocks[OPEN_KEY].value = 0.0
body.data.shape_keys.key_blocks[SMILE_KEY].value = 0.0
bpy.context.view_layer.update()
topology = build_patch(body)
states = [audit_state(scene, body, layers, frame) for frame in (1, 20, 33, 61)]
states.extend((audit_state(scene, body, layers, 1, OPEN_KEY), audit_state(scene, body, layers, 1, SMILE_KEY)))
hidden = []
for obj in scene.objects:
    is_hair = obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES"
    is_face_fibre = "Brow" in obj.name or obj.name.endswith(("UpperLashes", "LowerLashes"))
    if is_hair and not is_face_fibre and not obj.hide_render:
        obj.hide_render = True
        hidden.append(obj.name)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
rendered = [
    render(scene, "face-front", (0.0, -0.72, 1.430), (0.0, -0.060, 1.420), 88, (1000, 1000)),
    render(scene, "mouth-front", (0.0, -0.40, 1.388), (0.0, -0.10, 1.386), 135, (1200, 700)),
    render(scene, "mouth-oblique", (0.21, -0.39, 1.392), (0.0, -0.10, 1.386), 128, (1200, 700)),
]
for key, label in ((OPEN_KEY, "open"), (SMILE_KEY, "smile")):
    body.data.shape_keys.key_blocks[key].value = 1.0
    bpy.context.view_layer.update()
    rendered.append(render(scene, label, (0.0, -0.43, 1.388), (0.0, -0.10, 1.386), 135, (1200, 700)))
    body.data.shape_keys.key_blocks[key].value = 0.0
for name in hidden:
    bpy.data.objects[name].hide_render = False
technical = all(state["status"] == "PASS" for state in states)
scene["aevrynd_mainline_revision"] = "v249r1043-split-lip-grid"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REJECTED_SCORE_17" if technical else "TECHNICAL_FAIL"
scene["aevrynd_website_promotion"] = "forbidden"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "replace the complete skin/vermilion/inner-rim region with separate upper and lower horizontal quad grids, sharing explicit commissure poles and interpolating all shape-key deltas and deform weights",
    "topology": topology,
    "states": states,
    "rendered": rendered,
    "skinToneContract": "No material, light, exposure or color-management changes",
    "strictVisualReview": {
        "mouthScore": 17,
        "retainedMainlineMouthScore": 39,
        "verdict": "REJECTED_BELOW_R1033",
        "failures": [
            "the unchanged irregular outer boundary produces repeated pinch spikes across the philtrum, commissures and chin transition",
            "upper and lower grids read as two inflated slabs rather than continuous orbicularis and vermilion anatomy",
            "the nominal 0.4 mm neutral slit exposes planar oral and dental strips with insufficient cavity depth",
            "mouth-open and smile probes remain visually almost identical to neutral and do not show credible jaw-coupled deformation",
        ],
        "nextTopology": "return to the retained r1033 outer facial surface and rebuild only the inner vermilion, wetline and commissure topology with curvature-constrained local edge loops; do not replace the full perioral skin patch",
    },
    "websitePromotionApproved": False,
    "status": "TECHNICAL_PASS_VISUAL_REJECTED" if technical else "TECHNICAL_FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1043_SPLIT_LIP_GRID=" + json.dumps({"topology": topology, "states": [state["status"] for state in states], "status": report["status"]}, sort_keys=True))


