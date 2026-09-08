import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v30.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v33.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v33.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v33-lod1.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "undercut-density-v33"


def stubble_material():
    material = bpy.data.materials.get("Aevrynd_Hair_Undercut_v33") or bpy.data.materials.new(
        "Aevrynd_Hair_Undercut_v33"
    )
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 420.0
    noise.inputs["Detail"].default_value = 2.2
    noise.inputs["Roughness"].default_value = 0.72
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.28
    ramp.color_ramp.elements[0].color = (0.006, 0.0010, 0.0004, 1.0)
    ramp.color_ramp.elements[1].position = 0.74
    ramp.color_ramp.elements[1].color = (0.050, 0.0105, 0.0035, 1.0)
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.20
    bump.inputs["Distance"].default_value = 0.000055
    density = nodes.new("ShaderNodeVertexColor")
    density.layer_name = "AevryndUndercutDensity"
    shader.inputs["Roughness"].default_value = 0.66
    shader.inputs["Specular IOR Level"].default_value = 0.19
    if shader.inputs.get("Anisotropic IOR Level"):
        shader.inputs["Anisotropic IOR Level"].default_value = 0.28
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(density.outputs["Color"], shader.inputs["Base Color"])
    links.new(density.outputs["Alpha"], shader.inputs["Alpha"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material.surface_render_method = "DITHERED"
    material["aevrynd_requires_runtime_bake"] = True
    return material


def body_projection(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(points, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def build_undercut(body, rig, material, clearance=0.00072):
    old = bpy.data.objects.get("HairUndercutScalp")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    source = body.data
    tree = body_projection(body)
    nearest = KDTree(len(source.vertices))
    for vertex in source.vertices:
        nearest.insert(body.matrix_world @ vertex.co, vertex.index)
    nearest.balance()

    center = Vector((0.0, -0.002, 1.625))
    segments, rows = 72, 15
    vertices = []
    source_indices = []
    faces = []
    misses = 0
    for segment in range(segments):
        s = segment / (segments - 1)
        phi = 0.28 + s * (math.pi - 0.56)
        side = abs(math.cos(phi))
        top_theta = 1.31 + 0.11 * side
        bottom_theta = 2.31 - 0.15 * side
        for row in range(rows):
            t = row / (rows - 1)
            eased = t * t * (3.0 - 2.0 * t)
            theta = top_theta + (bottom_theta - top_theta) * eased
            direction = Vector((
                0.98 * math.sin(theta) * math.cos(phi),
                1.12 * math.sin(theta) * math.sin(phi),
                math.cos(theta),
            )).normalized()
            location, normal, _, _ = tree.ray_cast(center, direction, 0.30)
            if location is None:
                misses += 1
                location = center + direction * 0.10
                normal = direction
            point = location + normal.normalized() * clearance
            vertices.append(tuple(body.matrix_world.inverted() @ point))
            _, source_index, _ = nearest.find(location)
            source_indices.append(source_index)
    for segment in range(segments - 1):
        for row in range(rows - 1):
            a = segment * rows + row
            b = (segment + 1) * rows + row
            faces.append((a, b, b + 1, a + 1))
    mesh = bpy.data.meshes.new("HairUndercutScalpMeshV33")
    mesh.from_pydata(vertices, [], faces)
    density = mesh.color_attributes.new(
        name="AevryndUndercutDensity", type="BYTE_COLOR", domain="POINT"
    )
    for segment in range(segments):
        s = segment / (segments - 1)
        side_fade = math.sin(math.pi * s) ** 0.48
        for row in range(rows):
            t = row / (rows - 1)
            vertical_fade = math.sin(math.pi * t) ** 0.42
            alpha = 0.58 * side_fade * vertical_fade
            grain = 0.008 * math.sin(segment * 2.17 + row * 4.31)
            density.data[segment * rows + row].color_srgb = (
                max(0.0, 0.070 + grain),
                max(0.0, 0.022 + grain * 0.35),
                max(0.0, 0.009 + grain * 0.15),
                alpha,
            )
    mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True

    obj = bpy.data.objects.new("HairUndercutScalp", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = body.matrix_world.copy()
    group_map = {
        source_group.index: obj.vertex_groups.new(name=source_group.name)
        for source_group in body.vertex_groups
    }
    for target_index, source_index in enumerate(source_indices):
        for assignment in source.vertices[source_index].groups:
            if assignment.weight > 1e-8:
                group_map[assignment.group].add([target_index], assignment.weight, "REPLACE")
    armature = obj.modifiers.new("Aevrynd Undercut Deform", "ARMATURE")
    armature.object = rig
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.matrix_world = world
    obj["aevrynd_role"] = "hair_undercut_scalp"
    obj["aevrynd_hair_revision"] = 33
    obj["aevrynd_body_clearance_m"] = clearance
    obj["aevrynd_segments"] = segments
    obj["aevrynd_rows"] = rows
    obj["aevrynd_projection_misses"] = misses
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens=86):
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.data.lens = lens
    camera.location = location
    look_at(camera, target)
    for obj in bpy.data.objects:
        if obj.get("aevrynd_role") == "cornea":
            obj.hide_render = False
    bpy.ops.render.render(write_still=True)


def export_runtime(path, rig, excluded=()):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.data.objects:
        if obj.type in {"MESH", "ARMATURE"} and obj.name not in excluded:
            obj.hide_render = False
            obj.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format="GLB", use_selection=True,
        export_apply=True, export_yup=True, export_extras=True,
        export_animations=True, export_frame_range=True,
        export_attributes=True, export_vertex_color="ACTIVE",
    )


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
bpy.context.scene.frame_set(1)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BUILD.parent.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]
rig = bpy.data.objects["AevryndFemaleRig"]
undercut = build_undercut(body, rig, stubble_material())
bpy.context.scene["aevrynd_hair_revision"] = 33
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-undercut-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555))
render(camera, "female-undercut-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55))
render(camera, "female-undercut-left", (-0.66, -0.05, 1.575), (0.0, 0.0, 1.545))
render(camera, "female-undercut-right", (0.66, -0.05, 1.575), (0.0, 0.0, 1.545))
render(camera, "female-undercut-back", (0.0, 0.76, 1.575), (0.0, 0.01, 1.545))

multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_levels = (multires.levels, multires.sculpt_levels, multires.render_levels)
multires.levels = multires.sculpt_levels = multires.render_levels = 0
export_runtime(BUILD, rig)
export_runtime(LOD1, rig, {"HairMain", "HairFlyaways"})
multires.levels, multires.sculpt_levels, multires.render_levels = old_levels

print("AEVRYND_UNDERCUT_DENSITY_V33_REPORT=" + json.dumps({
    "state": "AUTHORING",
    "vertices": len(undercut.data.vertices),
    "faces": len(undercut.data.polygons),
    "clearance_m": undercut["aevrynd_body_clearance_m"],
    "projection_misses": undercut["aevrynd_projection_misses"],
    "runtime_glb": str(BUILD),
    "lod1_glb": str(LOD1),
}))
