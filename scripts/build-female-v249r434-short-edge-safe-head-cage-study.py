import json
from collections import deque
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-layered-optical-stack-r420.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-short-edge-safe-head-cage-r434-study.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-exterior-head-cage-r434.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r434-short-edge-safe-head-cage-study"
BODY = "AevryndFemaleBody_CC0_R249"
NECK_CUT_Z = 1.405
TARGET_FACES = 18000
VOXEL_SIZE = 0.0015
QUADRIFLOW_MIN_EDGE = 0.000101


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def mesh_stats(obj):
    polygons = list(obj.data.polygons)
    quads = sum(1 for polygon in polygons if len(polygon.vertices) == 4)
    return {
        "vertices": len(obj.data.vertices),
        "edges": len(obj.data.edges),
        "polygons": len(polygons),
        "triangles": sum(max(1, len(polygon.vertices) - 2) for polygon in polygons),
        "quads": quads,
        "quadRatio": quads / max(1, len(polygons)),
        "ngons": sum(1 for polygon in polygons if len(polygon.vertices) > 4),
    }


def bmesh_topology_stats(bm):
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    unseen = set(bm.verts)
    components = []
    while unseen:
        seed = unseen.pop()
        queue = deque([seed])
        count = 0
        while queue:
            vertex = queue.popleft()
            count += 1
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in unseen:
                    unseen.remove(other)
                    queue.append(other)
        components.append(count)
    components.sort(reverse=True)
    return {
        "componentCount": len(components),
        "componentVertexCounts": components[:20],
        "boundaryEdges": sum(1 for edge in bm.edges if len(edge.link_faces) == 1),
        "wireEdges": sum(1 for edge in bm.edges if len(edge.link_faces) == 0),
        "overConnectedEdges": sum(1 for edge in bm.edges if len(edge.link_faces) > 2),
    }


def retain_largest_component_and_repair(mesh, matrix_world):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    remove = [vertex for vertex in bm.verts if (matrix_world @ vertex.co).z < NECK_CUT_Z]
    bmesh.ops.delete(bm, geom=remove, context="VERTS")
    bm.verts.ensure_lookup_table()
    before = bmesh_topology_stats(bm)

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
    largest = max(components, key=len)
    discard = [vertex for component in components if component is not largest for vertex in component]
    if discard:
        bmesh.ops.delete(bm, geom=discard, context="VERTS")
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1.0e-7)
    after_cleanup = bmesh_topology_stats(bm)
    boundary_edges = [edge for edge in bm.edges if len(edge.link_faces) == 1]
    if boundary_edges:
        bmesh.ops.triangle_fill(bm, edges=boundary_edges, use_beauty=True)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    after_cap = bmesh_topology_stats(bm)
    bm.to_mesh(mesh)
    bm.free()
    mesh.validate(verbose=True, clean_customdata=True)
    mesh.update(calc_edges=True)
    return before, after_cleanup, after_cap


