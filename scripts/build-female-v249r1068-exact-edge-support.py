"""Bake an exact measured lower-inner support ring and transfer the full deformation contract."""

import json
import math
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-structured-lips-r1061-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-exact-edge-support-r1068-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1068-exact-edge-support.study.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1068-exact-edge-support"
BODY = "AevryndFemaleCC0StructuredLips_R1061"
TARGET = "AevryndFemaleCC0ExactEdgeSupport_R1068"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
CENTER_Z = 1.3862
RADIUS_X = 0.034
RADIUS_Z = 0.008
SUPPORT_WIDTH = 0.00005
EDGE_INSPECTION = ASSETS / "female-v249-mainline-r1063-lower-inner-edge.inspect.json"


def make_cutter(segments=96):
    vertices = []
    for y in (-0.30, -0.090):
        for index in range(segments):
            theta = 2.0 * math.pi * index / segments
            vertices.append((RADIUS_X * math.cos(theta), y, CENTER_Z + RADIUS_Z * math.sin(theta)))
    faces = []
    for index in range(segments):
        following = (index + 1) % segments
        faces.append((index, following, segments + following, segments + index))
    faces.append(tuple(reversed(range(segments))))
    faces.append(tuple(range(segments, 2 * segments)))
    mesh = bpy.data.meshes.new("Aevrynd_R1060_Cutter_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    cutter = bpy.data.objects.new("Aevrynd_R1060_Cutter", mesh)
    bpy.context.scene.collection.objects.link(cutter)
    return cutter


def barycentric(point, first, second, third):
    v0 = second - first
    v1 = third - first
    v2 = point - first
    d00 = v0.dot(v0)
    d01 = v0.dot(v1)
    d11 = v1.dot(v1)
    d20 = v2.dot(v0)
    d21 = v2.dot(v1)
    denominator = d00 * d11 - d01 * d01
    if abs(denominator) < 1e-16:
        return (1.0, 0.0, 0.0)
    second_weight = (d11 * d20 - d01 * d21) / denominator
    third_weight = (d00 * d21 - d01 * d20) / denominator
    first_weight = 1.0 - second_weight - third_weight
    weights = [max(0.0, min(1.0, value)) for value in (first_weight, second_weight, third_weight)]
    total = sum(weights) or 1.0
    return tuple(value / total for value in weights)


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(fraction * len(ordered)))] if ordered else 0.0


def build_basis_target(source):
    key_blocks = source.data.shape_keys.key_blocks
    stored_values = {block.name: block.value for block in key_blocks}
    for block in key_blocks:
        block.value = 0.0
    subdivision = source.modifiers.get("Aevrynd CC0 Reference Subdivision")
    armature = source.modifiers.get("Aevrynd R647 Retargeted Armature")
    stored_modifier_state = {}
    for modifier in (subdivision, armature):
        if modifier is not None:
            stored_modifier_state[modifier.name] = (modifier.show_viewport, modifier.show_render)
            modifier.show_viewport = False
            modifier.show_render = False
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = source.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=depsgraph)
    target = bpy.data.objects.new(TARGET, mesh)
    target.matrix_world = source.matrix_world.copy()
    bpy.context.scene.collection.objects.link(target)
    for block in key_blocks:
        block.value = stored_values[block.name]
    for modifier in (subdivision, armature):
        if modifier is not None:
            modifier.show_viewport, modifier.show_render = stored_modifier_state[modifier.name]
    inspection = json.loads(EDGE_INSPECTION.read_text(encoding="utf-8"))
    edge_indices = {
        item["edge"] for item in inspection["candidates"]
        if item["dihedralDegrees"] >= 30.0
        and item["center"][1] < -0.120
        and 1.383 < item["center"][2] < 1.3895
        and min(item["lipWeights"]) >= 0.24
    }
    bm = bmesh.new()
    bm.from_mesh(target.data)
    bm.edges.ensure_lookup_table()
    selected_edges = [bm.edges[index] for index in sorted(edge_indices)]
    result = bmesh.ops.bevel(
        bm,
        geom=selected_edges,
        offset=SUPPORT_WIDTH,
        offset_type="OFFSET",
        segments=2,
        profile=0.5,
        affect="EDGES",
        clamp_overlap=True,
    )
    bm.to_mesh(target.data)
    bm.free()
    target.data.update()
    target["aevrynd_exact_support_edges"] = len(selected_edges)
    target["aevrynd_exact_support_width_mm"] = SUPPORT_WIDTH * 1000.0
    target["aevrynd_exact_support_created_faces"] = len(result.get("faces", []))
    return target


