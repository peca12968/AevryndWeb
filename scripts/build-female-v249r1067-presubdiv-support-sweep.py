"""Test procedural support geometry on the measured lower inner-lip band."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-structured-lips-r1061-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-presubdiv-support-r1067-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1067-presubdiv-support.study.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1067-presubdiv-support"
BODY = "AevryndFemaleCC0StructuredLips_R1061"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
VARIANTS = (("a-control", 0.0, 0), ("b-0.10mm-s1", 0.00010, 1), ("c-0.20mm-s1", 0.00020, 1), ("d-0.35mm-s2", 0.00035, 2), ("e-0.50mm-s2", 0.00050, 2))
SELECTED = "c-0.20mm-s1"


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


def add_support_bevel(body, width, segments):
    selected, support, edges = measured_region(body)
    group = body.vertex_groups.get("Aevrynd_LowerInnerBevel_R1067") or body.vertex_groups.new(name="Aevrynd_LowerInnerBevel_R1067")
    group.add(list(selected), 1.0, "REPLACE")
    group.add(list(support), 0.35, "REPLACE")
    modifier = None
    if width:
        modifier = body.modifiers.new("Aevrynd R1067 Lower Inner Support Bevel", "BEVEL")
        modifier.affect = "EDGES"
        modifier.limit_method = "VGROUP"
        modifier.vertex_group = group.name
        modifier.width = width
        modifier.segments = segments
        modifier.profile = 0.5
        modifier.harden_normals = False
        bpy.context.view_layer.objects.active = body
        body.select_set(True)
        bpy.ops.object.modifier_move_to_index(modifier=modifier.name, index=0)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    evaluated_mesh = evaluated.to_mesh()
    evaluated_mesh.calc_loop_triangles()
    topology = {"vertices": len(evaluated_mesh.vertices), "triangles": len(evaluated_mesh.loop_triangles)}
    evaluated.to_mesh_clear()
    return {"measuredEdges": edges, "coreVertices": len(selected), "supportVertices": len(support), "bevelWidthMm": width * 1000.0, "segments": segments, "modifierAdded": modifier is not None, "evaluatedTopology": topology}


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
for label, width, segments in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    body = bpy.data.objects[BODY]
    body.name = "AevryndFemaleCC0InnerEdgeNormals_R1067"
    hide_hair(scene)
    metrics = add_support_bevel(body, width, segments)
    # Blender 5.2.2 crashes on a second render of the pre-subdivision bevel
    # stack. Keep each freshly loaded variant to one deterministic front view.
    renders = [render(scene, f"{label}-front")]
    results.append({"label": label, "metrics": metrics, "renders": renders})
    if label == SELECTED:
        body["aevrynd_revision"] = "v249r1067-presubdiv-support"
        body["aevrynd_source"] = SOURCE.name
        scene["aevrynd_release_state"] = "VISUAL_EXPORT_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "revision": "v249r1067-presubdiv-support",
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "narrow procedural Bevel modifier before subdivision and armature, limited by the measured 85-vertex core and 90-vertex support group",
    "variants": results,
    "selectedVariant": SELECTED,
    "sourceGeometryChanged": False,
    "evaluatedGeometryChanged": True,
    "shapeKeysChanged": False,
    "websitePromotionApproved": False,
    "candidateStatus": "VISUAL_EXPORT_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1067_BEVEL=" + json.dumps({"selected": SELECTED, "variants": [item["metrics"] for item in results]}, sort_keys=True))