def retain_largest_component(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
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
    stats = bmesh_topology_stats(bm)
    bm.to_mesh(mesh)
    bm.free()
    mesh.validate(verbose=True, clean_customdata=True)
    mesh.update(calc_edges=True)
    return stats


def rebuild_geometry_only(obj):
    source_mesh = obj.data
    vertices = [vertex.co.copy() for vertex in source_mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in source_mesh.polygons]
    clean_mesh = bpy.data.meshes.new("AevryndFemaleShortEdgeSafeHeadCage_R434InputGeometry")
    clean_mesh.from_pydata(vertices, [], faces)
    clean_mesh.validate(verbose=True, clean_customdata=True)
    clean_mesh.update(calc_edges=True)
    obj.data = clean_mesh
    bpy.data.meshes.remove(source_mesh)
    return {
        "vertices": len(vertices),
        "faces": len(faces),
        "attributeNames": [attribute.name for attribute in clean_mesh.attributes],
    }


def eliminate_quadriflow_short_edges(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    before_lengths = [edge.calc_length() for edge in bm.edges]
    short_before = sum(1 for length in before_lengths if length < QUADRIFLOW_MIN_EDGE)
    bmesh.ops.dissolve_degenerate(
        bm,
        dist=QUADRIFLOW_MIN_EDGE,
        edges=list(bm.edges),
    )
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    after_lengths = [edge.calc_length() for edge in bm.edges]
    report = {
        "thresholdMeters": QUADRIFLOW_MIN_EDGE,
        "shortEdgesBefore": short_before,
        "shortEdgesAfter": sum(1 for length in after_lengths if length < QUADRIFLOW_MIN_EDGE),
        "minimumEdgeBeforeMeters": min(before_lengths) if before_lengths else None,
        "minimumEdgeAfterMeters": min(after_lengths) if after_lengths else None,
        "topology": bmesh_topology_stats(bm),
    }
    bm.to_mesh(mesh)
    bm.free()
    mesh.validate(verbose=True, clean_customdata=True)
    mesh.update(calc_edges=True)
    return report


def hide_non_review_layers(cage):
    for obj in bpy.data.objects:
        if obj == cage:
            continue
        name = obj.name.lower()
        if any(token in name for token in ("eye", "caruncle", "tear", "brow", "lash")):
            obj.hide_render = False
            continue
        if obj.type in {"MESH", "CURVES", "CURVE"}:
            obj.hide_render = True


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
source_body = bpy.data.objects[BODY]
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = source_body.evaluated_get(depsgraph)
mesh = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=True, depsgraph=depsgraph)
cage = bpy.data.objects.new("AevryndFemaleShortEdgeSafeHeadCage_R434", mesh)
scene.collection.objects.link(cage)
cage.matrix_world = source_body.matrix_world.copy()
cage["aevrynd_layer"] = "body.head.exterior_retopology_cage.study"
cage["aevrynd_revision"] = "v249r434-study"
cage["aevrynd_source"] = SOURCE.name

topology_before, topology_after_cleanup, topology_after_cap = retain_largest_component_and_repair(mesh, cage.matrix_world)
before_quadriflow = mesh_stats(cage)

for obj in bpy.context.selected_objects:
    obj.select_set(False)
cage.select_set(True)
bpy.context.view_layer.objects.active = cage
cage.data.remesh_voxel_size = VOXEL_SIZE
cage.data.use_remesh_preserve_volume = True
bpy.ops.object.voxel_remesh()
after_voxel_remesh = mesh_stats(cage)
topology_after_voxel_cleanup = retain_largest_component(cage.data)
geometry_rebuild = rebuild_geometry_only(cage)
short_edge_cleanup = eliminate_quadriflow_short_edges(cage.data)
after_voxel_cleanup = mesh_stats(cage)
bpy.ops.object.quadriflow_remesh(
    use_mesh_symmetry=True,
    use_preserve_sharp=False,
    use_preserve_boundary=True,
    preserve_attributes=False,
    smooth_normals=True,
    mode="FACES",
    target_faces=TARGET_FACES,
    seed=11,
)
cage.name = "AevryndFemaleShortEdgeSafeHeadCage_R434"
cage.data.name = "AevryndFemaleShortEdgeSafeHeadCage_R434Geometry"
after_quadriflow = mesh_stats(cage)
quadriflow_changed = after_quadriflow["polygons"] < before_quadriflow["polygons"] * 0.75
target_range_pass = TARGET_FACES * 0.55 <= after_quadriflow["polygons"] <= TARGET_FACES * 1.45
quad_ratio_pass = after_quadriflow["quadRatio"] >= 0.95
topology_gate_pass = quadriflow_changed and target_range_pass and quad_ratio_pass

if source_body.data.materials:
    cage.data.materials.clear()
    cage.data.materials.append(source_body.data.materials[0])
for polygon in cage.data.polygons:
    polygon.use_smooth = True

hide_non_review_layers(cage)
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
    ("front", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
    ("three-quarter", (0.44, -0.63, 1.62), (0.0, -0.02, 1.595), 88),
    ("profile", (0.72, -0.20, 1.60), (0.0, -0.02, 1.595), 88),
)
for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.filepath = str(RENDER_DIR / f"r434-{name}.png")
    bpy.ops.render.render(write_still=True)

status = "TOPOLOGY_GATE_PASS_VISUAL_REVIEW_PENDING" if topology_gate_pass else "REJECTED_QUADRIFLOW_TOPOLOGY_GATE_FAIL"
scene["aevrynd_head_retopology_study"] = "v249r434"
scene["aevrynd_release_state"] = status
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "renderDirectory": str(RENDER_DIR),
    "neckCutWorldZ": NECK_CUT_Z,
    "targetFaces": TARGET_FACES,
    "voxelSizeMeters": VOXEL_SIZE,
    "topologyBeforeCleanup": topology_before,
    "topologyAfterCleanup": topology_after_cleanup,
    "topologyAfterNeckCap": topology_after_cap,
    "beforeQuadriflow": before_quadriflow,
    "afterVoxelRemesh": after_voxel_remesh,
    "topologyAfterVoxelCleanup": topology_after_voxel_cleanup,
    "afterVoxelCleanup": after_voxel_cleanup,
    "geometryOnlyRebuildBeforeQuadriflow": geometry_rebuild,
    "shortEdgeCleanup": short_edge_cleanup,
    "afterQuadriflow": after_quadriflow,
    "gates": {
        "quadriflowChanged": quadriflow_changed,
        "targetRangePass": target_range_pass,
        "quadRatioPass": quad_ratio_pass,
        "topologyGatePass": topology_gate_pass,
    },
    "derivedOnlyFromOwnedCC0Mainline": True,
    "rigTransferred": False,
    "shapeKeysCreated": False,
    "websitePromotionApproved": False,
    "status": status,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R434_SHORT_EDGE_SAFE_HEAD_CAGE=" + json.dumps(report, sort_keys=True))