def transfer_contract(source, target):
    source_mesh = source.data
    target_mesh = target.data
    source_mesh.calc_loop_triangles()
    triangles = [tuple(triangle.vertices) for triangle in source_mesh.loop_triangles]
    basis = source_mesh.shape_keys.key_blocks[0]
    basis_points = [item.co.copy() for item in basis.data]
    tree = BVHTree.FromPolygons(basis_points, triangles)
    mappings = []
    distances = []
    for vertex in target_mesh.vertices:
        location, _normal, triangle_index, distance = tree.find_nearest(vertex.co)
        if triangle_index is None:
            raise RuntimeError(f"No source triangle for target vertex {vertex.index}")
        triangle = triangles[triangle_index]
        weights = barycentric(location, *(basis_points[index] for index in triangle))
        mappings.append((triangle, weights))
        distances.append(distance)

    source_groups = {
        vertex.index: {membership.group: membership.weight for membership in vertex.groups}
        for vertex in source_mesh.vertices
    }
    for source_group in source.vertex_groups:
        target.vertex_groups.new(name=source_group.name)
    assigned_weights = 0
    minimum_group_count = None
    for target_index, (triangle, weights) in enumerate(mappings):
        combined = {}
        for source_index, influence in zip(triangle, weights):
            for group, weight in source_groups[source_index].items():
                combined[group] = combined.get(group, 0.0) + influence * weight
        total = sum(combined.values())
        if total > 1e-12:
            combined = {group: weight / total for group, weight in combined.items() if weight > 1e-7}
        for group, weight in combined.items():
            target.vertex_groups[group].add([target_index], weight, "REPLACE")
            assigned_weights += 1
        count = len(combined)
        minimum_group_count = count if minimum_group_count is None else min(minimum_group_count, count)

    target_basis = target.shape_key_add(name=basis.name, from_mix=False)
    source_blocks = list(source_mesh.shape_keys.key_blocks)
    created = {basis.name: target_basis}
    target_basis_coords = [vertex.co.copy() for vertex in target_mesh.vertices]
    for source_block in source_blocks[1:]:
        target_block = target.shape_key_add(name=source_block.name, from_mix=False)
        created[source_block.name] = target_block
        for target_index, (triangle, weights) in enumerate(mappings):
            delta = Vector()
            for source_index, influence in zip(triangle, weights):
                delta += influence * (source_block.data[source_index].co - basis.data[source_index].co)
            target_block.data[target_index].co = target_basis_coords[target_index] + delta
        target_block.value = source_block.value
        target_block.slider_min = source_block.slider_min
        target_block.slider_max = source_block.slider_max
        target_block.mute = source_block.mute
        target_block.vertex_group = source_block.vertex_group
        target_block.interpolation = source_block.interpolation
    for source_block in source_blocks[1:]:
        created[source_block.name].relative_key = created[source_block.relative_key.name]

    source_subdivision = source.modifiers.get("Aevrynd CC0 Reference Subdivision")
    if source_subdivision is not None:
        subdivision = target.modifiers.new(source_subdivision.name, "SUBSURF")
        subdivision.subdivision_type = source_subdivision.subdivision_type
        subdivision.levels = source_subdivision.levels
        subdivision.render_levels = source_subdivision.render_levels
        subdivision.show_viewport = source_subdivision.show_viewport
        subdivision.show_render = source_subdivision.show_render
    source_armature = source.modifiers.get("Aevrynd R647 Retargeted Armature")
    if source_armature is not None:
        armature = target.modifiers.new(source_armature.name, "ARMATURE")
        armature.object = source_armature.object
        armature.use_deform_preserve_volume = source_armature.use_deform_preserve_volume
        armature.use_vertex_groups = source_armature.use_vertex_groups
        armature.use_bone_envelopes = source_armature.use_bone_envelopes
    target.parent = source.parent
    target.parent_type = source.parent_type
    target.parent_bone = source.parent_bone
    target.matrix_parent_inverse = source.matrix_parent_inverse.copy()
    target["aevrynd_revision"] = "v249r1068-exact-edge-support"
    target["aevrynd_source"] = SOURCE.name
    return {
        "sourceShapeKeys": len(source_blocks),
        "targetShapeKeys": len(target.data.shape_keys.key_blocks),
        "shapeKeyNamesMatch": [block.name for block in source_blocks] == [block.name for block in target.data.shape_keys.key_blocks],
        "targetVertices": len(target_mesh.vertices),
        "targetFaces": len(target_mesh.polygons),
        "mappingDistanceMm": {
            "median": percentile(distances, 0.50) * 1000.0,
            "p95": percentile(distances, 0.95) * 1000.0,
            "maximum": max(distances) * 1000.0,
        },
        "assignedWeights": assigned_weights,
        "minimumVertexGroupCount": minimum_group_count,
    }


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, target, label, expression=None, oblique=False):
    keys = target.data.shape_keys.key_blocks
    keys[OPEN_KEY].value = 1.0 if expression == "open" else 0.0
    keys[SMILE_KEY].value = 1.0 if expression == "smile" else 0.0
    camera = scene.camera
    camera.data.lens = 135
    camera.location = ((-0.105 if oblique else 0.0), -0.43, 1.391)
    look_at(camera, (0.0, -0.115, 1.386))
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    keys[OPEN_KEY].value = 0.0
    keys[SMILE_KEY].value = 0.0
    return str(path)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
source = bpy.data.objects[BODY]
target = build_basis_target(source)
transfer = transfer_contract(source, target)
source.hide_render = True
source.hide_viewport = True
for obj in scene.objects:
    name = obj.name.lower()
    if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
        if not any(token in name for token in ("brow", "lash")):
            obj.hide_render = True
OUT.mkdir(parents=True, exist_ok=True)
renders = [
    render(scene, target, "neutral-front"),
    render(scene, target, "neutral-oblique", oblique=True),
    render(scene, target, "mouth-open", "open"),
    render(scene, target, "smile", "smile"),
]
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "revision": "v249r1068-exact-edge-support",
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "exact 76-edge two-segment low-density support bevel at 0.05 mm followed by nearest-source-triangle barycentric transfer of all 35 shape-key deltas and normalized deform weights; restore subdivision and Armature",
    "transfer": transfer,
    "renders": renders,
    "candidateStatus": "VISUAL_AND_COLLISION_REVIEW_PENDING",
    "websitePromotionApproved": False,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1068_SUPPORT=" + json.dumps(transfer, sort_keys=True))

