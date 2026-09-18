"""Add restrained weighted inner walls behind the current 45-edge eye apertures."""
import json
from collections import defaultdict
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-commissure-curvature-r1076-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-eyelid-inner-wall-r1078-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1078-eyelid-inner-wall-sweep.study.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1078-eyelid-inner-wall"
BODY = "AevryndFemaleCC0CommissureCurvature_R1076"
TARGET = "AevryndFemaleCC0EyelidInnerWall_R1078"
FRAMES = (1, 20, 33, 61)
# label, first depth, total depth, first radial shrink, total radial shrink, rings
VARIANTS = (
    ("a-control", 0.0, 0.0, 0.0, 0.0, 0),
    ("b-one-ring-forward-0.12", -0.00012, -0.00012, 0.002, 0.002, 1),
    ("c-two-ring-forward-0.22", -0.00010, -0.00022, 0.002, 0.005, 2),
    ("d-two-ring-forward-0.32", -0.00016, -0.00032, 0.003, 0.008, 2),
)
SELECTED = "c-two-ring-forward-0.22"


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


def eye_frames():
    depsgraph = bpy.context.evaluated_depsgraph_get()
    result = {}
    for side in ("L", "R"):
        points = []
        for name in (f"Eye_{side}_Sclera", f"Eye_{side}_Cornea"):
            obj = bpy.data.objects[name].evaluated_get(depsgraph)
            mesh = obj.to_mesh()
            points.extend(obj.matrix_world @ vertex.co for vertex in mesh.vertices)
            obj.to_mesh_clear()
        minimum = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
        maximum = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
        result[side] = ((minimum + maximum) * 0.5, (maximum - minimum) * 0.5)
    return result


def aperture_edges(body, frames):
    points = active_coordinates(body)
    users = defaultdict(int)
    for polygon in body.data.polygons:
        vertices = list(polygon.vertices)
        for index, first in enumerate(vertices):
            users[tuple(sorted((first, vertices[(index + 1) % len(vertices)])))] += 1
    selected = {"L": [], "R": []}
    for edge in body.data.edges:
        key = tuple(sorted(edge.vertices))
        if users[key] != 1:
            continue
        midpoint = (points[edge.vertices[0]] + points[edge.vertices[1]]) * 0.5
        for side, (center, radius) in frames.items():
            if abs(midpoint.x - center.x) < radius.x * 1.15 and abs(midpoint.z - center.z) < radius.z * 0.60 and midpoint.y < -0.110:
                selected[side].append(edge.index)
                break
    return selected


def extrude_walls(body, frames, edge_indices, first_depth, total_depth, first_shrink, total_shrink, ring_count):
    before_vertices, before_faces = len(body.data.vertices), len(body.data.polygons)
    before_keys = [block.name for block in body.data.shape_keys.key_blocks]
    if ring_count == 0:
        return {"beforeVertices": before_vertices, "afterVertices": before_vertices, "addedVertices": 0, "beforeFaces": before_faces, "afterFaces": before_faces, "addedFaces": 0, "newVerticesWithWeights": 0, "newVertexMinimumWeightGroupCount": 0, "shapeKeyCompatibility": True, "ringVertices": []}
    inverse = body.matrix_world.inverted()
    centers = {side: inverse @ center for side, (center, _radius) in frames.items()}
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    body.active_shape_key_index = 0
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(body.data)
    bm.edges.ensure_lookup_table()
    deform = bm.verts.layers.deform.verify()
    source_edges = [bm.edges[index] for side in ("L", "R") for index in edge_indices[side]]
    source_vertices = {vertex for edge in source_edges for vertex in edge.verts}
    result1 = bmesh.ops.extrude_edge_only(bm, edges=source_edges)
    ring1 = [item for item in result1["geom"] if isinstance(item, bmesh.types.BMVert)]
    new_faces = [item for item in result1["geom"] if isinstance(item, bmesh.types.BMFace)]
    for face in new_faces:
        face.material_index = 0
    for vertex in ring1:
        source = min(source_vertices, key=lambda item: (item.co - vertex.co).length_squared)
        for group, weight in source[deform].items():
            vertex[deform][group] = weight
        side = "L" if source.co.x >= 0.0 else "R"
        center = centers[side]
        vertex.co.x = center.x + (vertex.co.x - center.x) * (1.0 - first_shrink)
        vertex.co.z = center.z + (vertex.co.z - center.z) * (1.0 - first_shrink)
        vertex.co += inverse.to_3x3() @ Vector((0.0, first_depth, 0.0))
    rings = [ring1]
    if ring_count == 2:
        ring1_set = set(ring1)
        ring1_edges = [item for item in result1["geom"] if isinstance(item, bmesh.types.BMEdge) and all(vertex in ring1_set for vertex in item.verts) and len(item.link_faces) == 1]
        result2 = bmesh.ops.extrude_edge_only(bm, edges=ring1_edges)
        ring2 = [item for item in result2["geom"] if isinstance(item, bmesh.types.BMVert)]
        for face in [item for item in result2["geom"] if isinstance(item, bmesh.types.BMFace)]:
            face.material_index = 0
        extra_shrink = 1.0 - (1.0 - total_shrink) / (1.0 - first_shrink)
        for vertex in ring2:
            source = min(ring1, key=lambda item: (item.co - vertex.co).length_squared)
            for group, weight in source[deform].items():
                vertex[deform][group] = weight
            side = "L" if source.co.x >= 0.0 else "R"
            center = centers[side]
            vertex.co.x = center.x + (vertex.co.x - center.x) * (1.0 - extra_shrink)
            vertex.co.z = center.z + (vertex.co.z - center.z) * (1.0 - extra_shrink)
            vertex.co += inverse.to_3x3() @ Vector((0.0, total_depth - first_depth, 0.0))
        rings.append(ring2)
    bmesh.update_edit_mesh(body.data, loop_triangles=True, destructive=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    body.data.update()
    after_vertices, after_faces = len(body.data.vertices), len(body.data.polygons)
    weights = [len(body.data.vertices[index].groups) for index in range(before_vertices, after_vertices)]
    key_lengths = {block.name: len(block.data) for block in body.data.shape_keys.key_blocks}
    return {
        "beforeVertices": before_vertices, "afterVertices": after_vertices, "addedVertices": after_vertices - before_vertices,
        "beforeFaces": before_faces, "afterFaces": after_faces, "addedFaces": after_faces - before_faces,
        "newVerticesWithWeights": sum(value > 0 for value in weights),
        "newVertexMinimumWeightGroupCount": min(weights) if weights else 0,
        "shapeKeyCompatibility": before_keys == list(key_lengths) and all(length == after_vertices for length in key_lengths.values()),
        "ringVertices": [len(ring) for ring in rings],
    }


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles()
    triangles = [tuple(triangle.vertices) for triangle in mesh.loop_triangles]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, triangles, all_triangles=True)


