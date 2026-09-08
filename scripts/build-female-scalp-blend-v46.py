import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v45.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v46.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v46.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v46-lod1.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "scalp-blend-v46"


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def body_tree(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
    result = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    return result


def material():
    result = bpy.data.materials.get("Aevrynd_Hair_Undercut_v46") or bpy.data.materials.new("Aevrynd_Hair_Undercut_v46")
    result.use_nodes = True
    nodes = result.node_tree.nodes
    links = result.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    density = nodes.new("ShaderNodeVertexColor")
    density.layer_name = "AevryndUndercutDensity"
    shader.inputs["Roughness"].default_value = 0.72
    shader.inputs["Specular IOR Level"].default_value = 0.07
    if shader.inputs.get("Anisotropic IOR Level"):
        shader.inputs["Anisotropic IOR Level"].default_value = 0.20
    links.new(density.outputs["Color"], shader.inputs["Base Color"])
    links.new(density.outputs["Alpha"], shader.inputs["Alpha"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    result.surface_render_method = "DITHERED"
    result.use_transparency_overlap = False
    result["aevrynd_runtime_owned"] = True
    result["aevrynd_alpha_strategy"] = "wide_four_edge_vertex_fade"
    return result


def rebuild_undercut(body, rig, undercut_material, clearance=0.00072):
    old = bpy.data.objects.get("HairUndercutScalp")
    if old:
        old_mesh = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
    source = body.data
    projection = body_tree(body)
    nearest = KDTree(len(source.vertices))
    for vertex in source.vertices:
        nearest.insert(body.matrix_world @ vertex.co, vertex.index)
    nearest.balance()
    center = Vector((0.0, -0.002, 1.625))
    segments, rows = 96, 28
    vertices, source_indices, faces = [], [], []
    misses = 0
    for segment in range(segments):
        s = segment / (segments - 1)
        phi = 0.28 + s * (math.pi - 0.56)
        side = abs(math.cos(phi))
        top_theta = 1.31 + 0.11 * side
        bottom_theta = 2.31 - 0.15 * side
        for row in range(rows):
            t = row / (rows - 1)
            eased = smoothstep(t)
            theta = top_theta + (bottom_theta - top_theta) * eased
            direction = Vector((0.98 * math.sin(theta) * math.cos(phi), 1.12 * math.sin(theta) * math.sin(phi), math.cos(theta))).normalized()
            location, normal, _, _ = projection.ray_cast(center, direction, 0.30)
            if location is None:
                misses += 1
                location = center + direction * 0.10
                normal = direction
            vertices.append(tuple(body.matrix_world.inverted() @ (location + normal.normalized() * clearance)))
            _, source_index, _ = nearest.find(location)
            source_indices.append(source_index)
    for segment in range(segments - 1):
        for row in range(rows - 1):
            a = segment * rows + row
            b = (segment + 1) * rows + row
            faces.append((a, b, b + 1, a + 1))
    mesh = bpy.data.meshes.new("HairUndercutScalpMeshV46")
    mesh.from_pydata(vertices, [], faces)
    density = mesh.color_attributes.new(name="AevryndUndercutDensity", type="BYTE_COLOR", domain="POINT")
    alpha_values = []
    for segment in range(segments):
        s = segment / (segments - 1)
        side_fade = smoothstep(min(s, 1.0 - s) / 0.24)
        for row in range(rows):
            t = row / (rows - 1)
            vertical_fade = smoothstep(min(t, 1.0 - t) / 0.24)
            variation = 0.90 + 0.10 * math.sin(segment * 2.17 + row * 4.31)
            alpha = 0.46 * side_fade * vertical_fade * variation
            alpha_values.append(alpha)
            tone = 0.82 + 0.18 * math.sin(segment * 1.73 + row * 3.19) ** 2
            density.data[segment * rows + row].color_srgb = (0.050 * tone, 0.0125 * tone, 0.0045 * tone, alpha)
    mesh.materials.append(undercut_material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj = bpy.data.objects.new("HairUndercutScalp", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = body.matrix_world.copy()
    groups = {group.index: obj.vertex_groups.new(name=group.name) for group in body.vertex_groups}
    for target_index, source_index in enumerate(source_indices):
        for assignment in source.vertices[source_index].groups:
            if assignment.weight > 1e-8:
                groups[assignment.group].add([target_index], assignment.weight, "REPLACE")
    armature = obj.modifiers.new("Aevrynd Undercut Deform", "ARMATURE")
    armature.object = rig
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.matrix_world = world
    obj["aevrynd_role"] = "hair_undercut_scalp"
    obj["aevrynd_hair_revision"] = 46
    obj["aevrynd_body_clearance_m"] = clearance
    obj["aevrynd_segments"] = segments
    obj["aevrynd_rows"] = rows
    obj["aevrynd_projection_misses"] = misses
    obj["aevrynd_alpha_min"] = min(alpha_values)
    obj["aevrynd_alpha_max"] = max(alpha_values)
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, isolated=False):
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.data.lens = 88
    camera.location = location
    look_at(camera, target)
    if isolated:
        for obj in bpy.data.objects:
            if obj.type == "MESH" and obj.name.startswith("Hair"):
                obj.hide_render = obj.name == "HairUndercutScalp" and False or obj.name != "HairUndercutScalp"
    else:
        for obj in bpy.data.objects:
            if obj.type == "MESH":
                obj.hide_render = False
    bpy.ops.render.render(write_still=True)


def export(path, rig, excluded=()):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.data.objects:
        if obj.type in {"MESH", "ARMATURE"} and obj.name not in excluded:
            obj.hide_render = False
            obj.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True, export_apply=True, export_yup=True, export_extras=True, export_animations=True, export_frame_range=True, export_attributes=True, export_vertex_color="ACTIVE")


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
bpy.context.scene.frame_set(1)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BUILD.parent.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]
rig = bpy.data.objects["AevryndFemaleRig"]
undercut = rebuild_undercut(body, rig, material())
bpy.context.scene["aevrynd_hair_revision"] = 46
bpy.context.scene["aevrynd_undercut_strategy"] = "high_resolution_wide_four_edge_fade"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-scalp-blend-isolated-right", (0.58, -0.08, 1.615), (0.0, 0.0, 1.59), True)
for name, location, target in (
    ("female-scalp-blend-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555)),
    ("female-scalp-blend-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55)),
    ("female-scalp-blend-left", (-0.66, -0.05, 1.60), (0.0, 0.0, 1.57)),
    ("female-scalp-blend-right", (0.66, -0.05, 1.60), (0.0, 0.0, 1.57)),
    ("female-scalp-blend-back", (0.0, 0.76, 1.60), (0.0, 0.01, 1.57)),
):
    render(camera, name, location, target)
multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
levels = (multires.levels, multires.sculpt_levels, multires.render_levels)
multires.levels = multires.sculpt_levels = multires.render_levels = 0
export(BUILD, rig)
export(LOD1, rig, {"HairMain", "HairFlyaways", "HairGuides", "HairClumpsMediumCards", "HairlineBaby", "HairTempleClumps", "HairNapeClumps", "HairBoundaryClumps", "HairUndercutScalp"})
multires.levels, multires.sculpt_levels, multires.render_levels = levels
print("AEVRYND_SCALP_BLEND_V46_REPORT=" + json.dumps({"state": "AUTHORING", "vertices": len(undercut.data.vertices), "faces": len(undercut.data.polygons), "alpha_min": undercut["aevrynd_alpha_min"], "alpha_max": undercut["aevrynd_alpha_max"], "runtime_glb": str(BUILD), "lod1_glb": str(LOD1)}))
