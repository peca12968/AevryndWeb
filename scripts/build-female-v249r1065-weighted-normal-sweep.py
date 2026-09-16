"""Test exportable weighted normals on the measured lower inner-lip band."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-structured-lips-r1061-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-inner-edge-normals-r1065-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1065-weighted-normal.study.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1065-weighted-normal"
BODY = "AevryndFemaleCC0StructuredLips_R1061"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
VARIANTS = (("a-control", 0), ("b-weight10", 10), ("c-weight30", 30), ("d-weight50", 50), ("e-weight100", 100))
SELECTED = "d-weight50"


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


def measured_region(body):
    mesh = body.data
    points = neutral_coordinates(body)
    normals = [face_normal(polygon, points) for polygon in mesh.polygons]
    lookup = {tuple(sorted(edge.vertices)): edge.index for edge in mesh.edges}
    edge_faces = {edge.index: [] for edge in mesh.edges}
    neighbors = {vertex.index: set() for vertex in mesh.vertices}
    for edge in mesh.edges:
        first, second = edge.vertices
        neighbors[first].add(second)
        neighbors[second].add(first)
    for polygon in mesh.polygons:
        for edge_key in polygon.edge_keys:
            edge_faces[lookup[tuple(sorted(edge_key))]].append(polygon.index)
    lips = body.vertex_groups["lips"]
    weights = {vertex.index: next((item.weight for item in vertex.groups if item.group == lips.index), 0.0) for vertex in mesh.vertices}
    selected = set()
    edges = 0
    for edge in mesh.edges:
        faces = edge_faces[edge.index]
        if len(faces) != 2:
            continue
        center = (points[edge.vertices[0]] + points[edge.vertices[1]]) * 0.5
        angle = math.degrees(normals[faces[0]].angle(normals[faces[1]]))
        if center.y < -0.120 and 1.383 < center.z < 1.3895 and angle >= 30.0 and min(weights[index] for index in edge.vertices) >= 0.24:
            selected.update(edge.vertices)
            edges += 1
    support = set().union(*(neighbors[index] for index in selected)) - selected
    return selected, support, edges


def add_weighted_normal(body, weight):
    selected, support, edges = measured_region(body)
    group = body.vertex_groups.get("Aevrynd_LowerInnerNormal_R1065") or body.vertex_groups.new(name="Aevrynd_LowerInnerNormal_R1065")
    group.add(list(selected), 1.0, "REPLACE")
    group.add(list(support), 0.35, "REPLACE")
    modifier = None
    if weight:
        modifier = body.modifiers.new("Aevrynd R1065 Lower Inner Weighted Normal", "WEIGHTED_NORMAL")
        modifier.mode = "FACE_AREA"
        modifier.weight = weight
        modifier.thresh = 0.01
        modifier.keep_sharp = False
        modifier.vertex_group = group.name
        modifier.invert_vertex_group = False
    return {"measuredEdges": edges, "coreVertices": len(selected), "supportVertices": len(support), "modifierWeight": weight, "modifierAdded": modifier is not None}


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def hide_hair(scene):
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")):
                obj.hide_render = True


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
results = []
for label, weight in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    body = bpy.data.objects[BODY]
    body.name = "AevryndFemaleCC0InnerEdgeNormals_R1065"
    hide_hair(scene)
    metrics = add_weighted_normal(body, weight)
    renders = [render(scene, f"{label}-front"), render(scene, f"{label}-oblique", True)]
    results.append({"label": label, "metrics": metrics, "renders": renders})
    if label == SELECTED:
        body["aevrynd_revision"] = "v249r1065-weighted-normal"
        body["aevrynd_source"] = SOURCE.name
        scene["aevrynd_release_state"] = "VISUAL_EXPORT_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "revision": "v249r1065-weighted-normal",
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "Weighted Normal modifier after subdivision and armature, confined by the measured 85-vertex core and 90-vertex support group",
    "variants": results,
    "selectedVariant": SELECTED,
    "geometryChanged": False,
    "shapeKeysChanged": False,
    "websitePromotionApproved": False,
    "candidateStatus": "VISUAL_EXPORT_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1065_NORMALS=" + json.dumps({"selected": SELECTED, "variants": [item["metrics"] for item in results]}, sort_keys=True))
