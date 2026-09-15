"""Cut one contiguous balanced eye aperture per eye into r1001.

Faces are removed only on the camera-facing surface.  Retaining every vertex
keeps all 30 existing shape-key blocks index-compatible for this topology test.
"""

import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-mixed-space-eyelid-relief-r1001.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-contiguous-open-aperture-r1017-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1017-contiguous-open-aperture.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1017-contiguous-open-aperture"
BODY = "AevryndFemaleCC0Baseline_v259"
UPPER_HEIGHT = 0.40
LOWER_DEPTH = 0.26
EXTENT = 0.88


def mixed_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    coordinates = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        for index, coordinate in enumerate(coordinates):
            coordinate += block.value * (block.data[index].co - block.relative_key.data[index].co)
    return [body.matrix_world @ coordinate for coordinate in coordinates]


def object_bounds(names):
    points = []
    for name in names:
        obj = bpy.data.objects[name]
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    minimum = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    maximum = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    return (minimum + maximum) * 0.5, (maximum - minimum) * 0.5


def aperture_bounds(point, center, radius, side):
    u = (point.x - center.x) / radius.x
    if abs(u) >= EXTENT:
        return False
    temple_sign = 1.0 if side == "L" else -1.0
    temporal = u * temple_sign
    arc = math.sqrt(max(0.0, 1.0 - (u / EXTENT) ** 2))
    canthus_z = -0.035 + (temporal + EXTENT) / (2.0 * EXTENT) * 0.145
    upper = canthus_z + UPPER_HEIGHT * arc
    lower = canthus_z - LOWER_DEPTH * arc
    z = (point.z - center.z) / radius.z
    return lower < z < upper


def world_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    result = BVHTree.FromPolygons(points, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return result


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY]
before_vertices = len(body.data.vertices)
before_polygons = len(body.data.polygons)
before_keys = [block.name for block in body.data.shape_keys.key_blocks]
points = mixed_coordinates(body)
frames = {side: object_bounds((f"Eye_{side}_Sclera", f"Eye_{side}_Cornea")) for side in ("L", "R")}

candidate_by_side = {"L": set(), "R": set()}
face_edges = {}
edge_faces = {}
for polygon in body.data.polygons:
    vertices = [points[index] for index in polygon.vertices]
    center = sum(vertices, Vector()) / len(vertices)
    indices = list(polygon.vertices)
    edges = {
        tuple(sorted((indices[index], indices[(index + 1) % len(indices)])))
        for index in range(len(indices))
    }
    face_edges[polygon.index] = edges
    for edge in edges:
        edge_faces.setdefault(edge, set()).add(polygon.index)
    for side in ("L", "R"):
        eye_center, eye_radius = frames[side]
        # Build a generous candidate mask, then keep exactly one connected
        # surface component.  The old normal filter punctured the mask into
        # dozens of islands along the irregular source topology.
        if center.y < -0.108 and aperture_bounds(center, eye_center, eye_radius, side):
            candidate_by_side[side].add(polygon.index)
            break


def connected_face_components(face_indices):
    remaining = set(face_indices)
    components = []
    while remaining:
        seed = remaining.pop()
        stack = [seed]
        component = {seed}
        while stack:
            face_index = stack.pop()
            neighbours = set()
            for edge in face_edges[face_index]:
                neighbours.update(edge_faces[edge])
            fresh = neighbours & remaining
            remaining.difference_update(fresh)
            component.update(fresh)
            stack.extend(fresh)
        components.append(component)
    return sorted(components, key=len, reverse=True)


components_by_side = {
    side: connected_face_components(candidate_by_side[side]) for side in ("L", "R")
}
selected_by_side = {
    side: (components_by_side[side][0] if components_by_side[side] else set())
    for side in ("L", "R")
}
delete_indices = sorted(selected_by_side["L"] | selected_by_side["R"])
delete_by_side = {side: len(selected_by_side[side]) for side in ("L", "R")}


def cut_boundary_components(selected):
    boundary = {
        edge for edge, adjacent in edge_faces.items()
        if bool(adjacent & selected) and bool(adjacent - selected)
    }
    vertex_edges = {}
    for edge in boundary:
        for vertex in edge:
            vertex_edges.setdefault(vertex, set()).add(edge)
    remaining = set(boundary)
    components = []
    while remaining:
        seed = remaining.pop()
        stack = [seed]
        component = {seed}
        while stack:
            edge = stack.pop()
            neighbours = set()
            for vertex in edge:
                neighbours.update(vertex_edges[vertex])
            fresh = neighbours & remaining
            remaining.difference_update(fresh)
            component.update(fresh)
            stack.extend(fresh)
        components.append(component)
    return sorted((len(component) for component in components), reverse=True)


