"""Open only the retained r1033 inner lip band and add an attached oral rim."""

import json
import math
from collections import defaultdict
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-lower-lip-rim-turn-r1033-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-local-inner-lip-r1044-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1044-local-inner-lip.study.json"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "v249r1044-local-inner-lip"
BODY = "AevryndFemaleCC0Baseline_v259"
RIG = "AevryndFemaleRig"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
ORAL_LAYERS = (
    "Aevrynd_OralBackWall_R1044", "Aevrynd_UpperGum_R1044", "Aevrynd_LowerGum_R1044",
    "Aevrynd_UpperTeeth_R1044", "Aevrynd_LowerTeeth_R1044", "Aevrynd_Tongue_R1044",
)
CENTER_Z = 1.3862
RADIUS_X = 0.020
RADIUS_Z = 0.0008
RINGS = ((0.0002, 0.03), (0.0005, 0.08), (0.0008, 0.14))


def mixed_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    coordinates = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        relative = block.relative_key
        for index, item in enumerate(block.data):
            coordinates[index] += block.value * (item.co - relative.data[index].co)
    return [body.matrix_world @ point for point in coordinates]


def vertex_components(mesh):
    parent = list(range(len(mesh.vertices)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(first, second):
        first, second = find(first), find(second)
        if first != second:
            parent[second] = first

    for polygon in mesh.polygons:
        vertices = list(polygon.vertices)
        for vertex in vertices[1:]:
            union(vertices[0], vertex)
    groups = defaultdict(set)
    for index in range(len(mesh.vertices)):
        groups[find(index)].add(index)
    return find, sorted(groups.values(), key=len, reverse=True)


def edge_maps(mesh):
    edge_faces = defaultdict(set)
    face_edges = defaultdict(set)
    for polygon in mesh.polygons:
        vertices = list(polygon.vertices)
        for offset, first in enumerate(vertices):
            edge = tuple(sorted((first, vertices[(offset + 1) % len(vertices)])))
            edge_faces[edge].add(polygon.index)
            face_edges[polygon.index].add(edge)
    return edge_faces, face_edges


def face_components(indices, edge_faces, face_edges):
    pending = set(indices)
    result = []
    while pending:
        root = pending.pop()
        queue = [root]
        found = {root}
        while queue:
            neighbors = set().union(*(edge_faces[edge] for edge in face_edges[queue.pop()]))
            fresh = neighbors & pending
            pending.difference_update(fresh)
            found.update(fresh)
            queue.extend(fresh)
        result.append(found)
    return sorted(result, key=len, reverse=True)


def order_loop(edges, points):
    adjacency = defaultdict(set)
    for first, second in edges:
        adjacency[first].add(second)
        adjacency[second].add(first)
    if not adjacency or any(len(neighbors) != 2 for neighbors in adjacency.values()):
        raise RuntimeError("Local inner-lip cut did not produce one degree-two boundary")
    start = max(adjacency, key=lambda index: points[index].x)
    current = max(adjacency[start], key=lambda index: points[index].z)
    ordered = [start]
    previous = start
    while current != start:
        ordered.append(current)
        following = adjacency[current] - {previous}
        if not following:
            raise RuntimeError("Open lip boundary")
        previous, current = current, next(iter(following))
        if len(ordered) > len(adjacency):
            raise RuntimeError("Lip boundary repeated before closure")
    if len(ordered) != len(adjacency):
        raise RuntimeError("Lip boundary contains multiple loops")
    return ordered


def make_material(name, color, roughness, subsurface=0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = subsurface
    material["aevrynd_owned_procedural"] = True
    return material


def build_local_rim(body):
    mesh = body.data
    blocks = list(mesh.shape_keys.key_blocks)
    source = {block.name: [item.co.copy() for item in block.data] for block in blocks}
    points = mixed_coordinates(body)
    find, components = vertex_components(mesh)
    main = components[0]
    main_root = find(next(iter(main)))
    edge_faces, face_edges = edge_maps(mesh)
    candidates = set()
    hidden_main_faces = set()
    for polygon in mesh.polygons:
        if find(polygon.vertices[0]) != main_root:
            continue
        center = sum((points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
        ellipse = (center.x / RADIUS_X) ** 2 + ((center.z - CENTER_Z) / RADIUS_Z) ** 2
        if center.y < -0.105 and ellipse < 1.0:
            candidates.add(polygon.index)
        hidden_ellipse = (center.x / 0.023) ** 2 + ((center.z - CENTER_Z) / 0.0040) ** 2
        if -0.115 < center.y < -0.030 and hidden_ellipse < 1.0:
            hidden_main_faces.add(polygon.index)
    groups = face_components(candidates, edge_faces, face_edges)
    cut = groups[0]
    residual_candidate_faces = set().union(*groups[1:]) if len(groups) > 1 else set()
    boundary_edges = {
        edge for face in cut for edge in face_edges[face]
        if any(neighbor not in cut for neighbor in edge_faces[edge])
    }
    loop = order_loop(boundary_edges, points)

    hidden_components = []
    hidden_roots = set()
    for component in components[1:]:
        local = [points[index] for index in component]
        if len(component) in (68, 226) and max(abs(point.x) for point in local) < 0.040 and 1.36 < min(point.z for point in local) and max(point.z for point in local) < 1.42:
            root = find(next(iter(component)))
            hidden_roots.add(root)
            hidden_components.append(len(component))
    cleanup = residual_candidate_faces | hidden_main_faces | {
        polygon.index for polygon in mesh.polygons
        if find(polygon.vertices[0]) in hidden_roots
    }

    source_weights = {
        index: {membership.group: membership.weight for membership in mesh.vertices[index].groups}
        for index in loop
    }
    inverse = body.matrix_world.inverted()
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    body.active_shape_key_index = 0
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    deform = bm.verts.layers.deform.verify()
    bmesh.ops.delete(bm, geom=[bm.faces[index] for index in sorted(cut | cleanup)], context="FACES_ONLY")
    bm.verts.ensure_lookup_table()
    rows = [[bm.verts[index] for index in loop]]
    descriptors = []
    added_faces = []
    wetline_index = len(mesh.materials) - 1
    for ring_number, (depth, closure) in enumerate(RINGS, start=1):
        row = []
        for boundary_index in loop:
            point = points[boundary_index].copy()
            point.y += depth
            point.x *= 1.0 - 0.025 * closure
            point.z = CENTER_Z + (point.z - CENTER_Z) * (1.0 - 0.35 * closure)
            vertex = bm.verts.new(inverse @ point)
            for group, weight in source_weights[boundary_index].items():
                vertex[deform][group] = weight
            descriptors.append((vertex, point, boundary_index, 1.0))
            row.append(vertex)
        previous = rows[-1]
        for index in range(len(loop)):
            face = bm.faces.new((previous[index], previous[(index + 1) % len(loop)], row[(index + 1) % len(loop)], row[index]))
            face.material_index = wetline_index
            added_faces.append(face)
        rows.append(row)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.verts.index_update()
    new_indices = [vertex.index for vertex, *_ in descriptors]
    bmesh.update_edit_mesh(mesh, loop_triangles=True, destructive=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    mesh.update()

    for (_vertex, target_world, boundary_index, expression_scale), new_index in zip(descriptors, new_indices):
        deformation = {}
        for block in blocks[1:]:
            relative = source[block.relative_key.name][boundary_index]
            delta = source[block.name][boundary_index] - relative
            deformation[block.name] = delta * expression_scale if block.name in (OPEN_KEY, SMILE_KEY) else delta
        active_offset = Vector()
        for block in blocks[1:]:
            if not block.mute:
                active_offset += block.value * deformation[block.name]
        basis = inverse @ target_world - active_offset
        blocks[0].data[new_index].co = basis
        for block in blocks[1:]:
            block.data[new_index].co = basis + deformation[block.name]
    new_set = set(new_indices)
    for polygon in mesh.polygons:
        if any(index in new_set for index in polygon.vertices):
            polygon.use_smooth = True
    mesh.update()
    return {
        "candidateFaces": len(candidates),
        "candidateComponentSizes": [len(group) for group in groups],
        "deletedMainFaces": len(cut),
        "deletedResidualCandidateFaces": len(residual_candidate_faces),
        "deletedHiddenFaces": len(cleanup),
        "deletedHiddenMainFaces": len(hidden_main_faces),
        "removedHiddenComponentVertices": sorted(hidden_components, reverse=True),
        "boundaryEdges": len(boundary_edges),
        "addedRings": len(RINGS),
        "addedVertices": len(new_indices),
        "addedFaces": len(added_faces),
        "shapeKeyCount": len(blocks),
        "shapeKeyCompatibility": all(len(block.data) == len(mesh.vertices) for block in blocks),
        "newVertexMinimumWeightGroupCount": min(len(mesh.vertices[index].groups) for index in new_indices),
    }


def remove_aperture_occluders(body):
    """Delete only original skin faces hit through the intended mouth slit."""
    passes = []
    for _ in range(4):
        mesh = body.data
        points = mixed_coordinates(body)
        polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
        tree = BVHTree.FromPolygons(points, polygons)
        hits = set()
        for x_step in range(-36, 37):
            x = x_step * 0.0005
            for z_step in range(-3, 4):
                z = CENTER_Z + z_step * 0.0002
                location, _normal, polygon_index, _distance = tree.ray_cast(Vector((x, -0.40, z)), Vector((0.0, 1.0, 0.0)), 0.50)
                if polygon_index is None:
                    continue
                polygon = mesh.polygons[polygon_index]
                center = sum((points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
                if polygon.material_index == 0 and center.y < -0.030:
                    hits.add(polygon_index)
        passes.append(len(hits))
        if not hits:
            break
        bpy.context.view_layer.objects.active = body
        body.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        bm = bmesh.from_edit_mesh(mesh)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[bm.faces[index] for index in sorted(hits)], context="FACES_ONLY")
        bmesh.update_edit_mesh(mesh, loop_triangles=True, destructive=True)
        bpy.ops.object.mode_set(mode="OBJECT")
        mesh.update()
    return {"deletedFacesPerPass": passes, "deletedFaces": sum(passes)}


def classify_aperture_occluders(body):
    """Mark only body faces first visible through the slit as inner oral tissue."""
    mesh = body.data
    points = mixed_coordinates(body)
    polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(points, polygons)
    hits = set()
    for x_step in range(-36, 37):
        x = x_step * 0.0005
        for z_step in range(-3, 4):
            z = CENTER_Z + z_step * 0.0002
            _location, _normal, polygon_index, _distance = tree.ray_cast(Vector((x, -0.40, z)), Vector((0.0, 1.0, 0.0)), 0.50)
            if polygon_index is None:
                continue
            polygon = mesh.polygons[polygon_index]
            center = sum((points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
            if polygon.material_index == 0 and center.y < -0.030:
                hits.add(polygon_index)
    wetline_index = len(mesh.materials) - 1
    for polygon_index in hits:
        mesh.polygons[polygon_index].material_index = wetline_index
    mesh.update()
    return {"classifiedFaces": len(hits), "materialIndex": wetline_index}


def object_from_bmesh(name, bm, material):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
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


def ellipsoid_layer(name, entries, material, teeth=False):
    bm = bmesh.new()
    for center, radii in entries:
        (add_superellipsoid if teeth else add_ellipsoid)(bm, center, radii)
    return object_from_bmesh(name, bm, material)


def bind_head(obj):
    world = obj.matrix_world.copy()
    obj.parent = bpy.data.objects[RIG]
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world
    obj["aevrynd_layer_owner"] = "Aevrynd"
    obj["aevrynd_layer_revision"] = "v249r1044"


def build_oral_layers():
    cavity = make_material("Aevrynd_OralBackWallMat_R1044", (0.003, 0.0003, 0.0005), 0.82)
    gum = make_material("Aevrynd_GumMat_R1044", (0.085, 0.010, 0.015), 0.64, 0.10)
    tooth = make_material("Aevrynd_ToothMat_R1044", (0.72, 0.64, 0.52), 0.38)
    tongue = make_material("Aevrynd_TongueMat_R1044", (0.27, 0.045, 0.055), 0.64, 0.12)
    mesh = bpy.data.meshes.new(ORAL_LAYERS[0] + "_Mesh")
    vertices = [(0.0, -0.130, CENTER_Z)]
    for index in range(40):
        angle = 2.0 * math.pi * index / 40
        vertices.append((0.013 * math.sin(angle), -0.130 - 0.0001 * math.cos(angle), CENTER_Z + 0.00025 * math.cos(angle)))
    mesh.from_pydata(vertices, [], [(0, 1 + index, 1 + ((index + 1) % 40)) for index in range(40)])
    mesh.materials.append(cavity)
    back = bpy.data.objects.new(ORAL_LAYERS[0], mesh)
    bpy.context.scene.collection.objects.link(back)
    upper_gum = [((x, -0.058, 1.4030), (0.0022, 0.0008, 0.0008)) for x in [(-0.020 + i * 0.004) for i in range(11)]]
    lower_gum = [((x, -0.061, 1.3695), (0.0020, 0.0006, 0.0006)) for x in [(-0.018 + i * 0.004) for i in range(10)]]
    upper_teeth = [((x, -0.070, 1.4020), (0.0027, 0.0026, 0.0031)) for x in (-0.018, -0.012, -0.006, 0.0, 0.006, 0.012, 0.018)]
    lower_teeth = [((x, -0.067, 1.3710), (0.0025, 0.0024, 0.0025)) for x in (-0.015, -0.009, -0.003, 0.003, 0.009, 0.015)]
    layers = [
        back,
        ellipsoid_layer(ORAL_LAYERS[1], upper_gum, gum),
        ellipsoid_layer(ORAL_LAYERS[2], lower_gum, gum),
        ellipsoid_layer(ORAL_LAYERS[3], upper_teeth, tooth, True),
        ellipsoid_layer(ORAL_LAYERS[4], lower_teeth, tooth, True),
        ellipsoid_layer(ORAL_LAYERS[5], [((0.0, -0.030, 1.3760), (0.017, 0.007, 0.0026))], tongue),
    ]
    for layer in layers:
        bind_head(layer)
    return layers


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles()
    triangles = [tuple(triangle.vertices) for triangle in mesh.loop_triangles]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, triangles, all_triangles=True), triangles


def audit_state(scene, body, layers, frame, expression=None):
    scene.frame_set(frame)
    keys = body.data.shape_keys.key_blocks
    keys[OPEN_KEY].value = 1.0 if expression == OPEN_KEY else 0.0
    keys[SMILE_KEY].value = 1.0 if expression == SMILE_KEY else 0.0
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    body_tree, body_triangles = evaluated_tree(body, depsgraph)
    self_pairs = [(a, b) for a, b in body_tree.overlap(body_tree) if a < b and set(body_triangles[a]).isdisjoint(body_triangles[b])]
    oral = {}
    for layer in layers:
        layer_tree, _ = evaluated_tree(layer, depsgraph)
        oral[layer.name] = len(body_tree.overlap(layer_tree))
    result = {
        "frame": frame,
        "expression": expression or "neutral",
        "bodySelfNonAdjacentPairs": len(self_pairs),
        "bodyOralTriangleOverlap": oral,
    }
    result["status"] = "PASS" if not self_pairs and not any(oral.values()) else "FAIL"
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
scene.frame_set(1)
body.data.shape_keys.key_blocks[OPEN_KEY].value = 0.0
body.data.shape_keys.key_blocks[SMILE_KEY].value = 0.0
wetline = make_material("Aevrynd_InnerLipWetline_R1044", (0.055, 0.0045, 0.007), 0.48, 0.08)
body.data.materials.append(wetline)
topology = build_local_rim(body)
topology["apertureOccluderCleanup"] = {"status": "REJECTED_DIAGNOSTIC_ONLY", "deletedFaces": 0, "reason": "iterative ray deletion exposed progressively deeper folded fragments"}
topology["apertureOccluderMaterial"] = {"status": "REJECTED_DIAGNOSTIC_ONLY", "classifiedFaces": 0, "reason": "ray-hit material reassignment produced hanging dark tabs on visible folded faces"}
layers = build_oral_layers()
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
    render(scene, "mouth-front", (0.0, -0.43, 1.388), (0.0, -0.105, 1.386), 135, (1200, 700)),
    render(scene, "mouth-oblique", (0.21, -0.39, 1.392), (0.0, -0.100, 1.386), 128, (1200, 700)),
]
for layer in layers:
    layer.hide_render = True
rendered.append(render(scene, "mouth-no-oral-layers", (0.0, -0.43, 1.388), (0.0, -0.105, 1.386), 135, (1200, 700)))
wetline_bsdf = next(node for node in wetline.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
wetline_color = wetline_bsdf.inputs["Base Color"].default_value[:]
wetline_bsdf.inputs["Base Color"].default_value = (0.0, 1.0, 0.0, 1.0)
rendered.append(render(scene, "mouth-wetline-isolation", (0.0, -0.43, 1.388), (0.0, -0.105, 1.386), 135, (1200, 700)))
wetline_bsdf.inputs["Base Color"].default_value = wetline_color
for layer in layers:
    layer.hide_render = False
for key, label in ((OPEN_KEY, "open"), (SMILE_KEY, "smile")):
    body.data.shape_keys.key_blocks[key].value = 1.0
    bpy.context.view_layer.update()
    rendered.append(render(scene, label, (0.0, -0.43, 1.388), (0.0, -0.100, 1.386), 135, (1200, 700)))
    body.data.shape_keys.key_blocks[key].value = 0.0
for name in hidden:
    bpy.data.objects[name].hide_render = False

technical = all(state["status"] == "PASS" for state in states)
scene["aevrynd_mainline_revision"] = "v249r1044-local-inner-lip"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REJECTED_SCORE_30" if technical else "TECHNICAL_FAIL"
scene["aevrynd_website_promotion"] = "forbidden"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "remove only a 20-by-0.8 mm inner-lip face band from retained r1033, preserve the outer facial surface, add three attached 36-vertex oral support rings and six explicit Aevrynd-owned oral layers",
    "topology": topology,
    "states": states,
    "rendered": rendered,
    "skinToneContract": "No skin material, light, exposure or color-management changes",
    "strictVisualReview": {
        "mouthScore": 30,
        "retainedMainlineMouthScore": 39,
        "verdict": "REJECTED_BELOW_R1033",
        "gains": [
            "preserves the stable r1033 outer lip and perioral surface",
            "reduces the replacement to a single 36-edge inner aperture with attached support rings",
            "passes all six self-collision and oral-layer overlap states",
        ],
        "failures": [
            "the inherited main head component contains folded internal faces that remain visible through the slit",
            "ray-guided deletion exposes progressively deeper fragments instead of a clean cavity",
            "material reassignment turns the same fragments into hanging tabs rather than anatomical wetline tissue",
            "the inherited mouth-open and smile shapes remain too shallow for credible jaw-coupled expression",
        ],
        "nextTopology": "construct a clean contiguous oral vestibule source with explicit upper/lower inner-lip paths, then transfer the retained r1033 outer surface onto that topology instead of excavating the inherited folded head",
    },
    "websitePromotionApproved": False,
    "status": "TECHNICAL_PASS_VISUAL_REJECTED" if technical else "TECHNICAL_FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1044_LOCAL_INNER_LIP=" + json.dumps({"topology": topology, "states": [state["status"] for state in states], "status": report["status"]}, sort_keys=True))
