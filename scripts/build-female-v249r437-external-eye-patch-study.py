import json
from collections import deque
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-layered-optical-stack-r420.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-external-eye-patch-r437-study.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-external-eye-patch-r437.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r437-external-eye-patch-study"
BODY = "AevryndFemaleBody_CC0_R249"
EYE_Z = 1.6070
EYE_CENTERS_X = {"L": 0.03315, "R": -0.03318}
REGION_RX = 0.0170
REGION_RZ = 0.0120
FRONT_Y_LIMIT = -0.118
FRONT_NORMAL_Y_MAX = -0.20
TARGET_FACES = 900
QUADRIFLOW_SCALE = 100.0


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def topology_stats(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    unseen = set(bm.verts)
    components = []
    while unseen:
        seed = unseen.pop()
        count = 1
        queue = deque([seed])
        while queue:
            vertex = queue.popleft()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in unseen:
                    unseen.remove(other)
                    count += 1
                    queue.append(other)
        components.append(count)
    components.sort(reverse=True)
    lengths = [edge.calc_length() for edge in bm.edges]
    report = {
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "quads": sum(1 for face in bm.faces if len(face.verts) == 4),
        "quadRatio": sum(1 for face in bm.faces if len(face.verts) == 4) / max(1, len(bm.faces)),
        "boundaryEdges": sum(1 for edge in bm.edges if len(edge.link_faces) == 1),
        "wireEdges": sum(1 for edge in bm.edges if len(edge.link_faces) == 0),
        "overConnectedEdges": sum(1 for edge in bm.edges if len(edge.link_faces) > 2),
        "componentCount": len(components),
        "componentVertexCounts": components[:10],
        "minimumEdgeMeters": min(lengths) if lengths else None,
    }
    bm.free()
    return report


def extract_eye_patch(source_obj, evaluated_mesh, side):
    center_x = EYE_CENTERS_X[side]
    normal_matrix = source_obj.matrix_world.to_3x3()
    selected_faces = []
    selected_indices = set()
    for polygon in evaluated_mesh.polygons:
        center = source_obj.matrix_world @ polygon.center
        normal = (normal_matrix @ polygon.normal).normalized()
        ellipse = ((center.x - center_x) / REGION_RX) ** 2 + ((center.z - EYE_Z) / REGION_RZ) ** 2
        if ellipse <= 1.0 and center.y < FRONT_Y_LIMIT and normal.y < FRONT_NORMAL_Y_MAX:
            face = tuple(polygon.vertices)
            selected_faces.append(face)
            selected_indices.update(face)
    ordered = sorted(selected_indices)
    remap = {old: new for new, old in enumerate(ordered)}
    vertices = [evaluated_mesh.vertices[index].co.copy() for index in ordered]
    faces = [tuple(remap[index] for index in face) for face in selected_faces]
    mesh = bpy.data.meshes.new(f"AevryndEye_{side}_ExternalPatch_R437Geometry")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(verbose=True, clean_customdata=True)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(f"AevryndEye_{side}_ExternalPatch_R437", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = source_obj.matrix_world.copy()
    obj["aevrynd_layer"] = f"body.face.eye_{side.lower()}.external_patch.study"
    obj["aevrynd_revision"] = "v249r437-study"
    return obj


def retain_largest_component(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    unseen = set(bm.verts)
    components = []
    while unseen:
        seed = unseen.pop()
        component = {seed}
        queue = deque([seed])
        while queue:
            vertex = queue.popleft()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in unseen:
                    unseen.remove(other)
                    component.add(other)
                    queue.append(other)
        components.append(component)
    components.sort(key=len, reverse=True)
    discard = [vertex for component in components[1:] for vertex in component]
    if discard:
        bmesh.ops.delete(bm, geom=discard, context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update(calc_edges=True)


def remesh_patch(obj):
    retain_largest_component(obj)
    before = topology_stats(obj.data)
    for vertex in obj.data.vertices:
        vertex.co *= QUADRIFLOW_SCALE
    obj.data.update()
    for selected in bpy.context.selected_objects:
        selected.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    result = bpy.ops.object.quadriflow_remesh(
        use_mesh_symmetry=False,
        use_preserve_sharp=False,
        use_preserve_boundary=True,
        preserve_attributes=False,
        smooth_normals=True,
        mode="FACES",
        target_faces=TARGET_FACES,
        seed=17,
    )
    for vertex in obj.data.vertices:
        vertex.co /= QUADRIFLOW_SCALE
    obj.data.update()
    after = topology_stats(obj.data)
    return {"operatorResult": sorted(result), "before": before, "after": after}


def make_wire_material():
    material = bpy.data.materials.new("Aevrynd_R437_TopologyWire")
    material.diffuse_color = (0.01, 0.55, 1.0, 1.0)
    material.use_nodes = True
    bsdf = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.005, 0.25, 0.8, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.28
    bsdf.inputs["Emission Color"].default_value = (0.0, 0.16, 0.8, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 1.6
    return material


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
source_body = bpy.data.objects[BODY]
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = source_body.evaluated_get(depsgraph)
evaluated_mesh = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=False, depsgraph=depsgraph)
patches = {side: extract_eye_patch(source_body, evaluated_mesh, side) for side in ("L", "R")}
results = {side: remesh_patch(obj) for side, obj in patches.items()}

wire_material = make_wire_material()
for patch in patches.values():
    patch.data.materials.clear()
    patch.data.materials.append(wire_material)
    wire = patch.modifiers.new("Aevrynd R437 Topology Wire Review", "WIREFRAME")
    wire.thickness = 0.00018
    wire.offset = 1.0
    wire.use_replace = True

for obj in bpy.data.objects:
    name = obj.name.lower()
    if obj in patches.values() or obj == source_body:
        obj.hide_render = False
    elif any(token in name for token in ("eye", "caruncle", "tear", "brow", "lash")):
        obj.hide_render = False
    elif obj.type in {"MESH", "CURVES", "CURVE"}:
        obj.hide_render = True

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Base Contrast"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
scene.camera = camera
views = (
    ("front", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 100),
    ("three-quarter", (0.34, -0.60, 1.618), (0.0, -0.025, 1.604), 96),
    ("eyes-close", (0.0, -0.48, 1.607), (0.0, -0.045, 1.607), 112),
)
for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 1200
    scene.render.filepath = str(RENDER_DIR / f"r437-{name}.png")
    bpy.ops.render.render(write_still=True)

topology_gate_pass = all(
    result["operatorResult"] == ["FINISHED"]
    and result["after"]["faces"] < result["before"]["faces"]
    and result["after"]["quadRatio"] >= 0.95
    and result["after"]["overConnectedEdges"] == 0
    and result["after"]["wireEdges"] == 0
    for result in results.values()
)
status = "LOCAL_PATCH_TOPOLOGY_PASS_FEATURE_FLOW_FAIL_REFERENCE_ONLY" if topology_gate_pass else "REJECTED_LOCAL_PATCH_TOPOLOGY_GATE_FAIL"
scene["aevrynd_eye_patch_study"] = "v249r437"
scene["aevrynd_release_state"] = status
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "renderDirectory": str(RENDER_DIR),
    "selection": {
        "eyeCentersX": EYE_CENTERS_X,
        "eyeZ": EYE_Z,
        "regionRadiusX": REGION_RX,
        "regionRadiusZ": REGION_RZ,
        "frontYLimit": FRONT_Y_LIMIT,
        "frontNormalYMaximum": FRONT_NORMAL_Y_MAX,
    },
    "targetFacesPerEye": TARGET_FACES,
    "results": results,
    "derivedOnlyFromOwnedCC0Mainline": True,
    "integratedIntoHeadCage": False,
    "rigTransferred": False,
    "collisionAuditComplete": False,
    "websitePromotionApproved": False,
    "status": status,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R437_EXTERNAL_EYE_PATCH=" + json.dumps(report, sort_keys=True))