boundary_components = {
    side: cut_boundary_components(selected_by_side[side]) for side in ("L", "R")
}

bpy.context.view_layer.objects.active = body
body.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
bm = bmesh.from_edit_mesh(body.data)
bm.faces.ensure_lookup_table()
faces = [bm.faces[index] for index in delete_indices]
bmesh.ops.delete(bm, geom=faces, context="FACES_ONLY")
bmesh.update_edit_mesh(body.data, loop_triangles=True, destructive=True)
bpy.ops.object.mode_set(mode="OBJECT")
body.data.update()

after_vertices = len(body.data.vertices)
after_polygons = len(body.data.polygons)
after_keys = [block.name for block in body.data.shape_keys.key_blocks]
bpy.context.view_layer.update()
body_tree = world_tree(body)
collision = {}
for side in ("L", "R"):
    collision[side] = {}
    for layer in ("Sclera", "Cornea", "Iris", "UpperLashes", "LowerLashes"):
        name = f"Eye_{side}_{layer}"
        collision[side][layer] = len(body_tree.overlap(world_tree(bpy.data.objects[name])))

hidden = []
for obj in scene.objects:
    is_hair = obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES"
    is_lash = obj.name.endswith(("UpperLashes", "LowerLashes"))
    if (is_hair or is_lash) and not obj.hide_render:
        obj.hide_render = True
        hidden.append(obj.name)

RENDER_DIR.mkdir(parents=True, exist_ok=True)
scene.render.resolution_x = scene.render.resolution_y = 900
camera = scene.camera
camera.data.lens = 105
rendered = []
for name, location, target in (
    ("front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.484)),
    ("three-quarter-left", (0.205, -0.425, 1.490), (0.0, -0.057, 1.482)),
    ("three-quarter-right", (-0.205, -0.425, 1.490), (0.0, -0.057, 1.482)),
    ("profile-left", (0.43, -0.115, 1.490), (0.020, -0.055, 1.482)),
):
    camera.location = location
    look_at(camera, target)
    path = RENDER_DIR / f"{name}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    rendered.append(str(path))
for name in hidden:
    bpy.data.objects[name].hide_render = False

shape_key_pass = before_vertices == after_vertices and before_keys == after_keys
collision_pass = all(count == 0 for values in collision.values() for count in values.values())
scene["aevrynd_mainline_revision"] = "v249r1017-contiguous-open-aperture-study"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "STATIC_TOPOLOGY_STUDY_VISUAL_REVIEW_REQUIRED"
scene["aevrynd_website_promotion"] = "forbidden"
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "guide": "r1014 b-balanced",
    "deletedFaces": len(delete_indices),
    "deletedFacesBySide": delete_by_side,
    "candidateFacesBySide": {side: len(candidate_by_side[side]) for side in ("L", "R")},
    "candidateComponentSizesBySide": {
        side: [len(component) for component in components_by_side[side]] for side in ("L", "R")
    },
    "cutBoundaryComponentEdgeCountsBySide": boundary_components,
    "before": {"vertices": before_vertices, "polygons": before_polygons, "shapeKeys": before_keys},
    "after": {"vertices": after_vertices, "polygons": after_polygons, "shapeKeys": after_keys},
    "gates": {"vertexAndShapeKeyIndexCompatibility": shape_key_pass, "frame1BodyEyeLashCollision": collision_pass},
    "frame1BodyTriangleOverlaps": collision,
    "rendered": rendered,
    "status": "VISUAL_REVIEW_REQUIRED" if shape_key_pass and collision_pass else "REJECTED_TECHNICAL_GATE",
    "websitePromotionApproved": False,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R1017_CONTIGUOUS_OPEN_APERTURE=" + json.dumps({
    "deletedFaces": len(delete_indices), "deletedFacesBySide": delete_by_side,
    "boundaryComponents": boundary_components, "gates": report["gates"],
    "output": str(OUTPUT), "status": report["status"]
}, sort_keys=True))
if not shape_key_pass or not collision_pass:
    raise SystemExit(2)
