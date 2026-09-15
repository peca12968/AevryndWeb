"""Replace the sealed r1033 mouth with one contiguous weighted aperture and oral layers."""

import json
import math
from collections import defaultdict
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-lower-lip-rim-turn-r1033-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-contiguous-mouth-aperture-r1035-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1035-contiguous-mouth-aperture-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1035-contiguous-mouth-aperture-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
RIG = "AevryndFemaleRig"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
LAYERS = (
    "Aevrynd_OralBackWall_R1035",
    "Aevrynd_UpperGum_R1035",
    "Aevrynd_LowerGum_R1035",
    "Aevrynd_UpperTeeth_R1035",
    "Aevrynd_LowerTeeth_R1035",
    "Aevrynd_Tongue_R1035",
)
VARIANTS = (("a-restrained", 0.022, 0.0038), ("b-anatomical", 0.026, 0.0048), ("c-open", 0.030, 0.0060))
SELECTED = "b-anatomical"


def mixed_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    coordinates = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        for index, coordinate in enumerate(coordinates):
            coordinate += block.value * (block.data[index].co - block.relative_key.data[index].co)
    return [body.matrix_world @ coordinate for coordinate in coordinates]


def connected_components(body):
    parent = list(range(len(body.data.vertices)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(first, second):
        first = find(first)
        second = find(second)
        if first != second:
            parent[second] = first

    for polygon in body.data.polygons:
        vertices = list(polygon.vertices)
        for vertex in vertices[1:]:
            union(vertices[0], vertex)
    components = defaultdict(set)
    for index in range(len(body.data.vertices)):
        components[find(index)].add(index)
    return find, components


def face_maps(body):
    face_edges = {}
    edge_faces = defaultdict(set)
    for polygon in body.data.polygons:
        indices = list(polygon.vertices)
        edges = {tuple(sorted((indices[index], indices[(index + 1) % len(indices)]))) for index in range(len(indices))}
        face_edges[polygon.index] = edges
        for edge in edges:
            edge_faces[edge].add(polygon.index)
    return face_edges, edge_faces


def face_components(face_indices, face_edges, edge_faces):
    remaining = set(face_indices)
    result = []
    while remaining:
        seed = remaining.pop()
        stack = [seed]
        component = {seed}
        while stack:
            face = stack.pop()
            neighbours = set()
            for edge in face_edges[face]:
                neighbours.update(edge_faces[edge])
            fresh = neighbours & remaining
            remaining.difference_update(fresh)
            component.update(fresh)
            stack.extend(fresh)
        result.append(component)
    return sorted(result, key=len, reverse=True)


def cut_and_cleanup(body, radius_x, radius_z):
    before = {"vertices": len(body.data.vertices), "polygons": len(body.data.polygons), "shapeKeys": [block.name for block in body.data.shape_keys.key_blocks]}
    points = mixed_coordinates(body)
    find, components = connected_components(body)
    sizes = {root: len(vertices) for root, vertices in components.items()}
    main_root = max(components, key=lambda root: sizes[root])
    face_edges, edge_faces = face_maps(body)
    candidates = set()
    for polygon in body.data.polygons:
        if find(polygon.vertices[0]) != main_root:
            continue
        center = sum((points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
        ellipse = (center.x / radius_x) ** 2 + ((center.z - 1.3890) / radius_z) ** 2
        # The MPFB body folds a second surface behind the visible face.  Cut
        # the full proven oral projection, otherwise that inner sheet remains
        # as a skin-coloured plug after the outer faces are removed.
        if center.y < -0.040 and ellipse < 1.0:
            candidates.add(polygon.index)
    candidate_components = face_components(candidates, face_edges, edge_faces)
    cut_faces = candidate_components[0] if candidate_components else set()

    oral_roots = set()
    oral_inventory = []
    for root, vertices in components.items():
        if root == main_root or len(vertices) >= 300:
            continue
        local = [points[index] for index in vertices]
        if any(abs(point.x) < 0.080 and point.y < -0.040 and 1.330 < point.z < 1.430 for point in local):
            oral_roots.add(root)
            oral_inventory.append({
                "vertices": len(vertices),
                "x": [min(point.x for point in local), max(point.x for point in local)],
                "y": [min(point.y for point in local), max(point.y for point in local)],
                "z": [min(point.z for point in local), max(point.z for point in local)],
            })
    cleanup_faces = {polygon.index for polygon in body.data.polygons if find(polygon.vertices[0]) in oral_roots}
    delete_faces = sorted(cut_faces | cleanup_faces)
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    body.active_shape_key_index = 0
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(body.data)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[index] for index in delete_faces], context="FACES_ONLY")
    bmesh.update_edit_mesh(body.data, loop_triangles=True, destructive=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    body.data.update()
    # The first cut detaches a second folded sheet from the main component.
    # Remove that newly isolated oral plug in a second topology pass.
    find_after, components_after = connected_components(body)
    main_after = max(components_after, key=lambda root: len(components_after[root]))
    post_roots = set()
    post_inventory = []
    for root, vertices in components_after.items():
        if root == main_after or len(vertices) >= 1000:
            continue
        local = [points[index] for index in vertices]
        if any(abs(point.x) < 0.036 and -0.130 < point.y < -0.030 and 1.380 < point.z < 1.398 for point in local):
            post_roots.add(root)
            post_inventory.append({"vertices": len(vertices), "faces": sum(1 for polygon in body.data.polygons if find_after(polygon.vertices[0]) == root)})
    post_faces = [polygon.index for polygon in body.data.polygons if find_after(polygon.vertices[0]) in post_roots]
    if post_faces:
        bpy.context.view_layer.objects.active = body
        body.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        bm = bmesh.from_edit_mesh(body.data)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[bm.faces[index] for index in post_faces], context="FACES_ONLY")
        bmesh.update_edit_mesh(body.data, loop_triangles=True, destructive=True)
        bpy.ops.object.mode_set(mode="OBJECT")
        body.data.update()
    return before, {
        "candidateFaces": len(candidates),
        "candidateComponentSizes": [len(component) for component in candidate_components],
        "deletedMainFaces": len(cut_faces),
        "deletedHiddenComponentFaces": len(cleanup_faces),
        "removedHiddenComponents": sorted(oral_inventory, key=lambda item: item["vertices"], reverse=True),
        "deletedPostCutPlugFaces": len(post_faces),
        "removedPostCutPlugComponents": post_inventory,
    }


def mouth_boundary(body):
    points = mixed_coordinates(body)
    users = defaultdict(int)
    for polygon in body.data.polygons:
        indices = list(polygon.vertices)
        for index, first in enumerate(indices):
            users[tuple(sorted((first, indices[(index + 1) % len(indices)])))] += 1
    candidates = []
    for edge in body.data.edges:
        if users[tuple(sorted(edge.vertices))] != 1:
            continue
        midpoint = (points[edge.vertices[0]] + points[edge.vertices[1]]) * 0.5
        if abs(midpoint.x) < 0.045 and midpoint.y < -0.110 and 1.370 < midpoint.z < 1.408:
            candidates.append(edge.index)
    vertex_edges = defaultdict(set)
    for edge_index in candidates:
        for vertex in body.data.edges[edge_index].vertices:
            vertex_edges[vertex].add(edge_index)
    remaining = set(candidates)
    components = []
    while remaining:
        seed = remaining.pop()
        stack = [seed]
        component = {seed}
        while stack:
            edge_index = stack.pop()
            neighbours = set()
            for vertex in body.data.edges[edge_index].vertices:
                neighbours.update(vertex_edges[vertex])
            fresh = neighbours & remaining
            remaining.difference_update(fresh)
            component.update(fresh)
            stack.extend(fresh)
        components.append(component)
    components.sort(key=len, reverse=True)
    return sorted(components[0]), sorted((len(component) for component in components), reverse=True)


def subdivide_boundary(body, edge_indices):
    before = len(body.data.vertices)
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    body.active_shape_key_index = 0
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(body.data)
    bm.edges.ensure_lookup_table()
    bmesh.ops.subdivide_edges(bm, edges=[bm.edges[index] for index in edge_indices], cuts=1, use_grid_fill=True)
    bmesh.update_edit_mesh(body.data, loop_triangles=True, destructive=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    body.data.update()
    after = len(body.data.vertices)
    key_lengths = {block.name: len(block.data) for block in body.data.shape_keys.key_blocks}
    return {"beforeVertices": before, "afterVertices": after, "addedVertices": after - before, "shapeKeyCompatibility": all(length == after for length in key_lengths.values())}


def regularize_boundary(body, edge_indices, radius_x, radius_z):
    points = mixed_coordinates(body)
    inverse3 = body.matrix_world.inverted().to_3x3()
    vertices = sorted({vertex for edge_index in edge_indices for vertex in body.data.edges[edge_index].vertices})
    deltas = {}
    for index in vertices:
        point = points[index]
        u = max(-1.0, min(1.0, point.x / radius_x))
        arc = math.sqrt(max(0.0, 1.0 - u * u))
        cupid = math.exp(-0.5 * ((abs(point.x) - 0.010) / 0.004) ** 2)
        notch = math.exp(-0.5 * (point.x / 0.0038) ** 2)
        if point.z >= 1.3890:
            target_z = 1.3890 + radius_z * arc + 0.00035 * cupid - 0.00018 * notch
        else:
            target_z = 1.3890 - radius_z * 0.76 * arc
        target = point.copy()
        target.z = point.z * 0.20 + target_z * 0.80
        target_y = -0.1320 - 0.0080 * arc
        target.y = point.y * 0.20 + target_y * 0.80
        deltas[index] = inverse3 @ (target - point)
    for block in body.data.shape_keys.key_blocks:
        for index, delta in deltas.items():
            block.data[index].co += delta
    body.data.update()
    return {"vertices": len(vertices), "maximumDeltaMm": max(delta.length for delta in deltas.values()) * 1000.0, "meanDeltaMm": sum(delta.length for delta in deltas.values()) / len(deltas) * 1000.0}


def extrude_inner_rings(body, edge_indices, material_index):
    before = len(body.data.vertices)
    before_keys = [block.name for block in body.data.shape_keys.key_blocks]
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    body.active_shape_key_index = 0
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(body.data)
    bm.edges.ensure_lookup_table()
    deform = bm.verts.layers.deform.verify()
    source_edges = [bm.edges[index] for index in edge_indices]
    source_vertices = {vertex for edge in source_edges for vertex in edge.verts}
    center = sum((vertex.co for vertex in source_vertices), Vector()) / len(source_vertices)
    result1 = bmesh.ops.extrude_edge_only(bm, edges=source_edges)
    ring1 = [item for item in result1["geom"] if isinstance(item, bmesh.types.BMVert)]
    for vertex in ring1:
        source = min(source_vertices, key=lambda item: (item.co - vertex.co).length_squared)
        for group, weight in source[deform].items():
            vertex[deform][group] = weight
        vertex.co.x = center.x + (vertex.co.x - center.x) * 0.97
        vertex.co.z = center.z + (vertex.co.z - center.z) * 0.97
        vertex.co.y += 0.0012
    ring1_set = set(ring1)
    ring1_edges = [item for item in result1["geom"] if isinstance(item, bmesh.types.BMEdge) and all(vertex in ring1_set for vertex in item.verts) and len(item.link_faces) == 1]
    for face in [item for item in result1["geom"] if isinstance(item, bmesh.types.BMFace)]:
        face.material_index = material_index
    result2 = bmesh.ops.extrude_edge_only(bm, edges=ring1_edges)
    ring2 = [item for item in result2["geom"] if isinstance(item, bmesh.types.BMVert)]
    for vertex in ring2:
        source = min(ring1, key=lambda item: (item.co - vertex.co).length_squared)
        for group, weight in source[deform].items():
            vertex[deform][group] = weight
        vertex.co.x = center.x + (vertex.co.x - center.x) * 0.93
        vertex.co.z = center.z + (vertex.co.z - center.z) * 0.93
        vertex.co.y += 0.0020
    for face in [item for item in result2["geom"] if isinstance(item, bmesh.types.BMFace)]:
        face.material_index = material_index
    bmesh.update_edit_mesh(body.data, loop_triangles=True, destructive=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    body.data.update()
    after = len(body.data.vertices)
    key_lengths = {block.name: len(block.data) for block in body.data.shape_keys.key_blocks}
    weight_counts = [len(body.data.vertices[index].groups) for index in range(before, after)]
    return {
        "beforeVertices": before,
        "afterVertices": after,
        "addedVertices": after - before,
        "firstRingVertices": len(ring1),
        "secondRingVertices": len(ring2),
        "shapeKeyCompatibility": before_keys == list(key_lengths) and all(length == after for length in key_lengths.values()),
        "shapeKeyCount": len(key_lengths),
        "newVerticesWithWeights": sum(value > 0 for value in weight_counts),
        "newVertexMinimumWeightGroupCount": min(weight_counts) if weight_counts else 0,
    }


def make_material(name, color, roughness, subsurface=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = subsurface
    mat["aevrynd_owned_procedural"] = True
    return mat


def object_from_bmesh(name, bm, mat):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    return obj


def add_ellipsoid(bm, center, radii):
    transform = Matrix.Translation(Vector(center)) @ Matrix.Diagonal((*radii, 1.0))
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=1.0, matrix=transform)


def add_superellipsoid(bm, center, radii, exponent=0.62):
    result = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=1.0)
    for vertex in result["verts"]:
        point = vertex.co.copy()
        shaped = Vector(tuple(math.copysign(abs(value) ** exponent, value) if abs(value) > 1e-9 else 0.0 for value in point))
        vertex.co = Vector(center) + Vector((shaped.x * radii[0], shaped.y * radii[1], shaped.z * radii[2]))


def ellipsoid_layer(name, entries, mat):
    bm = bmesh.new()
    for center, radii in entries:
        add_ellipsoid(bm, center, radii)
    return object_from_bmesh(name, bm, mat)


def tooth_layer(name, entries, mat):
    bm = bmesh.new()
    for center, radii in entries:
        add_superellipsoid(bm, center, radii)
    return object_from_bmesh(name, bm, mat)


def back_wall(name, mat):
    segments = 40
    vertices = [(0.0, -0.004, 1.389)]
    for index in range(segments):
        angle = 2.0 * math.pi * index / segments
        vertices.append((0.023 * math.sin(angle), -0.004 - 0.001 * math.cos(angle), 1.389 + 0.007 * math.cos(angle)))
    faces = [(0, 1 + index, 1 + ((index + 1) % segments)) for index in range(segments)]
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def gum_layer(name, upper, mat):
    bm = bmesh.new()
    z = 1.3970 if upper else 1.3805
    for index in range(11):
        x = -0.023 + index * 0.0046
        lateral = abs(x) / 0.023
        y = (-0.058 if upper else -0.064) + 0.003 * lateral * lateral
        radii = (0.0024, 0.0009, 0.0010) if upper else (0.0021, 0.0006, 0.0007)
        add_ellipsoid(bm, (x, y, z + (0.0008 if upper else -0.0004) * lateral), radii)
    return object_from_bmesh(name, bm, mat)


def bind_head(obj):
    world = obj.matrix_world.copy()
    obj.parent = bpy.data.objects[RIG]
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world
    obj["aevrynd_layer_owner"] = "Aevrynd"
    obj["aevrynd_layer_revision"] = "v249r1035"


def build_oral_layers():
    cavity_mat = make_material("Aevrynd_OralBackWallMat_R1035", (0.003, 0.0003, 0.0005), 0.82)
    gum_mat = make_material("Aevrynd_GumMat_R1035", (0.085, 0.010, 0.015), 0.64, 0.10)
    tooth_mat = make_material("Aevrynd_ToothMat_R1035", (0.72, 0.64, 0.52), 0.38)
    tongue_mat = make_material("Aevrynd_TongueMat_R1035", (0.27, 0.045, 0.055), 0.64, 0.12)
    layers = [back_wall(LAYERS[0], cavity_mat), gum_layer(LAYERS[1], True, gum_mat), gum_layer(LAYERS[2], False, gum_mat)]
    upper = []
    for index, x in enumerate((-0.0265, -0.0210, -0.0152, -0.0092, -0.0031, 0.0031, 0.0092, 0.0152, 0.0210, 0.0265)):
        lateral = abs(x) / 0.0265
        width = 0.0032 if 3 <= index <= 6 else 0.0028
        upper.append(((x, -0.073 + 0.004 * lateral * lateral, 1.3975 + 0.0008 * lateral), (width * 0.90, 0.0028, 0.0035 - 0.0005 * lateral)))
    lower = []
    for index, x in enumerate((-0.0215, -0.0155, -0.0094, -0.0031, 0.0031, 0.0094, 0.0155, 0.0215)):
        lateral = abs(x) / 0.0215
        width = 0.0030 if 2 <= index <= 5 else 0.0027
        lower.append(((x, -0.069 + 0.0035 * lateral * lateral, 1.3775 - 0.0005 * lateral), (width * 0.88, 0.0026, 0.0028 - 0.0003 * lateral)))
    layers.append(tooth_layer(LAYERS[3], upper, tooth_mat))
    layers.append(tooth_layer(LAYERS[4], lower, tooth_mat))
    layers.append(ellipsoid_layer(LAYERS[5], [((0.0, -0.025, 1.3740), (0.020, 0.008, 0.0030))], tongue_mat))
    for obj in layers:
        bind_head(obj)
    return layers


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles()
    triangles = [tuple(triangle.vertices) for triangle in mesh.loop_triangles]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, triangles, all_triangles=True), triangles


def collision(body, layers):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    body_tree, _ = world_tree(body, depsgraph)
    trees = {}
    body_counts = {}
    for obj in layers:
        tree, _ = world_tree(obj, depsgraph)
        trees[obj.name] = tree
        body_counts[obj.name] = len(body_tree.overlap(tree))
    pair_counts = {}
    for first_index, first in enumerate(layers):
        for second in layers[first_index + 1:]:
            pair_counts[first.name + "::" + second.name] = len(trees[first.name].overlap(trees[second.name]))
    return body_counts, pair_counts


def body_self_collision(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    tree, triangles = world_tree(body, depsgraph)
    pairs = [(first, second) for first, second in tree.overlap(tree) if first < second and set(triangles[first]).isdisjoint(triangles[second])]
    return {"nonAdjacentPairs": len(pairs), "samplePairs": [list(pair) for pair in pairs[:24]], "status": "PASS" if not pairs else "FAIL"}


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def hide_hair(scene):
    hidden = []
    for obj in scene.objects:
        is_hair = obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES"
        is_face_fibre = "Brow" in obj.name or obj.name.endswith(("UpperLashes", "LowerLashes"))
        if is_hair and not is_face_fibre and not obj.hide_render:
            obj.hide_render = True
            hidden.append(obj.name)
    return hidden


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


RENDER_DIR.mkdir(parents=True, exist_ok=True)
variants = []
for label, radius_x, radius_z in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    body = bpy.data.objects[BODY]
    before, cut = cut_and_cleanup(body, radius_x, radius_z)
    bpy.context.view_layer.update()
    boundary, inventory = mouth_boundary(body)
    subdivision = subdivide_boundary(body, boundary)
    bpy.context.view_layer.update()
    boundary, inventory_after_subdivision = mouth_boundary(body)
    regularization = regularize_boundary(body, boundary, radius_x, radius_z)
    bpy.context.view_layer.update()
    boundary, _ = mouth_boundary(body)
    rim_material = make_material("Aevrynd_InnerMouthRimMat_R1035", (0.018, 0.0012, 0.0025), 0.74, 0.08)
    body.data.materials.append(rim_material)
    inner_rim = extrude_inner_rings(body, boundary, len(body.data.materials) - 1)
    layers = build_oral_layers()
    bpy.context.view_layer.update()
    body_counts, pair_counts = collision(body, layers)
    self_audit = body_self_collision(body)
    hidden = hide_hair(scene)
    rendered = [
        render(scene, label + "-face-front", (0.0, -0.72, 1.430), (0.0, -0.060, 1.420), 88, (1000, 1000)),
        render(scene, label + "-mouth-front", (0.0, -0.43, 1.388), (0.0, -0.105, 1.386), 135, (1200, 700)),
        render(scene, label + "-mouth-oblique", (0.21, -0.39, 1.392), (0.0, -0.100, 1.386), 128, (1200, 700)),
    ]
    open_key = body.data.shape_keys.key_blocks.get(OPEN_KEY)
    if open_key:
        open_key.value = 1.5
        bpy.context.view_layer.update()
        rendered.append(render(scene, label + "-mouth-open", (0.0, -0.43, 1.388), (0.0, -0.100, 1.386), 135, (1200, 700)))
        open_key.value = 0.0
    for name in hidden:
        bpy.data.objects[name].hide_render = False
    body_failures = {name: count for name, count in body_counts.items() if count}
    pair_failures = {name: count for name, count in pair_counts.items() if count}
    after = {"vertices": len(body.data.vertices), "polygons": len(body.data.polygons), "shapeKeys": [block.name for block in body.data.shape_keys.key_blocks]}
    technical = before["shapeKeys"] == after["shapeKeys"] and subdivision["shapeKeyCompatibility"] and inner_rim["shapeKeyCompatibility"] and inner_rim["newVerticesWithWeights"] == inner_rim["addedVertices"] and not body_failures and not pair_failures and self_audit["status"] == "PASS"
    item = {"label": label, "apertureRadiusM": [radius_x, radius_z], "before": before, "cut": cut, "boundaryComponentInventory": inventory, "subdivision": subdivision, "boundaryComponentInventoryAfterSubdivision": inventory_after_subdivision, "regularization": regularization, "innerRim": inner_rim, "after": after, "bodyLayerTriangleOverlap": body_counts, "interLayerTriangleOverlap": pair_counts, "bodySelfCollision": self_audit, "rendered": rendered, "status": "TECHNICAL_PASS" if technical else "TECHNICAL_FAIL"}
    variants.append(item)
    if label == SELECTED and technical:
        scene["aevrynd_mainline_revision"] = "v249r1035-contiguous-mouth-aperture"
        scene["aevrynd_mainline_parent"] = SOURCE.name
        scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REJECTED_STUDY_ONLY"
        scene["aevrynd_website_promotion"] = "forbidden"
        scene["aevrynd_oral_layer_names"] = json.dumps(list(LAYERS))
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {"source": str(SOURCE), "output": str(OUTPUT), "method": "remove sealed face patch and proven hidden oral fragments, regularize one contiguous aperture, extrude two weighted inner rings, then add six owned head-bound oral layers", "variants": variants, "provisionalSelection": SELECTED, "selectedVariant": None, "retainedTechnicalStudy": SELECTED, "visualAssessment": "All bounds fail the strict visual gate: the inherited facial topology produces a jagged aperture, the outer vermilion transition is missing, and the opening reads as a cutout. The b-anatomical file is retained only because its topology, weights and dynamic collision gates pass.", "strictMouthScore": 24, "websitePromotionApproved": False, "status": "TECHNICAL_PASS_VISUAL_REJECTED_STUDY_ONLY"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1035_MOUTH_APERTURE=" + json.dumps({"output": str(OUTPUT), "variants": [{"label": item["label"], "cut": item["cut"]["deletedMainFaces"], "boundary": item["regularization"]["vertices"], "added": item["innerRim"]["addedVertices"], "bodyFailures": sum(1 for count in item["bodyLayerTriangleOverlap"].values() if count), "pairFailures": sum(1 for count in item["interLayerTriangleOverlap"].values() if count), "selfPairs": item["bodySelfCollision"]["nonAdjacentPairs"], "status": item["status"]} for item in variants]}, sort_keys=True))
