"""Test smooth closed boolean cuts through the defective r1033 mouth field."""

import json
import math
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-lower-lip-rim-turn-r1033-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1059-lowpoly-mouth-boolean.study.json"
OUTPUT = ASSETS / "aevrynd-female-cc0-smooth-mouth-cut-r1059-study.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r1059-lowpoly-mouth-boolean"
BODY = "AevryndFemaleCC0Baseline_v259"
CENTER_Z = 1.3862
VARIANTS = (
    ("a-compact", 0.034, 0.008),
    ("b-balanced", 0.038, 0.010),
    ("c-broad", 0.042, 0.012),
)


def mixed_local_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    coordinates = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        relative = block.relative_key
        for index, item in enumerate(block.data):
            coordinates[index] += block.value * (item.co - relative.data[index].co)
    return coordinates


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


def make_cutter(radius_x, radius_z, segments=96):
    vertices = []
    for y in (-0.30, -0.090):
        for index in range(segments):
            theta = 2.0 * math.pi * index / segments
            vertices.append((radius_x * math.cos(theta), y, CENTER_Z + radius_z * math.sin(theta)))
    faces = []
    for index in range(segments):
        following = (index + 1) % segments
        faces.append((index, following, segments + following, segments + index))
    faces.append(tuple(reversed(range(segments))))
    faces.append(tuple(range(segments, segments * 2)))
    mesh = bpy.data.meshes.new("Aevrynd_R1059_Cutter_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    cutter = bpy.data.objects.new("Aevrynd_R1059_Cutter", mesh)
    bpy.context.scene.collection.objects.link(cutter)
    return cutter


def mouth_boundary_loops(body):
    mesh = body.data
    points = [body.matrix_world @ vertex.co for vertex in mesh.vertices]
    boundary = {tuple(sorted(edge.vertices)) for edge in mesh.edges if len(edge.link_loops) == 0} if False else set()
    edge_faces = defaultdict(set)
    for polygon in mesh.polygons:
        ids = list(polygon.vertices)
        for offset, first in enumerate(ids):
            edge_faces[tuple(sorted((first, ids[(offset + 1) % len(ids)])))].add(polygon.index)
    boundary = {edge for edge, users in edge_faces.items() if len(users) == 1}
    vertex_edges = defaultdict(set)
    for edge in boundary:
        for vertex in edge:
            vertex_edges[vertex].add(edge)
    groups = connected(boundary, lambda edge: set().union(*(vertex_edges[v] for v in edge)))
    records = []
    for group in groups:
        vertices = {vertex for edge in group for vertex in edge}
        local = [points[index] for index in vertices]
        bounds = {
            "x": [min(point.x for point in local), max(point.x for point in local)],
            "y": [min(point.y for point in local), max(point.y for point in local)],
            "z": [min(point.z for point in local), max(point.z for point in local)],
        }
        if bounds["x"][0] < 0.0 < bounds["x"][1] and bounds["z"][0] < CENTER_Z < bounds["z"][1] and bounds["x"][1] - bounds["x"][0] < 0.12:
            records.append({
                "edges": len(group),
                "vertices": len(vertices),
                "degreeHistogram": {
                    str(degree): sum(1 for vertex in vertices if len(vertex_edges[vertex]) == degree)
                    for degree in sorted({len(vertex_edges[vertex]) for vertex in vertices})
                },
                "bounds": bounds,
                "vertexIndices": sorted(vertices),
            })
    return records, points


def boundary_curve(name, indices, points):
    if not indices:
        return None
    remaining = set(indices)
    # Angular order is reliable for the diagnostic curve because the cutter is convex.
    order = sorted(remaining, key=lambda index: math.atan2((points[index].z - CENTER_Z) / 0.010, points[index].x / 0.038))
    curve = bpy.data.curves.new(name + "_Curve", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = 0.00032
    curve.bevel_resolution = 3
    spline = curve.splines.new("POLY")
    spline.points.add(len(order))
    for target, index in zip(spline.points, order + [order[0]]):
        target.co = (*points[index], 1.0)
    material = bpy.data.materials.new(name + "_Material")
    material.diffuse_color = (0.02, 0.95, 0.12, 1.0)
    material.use_nodes = True
    bsdf = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.02, 0.95, 0.12, 1.0)
    bsdf.inputs["Emission Color"].default_value = (0.02, 0.95, 0.12, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 0.35
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, label, oblique=False):
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
    return str(path)


OUT.mkdir(parents=True, exist_ok=True)
variants = []
for label, radius_x, radius_z in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    source_body = bpy.data.objects[BODY]
    subdivision = source_body.modifiers.get("Aevrynd CC0 Reference Subdivision")
    if subdivision is not None:
        subdivision.show_viewport = False
        subdivision.show_render = False
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = source_body.evaluated_get(depsgraph)
    evaluated_mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=depsgraph)
    body = bpy.data.objects.new(BODY + "_R1059", evaluated_mesh)
    body.matrix_world = source_body.matrix_world.copy()
    scene.collection.objects.link(body)
    source_body.hide_render = True
    source_body.hide_viewport = True
    bpy.context.view_layer.objects.active = body
    source_body.select_set(False)
    body.select_set(True)
    body.data.update()
    cutter = make_cutter(radius_x, radius_z)
    modifier = body.modifiers.new("Aevrynd_R1059_SmoothMouthCut", "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = cutter
    before = {"vertices": len(body.data.vertices), "edges": len(body.data.edges), "faces": len(body.data.polygons)}
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    after = {"vertices": len(body.data.vertices), "edges": len(body.data.edges), "faces": len(body.data.polygons)}
    bpy.data.objects.remove(cutter, do_unlink=True)
    loops, points = mouth_boundary_loops(body)
    diagnostic = None
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")) and obj != diagnostic:
                obj.hide_render = True
    renders = [render(scene, f"{label}-front"), render(scene, f"{label}-oblique", True)]
    if label == "a-compact":
        body["aevrynd_revision"] = "v249r1059-lowpoly-smooth-mouth-cut"
        body["aevrynd_status"] = "topology-transfer-study-no-shape-keys"
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    variants.append({
        "label": label,
        "radiusM": [radius_x, radius_z],
        "before": before,
        "after": after,
        "mouthBoundaryLoops": loops,
        "renders": renders,
        "status": "BOOLEAN_BOUNDARY_REVIEW_PENDING",
    })

report = {
    "revision": "v249r1059-lowpoly-mouth-boolean",
    "source": str(SOURCE),
    "method": "bake the active 35-key state into a 19k-vertex diagnostic duplicate, remove all modifiers and keys from that duplicate only, then apply the Aevrynd-authored 96-segment elliptical cutter before any deformation transfer",
    "variants": variants,
    "candidateBlendSaved": False,
    "topologyTransferStudyBlend": str(OUTPUT),
    "websitePromotionApproved": False,
    "status": "BOUNDARY_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1059_LOWPOLY_BOOLEAN=" + json.dumps([
    {"label": item["label"], "before": item["before"], "after": item["after"], "loops": [(loop["edges"], loop["degreeHistogram"]) for loop in item["mouthBoundaryLoops"]]}
    for item in variants
], sort_keys=True))
