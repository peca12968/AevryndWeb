"""Fair the measured high-dihedral lower inner-lip edge in depth only."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-structured-lips-r1061-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-inner-edge-fairing-r1063-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1063-inner-edge-fairing.study.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1063-inner-edge-fairing"
BODY = "AevryndFemaleCC0StructuredLips_R1061"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
VARIANTS = (("a-control", 0.0), ("b-quarter", 0.25), ("c-half", 0.50), ("d-three-quarter", 0.75), ("e-full", 1.0))
SELECTED = "c-half"


def neutral_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    points = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.name in (OPEN_KEY, SMILE_KEY) or block.mute or abs(block.value) < 1e-8:
            continue
        for index, point in enumerate(points):
            point += block.value * (block.data[index].co - block.relative_key.data[index].co)
    return [body.matrix_world @ point for point in points]


def face_normal(polygon, points):
    first = points[polygon.vertices[0]]
    value = Vector()
    for offset in range(1, len(polygon.vertices) - 1):
        value += (points[polygon.vertices[offset]] - first).cross(points[polygon.vertices[offset + 1]] - first)
    return value.normalized() if value.length else Vector((0, 0, 1))


def measured_vertices(body, points):
    mesh = body.data
    normals = [face_normal(polygon, points) for polygon in mesh.polygons]
    edge_lookup = {tuple(sorted(edge.vertices)): edge.index for edge in mesh.edges}
    edge_faces = {edge.index: [] for edge in mesh.edges}
    neighbors = {vertex.index: set() for vertex in mesh.vertices}
    for edge in mesh.edges:
        first, second = edge.vertices
        neighbors[first].add(second)
        neighbors[second].add(first)
    for polygon in mesh.polygons:
        for edge_key in polygon.edge_keys:
            edge_faces[edge_lookup[tuple(sorted(edge_key))]].append(polygon.index)
    lips = body.vertex_groups["lips"]
    weights = {
        vertex.index: next((item.weight for item in vertex.groups if item.group == lips.index), 0.0)
        for vertex in mesh.vertices
    }
    selected = set()
    edge_count = 0
    maximum_angle = 0.0
    for edge in mesh.edges:
        faces = edge_faces[edge.index]
        if len(faces) != 2:
            continue
        center = (points[edge.vertices[0]] + points[edge.vertices[1]]) * 0.5
        angle = math.degrees(normals[faces[0]].angle(normals[faces[1]]))
        if center.y < -0.120 and 1.383 < center.z < 1.3895 and angle >= 30.0 and min(weights[index] for index in edge.vertices) >= 0.24:
            edge_count += 1
            maximum_angle = max(maximum_angle, angle)
            selected.update(edge.vertices)
    return selected, neighbors, edge_count, maximum_angle


def apply_fairing(body, strength):
    points = neutral_coordinates(body)
    selected, neighbors, edge_count, maximum_angle = measured_vertices(body, points)
    support = set().union(*(neighbors[index] for index in selected)) - selected
    inverse3 = body.matrix_world.inverted().to_3x3()
    movements = {}
    for index in selected | support:
        adjacent = neighbors[index]
        if not adjacent:
            continue
        mean_y = sum(points[other].y for other in adjacent) / len(adjacent)
        weight = 1.0 if index in selected else 0.28
        amount = max(-0.0008, min(0.0008, (mean_y - points[index].y) * strength * weight))
        if abs(amount) > 1e-8:
            movements[index] = inverse3 @ Vector((0.0, amount, 0.0))
    for block in body.data.shape_keys.key_blocks:
        for index, movement in movements.items():
            block.data[index].co += movement
    body.data.update()
    return {
        "measuredEdges": edge_count,
        "selectedVertices": len(selected),
        "supportVertices": len(support),
        "movedVertices": len(movements),
        "maximumSourceDihedralDegrees": maximum_angle,
        "maximumDepthMoveMm": max((abs(movement.y) for movement in movements.values()), default=0.0) * 1000.0,
    }


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


def hide_hair(scene):
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")):
                obj.hide_render = True


OUT.mkdir(parents=True, exist_ok=True)
results = []
for label, strength in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    body = bpy.data.objects[BODY]
    body.name = "AevryndFemaleCC0InnerEdgeFairing_R1063"
    hide_hair(scene)
    metrics = apply_fairing(body, strength)
    renders = [render(scene, f"{label}-neutral-front"), render(scene, f"{label}-neutral-oblique", True)]
    result = {"label": label, "strength": strength, "metrics": metrics, "renders": renders}
    results.append(result)
    if label == SELECTED:
        body["aevrynd_revision"] = "v249r1063-inner-edge-fairing"
        body["aevrynd_source"] = SOURCE.name
        body["aevrynd_fairing_strength"] = strength
        scene["aevrynd_release_state"] = "VISUAL_AND_COLLISION_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "revision": "v249r1063-inner-edge-fairing",
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "measured >=30 degree lower inner-lip edges plus one support ring; depth-only clamped Laplacian fairing across all 35 shape keys",
    "variants": results,
    "selectedVariant": SELECTED,
    "websitePromotionApproved": False,
    "candidateStatus": "VISUAL_AND_COLLISION_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1063_FAIRING=" + json.dumps({"selected": SELECTED, "variants": [{"label": item["label"], **item["metrics"]} for item in results]}, sort_keys=True))
