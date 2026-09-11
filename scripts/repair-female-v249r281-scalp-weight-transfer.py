import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-scalp-underlayer-grouped-tips-r280.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-scalp-weight-transfer-r281.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-scalp-weight-transfer-r281.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r281-scalp-weight-transfer"
BODY = "AevryndFemaleBody_CC0_R249"
SCALP = "AevryndFemaleScalpUnderlayer_R280"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def source_vertex_ids(body):
    selected = []
    for polygon in body.data.polygons:
        center = sum((body.data.vertices[index].co for index in polygon.vertices), Vector()) / len(polygon.vertices)
        if center.z > 1.555 and center.y > -0.064:
            selected.append(polygon)
    return sorted({index for polygon in selected for index in polygon.vertices})


def transfer_weights(body, scalp):
    source_ids = source_vertex_ids(body)
    if len(source_ids) != len(scalp.data.vertices):
        raise RuntimeError(f"scalp/source topology mismatch: {len(scalp.data.vertices)} != {len(source_ids)}")
    for group in list(scalp.vertex_groups):
        scalp.vertex_groups.remove(group)
    groups = {group.index: scalp.vertex_groups.new(name=group.name) for group in body.vertex_groups}
    assignments = 0
    totals = []
    for scalp_index, source_index in enumerate(source_ids):
        total = 0.0
        for membership in body.data.vertices[source_index].groups:
            groups[membership.group].add([scalp_index], membership.weight, "REPLACE")
            total += membership.weight
            assignments += 1
        totals.append(total)
    return {
        "sourceVertices": len(source_ids), "targetVertices": len(scalp.data.vertices),
        "vertexGroupCount": len(groups), "weightAssignments": assignments,
        "minimumWeightSum": min(totals), "maximumWeightSum": max(totals),
        "unweightedVertices": sum(1 for total in totals if total <= 1e-8),
    }


def body_tree(body, depsgraph):
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def clearance_audit(scene, body, scalp):
    result = {}
    for frame in (1, 33, 61):
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        tree = body_tree(body, depsgraph)
        evaluated = scalp.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        signed_values = []
        for vertex in mesh.vertices:
            world = evaluated.matrix_world @ vertex.co
            hit = tree.find_nearest(world, 0.05)
            if hit is not None and hit[1] is not None:
                signed_values.append((world - hit[0]).dot(hit[1].normalized()))
        evaluated.to_mesh_clear()
        result[str(frame)] = {
            "samples": len(signed_values), "minimumSignedM": min(signed_values),
            "maximumSignedM": max(signed_values),
            "penetratingVertices": sum(1 for value in signed_values if value < 0.0),
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
body = bpy.data.objects[BODY]
scalp = bpy.data.objects[SCALP]
transfer = transfer_weights(body, scalp)
clearance = clearance_audit(scene, body, scalp)
failures = []
if transfer["unweightedVertices"]:
    failures.append({"unweightedVertices": transfer["unweightedVertices"]})
for frame, values in clearance.items():
    if values["penetratingVertices"]:
        failures.append({"frame": frame, "penetratingVertices": values["penetratingVertices"]})
scalp["aevrynd_revision"] = "v249r281"
scalp["aevrynd_weight_source"] = BODY
scene["aevrynd_mainline_revision"] = "v249r281-scalp-weight-transfer"
scene["aevrynd_release_state"] = "SCALP_WEIGHT_TRANSFER_PASS_VISUAL_AND_HAIR_DYNAMIC_REAUDIT_PENDING" if not failures else "SCALP_WEIGHT_TRANSFER_FAIL"
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
    "weightTransfer": transfer, "clearanceAudit": clearance, "failures": failures,
    "renderDirectory": str(RENDER_DIR), "status": "PASS_PENDING_VISUAL_AND_HAIR_DYNAMIC_AUDIT" if not failures else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R281_SCALP_WEIGHT_TRANSFER=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
