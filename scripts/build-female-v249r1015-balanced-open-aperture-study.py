"""Cut a balanced true eye aperture into r1001 without deleting vertices.

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
OUTPUT = ASSETS / "aevrynd-female-cc0-balanced-open-aperture-r1015-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1015-balanced-open-aperture.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1015-balanced-open-aperture"
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

delete_indices = []
delete_by_side = {"L": 0, "R": 0}
for polygon in body.data.polygons:
    vertices = [points[index] for index in polygon.vertices]
    center = sum(vertices, Vector()) / len(vertices)
    edge_a = vertices[1] - vertices[0]
    edge_b = vertices[2] - vertices[0]
    normal = edge_a.cross(edge_b).normalized()
    for side in ("L", "R"):
        eye_center, eye_radius = frames[side]
        # Only remove the outer face.  The existing rear socket stays intact
        # during this first aperture-density test.
        if center.y < -0.108 and normal.y < -0.12 and aperture_bounds(center, eye_center, eye_radius, side):
            delete_indices.append(polygon.index)
            delete_by_side[side] += 1
            break

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
scene["aevrynd_mainline_revision"] = "v249r1015-balanced-open-aperture-study"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "STATIC_TOPOLOGY_STUDY_VISUAL_REVIEW_REQUIRED"
scene["aevrynd_website_promotion"] = "forbidden"
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "guide": "r1014 b-balanced",
    "deletedFaces": len(delete_indices),
    "deletedFacesBySide": delete_by_side,
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
print("AEVRYND_R1015_BALANCED_OPEN_APERTURE=" + json.dumps({
    "deletedFaces": len(delete_indices), "deletedFacesBySide": delete_by_side,
    "gates": report["gates"], "output": str(OUTPUT), "status": report["status"]
}, sort_keys=True))
if not shape_key_pass or not collision_pass:
    raise SystemExit(2)
