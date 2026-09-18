"""Classify and false-colour the r1068 baked support faces that remain visible."""
import json
from collections import Counter
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-exact-edge-support-r1068-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1070-visible-support-faces.inspect.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1070-visible-support-faces"
BODY = "AevryndFemaleCC0ExactEdgeSupport_R1068"
ORIGINAL_VERTEX_COUNT = 13583
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def hide_hair(scene):
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")):
                obj.hide_render = True


def active_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    coords = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.name in (OPEN_KEY, SMILE_KEY) or block.mute or abs(block.value) < 1e-8:
            continue
        for index, item in enumerate(block.data):
            coords[index] += block.value * (item.co - block.relative_key.data[index].co)
    return coords


def polygon_geometry(body, polygon, coords):
    world = [body.matrix_world @ coords[index] for index in polygon.vertices]
    center = sum(world, Vector()) / len(world)
    normal = Vector()
    for index in range(1, len(world) - 1):
        normal += (world[index] - world[0]).cross(world[index + 1] - world[0])
    if normal.length_squared:
        normal.normalize()
    return center, normal


def diagnostic_material(name, colour):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*colour, 1.0)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (*colour, 1.0)
    emission.inputs["Strength"].default_value = 2.5
    material.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return material


def render(scene, label, oblique=False, opened=False):
    body = bpy.data.objects[BODY]
    keys = body.data.shape_keys.key_blocks
    keys[OPEN_KEY].value = 1.0 if opened else 0.0
    keys[SMILE_KEY].value = 0.0
    camera = scene.camera
    camera.data.lens = 135
    camera.location = ((-0.105 if oblique else 0.0), -0.43, 1.391)
    look_at(camera, (0.0, -0.115, 1.386))
    scene.render.resolution_x, scene.render.resolution_y = 1100, 720
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
hide_hair(scene)
OUT.mkdir(parents=True, exist_ok=True)
coords = active_coordinates(body)
new_vertices = set(range(ORIGINAL_VERTEX_COUNT, len(body.data.vertices)))
camera_location = Vector((0.0, -0.43, 1.391))
records = []
for polygon in body.data.polygons:
    new_count = sum(index in new_vertices for index in polygon.vertices)
    if not new_count:
        continue
    center, normal = polygon_geometry(body, polygon, coords)
    to_camera = (camera_location - center).normalized()
    records.append({
        "face": polygon.index,
        "newVertexCount": new_count,
        "vertexCount": len(polygon.vertices),
        "center": [center.x, center.y, center.z],
        "normal": [normal.x, normal.y, normal.z],
        "cameraFacing": normal.dot(to_camera),
        "material": polygon.material_index,
    })

support_face_indices = {item["face"] for item in records}
support_vertices = {index for face_index in support_face_indices for index in body.data.polygons[face_index].vertices}
adjacent_records = []
for polygon in body.data.polygons:
    if polygon.index in support_face_indices or not any(index in support_vertices for index in polygon.vertices):
        continue
    center, normal = polygon_geometry(body, polygon, coords)
    to_camera = (camera_location - center).normalized()
    shared = sum(index in support_vertices for index in polygon.vertices)
    adjacent_records.append({
        "face": polygon.index,
        "sharedSupportVertexCount": shared,
        "vertexCount": len(polygon.vertices),
        "center": [center.x, center.y, center.z],
        "normal": [normal.x, normal.y, normal.z],
        "cameraFacing": normal.dot(to_camera),
        "material": polygon.material_index,
    })

# Preserve original assignments so each diagnostic render is independent.
original_materials = [polygon.material_index for polygon in body.data.polygons]
original_material_slot_count = len(body.data.materials)
palette = (
    (1.0, 0.02, 0.02),
    (0.02, 1.0, 0.04),
    (0.02, 0.2, 1.0),
    (1.0, 0.02, 0.8),
    (1.0, 0.55, 0.02),
    (0.02, 1.0, 1.0),
)
counts = sorted({item["newVertexCount"] for item in records})
colours = {count: palette[index % len(palette)] for index, count in enumerate(counts)}
slots = {}
for count, colour in colours.items():
    slots[count] = len(body.data.materials)
    body.data.materials.append(diagnostic_material(f"R1070_NewVertexCount_{count}", colour))


