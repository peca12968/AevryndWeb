import json
import math
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-scalp-parent-clearance-r282.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-scalp-boundary-cleanup-r283.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-scalp-boundary-cleanup-r283.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r283-scalp-boundary-cleanup"
BODY = "AevryndFemaleBody_CC0_R249"
RIG = "AevryndFemaleRig"
SCALP = "AevryndFemaleScalpUnderlayer_R280"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def remove_ambiguous_boundary_vertex(scalp, vertex_index=533):
    mesh = scalp.data
    before = (len(mesh.vertices), len(mesh.polygons))
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    linked_faces = len(bm.verts[vertex_index].link_faces)
    bmesh.ops.delete(bm, geom=[bm.verts[vertex_index]], context="VERTS")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return {"removedVertex": vertex_index, "linkedFaces": linked_faces, "before": before, "after": (len(mesh.vertices), len(mesh.polygons))}


def body_tree(body, depsgraph):
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def repair_rest_clearance(scene, body, scalp, target=0.0010):
    scene.frame_set(1)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    tree = body_tree(body, depsgraph)
    matrix, inverse = scalp.matrix_world.copy(), scalp.matrix_world.inverted()
    repaired, before = [], math.inf
    for vertex in scalp.data.vertices:
        world = matrix @ vertex.co
        hit = tree.find_nearest(world, 0.05)
        if hit is None or hit[1] is None:
            continue
        normal = hit[1].normalized()
        signed = (world - hit[0]).dot(normal)
        before = min(before, signed)
        if signed < target:
            vertex.co = inverse @ (hit[0] + normal * target)
            repaired.append(vertex.index)
    scalp.data.update()
    return {"targetM": target, "beforeMinimumSignedM": before, "repairedVertices": len(repaired), "sample": repaired[:32]}


def clearance_audit(scene, body, scalp):
    result = {}
    for frame in (1, 33, 61):
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        tree = body_tree(body, depsgraph)
        evaluated = scalp.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        values = []
        penetrating = []
        for vertex in mesh.vertices:
            world = evaluated.matrix_world @ vertex.co
            hit = tree.find_nearest(world, 0.05)
            if hit is not None and hit[1] is not None:
                signed = (world - hit[0]).dot(hit[1].normalized())
                values.append(signed)
                if signed < 0.0:
                    penetrating.append({"vertex": vertex.index, "signedM": signed})
        evaluated.to_mesh_clear()
        result[str(frame)] = {
            "samples": len(values), "minimumSignedM": min(values), "maximumSignedM": max(values),
            "penetratingVertices": sum(1 for value in values if value < 0.0),
            "penetratingSample": penetrating[:16],
        }
    return result


def render(camera, frame, name, location):
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.location = location
    camera.data.lens = 82
    look_at(camera, (0.0, 0.0, 1.56))
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
rig = bpy.data.objects[RIG]
scalp = bpy.data.objects[SCALP]
boundary_cleanup = remove_ambiguous_boundary_vertex(scalp)
scalp.parent = rig
scalp.parent_type = body.parent_type
scalp.matrix_parent_inverse = body.matrix_parent_inverse.copy()
scalp.matrix_basis = body.matrix_basis.copy()
repair = repair_rest_clearance(scene, body, scalp)
audit = clearance_audit(scene, body, scalp)
failures = [{"frame": frame, "penetratingVertices": values["penetratingVertices"]} for frame, values in audit.items() if values["penetratingVertices"]]
scalp["aevrynd_revision"] = "v249r283"
scalp["aevrynd_parent_contract"] = "same rig parent, parent inverse and basis as source body"
scalp["aevrynd_clearance_m"] = 0.0010
scene["aevrynd_mainline_revision"] = "v249r283-scalp-boundary-cleanup"
scene["aevrynd_release_state"] = "SCALP_BOUNDARY_CLEANUP_PASS_VISUAL_HAIR_REAUDIT_PENDING" if not failures else "SCALP_BOUNDARY_CLEANUP_FAIL"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
for frame, name, location in (
    (1, "front-f01", (0.0, -0.90, 1.59)), (33, "front-f33", (0.0, -0.90, 1.59)),
    (1, "left-f01", (-0.72, -0.55, 1.59)), (1, "right-f01", (0.72, -0.55, 1.59)),
    (1, "back-f01", (0.0, 0.90, 1.59)), (33, "back-f33", (0.0, 0.90, 1.59)),
):
    render(camera, frame, name, location)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "scalpObject": SCALP,
    "parent": rig.name, "parentType": scalp.parent_type, "boundaryCleanup": boundary_cleanup, "restClearanceRepair": repair,
    "clearanceAudit": audit, "failures": failures, "renderDirectory": str(RENDER_DIR),
    "status": "PASS_PENDING_VISUAL_AND_HAIR_DYNAMIC_AUDIT" if not failures else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R283_SCALP_BOUNDARY_CLEANUP=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)

