import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v44.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v45.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v45.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v45-lod1.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "crown-cards-v45"
TEXTURE = ROOT / "assets-source" / "aevrynd-character" / "textures" / "aevrynd-hair-clump-alpha-v45.png"
RNG = random.Random(45019)


def evaluated_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
    result = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    return result


def connected_components(mesh):
    parent = list(range(len(mesh.vertices)))
    used = set()

    def find(value):
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(first, second):
        first, second = find(first), find(second)
        if first != second:
            parent[second] = first

    for polygon in mesh.polygons:
        indices = list(polygon.vertices)
        used.update(indices)
        for index in indices[1:]:
            union(indices[0], index)
    groups = {}
    for index in sorted(used):
        groups.setdefault(find(index), []).append(index)
    return [sorted(indices) for _, indices in sorted(groups.items())]


def conform_cards(obj, scalp_tree, clearance, width_range, seed):
    rng = random.Random(seed)
    inverse = obj.matrix_world.inverted()
    components = connected_components(obj.data)
    minimum_clearance = 999.0
    width_factors = []
    for component_index, indices in enumerate(components):
        if len(indices) % 2:
            raise RuntimeError(f"{obj.name} component has odd vertex count")
        width_factor = rng.uniform(*width_range)
        width_factors.append(width_factor)
        rows = len(indices) // 2
        phase = rng.uniform(-math.pi, math.pi)
        for row in range(rows):
            first_index, second_index = indices[row * 2:row * 2 + 2]
            first = obj.matrix_world @ obj.data.vertices[first_index].co
            second = obj.matrix_world @ obj.data.vertices[second_index].co
            center = (first + second) * 0.5
            location, normal, _, _ = scalp_tree.find_nearest(center)
            if location is None:
                continue
            normal.normalize()
            if normal.dot(center - Vector((0.0, 0.0, 1.60))) < 0.0:
                normal.negate()
            axis = second - first
            axis -= normal * axis.dot(normal)
            if axis.length < 1e-8:
                axis = Vector((1.0, 0.0, 0.0))
            axis.normalize()
            t = row / max(1, rows - 1)
            shell = clearance + 0.00028 * math.sin(math.pi * t) + 0.00010 * math.sin(math.tau * t + phase)
            new_center = location + normal * shell
            half_width = (second - first).length * 0.5 * width_factor * (0.96 + 0.04 * math.sin(math.pi * t))
            new_first = new_center - axis * half_width
            new_second = new_center + axis * half_width
            obj.data.vertices[first_index].co = inverse @ new_first
            obj.data.vertices[second_index].co = inverse @ new_second
            minimum_clearance = min(minimum_clearance, shell)
    obj.data.update()
    obj["aevrynd_groom_revision"] = 45
    obj["aevrynd_card_shell_clearance_m"] = clearance
    obj["aevrynd_card_width_factor_min"] = min(width_factors)
    obj["aevrynd_card_width_factor_max"] = max(width_factors)
    obj["aevrynd_card_component_count"] = len(components)
    return {"components": len(components), "width_min": min(width_factors), "width_max": max(width_factors), "minimum_shell": minimum_clearance}


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def create_texture():
    width, height = 256, 512
    old = bpy.data.images.get("AevryndHairClumpAlphaV45")
    if old:
        bpy.data.images.remove(old)
    image = bpy.data.images.new("AevryndHairClumpAlphaV45", width=width, height=height, alpha=True)
    phases = [RNG.uniform(0.0, math.tau) for _ in range(23)]
    amplitudes = [RNG.uniform(0.58, 1.0) for _ in phases]
    widths = [RNG.uniform(0.0065, 0.0125) for _ in phases]
    pixels = [0.0] * (width * height * 4)
    for y in range(height):
        v = y / (height - 1)
        root = smoothstep(v / 0.025)
        tip = 1.0 - smoothstep((v - 0.72) / 0.28)
        for x in range(width):
            u = x / (width - 1)
            edge = 1.0 - smoothstep((abs(u - 0.5) - 0.455) / 0.045)
            fibers = 0.0
            tone = 0.0
            for index, phase in enumerate(phases):
                center = (index + 0.5) / len(phases)
                center += 0.010 * math.sin(v * (1.6 + index % 5 * 0.23) * math.tau + phase)
                strength = amplitudes[index] * math.exp(-((u - center) / widths[index]) ** 2)
                fibers = max(fibers, strength)
                tone = max(tone, strength * (0.72 + 0.28 * math.sin(index * 2.17) ** 2))
            alpha = max(0.0, min(1.0, edge * root * tip * (0.025 + 0.975 * fibers)))
            color = 0.62 + 0.38 * tone
            offset = (y * width + x) * 4
            pixels[offset:offset + 4] = (0.036 * color, 0.0085 * color, 0.0032 * color, alpha)
    image.pixels.foreach_set(pixels)
    image.filepath_raw = str(TEXTURE)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image


