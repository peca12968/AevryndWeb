import json
from collections import defaultdict, deque
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-nasal-midface-planes-r473.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-fitted-upper-lip-r475.blend"
REPORT = ASSETS / "female-v249-mainline-fitted-upper-lip-r475.build-report.json"
REVIEW_DIR = ASSETS / "reviews/v249r475-fitted-upper-lip"
BODY = "AevryndFemaleBodyBaseV118"
UPPER = "Lip_Upper"
CLEARANCE = 0.00045


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def body_bvh(body, depsgraph):
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


def outward(normal):
    normal = normal.normalized()
    if normal.y > 0.0:
        normal.negate()
    return normal


def boundary_rings(mesh):
    edge_faces = defaultdict(int)
    adjacency = defaultdict(set)
    for polygon in mesh.polygons:
        for edge in polygon.edge_keys:
            edge_faces[tuple(sorted(edge))] += 1
    for edge in mesh.edges:
        a, b = edge.vertices
        adjacency[a].add(b)
        adjacency[b].add(a)
    boundary = {vertex for edge, count in edge_faces.items() if count == 1 for vertex in edge}
    distances = {vertex: 0 for vertex in boundary}
    queue = deque(boundary)
    while queue:
        current = queue.popleft()
        for neighbor in adjacency[current]:
            if neighbor not in distances:
                distances[neighbor] = distances[current] + 1
                queue.append(neighbor)
    return boundary, distances


def fit_upper_lip(upper, tree, depsgraph):
    mesh = upper.data
    boundary, rings = boundary_rings(mesh)
    maximum_ring = max(rings.values())
    evaluated = upper.evaluated_get(depsgraph)
    evaluated_mesh = evaluated.to_mesh()
    world_points = [evaluated.matrix_world @ vertex.co for vertex in evaluated_mesh.vertices]
    evaluated.to_mesh_clear()
    inverse = upper.matrix_world.inverted()
    moved = 0
    maximum_delta = 0.0
    minimum_clearance = float("inf")
    for index, point in enumerate(world_points):
        hit, normal, _face, _distance = tree.find_nearest(point)
        signed = (point - hit).dot(normal)
        safe = hit + normal * max(CLEARANCE, signed)
        t = rings[index] / maximum_ring
        authored_weight = smoothstep(t)
        target = safe.lerp(point, authored_weight)
        hit2, normal2, _face2, _distance2 = tree.find_nearest(target)
        signed2 = (target - hit2).dot(normal2)
        if signed2 < CLEARANCE:
            target = hit2 + normal2 * CLEARANCE
            signed2 = CLEARANCE
        delta = (target - point).length
        mesh.vertices[index].co = inverse @ target
        moved += delta > 1e-7
        maximum_delta = max(maximum_delta, delta)
        minimum_clearance = min(minimum_clearance, signed2)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    mesh.update()
    return {
        "vertices": len(mesh.vertices),
        "polygons": len(mesh.polygons),
        "boundaryVertices": len(boundary),
        "topologicalRings": maximum_ring + 1,
        "verticesMoved": moved,
        "maximumFitDeltaMm": maximum_delta * 1000.0,
        "minimumAuthoredClearanceMm": minimum_clearance * 1000.0,
    }


