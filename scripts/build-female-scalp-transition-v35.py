import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v33.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v35.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v35.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v35-lod1.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "scalp-transition-v35"


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def add_density_fade(scalp, fade_m=0.0135):
    mesh = scalp.data
    edge_uses = {tuple(sorted(edge.vertices)): 0 for edge in mesh.edges}
    for polygon in mesh.polygons:
        verts = list(polygon.vertices)
        for index, a in enumerate(verts):
            b = verts[(index + 1) % len(verts)]
            key = tuple(sorted((a, b)))
            edge_uses[key] = edge_uses.get(key, 0) + 1
    boundary_indices = sorted({index for edge, uses in edge_uses.items() if uses == 1 for index in edge})
    tree = KDTree(len(boundary_indices))
    for slot, index in enumerate(boundary_indices):
        tree.insert(scalp.matrix_world @ mesh.vertices[index].co, slot)
    tree.balance()

    old = mesh.color_attributes.get("AevryndScalpDensity")
    if old:
        mesh.color_attributes.remove(old)
    density = mesh.color_attributes.new(name="AevryndScalpDensity", type="BYTE_COLOR", domain="POINT")
    alpha_values = []
    for vertex in mesh.vertices:
        world = scalp.matrix_world @ vertex.co
        _, _, distance = tree.find(world)
        normalized = smoothstep(distance / fade_m)
        # A faint root shadow avoids an artificial transparent gap while the
        # nonlinear ramp removes the hard helmet edge.
        alpha = 0.10 + 0.90 * normalized
        density.data[vertex.index].color = (0.020, 0.0035, 0.0012, alpha)
        alpha_values.append(alpha)
    mesh.color_attributes.active_color = density

    material = mesh.materials[0]
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    vertex_color = nodes.get("Aevrynd Scalp Density") or nodes.new("ShaderNodeVertexColor")
    vertex_color.name = "Aevrynd Scalp Density"
    vertex_color.layer_name = "AevryndScalpDensity"
    for link in list(shader.inputs["Alpha"].links):
        links.remove(link)
    for link in list(shader.inputs["Base Color"].links):
        links.remove(link)
    links.new(vertex_color.outputs["Color"], shader.inputs["Base Color"])
    links.new(vertex_color.outputs["Alpha"], shader.inputs["Alpha"])
    shader.inputs["Roughness"].default_value = 0.71
    shader.inputs["Specular IOR Level"].default_value = 0.18
    if shader.inputs.get("Anisotropic IOR Level"):
        shader.inputs["Anisotropic IOR Level"].default_value = 0.28
    material.surface_render_method = "DITHERED"
    material.use_transparency_overlap = False
    material["aevrynd_runtime_owned"] = True
    scalp["aevrynd_groom_revision"] = 35
    scalp["aevrynd_boundary_vertex_count"] = len(boundary_indices)
    scalp["aevrynd_density_fade_m"] = fade_m
    scalp["aevrynd_density_alpha_min"] = min(alpha_values)
    scalp["aevrynd_density_alpha_max"] = max(alpha_values)
    return boundary_indices, alpha_values


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target):
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.data.lens = 82
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
scalp = bpy.data.objects["HairScalp"]
boundary, alpha_values = add_density_fade(scalp)
bpy.context.scene["aevrynd_hair_revision"] = 35
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-scalp-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555))
render(camera, "female-scalp-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55))
render(camera, "female-scalp-left", (-0.66, -0.05, 1.575), (0.0, 0.0, 1.545))
render(camera, "female-scalp-right", (0.66, -0.05, 1.575), (0.0, 0.0, 1.545))
render(camera, "female-scalp-back", (0.0, 0.76, 1.575), (0.0, 0.01, 1.545))

multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_levels = (multires.levels, multires.sculpt_levels, multires.render_levels)
multires.levels = multires.sculpt_levels = multires.render_levels = 0
export_runtime(BUILD, rig)
export_runtime(LOD1, rig, {"HairMain", "HairFlyaways"})
multires.levels, multires.sculpt_levels, multires.render_levels = old_levels

print("AEVRYND_SCALP_TRANSITION_V35_REPORT=" + json.dumps({
    "state": "AUTHORING",
    "boundary_vertices": len(boundary),
    "fade_m": float(scalp["aevrynd_density_fade_m"]),
    "alpha_range": [min(alpha_values), max(alpha_values)],
    "runtime_glb": str(BUILD),
    "lod1_glb": str(LOD1),
}))