def restore():
    for polygon, material_index in zip(body.data.polygons, original_materials):
        polygon.material_index = material_index


def assign(predicate, by_count=False):
    restore()
    selected = []
    by_face = {item["face"]: item for item in records}
    for face_index, item in by_face.items():
        if predicate(item):
            body.data.polygons[face_index].material_index = slots[item["newVertexCount"] if by_count else 1]
            selected.append(face_index)
    body.data.update()
    return selected


renders = []
assign(lambda item: True, by_count=True)
renders += [render(scene, "all-support-classified-front"), render(scene, "all-support-classified-oblique", oblique=True)]
fully_new = assign(lambda item: item["newVertexCount"] == item["vertexCount"])
renders += [render(scene, "fully-new-only-front"), render(scene, "fully-new-only-open", opened=True)]
camera_facing = assign(lambda item: item["cameraFacing"] > 0.15)
renders += [render(scene, "camera-facing-only-front"), render(scene, "camera-facing-only-oblique", oblique=True), render(scene, "camera-facing-only-open", opened=True)]
restore()

def camera_ray(camera, scene, pixel_x, pixel_y, width, height):
    frame = camera.data.view_frame(scene=scene)
    left = sorted((point for point in frame if point.x < 0), key=lambda point: point.y)
    right = sorted((point for point in frame if point.x >= 0), key=lambda point: point.y)
    lower_left, upper_left = left[0], left[-1]
    lower_right, upper_right = right[0], right[-1]
    u = (pixel_x + 0.5) / width
    v = 1.0 - (pixel_y + 0.5) / height
    lower = lower_left.lerp(lower_right, u)
    upper = upper_left.lerp(upper_right, u)
    point_camera = lower.lerp(upper, v)
    origin = camera.matrix_world.translation
    point_world = camera.matrix_world @ point_camera
    return origin, (point_world - origin).normalized()


keys = body.data.shape_keys.key_blocks
keys[OPEN_KEY].value = keys[SMILE_KEY].value = 0.0
scene.camera.location = (0.0, -0.43, 1.391)
look_at(scene.camera, (0.0, -0.115, 1.386))
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
world_coords = [body.matrix_world @ coordinate for coordinate in coords]
base_bvh = BVHTree.FromPolygons(world_coords, [list(polygon.vertices) for polygon in body.data.polygons], all_triangles=False)
pixel_rays = []
grid_pixels = [(pixel_x, pixel_y) for pixel_y in (344, 348, 352, 356, 360) for pixel_x in (300, 400, 500, 550, 600, 700, 800)]
bright_line_pixels = [(280, 357), (300, 356), (320, 351), (460, 346), (480, 349), (500, 351), (520, 353), (540, 354), (560, 354), (580, 353), (600, 351), (620, 349), (640, 346), (760, 348), (780, 351), (800, 356), (820, 358)]
for pixel_x, pixel_y in grid_pixels + bright_line_pixels:
        origin, direction = camera_ray(scene.camera, scene, pixel_x, pixel_y, 1100, 720)
        hit, location, normal, face_index, hit_object, _ = scene.ray_cast(depsgraph, origin, direction)
        record = {"pixel": [pixel_x, pixel_y], "sampleKind": "brightLine" if (pixel_x, pixel_y) in bright_line_pixels else "grid", "hit": bool(hit)}
        if hit:
            evaluated = hit_object.evaluated_get(depsgraph)
            material_index = evaluated.data.polygons[face_index].material_index if face_index < len(evaluated.data.polygons) else None
            material_name = None
            if material_index is not None and material_index < len(hit_object.material_slots):
                slot = hit_object.material_slots[material_index]
                material_name = slot.material.name if slot.material else None
            record.update({
                "object": hit_object.name,
                "evaluatedFace": face_index,
                "materialIndex": material_index,
                "material": material_name,
                "location": [location.x, location.y, location.z],
                "normal": [normal.x, normal.y, normal.z],
            })
            nearest_location, nearest_normal, nearest_face, nearest_distance = base_bvh.find_nearest(location)
            if nearest_face is not None:
                nearest_polygon = body.data.polygons[nearest_face]
                record.update({
                    "nearestBaseFace": nearest_face,
                    "nearestBaseDistanceMm": nearest_distance * 1000.0,
                    "nearestBaseNewVertexCount": sum(index in new_vertices for index in nearest_polygon.vertices),
                    "nearestBaseIsSupport": nearest_face in support_face_indices,
                    "nearestBaseIsAdjacent": any(item["face"] == nearest_face for item in adjacent_records),
                    "nearestBaseMaterial": nearest_polygon.material_index,
                })
        pixel_rays.append(record)