def collision_frames(body):
    results, failures = {}, []
    scene = bpy.context.scene
    for frame in FRAMES:
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        body_tree = world_tree(body, depsgraph)
        frame_result = {}
        for side in ("L", "R"):
            values = {}
            for layer in ("Sclera", "Cornea", "Iris", "UpperLashes", "LowerLashes"):
                count = len(body_tree.overlap(world_tree(bpy.data.objects[f"Eye_{side}_{layer}"], depsgraph)))
                values[layer] = count
                if count:
                    failures.append({"frame": frame, "side": side, "layer": layer, "triangleOverlapCount": count})
            frame_result[side] = values
        results[str(frame)] = frame_result
    return results, failures


def render(scene, label, view):
    camera = scene.camera
    if view == "eye-front":
        camera.location, target, camera.data.lens, size = (0.0, -0.405, 1.449), (0.0, -0.105, 1.449), 135, (1400, 760)
    elif view == "eye-oblique":
        camera.location, target, camera.data.lens, size = (0.235, -0.405, 1.451), (0.0, -0.105, 1.449), 135, (1400, 760)
    elif view == "face-front":
        camera.location, target, camera.data.lens, size = (0.0, -0.72, 1.445), (0.0, -0.025, 1.440), 88, (1000, 1000)
    else:
        camera.location, target, camera.data.lens, size = (0.45, -0.62, 1.460), (0.0, -0.015, 1.440), 88, (1000, 1000)
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}-{view}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


OUT.mkdir(parents=True, exist_ok=True)
variants = []
for label, first_depth, total_depth, first_shrink, total_shrink, ring_count in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    body = bpy.data.objects[BODY]
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")):
                obj.hide_render = True
    frames = eye_frames()
    edges = aperture_edges(body, frames)
    patch = extrude_walls(body, frames, edges, first_depth, total_depth, first_shrink, total_shrink, ring_count)
    bpy.context.view_layer.update()
    collisions, failures = collision_frames(body)
    scene.frame_set(1)
    bpy.context.view_layer.update()
    renders = [render(scene, label, view) for view in ("eye-front", "eye-oblique", "face-front", "face-three-quarter")]
    technical = len(edges["L"]) == len(edges["R"]) == 45 and patch["shapeKeyCompatibility"] and (ring_count == 0 or patch["newVerticesWithWeights"] == patch["addedVertices"]) and not failures
    variants.append({
        "label": label, "firstDepthMm": first_depth * 1000.0, "totalDepthMm": total_depth * 1000.0,
        "firstRadialShrink": first_shrink, "totalRadialShrink": total_shrink, "ringCount": ring_count,
        "apertureEdges": {side: len(values) for side, values in edges.items()},
        "patch": patch, "collisionFrames": collisions, "collisionFailures": failures,
        "renders": renders, "status": "TECHNICAL_PASS" if technical else "TECHNICAL_FAIL",
    })
    if label == SELECTED:
        body.name = TARGET
        body["aevrynd_revision"] = "v249r1078-eyelid-inner-wall"
        body["aevrynd_source"] = SOURCE.name
        body["aevrynd_inner_wall_depth_mm"] = total_depth * 1000.0
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "revision": "v249r1078-eyelid-inner-wall-sweep", "source": str(SOURCE), "output": str(OUTPUT),
    "method": "preserve the current 45-edge aperture silhouette and extrude one or two weighted skin-material support rings toward the orbital interior",
    "variants": variants, "selectedVariant": SELECTED,
    "websitePromotionApproved": False, "candidateStatus": "VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1078_INNER_WALL=" + json.dumps({"selected": SELECTED, "variants": [{"label": item["label"], "patch": item["patch"], "failures": len(item["collisionFailures"]), "status": item["status"]} for item in variants]}, sort_keys=True))
