"""Delete the eight strip faces and refill only their new figure-eight holes."""

import json
from collections import Counter
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-depth-cleanup-r1046-study.blend"
INSPECTION = ASSETS / "female-v249-mainline-r1048-removal-boundaries.inspect.json"
REPORT = ASSETS / "female-v249-mainline-r1048-figure8-fill.study.json"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "v249r1048-figure8-fill"
BODY = "AevryndFemaleCC0Baseline_v259"
VARIANTS = (("a-skin-fill", "skin"), ("b-wetline-fill", "wetline"))


def delete_and_fill(body, removed, material_role):
    mesh = body.data
    edge_users = Counter()
    for polygon in mesh.polygons:
        vertices = list(polygon.vertices)
        for index, first in enumerate(vertices):
            edge_users[tuple(sorted((first, vertices[(index + 1) % len(vertices)])))] += 1
    before_boundary = {edge for edge, users in edge_users.items() if users == 1}
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[index] for index in sorted(removed)], context="FACES_ONLY")
    bm.edges.ensure_lookup_table()
    new_boundary = [
        edge for edge in bm.edges
        if len(edge.link_faces) == 1
        and tuple(sorted(vertex.index for vertex in edge.verts)) not in before_boundary
    ]
    result = bmesh.ops.holes_fill(bm, edges=new_boundary, sides=0)
    material_index = 0
    if material_role == "wetline":
        for index, material in enumerate(mesh.materials):
            if material and "InnerLipWetline" in material.name:
                material_index = index
                break
    for face in result.get("faces", []):
        face.material_index = material_index
        face.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bmesh.update_edit_mesh(mesh, loop_triangles=True, destructive=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    return {
        "newBoundaryEdges": len(new_boundary),
        "filledFaces": len(result.get("faces", [])),
        "materialRole": material_role,
        "shapeKeyCount": len(mesh.shape_keys.key_blocks),
        "shapeKeyCompatibility": all(len(block.data) == len(mesh.vertices) for block in mesh.shape_keys.key_blocks),
    }


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, label, expression=None):
    body = bpy.data.objects[BODY]
    keys = body.data.shape_keys.key_blocks
    keys["Aevrynd_MouthOpenTest_R1030"].value = 1.0 if expression == "open" else 0.0
    keys["Aevrynd_SmileTest_R1030"].value = 1.0 if expression == "smile" else 0.0
    camera = scene.camera
    camera.location = (0.0, -0.43, 1.388)
    camera.data.lens = 135
    look_at(camera, (0.0, -0.105, 1.386))
    scene.render.resolution_x, scene.render.resolution_y = 1200, 700
    scene.render.resolution_percentage = 100
    path = RENDER_DIR / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    keys["Aevrynd_MouthOpenTest_R1030"].value = 0.0
    keys["Aevrynd_SmileTest_R1030"].value = 0.0
    return str(path)


inspection = json.loads(INSPECTION.read_text(encoding="utf-8"))
removed = inspection["variants"]["strip8"]["removedFaces"]
RENDER_DIR.mkdir(parents=True, exist_ok=True)
variants = []
for label, material_role in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    body = bpy.data.objects[BODY]
    topology = delete_and_fill(body, removed, material_role)
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")):
                obj.hide_render = True
    renders = [render(scene, f"{label}-neutral"), render(scene, f"{label}-mouth-open", "open"), render(scene, f"{label}-smile", "smile")]
    variants.append({"label": label, "topology": topology, "renders": renders, "status": "VISUAL_DIAGNOSTIC"})

report = {
    "revision": "v249r1048-figure8-fill",
    "source": str(SOURCE),
    "removedFaces": removed,
    "method": "delete eight proven strip faces and fill only newly exposed one-face boundary edges using existing vertices",
    "variants": variants,
    "websitePromotionApproved": False,
    "status": "PENDING_STRICT_VISUAL_REVIEW",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1048_FILL=" + json.dumps({"variants": [{"label": item["label"], **item["topology"]} for item in variants]}, sort_keys=True))