def assign_adjacent(predicate):
    restore()
    selected = []
    for item in adjacent_records:
        if predicate(item):
            body.data.polygons[item["face"]].material_index = slots[1]
            selected.append(item["face"])
    body.data.update()
    return selected


adjacent_all = assign_adjacent(lambda item: True)
renders += [render(scene, "adjacent-old-all-front"), render(scene, "adjacent-old-all-oblique", oblique=True)]
adjacent_facing = assign_adjacent(lambda item: item["cameraFacing"] > 0.15)
renders += [render(scene, "adjacent-old-facing-front"), render(scene, "adjacent-old-facing-open", opened=True)]
adjacent_lower = assign_adjacent(lambda item: item["cameraFacing"] > 0.15 and item["center"][2] < 1.386)
renders += [render(scene, "adjacent-old-facing-lower-front"), render(scene, "adjacent-old-facing-lower-open", opened=True)]
restore()

mouth_material_records = []
for polygon in body.data.polygons:
    if polygon.material_index == 0:
        continue
    center, normal = polygon_geometry(body, polygon, coords)
    if abs(center.x) > 0.04 or not (1.37 < center.z < 1.40):
        continue
    to_camera = (camera_location - center).normalized()
    mouth_material_records.append({
        "face": polygon.index,
        "material": polygon.material_index,
        "center": [center.x, center.y, center.z],
        "normal": [normal.x, normal.y, normal.z],
        "cameraFacing": normal.dot(to_camera),
    })

def assign_material_faces(material_index):
    restore()
    selected = []
    for item in mouth_material_records:
        if item["material"] == material_index:
            body.data.polygons[item["face"]].material_index = slots[1]
            selected.append(item["face"])
    body.data.update()
    return selected


material_face_counts = {}
for material_index in range(1, original_material_slot_count):
    selected = assign_material_faces(material_index)
    material_face_counts[str(material_index)] = len(selected)
    if selected:
        renders += [render(scene, f"mouth-material-{material_index}-front"), render(scene, f"mouth-material-{material_index}-open", opened=True)]
restore()

facing_sorted = sorted(records, key=lambda item: item["cameraFacing"], reverse=True)
report = {
    "revision": "v249r1070-visible-support-faces",
    "source": str(SOURCE),
    "body": BODY,
    "supportFaceCount": len(records),
    "newVertexCountHistogram": dict(sorted(Counter(item["newVertexCount"] for item in records).items())),
    "fullyNewFaceCount": len(fully_new),
    "cameraFacingThreshold": 0.15,
    "cameraFacingFaceCount": len(camera_facing),
    "cameraFacingRange": [min(item["cameraFacing"] for item in records), max(item["cameraFacing"] for item in records)],
    "adjacentOldFaceCount": len(adjacent_records),
    "adjacentOldFacingFaceCount": len(adjacent_facing),
    "adjacentOldFacingLowerFaceCount": len(adjacent_lower),
    "adjacentOldFaces": adjacent_records,
    "bodyMaterialSlots": [slot.material.name if slot.material else None for slot in body.material_slots],
    "mouthNonSkinMaterialFaceCounts": material_face_counts,
    "mouthNonSkinMaterialFaces": mouth_material_records,
    "whiteLinePixelRays": pixel_rays,
    "topCameraFacingFaces": facing_sorted[:40],
    "allFaces": records,
    "renders": renders,
    "findingStatus": "FALSE_COLOUR_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1070_VISIBLE_SUPPORT=" + json.dumps({key: report[key] for key in ("supportFaceCount", "newVertexCountHistogram", "fullyNewFaceCount", "cameraFacingFaceCount", "cameraFacingRange")}, sort_keys=True))