def repair_dynamic_clearance(scene, body, upper, frames=(20, 1, 20, 1), margin=0.00008):
    changes = []
    inverse3 = upper.matrix_world.inverted().to_3x3()
    for pass_index, frame in enumerate(frames, 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        tree = body_bvh(body, depsgraph)
        evaluated = upper.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        if len(mesh.vertices) != len(upper.data.vertices):
            evaluated.to_mesh_clear()
            raise RuntimeError("upper-lip evaluated/base vertex count mismatch")
        points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
        evaluated.to_mesh_clear()
        moved = 0
        maximum = 0.0
        for index, point in enumerate(points):
            hit = tree.find_nearest(point, 0.008)
            if hit is None or hit[1] is None:
                continue
            normal = outward(hit[1])
            signed = (point - hit[0]).dot(normal)
            if signed >= CLEARANCE:
                continue
            translation = normal * (CLEARANCE - signed + margin)
            upper.data.vertices[index].co += inverse3 @ translation
            moved += 1
            maximum = max(maximum, translation.length)
        upper.data.update()
        bpy.context.view_layer.update()
        changes.append({"pass": pass_index, "frame": frame, "verticesMoved": moved, "maximumTranslationMm": maximum * 1000.0})
    scene.frame_set(1)
    bpy.context.view_layer.update()
    return changes


def repair_intersecting_faces(scene, body, upper, passes=8, face_clearance=0.00082):
    changes = []
    inverse3 = upper.matrix_world.inverted().to_3x3()
    for pass_index in range(1, passes + 1):
        frame = 1 if pass_index % 2 else 20
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        body_tree = body_bvh(body, depsgraph)
        evaluated = upper.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
        polygons = [tuple(poly.vertices) for poly in mesh.polygons]
        upper_tree = BVHTree.FromPolygons(points, polygons, all_triangles=False)
        overlaps = body_tree.overlap(upper_tree)
        face_indices = sorted({upper_face for _body_face, upper_face in overlaps})
        if not face_indices:
            evaluated.to_mesh_clear()
            changes.append({"pass": pass_index, "frame": frame, "overlapFaces": 0, "verticesMoved": 0, "maximumTranslationMm": 0.0})
            continue
        affected_vertices = sorted({index for face_index in face_indices for index in polygons[face_index]})
        translations = {}
        maximum = 0.0
        for index in affected_vertices:
            point = points[index]
            hit = body_tree.find_nearest(point, 0.008)
            if hit is None or hit[1] is None:
                continue
            normal = outward(hit[1])
            signed = (point - hit[0]).dot(normal)
            translation = normal * max(0.00012, face_clearance - signed)
            translations[index] = translation
            maximum = max(maximum, translation.length)
        evaluated.to_mesh_clear()
        for index, translation in translations.items():
            upper.data.vertices[index].co += inverse3 @ translation
        upper.data.update()
        changes.append({
            "pass": pass_index,
            "frame": frame,
            "overlapFaces": len(face_indices),
            "verticesMoved": len(translations),
            "maximumTranslationMm": maximum * 1000.0,
        })
    scene.frame_set(1)
    bpy.context.view_layer.update()
    return changes


def transparent_material():
    material = bpy.data.materials.new("Aevrynd_LipOuter_Transparent_R475")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    material.node_tree.links.new(transparent.outputs[0], output.inputs[0])
    material.surface_render_method = "BLENDED"
    return material


def remove_transparent_transition_faces(upper):
    mesh = upper.data
    bmesh_data = bmesh.new()
    bmesh_data.from_mesh(mesh)
    faces = [face for face in bmesh_data.faces if face.material_index == 0]
    removed = len(faces)
    bmesh.ops.delete(bmesh_data, geom=faces, context="FACES")
    bmesh_data.to_mesh(mesh)
    bmesh_data.free()
    mesh.update()
    return {"facesRemoved": removed, "remainingVertices": len(mesh.vertices), "remainingPolygons": len(mesh.polygons)}


def tint_skin_material(source, name, target, factor, roughness):
    material = source.copy()
    material.name = name
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    base = shader.inputs["Base Color"]
    source_socket = base.links[0].from_socket
    for link in list(base.links):
        links.remove(link)
    mix = nodes.new("ShaderNodeMixRGB")
    mix.name = name + " Color Mix"
    mix.blend_type = "MIX"
    mix.inputs[0].default_value = factor
    mix.inputs[2].default_value = target
    links.new(source_socket, mix.inputs[1])
    links.new(mix.outputs["Color"], base)
    shader.inputs["Roughness"].default_value = roughness
    return material


def add_lower_lip_response(body, world_points, source_material):
    attribute_name = "AevryndLowerVermilionR475"
    old = body.data.color_attributes.get(attribute_name)
    if old:
        body.data.color_attributes.remove(old)
    attribute = body.data.color_attributes.new(name=attribute_name, type="FLOAT_COLOR", domain="POINT")
    tinted = 0
    maximum = 0.0
    for index, point in enumerate(world_points):
        ax = abs(point.x)
        width = 1.0 - smoothstep((ax - 0.030) / 0.014)
        lower = smoothstep((point.z - 1.5194) / 0.0018) * (1.0 - smoothstep((point.z - 1.5282) / 0.0015))
        front = 1.0 - smoothstep((point.y + 0.126) / 0.018)
        mask = 0.10 * width * lower * front if ax < 0.044 and point.y < -0.108 else 0.0
        mask = clamp(mask)
        attribute.data[index].color = (mask, mask, mask, 1.0)
        if mask > 0.001:
            tinted += 1
            maximum = max(maximum, mask)
    material = source_material.copy()
    material.name = "Aevrynd_Skin_LowerVermilion_R475"
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    base = shader.inputs["Base Color"]
    source_socket = base.links[0].from_socket
    for link in list(base.links):
        links.remove(link)
    color = nodes.new("ShaderNodeVertexColor")
    color.name = "Aevrynd Lower Vermilion Mask R475"
    color.layer_name = attribute_name
    mix = nodes.new("ShaderNodeMixRGB")
    mix.name = "Aevrynd Lower Vermilion Color R475"
    mix.blend_type = "MIX"
    mix.inputs[2].default_value = (0.18, 0.050, 0.043, 1.0)
    links.new(color.outputs["Color"], mix.inputs[0])
    links.new(source_socket, mix.inputs[1])
    links.new(mix.outputs["Color"], base)
    body.data.materials.clear()
    body.data.materials.append(material)
    return {"attribute": attribute_name, "verticesTinted": tinted, "maximumMix": maximum, "material": material.name}


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, label, location, target, lens, size, frame=1):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(REVIEW_DIR / f"{label}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
body = bpy.data.objects[BODY]
upper = bpy.data.objects[UPPER]
source_skin = body.active_material
body_evaluated = body.evaluated_get(depsgraph)
body_mesh = body_evaluated.to_mesh()
body_world_points = [body_evaluated.matrix_world @ vertex.co for vertex in body_mesh.vertices]
body_evaluated.to_mesh_clear()
fit = fit_upper_lip(upper, body_bvh(body, depsgraph), depsgraph)
transition_removal = remove_transparent_transition_faces(upper)
upper.hide_render = False
upper.data.materials[0] = transparent_material()
upper.data.materials[1] = tint_skin_material(
    source_skin,
    "Aevrynd_UpperVermilion_BodyResponse_R475",
    (0.19, 0.060, 0.050, 1.0),
    0.08,
    0.52,
)
upper.data.materials[2] = tint_skin_material(
    source_skin,
    "Aevrynd_UpperLipInner_BodyResponse_R475",
    (0.040, 0.006, 0.010, 1.0),
    0.68,
    0.44,
)
bpy.data.objects["Lip_Lower"].hide_render = True
bpy.data.objects["Mouth_WetLine"].hide_render = True
lower_response = add_lower_lip_response(body, body_world_points, source_skin)
dynamic_clearance = repair_dynamic_clearance(scene, body, upper)
intersection_repair = repair_intersecting_faces(scene, body, upper)
upper["aevrynd_layer"] = "ANATOMY_UPPER_VERMILION_FITTED"
upper["aevrynd_clearance_m"] = CLEARANCE
body["aevrynd_face_revision"] = "r475-fitted-upper-lip"
scene["aevrynd_character_revision"] = "v249r475"
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

REVIEW_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
views = (
    ("01-face-front-f01", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108, (1100, 1100), 1),
    ("02-mouth-close-f01", (0.0, -0.405, 1.528), (0.0, -0.115, 1.528), 135, (1400, 800), 1),
    ("03-mouth-oblique-f01", (0.235, -0.405, 1.53), (0.0, -0.112, 1.528), 135, (1400, 800), 1),
    ("04-three-quarter-f01", (0.40, -0.57, 1.58), (0.0, -0.030, 1.56), 92, (1000, 1000), 1),
    ("05-face-front-f20", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108, (1100, 1100), 20),
)
for args in views:
    render(scene, camera, *args)
scene.frame_set(1)
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "upperLipFit": fit,
    "transparentTransitionRemoval": transition_removal,
    "dynamicClearanceRepair": dynamic_clearance,
    "intersectionFaceRepair": intersection_repair,
    "lowerLipResponse": lower_response,
    "upperLipVisible": not upper.hide_render,
    "lowerLipShellVisible": not bpy.data.objects["Lip_Lower"].hide_render,
    "wetLineShellVisible": not bpy.data.objects["Mouth_WetLine"].hide_render,
    "reviewDirectory": str(REVIEW_DIR),
    "reviewColorManagement": {"viewTransform": "Standard", "look": "None", "exposure": 0.0},
    "status": "VISUAL_PASS_PENDING_COLLISION_AUDIT",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R475_FITTED_UPPER_LIP=" + json.dumps(report, sort_keys=True))
