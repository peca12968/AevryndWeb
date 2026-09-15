"""Remove measured inherited mouth folds and test a bounded rear vestibule wall."""

import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-local-inner-lip-r1044-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-depth-cleanup-r1046-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1046-depth-cleanup-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "v249r1046-depth-cleanup-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
BACK = "Aevrynd_OralBackWall_R1044"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
CENTER_Z = 1.3862
VARIANTS = (
    ("a-compact", 0.018, 0.0025, -0.116, -0.123),
    ("b-balanced", 0.020, 0.0032, -0.116, -0.123),
    ("c-wide", 0.022, 0.0038, -0.116, -0.123),
    ("d-full-depth", 0.020, 0.0032, -0.116, -0.125),
)


def mixed_coordinates(obj):
    blocks = obj.data.shape_keys.key_blocks
    result = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-9:
            continue
        relative = block.relative_key
        for index, coordinate in enumerate(result):
            coordinate += block.value * (block.data[index].co - relative.data[index].co)
    return result


def measured_internal_faces(body, front_cutoff):
    points = mixed_coordinates(body)
    polygons = [tuple(polygon.vertices) for polygon in body.data.polygons]
    tree = BVHTree.FromPolygons(points, polygons, all_triangles=False)
    hits = set()
    for x_step in range(-36, 37, 2):
        x = x_step * 0.0005
        for z_step in range(-3, 4):
            origin = Vector((x, -0.40, CENTER_Z + z_step * 0.0002))
            for _ in range(32):
                location, _normal, polygon_index, _distance = tree.ray_cast(origin, Vector((0.0, 1.0, 0.0)), 0.60)
                if polygon_index is None:
                    break
                polygon = body.data.polygons[polygon_index]
                center = sum((points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
                if polygon.material_index == 0 and front_cutoff < center.y < -0.025:
                    hits.add(polygon_index)
                origin = location + Vector((0.0, 0.00005, 0.0))
    return hits


def delete_faces(body, indices):
    mesh = body.data
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[index] for index in sorted(indices)], context="FACES_ONLY")
    bmesh.update_edit_mesh(mesh, loop_triangles=True, destructive=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    mesh.update()


def replace_back_wall(radius_x, radius_z, y):
    old = bpy.data.objects.get(BACK)
    if old is None:
        raise RuntimeError("r1044 back wall missing")
    material = old.data.materials[0]
    parent, parent_type, parent_bone = old.parent, old.parent_type, old.parent_bone
    bpy.data.objects.remove(old, do_unlink=True)
    mesh = bpy.data.meshes.new("Aevrynd_OralBackWall_R1046_Mesh")
    vertices = [(0.0, y, CENTER_Z)]
    segments = 64
    for index in range(segments):
        angle = 2.0 * math.pi * index / segments
        vertices.append((radius_x * math.sin(angle), y, CENTER_Z + radius_z * math.cos(angle)))
    mesh.from_pydata(vertices, [], [(0, 1 + index, 1 + ((index + 1) % segments)) for index in range(segments)])
    mesh.materials.append(material)
    wall = bpy.data.objects.new("Aevrynd_OralBackWall_R1046", mesh)
    bpy.context.scene.collection.objects.link(wall)
    world = wall.matrix_world.copy()
    wall.parent, wall.parent_type, wall.parent_bone = parent, parent_type, parent_bone
    wall.matrix_world = world
    wall["aevrynd_layer_owner"] = "Aevrynd"
    wall["aevrynd_layer_revision"] = "v249r1046-diagnostic"
    return wall


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles()
    triangles = [tuple(triangle.vertices) for triangle in mesh.loop_triangles]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, triangles, all_triangles=True), triangles