def create_material(image):
    material = bpy.data.materials.get("Aevrynd_Hair_Clumps_v45") or bpy.data.materials.new("Aevrynd_Hair_Clumps_v45")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    shader.inputs["Base Color"].default_value = (0.024, 0.0042, 0.0015, 1.0)
    shader.inputs["Roughness"].default_value = 0.58
    shader.inputs["Specular IOR Level"].default_value = 0.07
    if shader.inputs.get("Anisotropic IOR Level"):
        shader.inputs["Anisotropic IOR Level"].default_value = 0.42
    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    links.new(texture.outputs["Alpha"], shader.inputs["Alpha"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material.surface_render_method = "DITHERED"
    material.use_transparency_overlap = False
    material["aevrynd_runtime_owned"] = True
    material["aevrynd_alpha_strategy"] = "separated_fiber_alpha_low_background"
    return material


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens=88):
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.data.lens = lens
    camera.location = location
    look_at(camera, target)
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
TEXTURE.parent.mkdir(parents=True, exist_ok=True)
BUILD.parent.mkdir(parents=True, exist_ok=True)
scalp = bpy.data.objects["HairScalp"]
scalp_tree = evaluated_tree(scalp)
large = bpy.data.objects["HairClumpsLarge"]
medium = bpy.data.objects["HairClumpsMediumCards"]
geometry = {
    "large": conform_cards(large, scalp_tree, 0.00110, (0.52, 0.80), 4511),
    "medium": conform_cards(medium, scalp_tree, 0.00265, (0.58, 0.88), 4522),
}
material = create_material(create_texture())
for obj in (large, medium):
    obj.data.materials.clear()
    obj.data.materials.append(material)
bpy.context.scene["aevrynd_hair_revision"] = 45
bpy.context.scene["aevrynd_card_strategy"] = "nested_scalp_shells_narrow_fiber_alpha"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
for name, location, target, lens in (
    ("female-crown-top", (0.0, -0.18, 2.02), (0.0, 0.0, 1.67), 105),
    ("female-crown-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555), 82),
    ("female-crown-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55), 82),
    ("female-crown-left", (-0.66, -0.05, 1.60), (0.0, 0.0, 1.57), 88),
    ("female-crown-right", (0.66, -0.05, 1.60), (0.0, 0.0, 1.57), 88),
    ("female-crown-back", (0.0, 0.76, 1.60), (0.0, 0.01, 1.57), 88),
):
    render(camera, name, location, target, lens)

body = bpy.data.objects["AevryndFemaleBodyBase"]
rig = bpy.data.objects["AevryndFemaleRig"]
multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
levels = (multires.levels, multires.sculpt_levels, multires.render_levels)
multires.levels = multires.sculpt_levels = multires.render_levels = 0
export(BUILD, rig)
export(LOD1, rig, {"HairMain", "HairFlyaways", "HairGuides", "HairClumpsMediumCards", "HairlineBaby", "HairTempleClumps", "HairNapeClumps", "HairBoundaryClumps", "HairUndercutScalp"})
multires.levels, multires.sculpt_levels, multires.render_levels = levels
print("AEVRYND_CROWN_CARDS_V45_REPORT=" + json.dumps({"state": "AUTHORING", "geometry": geometry, "texture": str(TEXTURE), "runtime_glb": str(BUILD), "lod1_glb": str(LOD1)}))