def audit(scene, body, layers, frame, expression=None):
    scene.frame_set(frame)
    keys = body.data.shape_keys.key_blocks
    keys[OPEN_KEY].value = 1.0 if expression == OPEN_KEY else 0.0
    keys[SMILE_KEY].value = 1.0 if expression == SMILE_KEY else 0.0
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    body_tree, body_triangles = evaluated_tree(body, depsgraph)
    self_pairs = [(a, b) for a, b in body_tree.overlap(body_tree) if a < b and set(body_triangles[a]).isdisjoint(body_triangles[b])]
    body_layer = {}
    layer_trees = {}
    for layer in layers:
        layer_tree, _triangles = evaluated_tree(layer, depsgraph)
        layer_trees[layer.name] = layer_tree
        body_layer[layer.name] = len(body_tree.overlap(layer_tree))
    inter_layer = {}
    names = list(layer_trees)
    for first_index, first in enumerate(names):
        for second in names[first_index + 1:]:
            count = len(layer_trees[first].overlap(layer_trees[second]))
            if count:
                inter_layer[f"{first}::{second}"] = count
    keys[OPEN_KEY].value = 0.0
    keys[SMILE_KEY].value = 0.0
    return {
        "frame": frame,
        "expression": expression or "neutral",
        "bodySelfNonAdjacentPairs": len(self_pairs),
        "bodyLayerOverlap": body_layer,
        "interLayerOverlap": inter_layer,
        "status": "PASS" if not self_pairs and not any(body_layer.values()) and not inter_layer else "FAIL",
    }


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, label):
    camera = scene.camera
    camera.location = (0.0, -0.43, 1.388)
    camera.data.lens = 135
    look_at(camera, (0.0, -0.105, 1.386))
    scene.render.resolution_x, scene.render.resolution_y = 1200, 700
    scene.render.resolution_percentage = 100
    path = RENDER_DIR / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


def hide_hair(scene):
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")):
                obj.hide_render = True


RENDER_DIR.mkdir(parents=True, exist_ok=True)
variants = []
for label, radius_x, radius_z, y, front_cutoff in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    body = bpy.data.objects[BODY]
    removed = measured_internal_faces(body, front_cutoff)
    delete_faces(body, removed)
    wall = replace_back_wall(radius_x, radius_z, y)
    layers = [obj for obj in scene.objects if obj.name.startswith(("Aevrynd_UpperGum_R1044", "Aevrynd_LowerGum_R1044", "Aevrynd_UpperTeeth_R1044", "Aevrynd_LowerTeeth_R1044", "Aevrynd_Tongue_R1044"))]
    layers.append(wall)
    gates = [audit(scene, body, layers, frame) for frame in (1, 20, 33, 61)]
    gates.extend((audit(scene, body, layers, 1, OPEN_KEY), audit(scene, body, layers, 1, SMILE_KEY)))
    hide_hair(scene)
    body.data.shape_keys.key_blocks[OPEN_KEY].value = 0.0
    body.data.shape_keys.key_blocks[SMILE_KEY].value = 0.0
    neutral = render(scene, f"{label}-neutral")
    body.data.shape_keys.key_blocks[OPEN_KEY].value = 1.0
    opened = render(scene, f"{label}-mouth-open")
    body.data.shape_keys.key_blocks[OPEN_KEY].value = 0.0
    body.data.shape_keys.key_blocks[SMILE_KEY].value = 1.0
    smile = render(scene, f"{label}-smile")
    body.data.shape_keys.key_blocks[SMILE_KEY].value = 0.0
    variant = {
        "label": label,
        "wall": {"radiusX": radius_x, "radiusZ": radius_z, "y": y},
        "frontCutoffY": front_cutoff,
        "deletedMeasuredInternalFaces": len(removed),
        "deletedFaceIndices": sorted(removed),
        "shapeKeyCount": len(body.data.shape_keys.key_blocks),
        "gates": gates,
        "renders": [neutral, opened, smile],
        "status": "TECHNICAL_PASS_PENDING_VISUAL" if all(gate["status"] == "PASS" for gate in gates) else "TECHNICAL_FAIL",
    }
    variants.append(variant)
    if label == "d-full-depth" and variant["status"] == "TECHNICAL_PASS_PENDING_VISUAL":
        scene["aevrynd_mainline_revision"] = "v249r1046-depth-cleanup-study"
        scene["aevrynd_mainline_parent"] = SOURCE.name
        scene["aevrynd_release_state"] = "TECHNICAL_PASS_PENDING_STRICT_VISUAL_REVIEW"
        scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "revision": "v249r1046-depth-cleanup-sweep",
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "delete only the 17 measured original-skin faces hit behind the slit, then test a rear bounded vestibule wall",
    "variants": variants,
    "websitePromotionApproved": False,
    "status": "DIAGNOSTIC_PENDING_STRICT_VISUAL_REVIEW",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1046_CLEANUP=" + json.dumps({"variants": [{"label": item["label"], "deleted": item["deletedMeasuredInternalFaces"], "status": item["status"]} for item in variants]}, sort_keys=True))
